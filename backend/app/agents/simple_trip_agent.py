"""简化的行程规划Agent - 专注于LLM Function Calling

这个Agent实现了纯粹的LLM Function Calling模式，让大语言模型自己决定何时调用工具。
"""

import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, AsyncGenerator
from app.agents.base_agent import BaseAgent
from app.services.llm_service import llm_service_instance
from app.utils.tool_definitions import get_all_tools
from app.utils.baidu_map_tools import baidu_map_tools


class SimpleTripAgent(BaseAgent):
    """简化的行程规划Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="simple-trip-planner",
            agent_name="简化行程规划师"
        )
    
    async def run(
        self, 
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        run_id: str = None,
        context: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """
        运行简化的行程规划Agent - 使用LLM Function Calling
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            run_id: 运行ID
            
        Yields:
            AG-UI事件流
        """
        if not run_id:
            run_id = f"simple_trip_{int(datetime.now().timestamp())}"
        
        try:
            # 1. 发送RUN_STARTED事件
            yield self._create_run_started_event(run_id)
            
            # 2. 发送系统消息
            yield self._create_system_message_event("开始分析您的旅行需求...")
            
            # 3. 生成系统提示词
            system_prompt = self._generate_system_prompt(system_prompt, context)
            
            # 4. 获取工具定义
            tools = get_all_tools()
            
            # 5. 先获取完整的LLM回复（不流式发送）
            message_id = f"msg_{int(datetime.now().timestamp())}"
            full_response = ""
            
            print(f"DEBUG: Starting LLM call without tools")
            print(f"DEBUG: User input: {user_input}")
            print(f"DEBUG: System prompt: {system_prompt}")
            
            try:
                # 先收集完整的回复，不流式发送
                async for chunk in llm_service_instance.stream_llm_response(
                    user_input, system_prompt, history
                ):
                    try:
                        chunk_data = json.loads(chunk)
                        print(f"DEBUG: Received chunk: {chunk[:200]}...")
                        
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            choice = chunk_data["choices"][0]
                            
                            # 处理文本内容
                            if "delta" in choice and "content" in choice["delta"] and choice["delta"]["content"]:
                                content = choice["delta"]["content"]
                                full_response += content
                            
                            # 检查是否完成
                            if choice.get("finish_reason") == "stop":
                                break
                                
                    except json.JSONDecodeError:
                        continue
                
                # 6. 解析回复中的工具调用指令
                print(f"DEBUG: Full response: {full_response}")
                tool_calls = self._parse_tool_calls(full_response)
                print(f"DEBUG: Parsed tool calls: {tool_calls}")
                
                # 执行工具调用并收集结果
                tool_results = []
                if tool_calls:
                    for i, tool_call in enumerate(tool_calls):
                        call_id = f"call_{int(datetime.now().timestamp())}_{i}"
                        try:
                            print(f"DEBUG: Executing tool call: {tool_call}")
                            
                            # 发送工具调用请求事件
                            yield self._create_tool_call_request_event(
                                tool_call["name"], 
                                tool_call["args"], 
                                call_id
                            )
                            
                            # 执行工具调用
                            result = await self._execute_tool_call(tool_call["name"], tool_call["args"], context)
                            
                            # 发送工具调用结果事件
                            yield self._create_tool_call_result_event(call_id, result)
                            
                            # 收集结果用于生成详细回复
                            tool_results.append({
                                "name": tool_call["name"],
                                "args": tool_call["args"],
                                "result": result
                            })
                            
                        except Exception as e:
                            print(f"Error executing tool call: {e}")
                            # 发送错误结果
                            error_result = {"success": False, "error": str(e)}
                            yield self._create_tool_call_result_event(call_id, error_result)
                            
                            # 收集错误结果
                            tool_results.append({
                                "name": tool_call["name"],
                                "args": tool_call["args"],
                                "result": error_result
                            })
                
                # 7. 根据是否有工具调用决定如何发送回复
                if tool_calls and tool_results:
                    # 有工具调用：基于工具调用结果生成详细回复
                    detailed_response = await self._generate_detailed_response_from_actual_tools(tool_results, user_input)
                    if detailed_response.strip():
                        print(f"DEBUG: Sending detailed response based on tool results: {detailed_response}")
                        yield self._create_text_message_content_event(detailed_response, message_id)
                    else:
                        # 如果没有生成详细回复，发送清理后的回复
                        clean_response = self._clean_tool_calls_from_response(full_response)
                        if clean_response.strip():
                            print(f"DEBUG: Sending clean response after tool calls: {clean_response}")
                            yield self._create_text_message_content_event(clean_response, message_id)
                else:
                    # 没有工具调用：直接发送完整回复
                    if full_response.strip():
                        print(f"DEBUG: No tool calls, sending full response: {full_response}")
                        yield self._create_text_message_content_event(full_response, message_id)
                        
            except Exception as e:
                print(f"DEBUG: Error in LLM call: {e}")
                # 发送错误事件
                yield self._create_run_error_event(run_id, str(e))
                return
            
            # 6. 发送RUN_FINISHED事件
            yield self._create_run_finished_event(run_id, {
                "messageId": message_id, 
                "content": full_response, 
                "runId": run_id, 
                "agentId": self.agent_id
            })
            
        except Exception as e:
            print(f"Error in SimpleTripAgent: {e}")
            # 发送RUN_ERROR事件
            yield self._create_run_error_event(run_id, str(e))
    
    def _generate_system_prompt(self, custom_prompt: str = None, context: Dict[str, Any] = None) -> str:
        """生成系统提示词"""
        if custom_prompt:
            return custom_prompt
        
        base_prompt = """你是一个专业的旅行规划助手。你可以帮助用户：

