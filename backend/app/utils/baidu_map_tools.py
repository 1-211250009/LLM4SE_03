"""
百度地图工具函数
为Agent提供POI搜索、路线规划等功能
"""

import requests
import json
from typing import Dict, List, Optional, Any
from app.core.config import settings


class BaiduMapTools:
    """百度地图工具类"""
    
    def __init__(self):
        self.api_key = settings.BAIDU_MAP_AK
        self.sk = settings.BAIDU_MAP_SK
        self.base_url = "https://api.map.baidu.com"
    
    def geocode(self, address: str) -> Optional[Dict[str, float]]:
        """
        地理编码 - 将地址转换为坐标
        
        Args:
            address: 地址字符串
            
        Returns:
            坐标字典 {"lat": 39.9042, "lng": 116.4074} 或 None
        """
        try:
            # 使用百度地图Web服务API的地理编码服务 v3
            url = f"{self.base_url}/geocoding/v3/"
            params = {
                "address": address,
                "output": "json",
                "ak": self.api_key
            }
            
            print(f"DEBUG: 地理编码API调用 - URL: {url}")
            print(f"参数: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # 检查响应内容类型
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type and 'javascript' not in content_type:
                print(f"DEBUG: 响应不是JSON格式，内容类型: {content_type}")
                print(f"响应内容: {response.text[:200]}...")
                return None
            
            data = response.json()
            print(f"地理编码API响应: {data}")
            
            if data.get("status") == 0 and data.get("result"):
                location = data["result"]["location"]
                return {
                    "lat": location["lat"],
                    "lng": location["lng"]
                }
            else:
                print(f"地理编码失败: {data.get('message', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"地理编码API调用异常: {e}")
            return None
    
    def search_poi(self, keyword: str, city: str = "北京", category: str = None, 
                   location: Dict[str, float] = None, radius: int = 10000, 
                   limit: int = 10) -> Dict[str, Any]:
        """
        搜索POI
        
        Args:
            keyword: 搜索关键词
            city: 城市名称
            category: POI分类
            location: 中心点坐标 {"lat": 39.9042, "lng": 116.4074}
            radius: 搜索半径(米)
            limit: 返回数量限制
            
        Returns:
            POI搜索结果
        """
        try:
            # 构建搜索参数
            params = {
                "query": keyword,
                "region": city,
                "output": "json",
                "ak": self.api_key,
                "page_size": limit,
                "scope": "2"  # 返回详细信息
            }
            
            if location:
                params["location"] = f"{location['lat']},{location['lng']}"
                params["radius"] = radius
            
            # 根据category设置合适的tag参数
            if category:
                if category == "attraction":
                    params["tag"] = "旅游景点"
                elif category == "restaurant":
                    params["tag"] = "美食"
                elif category == "hotel":
                    params["tag"] = "酒店"
                else:
                    params["tag"] = category
            
            # 调用百度地图POI搜索API
            url = f"{self.base_url}/place/v2/search"
            print(f"DEBUG: 百度地图API调用 - URL: {url}")
            print(f"DEBUG: 参数: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"DEBUG: API响应: {data}")
            
            if data.get("status") == 0:
                results = data.get("results", [])
                pois = []
                
                for item in results:
                    poi = {
                        "id": item.get("uid", ""),
                        "name": item.get("name", ""),
                        "address": item.get("address", ""),
                        "location": {
                            "lat": item.get("location", {}).get("lat", 0),
                            "lng": item.get("location", {}).get("lng", 0)
                        },
                        "category": item.get("detail_info", {}).get("tag", ""),
                        "rating": item.get("detail_info", {}).get("overall_rating", 0),
                        "price": item.get("detail_info", {}).get("price", ""),
                        "phone": item.get("detail_info", {}).get("telephone", ""),
                        "website": item.get("detail_info", {}).get("detail_url", ""),
                        "opening_hours": item.get("detail_info", {}).get("opening_hours", ""),
                        "description": item.get("detail_info", {}).get("content", "")
                    }
                    pois.append(poi)
                
                return {
                    "success": True,
                    "data": {
                        "pois": pois,
                        "total": len(pois),
                        "keyword": keyword,
                        "city": city
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"POI搜索失败: {data.get('message', '未知错误')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"POI搜索异常: {str(e)}"
            }
    
    def calculate_route(self, origin: str, destination: str, 
                       mode: str = "driving") -> Dict[str, Any]:
        """
        计算路线
        
        Args:
            origin: 起点
            destination: 终点
            mode: 交通方式 (driving, transit, walking, bicycling)
            
        Returns:
            路线计算结果
        """
        try:
            # 构建路线规划参数
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "output": "json",
                "ak": self.api_key
            }
            
            # 调用百度地图路线规划API
            url = f"{self.base_url}/direction/v2/{mode}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == 0:
                route = data.get("result", {}).get("routes", [{}])[0]
                
                return {
                    "success": True,
                    "data": {
                        "distance": route.get("distance", 0),
                        "duration": route.get("duration", 0),
                        "steps": route.get("steps", []),
                        "mode": mode,
                        "origin": origin,
                        "destination": destination
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"路线计算失败: {data.get('message', '未知错误')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"路线计算异常: {str(e)}"
            }
    
    
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        逆地理编码（坐标转地址）
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            逆地理编码结果
        """
        try:
            params = {
                "location": f"{lat},{lng}",
                "output": "json",
                "ak": self.api_key
            }
            
            url = f"{self.base_url}/geocoding/v2/"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == 0:
                result = data.get("result", {})
                
                return {
                    "success": True,
                    "data": {
                        "address": result.get("formatted_address", ""),
                        "location": {"lat": lat, "lng": lng},
                        "business": result.get("business", ""),
                        "address_components": result.get("addressComponent", {})
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"逆地理编码失败: {data.get('message', '未知错误')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"逆地理编码异常: {str(e)}"
            }


# 创建全局实例
baidu_map_tools = BaiduMapTools()
