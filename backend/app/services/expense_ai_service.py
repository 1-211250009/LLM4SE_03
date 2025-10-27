"""
费用智能体服务
提供自然语言管理费用功能
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import json
import re

from ..models.trip import Expense, Budget, Trip
from ..schemas.expense import ExpenseCreate, ExpenseUpdate
from .expense_service import ExpenseService
from .llm_service import LLMService


class ExpenseAIService:
    """费用智能体服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.expense_service = ExpenseService(db)
        self.llm_service = LLMService()

    async def process_natural_language_query(
        self, 
        query: str, 
        user_id: str, 
        trip_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理自然语言查询"""
        
        # 构建系统提示
        system_prompt = self._build_system_prompt(user_id, trip_id, context)
        
        # 调用LLM处理查询
        response = await self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            tools=self._get_available_tools()
        )
        
        # 处理工具调用
        if response.get('tool_calls'):
            result = await self._handle_tool_calls(response['tool_calls'], user_id, trip_id)
            return result
        
        return response.get('content', '抱歉，我无法理解您的请求。')

    def _build_system_prompt(self, user_id: str, trip_id: Optional[str], context: Dict[str, Any]) -> str:
        """构建系统提示"""
        prompt = f"""你是一个专业的费用管理助手，可以帮助用户管理旅行费用。

用户ID: {user_id}
行程ID: {trip_id or '未指定'}

可用功能：
1. 添加费用记录
2. 查询费用统计
3. 分析费用趋势
4. 提供预算建议
5. 费用分类管理

费用分类包括：
- transportation: 交通
- accommodation: 住宿
- food: 餐饮
- attraction: 景点
- shopping: 购物
- entertainment: 娱乐
- other: 其他

请根据用户的需求提供帮助。如果需要操作费用数据，请使用相应的工具函数。"""

        if context:
            prompt += f"\n\n当前上下文：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        return prompt

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_expense",
                    "description": "添加费用记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trip_id": {
                                "type": "string",
                                "description": "行程ID"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["transportation", "accommodation", "food", "attraction", "shopping", "entertainment", "other"],
                                "description": "费用分类"
                            },
                            "amount": {
                                "type": "number",
                                "description": "金额"
                            },
                            "description": {
                                "type": "string",
                                "description": "费用描述"
                            },
                            "location": {
                                "type": "string",
                                "description": "地点（可选）"
                            }
                        },
                        "required": ["trip_id", "category", "amount", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_expense_summary",
                    "description": "获取费用统计摘要",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trip_id": {
                                "type": "string",
                                "description": "行程ID（可选）"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_category_stats",
                    "description": "获取费用分类统计",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trip_id": {
                                "type": "string",
                                "description": "行程ID（可选）"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_expense_trends",
                    "description": "分析费用趋势",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trip_id": {
                                "type": "string",
                                "description": "行程ID（可选）"
                            },
                            "period": {
                                "type": "string",
                                "enum": ["daily", "weekly", "monthly"],
                                "description": "分析周期"
                            }
                        }
                    }
                }
            }
        ]

    async def _handle_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]], 
        user_id: str, 
        trip_id: Optional[str]
    ) -> str:
        """处理工具调用"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            arguments = json.loads(tool_call['function']['arguments'])
            
            try:
                if function_name == "add_expense":
                    result = await self._add_expense(arguments, user_id)
                    results.append(f"✅ 已添加费用记录：{result}")
                
                elif function_name == "get_expense_summary":
                    result = await self._get_expense_summary(arguments, user_id)
                    results.append(f"📊 费用统计：\n{result}")
                
                elif function_name == "get_category_stats":
                    result = await self._get_category_stats(arguments, user_id)
                    results.append(f"📈 分类统计：\n{result}")
                
                elif function_name == "analyze_expense_trends":
                    result = await self._analyze_expense_trends(arguments, user_id)
                    results.append(f"📉 费用趋势分析：\n{result}")
                
                else:
                    results.append(f"❌ 未知功能：{function_name}")
            
            except Exception as e:
                results.append(f"❌ 执行失败：{str(e)}")
        
        return "\n\n".join(results)

    async def _add_expense(self, arguments: Dict[str, Any], user_id: str) -> str:
        """添加费用记录"""
        # 如果没有指定trip_id，使用默认的
        if not arguments.get('trip_id'):
            # 获取用户最近的行程
            trip = self.db.query(Trip).filter(
                Trip.user_id == user_id
            ).order_by(Trip.created_at.desc()).first()
            
            if not trip:
                raise ValueError("请先创建一个行程")
            
            arguments['trip_id'] = trip.id
        
        expense_data = ExpenseCreate(**arguments)
        expense = await self.expense_service.create_expense(expense_data, user_id)
        
        return f"¥{expense.amount} - {expense.description} ({expense.category})"

    async def _get_expense_summary(self, arguments: Dict[str, Any], user_id: str) -> str:
        """获取费用统计摘要"""
        trip_id = arguments.get('trip_id')
        summary = await self.expense_service.get_expense_summary(
            user_id=user_id,
            trip_id=trip_id
        )
        
        return f"""
总支出：¥{summary.total_amount:.2f}
总笔数：{summary.total_count}笔
平均支出：¥{summary.average_amount:.2f}

分类明细：
{self._format_category_breakdown(summary.category_breakdown)}
        """.strip()

    async def _get_category_stats(self, arguments: Dict[str, Any], user_id: str) -> str:
        """获取费用分类统计"""
        trip_id = arguments.get('trip_id')
        stats = await self.expense_service.get_category_stats(
            user_id=user_id,
            trip_id=trip_id
        )
        
        if not stats:
            return "暂无费用数据"
        
        result = "费用分类统计：\n"
        for stat in stats:
            result += f"• {stat.category}: ¥{stat.amount:.2f} ({stat.count}笔, {stat.percentage}%)\n"
        
        return result.strip()

    async def _analyze_expense_trends(self, arguments: Dict[str, Any], user_id: str) -> str:
        """分析费用趋势"""
        trip_id = arguments.get('trip_id')
        period = arguments.get('period', 'daily')
        
        # 这里可以实现更复杂的趋势分析
        summary = await self.expense_service.get_expense_summary(
            user_id=user_id,
            trip_id=trip_id
        )
        
        if not summary.daily_breakdown:
            return "暂无费用趋势数据"
        
        # 简单的趋势分析
        daily_amounts = list(summary.daily_breakdown.values())
        if len(daily_amounts) < 2:
            return "数据不足，无法分析趋势"
        
        avg_daily = sum(daily_amounts) / len(daily_amounts)
        trend = "上升" if daily_amounts[-1] > daily_amounts[0] else "下降"
        
        return f"""
费用趋势分析（{period}）：
• 平均每日支出：¥{avg_daily:.2f}
• 总体趋势：{trend}
• 最高单日：¥{max(daily_amounts):.2f}
• 最低单日：¥{min(daily_amounts):.2f}
        """.strip()

    def _format_category_breakdown(self, breakdown: Dict[str, Dict[str, Any]]) -> str:
        """格式化分类明细"""
        if not breakdown:
            return "暂无数据"
        
        result = ""
        for category, data in breakdown.items():
            result += f"• {category}: ¥{data['amount']:.2f} ({data['count']}笔, {data['percentage']}%)\n"
        
        return result.strip()