1. 搜索景点、餐厅、酒店等POI信息
2. 在地图上标记指定地点
3. 计算路线和距离
4. 基于选中的地点规划完整行程
5. 提供旅行建议和规划

当用户要求"标记"、"在地图上标记"某个地点时，请使用：
[TOOL_CALL:mark_location:{"location":"地点名称","label":"标记标签","category":"attraction"}]

当用户询问关于地点、景点、餐厅、酒店等信息时，请使用：
[TOOL_CALL:search_poi:{"keyword":"具体景点名称","city":"城市名称","category":"attraction"}]

当用户询问路线、距离、交通方式时，请使用：
[TOOL_CALL:calculate_route:{"origin":"起点","destination":"终点","mode":"driving"}]

当用户要求"规划行程"、"生成行程"、"为这些地点规划行程"时，请使用：
[TOOL_CALL:plan_trip:{"selected_locations":["地点ID1","地点ID2"],"trip_duration":"1天","transport_mode":"mixed"}]

请根据用户的问题，智能地决定是否需要调用工具，并在回复中包含相应的工具调用指令。"""
        
        # 添加上下文信息
        if context:
            context_info = "\n\n当前对话上下文：\n"
            
            if context.get("previous_pois"):
                context_info += f"之前搜索过的POI: {', '.join([poi['name'] for poi in context['previous_pois']])}\n"
            
            if context.get("previous_routes"):
                route_strings = [f"{route['origin']}到{route['destination']}" for route in context['previous_routes']]
                context_info += f"之前计算过的路线: {', '.join(route_strings)}\n"
            
            if context.get("map_markers"):
                context_info += f"地图上的标记: {', '.join([marker['name'] for marker in context['map_markers']])}\n"
            
            base_prompt += context_info
        
        return base_prompt
    
    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """解析回复中的工具调用指令"""
        import re
        
        tool_calls = []
        
        # 匹配 [TOOL_CALL:function_name:{"args": "value"}] 格式，支持多行JSON
        pattern = r'\[TOOL_CALL:([^:]+):(\{.*?\})\]'
        matches = re.findall(pattern, response, re.DOTALL)
        
        print(f"DEBUG: Raw response: {response}")
        print(f"DEBUG: Found {len(matches)} tool call matches")
        
        for function_name, args_json in matches:
            try:
                # 清理JSON字符串，移除可能的换行符
                cleaned_json = args_json.strip().replace('\n', '').replace('\r', '')
                print(f"DEBUG: Cleaning JSON: {cleaned_json}")
                
                args = json.loads(cleaned_json)
                tool_calls.append({
                    "name": function_name,
                    "args": args
                })
                print(f"DEBUG: Parsed tool call: {function_name} with args: {args}")
            except json.JSONDecodeError as e:
                print(f"DEBUG: Failed to parse tool call args: {args_json}, error: {e}")
                # 尝试使用默认参数
                tool_calls.append({
                    "name": function_name,
                    "args": {}
                })
                print(f"DEBUG: Using default empty args for {function_name}")
                continue
        
        return tool_calls
    
    def _clean_tool_calls_from_response(self, response: str) -> str:
        """从回复中清理工具调用指令，只保留解释文字"""
        import re
        
        # 移除 [TOOL_CALL:...] 格式的指令
        pattern = r'\[TOOL_CALL:[^\]]+\]'
        clean_response = re.sub(pattern, '', response)
        
        # 清理多余的空白字符
        clean_response = re.sub(r'\n\s*\n', '\n\n', clean_response)
        clean_response = clean_response.strip()
        
        return clean_response
    
    async def _generate_detailed_response_from_actual_tools(self, tool_results: List[Dict[str, Any]], user_input: str) -> str:
        """基于实际工具调用结果生成详细的回复"""
        try:
            # 基于实际工具调用结果生成详细回复
            for tool_result in tool_results:
                tool_name = tool_result["name"]
                tool_args = tool_result["args"]
                result = tool_result["result"]
                
                if tool_name == "plan_trip" and result.get("success"):
                    # 处理行程规划结果
                    trip_plan = result.get("data", {}).get("trip_plan", {})
                    return self._generate_trip_planning_detailed_response_from_result(trip_plan, tool_args)
                elif tool_name == "search_poi" and result.get("success"):
                    # 处理POI搜索结果
                    return self._generate_poi_detailed_response_from_result(result.get("data", {}), tool_args)
                elif tool_name == "mark_location" and result.get("success"):
                    # 处理标记地点结果
                    return self._generate_mark_location_detailed_response_from_result(result.get("data", {}), tool_args)
                elif tool_name == "calculate_route" and result.get("success"):
                    # 处理路线计算结果
                    return self._generate_route_detailed_response_from_result(result.get("data", {}), tool_args)
            
            # 如果没有匹配的工具，返回通用回复
            return "我已经完成了您请求的操作，请查看地图上的标记获取详细信息。"
            
        except Exception as e:
            print(f"Error generating detailed response from actual tools: {e}")
            return "我已经完成了您请求的操作，请查看地图上的标记获取详细信息。"
    
    async def _generate_detailed_response_from_tools(self, tool_calls: List[Dict[str, Any]], user_input: str) -> str:
        """基于工具调用结果生成详细的回复"""
        try:
            # 收集工具调用结果
            tool_results = []
            for tool_call in tool_calls:
                if tool_call["name"] == "search_poi":
                    # 模拟获取POI搜索结果（实际应该从工具调用结果中获取）
                    tool_results.append({
                        "type": "poi_search",
                        "keyword": tool_call["args"].get("keyword", ""),
                        "city": tool_call["args"].get("city", ""),
                        "category": tool_call["args"].get("category", "")
                    })
                elif tool_call["name"] == "calculate_route":
                    tool_results.append({
                        "type": "route_calculation",
                        "origin": tool_call["args"].get("origin", ""),
                        "destination": tool_call["args"].get("destination", ""),
                        "mode": tool_call["args"].get("mode", "")
                    })
                elif tool_call["name"] == "plan_trip":
                    # 模拟获取行程规划结果
                    tool_results.append({
                        "type": "trip_planning",
                        "trip_plan": {
                            "title": f"{tool_call['args'].get('trip_duration', '1天')}行程规划",
                            "duration": tool_call["args"].get("trip_duration", "1天"),
                            "transport_mode": tool_call["args"].get("transport_mode", "mixed"),
                            "interests": tool_call["args"].get("interests", []),
                            "locations": tool_call["args"].get("selected_locations", []),
                            "schedule": [
                                {
                                    "time": "上午",
                                    "location": tool_call["args"].get("selected_locations", [""])[0] if tool_call["args"].get("selected_locations") else "选定地点",
                                    "activity": "游览选定地点",
                                    "duration": "1-2小时"
                                }
                            ],
                            "routes": [],
                            "tips": [
                                "建议提前查看各景点的开放时间",
                                "根据天气情况调整行程安排",
                                "预留充足的交通时间",
                                "携带必要的证件和物品"
                            ]
                        },
                        "selected_locations": tool_call["args"].get("selected_locations", []),
                        "trip_duration": tool_call["args"].get("trip_duration", "1天"),
                        "transport_mode": tool_call["args"].get("transport_mode", "mixed")
                    })
            
            # 基于工具结果生成详细回复
            if any(result["type"] == "trip_planning" for result in tool_results):
                return self._generate_trip_planning_detailed_response(tool_results, user_input)
            elif any(result["type"] == "poi_search" for result in tool_results):
                return self._generate_poi_detailed_response(tool_results, user_input)
            elif any(result["type"] == "route_calculation" for result in tool_results):
                return self._generate_route_detailed_response(tool_results, user_input)
            else:
                return "我已经完成了您请求的操作，请查看地图上的标记获取详细信息。"
                
        except Exception as e:
            print(f"Error generating detailed response: {e}")
            return "我已经完成了您请求的操作，请查看地图上的标记获取详细信息。"
    
    def _generate_poi_detailed_response(self, tool_results: List[Dict[str, Any]], user_input: str) -> str:
        """生成POI搜索的详细回复"""
        poi_result = next((r for r in tool_results if r["type"] == "poi_search"), None)
        if not poi_result:
            return "我已经完成了您请求的操作，请查看地图上的标记获取详细信息。"
        
        keyword = poi_result["keyword"]
        city = poi_result["city"]
        category = poi_result["category"]
        
        # 根据不同的搜索类型生成不同的回复
        if "美食" in keyword or "restaurant" in category:
            return f"""根据搜索结果，我为您找到了{city}的{keyword}信息。这些地点已经在地图上标记出来，您可以：

