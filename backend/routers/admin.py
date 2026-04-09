import asyncio
import io
import json
import logging
import openpyxl
import bcrypt
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3
from web3.middleware import geth_poa_middleware

from config import ADMIN_PRIVATE_KEY, ADMIN_WALLET_ADDRESS, SEPOLIA_RPC, SEPOLIA_RPC_URL
from database import get_db
from models import Voter, ClaimedTicket, ElectionVoter, TransactionLog, SecurityLog, Election
from services.blockchain import get_web3, get_contract
from services.ipfs import pin_file_to_ipfs

router = APIRouter(prefix="/api/admin", tags=["管理"])
ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "contracts" / "VotingSystem.sol" / "VotingSystem.json"

admin_logger = logging.getLogger("admin_logger")
admin_logger.setLevel(logging.INFO)
if not admin_logger.handlers:
    fh = logging.FileHandler("app_business.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    admin_logger.addHandler(fh)


class DeployElectionRequest(BaseModel):
    start_time: int
    end_time: int


class DeployElectionResponse(BaseModel):
    success: bool
    contract_address: str
    message: str


class RegisterVoterRequest(BaseModel):
    student_id: str
    password: str
    election_address: str

    @field_validator("election_address")
    @classmethod
    def validate_election_address(cls, v: str) -> str:
        if not re.match(r"^0x[0-9a-fA-F]{40}$", v):
            raise ValueError("参数不完整或格式错误")
        return v.lower()


class RegisterVoterResponse(BaseModel):
    success: bool
    message: str


class SetVotingTimeRequest(BaseModel):
    election_address: str
    start_time: int
    end_time: int


class SyncElectionRequest(BaseModel):
    election_address: str
    title: str
    start_time: int
    end_time: int

    @field_validator("election_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not re.match(r"^0x[0-9a-fA-F]{40}$", v):
            raise ValueError("钱包地址格式错误")
        return v.lower()


class LogTransactionRequest(BaseModel):
    tx_hash: str
    election_address: str
    operation_type: str
    gas_used: Optional[int] = None
    gas_price: Optional[float] = None
    total_cost: Optional[str] = None
    status: str = "pending"
    memo: Optional[str] = None

    @field_validator("election_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not re.match(r"^0x[0-9a-fA-F]{40}$", v):
            raise ValueError("钱包地址格式错误")
        return v.lower()


class LogSecurityRequest(BaseModel):
    event_type: str
    student_id: Optional[str] = None
    election_address: Optional[str] = None
    details: str
    severity: str = "warning"


@router.post("/deploy-election", response_model=DeployElectionResponse)
async def deploy_election(req: DeployElectionRequest, db: AsyncSession = Depends(get_db)):
    try:
        w3 = get_web3()
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

        with ARTIFACT_PATH.open("r", encoding="utf-8") as f:
            artifact = json.load(f)
        abi = artifact["abi"]
        bytecode = artifact["bytecode"]

        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx = contract.constructor(admin_account.address).build_transaction({
            "from": admin_account.address,
            "nonce": w3.eth.get_transaction_count(admin_account.address),
            "gas": 4000000,
            "gasPrice": w3.eth.gas_price,
        })
        signed = admin_account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        contract_address = receipt.contractAddress.lower()

        db.add(Election(contract_address=contract_address, start_time=req.start_time, end_time=req.end_time))
        await db.commit()
        return DeployElectionResponse(success=True, contract_address=contract_address, message="合约部署成功")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"部署失败: {str(e)}")


@router.get("/election-time")
async def get_election_time(election_address: str, db: AsyncSession = Depends(get_db)):
    election = await db.scalar(select(Election).where(func.lower(Election.contract_address) == election_address.lower()))
    if not election:
        raise HTTPException(status_code=404, detail="未找到对应选举")
    return {"start_time": election.start_time, "end_time": election.end_time}


@router.post("/set-voting-time")
async def set_voting_time(req: SetVotingTimeRequest, db: AsyncSession = Depends(get_db)):
    if not req.election_address or req.start_time >= req.end_time:
        raise HTTPException(status_code=400, detail="请求参数错误")
    try:
        normalized_address = req.election_address.lower()
        w3 = get_web3()
        contract = get_contract(w3, normalized_address)
        admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(admin_account.address)
        tx = contract.functions.startVoting(req.start_time, req.end_time).build_transaction({
            "from": admin_account.address,
            "nonce": nonce,
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = admin_account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        election = await db.scalar(select(Election).where(func.lower(Election.contract_address) == normalized_address))
        if election:
            election.start_time = req.start_time
            election.end_time = req.end_time
        else:
            db.add(Election(contract_address=normalized_address, start_time=req.start_time, end_time=req.end_time))
        await db.commit()
        return {"success": True, "message": "投票时间已设置", "tx_hash": tx_hash.hex()}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"部署失败: {str(e)}")


@router.post("/sync-election")
async def sync_election(req: SyncElectionRequest, db: AsyncSession = Depends(get_db)):
    try:
        normalized_address = req.election_address.lower()
        election = await db.scalar(select(Election).where(func.lower(Election.contract_address) == normalized_address))
        
        if election:
            election.title = req.title
            election.start_time = req.start_time
            election.end_time = req.end_time
        else:
            new_election = Election(
                contract_address=normalized_address,
                title=req.title,
                start_time=req.start_time,
                end_time=req.end_time
            )
            db.add(new_election)
            
        await db.commit()
        return {"success": True, "message": "项目同步成功"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"项目同步失败: {str(e)}")


def _hash_pass(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def _check_pass(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

@router.post("/register-voter", response_model=RegisterVoterResponse)
async def register_voter(req: RegisterVoterRequest, db: AsyncSession = Depends(get_db)):
    student_id = req.student_id.strip()
    election_address = req.election_address.lower()

    election = await db.scalar(select(Election).where(Election.contract_address == election_address))
    if not election:
        raise HTTPException(status_code=404, detail="无效的投票项目")

    voter = await db.scalar(select(Voter).where(Voter.student_id == student_id))
    loop = asyncio.get_running_loop()
    if not voter:
        hashed = await loop.run_in_executor(None, _hash_pass, req.password)
        voter = Voter(
            student_id=student_id,
            password_hash=hashed.decode("utf-8"),
            has_claimed=False,
        )
        db.add(voter)
    else:
        is_valid = await loop.run_in_executor(None, _check_pass, req.password, voter.password_hash)
        if not is_valid:
            raise HTTPException(status_code=409, detail="该学号已存在且密码不一致")

    existing_mapping = await db.scalar(
        select(ElectionVoter).where(
            ElectionVoter.student_id == student_id,
            ElectionVoter.election_id == election.id,
        )
    )
    if existing_mapping:
        raise HTTPException(status_code=409, detail="该学号已注册到当前投票项目")

    db.add(ElectionVoter(student_id=student_id, election_id=election.id))
    await db.commit()

    return RegisterVoterResponse(success=True, message="选民注册成功（已加入当前项目白名单）")


@router.post("/upload-voters-excel")
async def upload_voters_excel(
    election_address: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not re.match(r"^0x[0-9a-fA-F]{40}$", election_address):
        raise HTTPException(status_code=400, detail="无效的投票项目合约地址格式")
    election_address = election_address.lower()

    election = await db.scalar(select(Election).where(Election.contract_address == election_address))
    if not election:
        raise HTTPException(status_code=404, detail="无效的投票项目")

    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="请上传 .xlsx 格式的 Excel 文件")

    contents = await file.read()
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        sheet = workbook.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析 Excel 文件失败: {str(e)}")

    rows = list(sheet.iter_rows(values_only=True))
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="Excel文件内容为空或缺少数据行")

    header = rows[0]
    try:
        col_student_id = header.index("学号")
        col_password = header.index("初始密码")
    except ValueError:
        try:
            col_student_id = header.index("studentId")
            col_password = header.index("password")
        except ValueError:
            raise HTTPException(status_code=400, detail="Excel文件必须包含“学号”和“初始密码”列")

    success_count = 0
    duplicate_count = 0
    errors = []

    for i, row in enumerate(rows[1:], start=2):
        if not row[col_student_id] or not row[col_password]:
            continue

        student_id = str(row[col_student_id]).strip()
        password = str(row[col_password]).strip()

        voter = await db.scalar(select(Voter).where(Voter.student_id == student_id))
        loop = asyncio.get_running_loop()
        
        if not voter:
            hashed = await loop.run_in_executor(None, _hash_pass, password)
            voter = Voter(
                student_id=student_id,
                password_hash=hashed.decode("utf-8"),
                has_claimed=False,
            )
            db.add(voter)
            await db.flush()
        else:
            is_valid = await loop.run_in_executor(None, _check_pass, password, voter.password_hash)
            if not is_valid:
                errors.append(f"第 {i} 行: 学号 {student_id} 已存在但密码不匹配")
                continue

        existing_mapping = await db.scalar(
            select(ElectionVoter).where(
                ElectionVoter.student_id == student_id,
                ElectionVoter.election_id == election.id,
            )
        )
        if existing_mapping:
            duplicate_count += 1
            continue

        db.add(ElectionVoter(student_id=student_id, election_id=election.id))
        success_count += 1

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(e)}")

    return {
        "success": True,
        "message": f"导入完成。成功新增 {success_count} 人，已存在/跳过 {duplicate_count} 人。错误: {len(errors)} 条",
        "errors": errors,
    }


@router.get("/voters-count")
async def get_voters_count(
    election_address: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if election_address:
        election_address = election_address.strip().lower()
        election = await db.scalar(select(Election).where(Election.contract_address == election_address))
        if not election:
            return {"total_registered": 0, "total_claimed": 0}
        
        total = await db.scalar(select(func.count()).select_from(ElectionVoter).where(ElectionVoter.election_id == election.id))
        claimed = await db.scalar(select(func.count()).select_from(ClaimedTicket).where(ClaimedTicket.election_id == election.id))
    else:
        total = await db.scalar(select(func.count()).select_from(Voter))
        claimed = await db.scalar(select(func.count()).select_from(ClaimedTicket))
    return {"total_registered": total, "total_claimed": claimed}


@router.post("/upload-ipfs")
async def upload_to_ipfs(file: UploadFile = File(...), purpose: str = Form("generic")):
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件大小不能超过 10MB")

    contents = await file.read()
    normalized_purpose = (purpose or "generic").strip().lower()

    if normalized_purpose == "manifesto":
        filename = (file.filename or "").lower()
        content_type = (file.content_type or "").lower()
        is_pdf_name = filename.endswith(".pdf")
        is_pdf_type = content_type in {"application/pdf", "application/x-pdf"}
        is_pdf_binary = contents.startswith(b"%PDF-")
        if not (is_pdf_name or is_pdf_type or is_pdf_binary):
            raise HTTPException(status_code=400, detail="候选人竞选宣言必须上传 PDF 文件")

    try:
        cid = pin_file_to_ipfs(contents, file.filename or "upload")
        admin_logger.info(f"[Web3Service] 管理员向区块链发起交易，成功将文件 {file.filename or 'upload'} 上传至 IPFS，CID: {cid}")
    except RuntimeError as e:
        admin_logger.error(f"[Web3Service] 管理员向 Web3 发起操作，IPFS 上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"IPFS 上传失败: {str(e)}")

    if not ADMIN_WALLET_ADDRESS:
        raise HTTPException(status_code=500, detail="管理员钱包地址未配置")

    try:
        w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
        balance_wei = w3.eth.get_balance(ADMIN_WALLET_ADDRESS)
        balance_eth = w3.from_wei(balance_wei, "ether")
        return {
            "cid": cid,
            "address": ADMIN_WALLET_ADDRESS,
            "balance_eth": float(balance_eth),
            "balance_wei": str(balance_wei),
            "updated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取余额失败: {str(e)}")


@router.get("/transaction-logs")
async def get_transaction_logs(
    election_address: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(TransactionLog)
    count_query = select(func.count()).select_from(TransactionLog)

    if election_address:
        lowered = election_address.lower()
        query = query.where(TransactionLog.election_address == lowered)
        count_query = count_query.where(TransactionLog.election_address == lowered)

    if status:
        query = query.where(TransactionLog.status == status)
        count_query = count_query.where(TransactionLog.status == status)

    logs = (await db.scalars(query.order_by(desc(TransactionLog.created_at)).offset(offset).limit(limit))).all()
    total = await db.scalar(count_query)

    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "tx_hash": log.tx_hash,
                "election_address": log.election_address,
                "operation_type": log.operation_type,
                "gas_used": log.gas_used,
                "gas_price": log.gas_price,
                "total_cost": log.total_cost,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "memo": log.memo,
            }
            for log in logs
        ],
    }


@router.get("/security-logs")
async def get_security_logs(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    election_address: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(SecurityLog)
    count_query = select(func.count()).select_from(SecurityLog)

    if event_type:
        query = query.where(SecurityLog.event_type == event_type)
        count_query = count_query.where(SecurityLog.event_type == event_type)

    if severity:
        query = query.where(SecurityLog.severity == severity)
        count_query = count_query.where(SecurityLog.severity == severity)

    if election_address:
        lowered = election_address.lower()
        query = query.where(SecurityLog.election_address == lowered)
        count_query = count_query.where(SecurityLog.election_address == lowered)

    logs = (await db.scalars(query.order_by(desc(SecurityLog.created_at)).offset(offset).limit(limit))).all()
    total = await db.scalar(count_query)

    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "student_id": log.student_id,
                "election_address": log.election_address,
                "details": log.details,
                "severity": log.severity,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


@router.post("/log-transaction")
async def log_transaction(req: LogTransactionRequest, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.scalar(select(TransactionLog).where(TransactionLog.tx_hash == req.tx_hash))
        if existing:
            existing.status = req.status
            if req.gas_used is not None:
                existing.gas_used = req.gas_used
            if req.gas_price is not None:
                existing.gas_price = req.gas_price
            if req.total_cost is not None:
                existing.total_cost = req.total_cost
            if req.memo is not None:
                existing.memo = req.memo
            await db.commit()
            return {"success": True, "message": "交易日志已更新"}

        log = TransactionLog(
            tx_hash=req.tx_hash,
            election_address=req.election_address.lower(),
            operation_type=req.operation_type,
            gas_used=req.gas_used,
            gas_price=req.gas_price,
            total_cost=req.total_cost,
            status=req.status,
            memo=req.memo,
        )
        db.add(log)
        await db.commit()
        return {"success": True, "message": "交易日志已记录"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-security")
async def log_security(req: LogSecurityRequest, db: AsyncSession = Depends(get_db)):
    try:
        log = SecurityLog(
            event_type=req.event_type,
            student_id=req.student_id,
            election_address=req.election_address.lower() if req.election_address else None,
            details=req.details,
            severity=req.severity,
        )
        db.add(log)
        await db.commit()
        return {"success": True, "message": "安全日志已记录"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-data")
async def debug_data(db: AsyncSession = Depends(get_db)):
    """DEBUG ENDPOINT: Show all elections and ElectionVoter mappings"""
    try:
        # Get all elections
        all_elections = (await db.scalars(select(Election))).all()
        
        # Get count of ElectionVoter records
        total_election_voters = await db.scalar(select(func.count()).select_from(ElectionVoter))
        
        # Get student 2025001's assignments
        student_2025001_elections = (await db.scalars(
            select(ElectionVoter).where(ElectionVoter.student_id == "2025001")
        )).all()
        
        # Get all unique students
        unique_students = (await db.scalars(
            select(ElectionVoter.student_id).distinct()
        )).all()
        
        return {
            "total_elections_in_db": len(all_elections),
            "elections": [
                {
                    "contract_address": e.contract_address,
                    "start_time": e.start_time,
                    "end_time": e.end_time,
                }
                for e in all_elections
            ],
            "total_election_voters": total_election_voters,
            "student_2025001_count": len(student_2025001_elections),
            "student_2025001_elections": [
                {
                    "student_id": ev.student_id,
                    "election_address": ev.election_address,
                }
                for ev in student_2025001_elections
            ],
            "total_unique_students": len(unique_students),
            "sample_students": unique_students[:5] if unique_students else [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调试数据获取失败: {str(e)}")
