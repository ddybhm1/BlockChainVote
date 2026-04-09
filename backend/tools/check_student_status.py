#!/usr/bin/env python3
"""
检查学生 2025001 在项目 2025年学生会主席选举 的投票状态
"""
import asyncio
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))

from database import AsyncSession, engine
from models import ClaimedTicket, Election
from sqlalchemy import select

async def main():
    print("="*80)
    print("学生投票状态检查")
    print("="*80)
    
    target_project = "0x7d1a34a4925a7c24c16d76fbf115376435794128"
    target_student = "2025001"
    
    async with AsyncSession(engine) as db:
        # 查询这个项目的 Election 信息
        election = await db.scalar(
            select(Election).where(
                Election.contract_address == target_project
            )
        )
        
        if election:
            print(f"\n【项目信息】")
            print(f"  合约地址: {election.contract_address}")
            print(f"  标题: {election.title}")
            print(f"  开始时间: {election.start_time}")
            print(f"  结束时间: {election.end_time}")
        else:
            print(f"  ✗ 项目未找到")
        
        # 查询学生的 ClaimedTicket 记录
        ticket = await db.scalar(
            select(ClaimedTicket).where(
                ClaimedTicket.student_id == target_student,
                ClaimedTicket.election_address == target_project
            )
        )
        
        print(f"\n【学生 {target_student} 的投票状态】")
        if ticket:
            print(f"  ✓ 找到投票记录")
            print(f"    - 学号: {ticket.student_id}")
            print(f"    - 项目: {ticket.election_address}")
            print(f"    - 状态: {ticket.status}")
            print(f"    - 领票交易: {ticket.tx_hash}")
            print(f"    - 投票交易: {ticket.vote_tx_hash}")
            print(f"    - 更新时间: {ticket.updated_at}")
        else:
            print(f"  ✗ 未找到投票记录")
        
        # 查询所有的 ClaimedTicket 记录统计
        print(f"\n【整体统计】")
        all_tickets = (await db.scalars(select(ClaimedTicket))).all()
        print(f"  总 ClaimedTicket 记录: {len(all_tickets)}")
        
        student_tickets = [t for t in all_tickets if t.student_id == target_student]
        print(f"  学生 {target_student} 的投票记录: {len(student_tickets)}")
        
        if student_tickets:
            print(f"\n  学生 {target_student} 的所有投票:")
            for t in student_tickets[:5]:
                print(f"    - {t.election_address[:10]}... | 状态: {t.status}")
            if len(student_tickets) > 5:
                print(f"    ... 还有 {len(student_tickets) - 5} 条")

print("="*80)
asyncio.run(main())
print("="*80)
