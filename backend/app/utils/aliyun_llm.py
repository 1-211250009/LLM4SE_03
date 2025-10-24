"""阿里云LLM API集成

This module provides integration with Alibaba Cloud LLM API (DashScope).
"""

import httpx
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.core.config import settings


class AliyunLLMService:
    """阿里云LLM服务类"""
    
    def __init__(self):
        self.api_key = settings.ALIYUN_LLM_API_KEY
        self.base_url = settings.ALIYUN_LLM_ENDPOINT
        self.model = "deepseek-chat"  # 默认模型
        
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
        调用阿里云LLM聊天完成API
        
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
            raise ValueError("阿里云LLM API Key未配置")
        
        model = model or self.model
        url = f"{self.base_url}/chat/completions"
        
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                if stream:
                    return response  # 返回响应对象用于流式处理
                else:
                    return response.json()
                    
        except httpx.HTTPStatusError as e:
            raise Exception(f"阿里云LLM API调用失败: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"阿里云LLM API调用异常: {str(e)}")
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式调用阿里云LLM聊天完成API
        
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
            raise ValueError("阿里云LLM API Key未配置")
        
        model = model or self.model
        url = f"{self.base_url}/chat/completions"
        
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
            raise Exception(f"阿里云LLM流式API调用失败: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"阿里云LLM流式API调用异常: {str(e)}")
    
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
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 添加对话历史
        if history:
            messages.extend(history)
        
        # 添加用户输入
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        return messages
    
    async def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            test_messages = [
                {"role": "user", "content": "你好"}
            ]
            
            result = await self.chat_completion(test_messages)
            return "choices" in result
            
        except Exception:
            return False


# 全局LLM服务实例
llm_service = AliyunLLMService()


async def get_llm_response(
    user_input: str,
    system_prompt: str = None,
    history: List[Dict[str, str]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """
    获取LLM响应的便捷函数
    
    Args:
        user_input: 用户输入
        system_prompt: 系统提示词
        history: 对话历史
        stream: 是否流式响应
        
    Returns:
        LLM响应结果
    """
    messages = llm_service.format_messages(user_input, system_prompt, history)
    return await llm_service.chat_completion(messages, stream=stream)


async def stream_llm_response(
    user_input: str,
    system_prompt: str = None,
    history: List[Dict[str, str]] = None
) -> AsyncGenerator[str, None]:
    """
    流式获取LLM响应的便捷函数
    
    Args:
        user_input: 用户输入
        system_prompt: 系统提示词
        history: 对话历史
        
    Yields:
        流式响应数据
    """
    messages = llm_service.format_messages(user_input, system_prompt, history)
    async for chunk in llm_service.stream_chat_completion(messages):
        yield chunk
