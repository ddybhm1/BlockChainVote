#!/usr/bin/env python3
"""
测试新的投票状态同步端点
"""
import requests
import json

BASE_URL = 'http://localhost:8000'

print("="*80)
print("测试投票状态同步端点")
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
token = login_data.get('token')
print(f"  ✓ 登录成功")

headers = {'Authorization': f'Bearer {token}'}

print(f"\n【第2步】查看当前投票状态...")
elections_response = requests.get(
    f'{BASE_URL}/api/auth/my-elections',
    headers=headers
)
elections_data = elections_response.json()

for election in elections_data:
    print(f"  项目: {election['title']}")
    print(f"  状态: {election['status']}")
    print(f"  投票交易: {election['vote_tx_hash']}")

print(f"\n【第3步】调用同步端点...")
sync_response = requests.post(
    f'{BASE_URL}/api/auth/sync-vote-status/{target_project}',
    headers=headers
)

if sync_response.status_code == 200:
    result = sync_response.json()
    print(f"  ✓ 同步成功!")
    print(f"    - {result.get('message', '')}")
    print(f"    - 新状态: {result.get('status', '')}")
else:
    print(f"  ✗ 同步失败: {sync_response.text}")
    exit(1)

print(f"\n【第4步】验证更新...")
elections_response = requests.get(
    f'{BASE_URL}/api/auth/my-elections',
    headers=headers
)
elections_data = elections_response.json()

for election in elections_data:
    if election['election_address'].lower() == target_project.lower():
        print(f"  项目: {election['title']}")
        print(f"  新状态: {election['status']}")
        if election['status'] == 'VOTED':
            print(f"  ✅ 前端将显示: 已投票！")
        break

print("\n" + "="*80)
