"""初始化投票数据库和测试数据"""
import asyncio

import bcrypt
from sqlalchemy import select

from database import engine, SessionLocal, Base
from models import Voter


async def init():
    # 初始化数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表已创建")

    # 初始化测试用户数据
    db = SessionLocal()
    test_voters = [
        ("2024001", "pass123"),
        ("2024002", "pass456"),
        ("2024003", "pass789"),
    ]
    try:
        for sid, pwd in test_voters:
            existing = await db.scalar(select(Voter).where(Voter.student_id == sid))
            if not existing:
                hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt())
                db.add(Voter(student_id=sid, password_hash=hashed.decode("utf-8")))
                print(f"  添加测试用户: {sid}")
        await db.commit()
    finally:
        await db.close()
    print("测试用户初始化完成")


if __name__ == "__main__":
    asyncio.run(init())
