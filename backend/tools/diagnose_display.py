#!/usr/bin/env python3
"""
完整诊断报告 - 学生状态和项目显示检查
"""
import requests
import json

BASE_URL = 'http://localhost:8000'

print("="*80)
print("学生 2025001 的完整诊断报告")
print("="*80)

# 登录
print("\n【第1步】登录学生 2025001...")
login_response = requests.post(
    f'{BASE_URL}/api/auth/login',
    json={'student_id': '2025001', 'password': '123456'}
)
token = login_response.json().get('token')
print(f"  ✓ 登录成功")

# 获取项目列表
headers = {'Authorization': f'Bearer {token}'}
elections_response = requests.get(
    f'{BASE_URL}/api/auth/my-elections',
    headers=headers
)
elections_data = elections_response.json()

print(f"\n【第2步】学生显示的项目列表...")
print(f"  总项目数: {len(elections_data)}")

# 统计各种状态
voted_count = 0
claimed_count = 0
active_count = 0
ended_count = 0
available_count = 0

for i, election in enumerate(elections_data, 1):
    print(f"\n  【项目 {i}】")
    print(f"    标题: {election['title']}")
    print(f"    地址: {election['election_address']}")
    print(f"    阶段 (phase): {election['phase']}")
    print(f"    状态 (status): {election['status']}")
    print(f"    领票交易 (claim_tx_hash): {election['claim_tx_hash']}")
    print(f"    投票交易 (vote_tx_hash): {election['vote_tx_hash']}")
    
    # 统计
    if election['phase'] == "ENDED":
        ended_count += 1
    if election['phase'] == "ACTIVE":
        active_count += 1
    
    if election['status'] == "VOTED":
        voted_count += 1
    elif election['status'] == "CLAIMED":
        claimed_count += 1
    elif election['status'] == "AVAILABLE":
        available_count += 1

print(f"\n【第3步】统计分析...")
print(f"  按阶段统计:")
print(f"    - ACTIVE (进行中): {active_count}")
print(f"    - ENDED (已结束): {ended_count}")
print(f"  按状态统计:")
print(f"    - VOTED (已投票): {voted_count}")
print(f"    - CLAIMED (已领票): {claimed_count}")
print(f"    - AVAILABLE (未参与): {available_count}")

print(f"\n【第4步】仪表板统计卡片数值...")
# 根据前端的计算逻辑
status_voted_or_ended = len([e for e in elections_data if e['phase'] == "ENDED" or e['status'] == "VOTED"])
print(f"  待投票项目(计算方式: AVAILABLE + CLAIMED): {available_count + claimed_count}")
print(f"  已完成项目(计算方式: ENDED or VOTED): {status_voted_or_ended}")
print(f"  全部项目: {len(elections_data)}")

print("\n【诊断结论】")
if len(elections_data) == 1:
    print(f"  ✓ 正确: 学生仅看到工厂合约中的 {len(elections_data)} 个项目")
    if elections_data[0]['status'] == "AVAILABLE":
        print(f"  ✓ 正确: 该项目状态为 AVAILABLE (未参与)")
        print(f"  → 这表示学生还没有在这个项目投票")
else:
    print(f"  ⚠ 异常: 学生显示了 {len(elections_data)} 个项目（预期应该是 1 个）")

print("\n" + "="*80)
