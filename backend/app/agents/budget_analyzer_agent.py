"""
费用分析Agent

专门负责旅行费用分析和预算管理的智能代理
"""

import asyncio
import json
from typing import Dict, Any, List, AsyncGenerator, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..services.llm_service import llm_service_instance


class BudgetAnalyzerAgent(BaseAgent):
    """
    费用分析Agent
    
    负责分析旅行费用、制定预算建议、费用优化等
    """
    
    def __init__(self):
        super().__init__(
            agent_id="budget-analyzer",
            agent_name="费用分析助手"
        )
    
    async def run(
        self, 
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        run_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        运行费用分析Agent
        """
        if not run_id:
            run_id = f"budget_analysis_{int(datetime.now().timestamp())}"
        
        try:
            # 1. 发送RUN_STARTED事件
            yield self._create_run_started_event(run_id)
            
            # 2. 发送系统消息
            yield self._create_system_message_event("开始分析您的旅行预算...")
            
            # 3. 生成系统提示词
            system_prompt = self._generate_system_prompt(system_prompt)
            
            # 4. 格式化消息
            messages = self._format_messages_for_llm(user_input, system_prompt, history)
            
            # 5. 流式调用LLM
            message_id = f"budget_msg_{int(datetime.now().timestamp())}"
            full_response = ""
            
            async for chunk in llm_service_instance.stream_llm_response(
                user_input, system_prompt, history
            ):
                try:
                    chunk_data = json.loads(chunk)
                    
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        choice = chunk_data["choices"][0]
                        
                        if "delta" in choice and "content" in choice["delta"]:
                            content = choice["delta"]["content"]
                            full_response += content
                            
                            # 发送文本流事件
                            yield self._create_text_message_delta_event(content, message_id)
                        
                        # 检查是否完成
                        if choice.get("finish_reason") == "stop":
                            break
                            
                except json.JSONDecodeError:
                    continue
            
            # 6. 发送文本消息完成事件
            yield self._create_text_message_content_event(full_response, message_id)
            
            # 7. 如果需要查询价格信息
            if self._should_query_prices(user_input):
                yield self._create_system_message_event("正在查询相关价格信息...")
                
                # 调用价格查询工具
                price_results = await self._call_price_tools(user_input)
                
                # 发送工具调用结果
                for price_result in price_results:
                    yield self._create_tool_call_result_event(
                        price_result["call_id"], 
                        price_result["result"]
                    )
                
                # 基于价格结果生成详细分析
                if price_results:
                    yield self._create_system_message_event("基于价格信息，为您提供详细的预算分析...")
                    
                    # 生成预算分析
                    budget_analysis = await self._generate_budget_analysis(user_input, price_results)
                    analysis_message_id = f"analysis_{int(datetime.now().timestamp())}"
                    
                    for char in budget_analysis:
                        yield self._create_text_message_delta_event(char, analysis_message_id)
                        await asyncio.sleep(0.01)  # 模拟流式输出
                    
                    yield self._create_text_message_content_event(budget_analysis, analysis_message_id)
            
            # 8. 发送RUN_FINISHED事件
            result = {
                "messageId": message_id,
                "content": full_response,
                "runId": run_id,
                "agentId": self.agent_id,
                "budgetAnalysis": True
            }
            yield self._create_run_finished_event(run_id, result)
            
        except Exception as e:
            # 发送错误事件
            yield self._create_run_error_event(run_id, str(e))
    
    def _generate_system_prompt(self, custom_prompt: str = None) -> str:
        """生成系统提示词"""
        if custom_prompt:
            return custom_prompt
        
        return """你是一个专业的旅行费用分析助手。请用中文回答用户的问题，帮助用户分析旅行费用和制定预算。

你可以提供以下帮助：
1. 分析旅行各项费用（交通、住宿、餐饮、门票等）
2. 制定合理的预算建议
3. 提供费用优化建议
4. 比较不同选项的费用差异
5. 分析费用趋势和变化

当需要查询具体价格信息时，你可以使用以下工具：
- queryPrice: 查询酒店、机票、门票等价格信息

请保持回答专业准确，并提供具体的数字和建议。"""
    
    def _should_query_prices(self, user_input: str) -> bool:
        """判断是否需要查询价格"""
        price_keywords = [
            "价格", "费用", "预算", "花费", "成本", "多少钱", "贵不贵",
            "酒店", "机票", "门票", "交通费", "餐饮费"
        ]
        
        return any(keyword in user_input for keyword in price_keywords)
    
    async def _call_price_tools(self, user_input: str) -> List[Dict[str, Any]]:
        """调用价格查询工具"""
        tool_results = []
        
        # 根据用户输入决定查询哪些价格
        if any(keyword in user_input for keyword in ["酒店", "住宿"]):
            call_id = f"hotel_price_{int(datetime.now().timestamp())}"
            tool_result = await self._call_frontend_tool("queryPrice", {
                "type": "hotel",
                "location": self._extract_location_from_input(user_input)
            })
            tool_results.append({
                "call_id": call_id,
                "tool_name": "queryPrice",
                "result": tool_result
            })
        
        if any(keyword in user_input for keyword in ["机票", "航班", "交通"]):
            call_id = f"flight_price_{int(datetime.now().timestamp())}"
            tool_result = await self._call_frontend_tool("queryPrice", {
                "type": "flight",
                "location": self._extract_location_from_input(user_input)
            })
            tool_results.append({
                "call_id": call_id,
                "tool_name": "queryPrice",
                "result": tool_result
            })
        
        if any(keyword in user_input for keyword in ["门票", "景点", "游玩"]):
            call_id = f"ticket_price_{int(datetime.now().timestamp())}"
            tool_result = await self._call_frontend_tool("queryPrice", {
                "type": "ticket",
                "location": self._extract_location_from_input(user_input)
            })
            tool_results.append({
                "call_id": call_id,
                "tool_name": "queryPrice",
                "result": tool_result
            })
        
        return tool_results
    
    def _extract_location_from_input(self, user_input: str) -> str:
        """从用户输入中提取地点信息"""
        common_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "西安", "武汉", "重庆"]
        
        for city in common_cities:
            if city in user_input:
                return city
        
        return "北京"
    
    async def _generate_budget_analysis(self, user_input: str, price_results: List[Dict[str, Any]]) -> str:
        """生成预算分析"""
        analysis_prompt = f"""基于以下价格信息，为用户提供详细的预算分析：

用户问题：{user_input}

价格信息：
{json.dumps(price_results, ensure_ascii=False, indent=2)}

请提供：
1. 各项费用的详细分析
2. 总预算估算
3. 费用优化建议
4. 不同档次的预算方案
5. 省钱小贴士

保持专业性和实用性。"""
        
        # 调用LLM生成分析
        analysis_response = ""
        async for chunk in llm_service_instance.stream_llm_response(
            user_input, analysis_prompt, []
        ):
            try:
                chunk_data = json.loads(chunk)
                
                if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                    choice = chunk_data["choices"][0]
                    
                    if "delta" in choice and "content" in choice["delta"]:
                        content = choice["delta"]["content"]
                        analysis_response += content
                    
                    if choice.get("finish_reason") == "stop":
                        break
                        
            except json.JSONDecodeError:
                continue
        
        return analysis_response
