"""LLM服务层

This module provides high-level LLM service functions with AG-UI protocol integration.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.utils.deepseek_llm import deepseek_llm_service, stream_llm_response
from app.utils.agui_encoder import AGUIEventEncoder
from app.utils.agui_utils import generate_run_id, generate_message_id


class LLMService:
    """LLM服务类，集成AG-UI协议"""
    
    def __init__(self):
        self.encoder = AGUIEventEncoder()
    
    async def chat_with_agui_stream(
        self,
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        run_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        使用AG-UI协议进行流式对话
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            run_id: 运行ID
            
        Yields:
            AG-UI格式的SSE事件流
        """
        if not run_id:
            run_id = generate_run_id()
        
        message_id = generate_message_id()
        
        try:
            # 1. 发送RUN_STARTED事件
            yield self.encoder.encode_run_started(run_id, "default-agent")
            
            # 2. 流式调用LLM API
            full_response = ""
            async for chunk_data in stream_llm_response(user_input, system_prompt, history):
                try:
                    # 解析阿里云API的流式响应
                    chunk = json.loads(chunk_data)
                    
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        choice = chunk["choices"][0]
                        
                        if "delta" in choice and "content" in choice["delta"]:
                            content = choice["delta"]["content"]
                            full_response += content
                            
                            # 发送TEXT_MESSAGE_DELTA事件
                            yield self.encoder.encode_text_stream(content, message_id)
                        
                        # 检查是否完成
                        if choice.get("finish_reason") == "stop":
                            break
                            
                except json.JSONDecodeError:
                    continue
            
            # 3. 发送TEXT_MESSAGE_DONE事件
            yield self.encoder.encode_text_stream("", message_id)  # 空内容表示完成
            
            # 4. 发送RUN_FINISHED事件
            result = {
                "messageId": message_id,
                "content": full_response,
                "runId": run_id
            }
            yield self.encoder.encode_run_finished(run_id, result)
            
        except Exception as e:
            # 发送RUN_ERROR事件
            yield self.encoder.encode_run_error(run_id, str(e))
    
    async def simple_chat(
        self,
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        简单对话（非流式）
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            
        Returns:
            LLM响应内容
        """
        try:
            messages = deepseek_llm_service.format_messages(user_input, system_prompt, history)
            result = await deepseek_llm_service.chat_completion(messages, stream=False)
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "抱歉，我无法生成回复。"
                
        except Exception as e:
            return f"发生错误: {str(e)}"
    
    async def stream_llm_response(
        self,
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式调用LLM API
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            
        Yields:
            LLM响应的JSON字符串
        """
        async for chunk in stream_llm_response(user_input, system_prompt, history):
            yield chunk
    
    async def stream_llm_response_with_tools(
        self,
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        带工具的流式LLM响应
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            tools: 工具定义列表
            
        Yields:
            流式响应数据
        """
        try:
            messages = deepseek_llm_service.format_messages(user_input, system_prompt, history)
            generator = deepseek_llm_service.stream_chat_completion(messages, tools=tools)
            try:
                async for chunk in generator:
                    yield chunk
            finally:
                # 确保生成器被正确关闭
                if hasattr(generator, 'aclose'):
                    try:
                        await generator.aclose()
                    except:
                        pass
        except Exception as e:
            print(f"带工具的LLM流式调用错误: {e}")
            yield json.dumps({"error": str(e)})

    async def test_llm_connection(self) -> Dict[str, Any]:
        """
        测试LLM连接
        
        Returns:
            测试结果
        """
        try:
            is_connected = await deepseek_llm_service.test_connection()
            
            return {
                "success": is_connected,
                "message": "LLM连接成功" if is_connected else "LLM连接失败",
                "api_key_configured": bool(deepseek_llm_service.api_key)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"LLM连接测试失败: {str(e)}",
                "api_key_configured": bool(deepseek_llm_service.api_key)
            }


# 全局LLM服务实例
llm_service_instance = LLMService()


async def chat_with_agui_stream(
    user_input: str,
    system_prompt: str = None,
    history: List[Dict[str, str]] = None,
    run_id: str = None
) -> AsyncGenerator[str, None]:
    """
    便捷函数：使用AG-UI协议进行流式对话
    """
    async for event in llm_service_instance.chat_with_agui_stream(
        user_input, system_prompt, history, run_id
    ):
        yield event


async def simple_chat(
    user_input: str,
    system_prompt: str = None,
    history: List[Dict[str, str]] = None
) -> str:
    """
    便捷函数：简单对话
    """
    return await llm_service_instance.simple_chat(user_input, system_prompt, history)


async def test_llm_connection() -> Dict[str, Any]:
    """
    便捷函数：测试LLM连接
    """
    return await llm_service_instance.test_llm_connection()
