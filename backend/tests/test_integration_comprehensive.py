"""
集成测试
测试完整的业务流程
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any, List


class TestCompleteWorkflow:
    """完整流程测试"""
    
    def test_full_trip_lifecycle(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试完整的行程生命周期"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. 创建行程
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=2)
        trip_data = {
            "title": "完整流程测试行程",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 5000.0,
            "currency": "CNY",
            "traveler_count": 2,
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        assert trip_response.status_code == 200
        trip = trip_response.json()
        trip_id = trip["id"]
        assert trip["duration_days"] == 3
        
        # 2. 创建行程安排
        itineraries = []
        for day in range(1, 4):
            itinerary_data = {
                "day_number": day,
                "date": f"{(start_date + timedelta(days=day-1))}T00:00:00",
                "title": f"第{day}天",
                "description": f"第{day}天行程安排"
            }
            itinerary_response = client.post(
                f"/api/v1/trips/{trip_id}/itineraries",
                json=itinerary_data,
                headers=headers
            )
            assert itinerary_response.status_code == 200
            itineraries.append(itinerary_response.json())
        
        assert len(itineraries) == 3
        
        # 3. 创建行程节点
        items = []
        locations = [
            {"name": "天安门广场", "lat": 39.9042, "lng": 116.3974},
            {"name": "故宫博物院", "lat": 39.9163, "lng": 116.3972},
            {"name": "颐和园", "lat": 39.9990, "lng": 116.2750}
        ]
        
        for i, itinerary in enumerate(itineraries):
            if i < len(locations):
                item_data = {
                    "name": locations[i]["name"],
                    "category": "attraction",
                    "address": f"北京市{locations[i]['name']}",
                    "coordinates": {"lat": locations[i]["lat"], "lng": locations[i]["lng"]},
                    "order_index": 0
                }
                item_response = client.post(
                    f"/api/v1/trips/itineraries/{itinerary['id']}/items",
                    json=item_data,
                    headers=headers
                )
                assert item_response.status_code == 200
                items.append(item_response.json())
        
        assert len(items) == 3
        
        # 4. 创建费用
        expenses = []
        expense_categories = ["food", "transportation", "accommodation"]
        for i, category in enumerate(expense_categories):
            expense_data = {
                "amount": 100.0 * (i + 1),
                "category": category,
                "description": f"{category}费用",
                "currency": "CNY",
                "expense_date": f"{(start_date + timedelta(days=i))}T00:00:00",
                "itinerary_item_id": items[i]["id"] if i < len(items) else None
            }
            expense_response = client.post(
                f"/api/v1/budgets/trips/{trip_id}/expenses",
                json=expense_data,
                headers=headers
            )
            assert expense_response.status_code == 200
            expenses.append(expense_response.json())
        
        assert len(expenses) == 3
        
        # 5. 验证预算
        budget_response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        assert budget_response.status_code == 200
        budget_data = budget_response.json()
        assert budget_data["total_budget"] == 5000.0
        assert budget_data["spent_amount"] == 600.0  # 100 + 200 + 300
        assert budget_data["remaining_budget"] == 4400.0
        
        # 6. 验证费用统计
        stats_response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses/stats",
            headers=headers
        )
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["total_amount"] == 600.0
        assert "category_breakdown" in stats_data
        
        # 7. 验证行程详情包含所有数据
        trip_detail_response = client.get(
            f"/api/v1/trips/{trip_id}",
            headers=headers
        )
        assert trip_detail_response.status_code == 200
        trip_detail = trip_detail_response.json()
        assert len(trip_detail["itineraries"]) == 3
        assert len(trip_detail["expenses"]) == 3
        assert trip_detail["itineraries"][0]["items"][0]["name"] == "天安门广场"
        
        # 8. 更新行程
        update_data = {
            "title": "更新后的行程标题",
            "budget_total": 10000.0
        }
        update_response = client.put(
            f"/api/v1/trips/{trip_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        updated_trip = update_response.json()
        assert updated_trip["title"] == "更新后的行程标题"
        assert updated_trip["budget_total"] == 10000.0
        
        # 9. 删除费用
        if expenses:
            delete_expense_response = client.delete(
                f"/api/v1/budgets/trips/{trip_id}/expenses/{expenses[0]['id']}",
                headers=headers
            )
            assert delete_expense_response.status_code == 200
        
        # 10. 删除节点
        if items:
            delete_item_response = client.delete(
                f"/api/v1/trips/itineraries/{items[0]['itinerary_id']}/items/{items[0]['id']}",
                headers=headers
            )
            assert delete_item_response.status_code == 200
        
        # 11. 删除行程安排
        if itineraries:
            delete_itinerary_response = client.delete(
                f"/api/v1/trips/{trip_id}/itineraries/{itineraries[0]['id']}",
                headers=headers
            )
            assert delete_itinerary_response.status_code == 200
        
        # 12. 删除行程
        delete_trip_response = client.delete(
            f"/api/v1/trips/{trip_id}",
            headers=headers
        )
        assert delete_trip_response.status_code == 200
        
        # 13. 验证行程已删除
        get_trip_response = client.get(
            f"/api/v1/trips/{trip_id}",
            headers=headers
        )
        assert get_trip_response.status_code == 404
    
    def test_trip_date_calculation_edge_cases(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试行程日期计算的边界情况"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试同一天（开始日期 = 结束日期）
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
        
        # 测试3天行程（开始日期 + 2天 = 结束日期）
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=2)
        trip_data = {
            "title": "3天行程",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 3000.0,
            "currency": "CNY",
            "status": "planned"
        }
        response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["duration_days"] == 3
    
    def test_expense_linking_to_items(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试费用关联节点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建行程和节点
        start_date = datetime.now().date()
        trip_data = {
            "title": "费用关联测试",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{(start_date + timedelta(days=1))}T00:00:00",
            "budget_total": 2000.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 创建行程安排和节点
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
        itinerary_id = itinerary_response.json()["id"]
        
        item_data = {
            "name": "测试节点",
            "category": "attraction",
            "address": "北京市",
            "coordinates": {"lat": 39.9042, "lng": 116.3974},
            "order_index": 0
        }
        item_response = client.post(
            f"/api/v1/trips/itineraries/{itinerary_id}/items",
            json=item_data,
            headers=headers
        )
        item_id = item_response.json()["id"]
        
        # 创建关联节点的费用
        expense_data = {
            "amount": 50.0,
            "category": "attraction",
            "description": "节点门票",
            "currency": "CNY",
            "expense_date": f"{start_date}T00:00:00",
            "itinerary_item_id": item_id
        }
        expense_response = client.post(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            json=expense_data,
            headers=headers
        )
        assert expense_response.status_code == 200
        expense = expense_response.json()
        assert expense["itinerary_item_id"] == item_id
        
        # 验证费用列表显示关联节点
        expenses_response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses",
            headers=headers
        )
        assert expenses_response.status_code == 200
        expenses = expenses_response.json()["expenses"]
        assert len(expenses) == 1
        assert expenses[0]["itinerary_item_id"] == item_id
    
    def test_budget_statistics_accuracy(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试预算统计准确性"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建行程
        start_date = datetime.now().date()
        trip_data = {
            "title": "预算统计测试",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{(start_date + timedelta(days=2))}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        trip_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = trip_response.json()["id"]
        
        # 创建多个费用
        expenses_data = [
            {"amount": 100.0, "category": "food", "description": "费用1", "currency": "CNY", "expense_date": f"{start_date}T00:00:00"},
            {"amount": 200.0, "category": "food", "description": "费用2", "currency": "CNY", "expense_date": f"{start_date}T00:00:00"},
            {"amount": 150.0, "category": "transportation", "description": "费用3", "currency": "CNY", "expense_date": f"{(start_date + timedelta(days=1))}T00:00:00"},
            {"amount": 50.0, "category": "other", "description": "费用4", "currency": "CNY", "expense_date": f"{(start_date + timedelta(days=2))}T00:00:00"}
        ]
        
        for expense_data in expenses_data:
            client.post(
                f"/api/v1/budgets/trips/{trip_id}/expenses",
                json=expense_data,
                headers=headers
            )
        
        # 验证预算统计
        budget_response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/budget",
            headers=headers
        )
        budget_data = budget_response.json()
        
        # 总支出：100 + 200 + 150 + 50 = 500
        assert abs(budget_data["spent_amount"] - 500.0) < 0.01
        # 剩余预算：1000 - 500 = 500
        assert abs(budget_data["remaining_budget"] - 500.0) < 0.01
        # 使用率：500 / 1000 * 100 = 50%
        assert abs(budget_data["budget_usage_percent"] - 50.0) < 0.01
        
        # 验证分类统计
        category_breakdown = budget_data["category_breakdown"]
        assert abs(category_breakdown.get("food", 0) - 300.0) < 0.01  # 100 + 200
        assert abs(category_breakdown.get("transportation", 0) - 150.0) < 0.01
        assert abs(category_breakdown.get("other", 0) - 50.0) < 0.01
        
        # 验证费用统计
        stats_response = client.get(
            f"/api/v1/budgets/trips/{trip_id}/expenses/stats",
            headers=headers
        )
        stats_data = stats_response.json()
        
        assert abs(stats_data["total_amount"] - 500.0) < 0.01
        assert "food" in stats_data["category_breakdown"]
        assert abs(stats_data["category_breakdown"]["food"] - 300.0) < 0.01

