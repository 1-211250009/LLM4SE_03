"""
Agent服务

管理各种Agent的创建和调用
"""

from typing import Dict, Any, AsyncGenerator, Optional
from ..agents import (
    BaseAgent,
    TripPlannerAgent,
    BudgetAnalyzerAgent,
    ChatAssistantAgent
)
from ..agents.simple_trip_agent import SimpleTripAgent


class AgentService:
    """
    Agent服务类
    
    负责管理各种Agent的创建、配置和调用
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """初始化所有Agent"""
        self.agents = {
            "trip-planner": TripPlannerAgent(),
            "simple-trip-planner": SimpleTripAgent(),
            "budget-analyzer": BudgetAnalyzerAgent(),
            "chat-assistant": ChatAssistantAgent()
        }
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取指定ID的Agent"""
        return self.agents.get(agent_id)
    
    def get_available_agents(self) -> Dict[str, str]:
        """获取所有可用的Agent"""
        return {
            agent_id: agent.agent_name 
            for agent_id, agent in self.agents.items()
        }
    
    async def run_agent(
        self,
        agent_id: str,
        user_input: str,
        system_prompt: str = None,
        history: list = None,
        run_id: str = None,
        context: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """
        运行指定的Agent
        
        Args:
            agent_id: Agent ID
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            run_id: 运行ID
            
        Yields:
            AG-UI格式的SSE事件流
        """
        agent = self.get_agent(agent_id)
        if not agent:
            # 如果Agent不存在，返回错误事件
            from ..utils.agui_encoder import AGUIEventEncoder
            from ..utils.agui_types import create_event, AGUIEventType
            from datetime import datetime
            
            encoder = AGUIEventEncoder()
            error_event = create_event(
                AGUIEventType.RUN_ERROR,
                data={
                    "runId": run_id or "unknown",
                    "error": f"Agent {agent_id} 不存在",
                    "timestamp": datetime.now().isoformat()
                }
            )
            yield encoder.encode_event(error_event)
            return
        
        # 运行Agent
        async for event in agent.run(user_input, system_prompt, history, run_id, context):
            yield event
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取Agent信息"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        return {
            "agentId": agent.agent_id,
            "agentName": agent.agent_name,
            "description": self._get_agent_description(agent_id)
        }
    
    def _get_agent_description(self, agent_id: str) -> str:
        """获取Agent描述"""
        descriptions = {
            "trip-planner": "专业的旅行行程规划助手，帮助您制定详细的旅行计划",
            "simple-trip-planner": "简化的行程规划助手，专注于LLM Function Calling",
            "budget-analyzer": "费用分析专家，协助您制定和管理旅行预算",
            "chat-assistant": "通用对话助手，回答各种问题和提供咨询服务"
        }
        return descriptions.get(agent_id, "未知Agent")


# 全局Agent服务实例
agent_service = AgentService()
