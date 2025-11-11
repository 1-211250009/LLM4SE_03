"""
行程管理全面测试
测试行程的创建、查询、更新、删除等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any


class TestTripManagement:
    """行程管理测试"""
    
    def test_create_trip_same_day(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试创建同一天的行程（开始日期=结束日期）"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        today = datetime.now().date()
        trip_data = {
            "title": "测试行程-同一天",
            "description": "测试同一天行程",
            "destination": "北京",
            "start_date": f"{today}T00:00:00",
            "end_date": f"{today}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "traveler_count": 2,
            "status": "planned"
        }
        
        response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == trip_data["title"]
        assert data["duration_days"] == 1  # 同一天应该是1天
        assert data["budget_total"] == 1000.0
    
    def test_create_trip_multiple_days(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试创建多天行程"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=2)
        
        trip_data = {
            "title": "测试行程-3天",
            "description": "测试3天行程",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 5000.0,
            "currency": "CNY",
            "traveler_count": 2,
            "status": "planned"
        }
        
        response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == trip_data["title"]
        assert data["duration_days"] == 3  # 应该是3天
        assert data["budget_total"] == 5000.0
    
    def test_create_trip_auto_calculate_duration(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试自动计算行程天数（不提供duration_days）"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=5)
        
        trip_data = {
            "title": "测试行程-自动计算天数",
            "destination": "上海",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 10000.0,
            "currency": "CNY",
            "traveler_count": 1,
            "status": "planned"
        }
        
        response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["duration_days"] == 6  # 自动计算：5天差 + 1 = 6天
    
    def test_create_trip_invalid_date_range(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试创建行程：结束日期早于开始日期（应该失败）"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        start_date = datetime.now().date()
        end_date = start_date - timedelta(days=1)  # 结束日期早于开始日期
        
        trip_data = {
            "title": "测试行程-无效日期",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        
        response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        assert response.status_code == 422  # 验证失败
    
    def test_get_trip_list(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试获取行程列表"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 先创建几个行程
        for i in range(3):
            trip_data = {
                "title": f"测试行程{i+1}",
                "destination": "北京",
                "start_date": f"{datetime.now().date()}T00:00:00",
                "end_date": f"{(datetime.now() + timedelta(days=i)).date()}T00:00:00",
                "budget_total": 1000.0 * (i + 1),
                "currency": "CNY",
                "status": "planned"
            }
            client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        # 获取列表
        response = client.get("/api/v1/trips/?page=1&size=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "trips" in data
        assert "total" in data
        assert len(data["trips"]) >= 3
    
    def test_get_trip_detail(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试获取行程详情"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建行程
        trip_data = {
            "title": "测试行程详情",
            "destination": "北京",
            "start_date": f"{datetime.now().date()}T00:00:00",
            "end_date": f"{(datetime.now() + timedelta(days=2)).date()}T00:00:00",
            "budget_total": 5000.0,
            "currency": "CNY",
            "status": "planned"
        }
        create_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = create_response.json()["id"]
        
        # 获取详情
        response = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == trip_id
        assert data["title"] == trip_data["title"]
        assert "itineraries" in data
        assert "expenses" in data
    
    def test_update_trip(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试更新行程"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建行程
        trip_data = {
            "title": "原始标题",
            "destination": "北京",
            "start_date": f"{datetime.now().date()}T00:00:00",
            "end_date": f"{(datetime.now() + timedelta(days=2)).date()}T00:00:00",
            "budget_total": 5000.0,
            "currency": "CNY",
            "status": "planned"
        }
        create_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = create_response.json()["id"]
        
        # 更新行程
        update_data = {
            "title": "更新后的标题",
            "budget_total": 8000.0
        }
        response = client.put(f"/api/v1/trips/{trip_id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["budget_total"] == 8000.0
    
    def test_update_trip_recalculate_duration(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试更新行程日期后自动重新计算天数"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建3天行程
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=2)
        trip_data = {
            "title": "测试更新日期",
            "destination": "北京",
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "budget_total": 5000.0,
            "currency": "CNY",
            "status": "planned"
        }
        create_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = create_response.json()["id"]
        assert create_response.json()["duration_days"] == 3
        
        # 更新为5天行程
        new_end_date = start_date + timedelta(days=4)
        update_data = {
            "end_date": f"{new_end_date}T00:00:00"
        }
        response = client.put(f"/api/v1/trips/{trip_id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["duration_days"] == 5  # 应该自动重新计算为5天
    
    def test_delete_trip(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试删除行程"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建行程
        trip_data = {
            "title": "待删除行程",
            "destination": "北京",
            "start_date": f"{datetime.now().date()}T00:00:00",
            "end_date": f"{(datetime.now() + timedelta(days=1)).date()}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        create_response = client.post("/api/v1/trips/", json=trip_data, headers=headers)
        trip_id = create_response.json()["id"]
        
        # 删除行程
        response = client.delete(f"/api/v1/trips/{trip_id}", headers=headers)
        
        assert response.status_code == 200
        
        # 验证行程已删除
        get_response = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
        assert get_response.status_code == 404
    
    def test_get_trip_not_owned(self, client: TestClient, registered_user: Dict[str, Any], test_user_data: Dict[str, Any]):
        """测试获取其他用户的行程（应该失败）"""
        token1 = registered_user["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        # 用户1创建行程
        trip_data = {
            "title": "用户1的行程",
            "destination": "北京",
            "start_date": f"{datetime.now().date()}T00:00:00",
            "end_date": f"{(datetime.now() + timedelta(days=1)).date()}T00:00:00",
            "budget_total": 1000.0,
            "currency": "CNY",
            "status": "planned"
        }
        create_response = client.post("/api/v1/trips/", json=trip_data, headers=headers1)
        trip_id = create_response.json()["id"]
        
        # 用户2尝试获取（需要创建用户2）
        user2_data = {
            "email": "test2@example.com",
            "password": "password123",
            "name": "Test User 2"
        }
        register_response = client.post("/api/v1/auth/register", json=user2_data)
        if register_response.status_code in [200, 201]:
            token2 = register_response.json()["access_token"]
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            # 用户2尝试获取用户1的行程
            response = client.get(f"/api/v1/trips/{trip_id}", headers=headers2)
            assert response.status_code == 404  # 应该返回404（不存在或无权限）


class TestTripFiltering:
    """行程筛选测试"""
    
    def test_filter_trips_by_status(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试按状态筛选行程"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建不同状态的行程
        for status in ["planned", "active", "completed"]:
            trip_data = {
                "title": f"测试行程-{status}",
                "destination": "北京",
                "start_date": f"{datetime.now().date()}T00:00:00",
                "end_date": f"{(datetime.now() + timedelta(days=1)).date()}T00:00:00",
                "budget_total": 1000.0,
                "currency": "CNY",
                "status": status
            }
            client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        # 筛选planned状态的行程
        response = client.get("/api/v1/trips/?status=planned", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        for trip in data["trips"]:
            assert trip["status"] == "planned"
    
    def test_filter_trips_by_destination(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试按目的地筛选行程"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建不同目的地的行程
        destinations = ["北京", "上海", "广州"]
        for dest in destinations:
            trip_data = {
                "title": f"测试行程-{dest}",
                "destination": dest,
                "start_date": f"{datetime.now().date()}T00:00:00",
                "end_date": f"{(datetime.now() + timedelta(days=1)).date()}T00:00:00",
                "budget_total": 1000.0,
                "currency": "CNY",
                "status": "planned"
            }
            client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        # 筛选北京的行程
        response = client.get("/api/v1/trips/?destination=北京", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        for trip in data["trips"]:
            assert "北京" in trip["destination"]
    
    def test_trip_pagination(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试行程分页"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建多个行程
        for i in range(15):
            trip_data = {
                "title": f"测试行程{i+1}",
                "destination": "北京",
                "start_date": f"{datetime.now().date()}T00:00:00",
                "end_date": f"{(datetime.now() + timedelta(days=1)).date()}T00:00:00",
                "budget_total": 1000.0,
                "currency": "CNY",
                "status": "planned"
            }
            client.post("/api/v1/trips/", json=trip_data, headers=headers)
        
        # 获取第一页
        response1 = client.get("/api/v1/trips/?page=1&size=10", headers=headers)
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["trips"]) <= 10
        assert data1["page"] == 1
        assert data1["size"] == 10
        
        # 获取第二页
        response2 = client.get("/api/v1/trips/?page=2&size=10", headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
        assert data2["has_next"] is not None

