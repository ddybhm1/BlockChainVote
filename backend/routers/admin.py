"""管理路由 - 选民注册、IPFS 上传、财务监控"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import desc
import bcrypt
import re
from datetime import datetime
import io
import openpyxl
from web3 import Web3

from database import get_db
from models import Voter, ClaimedTicket, ElectionVoter, TransactionLog, SecurityLog
from services.ipfs import pin_file_to_ipfs
from config import ADMIN_WALLET_ADDRESS, SEPOLIA_RPC

router = APIRouter(prefix="/api/admin", tags=["管理"])

# 配置独立的业务日志
admin_logger = logging.getLogger("admin_logger")
admin_logger.setLevel(logging.INFO)
if not admin_logger.handlers:
    fh = logging.FileHandler("app_business.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    admin_logger.addHandler(fh)


class RegisterVoterRequest(BaseModel):
    student_id: str
    password: str
    election_address: str

    @field_validator("election_address")
    @classmethod
    def validate_election_address(cls, v: str) -> str:
        if not re.match(r"^0x[0-9a-fA-F]{40}$", v):
            raise ValueError("无效的投票项目合约地址格式")
        return v.lower()


class RegisterVoterResponse(BaseModel):
    success: bool
    message: str


class LogTransactionRequest(BaseModel):
    tx_hash: str
    election_address: str
    operation_type: str  # authorize_voter, add_candidate, start_voting, end_voting
    gas_used: Optional[int] = None
    gas_price: Optional[float] = None
    total_cost: Optional[str] = None
    status: str = "pending"  # success, pending, failed
    memo: Optional[str] = None

    @field_validator("election_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not re.match(r"^0x[0-9a-fA-F]{40}$", v):
            raise ValueError("无效地址格式")
        return v.lower()


class LogSecurityRequest(BaseModel):
    event_type: str
    student_id: Optional[str] = None
    election_address: Optional[str] = None
    details: str
    severity: str = "warning"  # info, warning, critical


@router.post("/register-voter", response_model=RegisterVoterResponse)
async def register_voter(req: RegisterVoterRequest, db: Session = Depends(get_db)):
    """注册项目选民到 MySQL（管理员操作，用于录入某个投票项目的合法选民名单）"""
    student_id = req.student_id.strip()

    # 1) 维护全局身份凭据（同一学号只保留一套密码）
    voter = db.query(Voter).filter(Voter.student_id == student_id).first()
    if not voter:
        hashed = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt())
        voter = Voter(
            student_id=student_id,
            password_hash=hashed.decode("utf-8"),
            has_claimed=False,
        )
        db.add(voter)
    else:
        if not bcrypt.checkpw(req.password.encode("utf-8"), voter.password_hash.encode("utf-8")):
            raise HTTPException(status_code=409, detail="该学号已存在且密码不一致")

    # 2) 维护项目级选民名单
    existing_mapping = db.query(ElectionVoter).filter(
        ElectionVoter.student_id == student_id,
        ElectionVoter.election_address == req.election_address,
    ).first()
    if existing_mapping:
        raise HTTPException(status_code=409, detail="该学号已注册到当前投票项目")

    db.add(ElectionVoter(student_id=student_id, election_address=req.election_address))
    db.commit()

    return RegisterVoterResponse(success=True, message="选民注册成功（已加入当前项目白名单）")


@router.post("/upload-voters-excel")
async def upload_voters_excel(
    election_address: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """通过 Excel 批量导入全校学生并注册到项目中"""
    if not re.match(r"^0x[0-9a-fA-F]{40}$", election_address):
        raise HTTPException(status_code=400, detail="无效的投票项目合约地址格式")
    election_address = election_address.lower()

    if not file.filename.endswith(('.xlsx', '.xls')):
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

        # 1) 维持全局选民
        voter = db.query(Voter).filter(Voter.student_id == student_id).first()
        if not voter:
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            voter = Voter(
                student_id=student_id,
                password_hash=hashed.decode("utf-8"),
                has_claimed=False,
            )
            db.add(voter)
            db.flush() # flush to avoid conflicting in session, although logically safe
        else:
            if not bcrypt.checkpw(password.encode("utf-8"), voter.password_hash.encode("utf-8")):
                errors.append(f"第 {i} 行: 学号 {student_id} 已存在但密码不匹配")
                continue

        # 2) 维护项目级名单
        existing_mapping = db.query(ElectionVoter).filter(
            ElectionVoter.student_id == student_id,
            ElectionVoter.election_address == election_address,
        ).first()
        if existing_mapping:
            duplicate_count += 1
            continue
        
        db.add(ElectionVoter(student_id=student_id, election_address=election_address))
        success_count += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(e)}")

    return {
        "success": True, 
        "message": f"导入完成。成功新增 {success_count} 人，已存在/跳过 {duplicate_count} 人。错误: {len(errors)} 条",
        "errors": errors
    }

@router.get("/voters-count")
async def get_voters_count(
    election_address: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取已注册和已领票的选民数量（支持按投票项目查询）"""
    if election_address:
        election_address = election_address.lower()
        total = db.query(ElectionVoter).filter(
            ElectionVoter.election_address == election_address
        ).count()
        claimed = db.query(ClaimedTicket).filter(
            ClaimedTicket.election_address == election_address
        ).count()
    else:
        total = db.query(Voter).count()
        claimed = db.query(ClaimedTicket).count()
    return {"total_registered": total, "total_claimed": claimed}


