"""
基础Agent类

所有Agent的基类，提供AG-UI协议事件生成和工具调用功能
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncGenerator, Optional
from datetime import datetime
import uuid

from ..utils.agui_types import (
    AGUIEvent, AGUIEventType, create_event
)
from ..utils.agui_utils import generate_run_id, generate_message_id
from ..utils.agui_encoder import AGUIEventEncoder


class BaseAgent(ABC):
    """
    基础Agent类
    
    提供AG-UI协议事件生成、工具调用等基础功能
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.encoder = AGUIEventEncoder()
        
    @abstractmethod
    async def run(
        self, 
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        run_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        运行Agent
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            run_id: 运行ID
            
        Yields:
            AG-UI格式的SSE事件流
        """
        pass
    
    def _create_run_started_event(self, run_id: str) -> str:
        """创建RUN_STARTED事件"""
        event = create_event(
            AGUIEventType.RUN_STARTED,
            data={
                "runId": run_id,
                "agentId": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        return self.encoder.encode_event(event)
    
    def _create_run_finished_event(self, run_id: str, result: Dict[str, Any] = None) -> str:
        """创建RUN_FINISHED事件"""
        event = create_event(
            AGUIEventType.RUN_FINISHED,
            data={
                "runId": run_id,
                "result": result or {},
                "timestamp": datetime.now().isoformat()
            }
        )
        return self.encoder.encode_event(event)
    
    def _create_run_error_event(self, run_id: str, error: str) -> str:
        """创建RUN_ERROR事件"""
        event = create_event(
            AGUIEventType.RUN_ERROR,
            data={
                "runId": run_id,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        )
        return self.encoder.encode_event(event)
    
    def _create_text_message_delta_event(self, content: str, message_id: str) -> str:
        """创建TEXT_MESSAGE_DELTA事件"""
        return self.encoder.encode_text_stream(content, message_id)
    
    def _create_text_message_content_event(self, content: str, message_id: str) -> str:
        """创建TEXT_MESSAGE_CONTENT事件"""
        event = create_event(
            AGUIEventType.TEXT_MESSAGE_CONTENT,
            data={
                "content": content,
                "messageId": message_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        return self.encoder.encode_event(event)
    
    def _create_tool_call_request_event(self, tool_name: str, parameters: Dict[str, Any], call_id: str) -> str:
        """创建TOOL_CALL_REQUEST事件"""
        # 确保参数不为None
        if tool_name is None:
            tool_name = "unknown"
        if parameters is None:
            parameters = {}
        if call_id is None:
            call_id = f"call_{int(datetime.now().timestamp())}"
            
        event = create_event(
            AGUIEventType.TOOL_CALL_REQUEST,
            data={
                "toolName": tool_name,
                "parameters": parameters,
                "callId": call_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        return self.encoder.encode_event(event)
    
    def _create_tool_call_result_event(self, call_id: str, result: Dict[str, Any]) -> str:
        """创建TOOL_CALL_RESULT事件"""
        # 确保参数不为None
        if call_id is None:
            call_id = f"call_{int(datetime.now().timestamp())}"
        if result is None:
            result = {"success": False, "error": "No result provided"}
            
        event = create_event(
            AGUIEventType.TOOL_CALL_RESULT,
            data={
                "callId": call_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        )
        return self.encoder.encode_event(event)
    
    def _create_system_message_event(self, message: str, level: str = "info") -> str:
        """创建SYSTEM_MESSAGE事件"""
        event = create_event(
            AGUIEventType.SYSTEM_MESSAGE,
            data={
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat()
            }
        )
        return self.encoder.encode_event(event)
    
    async def _call_frontend_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用前端工具
        
        注意：这是一个模拟实现，实际应该通过WebSocket或HTTP与前端通信
        """
        # 模拟工具调用结果
        mock_results = {
            "searchPOI": {
                "success": True,
                "data": {
                    "results": [
                        {
                            "id": "poi_1",
                            "name": "故宫博物院",
                            "address": "北京市东城区景山前街4号",
                            "location": {"lat": 39.9163, "lng": 116.3972},
                            "category": "attraction",
                            "rating": 4.8,
                            "price": "60元",
                            "description": "明清两朝的皇家宫殿，世界文化遗产"
                        }
                    ],
                    "total": 1
                }
            },
            "calculateRoute": {
                "success": True,
                "data": {
                    "route": {
                        "distance": 2500,
                        "duration": 1800,
                        "steps": [
                            {"instruction": "从起点出发", "distance": 0, "duration": 0},
                            {"instruction": "沿主路直行", "distance": 2500, "duration": 1800},
                            {"instruction": "到达目的地", "distance": 0, "duration": 0}
                        ]
                    }
                }
            },
            "queryPrice": {
                "success": True,
                "data": {
                    "type": "hotel",
                    "location": "北京",
                    "prices": [
                        {"name": "经济型酒店", "price": 200, "currency": "CNY"},
                        {"name": "商务酒店", "price": 400, "currency": "CNY"}
                    ],
                    "averagePrice": 300
                }
            },
            "getWeather": {
                "success": True,
                "data": {
                    "location": "北京",
                    "temperature": {"min": 15, "max": 25, "current": 20},
                    "condition": "晴",
                    "description": "晴朗，适合出行"
                }
            }
        }
        
        # 模拟异步调用
        await asyncio.sleep(0.1)
        
        return mock_results.get(tool_name, {
            "success": False,
            "error": f"工具 {tool_name} 不存在"
        })
    
    def _format_messages_for_llm(
        self, 
        user_input: str, 
        system_prompt: str = None, 
        history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """格式化消息给LLM"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": user_input})
        
        return messages
