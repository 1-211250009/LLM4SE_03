"""
通用对话助手Agent

提供通用的对话和问答功能
"""

import asyncio
import json
from typing import Dict, Any, List, AsyncGenerator, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..services.llm_service import llm_service_instance


class ChatAssistantAgent(BaseAgent):
    """
    通用对话助手Agent
    
    提供通用的对话、问答和咨询服务
    """
    
    def __init__(self):
        super().__init__(
            agent_id="chat-assistant",
            agent_name="对话助手"
        )
    
    async def run(
        self, 
        user_input: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        run_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        运行对话助手Agent
        """
        if not run_id:
            run_id = f"chat_{int(datetime.now().timestamp())}"
        
        try:
            # 1. 发送RUN_STARTED事件
            yield self._create_run_started_event(run_id)
            
            # 2. 生成系统提示词
            system_prompt = self._generate_system_prompt(system_prompt)
            
            # 3. 格式化消息
            messages = self._format_messages_for_llm(user_input, system_prompt, history)
            
            # 4. 流式调用LLM
            message_id = f"chat_msg_{int(datetime.now().timestamp())}"
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
            
            # 5. 发送文本消息完成事件
            yield self._create_text_message_content_event(full_response, message_id)
            
            # 6. 发送RUN_FINISHED事件
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
        
        return """你是一个友好的AI助手，专门帮助用户解答各种问题。

你可以提供以下帮助：
1. 回答一般性问题
2. 提供信息咨询
3. 协助解决问题
4. 进行日常对话
5. 提供建议和指导

请保持回答友好、准确、有用。如果遇到不确定的问题，请诚实地说不知道，并建议用户如何获取准确信息。"""