**推荐地点：**
- 查看地图上的标记，每个标记都包含详细的地址和评分信息
- 点击标记可以查看更详细的信息
- 建议您根据个人口味偏好和预算选择合适的餐厅

**实用建议：**
- 建议提前查看营业时间和预订信息
- 可以根据评分和价格信息进行筛选
- 如果需要特定类型的美食，请告诉我，我可以为您进一步搜索

您对这些推荐有什么特别想了解的吗？比如具体的菜品推荐、价格范围或者交通方式？"""
        
        elif "景点" in keyword or "attraction" in category:
            return f"""根据搜索结果，我为您找到了{city}的{keyword}信息。这些景点已经在地图上标记出来，您可以：

**推荐景点：**
- 查看地图上的标记，每个标记都包含详细的地址和评分信息
- 点击标记可以查看更详细的信息
- 建议您根据个人兴趣和时间安排选择合适的景点

**实用建议：**
- 建议提前查看开放时间和门票信息
- 可以根据评分和距离进行筛选
- 如果需要特定类型的景点，请告诉我，我可以为您进一步搜索

您对这些推荐有什么特别想了解的吗？比如具体的游览路线、最佳游览时间或者周边设施？"""
        
        else:
            return f"""根据搜索结果，我为您找到了{city}的{keyword}信息。这些地点已经在地图上标记出来，您可以查看详细信息。如果您需要更具体的建议或有其他问题，请随时告诉我。"""
            
    def _generate_trip_planning_detailed_response(self, tool_results: List[Dict[str, Any]], user_input: str) -> str:
        """生成行程规划的详细回复"""
        trip_result = next((r for r in tool_results if r["type"] == "trip_planning"), None)
        if not trip_result:
            return "我已经完成了您请求的操作，请查看地图上的标记获取详细信息。"
        
        trip_plan = trip_result.get("trip_plan", {})
        selected_locations = trip_result.get("selected_locations", [])
        trip_duration = trip_result.get("trip_duration", "1天")
        transport_mode = trip_result.get("transport_mode", "mixed")
        
        response = f"""🎯 **{trip_plan.get('title', '行程规划')}**

