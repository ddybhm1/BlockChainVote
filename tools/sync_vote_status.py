#!/usr/bin/env python3
"""
同步学生的链上投票状态到数据库
"""
import requests
import json

BASE_URL = 'http://localhost:8000'

print("="*80)
print("同步学生投票状态到数据库")
print("="*80)

# 学生信息
target_student = "2025001"
target_project = "0x7d1a34a4925a7c24c16d76fbf115376435794128"

print(f"\n【第1步】登录学生 {target_student}...")
login_response = requests.post(
    f'{BASE_URL}/api/auth/login',
    json={'student_id': target_student, 'password': '123456'}
)
login_data = login_response.json()

if not login_data.get('success'):
    print(f"  ✗ 登录失败")
    exit(1)

token = login_data.get('token')
headers = {'Authorization': f'Bearer {token}'}
print(f"  ✓ 登录成功")

print(f"\n【第2步】获取学生的投票信息...")
elections_response = requests.get(
    f'{BASE_URL}/api/auth/my-elections',
    headers=headers
)
elections_data = elections_response.json()

# 找到目标项目
target_election = None
for election in elections_data:
    if election['election_address'].lower() == target_project.lower():
        target_election = election
        break

if not target_election:
    print(f"  ✗ 未找到项目 {target_project}")
    exit(1)

print(f"  ✓ 找到项目: {target_election['title']}")
print(f"    - 状态: {target_election['status']}")
print(f"    - 领票交易: {target_election['claim_tx_hash']}")
print(f"    - 投票交易: {target_election['vote_tx_hash']}")

if target_election['status'] == 'VOTED':
    print(f"  ✓ 项目已经标记为已投票，无需更新")
    exit(0)

# 需要提供钱包地址和投票交易哈希
print(f"\n【第3步】需要提供以下信息来标记投票...")
print(f"  提示: 你的投票交易哈希可以从 Etherscan 或钱包中查看")
print(f"  提示: 格式示例: 0x1234567890abcdef...")

# 从用户输入获取
wallet_address = input(f"  请输入你的钱包地址: ").strip()
if not wallet_address or not wallet_address.startswith('0x'):
    print(f"  ✗ 无效的钱包地址")
    exit(1)

vote_tx_hash = input(f"  请输入投票交易哈希: ").strip()
if not vote_tx_hash or not vote_tx_hash.startswith('0x'):
    print(f"  ✗ 无效的交易哈希")
    exit(1)

print(f"\n【第4步】调用 mark-voted 端点...")
mark_voted_response = requests.post(
    f'{BASE_URL}/api/auth/mark-voted',
    headers=headers,
    json={
        'election_address': target_project,
        'wallet_address': wallet_address,
        'tx_hash': vote_tx_hash
    }
)

if mark_voted_response.status_code != 200:
    print(f"  ✗ 标记失败: {mark_voted_response.text}")
    exit(1)

result = mark_voted_response.json()
print(f"  ✓ 标记成功!")
print(f"    - {result.get('message', '')}")
print(f"    - 新状态: {result.get('status', '')}")

print(f"\n【第5步】验证更新...")
elections_response = requests.get(
    f'{BASE_URL}/api/auth/my-elections',
    headers=headers
)
elections_data = elections_response.json()

for election in elections_data:
    if election['election_address'].lower() == target_project.lower():
        print(f"  ✓ 项目状态已更新: {election['status']}")
        if election['status'] == 'VOTED':
            print(f"  ✓ 前端将显示: 已投票 ✓")
        break

print("\n" + "="*80)
print("✅ 同步完成!")
print("="*80)
