"""初始化数据库表结构，并插入测试选民数据"""
import bcrypt
from database import engine, SessionLocal, Base
from models import Voter, ClaimedTicket


def init():
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表已创建")

    # 插入测试数据
    db = SessionLocal()
    test_voters = [
        ("2024001", "pass123"),
        ("2024002", "pass456"),
        ("2024003", "pass789"),
    ]
    for sid, pwd in test_voters:
        if not db.query(Voter).filter(Voter.student_id == sid).first():
            hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt())
            db.add(Voter(student_id=sid, password_hash=hashed.decode("utf-8")))
            print(f"  已添加测试选民: {sid}")
    db.commit()
    db.close()
    print("初始化完成")


if __name__ == "__main__":
    init()