**行程概览：**
- 时长：{trip_duration}
- 交通方式：{transport_mode}
- 包含地点：{len(selected_locations)}个

**详细安排：**
"""
        
        # 添加时间安排
        schedule = trip_plan.get("schedule", [])
        for i, item in enumerate(schedule, 1):
            response += f"""
**{item.get('time', '')}** - {item.get('activity', '')}
- 地点：{item.get('location', '')}
- 预计时长：{item.get('duration', '')}
"""
        
        # 添加路线建议
        routes = trip_plan.get("routes", [])
        if routes:
            response += "\n**路线规划：**\n"
            for i, route in enumerate(routes, 1):
                response += f"""
{i}. {route.get('from', '')} → {route.get('to', '')}
   - 交通方式：{route.get('transport', '')}
   - 预计时间：{route.get('estimated_time', '')}
"""
        
        # 添加实用建议
        tips = trip_plan.get("tips", [])
        if tips:
            response += "\n**实用建议：**\n"
            for tip in tips:
                response += f"• {tip}\n"
        
        response += "\n您觉得这个行程安排如何？需要调整某个环节吗？"
        
        return response
    
    def _generate_trip_planning_detailed_response_from_result(self, trip_plan: Dict[str, Any], tool_args: Dict[str, Any]) -> str:
        """基于实际行程规划结果生成详细回复"""
        trip_duration = tool_args.get("trip_duration", "1天")
        transport_mode = tool_args.get("transport_mode", "mixed")
        selected_locations = tool_args.get("selected_locations", [])
        
        response = f"""🎯 **{trip_plan.get('title', '行程规划')}**

