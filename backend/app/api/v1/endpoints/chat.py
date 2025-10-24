"""聊天对话API端点

This module provides chat endpoints with AG-UI protocol support.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.llm_service import chat_with_agui_stream, simple_chat, test_llm_connection
from app.services.agent_service import agent_service
from app.utils.agui_utils import generate_run_id

router = APIRouter()


@router.post(
    "/stream",
    summary="流式对话",
    description="使用AG-UI协议进行流式对话，返回SSE事件流"
)
async def stream_chat(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式对话端点
    
    请求格式:
    {
        "message": "用户消息",
        "system_prompt": "系统提示词（可选）",
        "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
        "run_id": "运行ID（可选）"
    }
    """
    try:
        message = request.get("message", "")
        system_prompt = request.get("system_prompt")
        history = request.get("history", [])
        run_id = request.get("run_id")
        
        if not message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )
        
        # 生成流式响应
        async def generate_stream():
            async for event in chat_with_agui_stream(
                user_input=message,
                system_prompt=system_prompt,
                history=history,
                run_id=run_id
            ):
                yield event
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"流式对话失败: {str(e)}"
        )


@router.post(
    "/simple",
    summary="简单对话",
    description="简单对话接口，返回完整响应"
)
async def simple_chat_endpoint(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    简单对话端点
    
    请求格式:
    {
        "message": "用户消息",
        "system_prompt": "系统提示词（可选）",
        "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    }
    """
    try:
        message = request.get("message", "")
        system_prompt = request.get("system_prompt")
        history = request.get("history", [])
        
        if not message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )
        
        response = await simple_chat(
            user_input=message,
            system_prompt=system_prompt,
            history=history
        )
        
        return {
            "success": True,
            "response": response,
            "run_id": generate_run_id()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话失败: {str(e)}"
        )


@router.get(
    "/test",
    summary="测试LLM连接",
    description="测试LLM服务连接状态"
)
async def test_llm(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    测试LLM连接端点
    """
    try:
        result = await test_llm_connection()
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"测试失败: {str(e)}",
            "api_key_configured": False
        }


@router.get(
    "/health",
    summary="聊天服务健康检查",
    description="检查聊天服务状态"
)
async def chat_health():
    """
    聊天服务健康检查
    """
    return {
        "status": "healthy",
        "service": "chat",
        "protocol": "AG-UI",
        "version": "1.0.0"
    }


@router.get(
    "/agents",
    summary="获取可用Agent列表",
    description="获取所有可用的Agent及其信息"
)
async def get_agents():
    """获取可用Agent列表"""
    try:
        agents = agent_service.get_available_agents()
        agent_info = {}
        
        for agent_id in agents:
            info = agent_service.get_agent_info(agent_id)
            if info:
                agent_info[agent_id] = info
        
        return {
            "success": True,
            "agents": agent_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Agent列表失败: {str(e)}"
        )


@router.post(
    "/agents/{agent_id}/stream",
    summary="运行指定Agent",
    description="运行指定的Agent进行流式对话"
)
async def run_agent_stream(
    agent_id: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    运行指定Agent进行流式对话
    
    Args:
        agent_id: Agent ID (trip-planner, budget-analyzer, chat-assistant)
        request: 请求数据
            - message: 用户消息
            - systemPrompt: 系统提示词 (可选)
            - history: 对话历史 (可选)
            - runId: 运行ID (可选)
    """
    try:
        # 验证Agent是否存在
        agent = agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} 不存在"
            )
        
        # 提取请求参数
        message = request.get("message", "")
        system_prompt = request.get("systemPrompt")
        history = request.get("history", [])
        run_id = request.get("runId")
        context = request.get("context", {})
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )
        
        # 生成运行ID
        if not run_id:
            run_id = generate_run_id()
        
        # 创建流式响应生成器
        async def generate_response():
            try:
                async for event in agent_service.run_agent(
                    agent_id=agent_id,
                    user_input=message,
                    system_prompt=system_prompt,
                    history=history,
                    run_id=run_id,
                    context=context
                ):
                    yield event
            except Exception as e:
                # 发送错误事件
                from app.utils.agui_encoder import AGUIEventEncoder
                from app.utils.agui_types import create_event, AGUIEventType
                from datetime import datetime
                
                encoder = AGUIEventEncoder()
                error_event = create_event(
                    AGUIEventType.RUN_ERROR,
                    data={
                        "runId": run_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                yield encoder.encode_event(error_event)
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"运行Agent失败: {str(e)}"
        )
