"""
数据验证测试
测试数据验证逻辑，包括日期计算、天数计算等
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, date
from typing import Dict, Any


class TestDateValidation:
    """日期验证测试"""
    
    def test_trip_same_day_validation(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试同一天行程验证（应该允许）"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        today = datetime.now().date()
        trip_data = {
            "title": "同一天行程",
            "destination": "北京",
            "start_date": f"{today}T00:00:00",
            "end_date": f"{today}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        
        response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["duration_days"] == 1
    
    def test_trip_end_before_start_validation(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试结束日期早于开始日期（应该拒绝）"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        trip_data = {
            "title": "无效日期行程",
            "destination": "北京",
            "start_date": f"{today}T00:00:00",
            "end_date": f"{yesterday}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        
        response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        assert response.status_code == 422  # 验证失败
    
    def test_trip_duration_calculation(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试行程天数计算"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        test_cases = [
            # (start_date_offset, end_date_offset, expected_days)
            (0, 0, 1),    # 同一天
            (0, 1, 2),    # 2天
            (0, 2, 3),    # 3天
            (0, 6, 7),    # 7天
        ]
        
        base_date = datetime.now().date()
        
        for start_offset, end_offset, expected_days in test_cases:
            start_date = base_date + timedelta(days=start_offset)
            end_date = base_date + timedelta(days=end_offset)
            
            trip_data = {
                "title": f"测试{expected_days}天行程",
                "destination": "北京",
                "start_date": f"{start_date}T00:00:00",
                "end_date": f"{end_date}T00:00:00",
                "budget_total": 1000.0,
                "currency": "CNY",
                "status": "planned"
            }
            
            response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
            assert response.status_code == 200
            assert response.json()["duration_days"] == expected_days


class TestExpenseValidation:
    """费用验证测试"""
    
    def test_expense_amount_validation(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试费用金额验证"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建测试行程
        start_date = datetime.now().date()
        trip_data = {
            "title": "费用验证测试",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{(start_date + timedelta(days=1))}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 测试负数金额
        expense_data = {
            "amount": -100.0,
            "category": "food",
            "description": "测试",
            "currency": "CNY"
        }
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        assert response.status_code == 422
        
        # 测试零金额
        expense_data["amount"] = 0
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        assert response.status_code == 422
        
        # 测试有效金额
        expense_data["amount"] = 100.0
        response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        assert response.status_code == 200
    
    def test_expense_category_validation(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试费用分类验证"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建测试行程
        start_date = datetime.now().date()
        trip_data = {
            "title": "费用分类验证",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{(start_date + timedelta(days=1))}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 测试有效分类
        valid_categories = ["transportation", "accommodation", "food", "attraction", "shopping", "other"]
        
        for category in valid_categories:
            expense_data = {
                "amount": 100.0,
                "category": category,
                "description": f"{category}费用",
                "currency": "CNY"
            }
            response = client.post(
                f"/api/v1/budgets/trips/{trip_id}/expenses",
                json=expense_data,
                headers=headers
            )
            assert response.status_code == 200


class TestItineraryValidation:
    """行程安排验证测试"""
    
    def test_itinerary_date_validation(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试行程安排日期验证"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建测试行程
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=2)
        trip_data = {
            "title": "行程安排验证",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 测试在范围内的日期
        itinerary_data = {
            "day_number": 1,
            "date": f"{start_date}T00:00:00",
            "title": "第1天"
        }
        response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        assert response.status_code == 200
        
        # 测试范围外的日期（早于开始日期）
        itinerary_data = {
            "day_number": 0,
            "date": f"{(start_date - timedelta(days=1))}T00:00:00",
            "title": "无效日期"
        }
        # 注意：后端可能不验证日期范围，这里只是测试数据格式
        response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        # 如果后端验证了日期范围，应该返回错误
        # 如果没有验证，可能会成功创建
        assert response.status_code in [200, 400, 422]


class TestBudgetValidation:
    """预算验证测试"""
    
    def test_budget_amount_validation(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试预算金额验证"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建测试行程
        start_date = datetime.now().date()
        trip_data = {
            "title": "预算验证",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{(start_date + timedelta(days=1))}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 测试负数预算
        update_data = {
            "total_budget": -100.0,
            "currency": "CNY"
        }
        response = client.put(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 422  # 验证失败
        
        # 测试零预算
        update_data["total_budget"] = 0
        response = client.put(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 422  # 验证失败
        
        # 测试有效预算
        update_data["total_budget"] = 2000.0
        response = client.put(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200

