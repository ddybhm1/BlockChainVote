#!/usr/bin/env python3
"""
检查工厂合约下的子合约，以及学生在这些子合约中的分配情况
"""
import asyncio
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))

from services.blockchain import fetch_factory_elections
from database import get_db, AsyncSession, engine
from models import Election, ElectionVoter
from sqlalchemy import select, func
from datetime import datetime

async def main():
    print("="*80)
    print("工厂合约子合约与学生分配检查")
    print("="*80)
    
    # 第一步：从工厂合约获取所有子合约
    print("\n【第1步】从工厂合约获取所有子合约...")
    try:
        factory_elections = fetch_factory_elections()
        factory_addresses = {e['address'].lower() for e in factory_elections}
        print(f"  ✓ 工厂合约中有 {len(factory_addresses)} 个子合约")
        
        if factory_elections:
            print("\n  工厂中的子合约列表:")
            for i, election in enumerate(factory_elections[:5], 1):
                print(f"    {i}. {election['address']} | {election.get('title', '未命名')}")
            if len(factory_elections) > 5:
                print(f"    ... 还有 {len(factory_elections) - 5} 个")
    except Exception as e:
        print(f"  ✗ 从工厂合约获取失败: {e}")
        factory_addresses = set()
    
    # 第二步：从数据库检查 Elections 表
    print("\n【第2步】检查数据库中的 Elections...")
    async with AsyncSession(engine) as db:
        try:
            all_elections = (await db.scalars(select(Election))).all()
            db_addresses = {e.contract_address.lower() for e in all_elections}
            print(f"  ✓ 数据库中有 {len(db_addresses)} 个 Elections")
            
            # 检查一致性
            in_factory_not_in_db = factory_addresses - db_addresses
            in_db_not_in_factory = db_addresses - factory_addresses
            
            if in_factory_not_in_db:
                print(f"\n  ⚠ 在工厂中但不在数据库的合约 ({len(in_factory_not_in_db)} 个):")
                for addr in sorted(in_factory_not_in_db)[:3]:
                    print(f"    - {addr}")
                if len(in_factory_not_in_db) > 3:
                    print(f"    ... 还有 {len(in_factory_not_in_db) - 3} 个")
            
            if in_db_not_in_factory:
                print(f"\n  ⚠ 在数据库中但不在工厂的合约 ({len(in_db_not_in_factory)} 个):")
                for addr in sorted(in_db_not_in_factory)[:3]:
                    print(f"    - {addr}")
                if len(in_db_not_in_factory) > 3:
                    print(f"    ... 还有 {len(in_db_not_in_factory) - 3} 个")
            
            if not in_factory_not_in_db and not in_db_not_in_factory:
                print("\n  ✓ 数据库和工厂合约的 Elections 完全一致")
        except Exception as e:
            print(f"  ✗ 查询数据库失败: {e}")
            return
        
        # 第三步：检查学生 2025001 的分配
        print("\n【第3步】检查学生 2025001 的分配...")
        try:
            student_voters = (await db.scalars(
                select(ElectionVoter).where(ElectionVoter.student_id == "2025001")
            )).all()
            
            student_addresses = {ev.election_address.lower() for ev in student_voters}
            print(f"  ✓ 学生 2025001 被分配到 {len(student_addresses)} 个合约")
            
            # 检查学生分配的合约是否都在工厂中
            student_not_in_factory = student_addresses - factory_addresses
            
            if student_not_in_factory:
                print(f"\n  ⚠ 学生被分配但不在工厂的合约 ({len(student_not_in_factory)} 个):")
                for addr in sorted(student_not_in_factory):
                    print(f"    - {addr}")
            else:
                print(f"\n  ✓ 学生被分配的所有合约都在工厂中")
            
            # 显示学生分配的合约详情
            print("\n  学生 2025001 被分配到的合约:")
            for i, student_voter in enumerate(sorted(student_voters, key=lambda x: x.election_address)[:10], 1):
                election = next((e for e in all_elections if e.contract_address.lower() == student_voter.election_address.lower()), None)
                title = election.title if election and election.title else "未命名"
                print(f"    {i}. {student_voter.election_address[-8:]}... | {title}")
            
            if len(student_voters) > 10:
                print(f"    ... 还有 {len(student_voters) - 10} 个")
        except Exception as e:
            print(f"  ✗ 查询学生分配失败: {e}")
            return
        
        # 第四步：汇总
        print("\n【第4步】数据一致性检查...")
        
        in_factory_not_in_student = factory_addresses - student_addresses
        in_student_not_in_factory = student_addresses - factory_addresses
        
        print(f"\n  统计对比:")
        print(f"    - 工厂中的合约总数: {len(factory_addresses)}")
        print(f"    - 数据库中的合约总数: {len(db_addresses)}")
        print(f"    - 学生被分配的合约数: {len(student_addresses)}")
        print(f"    - 工厂中但学生未被分配的: {len(in_factory_not_in_student)}")
        
        if not in_student_not_in_factory and len(student_addresses) <= len(factory_addresses):
            print("\n  ✅ 数据一致性检查通过!")
            print(f"     学生被分配的所有合约都在工厂中")
        else:
            print("\n  ⚠ 数据一致性有问题")
            if in_student_not_in_factory:
                print(f"    学生被分配但未在工厂的合约: {in_student_not_in_factory}")

print("="*80)
asyncio.run(main())
print("="*80)
