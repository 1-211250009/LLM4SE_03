"""
行程安排和节点全面测试
测试行程安排（itinerary）和行程节点（itinerary item）的创建、查询、更新、删除等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any


@pytest.fixture
def test_trip(client: TestClient, registered_user: Dict[str, Any]) -> Dict[str, Any]:
    """创建测试行程"""
    token = registered_user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=2)
    
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
    
    response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
    return response.json()


class TestItineraryManagement:
    """行程安排管理测试"""
    
    def test_create_itinerary(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试创建行程安排"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "第1天",
            "description": "第一天行程安排"
        }
        
        response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["day_number"] == 1
        assert data["title"] == "第1天"
        assert "id" in data
    
    def test_create_multiple_itineraries(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试创建多天行程安排"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        start_date = datetime.now().date()
        
        # 创建3天的行程安排
        for day in range(1, 4):
            itinerary_data = {
                "day_number": day,
                "date": f"{(start_date + timedelta(days=day-1))}T00:00:00",
                "title": f"第{day}天",
                "description": f"第{day}天行程安排"
            }
            
            response = client.post(
                f"/api/v1/trips/{trip_id}/itineraries",
                json=itinerary_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["day_number"] == day
    
    def test_get_itinerary_list(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试获取行程安排列表"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建几个行程安排
        start_date = datetime.now().date()
        for day in range(1, 3):
            itinerary_data = {
                "day_number": day,
                "date": f"{(start_date + timedelta(days=day-1))}T00:00:00",
                "title": f"第{day}天"
            }
            client.post(
                f"/api/v1/trips/{trip_id}/itineraries",
                json=itinerary_data,
                headers=headers
            )
        
        # 获取行程详情（包含itineraries）
        response = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "itineraries" in data
        assert len(data["itineraries"]) >= 2
    
    def test_update_itinerary(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试更新行程安排"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建行程安排
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "原始标题",
            "description": "原始描述"
        }
        create_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = create_response.json()["id"]
        
        # 更新行程安排
        update_data = {
            "title": "更新后的标题",
            "description": "更新后的描述"
        }
        response = client.put(
            f"/api/v1/trips/{trip_id}/itineraries/{itinerary_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["description"] == "更新后的描述"
    
    def test_delete_itinerary(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试删除行程安排"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建行程安排
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "待删除行程安排"
        }
        create_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = create_response.json()["id"]
        
        # 删除行程安排
        response = client.delete(
            f"/api/v1/trips/{trip_id}/itineraries/{itinerary_id}",
            headers=headers
        )
        
        assert response.status_code == 200


class TestItineraryItemManagement:
    """行程节点管理测试"""
    
    def test_create_itinerary_item(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试创建行程节点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 先创建行程安排
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "第1天"
        }
        itinerary_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = itinerary_response.json()["id"]
        
        # 创建节点
        item_data = {
            "name": "天安门广场",
            "category": "attraction",
            "description": "测试节点",
            "address": "北京市东城区东长安街",
            "coordinates": {
                "lat": 39.9042,
                "lng": 116.3974
            },
            "start_time": "09:00",
            "end_time": "11:00",
            "order_index": 0
        }
        
        response = client.post(
            f"/api/v1/trips/itineraries/{itinerary_id}/items",
            json=item_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "天安门广场"
        assert data["category"] == "attraction"
        assert data["coordinates"]["lat"] == 39.9042
        assert "id" in data
    
    def test_create_multiple_items(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试创建多个节点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建行程安排
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "第1天"
        }
        itinerary_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = itinerary_response.json()["id"]
        
        # 创建多个节点
        items = [
            {
                "name": "天安门广场",
                "category": "attraction",
                "address": "北京市东城区",
                "coordinates": {"lat": 39.9042, "lng": 116.3974},
                "order_index": 0
            },
            {
                "name": "故宫博物院",
                "category": "attraction",
                "address": "北京市东城区",
                "coordinates": {"lat": 39.9163, "lng": 116.3972},
                "order_index": 1
            }
        ]
        
        created_items = []
        for item_data in items:
            response = client.post(
                f"/api/v1/trips/itineraries/{itinerary_id}/items",
                json=item_data,
                headers=headers
            )
            assert response.status_code == 200
            created_items.append(response.json())
        
        assert len(created_items) == 2
    
    def test_create_item_with_time(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试创建带时间的节点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建行程安排
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "第1天"
        }
        itinerary_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = itinerary_response.json()["id"]
        
        # 创建带时间的节点
        item_data = {
            "name": "天安门广场",
            "category": "attraction",
            "address": "北京市东城区",
            "coordinates": {"lat": 39.9042, "lng": 116.3974},
            "start_time": "09:00",
            "end_time": "11:00",
            "estimated_duration": 120,  # 2小时
            "order_index": 0
        }
        
        response = client.post(
            f"/api/v1/trips/itineraries/{itinerary_id}/items",
            json=item_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["start_time"] == "09:00"
        assert data["end_time"] == "11:00"
        assert data["estimated_duration"] == 120
    
    def test_update_itinerary_item(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试更新节点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建行程安排和节点
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "第1天"
        }
        itinerary_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = itinerary_response.json()["id"]
        
        item_data = {
            "name": "原始名称",
            "category": "attraction",
            "address": "北京市",
            "coordinates": {"lat": 39.9042, "lng": 116.3974},
            "order_index": 0
        }
        create_response = client.post(
            f"/api/v1/trips/itineraries/{itinerary_id}/items",
            json=item_data,
            headers=headers
        )
        item_id = create_response.json()["id"]
        
        # 更新节点
        update_data = {
            "name": "更新后的名称",
            "description": "更新后的描述"
        }
        response = client.put(
            f"/api/v1/trips/itineraries/{itinerary_id}/items/{item_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的名称"
        assert data["description"] == "更新后的描述"
    
    def test_delete_itinerary_item(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试删除节点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建行程安排和节点
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "第1天"
        }
        itinerary_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = itinerary_response.json()["id"]
        
        item_data = {
            "name": "待删除节点",
            "category": "attraction",
            "address": "北京市",
            "coordinates": {"lat": 39.9042, "lng": 116.3974},
            "order_index": 0
        }
        create_response = client.post(
            f"/api/v1/trips/itineraries/{itinerary_id}/items",
            json=item_data,
            headers=headers
        )
        item_id = create_response.json()["id"]
        
        # 删除节点
        response = client.delete(
            f"/api/v1/trips/itineraries/{itinerary_id}/items/{item_id}",
            headers=headers
        )
        
        assert response.status_code == 200
    
    def test_item_order_index(self, client: TestClient, registered_user: Dict[str, Any], test_trip: Dict[str, Any]):
        """测试节点顺序索引"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        trip_id = test_trip["id"]
        
        # 创建行程安排
        itinerary_data = {
            "day_number": 1,
            "date": f"{datetime.now().date()}T00:00:00",
            "title": "第1天"
        }
        itinerary_response = client.post(
            f"/api/v1/trips/{trip_id}/itineraries",
            json=itinerary_data,
            headers=headers
        )
        itinerary_id = itinerary_response.json()["id"]
        
        # 创建多个节点，使用不同的order_index
        items_data = [
            {"name": "节点1", "category": "attraction", "coordinates": {"lat": 39.9042, "lng": 116.3974}, "order_index": 0},
            {"name": "节点2", "category": "attraction", "coordinates": {"lat": 39.9163, "lng": 116.3972}, "order_index": 1},
            {"name": "节点3", "category": "attraction", "coordinates": {"lat": 39.9990, "lng": 116.2750}, "order_index": 2}
        ]
        
        for item_data in items_data:
            response = client.post(
                f"/api/v1/trips/itineraries/{itinerary_id}/items",
                json=item_data,
                headers=headers
            )
            assert response.status_code == 200
        
        # 获取行程详情，验证节点顺序
        trip_response = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
        trip_data = trip_response.json()
        
        itinerary = next((it for it in trip_data["itineraries"] if it["id"] == itinerary_id), None)
        assert itinerary is not None
        assert len(itinerary["items"]) == 3
        
        # 验证节点按order_index排序
        items = itinerary["items"]
        for i in range(len(items) - 1):
            assert items[i]["order_index"] <= items[i + 1]["order_index"]

