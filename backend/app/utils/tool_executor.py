"""工具执行器模块

负责执行LLM调用的工具函数
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.trip import Trip, Itinerary, ItineraryItem, Expense
from app.utils.baidu_map_tools import baidu_map_tools


class ToolExecutor:
    """工具执行器类"""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            # 地图相关工具
            if tool_name == "search_poi":
                return await self._search_poi(parameters)
            elif tool_name == "calculate_route":
                return await self._calculate_route(parameters)
            elif tool_name == "mark_location":
                return await self._mark_location(parameters)
            
            # 行程管理工具
            elif tool_name == "create_trip":
                return await self._create_trip(parameters)
            elif tool_name == "add_itinerary_item":
                return await self._add_itinerary_item(parameters)
            elif tool_name == "plan_trip":
                return await self._plan_trip(parameters)
            elif tool_name == "list_trips":
                return await self._list_trips(parameters)
            
            # 费用管理工具
            elif tool_name == "add_expense":
                return await self._add_expense(parameters)
            elif tool_name == "query_trip_budget":
                return await self._query_trip_budget(parameters)
            
            else:
                return {
                    "success": False,
                    "error": f"未知的工具: {tool_name}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"工具执行失败: {str(e)}"
            }
    
    # ========== 地图相关工具 ==========
    
    async def _search_poi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """搜索POI"""
        try:
            keyword = params.get("keyword", "")
            city = params.get("city", "北京")
            category = params.get("category", "attraction")
            
            result = baidu_map_tools.search_poi(
                keyword=keyword,
                city=city,
                category=category
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"POI搜索失败: {str(e)}"
            }
    
    async def _calculate_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算路线"""
        try:
            origin = params.get("origin")
            destination = params.get("destination")
            mode = params.get("mode", "driving")
            
            result = baidu_map_tools.calculate_route(
                origin=origin,
                destination=destination,
                mode=mode
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"路线计算失败: {str(e)}"
            }
    
    async def _mark_location(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """标记地点"""
        try:
            location = params.get("location")
            label = params.get("label", location)
            category = params.get("category", "attraction")
            
            # 使用地理编码获取坐标
            result = baidu_map_tools.geocode(location)
            
            if result.get("success"):
                coordinates = result.get("data", {}).get("coordinates")
                marker_id = f"marker_{uuid.uuid4().hex[:8]}"
                
                return {
                    "success": True,
                    "data": {
                        "marker_id": marker_id,
                        "location": location,
                        "label": label,
                        "category": category,
                        "coordinates": coordinates
                    }
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"标记地点失败: {str(e)}"
            }
    
    # ========== 行程管理工具 ==========
    
    async def _create_trip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建行程"""
        try:
            trip = Trip(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                title=params.get("title"),
                destination=params.get("destination"),
                duration_days=params.get("duration_days", 1),
                budget_total=params.get("budget"),
                traveler_count=params.get("traveler_count", 1),
                preferences=params.get("preferences", {}),
                status="draft"
            )
            
            self.db.add(trip)
            self.db.commit()
            self.db.refresh(trip)
            
            return {
                "success": True,
                "data": {
                    "trip_id": trip.id,
                    "title": trip.title,
                    "destination": trip.destination,
                    "duration_days": trip.duration_days,
                    "budget_total": trip.budget_total,
                    "traveler_count": trip.traveler_count
                },
                "message": f"成功创建行程：{trip.title}"
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"创建行程失败: {str(e)}"
            }
    
    async def _add_itinerary_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """添加行程节点"""
        try:
            trip_id = params.get("trip_id")
            day_number = params.get("day_number")
            
            # 检查行程是否存在
            trip = self.db.query(Trip).filter(
                Trip.id == trip_id,
                Trip.user_id == self.user_id
            ).first()
            
            if not trip:
                return {
                    "success": False,
                    "error": "行程不存在"
                }
            
            # 查找或创建当天的Itinerary
            itinerary = self.db.query(Itinerary).filter(
                Itinerary.trip_id == trip_id,
                Itinerary.day_number == day_number
            ).first()
            
            if not itinerary:
                itinerary = Itinerary(
                    id=str(uuid.uuid4()),
                    trip_id=trip_id,
                    day_number=day_number,
                    title=f"第 {day_number} 天"
                )
                self.db.add(itinerary)
                self.db.flush()
            
            # 创建行程节点
            coordinates = params.get("coordinates")
            if coordinates and isinstance(coordinates, dict):
                coordinates_json = coordinates
            else:
                coordinates_json = None
            
            # 获取当前最大的order_index
            max_order = self.db.query(ItineraryItem).filter(
                ItineraryItem.itinerary_id == itinerary.id
            ).count()
            
            item = ItineraryItem(
                id=str(uuid.uuid4()),
                itinerary_id=itinerary.id,
                name=params.get("name"),
                category=params.get("category"),
                address=params.get("address"),
                coordinates=coordinates_json,
                start_time=params.get("start_time"),
                estimated_duration=params.get("estimated_duration"),
                estimated_cost=params.get("estimated_cost"),
                order_index=max_order
            )
            
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            
            return {
                "success": True,
                "data": {
                    "item_id": item.id,
                    "trip_id": trip_id,
                    "day_number": day_number,
                    "name": item.name,
                    "category": item.category,
                    "address": item.address,
                    "coordinates": item.coordinates
                },
                "message": f"成功添加行程节点：{item.name}"
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"添加行程节点失败: {str(e)}"
            }
    
    async def _plan_trip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """规划行程"""
        # 这个函数主要用于生成行程规划建议，不直接操作数据库
        try:
            selected_locations = params.get("selected_locations", [])
            trip_duration = params.get("trip_duration", "1天")
            transport_mode = params.get("transport_mode", "mixed")
            interests = params.get("interests", [])
            
            return {
                "success": True,
                "data": {
                    "trip_plan": {
                        "title": f"{trip_duration}行程规划",
                        "duration": trip_duration,
                        "transport_mode": transport_mode,
                        "locations": selected_locations,
                        "schedule": [],  # 由LLM生成详细安排
                        "routes": [],    # 路线信息
                        "tips": []       # 旅行建议
                    }
                },
                "message": "行程规划生成成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"行程规划失败: {str(e)}"
            }
    
    async def _list_trips(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取行程列表"""
        try:
            status = params.get("status", "all")
            limit = params.get("limit", 10)
            
            query = self.db.query(Trip).filter(Trip.user_id == self.user_id)
            
            if status != "all":
                query = query.filter(Trip.status == status)
            
            trips = query.order_by(Trip.created_at.desc()).limit(limit).all()
            
            trip_list = []
            for trip in trips:
                trip_list.append({
                    "id": trip.id,
                    "title": trip.title,
                    "destination": trip.destination,
                    "duration_days": trip.duration_days,
                    "budget_total": trip.budget_total,
                    "status": trip.status,
                    "created_at": trip.created_at.isoformat() if trip.created_at else None
                })
            
            return {
                "success": True,
                "data": {
                    "trips": trip_list,
                    "count": len(trip_list)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取行程列表失败: {str(e)}"
            }
    
    # ========== 费用管理工具 ==========
    
    async def _add_expense(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """添加费用"""
        try:
            trip_id = params.get("trip_id")
            
            # 检查行程是否存在
            trip = self.db.query(Trip).filter(
                Trip.id == trip_id,
                Trip.user_id == self.user_id
            ).first()
            
            if not trip:
                return {
                    "success": False,
                    "error": "行程不存在"
                }
            
            expense = Expense(
                id=str(uuid.uuid4()),
                trip_id=trip_id,
                itinerary_item_id=params.get("itinerary_item_id"),
                amount=params.get("amount"),
                currency=trip.currency,
                category=params.get("category"),
                description=params.get("description"),
                location=params.get("location"),
                expense_date=datetime.now()
            )
            
            self.db.add(expense)
            self.db.commit()
            self.db.refresh(expense)
            
            # 计算总花费
            total_expenses = self.db.query(Expense).filter(
                Expense.trip_id == trip_id
            ).all()
            total_amount = sum(e.amount for e in total_expenses)
            
            remaining_budget = None
            if trip.budget_total:
                remaining_budget = trip.budget_total - total_amount
            
            return {
                "success": True,
                "data": {
                    "expense_id": expense.id,
                    "amount": expense.amount,
                    "category": expense.category,
                    "description": expense.description,
                    "total_expenses": total_amount,
                    "remaining_budget": remaining_budget
                },
                "message": f"成功记录费用：{expense.description or expense.category}"
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"添加费用失败: {str(e)}"
            }
    
    async def _query_trip_budget(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询行程预算"""
        try:
            trip_id = params.get("trip_id")
            
            # 检查行程是否存在
            trip = self.db.query(Trip).filter(
                Trip.id == trip_id,
                Trip.user_id == self.user_id
            ).first()
            
            if not trip:
                return {
                    "success": False,
                    "error": "行程不存在"
                }
            
            # 计算总花费
            expenses = self.db.query(Expense).filter(
                Expense.trip_id == trip_id
            ).all()
            
            total_expenses = sum(e.amount for e in expenses)
            
            # 按类别统计
            category_breakdown = {}
            for expense in expenses:
                category = expense.category
                if category not in category_breakdown:
                    category_breakdown[category] = 0
                category_breakdown[category] += expense.amount
            
            remaining_budget = None
            budget_usage_percent = None
            if trip.budget_total:
                remaining_budget = trip.budget_total - total_expenses
                budget_usage_percent = (total_expenses / trip.budget_total * 100) if trip.budget_total > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "trip_id": trip_id,
                    "trip_title": trip.title,
                    "total_budget": trip.budget_total,
                    "total_expenses": total_expenses,
                    "remaining_budget": remaining_budget,
                    "budget_usage_percent": budget_usage_percent,
                    "category_breakdown": category_breakdown,
                    "expense_count": len(expenses)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"查询预算失败: {str(e)}"
            }

