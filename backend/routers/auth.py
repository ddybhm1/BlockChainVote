"""认证路由 - KYC 身份验证与匿名授权"""
import re
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
import bcrypt

from database import get_db
from models import Voter, ClaimedTicket, ElectionVoter, SecurityLog
from services.blockchain import authorize_voter_on_chain

router = APIRouter(prefix="/api/auth", tags=["认证"])


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
async def claim_ticket(req: ClaimTicketRequest, db: Session = Depends(get_db)):
    """
    选民领票：验证身份后授权匿名地址到指定投票项目。
    流程：
    1. MySQL 校验学号与密码
    2. 检查该学号是否已在该项目中领票（ClaimedTicket 表）
    3. 记录领票
    4. 调用智能合约授权匿名地址
    5. 丢弃地址，不留映射
    """
    # 1. 查询选民
    voter = db.query(Voter).filter(Voter.student_id == req.student_id).first()
    if not voter:
        raise HTTPException(status_code=401, detail="学号不存在")

    # 2. 验证密码
    if not bcrypt.checkpw(
        req.password.encode("utf-8"), voter.password_hash.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="密码错误")

    # 3. 检查是否已在该项目中领票
    in_election = db.query(ElectionVoter).filter(
        ElectionVoter.student_id == req.student_id,
        ElectionVoter.election_address == req.election_address.lower(),
    ).first()
    if not in_election:
        raise HTTPException(status_code=403, detail="该学号不在当前投票项目的选民名单中")

    # 4. 检查是否已在该项目中领票
    existing = db.query(ClaimedTicket).filter(
        ClaimedTicket.student_id == req.student_id,
        ClaimedTicket.election_address == req.election_address.lower(),
    ).first()
    if existing:
        # 记录重复领票的安全事件
        sec_log = SecurityLog(
            event_type="duplicate_claim",
            student_id=req.student_id,
            election_address=req.election_address.lower(),
            details=f"学号 {req.student_id} 尝试重复领票（投票项目 {req.election_address[:10]}...）",
            severity="warning"
        )
        db.add(sec_log)
        db.commit()
        raise HTTPException(status_code=409, detail="该学号已在此投票项目中领取过投票资格，不可重复领票")

    # 5. 记录领票（先记录，防止并发漏洞）
    ticket = ClaimedTicket(
        student_id=req.student_id,
        election_address=req.election_address.lower(),
    )
    db.add(ticket)
    db.commit()

    # 6. 链上授权匿名地址到指定项目合约
    try:
        tx_hash = await authorize_voter_on_chain(req.wallet_address, req.election_address)
    except Exception as e:
        # 链上失败则回滚领票记录
        db.delete(ticket)
        db.commit()
        raise HTTPException(status_code=500, detail=f"链上授权失败: {str(e)}")

    # 7. 函数结束，wallet_address 自动离开作用域被回收，不留任何映射
    return ClaimTicketResponse(
        success=True,
        message="投票资格已授权，请使用该钱包地址进行投票",
        tx_hash=tx_hash,
    )
