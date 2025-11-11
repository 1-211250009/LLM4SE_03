#!/usr/bin/env python3
"""
完整流程测试脚本
测试：注册 -> 登录 -> 创建行程 -> 添加节点 -> 添加费用 -> 验证统计
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用户信息
TEST_EMAIL = "test@outlook.com"
TEST_PASSWORD = "123456"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def register_user(email: str, password: str) -> bool:
    """注册用户"""
    print_info(f"注册用户: {email}")
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={"email": email, "password": password, "name": "测试用户"}
        )
        if response.status_code in [200, 201]:
            data = response.json()
            if data.get("access_token"):
                print_success("用户注册成功")
                return True
            else:
                print_warning("用户已存在或注册响应异常，尝试登录")
                return True
        elif response.status_code == 400:
            data = response.json()
            detail = data.get("detail", "")
            if "already" in detail.lower() or "已存在" in detail or "Email already" in detail:
                print_warning("用户已存在，继续测试（将使用登录）")
                return True
            else:
                print_error(f"注册失败: {detail}")
                return False
        else:
            # 检查响应内容
            try:
                data = response.json()
                detail = data.get("detail", "")
                if "already" in detail.lower() or "已存在" in detail or "Email already" in detail:
                    print_warning("用户已存在，继续测试（将使用登录）")
                    return True
            except:
                pass
            print_warning(f"注册返回状态码 {response.status_code}，继续测试（将使用登录）")
            return True  # 允许继续，使用登录
    except Exception as e:
        print_warning(f"注册异常: {str(e)}，继续测试（将使用登录）")
        return True  # 允许继续，使用登录

def login_user(email: str, password: str) -> str:
    """登录用户，返回token"""
    print_info(f"登录用户: {email}")
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_success("登录成功")
                return token
            else:
                print_error("登录响应中没有token")
                return None
        else:
            print_error(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        return None

def create_trip(token: str, start_date: str, end_date: str) -> str:
    """创建3天行程"""
    print_info("创建3天行程")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 计算行程天数
    from datetime import datetime
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00') if 'Z' in start_date else start_date)
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00') if 'Z' in end_date else end_date)
    duration_days = (end.date() - start.date()).days + 1
    
    trip_data = {
        "title": "测试行程",
        "description": "完整流程测试行程",
        "destination": "北京",
        "start_date": start_date,
        "end_date": end_date,
        "duration_days": duration_days,  # 明确指定行程天数
        "budget_total": 5000.0,
        "currency": "CNY",
        "traveler_count": 2,
        "status": "planned"
    }
    try:
        response = requests.post(
            f"{API_BASE}/trips",
            headers=headers,
            json=trip_data
        )
        if response.status_code == 200:
            data = response.json()
            trip_id = data.get("id")
            print_success(f"行程创建成功: {trip_id} (天数: {duration_days})")
            return trip_id
        else:
            print_error(f"创建行程失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"创建行程异常: {str(e)}")
        return None

def create_itinerary(token: str, trip_id: str, day_number: int, date: str) -> str:
    """创建行程安排（某一天）"""
    headers = {"Authorization": f"Bearer {token}"}
    itinerary_data = {
        "day_number": day_number,
        "date": date,
        "title": f"第{day_number}天",
        "description": ""
    }
    try:
        response = requests.post(
            f"{API_BASE}/trips/{trip_id}/itineraries",
            headers=headers,
            json=itinerary_data
        )
        if response.status_code == 200:
            data = response.json()
            itinerary_id = data.get("id")
            print_success(f"第{day_number}天行程创建成功: {itinerary_id}")
            return itinerary_id
        else:
            print_error(f"创建行程安排失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"创建行程安排异常: {str(e)}")
        return None

def create_itinerary_item(token: str, itinerary_id: str, name: str, category: str, address: str, coordinates: Dict) -> str:
    """创建行程节点"""
    headers = {"Authorization": f"Bearer {token}"}
    item_data = {
        "name": name,
        "category": category,
        "description": f"测试节点：{name}",
        "address": address,
        "coordinates": coordinates,
        "order_index": 0
    }
    try:
        response = requests.post(
            f"{API_BASE}/trips/itineraries/{itinerary_id}/items",
            headers=headers,
            json=item_data
        )
        if response.status_code == 200:
            data = response.json()
            item_id = data.get("id")
            print_success(f"节点创建成功: {name} ({item_id})")
            return item_id
        else:
            print_error(f"创建节点失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"创建节点异常: {str(e)}")
        return None

def create_expense(token: str, trip_id: str, amount: float, category: str, description: str, expense_date: str, itinerary_item_id: str = None) -> str:
    """创建费用记录"""
    headers = {"Authorization": f"Bearer {token}"}
    expense_data = {
        "amount": amount,
        "category": category,
        "description": description,
        "currency": "CNY",
        "expense_date": expense_date,
        "itinerary_item_id": itinerary_item_id
    }
    try:
        response = requests.post(
            f"{API_BASE}/budgets/trips/{trip_id}/expenses",
            headers=headers,
            json=expense_data
        )
        if response.status_code == 200:
            data = response.json()
            expense_id = data.get("id")
            print_success(f"费用创建成功: {description} - ¥{amount} ({expense_id})")
            return expense_id
        else:
            print_error(f"创建费用失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"创建费用异常: {str(e)}")
        return None

def get_trip_detail(token: str, trip_id: str) -> Dict:
    """获取行程详情"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{API_BASE}/trips/{trip_id}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"获取行程详情失败: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"获取行程详情异常: {str(e)}")
        return None

