from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint, DateTime, Float, Text, BigInteger
from database import Base
from datetime import datetime

# ========== 投票项目表 ========== #
class Election(Base):
    """投票项目表 - 存储合约地址及投票时间窗口"""
    __tablename__ = "elections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_address = Column(String(42), unique=True, nullable=False, index=True)
    start_time = Column(BigInteger, nullable=False)
    end_time = Column(BigInteger, nullable=False)
    # 可扩展：项目名称、描述等

class Voter(Base):
    """选民表 - 仅存储身份校验信息，绝不存储钱包地址"""
    __tablename__ = "voters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    has_claimed = Column(Boolean, default=False, nullable=False)


class ClaimedTicket(Base):
    """领票记录表 - 按投票项目跟踪每个学生的领票状态"""
    __tablename__ = "claimed_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), nullable=False, index=True)
    election_address = Column(String(42), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("student_id", "election_address", name="uq_student_election"),
    )


class ElectionVoter(Base):
    """项目选民名单表 - 约束每个项目可参与投票的学号范围"""
    __tablename__ = "election_voters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), nullable=False, index=True)
    election_address = Column(String(42), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("student_id", "election_address", name="uq_election_voter"),
    )


class TransactionLog(Base):
    """交易日志表 - 记录Gas费用、交易哈希等链上操作"""
    __tablename__ = "transaction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(255), unique=True, nullable=False, index=True)
    election_address = Column(String(42), nullable=False, index=True)
    operation_type = Column(String(50), nullable=False)  # authorize_voter, add_candidate, start_voting, end_voting
    gas_used = Column(Integer, nullable=True)  # Gas消耗量
    gas_price = Column(Float, nullable=True)  # Gas价格（wei）
    total_cost = Column(String(50), nullable=True)  # 总消耗（wei）
    status = Column(String(20), nullable=False, index=True)  # success, pending, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    memo = Column(Text, nullable=True)


class SecurityLog(Base):
    """安全日志表 - 记录攻击尝试、重复领票等异常"""
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)  # duplicate_claim, invalid_voter, contract_rejection, etc.
    student_id = Column(String(20), nullable=True, index=True)
    election_address = Column(String(42), nullable=True, index=True)
    details = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, critical
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