@router.post("/upload-ipfs")
async def upload_to_ipfs(file: UploadFile = File(...)):
    """上传文件到 IPFS（Pinata），返回 CID"""
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件大小不能超过 10MB")

    contents = await file.read()
    try:
        cid = pin_file_to_ipfs(contents, file.filename or "upload")
        admin_logger.info(f"[Web3Service] 管理员向区块链发起交易，成功将文件 {file.filename or 'upload'} 上传至 IPFS，CID: {cid}")
    except RuntimeError as e:
        admin_logger.error(f"[Web3Service] 管理员向 Web3 发起操作，IPFS 上传失败: {str(e)}")
    """获取管理员钱包的 ETH 余额"""
    if not ADMIN_WALLET_ADDRESS:
        raise HTTPException(status_code=500, detail="管理员钱包地址未配置")
    
    try:
        w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
        balance_wei = w3.eth.get_balance(ADMIN_WALLET_ADDRESS)
        balance_eth = w3.from_wei(balance_wei, "ether")
        
        return {
            "address": ADMIN_WALLET_ADDRESS,
            "balance_eth": float(balance_eth),
            "balance_wei": str(balance_wei),
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取余额失败: {str(e)}")


@router.get("/transaction-logs")
async def get_transaction_logs(
    election_address: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取交易日志（Gas费用记录）"""
    query = db.query(TransactionLog)
    
    if election_address:
        query = query.filter(TransactionLog.election_address == election_address.lower())
    
    if status:
        query = query.filter(TransactionLog.status == status)
    
    # 按创建时间倒序
    logs = query.order_by(desc(TransactionLog.created_at)).offset(offset).limit(limit).all()
    total = query.count()
    
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
                "memo": log.memo
            }
            for log in logs
        ]
    }


@router.get("/security-logs")
async def get_security_logs(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    election_address: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取安全日志（攻击拦截、重复领票等）"""
    query = db.query(SecurityLog)
    
    if event_type:
        query = query.filter(SecurityLog.event_type == event_type)
    
    if severity:
        query = query.filter(SecurityLog.severity == severity)
    
    if election_address:
        query = query.filter(SecurityLog.election_address == election_address.lower())
    
    # 按创建时间倒序
    logs = query.order_by(desc(SecurityLog.created_at)).offset(offset).limit(limit).all()
    total = query.count()
    
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
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    }


@router.post("/log-transaction")
async def log_transaction(req: LogTransactionRequest, db: Session = Depends(get_db)):
    """记录交易日志"""
    try:
        # 检查是否已存在
        existing = db.query(TransactionLog).filter(TransactionLog.tx_hash == req.tx_hash).first()
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
            db.commit()
            return {"success": True, "message": "交易日志已更新"}
        
        log = TransactionLog(
            tx_hash=req.tx_hash,
            election_address=req.election_address.lower(),
            operation_type=req.operation_type,
            gas_used=req.gas_used,
            gas_price=req.gas_price,
            total_cost=req.total_cost,
            status=req.status,
            memo=req.memo
        )
        db.add(log)
        db.commit()
        
        return {"success": True, "message": "交易日志已记录"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-security")
async def log_security(req: LogSecurityRequest, db: Session = Depends(get_db)):
    """记录安全事件"""
    try:
        log = SecurityLog(
            event_type=req.event_type,
            student_id=req.student_id,
            election_address=req.election_address.lower() if req.election_address else None,
            details=req.details,
            severity=req.severity
        )
        db.add(log)
        db.commit()
        
        return {"success": True, "message": "安全日志已记录"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
