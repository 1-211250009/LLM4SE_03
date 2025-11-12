"""
费用智能体服务
提供自然语言管理费用功能
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import json
import re

from ..models.trip import Expense, Trip
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
    ) -> Dict[str, Any]:
        """处理自然语言查询，返回响应和待确认的操作"""
        try:
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
                        # 根据不同的工具调用，生成友好的提示信息
                        function_name = tool_call['function']['name']
                        action_names = {
                            'add_expense': '我准备为您添加费用记录',
                            'update_expense': '我准备为您更新费用记录',
                            'delete_expense': '我准备为您删除费用记录',
                            'get_filtered_expenses': '我准备为您查询费用记录',
                            'get_expense_summary': '我准备为您获取费用统计',
                            'get_category_stats': '我准备为您获取分类统计',
                            'analyze_expense_trends': '我准备为您分析费用趋势'
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

    def _build_system_prompt(self, user_id: str, trip_id: Optional[str], context: Optional[Dict[str, Any]]) -> str:
        """构建系统提示"""
        prompt = """你是一名AI费用助手，辅助用户进行旅行行程的费用分析和管理。

你的角色定位：
- 帮助用户分析和管理旅行费用
- 提供费用统计和预算建议
- 协助用户添加、修改、删除费用记录
- 根据用户需求筛选和查询费用数据

费用分类包括：
- transportation: 交通
- accommodation: 住宿
- food: 餐饮
- attraction: 景点
- shopping: 购物
- entertainment: 娱乐
- other: 其他

重要提示：
1. 当用户要求执行操作（如添加、修改、删除费用）时，必须立即使用相应的工具函数（add_expense、update_expense、delete_expense等）
2. 工具函数调用会在前端显示确认卡片，由用户在前端确认后执行，所以你不需要询问用户确认，直接调用工具即可
3. 如果用户提供了足够的信息（金额、分类、描述），直接调用工具函数。如果缺少trip_id，使用上下文中的trip_id
4. 如果信息不足，可以询问用户补充信息，但一旦信息足够，立即调用工具
5. 在回答用户问题时，要结合当前的行程信息和费用数据
6. 提供清晰、准确的费用分析和建议

工具使用示例：
- 用户说"添加一笔100元的交通费用，描述是地铁票" -> 立即调用add_expense工具，参数：{"trip_id": "上下文中的trip_id", "amount": 100, "category": "transportation", "description": "地铁票"}
- 用户说"删除费用ID为xxx的记录" -> 立即调用delete_expense工具，参数：{"expense_id": "xxx"}
- 用户说"查询交通费用" -> 立即调用get_filtered_expenses工具，参数：{"trip_id": "上下文中的trip_id", "category": "transportation"}

注意：你有可用的工具函数（tools），当用户要求执行操作时，必须调用相应的工具函数。不要只是回复文字，要实际调用工具！
"""

        if context:
            # 构建详细的上下文信息
            context_parts = []
            
            # 行程信息（包含trip_id）
            if trip_id:
                context_parts.append(f"当前行程ID：{trip_id}")
            if context.get('trip_title'):
                context_parts.append(f"行程名称：{context['trip_title']}")
            
            # 费用统计
            if context.get('statistics'):
                stats = context['statistics']
                context_parts.append(f"""
费用统计：
- 总支出：¥{stats.get('totalSpent', 0):.2f}
- 费用笔数：{stats.get('expenseCount', 0)}笔
- 平均支出：¥{stats.get('averageExpense', 0):.2f}
""")
                
                # 分类统计
                if stats.get('categoryStats'):
                    context_parts.append("费用分类统计：")
                    for cat_stat in stats['categoryStats']:
                        context_parts.append(f"  - {cat_stat.get('category', '')}: ¥{cat_stat.get('amount', 0):.2f} ({cat_stat.get('count', 0)}笔, {cat_stat.get('percentage', 0)}%)")
            
            # 费用列表（简化显示）
            if context.get('expenses'):
                expenses = context['expenses']
                context_parts.append(f"\n费用列表（共{len(expenses)}条）：")
                for i, exp in enumerate(expenses[:10], 1):  # 只显示前10条
                    context_parts.append(f"  {i}. {exp.get('description', '')} - ¥{exp.get('amount', 0):.2f} ({exp.get('category', '')}) - {exp.get('expense_date', '')}")
                if len(expenses) > 10:
                    context_parts.append(f"  ... 还有{len(expenses) - 10}条费用记录")
            
            # 预算信息
            if context.get('budgets'):
                budgets = context['budgets']
                if budgets and len(budgets) > 0:
                    budget = budgets[0]
                    context_parts.append(f"""
