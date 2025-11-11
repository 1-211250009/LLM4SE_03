"""
行程创建智能体服务
通过对话方式收集行程信息并创建行程
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from ..models.trip import Trip
from ..schemas.trip import TripCreate
from .llm_service import LLMService


class TripAIService:
    """行程创建智能体服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def process_natural_language_query(
        self, 
        query: str, 
        user_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """处理自然语言查询，返回响应和待确认的操作"""
        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt()
            
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
                    content = '我已经收集到所有必要信息，准备为您创建行程。请确认以下信息：'
                
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

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        prompt = """你是一名AI行程创建助手，帮助用户通过对话方式创建旅行行程。

你的角色定位：
- 通过友好的对话，逐步收集创建行程所需的所有信息
- 引导用户提供必要的信息，但不要过于机械
- 根据用户的回答，智能推测和补充信息
- 在收集齐所有信息后，使用工具创建行程

创建行程需要收集的信息：
1. **行程标题** (title) - 必填，例如："北京三日游"、"上海迪士尼之旅"
2. **目的地** (destination) - 必填，例如："北京"、"上海"
3. **开始日期** (start_date) - 必填，格式：YYYY-MM-DD，例如："2025-11-15"
4. **结束日期** (end_date) - 必填，格式：YYYY-MM-DD，例如："2025-11-17"
5. **行程天数** (duration_days) - 可选，如果提供了开始和结束日期，会自动计算
6. **总预算** (budget_total) - 可选，数字，例如：5000
7. **货币单位** (currency) - 可选，默认："CNY"
8. **同行人数** (traveler_count) - 可选，默认：1
9. **行程状态** (status) - 可选，默认："draft"，可选值：draft, planned, active, completed, cancelled
10. **标签** (tags) - 可选，字符串数组，例如：["休闲", "文化"]
11. **是否公开** (is_public) - 可选，默认：false
12. **行程描述** (description) - 可选，可以根据收集到的信息自动生成

重要提示：
1. 当用户要求创建行程时，必须通过对话收集所有必填信息（标题、目的地、开始日期、结束日期）
2. 如果用户没有提供某些信息，要友好地询问
3. 可以根据上下文智能推测信息，例如：
   - 如果用户说"去北京玩3天"，可以推测目的地是"北京"，天数是3
   - 如果用户说"下周末"，可以根据当前日期推测具体日期
   - 如果用户说"预算5000元"，可以提取预算金额
4. 只有在收集齐所有必填信息后，才调用 create_trip 工具
5. 工具调用需要用户确认后才能执行
6. 在调用工具前，要向用户展示收集到的信息，让用户确认

工具使用示例：
- 用户说"我想创建一个去北京的行程，时间是11月15日到17日，预算5000元"
  -> 收集到：title="北京三日游", destination="北京", start_date="2025-11-15", end_date="2025-11-17", budget_total=5000
  -> 调用 create_trip 工具

- 用户说"帮我创建一个行程"
  -> 询问："请问您想去哪里旅行？"
  -> 用户回答后，继续询问其他信息

注意：你有可用的工具函数（tools），当收集齐所有信息后，必须调用 create_trip 工具。不要只是回复文字，要实际调用工具！
"""
        return prompt

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_trip",
                    "description": "创建新的旅行行程",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "行程标题，必填，例如：'北京三日游'、'上海迪士尼之旅'"
                            },
                            "destination": {
                                "type": "string",
                                "description": "目的地，必填，例如：'北京'、'上海'"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "开始日期，必填，格式：YYYY-MM-DD，例如：'2025-11-15'"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，必填，格式：YYYY-MM-DD，例如：'2025-11-17'"
                            },
                            "duration_days": {
                                "type": "integer",
                                "description": "行程天数，可选，如果提供了开始和结束日期会自动计算"
                            },
                            "budget_total": {
                                "type": "number",
                                "description": "总预算，可选，数字，例如：5000"
                            },
                            "currency": {
                                "type": "string",
                                "description": "货币单位，可选，默认：'CNY'"
                            },
                            "traveler_count": {
                                "type": "integer",
                                "description": "同行人数，可选，默认：1"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["draft", "planned", "active", "completed", "cancelled"],
                                "description": "行程状态，可选，默认：'draft'"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "标签，可选，字符串数组，例如：['休闲', '文化']"
                            },
                            "is_public": {
                                "type": "boolean",
                                "description": "是否公开，可选，默认：false"
                            },
                            "description": {
                                "type": "string",
                                "description": "行程描述，可选，可以根据收集到的信息自动生成"
                            }
                        },
                        "required": ["title", "destination", "start_date", "end_date"]
                    }
                }
            }
        ]
    
    async def execute_tool_call(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            if function_name == "create_trip":
                result = await self._create_trip(arguments, user_id)
                return {
                    "message": f"✅ 行程创建成功：{result.get('title', '')}",
                    "data": result
                }
            else:
                raise ValueError(f"未知功能：{function_name}")
        
        except Exception as e:
            raise Exception(f"执行失败：{str(e)}")
    
    async def _create_trip(self, arguments: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """创建行程"""
        from ..schemas.trip import TripCreate
        
        # 处理日期格式
        start_date = None
        end_date = None
        if arguments.get('start_date'):
            try:
                start_date = datetime.strptime(arguments['start_date'], '%Y-%m-%d').date()
            except:
                start_date = arguments['start_date']
        
        if arguments.get('end_date'):
            try:
                end_date = datetime.strptime(arguments['end_date'], '%Y-%m-%d').date()
            except:
                end_date = arguments['end_date']
        
        # 计算行程天数
        duration_days = arguments.get('duration_days')
        if not duration_days and start_date and end_date:
            if isinstance(start_date, date) and isinstance(end_date, date):
                duration_days = (end_date - start_date).days + 1
            else:
                duration_days = 1
        
        # 构建行程数据
        trip_data = TripCreate(
            title=arguments.get('title', ''),
            destination=arguments.get('destination', ''),
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days or 1,
            budget_total=arguments.get('budget_total'),
            currency=arguments.get('currency', 'CNY'),
            traveler_count=arguments.get('traveler_count', 1),
            status=arguments.get('status', 'draft'),
            tags=arguments.get('tags', []),
            is_public=arguments.get('is_public', False),
            description=arguments.get('description', '')
        )
        
        # 创建行程
        from ..models.trip import Trip as TripModel
        
        trip = TripModel(
            user_id=user_id,
            title=trip_data.title,
            description=trip_data.description,
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            duration_days=trip_data.duration_days,
            budget_total=trip_data.budget_total,
            currency=trip_data.currency,
            status=trip_data.status,
            is_public=trip_data.is_public,
            tags=trip_data.tags or [],
            preferences=trip_data.preferences or {},
            traveler_count=trip_data.traveler_count
        )
        
        self.db.add(trip)
        self.db.commit()
        self.db.refresh(trip)
        
        return {
            "id": trip.id,
            "title": trip.title,
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat() if trip.start_date else None,
            "end_date": trip.end_date.isoformat() if trip.end_date else None,
            "duration_days": trip.duration_days
        }

