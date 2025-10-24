"""
行程规划Agent

专门负责旅行行程规划的智能代理
"""

import asyncio
import json
from typing import Dict, Any, List, AsyncGenerator, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..services.llm_service import llm_service_instance
from ..utils.baidu_map_tools import baidu_map_tools
from ..utils.tool_definitions import get_all_tools


class TripPlannerAgent(BaseAgent):
    """
    行程规划Agent
    
    负责根据用户需求生成详细的旅行行程规划
    """
    
    def __init__(self):
        super().__init__(
            agent_id="trip-planner",
            agent_name="行程规划助手"
        )
        
        # 工具定义
        self.available_tools = [
            {
                "name": "searchPOI",
                "description": "搜索景点、餐厅、酒店等兴趣点",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                        "location": {
                            "type": "object",
                            "properties": {
                                "lat": {"type": "number", "description": "纬度"},
                                "lng": {"type": "number", "description": "经度"}
                            },
                            "description": "搜索中心位置"
                        },
                        "radius": {"type": "number", "description": "搜索半径（米）"},
                        "category": {"type": "string", "description": "分类：attraction, restaurant, hotel, shopping"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "calculateRoute",
                "description": "计算两点间的距离、时间和路线",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "object",
                            "properties": {
                                "lat": {"type": "number"},
                                "lng": {"type": "number"}
                            },
                            "required": ["lat", "lng"]
                        },
                        "destination": {
                            "type": "object",
                            "properties": {
                                "lat": {"type": "number"},
                                "lng": {"type": "number"}
                            },
                            "required": ["lat", "lng"]
                        },
                        "mode": {"type": "string", "enum": ["driving", "walking", "transit", "bicycling"]}
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "queryPrice",
                "description": "查询酒店、机票、门票等价格信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["hotel", "flight", "ticket", "restaurant"]},
                        "location": {"type": "string", "description": "地点"},
                        "checkIn": {"type": "string", "description": "入住日期"},
                        "checkOut": {"type": "string", "description": "退房日期"},
                        "adults": {"type": "number", "description": "成人数量"},
                        "children": {"type": "number", "description": "儿童数量"}
                    },
                    "required": ["type", "location"]
                }
            },
            {
                "name": "getWeather",
                "description": "查询指定地点的天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "地点名称"},
                        "date": {"type": "string", "description": "查询日期"}
                    },
                    "required": ["location"]
                }
            }
        ]
    
    async def run(
        self, 
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        run_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        运行行程规划Agent
        """
        if not run_id:
            run_id = f"trip_plan_{int(datetime.now().timestamp())}"
        
        try:
            # 1. 发送RUN_STARTED事件
            yield self._create_run_started_event(run_id)
            
            # 2. 发送系统消息
            yield self._create_system_message_event("开始分析您的旅行需求...")
            
            # 3. 生成系统提示词
            system_prompt = self._generate_system_prompt(system_prompt)
            
            # 4. 格式化消息
            messages = self._format_messages_for_llm(user_input, system_prompt, history)
            
            # 5. 流式调用LLM
            message_id = f"msg_{int(datetime.now().timestamp())}"
            full_response = ""
            
            # 获取工具定义
            tools = get_all_tools()
            
            async for chunk in llm_service_instance.stream_llm_response_with_tools(
                user_input, system_prompt, history, tools
            ):
                try:
                    chunk_data = json.loads(chunk)
                    print(f"DEBUG: Received chunk: {chunk[:200]}...")
                    
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        choice = chunk_data["choices"][0]
                        
                        # 处理文本内容
                        if "delta" in choice and "content" in choice["delta"]:
                            content = choice["delta"]["content"]
                            full_response += content
                            
                            # 发送文本流事件
                            yield self._create_text_message_delta_event(content, message_id)
                        
                        # 处理工具调用
                        if "delta" in choice and "tool_calls" in choice["delta"]:
                            tool_calls = choice["delta"]["tool_calls"]
                            for tool_call in tool_calls:
                                if tool_call.get("type") == "function":
                                    function = tool_call.get("function", {})
                                    function_name = function.get("name")
                                    function_args = function.get("arguments", "{}")
                                    
                                    # 检查必要参数
                                    if not function_name or function_name is None:
                                        print(f"Warning: function_name is None or empty, tool_call: {tool_call}")
                                        continue
                                    
                                    if not function_args or function_args is None:
                                        function_args = "{}"
                                    
                                    try:
                                        print(f"DEBUG: Processing tool call - function_name: {function_name}, function_args: {function_args}")
                                        
                                        # 发送工具调用请求事件
                                        yield self._create_tool_call_request_event(
                                            function_name, 
                                            json.loads(function_args), 
                                            tool_call.get("id", f"call_{int(datetime.now().timestamp())}")
                                        )
                                        
                                        # 执行工具调用
                                        result = await self._execute_tool_call(function_name, json.loads(function_args))
                                        
                                        # 发送工具调用结果事件
                                        yield self._create_tool_call_result_event(
                                            tool_call.get("id", f"call_{int(datetime.now().timestamp())}"),
                                            result
                                        )
                                    except Exception as e:
                                        print(f"Error processing tool call: {e}")
                                        # 发送错误结果
                                        yield self._create_tool_call_result_event(
                                            tool_call.get("id", f"call_{int(datetime.now().timestamp())}"),
                                            {"success": False, "error": str(e)}
                                        )
                        
                        # 检查是否完成
                        if choice.get("finish_reason") == "stop":
                            break
                            
                except json.JSONDecodeError:
                    continue
            
            # 6. 发送文本消息完成事件（流式已经完成，不需要再发送完整内容）
            # yield self._create_text_message_content_event(full_response, message_id)
            
            # 7. 分析是否需要调用工具
            if self._should_call_tools(user_input, full_response):
                yield self._create_system_message_event("正在搜索相关信息...")
                
                # 调用相关工具
                tool_results = await self._call_relevant_tools(user_input, full_response)
                
                # 发送工具调用请求和结果
                for tool_result in tool_results:
                    # 发送工具调用请求事件
                    yield self._create_tool_call_request_event(
                        tool_result["tool_name"],
                        tool_result.get("parameters", {}),
                        tool_result["call_id"]
                    )
                    
                    # 发送工具调用结果事件
                    yield self._create_tool_call_result_event(
                        tool_result["call_id"], 
                        tool_result["result"]
                    )
                
                # 基于工具结果生成补充信息
                if tool_results:
                    yield self._create_system_message_event("基于搜索结果，为您提供更详细的建议...")
                    
                    # 生成补充回复
                    supplement_prompt = self._generate_supplement_prompt(full_response, tool_results)
                    supplement_messages = [
                        {"role": "system", "content": supplement_prompt},
                        {"role": "user", "content": user_input}
                    ]
                    
                    supplement_message_id = f"supplement_{int(datetime.now().timestamp())}"
                    supplement_response = ""
                    
                    async for chunk in llm_service_instance.stream_llm_response(
                        user_input, supplement_prompt, []
                    ):
                        try:
                            chunk_data = json.loads(chunk)
                            
                            if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                choice = chunk_data["choices"][0]
                                
                                if "delta" in choice and "content" in choice["delta"]:
                                    content = choice["delta"]["content"]
                                    supplement_response += content
                                    
                                    yield self._create_text_message_delta_event(content, supplement_message_id)
                                
                                if choice.get("finish_reason") == "stop":
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
                    
                    yield self._create_text_message_content_event(supplement_response, supplement_message_id)
            
            # 8. 发送RUN_FINISHED事件
            result = {
                "messageId": message_id,
                "content": full_response,
                "runId": run_id,
                "agentId": self.agent_id
            }
            yield self._create_run_finished_event(run_id, result)
            
        except Exception as e:
            # 发送错误事件
            yield self._create_run_error_event(run_id, str(e))
    
    def _generate_system_prompt(self, custom_prompt: str = None) -> str:
        """生成系统提示词"""
        if custom_prompt:
            return custom_prompt
        
        return """你是一个专业的旅行规划助手。请用中文回答用户的问题，帮助用户规划旅行行程。

你可以提供以下帮助：
1. 推荐旅游目的地和景点
2. 制定详细的行程安排
3. 提供交通和住宿建议
4. 估算旅行费用
5. 回答旅行相关问题

当需要搜索具体信息时，你可以使用以下工具：
- searchPOI: 搜索景点、餐厅、酒店等
- calculateRoute: 计算路线距离和时间
- queryPrice: 查询价格信息
- getWeather: 查询天气信息

请保持回答简洁明了，并提供实用的建议。如果用户询问具体的地点、价格或路线信息，请主动使用相关工具进行搜索。"""
    
    def _should_call_tools(self, user_input: str, response: str) -> bool:
        """判断是否需要调用工具"""
        # 检查用户输入和AI回复中的关键词
        tool_keywords = [
            "搜索", "查找", "推荐", "附近", "价格", "费用", "路线", "距离", 
            "天气", "酒店", "餐厅", "景点", "门票", "交通", "北京", "上海", "广州"
        ]
        
        # 检查用户输入和AI回复
        user_has_keywords = any(keyword in user_input for keyword in tool_keywords)
        response_has_keywords = any(keyword in response for keyword in tool_keywords)
        
        # 添加调试信息
        print(f"DEBUG: user_input='{user_input}', user_has_keywords={user_has_keywords}")
        print(f"DEBUG: response='{response[:100]}...', response_has_keywords={response_has_keywords}")
        print(f"DEBUG: should_call_tools={user_has_keywords or response_has_keywords}")
        
        return user_has_keywords or response_has_keywords
    
    async def _call_relevant_tools(self, user_input: str, response: str) -> List[Dict[str, Any]]:
        """调用相关工具"""
        tool_results = []
        
        print(f"DEBUG: _call_relevant_tools called with user_input='{user_input}'")
        
        # 根据用户输入和回复内容决定调用哪些工具
        poi_keywords = ["景点", "餐厅", "酒店", "推荐", "附近"]
        has_poi_keywords = any(keyword in user_input.lower() for keyword in poi_keywords)
        print(f"DEBUG: checking POI keywords {poi_keywords}, has_poi_keywords={has_poi_keywords}")
        
        if has_poi_keywords:
            # 调用POI搜索
            call_id = f"poi_call_{int(datetime.now().timestamp())}"
            location = self._extract_location_from_input(user_input)
            
            # 使用百度地图API搜索POI
            search_keyword = self._extract_search_keyword(user_input)
            print(f"DEBUG: searching POI with keyword='{search_keyword}', city='{location}'")
            
            try:
                poi_result = baidu_map_tools.search_poi(
                    keyword=search_keyword,
                    city=location,
                    category="attraction"
                )
                print(f"DEBUG: POI search result: {poi_result}")
            except Exception as e:
                print(f"DEBUG: POI search error: {e}")
                poi_result = {
                    "success": False,
                    "error": str(e),
                    "data": None
                }
            
            # 无论API调用成功与否，都添加工具结果
            print(f"DEBUG: Adding tool result to tool_results")
            
            tool_results.append({
                "call_id": call_id,
                "tool_name": "searchPOI",
                "parameters": {
                    "query": search_keyword,
                    "city": location,
                    "category": "attraction"
                },
                "result": poi_result
            })
        
        if any(keyword in user_input.lower() for keyword in ["路线", "距离", "时间", "怎么去"]):
            # 调用路线计算
            call_id = f"route_call_{int(datetime.now().timestamp())}"
            
            # 提取起点和终点
            origin, destination = self._extract_route_points(user_input)
            if origin and destination:
                route_result = baidu_map_tools.calculate_route(
                    origin=origin,
                    destination=destination,
                    mode="driving"
                )
                
                tool_results.append({
                    "call_id": call_id,
                    "tool_name": "calculateRoute",
                    "parameters": {
                        "origin": origin,
                        "destination": destination,
                        "mode": "driving"
                    },
                    "result": route_result
                })
        
        print(f"DEBUG: _call_relevant_tools returning {len(tool_results)} tool results")
        return tool_results
    
    def _extract_location_from_input(self, user_input: str) -> str:
        """从用户输入中提取地点信息"""
        # 简单的地点提取逻辑
        common_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "西安", "武汉", "重庆"]
        
        for city in common_cities:
            if city in user_input:
                return city
        
        # 如果没有找到常见城市，返回默认值
        return "北京"
    
    def _extract_search_keyword(self, user_input: str) -> str:
        """从用户输入中提取搜索关键词"""
        # 移除常见城市名称，提取搜索关键词
        common_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "西安", "武汉", "重庆"]
        
        keyword = user_input
        for city in common_cities:
            keyword = keyword.replace(city, "")
        
        # 清理多余的空格
        keyword = keyword.strip()
        
        # 如果关键词太模糊，使用更具体的搜索词
        if not keyword or keyword in ["推荐", "景点", "推荐景点", "推荐的景点", "推荐一些", "推荐几个"]:
            return "北京景点"
        
        # 如果关键词包含"景点"相关词汇，使用更具体的搜索词
        if any(word in keyword for word in ["景点", "旅游", "游玩", "观光"]):
            return "北京景点"
        
        return keyword
    
    async def _execute_tool_call(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            if function_name == "search_poi":
                keyword = arguments.get("keyword", "景点")
                city = arguments.get("city", "北京")
                category = arguments.get("category", "attraction")
                
                result = baidu_map_tools.search_poi(
                    keyword=keyword,
                    city=city,
                    category=category
                )
                return result.model_dump() if hasattr(result, 'model_dump') else result
                
            elif function_name == "calculate_route":
                origin = arguments.get("origin")
                destination = arguments.get("destination")
                mode = arguments.get("mode", "driving")
                
                result = baidu_map_tools.calculate_route(
                    origin=origin,
                    destination=destination,
                    mode=mode
                )
                return result.model_dump() if hasattr(result, 'model_dump') else result
                
            else:
                return {"success": False, "error": f"未知的工具: {function_name}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_route_points(self, user_input: str) -> tuple:
        """从用户输入中提取路线起点和终点"""
        # 简单的路线提取逻辑
        # 这里可以根据实际需求实现更复杂的NLP解析
        
        # 默认返回空值，需要用户提供具体信息
        return None, None
    
    def _generate_supplement_prompt(self, original_response: str, tool_results: List[Dict[str, Any]]) -> str:
        """生成补充提示词"""
        return f"""基于以下搜索结果，为用户提供更详细和准确的旅行建议：

原始回复：{original_response}

搜索结果：
{json.dumps(tool_results, ensure_ascii=False, indent=2)}

请结合搜索结果，为用户提供更具体的建议，包括：
1. 具体的景点推荐和详细信息
2. 准确的价格信息
3. 实用的路线建议
4. 天气相关的出行建议

保持回答的实用性和准确性。"""
