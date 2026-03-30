"""认证路由 - KYC 身份验证与匿名授权"""
import re
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from database import get_db
from models import Voter, ClaimedTicket, ElectionVoter, SecurityLog
from services.blockchain import authorize_voter_on_chain

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 配置独立的业务日志
auth_logger = logging.getLogger("auth_logger")
auth_logger.setLevel(logging.INFO)
if not auth_logger.handlers:
    fh = logging.FileHandler("app_business.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    auth_logger.addHandler(fh)


class ClaimTicketRequest(BaseModel):
    """领票请求：学号 + 密码 + 匿名钱包地址 + 投票项目合约地址"""
    student_id: str
    password: str
    wallet_address: str
    election_address: str

    @field_validator("wallet_address")
    @classmethod
    def validate_eth_address(cls, v: str) -> str:
        if not re.match(r"^0x[0-9a-fA-F]{40}$", v):
            raise ValueError("无效的以太坊地址格式")
        return v

    @field_validator("election_address")
    @classmethod
    def validate_election_address(cls, v: str) -> str:
        if not re.match(r"^0x[0-9a-fA-F]{40}$", v):
            raise ValueError("无效的投票项目合约地址格式")
        return v

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, v: str) -> str:
        if not v or len(v) > 20:
            raise ValueError("学号格式无效")
        return v.strip()


class ClaimTicketResponse(BaseModel):
    success: bool
    message: str
    tx_hash: Optional[str] = None


@router.post("/claim-ticket", response_model=ClaimTicketResponse)
async def claim_ticket(req: ClaimTicketRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    选民领票：验证身份后授权匿名地址到指定投票项目。
    流程：
    1. MySQL 校验学号与密码
    2. 检查该学号是否已在该项目中领票（ClaimedTicket 表）
    3. 记录领票
    4. 调用智能合约授权匿名地址
    5. 丢弃地址，不留任何映射
    """
    client_ip = request.client.host if request.client else "unknown_ip"

    voter = await db.scalar(select(Voter).where(Voter.student_id == req.student_id))
    if not voter:
        auth_logger.warning(f"[AuthService] IP: {client_ip} - 学号 {req.student_id} 请求授权失败：学号不存在")
        raise HTTPException(status_code=401, detail="学号不存在")

    if not bcrypt.checkpw(req.password.encode("utf-8"), voter.password_hash.encode("utf-8")):
        auth_logger.warning(f"[AuthService] IP: {client_ip} - 学号 {req.student_id} 请求授权失败：密码错误")
        raise HTTPException(status_code=401, detail="密码错误")

    in_election = await db.scalar(
        select(ElectionVoter).where(
            ElectionVoter.student_id == req.student_id,
            ElectionVoter.election_address == req.election_address.lower(),
        )
    )
    if not in_election:
        auth_logger.warning(f"[AuthService] IP: {client_ip} - 学号 {req.student_id} 请求授权失败：该学号不在选民名单中")
        raise HTTPException(status_code=403, detail="该学号不在当前投票项目的选民名单中")

    existing = await db.scalar(
        select(ClaimedTicket).where(
            ClaimedTicket.student_id == req.student_id,
            ClaimedTicket.election_address == req.election_address.lower(),
        )
    )
    if existing:
        auth_logger.warning(f"[AuthService] IP: {client_ip} - 学号 {req.student_id} 请求授权失败：密码错误")
        sec_log = SecurityLog(
            event_type="duplicate_claim",
            student_id=req.student_id,
            election_address=req.election_address.lower(),
            details=f"学号 {req.student_id} 尝试重复领票（投票项目 {req.election_address[:10]}...）",
            severity="warning"
        )
        db.add(sec_log)
        await db.commit()
        raise HTTPException(status_code=409, detail="该学号已在此投票项目中领取过投票资格，不可重复领票")

    auth_logger.info(f"[AuthService] IP: {client_ip} - 学号 {req.student_id} 验证通过，准许发放选票。")

    ticket = ClaimedTicket(
        student_id=req.student_id,
        election_address=req.election_address.lower(),
    )
    db.add(ticket)
    await db.commit()

    try:
        tx_hash = await authorize_voter_on_chain(req.wallet_address, req.election_address)
        masked_address = f"{req.wallet_address[:6]}...{req.wallet_address[-4:]}"
        auth_logger.info(f"[Web3Service] 管理员向区块链发起交易，成功将地址 {masked_address} 加入白名单，TxHash: {tx_hash}")
    except Exception as e:
        await db.delete(ticket)
        await db.commit()
        masked_address = f"{req.wallet_address[:6]}...{req.wallet_address[-4:]}"
        auth_logger.error(f"[Web3Service] 管理员向区块链发起交易失败，尝试加入地址 {masked_address}：{str(e)}")
        raise HTTPException(status_code=500, detail=f"链上授权失败: {str(e)}")

    return ClaimTicketResponse(
        success=True,
        message="投票资格已授权，请使用该钱包地址进行投票",
        tx_hash=tx_hash,
    )