**行程概览：**
- 时长：{trip_duration}
- 交通方式：{transport_mode}
- 包含地点：{len(selected_locations)}个

**详细安排：**
"""
        
        # 添加时间安排
        schedule = trip_plan.get("schedule", [])
        for i, item in enumerate(schedule, 1):
            response += f"""
**{item.get('time', '')}** - {item.get('activity', '')}
- 地点：{item.get('location', '')}
- 预计时长：{item.get('duration', '')}
"""
        
        # 添加路线建议
        routes = trip_plan.get("routes", [])
        if routes:
            response += "\n**路线规划：**\n"
            for i, route in enumerate(routes, 1):
                response += f"""
{i}. {route.get('from', '')} → {route.get('to', '')}
   - 交通方式：{route.get('transport', '')}
   - 预计时间：{route.get('estimated_time', '')}
"""
        
        # 添加实用建议
        tips = trip_plan.get("tips", [])
        if tips:
            response += "\n**实用建议：**\n"
            for tip in tips:
                response += f"• {tip}\n"
        
        response += "\n您觉得这个行程安排如何？需要调整某个环节吗？"
        
        return response
    
    def _generate_poi_detailed_response_from_result(self, data: Dict[str, Any], tool_args: Dict[str, Any]) -> str:
        """基于实际POI搜索结果生成详细回复"""
        keyword = tool_args.get("keyword", "")
        city = tool_args.get("city", "")
        category = tool_args.get("category", "")
        
        pois = data.get("pois", [])
        total = data.get("total", 0)
        
        if not pois:
            return f"抱歉，没有找到{city}的{keyword}相关信息。"
        
        response = f"""根据搜索结果，我为您找到了{city}的{keyword}信息，共{total}个结果。这些地点已经在地图上标记出来，您可以：

