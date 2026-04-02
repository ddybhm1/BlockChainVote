#!/usr/bin/env python3
"""
诊断"去投票"按钮点击问题
检查路由和数据状态
"""
import requests
import json

BASE_URL = 'http://localhost:8000'

print("="*80)
print("诊断'去投票'按钮问题")
print("="*80)

# 学生信息
target_student = "2025003"
target_project = "0x7d1a34a4925a7c24c16d76fbf115376435794128"

print(f"\n【第1步】登录学生 {target_student}...")
login_response = requests.post(
    f'{BASE_URL}/api/auth/login',
    json={'student_id': target_student, 'password': '123456'}
)

if login_response.status_code != 200:
    print(f"  ✗ 登录失败")
    exit(1)

login_data = login_response.json()
token = login_data.get('token')
print(f"  ✓ 登录成功")

headers = {'Authorization': f'Bearer {token}'}

print(f"\n【第2步】获取学生的项目列表...")
elections_response = requests.get(
    f'{BASE_URL}/api/auth/my-elections',
    headers=headers
)

if elections_response.status_code != 200:
    print(f"  ✗ 获取项目列表失败")
    exit(1)

elections_data = elections_response.json()
print(f"  ✓ 成功获取 {len(elections_data)} 个项目")

for i, election in enumerate(elections_data, 1):
    print(f"\n  【项目 {i}】")
    print(f"    地址: {election['election_address']}")
    print(f"    标题: {election['title']}")
    print(f"    状态: {election['status']}")
    print(f"    阶段: {election['phase']}")

print(f"\n【第3步】验证 electionAddress 参数...")
if elections_data:
    target_election = elections_data[0]
    target_address = target_election['election_address']
    print(f"  ✓ 第一个项目地址: {target_address}")
    
    # 尝试调用 ticket-status 端点
    print(f"\n【第4步】通过 ticket-status 端点检查项目信息...")
    ticket_response = requests.get(
        f'{BASE_URL}/api/auth/ticket-status/{target_address}',
        headers=headers
    )
    
    if ticket_response.status_code == 200:
        print(f"  ✓ 端点返回成功")
        ticket_data = ticket_response.json()
        print(f"    状态: {ticket_data.get('status')}")
        print(f"    阶段: {ticket_data.get('phase')}")
    else:
        print(f"  ✗ 端点返回错误: {ticket_response.status_code}")
        print(f"    {ticket_response.text}")
else:
    print(f"  ✗ 没有项目数据")

print(f"\n【诊断结论】")
print(f"  如果 API 返回成功，那么路由问题可能是：")
print(f"  1. 前端路由跳转失败")
print(f"  2. 页面加载缓慢")
print(f"  3. 浏览器缓存问题")
print(f"\n  操作:") 
print(f"  1. 打开浏览器开发者工具 (F12)")
print(f"  2. 查看 Network 标签，检查是否有请求")
print(f"  3. 查看 Console 标签，检查是否有错误")
print(f"  4. 检查路由跳转是否执行")

print("\n" + "="*80)