def get_budget(token: str, trip_id: str) -> Dict:
    """获取预算信息"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{API_BASE}/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"获取预算失败: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"获取预算异常: {str(e)}")
        return None

def get_expense_stats(token: str, trip_id: str) -> Dict:
    """获取费用统计"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{API_BASE}/budgets/trips/{trip_id}/expenses/stats",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"获取费用统计失败: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"获取费用统计异常: {str(e)}")
        return None

def get_expenses(token: str, trip_id: str) -> List[Dict]:
    """获取费用列表"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # 获取所有费用（可能需要分页）
        all_expenses = []
        page = 1
        page_size = 100
        while True:
            response = requests.get(
                f"{API_BASE}/budgets/trips/{trip_id}/expenses?page={page}&size={page_size}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                expenses = data.get("expenses", [])
                all_expenses.extend(expenses)
                if not data.get("has_next", False):
                    break
                page += 1
            else:
                break
        return all_expenses
    except Exception as e:
        print_error(f"获取费用列表异常: {str(e)}")
        return []

def verify_statistics(trip_detail: Dict, budget: Dict, stats: Dict, expenses: List[Dict], expected_categories: List[str]):
    """验证统计数据"""
    print_info("验证统计数据...")
    
    # 计算总支出
    total_spent = sum(exp.get("amount", 0) for exp in expenses)
    
    # 验证总支出（从budget接口）
    budget_spent = budget.get("spent_amount", 0)
    if abs(total_spent - budget_spent) < 0.01:
        print_success(f"总支出正确: ¥{total_spent}")
    else:
        print_error(f"总支出不匹配: 期望 ¥{total_spent}, 实际 ¥{budget_spent}")
    
    # 验证总支出（从stats接口）
    if stats:
        stats_total = stats.get("total_amount", 0)
        if abs(total_spent - stats_total) < 0.01:
            print_success(f"统计总支出正确: ¥{stats_total}")
        else:
            print_error(f"统计总支出不匹配: 期望 ¥{total_spent}, 实际 ¥{stats_total}")
    
    # 验证剩余预算
    total_budget = budget.get("total_budget", 0)
    remaining_budget = budget.get("remaining_budget", 0)
    expected_remaining = total_budget - total_spent
    if abs(remaining_budget - expected_remaining) < 0.01:
        print_success(f"剩余预算正确: ¥{remaining_budget:.2f}")
    else:
        print_error(f"剩余预算不匹配: 期望 ¥{expected_remaining:.2f}, 实际 ¥{remaining_budget:.2f}")
    
    # 验证预算进度
    budget_usage = budget.get("budget_usage_percent", 0)
    expected_usage = (total_spent / total_budget * 100) if total_budget > 0 else 0
    if abs(budget_usage - expected_usage) < 0.01:
        print_success(f"预算进度正确: {budget_usage:.2f}%")
    else:
        print_error(f"预算进度不匹配: 期望 {expected_usage:.2f}%, 实际 {budget_usage:.2f}%")
    
    # 验证预算对比（从stats接口）
    if stats:
        budget_vs_actual = stats.get("budget_vs_actual", {})
        if budget_vs_actual:
            stats_remaining = budget_vs_actual.get("remaining", 0)
            if abs(stats_remaining - expected_remaining) < 0.01:
                print_success(f"统计剩余预算正确: ¥{stats_remaining:.2f}")
            else:
                print_error(f"统计剩余预算不匹配: 期望 ¥{expected_remaining:.2f}, 实际 ¥{stats_remaining:.2f}")
    
    # 验证费用分类统计
    if stats:
        category_breakdown = stats.get("category_breakdown", {})
        for category in expected_categories:
            category_expenses = [e for e in expenses if e.get("category") == category]
            expected_amount = sum(e.get("amount", 0) for e in category_expenses)
            actual_amount = category_breakdown.get(category, 0)
            if abs(actual_amount - expected_amount) < 0.01:
                print_success(f"分类 {category} 统计正确: ¥{actual_amount:.2f}")
            else:
                print_error(f"分类 {category} 统计不匹配: 期望 ¥{expected_amount:.2f}, 实际 ¥{actual_amount:.2f}")
    
    # 验证日均支出
    expense_count = len(expenses)
    if expense_count > 0 and stats:
        # 计算实际费用天数
        expense_dates = set()
        for exp in expenses:
            exp_date = exp.get("expense_date")
            if exp_date:
                if isinstance(exp_date, str):
                    expense_dates.add(exp_date.split("T")[0])
                else:
                    expense_dates.add(str(exp_date).split("T")[0])
        actual_days = len(expense_dates) if expense_dates else 1
        expected_daily_avg = total_spent / actual_days if actual_days > 0 else 0
        daily_avg = stats.get("daily_average", 0)
        if abs(daily_avg - expected_daily_avg) < 0.01:
            print_success(f"日均支出正确: ¥{daily_avg:.2f}")
        else:
            print_error(f"日均支出不匹配: 期望 ¥{expected_daily_avg:.2f}, 实际 ¥{daily_avg:.2f}")
    
    # 验证平均支出（每笔费用）
    if expense_count > 0:
        expected_avg = total_spent / expense_count
        print_info(f"平均每笔支出: ¥{expected_avg:.2f} (共{expense_count}笔)")

def main():
    """主测试流程"""
    print("=" * 60)
    print("完整流程测试开始")
    print("=" * 60)
    
    # 1. 注册用户
    if not register_user(TEST_EMAIL, TEST_PASSWORD):
        print_error("测试终止：用户注册失败")
        return
    
    # 2. 登录用户
    token = login_user(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        print_error("测试终止：用户登录失败")
        return
    
    # 3. 创建3天行程
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    trip_id = create_trip(token, f"{start_date}T00:00:00", f"{end_date}T00:00:00")
    if not trip_id:
        print_error("测试终止：行程创建失败")
        return
    
    # 4. 创建行程安排和节点
    print_info("创建行程安排和节点...")
    itinerary_items = {}  # {day_number: [item_id1, item_id2]}
    
    # 测试地点坐标（北京的不同位置）
    locations = [
        {"name": "天安门广场", "address": "北京市东城区东长安街", "coordinates": {"lat": 39.9042, "lng": 116.3974}},
        {"name": "故宫博物院", "address": "北京市东城区景山前街4号", "coordinates": {"lat": 39.9163, "lng": 116.3972}},
        {"name": "颐和园", "address": "北京市海淀区新建宫门路19号", "coordinates": {"lat": 39.9990, "lng": 116.2750}},
        {"name": "天坛公园", "address": "北京市东城区天坛路甲1号", "coordinates": {"lat": 39.8823, "lng": 116.4066}},
        {"name": "北京动物园", "address": "北京市西城区西直门外大街137号", "coordinates": {"lat": 39.9384, "lng": 116.3435}},
        {"name": "什刹海", "address": "北京市西城区什刹海", "coordinates": {"lat": 39.9426, "lng": 116.3867}},
    ]
    
    categories = ["attraction", "restaurant", "hotel", "transport", "shopping", "other"]
    
    item_index = 0
    for day in range(1, 4):
        date = (datetime.now() + timedelta(days=day-1)).strftime("%Y-%m-%d")
        itinerary_id = create_itinerary(token, trip_id, day, f"{date}T00:00:00")
        if not itinerary_id:
            continue
        
        # 每天创建2个节点
        day_items = []
        for i in range(2):
            if item_index < len(locations):
                loc = locations[item_index]
                category = categories[item_index % len(categories)]
                item_id = create_itinerary_item(
                    token, itinerary_id, 
                    loc["name"], category, 
                    loc["address"], loc["coordinates"]
                )
                if item_id:
                    day_items.append(item_id)
                item_index += 1
        itinerary_items[day] = day_items
    
    # 5. 创建费用记录
    print_info("创建费用记录...")
    expense_categories = ["transportation", "accommodation", "food", "attraction", "shopping", "other"]
    
    # 每种费用类型创建2条记录
    expense_index = 0
    all_item_ids = []
    for day_items in itinerary_items.values():
        all_item_ids.extend(day_items)
    
    for category in expense_categories:
        for i in range(2):
            # 绑定到不同的节点
            item_id = all_item_ids[expense_index % len(all_item_ids)] if all_item_ids else None
            expense_date = (datetime.now() + timedelta(days=expense_index % 3)).strftime("%Y-%m-%d")
            amount = (expense_index + 1) * 50.0  # 50, 100, 150, ...
            
            create_expense(
                token, trip_id, amount, category,
                f"{category}费用{i+1}", f"{expense_date}T00:00:00",
                item_id
            )
            expense_index += 1
    
    # 6. 验证统计数据
    print_info("获取并验证统计数据...")
    
    # 获取行程详情
    trip_detail = get_trip_detail(token, trip_id)
    if not trip_detail:
        print_error("无法获取行程详情")
        return
    
    # 获取预算信息
    budget = get_budget(token, trip_id)
    if not budget:
        print_error("无法获取预算信息")
        return
    
    # 获取费用统计
    stats = get_expense_stats(token, trip_id)
    if not stats:
        print_error("无法获取费用统计")
        return
    
    # 获取费用列表
    expenses = get_expenses(token, trip_id)
    if not expenses:
        print_error("无法获取费用列表")
        return
    
    # 验证统计数据
    verify_statistics(trip_detail, budget, stats, expenses, expense_categories)
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    print(f"行程ID: {trip_id}")
    print(f"总费用数: {len(expenses)}")
    print(f"总支出: ¥{sum(e.get('amount', 0) for e in expenses)}")
    print(f"剩余预算: ¥{budget.get('remaining_budget', 0)}")

if __name__ == "__main__":
    main()

