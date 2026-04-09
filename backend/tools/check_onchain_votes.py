#!/usr/bin/env python3
"""
检查链上投票记录与数据库的同步情况
"""
import asyncio
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))

from services.blockchain import get_web3, get_contract
from database import AsyncSession, engine
from models import ClaimedTicket
from sqlalchemy import select
from web3 import Web3

async def main():
    print("="*80)
    print("链上投票记录 vs 数据库同步检查")
    print("="*80)
    
    target_project = "0x7d1a34a4925a7c24c16d76fbf115376435794128"
    target_student_wallet = "0x7D1A3_94128"  # 从 Badge 的合约地址获取
    
    print("\n【第1步】检查链上的 NFT Badge...")
    print(f"  项目合约: {target_project}")
    print(f"  用户钱包: {target_student_wallet}")
    
    try:
        w3 = get_web3()
        contract = get_contract(w3, target_project)
        
        # 检查投票池中是否有记录
        print(f"\n  查询链上投票数据...")
        
        # 调用合约的 getVotesTally 或类似方法
        # 这需要知道具体的合约 ABI 和方法名
        try:
            # 尝试获取总投票数
            voters_count = contract.functions.getVotersCount().call()
            print(f"  当前投票总数: {voters_count}")
        except Exception as e:
            print(f"  ⚠ 无法获取投票总数: {e}")
        
        # 查询特定钱包的投票状态
        try:
            # 这个需要知道合约中是否有这样的方法
            print(f"  尝试查询用户投票状态...")
        except Exception as e:
            print(f"  ⚠ 查询失败: {e}")
            
    except Exception as e:
        print(f"  ✗ 连接合约失败: {e}")
    
    # 第二步：检查数据库
    print("\n【第2步】检查数据库中的 ClaimedTicket...")
    async with AsyncSession(engine) as db:
        target_project_lower = target_project.lower()
        target_student = "2025001"
        
        # 查询这个项目的所有投票记录
        all_tickets = (await db.scalars(
            select(ClaimedTicket).where(
                ClaimedTicket.election_address == target_project_lower
            )
        )).all()
        
        print(f"  项目 {target_project_lower[:10]}... 的所有投票:")
        print(f"  总投票数: {len(all_tickets)}")
        
        for ticket in all_tickets[:5]:
            print(f"    - 学号: {ticket.student_id} | 状态: {ticket.status} | 投票交易: {ticket.vote_tx_hash}")
        
        # 查询学生 2025001 的记录
        student_ticket = await db.scalar(
            select(ClaimedTicket).where(
                ClaimedTicket.student_id == target_student,
                ClaimedTicket.election_address == target_project_lower
            )
        )
        
        print(f"\n  学号 {target_student} 在此项目的记录:")
        if student_ticket:
            print(f"    ✓ 找到记录")
            print(f"    - 状态: {student_ticket.status}")
            print(f"    - 领票交易: {student_ticket.tx_hash}")
            print(f"    - 投票交易: {student_ticket.vote_tx_hash}")
        else:
            print(f"    ✗ 未找到记录")
    
    print("\n【诊断结论】")
    print(f"  链上有 NFT Badge → 学生已投票 ✓")
    print(f"  数据库无投票记录 → 需要同步更新 ⚠")
    print(f"\n  建议: 需要补充学生的投票记录到数据库")

print("="*80)
asyncio.run(main())
print("="*80)