**推荐地点：**
- 查看地图上的标记，每个标记都包含详细的地址和评分信息
- 点击标记可以查看更详细的信息
- 建议您根据个人兴趣和时间安排选择合适的景点

**实用建议：**
- 建议提前查看开放时间和门票信息
- 可以根据评分和距离进行筛选
- 如果需要特定类型的景点，请告诉我，我可以为您进一步搜索

您对这些推荐有什么特别想了解的吗？比如具体的游览路线、最佳游览时间或者周边设施？"""
        
        return response
    
    def _generate_mark_location_detailed_response_from_result(self, data: Dict[str, Any], tool_args: Dict[str, Any]) -> str:
        """基于实际标记地点结果生成详细回复"""
        location = tool_args.get("location", "")
        label = tool_args.get("label", location)
        coordinates = data.get("coordinates", {})
        
        response = f"""✅ 已成功在地图上标记：**{label}**

**位置信息：**
- 地点：{location}
- 坐标：{coordinates.get('lat', 0):.6f}, {coordinates.get('lng', 0):.6f}
- 分类：{data.get('category', 'attraction')}

这个地点已经添加到您的地图标记列表中，您可以：
- 在地图上查看标记位置
- 选择该标记进行行程规划
- 查看详细的位置信息

需要标记其他地点吗？"""
        
        return response
    
    def _generate_route_detailed_response_from_result(self, data: Dict[str, Any], tool_args: Dict[str, Any]) -> str:
        """基于实际路线计算结果生成详细回复"""
        origin = tool_args.get("origin", "")
        destination = tool_args.get("destination", "")
        mode = tool_args.get("mode", "driving")
        
        response = f"""🗺️ 路线规划完成

**路线信息：**
- 起点：{origin}
- 终点：{destination}
- 交通方式：{mode}

路线已经在地图上显示，您可以：
- 查看地图上的路线标记
- 根据不同的交通方式选择合适的路线
- 考虑实际交通状况和出行时间

**实用建议：**
- 建议提前查看实时交通状况
- 可以根据个人偏好选择不同的交通方式
- 如果需要更详细的路线规划，请告诉我具体需求

您对路线规划还有什么特别想了解的吗？比如具体的交通方式、预计时间或者沿途景点？"""
        
        return response
    
    async def _get_location_info_by_id(self, location_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """根据地点ID获取地点信息"""
        try:
            # 首先检查硬编码的映射表
            location_mapping = {
                "8fde79cc5a98e5c295ca072d": {"name": "天安门广场", "category": "attraction"},
                "d24e48eb4aac8db4afee7aec": {"name": "故宫博物院", "category": "attraction"},
                "26cb3536a49343e6f7e73bb2": {"name": "颐和园", "category": "attraction"},
                "0bd3ec34ea3b725b43afe605": {"name": "天坛公园", "category": "attraction"},
                "03ff6e2ecd84c091bea24001": {"name": "北海公园", "category": "attraction"},
            }
            
            if location_id in location_mapping:
                return location_mapping[location_id]
            
            # 如果不在硬编码映射中，尝试从上下文中的地图标记获取信息
            if context and "map_markers" in context:
                map_markers = context["map_markers"]
                for marker in map_markers:
                    if marker.get("id") == location_id:
                        return {
                            "name": marker.get("name", f"地点{location_id[:8]}"),
                            "category": marker.get("category", "unknown")
                        }
            
            # 如果都没有找到，返回一个更友好的默认名称
            return {"name": f"地点{location_id[:8]}", "category": "unknown"}
            
        except Exception as e:
            print(f"Error getting location info for {location_id}: {e}")
            return {"name": f"地点{location_id[:8]}", "category": "unknown"}
    
    def _generate_route_detailed_response(self, tool_results: List[Dict[str, Any]], user_input: str) -> str:
        """生成路线规划的详细回复"""
        route_result = next((r for r in tool_results if r["type"] == "route_calculation"), None)
        if not route_result:
            return "我已经完成了您请求的操作，请查看地图上的标记获取详细信息。"
        
        origin = route_result["origin"]
        destination = route_result["destination"]
        mode = route_result["mode"]
        
        return f"""我已经为您计算了从{origin}到{destination}的路线信息。路线已经在地图上显示，您可以：

