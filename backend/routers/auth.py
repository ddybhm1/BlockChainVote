from __future__ import annotations

"""认证路由 - 身份中心登录、项目状态与匿名授权"""
import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import JWT_EXPIRE_HOURS, JWT_SECRET_KEY
from database import get_db
from models import ClaimedTicket, Election, ElectionVoter, SecurityLog, Voter
from services.blockchain import (
    authorize_voter_on_chain,
    fetch_factory_elections,
    get_contract,
    get_web3,
)
from services.session_auth import create_token, decode_token

router = APIRouter(prefix="/api/auth", tags=["认证"])
bearer_scheme = HTTPBearer(auto_error=False)

STATUS_AVAILABLE = "AVAILABLE"
STATUS_CLAIMED = "CLAIMED"
STATUS_VOTED = "VOTED"
STATUS_RESTRICTED = "RESTRICTED"

auth_logger = logging.getLogger("auth_logger")
auth_logger.setLevel(logging.INFO)
if not auth_logger.handlers:
    fh = logging.FileHandler("app_business.log", encoding="utf-8")
    fh.setFormatter(
        logging.Formatter(
            "[%(levelname)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    auth_logger.addHandler(fh)


def _normalize_student_id(student_id: str) -> str:
    student_id = student_id.strip()
    if not student_id or len(student_id) > 20:
        raise ValueError("学号格式无效")
    return student_id


def _normalize_eth_address(address: str, label: str) -> str:
    if not re.match(r"^0x[0-9a-fA-F]{40}$", address or ""):
        raise ValueError(f"无效的{label}格式")
    return address.lower()


def _expect_eth_address(address: str, label: str) -> str:
    try:
        return _normalize_eth_address(address, label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _phase_from_times(start_time: int, end_time: int) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    if not start_time or not end_time or now < start_time:
        return "PENDING"
    if now > end_time:
        return "ENDED"
    return "ACTIVE"


def _serialize_ticket_status(ticket: Optional[ClaimedTicket]) -> str:
    if not ticket:
        return STATUS_AVAILABLE
    if ticket.status == STATUS_VOTED:
        return STATUS_VOTED
    return STATUS_CLAIMED


async def _get_current_student_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    try:
        payload = decode_token(credentials.credentials, JWT_SECRET_KEY)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    student_id = payload.get("sub", "").strip()
    if not student_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效")
    return student_id


async def _verify_student_password(student_id: str, password: str, client_ip: str, db: AsyncSession) -> Voter:
    voter = await db.scalar(select(Voter).where(Voter.student_id == student_id))
    if not voter:
        auth_logger.warning(f"[AuthService] IP: {client_ip} - 学号 {student_id} 登录失败：学号不存在")
        raise HTTPException(status_code=401, detail="学号不存在")

    if not bcrypt.checkpw(password.encode("utf-8"), voter.password_hash.encode("utf-8")):
        auth_logger.warning(f"[AuthService] IP: {client_ip} - 学号 {student_id} 登录失败：密码错误")
        raise HTTPException(status_code=401, detail="密码错误")

    return voter


async def _get_election_id(election_address: str, db: AsyncSession) -> int:
    election = await db.scalar(select(Election).where(Election.contract_address == election_address))
    if not election:
        raise HTTPException(status_code=404, detail="无效的投票项目地址")
    return election.id

async def _require_election_membership(student_id: str, election_address: str, db: AsyncSession) -> None:
    election_id = await _get_election_id(election_address, db)
    record = await db.scalar(
        select(ElectionVoter).where(
            ElectionVoter.student_id == student_id,
            ElectionVoter.election_id == election_id,
        )
    )
    if not record:
        raise HTTPException(status_code=403, detail="你不在该投票项目的选民名单中")


async def _get_ticket(student_id: str, election_address: str, db: AsyncSession) -> Optional[ClaimedTicket]:
    election_id = await _get_election_id(election_address, db)
    return await db.scalar(
        select(ClaimedTicket).where(
            ClaimedTicket.student_id == student_id,
            ClaimedTicket.election_id == election_id,
        )
    )


class LoginRequest(BaseModel):
    student_id: str
    password: str

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, value: str) -> str:
        return _normalize_student_id(value)


class LoginResponse(BaseModel):
    success: bool
    token: str
    student_id: str
    expires_in_hours: int


class SessionResponse(BaseModel):
    success: bool
    student_id: str


class TicketActionRequest(BaseModel):
    election_address: str
    wallet_address: str

    @field_validator("election_address")
    @classmethod
    def validate_election_address(cls, value: str) -> str:
        return _normalize_eth_address(value, "投票项目合约地址")

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet_address(cls, value: str) -> str:
        return _normalize_eth_address(value, "钱包地址")


class TicketActionResponse(BaseModel):
    success: bool
    message: str
    status: str


class DashboardElectionItem(BaseModel):
    election_address: str
    title: str
    start_time: int
    end_time: int
    phase: str
    status: str
    eligible: bool = True


async def _sync_election_titles(db: AsyncSession) -> None:
    loop = asyncio.get_running_loop()

    try:
        catalog = await loop.run_in_executor(None, fetch_factory_elections)
    except Exception as exc:
        auth_logger.warning(f"[CatalogService] 读取工厂标题失败：{exc}")
        return

    if not catalog:
        return

    titles_by_address = {
        item["address"]: item["title"]
        for item in catalog
        if item.get("address")
    }
    if not titles_by_address:
        return

    existing_rows = (
        await db.execute(
            select(Election).where(
                func.lower(Election.contract_address).in_(list(titles_by_address.keys()))
            )
        )
    ).scalars().all()
    existing_map = {row.contract_address.lower(): row for row in existing_rows}

    has_changes = False
    for address, title in titles_by_address.items():
        election = existing_map.get(address)
        clean_title = title or ""
        start_time = int(next((item.get("start_time", 0) for item in catalog if item.get("address") == address), 0))
        end_time = int(next((item.get("end_time", 0) for item in catalog if item.get("address") == address), 0))
        if election:
            if clean_title and election.title != clean_title:
                election.title = clean_title
                has_changes = True
            if start_time and election.start_time != start_time:
                election.start_time = start_time
                has_changes = True
            if end_time and election.end_time != end_time:
                election.end_time = end_time
                has_changes = True
            continue

        db.add(
            Election(
                contract_address=address,
                title=clean_title,
                start_time=start_time,
                end_time=end_time,
            )
        )
        has_changes = True

    if has_changes:
        await db.commit()


async def _authorize_ticket(
    *,
    student_id: str,
    wallet_address: str,
    election_address: str,
    client_ip: str,
    db: AsyncSession,
) -> TicketActionResponse:
    await _require_election_membership(student_id, election_address, db)

    existing_ticket = await _get_ticket(student_id, election_address, db)
    if existing_ticket:
        if existing_ticket.status == STATUS_VOTED:
            raise HTTPException(status_code=409, detail="该项目已经完成投票，无需再次授权")

        sec_log = SecurityLog(
            event_type="duplicate_claim",
            student_id=student_id,
            election_address=election_address,
            details=f"学号 {student_id} 尝试重复领票（投票项目 {election_address[:10]}...）",
            severity="warning",
        )
        db.add(sec_log)
        await db.commit()
        raise HTTPException(
            status_code=409,
            detail="该项目已经领票。系统不保存地址，请切换到当时授权的钱包继续投票。",
        )

    auth_logger.info(f"[AuthService] IP: {client_ip} - 学号 {student_id} 验证通过，准备进行链上授权。")

    try:
        tx_hash = await authorize_voter_on_chain(wallet_address, election_address)
    except Exception as exc:
        masked_address = f"{wallet_address[:6]}...{wallet_address[-4:]}"
        auth_logger.error(f"[Web3Service] 学号 {student_id} 授权地址 {masked_address} 失败：{exc}")
        raise HTTPException(status_code=500, detail=f"链上授权失败: {exc}") from exc

    election_id = await _get_election_id(election_address, db)
    ticket = ClaimedTicket(
        student_id=student_id,
        election_id=election_id,
        status=STATUS_CLAIMED,
        updated_at=datetime.utcnow(),
    )
    db.add(ticket)
    await db.commit()

    masked_address = f"{wallet_address[:6]}...{wallet_address[-4:]}"
    auth_logger.info(f"[Web3Service] 学号 {student_id} 的地址 {masked_address} 已授权，TxHash: {tx_hash}")

    return TicketActionResponse(
        success=True,
        message="领票成功，请使用当前钱包地址完成投票",
        status=STATUS_CLAIMED,
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown_ip"
    await _verify_student_password(req.student_id, req.password, client_ip, db)

    auth_logger.info(f"[AuthService] IP: {client_ip} - 学号 {req.student_id} 登录成功")
    token = create_token(req.student_id, JWT_SECRET_KEY, JWT_EXPIRE_HOURS * 3600)
    return LoginResponse(
        success=True,
        token=token,
        student_id=req.student_id,
        expires_in_hours=JWT_EXPIRE_HOURS,
    )


@router.get("/me", response_model=SessionResponse)
async def get_session(student_id: str = Depends(_get_current_student_id)):
    return SessionResponse(success=True, student_id=student_id)


@router.get("/my-elections", response_model=List[DashboardElectionItem])
async def get_my_elections(
    student_id: str = Depends(_get_current_student_id),
    db: AsyncSession = Depends(get_db),
):
    await _sync_election_titles(db)

    # 从工厂合约获取所有有效的项目地址
    loop = asyncio.get_running_loop()
    try:
        factory_elections = await loop.run_in_executor(None, fetch_factory_elections)
        factory_addresses = {item['address'].lower() for item in factory_elections}
    except Exception as exc:
        auth_logger.warning(f"[CatalogService] 获取工厂合约项目失败: {exc}")
        factory_addresses = set()

    # 获取当前学生有权访问的所有项目
    mappings = (
        await db.execute(
            select(ElectionVoter, Election, ClaimedTicket)
            .outerjoin(Election, Election.id == ElectionVoter.election_id)
            .outerjoin(
                ClaimedTicket,
                (ClaimedTicket.student_id == ElectionVoter.student_id)
                & (ClaimedTicket.election_id == ElectionVoter.election_id),
            )
            .where(ElectionVoter.student_id == student_id)
            .order_by(Election.start_time.asc(), Election.id.asc())
        )
    ).all()

    items = []
    for election_voter, election, ticket in mappings:
        if not election:
            continue
        
        normalized_address = election.contract_address.lower()
        
        # 只返回在工厂合约中的项目
        if normalized_address not in factory_addresses:
            auth_logger.debug(f"[CatalogService] 学生 {student_id} 的项目 {normalized_address} 不在工厂合约中，已过滤")
            continue
            
        start_time = int(election.start_time) if election.start_time else 0
        end_time = int(election.end_time) if election.end_time else 0
        
        items.append(
            DashboardElectionItem(
                election_address=normalized_address,
                title=(election.title.strip() if election and election.title else "未命名投票项目"),
                start_time=start_time,
                end_time=end_time,
                phase=_phase_from_times(start_time, end_time),
                status=_serialize_ticket_status(ticket),
                eligible=True,
            )
        )

    return items


@router.get("/ticket-status/{election_address}", response_model=DashboardElectionItem)
async def get_ticket_status(
    election_address: str,
    student_id: str = Depends(_get_current_student_id),
    db: AsyncSession = Depends(get_db),
):
    await _sync_election_titles(db)
    election_address = _expect_eth_address(election_address, "投票项目合约地址")
    await _require_election_membership(student_id, election_address, db)

    election = await db.scalar(
        select(Election).where(func.lower(Election.contract_address) == election_address)
    )
    ticket = await _get_ticket(student_id, election_address, db)
    start_time = int(election.start_time) if election else 0
    end_time = int(election.end_time) if election else 0

    return DashboardElectionItem(
        election_address=election_address,
        title=(election.title.strip() if election and election.title else "未命名投票项目"),
        start_time=start_time,
        end_time=end_time,
        phase=_phase_from_times(start_time, end_time),
        status=_serialize_ticket_status(ticket),
        eligible=True,
    )


@router.post("/authorize-ticket", response_model=TicketActionResponse)
async def authorize_ticket(
    req: TicketActionRequest,
    request: Request,
    student_id: str = Depends(_get_current_student_id),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown_ip"
    return await _authorize_ticket(
        student_id=student_id,
        wallet_address=req.wallet_address,
        election_address=req.election_address,
        client_ip=client_ip,
        db=db,
    )


@router.post("/mark-voted", response_model=TicketActionResponse)
async def mark_voted(
    req: TicketActionRequest,
    request: Request,
    student_id: str = Depends(_get_current_student_id),
    db: AsyncSession = Depends(get_db),
):
    """投票完成后标记票据状态为已投票"""
    client_ip = request.client.host if request.client else "unknown_ip"
    
    try:
        election_address = _expect_eth_address(req.election_address, "投票项目合约地址")
        wallet_address = _expect_eth_address(req.wallet_address, "钱包地址")
        await _require_election_membership(student_id, election_address, db)
        
        ticket = await _get_ticket(student_id, election_address, db)
        if not ticket:
            raise HTTPException(
                status_code=400, 
                detail="没有找到该投票项目的票据，请先领票"
            )
        
        # 检查是否已经投过票
        if ticket.status == STATUS_VOTED:
            return TicketActionResponse(
                success=True,
                message="你已经完成过本项目的投票",
                status=STATUS_VOTED,
            )
        
        # 标记为已投票
        ticket.status = STATUS_VOTED
        await db.commit()
        
        auth_logger.info(
            f"[TicketService] IP: {client_ip} - 学号 {student_id} "
            f"标记投票完成: {election_address}"
        )
        
        return TicketActionResponse(
            success=True,
            message="投票状态已更新",
            status=STATUS_VOTED,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        auth_logger.error(
            f"[TicketService] IP: {client_ip} - 学号 {student_id} "
            f"标记投票失败: {exc}"
        )
        raise HTTPException(status_code=500, detail="更新投票状态失败") from exc



