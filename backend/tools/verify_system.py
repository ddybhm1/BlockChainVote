#!/usr/bin/env python3
"""
完整系统验证脚本 - 检查学生是否只看到分配的项目
"""
import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:8000'

print("="*70)
print("区块链投票系统 - 数据过滤验证")
print("="*70)

# 第一步：获取调试数据
print("\n【第1步】检查数据库状态...")
try:
    debug_response = requests.get(f'{BASE_URL}/api/admin/debug-data')
    debug_data = debug_response.json()
    
    print(f"  ✓ 数据库中有 {debug_data['total_elections_in_db']} 个Elections")
    print(f"  ✓ ElectionVoter 记录总数: {debug_data['total_election_voters']}")
    print(f"  ✓ 学生 2025001 被分配到: {debug_data['student_2025001_count']} 个项目")
    
    student_elections = {e['election_address'] for e in debug_data['student_2025001_elections']}
    print(f"  ✓ 独特学生数: {debug_data['total_unique_students']}")
except Exception as e:
    print(f"  ✗ 调试端点失败: {e}")
    exit(1)

# 第二步：登录
print("\n【第2步】学生登录...")
try:
    login_response = requests.post(
        f'{BASE_URL}/api/auth/login',
        json={'student_id': '2025001', 'password': '123456'}
    )
    login_data = login_response.json()
    
    if login_response.status_code != 200 or not login_data.get('success'):
        print(f"  ✗ 登录失败: {login_data}")
        exit(1)
    
    token = login_data.get('token')
    print(f"  ✓ 学号 2025001 登录成功")
    print(f"  ✓ Token 有效期: {login_data['expires_in_hours']} 小时")
except Exception as e:
    print(f"  ✗ 登录失败: {e}")
    exit(1)

# 第三步：获取学生的项目列表
print("\n【第3步】获取学生的项目列表...")
try:
    headers = {'Authorization': f'Bearer {token}'}
    elections_response = requests.get(
        f'{BASE_URL}/api/auth/my-elections',
        headers=headers
    )
    
    if elections_response.status_code != 200:
        print(f"  ✗ 获取项目列表失败: {elections_response.text}")
        exit(1)
    
    elections_data = elections_response.json()
    
    if not isinstance(elections_data, list):
        print(f"  ✗ 返回数据格式错误: {type(elections_data)}")
        exit(1)
    
    returned_count = len(elections_data)
    print(f"  ✓ API 返回 {returned_count} 个项目")
    
except Exception as e:
    print(f"  ✗ 获取项目列表失败: {e}")
    exit(1)

# 第四步：验证数据一致性
print("\n【第4步】验证数据一致性...")

# 检查返回的项目是否都在学生的分配项目中
returned_elections = {e['election_address'].lower() for e in elections_data}
assigned_elections_lower = {addr.lower() for addr in student_elections}

missing = assigned_elections_lower - returned_elections
extra = returned_elections - assigned_elections_lower

if missing:
    print(f"  ⚠ 缺少的项目地址: {missing}")

if extra:
    print(f"  ⚠ 额外的项目地址: {extra}")

if not missing and not extra:
    print(f"  ✓ 返回的项目与分配的项目完全匹配")

# 第五步：分析项目状态
print("\n【第5步】分析项目状态...")

status_count = {}
phase_count = {}

for election in elections_data:
    status = election['status']
    phase = election['phase']
    
    status_count[status] = status_count.get(status, 0) + 1
    phase_count[phase] = phase_count.get(phase, 0) + 1

print(f"  按状态统计:")
for status, count in sorted(status_count.items()):
    print(f"    - {status}: {count}")

print(f"  按阶段统计:")
for phase, count in sorted(phase_count.items()):
    print(f"    - {phase}: {count}")

# 最终结果
print("\n" + "="*70)
if not missing and not extra and returned_count == debug_data['student_2025001_count']:
    print("✅ 验证成功！学生现在只看到被分配的项目。")
    print(f"   预期: {debug_data['student_2025001_count']} 项目")
    print(f"   实际: {returned_count} 项目")
else:
    print("⚠ 验证有警告")
    print(f"   预期: {debug_data['student_2025001_count']} 项目")
    print(f"   实际: {returned_count} 项目")

print("="*70)

# 详细项目列表
print("\n【项目详情】:")
for i, election in enumerate(elections_data, 1):
    print(f"  {i}. {election['title']:<20} | 状态: {election['status']:<10} | 阶段: {election['phase']:<8}")
