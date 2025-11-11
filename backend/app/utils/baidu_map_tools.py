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
    
    def calculate_route(self, origin: Dict[str, float], destination: Dict[str, float], 
                       mode: str = "driving") -> Dict[str, Any]:
        """
        计算路线
        
        Args:
            origin: 起点坐标 {"lat": 39.9042, "lng": 116.4074}
            destination: 终点坐标 {"lat": 39.9042, "lng": 116.4074}
            mode: 交通方式 (driving, transit, walking, bicycling)
            
        Returns:
            路线计算结果，包含overview_polyline和bounds
        """
        try:
            # 转换坐标为字符串格式
            origin_str = f"{origin.get('lat', 0)},{origin.get('lng', 0)}"
            destination_str = f"{destination.get('lat', 0)},{destination.get('lng', 0)}"
            
            # 构建路线规划参数
            params = {
                "origin": origin_str,
                "destination": destination_str,
                "output": "json",
                "ak": self.api_key,
                "tactics": "11"  # 不走高速
            }
            
            # 调用百度地图路线规划API
            # 注意：百度地图API v2使用direction/v2/driving
            url = f"{self.base_url}/direction/v2/driving"
            
            if mode == "walking":
                url = f"{self.base_url}/direction/v2/walking"
            elif mode == "transit":
                url = f"{self.base_url}/direction/v2/transit"
            elif mode == "riding":
                url = f"{self.base_url}/direction/v2/riding"
            
            print(f"DEBUG: 路线规划API调用 - URL: {url}")
            print(f"DEBUG: 参数: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"DEBUG: 路线规划API响应: {data}")
            
            if data.get("status") == 0:
                result = data.get("result", {})
                routes = result.get("routes", [])
                
                if routes and len(routes) > 0:
                    route = routes[0]
                    
                    # 提取路径点和边界
                    steps = route.get("steps", [])
                    points = []
                    bounds = {
                        "southwest": {"lat": float('inf'), "lng": float('inf')},
                        "northeast": {"lat": float('-inf'), "lng": float('-inf')}
                    }
                    
                    # 构建路径折线
                    # 注意：百度地图API返回的path格式是 lng,lat;lng,lat;...（经度在前，纬度在后）
                    for step in steps:
                        path = step.get("path", "")
                        if path:
                            # path格式：lng1,lat1;lng2,lat2;...
                            step_points = path.split(';')
                            for point_str in step_points:
                                if point_str and point_str.strip():
                                    coords = point_str.split(',')
                                    if len(coords) == 2:
                                        lng = float(coords[0].strip())  # 第一个是经度
                                        lat = float(coords[1].strip())  # 第二个是纬度
                                        points.append(f"{lng},{lat}")  # 保持 lng,lat 格式
                                        
                                        # 更新边界
                                        bounds["southwest"]["lat"] = min(bounds["southwest"]["lat"], lat)
                                        bounds["southwest"]["lng"] = min(bounds["southwest"]["lng"], lng)
                                        bounds["northeast"]["lat"] = max(bounds["northeast"]["lat"], lat)
                                        bounds["northeast"]["lng"] = max(bounds["northeast"]["lng"], lng)
                    
                    # 生成overview_polyline（分号分隔的点字符串）
                    overview_polyline = ";".join(points)
                
                return {
                    "success": True,
                    "data": {
                        "distance": route.get("distance", 0),
                        "duration": route.get("duration", 0),
                            "overview_polyline": overview_polyline,
                            "bounds": bounds,
                            "steps": steps,
                        "mode": mode,
                        "origin": {
                            "lat": float(origin.get("lat", 0)),
                            "lng": float(origin.get("lng", 0))
                        },
                        "destination": {
                            "lat": float(destination.get("lat", 0)),
                            "lng": float(destination.get("lng", 0))
                        }
                        }
                    }
            else:
                return {
                    "success": False,
                    "error": f"路线计算失败: {data.get('message', '未知错误')}",
                    "status": data.get("status")
                }
                
        except Exception as e:
            print(f"路线计算异常: {e}")
            import traceback
            traceback.print_exc()
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