预算信息：
- 总预算：¥{budget.get('total_budget', 0):.2f}
- 已支出：¥{budget.get('spent_amount', 0):.2f}
- 剩余预算：¥{budget.get('remaining_budget', 0):.2f}
- 预算使用率：{budget.get('budget_usage_percent', 0):.1f}%
""")
            
            if context_parts:
                prompt += "\n\n当前行程和费用信息：\n" + "\n".join(context_parts)
        
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
                                "description": "金额（必须大于0）"
                            },
                            "description": {
                                "type": "string",
                                "description": "费用描述"
                            },
                            "expense_date": {
                                "type": "string",
                                "description": "费用日期，格式：YYYY-MM-DD（可选，默认为今天）"
                            },
                            "location": {
                                "type": "string",
                                "description": "地点（可选）"
                            },
                            "itinerary_item_id": {
                                "type": "string",
                                "description": "关联的行程节点ID（可选）"
                            }
                        },
                        "required": ["trip_id", "category", "amount", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_expense",
                    "description": "修改费用记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expense_id": {
                                "type": "string",
                                "description": "费用记录ID"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["transportation", "accommodation", "food", "attraction", "shopping", "entertainment", "other"],
                                "description": "费用分类（可选）"
                            },
                            "amount": {
                                "type": "number",
                                "description": "金额（可选，必须大于0）"
                            },
                            "description": {
                                "type": "string",
                                "description": "费用描述（可选）"
                            },
                            "expense_date": {
                                "type": "string",
                                "description": "费用日期，格式：YYYY-MM-DD（可选）"
                            },
                            "location": {
                                "type": "string",
                                "description": "地点（可选）"
                            }
                        },
                        "required": ["expense_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_expense",
                    "description": "删除费用记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expense_id": {
                                "type": "string",
                                "description": "费用记录ID"
                            }
                        },
                        "required": ["expense_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_filtered_expenses",
                    "description": "获取筛选的费用列表（支持按分类和时间区间筛选）",
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
                                "description": "费用分类（可选，用于筛选）"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "开始日期，格式：YYYY-MM-DD（可选）"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，格式：YYYY-MM-DD（可选）"
                            }
                        },
                        "required": ["trip_id"]
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
    
    async def execute_tool_call(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        user_id: str,
        trip_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            if function_name == "add_expense":
                result = await self._add_expense(arguments, user_id, trip_id)
                return {
                    "message": f"✅ 已添加费用记录：¥{result.get('amount', 0):.2f} - {result.get('description', '')}",
                    "data": result
                }
            
            elif function_name == "update_expense":
                result = await self._update_expense(arguments, user_id)
                return {
                    "message": f"✅ 已更新费用记录：¥{result.get('amount', 0):.2f} - {result.get('description', '')}",
                    "data": result
                }
            
            elif function_name == "delete_expense":
                result = await self._delete_expense(arguments, user_id)
                return {
                    "message": "✅ 已删除费用记录",
                    "data": result
                }
            
            elif function_name == "get_filtered_expenses":
                result = await self._get_filtered_expenses(arguments, user_id, trip_id)
                return {
                    "message": f"📋 已获取费用列表（共{len(result)}条）",
                    "data": result
                }
            
            elif function_name == "get_expense_summary":
                result = await self._get_expense_summary(arguments, user_id)
                return {
                    "message": "📊 费用统计",
                    "data": result
                }
            
            elif function_name == "get_category_stats":
                result = await self._get_category_stats(arguments, user_id)
                return {
                    "message": "📈 分类统计",
                    "data": result
                }
            
            elif function_name == "analyze_expense_trends":
                result = await self._analyze_expense_trends(arguments, user_id)
                return {
                    "message": "📉 费用趋势分析",
                    "data": result
                }
            
            else:
                raise ValueError(f"未知功能：{function_name}")
        
        except Exception as e:
            raise Exception(f"执行失败：{str(e)}")
    
    async def _add_expense(self, arguments: Dict[str, Any], user_id: str, trip_id: Optional[str] = None) -> Dict[str, Any]:
        """添加费用记录"""
        # 如果没有指定trip_id，使用传入的trip_id或获取最近的行程
        if not arguments.get('trip_id'):
            if trip_id:
                arguments['trip_id'] = trip_id
            else:
                # 获取用户最近的行程
                trip = self.db.query(Trip).filter(
                    Trip.user_id == user_id
                ).order_by(Trip.created_at.desc()).first()
                
                if not trip:
                    raise ValueError("请先创建一个行程")
                
                arguments['trip_id'] = trip.id
        
        # 如果没有指定expense_date，使用今天的日期
        if not arguments.get('expense_date'):
            from datetime import datetime
            arguments['expense_date'] = datetime.now().strftime('%Y-%m-%d')
        
        expense_data = ExpenseCreate(**arguments)
        expense = await self.expense_service.create_expense(expense_data, user_id)
        
        return {
            "id": expense.id,
            "amount": expense.amount,
            "description": expense.description,
            "category": expense.category
        }
    
    async def _update_expense(self, arguments: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """修改费用记录"""
        expense_id = arguments.pop('expense_id')
        expense_update = ExpenseUpdate(**arguments)
        expense = await self.expense_service.update_expense(expense_id, expense_update, user_id)
        
        return {
            "id": expense.id,
            "amount": expense.amount,
            "description": expense.description,
            "category": expense.category
        }
    
    async def _delete_expense(self, arguments: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """删除费用记录"""
        expense_id = arguments['expense_id']
        await self.expense_service.delete_expense(expense_id, user_id)
        
        return {"id": expense_id}
    
    async def _get_filtered_expenses(self, arguments: Dict[str, Any], user_id: str, trip_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取筛选的费用列表"""
        if not arguments.get('trip_id') and trip_id:
            arguments['trip_id'] = trip_id
        
        from datetime import datetime
        start_date = None
        end_date = None
        if arguments.get('start_date'):
            start_date = datetime.strptime(arguments['start_date'], '%Y-%m-%d').date()
        if arguments.get('end_date'):
            end_date = datetime.strptime(arguments['end_date'], '%Y-%m-%d').date()
        
        expenses = await self.expense_service.get_expenses(
            user_id=user_id,
            trip_id=arguments.get('trip_id'),
            category=arguments.get('category'),
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=100
        )
        
        return [{
            "id": exp.id,
            "amount": exp.amount,
            "description": exp.description,
            "category": exp.category,
            "expense_date": exp.expense_date.isoformat() if exp.expense_date else None,
            "location": exp.location
        } for exp in expenses]
