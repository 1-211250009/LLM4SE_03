"""
行程规划智能体服务
通过对话方式帮助用户管理行程节点（添加、修改、删除）
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..models.trip import Trip, Itinerary, ItineraryItem
from ..schemas.trip import ItineraryItemCreate, ItineraryItemUpdate, POICategory
from .llm_service import LLMService


class TripPlanningAIService:
    """行程规划智能体服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def process_natural_language_query(
        self, 
        query: str, 
        user_id: str,
        trip_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """处理自然语言查询，返回响应和待确认的操作"""
        try:
            # 获取行程信息
            trip = self.db.query(Trip).filter(
                Trip.id == trip_id,
                Trip.user_id == user_id
            ).first()
            
            if not trip:
                raise ValueError("行程不存在或无权限")
            
            # 构建系统提示
            system_prompt = self._build_system_prompt(trip)
            
            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加历史对话
            if conversation_history:
                messages.extend(conversation_history)
            
            # 添加当前查询
            messages.append({"role": "user", "content": query})
            
            # 调用LLM处理查询
            response = await self.llm_service.chat_completion(
                messages=messages,
                tools=self._get_available_tools()
            )
            
            # 检查响应是否有效
            if not response:
                return {
                    'content': '抱歉，AI助手暂时无法响应，请稍后再试。',
                    'pending_action': None
                }
            
            # 如果有工具调用，返回待确认的操作
            if response.get('tool_calls'):
                tool_call = response['tool_calls'][0]  # 取第一个工具调用
                
                # 获取AI的回复内容，如果为空则使用默认提示
                content = response.get('content', '')
                if not content or content.strip() == '':
                    function_name = tool_call['function']['name']
                    action_names = {
                        'add_itinerary_item': '我准备为您添加行程节点',
                        'update_itinerary_item': '我准备为您更新行程节点',
                        'delete_itinerary_item': '我准备为您删除行程节点'
                    }
                    content = action_names.get(function_name, '我准备执行以下操作，请确认：')
                
                return {
                    'content': content,
                    'pending_action': {
                        'id': tool_call.get('id'),
                        'function_name': tool_call['function']['name'],
                        'arguments': tool_call['function']['arguments']
                    }
                }
            
            # 返回普通响应
            content = response.get('content', '')
            if not content or content.strip() == '':
                content = '抱歉，我无法理解您的请求。'
            
            return {
                'content': content,
                'pending_action': None
            }
        except Exception as e:
            import traceback
            print(f"process_natural_language_query error: {str(e)}")
            traceback.print_exc()
            raise

    def _build_system_prompt(self, trip: Trip) -> str:
        """构建系统提示，包含行程的详细信息"""
        prompt = f"""你是一名AI行程规划助手，帮助用户管理旅行行程中的节点（添加、修改、删除）。

你的角色定位：
- 帮助用户添加行程节点、删除行程节点、修改行程节点
- 通过友好的对话，收集操作所需的信息
- 确保收集足够的信息之后，再进行工具调用
- 工具调用会在前端显示确认卡片，由用户确认后执行

当前行程信息：
- 行程ID：{trip.id}
- 行程标题：{trip.title}
- 目的地：{trip.destination or '未设置'}
- 开始日期：{trip.start_date.strftime('%Y-%m-%d') if trip.start_date else '未设置'}
- 结束日期：{trip.end_date.strftime('%Y-%m-%d') if trip.end_date else '未设置'}
- 行程天数：{trip.duration_days}天
- 总预算：{trip.budget_total or '未设置'}
- 同行人数：{trip.traveler_count}人
- 行程状态：{trip.status}
"""

        # 添加行程安排信息
        if trip.itineraries:
            prompt += "\n当前行程安排（重要：每个行程安排的ID用于添加节点）：\n"
            for itinerary in sorted(trip.itineraries, key=lambda x: x.day_number):
                prompt += f"\n第{itinerary.day_number}天"
                if itinerary.date:
                    prompt += f" ({itinerary.date.strftime('%Y-%m-%d')})"
                if itinerary.title:
                    prompt += f" - {itinerary.title}"
                prompt += f"\n  行程安排ID：{itinerary.id}（用于添加节点到此天）\n"
                
                if itinerary.items:
                    for idx, item in enumerate(sorted(itinerary.items, key=lambda x: x.order_index or 0), 1):
                        prompt += f"  {idx}. {item.name}"
                        if item.start_time:
                            prompt += f" ({item.start_time}"
                            if item.end_time:
                                prompt += f" - {item.end_time}"
                            prompt += ")"
                        if item.address:
                            prompt += f" - {item.address}"
                        if item.description:
                            prompt += f"\n     描述：{item.description}"
                        prompt += f"\n     节点ID：{item.id}\n"
                else:
                    prompt += "  暂无节点\n"
        else:
            prompt += "\n当前行程安排：暂无行程安排\n"
            prompt += "\n注意：如果用户要添加节点，需要先创建行程安排（itinerary）。\n"

        prompt += """
重要提示：
1. 当用户要求执行操作（如添加、修改、删除节点）时，必须立即使用相应的工具函数
2. 工具函数调用会在前端显示确认卡片，由用户确认后执行，所以你不需要询问用户确认，直接调用工具即可
3. **关键**：itinerary_id和item_id必须从上面提供的"当前行程安排"信息中获取，不要询问用户这些ID。用户说"第1天"时，你应该从行程安排信息中找到第1天的itinerary_id；用户说节点名称时，你应该从节点列表中找到对应的item_id
4. 如果用户提供了足够的信息（节点名称、时间、分类等），直接调用工具函数，使用从行程安排信息中获取的ID
5. 如果缺少必要信息（如节点名称、时间等），可以询问用户补充，但不要询问ID
6. 在回答用户问题时，要结合当前的行程信息和节点数据
7. 提供清晰、准确的操作建议

节点信息字段说明：
- name: 节点名称（必填）
- description: 节点描述（可选）
- address: 地址（可选）
- category: 分类，可选值：attraction（景点）、restaurant（餐厅）、hotel（酒店）、shopping（购物）、transport（交通）、other（其他）
- start_time: 开始时间，格式：HH:MM，例如："09:00"（可选）
- end_time: 结束时间，格式：HH:MM，例如："17:00"（可选）
- estimated_duration: 预计停留时长（分钟，可选）
- estimated_cost: 预计费用（可选）
- order_index: 顺序索引，从0开始（可选，默认为0）
- itinerary_id: 行程安排ID（可选），如果提供了day_number或date，可以省略
- day_number: 第几天（可选），例如：1表示第1天。如果提供了itinerary_id，可以省略
- date: 日期（可选），格式：YYYY-MM-DD。如果提供了itinerary_id或day_number，可以省略
- 注意：必须提供itinerary_id、day_number或date中的至少一个

工具使用示例：
- 用户说"在第1天添加一个景点，名称是天安门，时间是上午9点到11点" 
  -> 如果第1天的itinerary已存在，从行程安排信息中获取itinerary_id；如果不存在，使用day_number
  -> 例如（itinerary存在）：{"itinerary_id": "从行程安排信息中获取的第1天的itinerary_id", "name": "天安门", "category": "attraction", "start_time": "09:00", "end_time": "11:00"}
  -> 例如（itinerary不存在）：{"day_number": 1, "name": "天安门", "category": "attraction", "start_time": "09:00", "end_time": "11:00"}

- 用户说"删除第1天的第一个节点"
  -> 从上面的行程安排信息中找到第1天的itinerary_id和第一个节点的item_id，然后调用delete_itinerary_item工具
  -> 例如：{"itinerary_id": "从行程安排信息中获取的第1天的itinerary_id", "item_id": "从节点列表中获取的第一个节点的ID"}

- 用户说"修改节点xxx的名称为xxx"
  -> 从上面的行程安排信息中找到节点所属的itinerary_id和节点ID，然后调用update_itinerary_item工具
  -> 例如：{"itinerary_id": "节点所属的itinerary_id", "item_id": "节点ID", "name": "新名称"}

重要：
1. 你必须从上面提供的"当前行程安排"信息中获取itinerary_id和item_id，不要询问用户这些ID
2. 如果用户说"第X天"，你可以：
   - 如果该天的itinerary已存在，使用itinerary_id
   - 如果该天的itinerary不存在，使用day_number（系统会自动创建itinerary）
3. 用户只需要告诉你"第几天"或"节点名称"，你就能从行程安排信息中找到对应的ID，或者使用day_number让系统自动创建

注意：你有可用的工具函数（tools），当用户要求执行操作时，必须调用相应的工具函数。不要只是回复文字，要实际调用工具！
"""
        return prompt

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_itinerary_item",
                    "description": "添加新的行程节点",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "itinerary_id": {
                                "type": "string",
                                "description": "行程安排ID（可选），如果提供了day_number或date，可以省略"
                            },
                            "day_number": {
                                "type": "integer",
                                "description": "第几天（可选），如果提供了itinerary_id，可以省略。如果既没有itinerary_id也没有day_number，必须提供date"
                            },
                            "date": {
                                "type": "string",
                                "description": "日期（可选），格式：YYYY-MM-DD，例如：'2025-01-21'。如果提供了itinerary_id或day_number，可以省略"
                            },
                            "name": {
                                "type": "string",
                                "description": "节点名称（必填），例如：'天安门'、'故宫博物院'"
                            },
                            "description": {
                                "type": "string",
                                "description": "节点描述（可选）"
                            },
                            "address": {
                                "type": "string",
                                "description": "地址（可选）"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["attraction", "restaurant", "hotel", "shopping", "transport", "other"],
                                "description": "分类（可选），默认：other"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "开始时间（可选），格式：HH:MM，例如：'09:00'"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "结束时间（可选），格式：HH:MM，例如：'17:00'"
                            },
                            "estimated_duration": {
                                "type": "integer",
                                "description": "预计停留时长（分钟，可选）"
                            },
                            "estimated_cost": {
                                "type": "number",
                                "description": "预计费用（可选）"
                            },
                            "order_index": {
                                "type": "integer",
                                "description": "顺序索引（可选，默认为0）"
                            }
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_itinerary_item",
                    "description": "更新现有的行程节点",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "itinerary_id": {
                                "type": "string",
                                "description": "行程安排ID（必填）"
                            },
                            "item_id": {
                                "type": "string",
                                "description": "节点ID（必填）"
                            },
                            "name": {
                                "type": "string",
                                "description": "节点名称（可选）"
                            },
                            "description": {
                                "type": "string",
                                "description": "节点描述（可选）"
                            },
                            "address": {
                                "type": "string",
                                "description": "地址（可选）"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["ATTRACTION", "RESTAURANT", "HOTEL", "SHOPPING", "TRANSPORTATION", "ENTERTAINMENT", "OTHER"],
                                "description": "分类（可选）"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "开始时间（可选），格式：HH:MM"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "结束时间（可选），格式：HH:MM"
                            },
                            "estimated_duration": {
                                "type": "integer",
                                "description": "预计停留时长（分钟，可选）"
                            },
                            "estimated_cost": {
                                "type": "number",
                                "description": "预计费用（可选）"
                            },
                            "order_index": {
                                "type": "integer",
                                "description": "顺序索引（可选）"
                            }
                        },
                        "required": ["itinerary_id", "item_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_itinerary_item",
                    "description": "删除行程节点",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "itinerary_id": {
                                "type": "string",
                                "description": "行程安排ID（必填）"
                            },
                            "item_id": {
                                "type": "string",
                                "description": "节点ID（必填）"
                            }
                        },
                        "required": ["itinerary_id", "item_id"]
                    }
                }
            }
        ]
    
    async def execute_tool_call(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        user_id: str,
        trip_id: str
    ) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            if function_name == "add_itinerary_item":
                result = await self._add_itinerary_item(arguments, user_id, trip_id)
                return {
                    "message": f"✅ 节点添加成功：{result.get('name', '')}",
                    "data": result
                }
            elif function_name == "update_itinerary_item":
                result = await self._update_itinerary_item(arguments, user_id, trip_id)
                return {
                    "message": f"✅ 节点更新成功：{result.get('name', '')}",
                    "data": result
                }
            elif function_name == "delete_itinerary_item":
                result = await self._delete_itinerary_item(arguments, user_id, trip_id)
                return {
                    "message": "✅ 节点删除成功",
                    "data": result
                }
            else:
                raise ValueError(f"未知功能：{function_name}")
        
        except Exception as e:
            raise Exception(f"执行失败：{str(e)}")
    
    async def _add_itinerary_item(self, arguments: Dict[str, Any], user_id: str, trip_id: str) -> Dict[str, Any]:
        """添加行程节点"""
        from ..models.trip import ItineraryItem as ItineraryItemModel
        from sqlalchemy.orm import joinedload
        from datetime import datetime, date as date_type
        
        # 获取trip信息
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()
        
        if not trip:
            raise ValueError("行程不存在或无权限")
        
        # 确定要使用的itinerary
        itinerary = None
        itinerary_id = arguments.get('itinerary_id')
        
        if itinerary_id:
            # 如果提供了itinerary_id，直接使用
            itinerary = self.db.query(Itinerary).options(
                joinedload(Itinerary.trip)
            ).filter(
                Itinerary.id == itinerary_id
            ).first()
            
            if not itinerary:
                raise ValueError("行程安排不存在")
            
            if itinerary.trip.user_id != user_id or itinerary.trip.id != trip_id:
                raise ValueError("无权限操作此行程")
        else:
            # 如果没有提供itinerary_id，尝试通过day_number或date查找或创建
            day_number = arguments.get('day_number')
            date_str = arguments.get('date')
            
            if not day_number and not date_str:
                raise ValueError("必须提供itinerary_id、day_number或date之一")
            
            # 如果提供了date，计算day_number
            if date_str and not day_number:
                if not trip.start_date:
                    raise ValueError("行程未设置开始日期，无法计算天数")
                try:
                    if isinstance(date_str, str):
                        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        target_date = date_str
                    start_date = trip.start_date if isinstance(trip.start_date, date_type) else trip.start_date.date()
                    day_number = (target_date - start_date).days + 1
                except Exception as e:
                    raise ValueError(f"日期格式错误或无法计算天数: {str(e)}")
            
            # 查找是否已存在该day_number的itinerary
            itinerary = self.db.query(Itinerary).options(
                joinedload(Itinerary.trip)
            ).filter(
                Itinerary.trip_id == trip_id,
                Itinerary.day_number == day_number
            ).first()
            
            # 如果不存在，创建新的itinerary
            if not itinerary:
                # 计算日期
                if date_str:
                    if isinstance(date_str, str):
                        itinerary_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        itinerary_date = date_str
                elif trip.start_date:
                    start_date = trip.start_date if isinstance(trip.start_date, date_type) else trip.start_date.date()
                    itinerary_date = start_date + timedelta(days=day_number - 1)
                else:
                    raise ValueError("无法确定日期，请提供date或确保行程有开始日期")
                
                itinerary = Itinerary(
                    trip_id=trip_id,
                    day_number=day_number,
                    date=itinerary_date,
                    title=f"第{day_number}天",
                    description=''
                )
                self.db.add(itinerary)
                self.db.flush()
                self.db.refresh(itinerary)
        
        # 构建节点数据
        category_str = arguments.get('category', 'other')
        try:
            category = POICategory(category_str)
        except ValueError:
            category = POICategory.OTHER
        
        item_data = ItineraryItemCreate(
            name=arguments['name'],
            description=arguments.get('description'),
            address=arguments.get('address'),
            category=category,
            start_time=arguments.get('start_time'),
            end_time=arguments.get('end_time'),
            estimated_duration=arguments.get('estimated_duration'),
            estimated_cost=arguments.get('estimated_cost'),
            order_index=arguments.get('order_index', 0)
        )
        
        # 创建节点
        item = ItineraryItemModel(
            itinerary_id=itinerary.id,
            name=item_data.name,
            description=item_data.description,
            address=item_data.address,
            category=item_data.category,
            start_time=item_data.start_time,
            end_time=item_data.end_time,
            estimated_duration=item_data.estimated_duration,
            estimated_cost=item_data.estimated_cost,
            order_index=item_data.order_index,
            is_completed=False
        )
        
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        return {
            "id": item.id,
            "name": item.name,
            "itinerary_id": item.itinerary_id
        }
    
    async def _update_itinerary_item(self, arguments: Dict[str, Any], user_id: str, trip_id: str) -> Dict[str, Any]:
        """更新行程节点"""
        from ..models.trip import ItineraryItem as ItineraryItemModel
        from sqlalchemy.orm import joinedload
        
        # 验证节点是否存在且有权限
        item = self.db.query(ItineraryItemModel).options(
            joinedload(ItineraryItemModel.itinerary).joinedload(Itinerary.trip)
        ).filter(
            ItineraryItemModel.id == arguments['item_id'],
            ItineraryItemModel.itinerary_id == arguments['itinerary_id']
        ).first()
        
        if not item:
            raise ValueError("节点不存在")
        
        if item.itinerary.trip.user_id != user_id or item.itinerary.trip.id != trip_id:
            raise ValueError("无权限操作此节点")
        
        # 构建更新数据
        category = None
        if arguments.get('category'):
            try:
                category = POICategory(arguments['category'])
            except ValueError:
                category = None
        
        update_data = ItineraryItemUpdate(
            name=arguments.get('name'),
            description=arguments.get('description'),
            address=arguments.get('address'),
            category=category,
            start_time=arguments.get('start_time'),
            end_time=arguments.get('end_time'),
            estimated_duration=arguments.get('estimated_duration'),
            estimated_cost=arguments.get('estimated_cost'),
            order_index=arguments.get('order_index')
        )
        
        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        self.db.commit()
        self.db.refresh(item)
        
        return {
            "id": item.id,
            "name": item.name,
            "itinerary_id": item.itinerary_id
        }
    
    async def _delete_itinerary_item(self, arguments: Dict[str, Any], user_id: str, trip_id: str) -> Dict[str, Any]:
        """删除行程节点"""
        from ..models.trip import ItineraryItem as ItineraryItemModel
        from sqlalchemy.orm import joinedload
        
        # 验证节点是否存在且有权限
        item = self.db.query(ItineraryItemModel).options(
            joinedload(ItineraryItemModel.itinerary).joinedload(Itinerary.trip)
        ).filter(
            ItineraryItemModel.id == arguments['item_id'],
            ItineraryItemModel.itinerary_id == arguments['itinerary_id']
        ).first()
        
        if not item:
            raise ValueError("节点不存在")
        
        if item.itinerary.trip.user_id != user_id or item.itinerary.trip.id != trip_id:
            raise ValueError("无权限操作此节点")
        
        item_id = item.id
        item_name = item.name
        
        self.db.delete(item)
        self.db.commit()
        
        return {
            "id": item_id,
            "name": item_name
        }

