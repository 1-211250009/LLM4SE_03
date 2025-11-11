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

def get_create_trip_tool() -> Dict[str, Any]:
    """获取创建行程工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "create_trip",
            "description": "创建新的旅行行程",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "行程标题"
                    },
                    "destination": {
                        "type": "string",
                        "description": "目的地"
                    },
                    "duration_days": {
                        "type": "integer",
                        "description": "行程天数"
                    },
                    "budget": {
                        "type": "number",
                        "description": "预算金额"
                    },
                    "traveler_count": {
                        "type": "integer",
                        "description": "同行人数",
                        "default": 1
                    },
                    "preferences": {
                        "type": "object",
                        "description": "用户偏好（如美食、购物、文化等）"
                    }
                },
                "required": ["title", "destination", "duration_days"]
            }
        }
    }

def get_add_itinerary_item_tool() -> Dict[str, Any]:
    """获取添加行程节点工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "add_itinerary_item",
            "description": "向行程中添加一个新的节点（景点、餐厅、酒店等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "string",
                        "description": "行程ID"
                    },
                    "day_number": {
                        "type": "integer",
                        "description": "第几天"
                    },
                    "name": {
                        "type": "string",
                        "description": "节点名称"
                    },
                    "category": {
                        "type": "string",
                        "description": "节点类别",
                        "enum": ["attraction", "restaurant", "hotel", "transport", "shopping", "other"]
                    },
                    "address": {
                        "type": "string",
                        "description": "地址"
                    },
                    "coordinates": {
                        "type": "object",
                        "description": "坐标",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"}
                        }
                    },
                    "start_time": {
                        "type": "string",
                        "description": "开始时间（HH:MM格式）"
                    },
                    "estimated_duration": {
                        "type": "integer",
                        "description": "预计停留时长（分钟）"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "预计费用"
                    }
                },
                "required": ["trip_id", "day_number", "name", "category"]
            }
        }
    }

def get_add_expense_tool() -> Dict[str, Any]:
    """获取添加费用工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "记录一笔旅行费用",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "string",
                        "description": "行程ID"
                    },
                    "amount": {
                        "type": "number",
                        "description": "金额"
                    },
                    "category": {
                        "type": "string",
                        "description": "费用类别",
                        "enum": ["transportation", "accommodation", "food", "attraction", "shopping", "other"]
                    },
                    "description": {
                        "type": "string",
                        "description": "费用描述"
                    },
                    "itinerary_item_id": {
                        "type": "string",
                        "description": "关联的行程节点ID（可选）"
                    },
                    "location": {
                        "type": "string",
                        "description": "消费地点"
                    }
                },
                "required": ["trip_id", "amount", "category"]
            }
        }
    }

def get_query_trip_budget_tool() -> Dict[str, Any]:
    """获取查询行程预算工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "query_trip_budget",
            "description": "查询行程的预算使用情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "string",
                        "description": "行程ID"
                    }
                },
                "required": ["trip_id"]
            }
        }
    }

def get_list_trips_tool() -> Dict[str, Any]:
    """获取查询行程列表工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "list_trips",
            "description": "获取用户的行程列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "行程状态筛选",
                        "enum": ["all", "draft", "planned", "active", "completed"],
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 10
                    }
                }
            }
        }
    }

def get_all_tools() -> List[Dict[str, Any]]:
    """获取所有工具定义"""
    return [
        # 地图相关工具
        get_poi_search_tool(),
        get_route_calculation_tool(),
        get_mark_location_tool(),
        
        # 行程管理工具
        get_create_trip_tool(),
        get_add_itinerary_item_tool(),
        get_plan_trip_tool(),
        get_list_trips_tool(),
        
        # 费用管理工具
        get_add_expense_tool(),
        get_query_trip_budget_tool()
    ]
