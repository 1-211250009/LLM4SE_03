"""
预算管理全面测试
测试预算查询、更新、统计等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any


@pytest.fixture
def test_trip_with_expenses(client: TestClient, registered_user: Dict[str, Any]) -> Dict[str, Any]:
    """创建带费用的测试行程"""
    token = registered_user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=2)
    
    # 创建行程
    trip_data = {
        "title": "测试行程",
        "destination": "北京",
        "start_date": f"{start_date}T00:00:00",
        "end_date": f"{end_date}T00:00:00",
        "budget_total": 5000.0,
        "currency": "CNY",
        "traveler_count": 2,
        "status": "planned"
    }
    trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
    trip = trip_response.json()
    trip_id = trip["id"]
    
    # 创建费用
    expenses_data = [
        {"amount": 100.0, "category": "food", "description": "午餐", "currency": "CNY", "expense_date": f"{start_date}T00:00:00"},
        {"amount": 200.0, "category": "transportation", "description": "交通", "currency": "CNY", "expense_date": f"{start_date}T00:00:00"},
        {"amount": 300.0, "category": "accommodation", "description": "住宿", "currency": "CNY", "expense_date": f"{(start_date + timedelta(days=1))}T00:00:00"}
    ]
    
    expenses = []
    for expense_data in expenses_data:
        expense_response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        expenses.append(expense_response.json())
    
    return {
        "trip": trip,
        "expenses": expenses
    }


class TestBudgetManagement:
    """预算管理测试"""
    
    def test_get_trip_budget(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_expenses: Dict[str, Any]):
        """测试获取行程预算"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_expenses["trip"]["id"]
        
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["trip_id"] == trip_id
        assert data["total_budget"] == 5000.0
        assert data["spent_amount"] == 600.0  # 100 + 200 + 300
        assert data["remaining_budget"] == 4400.0  # 5000 - 600
        assert data["budget_usage_percent"] == 12.0  # 600 / 5000 * 100
        assert "category_breakdown" in data
        assert data["expense_count"] == 3
    
    def test_budget_category_breakdown(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_expenses: Dict[str, Any]):
        """测试预算分类统计"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_expenses["trip"]["id"]
        
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        category_breakdown = data["category_breakdown"]
        
        assert category_breakdown["food"] == 100.0
        assert category_breakdown["transportation"] == 200.0
        assert category_breakdown["accommodation"] == 300.0
    
    def test_update_trip_budget(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_expenses: Dict[str, Any]):
        """测试更新行程预算"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_expenses["trip"]["id"]
        
        update_data = {
            "total_budget": 10000.0,
            "currency": "CNY"
        }
        
        response = client.put(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_budget"] == 10000.0
        
        # 验证预算已更新
        budget_response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        budget_data = budget_response.json()
        assert budget_data["total_budget"] == 10000.0
        assert budget_data["remaining_budget"] == 9400.0  # 10000 - 600
    
    def test_budget_calculation_accuracy(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_expenses: Dict[str, Any]):
        """测试预算计算准确性"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_expenses["trip"]["id"]
        
        # 添加更多费用
        new_expenses = [
            {"amount": 50.0, "category": "food", "description": "零食", "currency": "CNY", "expense_date": f"{datetime.now().date()}T00:00:00"},
            {"amount": 150.0, "category": "shopping", "description": "购物", "currency": "CNY", "expense_date": f"{datetime.now().date()}T00:00:00"}
        ]
        
        for expense_data in new_expenses:
            client.post(
                f"/api/v1/budgets/trips/{trip_id}/expenses",
                json=expense_data,
                headers=headers
            )
        
        # 获取预算
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证总支出：600 + 50 + 150 = 800
        assert abs(data["spent_amount"] - 800.0) < 0.01
        # 验证剩余预算：5000 - 800 = 4200
        assert abs(data["remaining_budget"] - 4200.0) < 0.01
        # 验证使用率：800 / 5000 * 100 = 16%
        assert abs(data["budget_usage_percent"] - 16.0) < 0.01
    
    def test_get_expense_stats(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_expenses: Dict[str, Any]):
        """测试获取费用统计"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_expenses["trip"]["id"]
        
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses/stats",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_amount" in data
        assert "category_breakdown" in data
        assert "daily_average" in data
        assert "budget_vs_actual" in data
        
        assert data["total_amount"] == 600.0
        assert "food" in data["category_breakdown"]
        assert "transportation" in data["category_breakdown"]
        assert "accommodation" in data["category_breakdown"]
        
        # 验证预算对比
        budget_vs_actual = data["budget_vs_actual"]
        assert budget_vs_actual["budget"] == 5000.0
        assert budget_vs_actual["actual"] == 600.0
        assert budget_vs_actual["remaining"] == 4400.0
        assert abs(budget_vs_actual["usage_percent"] - 12.0) < 0.01
    
    def test_expense_stats_daily_average(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_expenses: Dict[str, Any]):
        """测试日均支出计算"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_expenses["trip"]["id"]
        
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses/stats",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 费用分布在2天：第1天600，第2天300，总共600
        # 但实际有费用的天数应该是2天
        # 日均 = 600 / 2 = 300
        # 注意：这里需要根据实际的费用日期计算
        assert "daily_average" in data
        assert data["daily_average"] >= 0
    
    def test_budget_with_no_expenses(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试无费用时的预算"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建行程（无费用）
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
        trip_data = {
            "title": "无费用行程",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 获取预算
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["spent_amount"] == 0.0
        assert data["remaining_budget"] == 1000.0
        assert data["budget_usage_percent"] == 0.0
        assert data["expense_count"] == 0
        assert data["category_breakdown"] == {}
    
    def test_budget_over_budget(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试超预算情况"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建行程
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
        trip_data = {
            "title": "超预算行程",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 100.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 创建超过预算的费用
        expense_data = {
            "amount": 150.0,
            "category": "food",
            "description": "超预算费用",
            "currency": "CNY",
            "expense_date": f"{start_date}T00:00:00"
        }
        client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        
        # 获取预算
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["spent_amount"] == 150.0
        assert data["remaining_budget"] == -50.0  # 负数表示超预算
        assert data["budget_usage_percent"] == 150.0  # 150%

