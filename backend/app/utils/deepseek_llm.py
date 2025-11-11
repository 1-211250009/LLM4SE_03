"""DeepSeek LLM API集成

This module provides integration with DeepSeek LLM API.
"""

import httpx
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.core.config import settings


class DeepSeekLLMService:
    """DeepSeek LLM服务类"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com"
        self.model = "deepseek-chat"
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        调用DeepSeek LLM聊天完成API
        
        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式响应
            tools: 工具定义列表，用于Function Calling
            
        Returns:
            API响应结果
        """
        if not self.api_key:
            raise ValueError("DeepSeek API Key未配置")
        
        model = model or self.model
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        # 如果提供了工具定义，添加到payload中
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"  # 让模型自动决定是否使用工具
        
        try:
            # 增加超时时间到60秒，因为AI响应可能需要更长时间
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                if stream:
                    return response  # 返回响应对象用于流式处理
                else:
                    return response.json()
                    
        except httpx.HTTPStatusError as e:
            raise Exception(f"DeepSeek API调用失败: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"DeepSeek API调用异常: {str(e)}")
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式调用DeepSeek LLM聊天完成API
        
        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 工具定义列表，用于Function Calling
            
        Yields:
            流式响应数据
        """
        if not self.api_key:
            raise ValueError("DeepSeek API Key未配置")
        
        model = model or self.model
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        # 如果提供了工具定义，添加到payload中
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"  # 让模型自动决定是否使用工具
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # 移除 "data: " 前缀
                            
                            if data.strip() == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data)
                                yield data  # 返回原始数据
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            raise Exception(f"DeepSeek流式API调用失败: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"DeepSeek流式API调用异常: {str(e)}")
    
    def format_messages(self, user_input: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """
        格式化消息列表
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            
        Returns:
            格式化的消息列表
        """
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史对话
        if history:
            messages.extend(history)
        
        # 添加用户输入
        messages.append({"role": "user", "content": user_input})
        
        return messages


# 创建全局实例
deepseek_llm_service = DeepSeekLLMService()


# 兼容性函数
async def stream_llm_response(user_input: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> AsyncGenerator[str, None]:
    """
    流式调用DeepSeek LLM的兼容性函数
    
    Args:
        user_input: 用户输入
        system_prompt: 系统提示词
        history: 对话历史
        
    Yields:
        流式响应数据
    """
    messages = deepseek_llm_service.format_messages(user_input, system_prompt, history)
    async for chunk in deepseek_llm_service.stream_chat_completion(messages):
        yield chunk
