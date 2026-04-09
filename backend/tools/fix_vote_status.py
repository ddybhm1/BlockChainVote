#!/usr/bin/env python3
"""
为学生 2025001 补充投票记录
直接在数据库中插入投票记录，因为他已经有 NFT Badge
"""
import asyncio
import sys
from datetime import datetime

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))

from database import AsyncSession, engine
from models import ClaimedTicket
from sqlalchemy import select

async def main():
    print("="*80)
    print("补充投票记录到数据库")
    print("="*80)
    
    target_student = "2025001"
    target_project = "0x7d1a34a4925a7c24c16d76fbf115376435794128"
    
    async with AsyncSession(engine) as db:
        print(f"\n【第1步】检查现有记录...")
        existing_ticket = await db.scalar(
            select(ClaimedTicket).where(
                ClaimedTicket.student_id == target_student,
                ClaimedTicket.election_address == target_project
            )
        )
        
        if existing_ticket:
            print(f"  找到现有记录:")
            print(f"    - 状态: {existing_ticket.status}")
            print(f"    - 领票交易: {existing_ticket.tx_hash}")
            print(f"    - 投票交易: {existing_ticket.vote_tx_hash}")
            
            if existing_ticket.status == "VOTED":
                print(f"  ✓ 已经是 VOTED 状态，无需修改")
                return
            else:
                # 更新为 VOTED
                print(f"\n【第2步】更新为 VOTED 状态...")
                existing_ticket.status = "VOTED"
                existing_ticket.updated_at = datetime.utcnow()
                await db.commit()
                print(f"  ✓ 已更新为 VOTED")
        else:
            print(f"  未找到现有记录，将创建新记录")
            
            # 创建新记录
            print(f"\n【第2步】创建新投票记录...")
            new_ticket = ClaimedTicket(
                student_id=target_student,
                election_address=target_project,
                status="VOTED",  # 直接标记为已投票
                tx_hash=None,    # NFT Badge 表示已投票，但没有具体交易
                vote_tx_hash=None,
                updated_at=datetime.utcnow(),
            )
            db.add(new_ticket)
            await db.commit()
            print(f"  ✓ 已创建投票记录")
        
        # 验证
        print(f"\n【第3步】验证...")
        ticket = await db.scalar(
            select(ClaimedTicket).where(
                ClaimedTicket.student_id == target_student,
                ClaimedTicket.election_address == target_project
            )
        )
        print(f"  学号: {ticket.student_id}")
        print(f"  项目: {ticket.election_address}")
        print(f"  状态: {ticket.status}")
        print(f"  ✓ 验证成功")

print("="*80)
asyncio.run(main())
print("="*80)
print("\n现在刷新前端，应该会显示 '已投票' 状态!")
