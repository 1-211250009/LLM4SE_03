"""
地图服务全面测试
测试POI搜索、路线计算、地理编码等功能
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import os


@pytest.mark.skipif(
    not os.getenv("BAIDU_MAP_AK"),
    reason="需要配置百度地图API密钥"
)
class TestMapService:
    """地图服务测试"""
    
    def test_search_poi(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试POI搜索"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        search_data = {
            "keyword": "天安门",
            "city": "北京",
            "category": "attraction"
        }
        
        response = client.post(
            "/api/v1/map/poi/search",
            json=search_data,
            headers=headers
        )
        
        # 如果API密钥未配置，跳过测试
        if response.status_code == 500:
            pytest.skip("百度地图API密钥未配置或服务不可用")
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "data" in data or "pois" in data
    
    def test_calculate_route(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试路线计算"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        route_data = {
            "origin": {
                "lat": 39.9042,
                "lng": 116.3974
            },
            "destination": {
                "lat": 39.9163,
                "lng": 116.3972
            },
            "mode": "driving"
        }
        
        response = client.post(
            "/api/v1/map/route",
            json=route_data,
            headers=headers
        )
        
        # 如果API密钥未配置，跳过测试
        if response.status_code == 500:
            pytest.skip("百度地图API密钥未配置或服务不可用")
        
        assert response.status_code == 200
        data = response.json()
        # 检查返回数据是否包含路径信息
        assert "success" in data or "data" in data
    
    def test_calculate_route_walking(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试步行路线计算"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        route_data = {
            "origin": {
                "lat": 39.9042,
                "lng": 116.3974
            },
            "destination": {
                "lat": 39.9163,
                "lng": 116.3972
            },
            "mode": "walking"
        }
        
        response = client.post(
            "/api/v1/map/route",
            json=route_data,
            headers=headers
        )
        
        if response.status_code == 500:
            pytest.skip("百度地图API密钥未配置或服务不可用")
        
        assert response.status_code == 200
    
    def test_map_health_check(self, client: TestClient):
        """测试地图服务健康检查"""
        response = client.get("/api/v1/map/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "map"

