"""
费用管理全面测试
测试费用的创建、查询、更新、删除等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any


@pytest.fixture
def test_trip_with_itinerary(client: TestClient, registered_user: Dict[str, Any]) -> Dict[str, Any]:
    """创建带行程安排的测试行程"""
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
    
    # 创建行程安排
    itinerary_data = {
        "day_number": 1,
        "date": f"{start_date}T00:00:00",
        "title": "第1天"
    }
    itinerary_response = client.post(
        f"/api/v1/trips/{trip_id}/itineraries",
        json=itinerary_data,
        headers=headers
    )
    itinerary = itinerary_response.json()
    itinerary_id = itinerary["id"]
    
    # 创建节点
    item_data = {
        "name": "天安门广场",
        "category": "attraction",
        "address": "北京市东城区",
        "coordinates": {"lat": 39.9042, "lng": 116.3974},
        "order_index": 0
    }
    item_response = client.post(
        f"/api/v1/trips/itineraries/{itinerary_id}/items",
        json=item_data,
        headers=headers
    )
    item = item_response.json()
    
    return {
        "trip": trip,
        "itinerary": itinerary,
        "item": item
    }


class TestExpenseManagement:
    """费用管理测试"""
    
    def test_create_expense(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试创建费用"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        
        expense_data = {
            "amount": 100.0,
            "category": "food",
            "description": "午餐",
            "currency": "CNY",
            "expense_date": f"{datetime.now().date()}T00:00:00"
        }
        
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.0
        assert data["category"] == "food"
        assert data["description"] == "午餐"
        assert "id" in data
    
    def test_create_expense_with_item(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试创建关联节点的费用"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        item_id = test_trip_with_itinerary["item"]["id"]
        
        expense_data = {
            "amount": 50.0,
            "category": "attraction",
            "description": "门票",
            "currency": "CNY",
            "expense_date": f"{datetime.now().date()}T00:00:00",
            "itinerary_item_id": item_id
        }
        
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50.0
        assert data["itinerary_item_id"] == item_id
    
    def test_create_expense_all_categories(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试创建所有分类的费用"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        
        categories = ["transportation", "accommodation", "food", "attraction", "shopping", "other"]
        
        for category in categories:
            expense_data = {
                "amount": 100.0 * (categories.index(category) + 1),
                "category": category,
                "description": f"{category}费用",
                "currency": "CNY",
                "expense_date": f"{datetime.now().date()}T00:00:00"
            }
            
            response = client.post(
                f"/api/v1/budgets/trips/{trip_id}/expenses",
                json=expense_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["category"] == category
    
    def test_get_expenses(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试获取费用列表"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        
        # 创建几个费用
        for i in range(3):
            expense_data = {
                "amount": 100.0 * (i + 1),
                "category": "food",
                "description": f"费用{i+1}",
                "currency": "CNY",
                "expense_date": f"{datetime.now().date()}T00:00:00"
            }
            client.post(
                f"/api/v1/budgets/trips/{trip_id}/expenses",
                json=expense_data,
                headers=headers
            )
        
        # 获取费用列表
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses?page=1&size=10",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "expenses" in data
        assert len(data["expenses"]) >= 3
        assert "total_amount" in data
    
    def test_get_expenses_filter_by_category(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试按分类筛选费用"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        
        # 创建不同分类的费用
        categories = ["food", "transportation", "food"]
        for category in categories:
            expense_data = {
                "amount": 100.0,
                "category": category,
                "description": f"{category}费用",
                "currency": "CNY",
                "expense_date": f"{datetime.now().date()}T00:00:00"
            }
            client.post(
                f"/api/v1/budgets/trips/{trip_id}/expenses",
                json=expense_data,
                headers=headers
            )
        
        # 筛选food分类
        response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses?category=food",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for expense in data["expenses"]:
            assert expense["category"] == "food"
    
    def test_update_expense(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试更新费用"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        
        # 创建费用
        expense_data = {
            "amount": 100.0,
            "category": "food",
            "description": "原始描述",
            "currency": "CNY",
            "expense_date": f"{datetime.now().date()}T00:00:00"
        }
        create_response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        expense_id = create_response.json()["id"]
        
        # 更新费用
        update_data = {
            "amount": 200.0,
            "description": "更新后的描述"
        }
        response = client.put(
            f"/api/v1/expenses/{expense_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 200.0
        assert data["description"] == "更新后的描述"
    
    def test_update_expense_with_item(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试更新费用关联节点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        item_id = test_trip_with_itinerary["item"]["id"]
        
        # 创建费用（不关联节点）
        expense_data = {
            "amount": 100.0,
            "category": "food",
            "description": "午餐",
            "currency": "CNY",
            "expense_date": f"{datetime.now().date()}T00:00:00"
        }
        create_response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        expense_id = create_response.json()["id"]
        
        # 更新费用，关联节点
        update_data = {
            "itinerary_item_id": item_id
        }
        response = client.put(
            f"/api/v1/expenses/{expense_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["itinerary_item_id"] == item_id
    
    def test_delete_expense(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试删除费用"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        
        # 创建费用
        expense_data = {
            "amount": 100.0,
            "category": "food",
            "description": "待删除费用",
            "currency": "CNY",
            "expense_date": f"{datetime.now().date()}T00:00:00"
        }
        create_response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        expense_id = create_response.json()["id"]
        
        # 删除费用
        response = client.delete(
            f"/api/v1/budgets/trips/{trip_id}/expenses/{expense_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        
        # 验证费用已删除
        get_response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            headers=headers
        )
        expenses = get_response.json()["expenses"]
        expense_ids = [e["id"] for e in expenses]
        assert expense_id not in expense_ids
    
    def test_expense_validation(self, client: TestClient, registered_user: Dict[str, Any], test_trip_with_itinerary: Dict[str, Any]):
        """测试费用数据验证"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip_with_itinerary["trip"]["id"]
        
        # 测试负数金额（应该失败）
        expense_data = {
            "amount": -100.0,
            "category": "food",
            "description": "无效费用",
            "currency": "CNY"
        }
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        assert response.status_code == 422  # 验证失败
        
        # 测试零金额（应该失败）
        expense_data["amount"] = 0
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        assert response.status_code == 422  # 验证失败
        
        # 测试缺少必填字段（应该失败）
        incomplete_data = {
            "amount": 100.0
            # 缺少category
        }
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=incomplete_data,
            headers=headers
        )
        assert response.status_code == 422  # 验证失败

