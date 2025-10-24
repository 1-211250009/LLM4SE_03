"""工具定义模块

定义LLM可以调用的工具函数
"""

from typing import Dict, Any, List

def get_poi_search_tool() -> Dict[str, Any]:
    """获取POI搜索工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "search_poi",
            "description": "搜索指定城市的景点、餐厅、酒店等POI信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，如'故宫'、'天安门'、'颐和园'等"
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'等"
                    },
                    "category": {
                        "type": "string",
                        "description": "POI分类",
                        "enum": ["attraction", "restaurant", "hotel", "shopping", "entertainment"],
                        "default": "attraction"
                    }
                },
                "required": ["keyword", "city"]
            }
        }
    }

def get_route_calculation_tool() -> Dict[str, Any]:
    """获取路线计算工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "calculate_route",
            "description": "计算两个地点之间的路线和距离",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "起点，可以是地址或坐标"
                    },
                    "destination": {
                        "type": "string",
                        "description": "终点，可以是地址或坐标"
                    },
                    "mode": {
                        "type": "string",
                        "description": "交通方式",
                        "enum": ["driving", "walking", "transit", "bicycling"],
                        "default": "driving"
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    }

def get_mark_location_tool() -> Dict[str, Any]:
    """获取标记地点工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "mark_location",
            "description": "在地图上标记指定地点",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "要标记的地点名称或地址，如'故宫'、'天安门'、'北京站'等"
                    },
                    "label": {
                        "type": "string",
                        "description": "标记的标签名称，如果不提供则使用地点名称",
                        "default": ""
                    },
                    "category": {
                        "type": "string",
                        "description": "地点分类",
                        "enum": ["attraction", "restaurant", "hotel", "transport", "shopping", "entertainment"],
                        "default": "attraction"
                    }
                },
                "required": ["location"]
            }
        }
    }

def get_plan_trip_tool() -> Dict[str, Any]:
    """获取行程规划工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "plan_trip",
            "description": "基于选中的地点规划完整行程",
            "parameters": {
                "type": "object",
                "properties": {
                    "selected_locations": {
                        "type": "array",
                        "description": "用户选中的地点ID列表",
                        "items": {
                            "type": "string"
                        }
                    },
                    "trip_duration": {
                        "type": "string",
                        "description": "行程时长，如'1天'、'2天'、'半天'等",
                        "default": "1天"
                    },
                    "transport_mode": {
                        "type": "string",
                        "description": "主要交通方式",
                        "enum": ["walking", "driving", "transit", "mixed"],
                        "default": "mixed"
                    },
                    "interests": {
                        "type": "array",
                        "description": "用户兴趣偏好",
                        "items": {
                            "type": "string"
                        },
                        "default": []
                    }
                },
                "required": ["selected_locations"]
            }
        }
    }

def get_all_tools() -> List[Dict[str, Any]]:
    """获取所有工具定义"""
    return [
        get_poi_search_tool(),
        get_route_calculation_tool(),
        get_mark_location_tool(),
        get_plan_trip_tool()
    ]