**路线信息：**
- 查看地图上的路线标记
- 根据不同的交通方式选择合适的路线
- 考虑实际交通状况和出行时间

**实用建议：**
- 建议提前查看实时交通状况
- 可以根据个人偏好选择不同的交通方式
- 如果需要更详细的路线规划，请告诉我具体需求

您对路线规划还有什么特别想了解的吗？比如具体的交通方式、预计时间或者沿途景点？"""
    
    async def _execute_tool_call(self, function_name: str, arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            print(f"DEBUG: Executing tool call: {function_name} with args: {arguments}")
            
            if function_name == "search_poi":
                keyword = arguments.get("keyword", "景点")
                city = arguments.get("city", "北京")
                category = arguments.get("category", "attraction")
                location = arguments.get("location")
                
                # 如果有location参数，使用地理编码API获取坐标
                location_coords = None
                if location:
                    # 使用百度地图地理编码API
                    location_coords = baidu_map_tools.geocode(location)
                    if not location_coords:
                        print(f"DEBUG: 地理编码失败，使用城市中心点: {city}")
                        # 如果地理编码失败，使用城市中心点
                        city_centers = {
                            "北京": {"lat": 39.9042, "lng": 116.4074},
                            "上海": {"lat": 31.2304, "lng": 121.4737},
                            "广州": {"lat": 23.1291, "lng": 113.2644},
                            "深圳": {"lat": 22.5431, "lng": 114.0579},
                            "杭州": {"lat": 30.2741, "lng": 120.1551},
                            "南京": {"lat": 32.0603, "lng": 118.7969},
                            "成都": {"lat": 30.5728, "lng": 104.0668},
                            "武汉": {"lat": 30.5928, "lng": 114.3055}
                        }
                        location_coords = city_centers.get(city, city_centers["北京"])
                
                result = baidu_map_tools.search_poi(
                    keyword=keyword,
                    city=city,
                    category=category,
                    location=location_coords,
                    radius=5000  # 5公里半径
                )
                return result.model_dump() if hasattr(result, 'model_dump') else result
                
            elif function_name == "calculate_route":
                origin = arguments.get("origin")
                destination = arguments.get("destination")
                mode = arguments.get("mode", "driving")
                
                # 先进行地理编码，将地址转换为坐标
                origin_coords = None
                destination_coords = None
                
                if origin:
                    origin_coords = baidu_map_tools.geocode(origin)
                    if not origin_coords:
                        print(f"DEBUG: 起点地理编码失败: {origin}")
                        return {"success": False, "error": f"无法找到起点位置: {origin}"}
                
                if destination:
                    destination_coords = baidu_map_tools.geocode(destination)
                    if not destination_coords:
                        print(f"DEBUG: 终点地理编码失败: {destination}")
                        return {"success": False, "error": f"无法找到终点位置: {destination}"}
                
                # 使用坐标计算路线
                result = baidu_map_tools.calculate_route(
                    origin=f"{origin_coords['lat']},{origin_coords['lng']}",
                    destination=f"{destination_coords['lat']},{destination_coords['lng']}",
                    mode=mode
                )
                return result.model_dump() if hasattr(result, 'model_dump') else result
                
            elif function_name == "mark_location":
                location = arguments.get("location")
                label = arguments.get("label", "")
                category = arguments.get("category", "attraction")
                
                # 进行地理编码获取坐标
                coords = baidu_map_tools.geocode(location)
                if not coords:
                    return {"success": False, "error": f"无法找到地点: {location}"}
                
                # 生成标记ID
                marker_id = f"marker_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
                
                # 返回标记信息
                return {
                    "success": True,
                    "data": {
                        "marker_id": marker_id,
                        "location": location,
                        "label": label or location,
                        "category": category,
                        "coordinates": coords,
                        "message": f"已在地图上标记: {label or location}"
                    }
                }
                
            elif function_name == "plan_trip":
                selected_locations = arguments.get("selected_locations", [])
                trip_duration = arguments.get("trip_duration", "1天")
                transport_mode = arguments.get("transport_mode", "mixed")
                interests = arguments.get("interests", [])
                
                if not selected_locations:
                    return {"success": False, "error": "请先选择要规划的地点"}
                
                # 生成行程规划
                trip_plan = await self._generate_trip_plan(
                    selected_locations, trip_duration, transport_mode, interests, context
                )
                
                return {
                    "success": True,
                    "data": {
                        "trip_plan": trip_plan,
                        "selected_locations": selected_locations,
                        "trip_duration": trip_duration,
                        "transport_mode": transport_mode,
                        "interests": interests
                    }
                }
                
            else:
                return {"success": False, "error": f"未知的工具: {function_name}"}
                
        except Exception as e:
            print(f"Error executing tool call {function_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_trip_plan(self, selected_locations: List[str], trip_duration: str, 
                                transport_mode: str, interests: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成行程规划"""
        try:
            # 这里可以根据选中的地点生成详细的行程规划
            # 包括时间安排、路线优化、建议等
            
            plan = {
                "title": f"{trip_duration}行程规划",
                "duration": trip_duration,
                "transport_mode": transport_mode,
                "interests": interests,
                "locations": selected_locations,
                "schedule": [],
                "routes": [],
                "tips": []
            }
            
            # 根据时长和地点数量生成时间安排
            if trip_duration == "半天":
                time_slots = ["上午", "中午"]
            elif trip_duration == "1天":
                time_slots = ["上午", "中午", "下午", "晚上"]
            elif trip_duration == "2天":
                time_slots = ["第一天上午", "第一天中午", "第一天下午", "第一天晚上", 
                            "第二天上午", "第二天中午", "第二天下午"]
            else:
                time_slots = ["上午", "中午", "下午", "晚上"]
            
            # 为每个地点分配时间段
            for i, location_id in enumerate(selected_locations):
                if i < len(time_slots):
                    # 根据地点ID查找地点信息
                    location_info = await self._get_location_info_by_id(location_id, context)
                    location_name = location_info.get("name", location_id)
                    
                    plan["schedule"].append({
                        "time": time_slots[i],
                        "location": f"{location_name}（{location_id}）",
                        "activity": f"游览{location_name}",
                        "duration": "1-2小时"
                    })
            
            # 生成路线建议
            if len(selected_locations) > 1:
                for i in range(len(selected_locations) - 1):
                    # 获取起点和终点的名称
                    from_info = await self._get_location_info_by_id(selected_locations[i], context)
                    to_info = await self._get_location_info_by_id(selected_locations[i + 1], context)
                    from_name = from_info.get("name", selected_locations[i])
                    to_name = to_info.get("name", selected_locations[i + 1])
                    
                    plan["routes"].append({
                        "from": f"{from_name}（{selected_locations[i]}）",
                        "to": f"{to_name}（{selected_locations[i + 1]}）",
                        "transport": transport_mode,
                        "estimated_time": "15-30分钟"
                    })
            
            # 生成实用建议
            plan["tips"] = [
                "建议提前查看各景点的开放时间",
                "根据天气情况调整行程安排",
                "预留充足的交通时间",
                "携带必要的证件和物品"
            ]
            
            return plan
            
        except Exception as e:
            print(f"Error generating trip plan: {e}")
            return {
                "title": "行程规划生成失败",
                "error": str(e)
            }
