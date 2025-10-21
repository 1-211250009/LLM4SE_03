# AG-UI协议实现指南

## 概述

本文档详细说明如何在AI旅行规划师项目中实现AG-UI协议，确保前端与AI Agent之间的标准化通信。

**AG-UI协议文档**: 参见 `doc/AG-UI.txt` 或访问 https://docs.ag-ui.com/

---

## 一、AG-UI协议核心概念

### 1.1 什么是AG-UI协议？

AG-UI（Agent User Interaction Protocol）是一个**开放、轻量、事件驱动**的协议，用于标准化AI Agent与用户界面之间的通信。

**核心特性**:
- ✅ 事件驱动架构 - 16种标准事件类型
- ✅ 流式响应 - 实时显示AI生成内容
- ✅ 双向交互 - Agent可以调用前端工具
- ✅ 状态同步 - 前后端状态实时同步
- ✅ 传输无关 - 支持SSE、Binary、WebSocket等

### 1.2 为什么使用AG-UI？

传统的RESTful API难以满足AI Agent的需求：
- ❌ Agent运行时间长，需要流式反馈
- ❌ Agent输出不确定，难以预定义响应格式
- ❌ Agent需要调用前端能力（Human-in-the-Loop）
- ❌ 需要同步复杂的会话状态

AG-UI协议完美解决这些问题：
- ✅ 实时流式事件，提供即时反馈
- ✅ 灵活的事件系统，适应各种输出
- ✅ 前端工具系统，支持人机协作
- ✅ 高效的状态同步机制

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    前端（React）                      │
│  ┌──────────────────────────────────────────────┐   │
│  │           AG-UI客户端层                       │   │
│  │  ┌────────────────┐  ┌────────────────┐     │   │
│  │  │ EventSource    │  │ AgentSubscriber │     │   │
│  │  │ SSE客户端      │  │ 事件订阅器       │     │   │
│  │  └────────┬───────┘  └────────┬───────┘     │   │
│  │           │                   │             │   │
│  │  ┌────────▼───────────────────▼────────┐    │   │
│  │  │       事件处理器                     │    │   │
│  │  │  - onTextMessageContent              │    │   │
│  │  │  - onToolCallStart                   │    │   │
│  │  │  - onStateChanged                    │    │   │
│  │  └──────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         前端工具注册表                        │   │
│  │  Tools: [searchPOI, calculateRoute, ...]     │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP POST + SSE
                       │ RunAgentInput → AG-UI Events
┌──────────────────────▼───────────────────────────────┐
│                   后端（Node.js）                     │
│  ┌──────────────────────────────────────────────┐   │
│  │           AG-UI Agent层                       │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │      TripPlannerAgent                  │  │   │
│  │  │      (extends AbstractAgent)           │  │   │
│  │  │                                        │  │   │
│  │  │  run(input: RunAgentInput)            │  │   │
│  │  │    → Observable<BaseEvent>            │  │   │
│  │  └────────────────────────────────────────┘  │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                               │
│  ┌──────────────────▼───────────────────────────┐   │
│  │         AG-UI事件生成器                       │   │
│  │  ┌──────────────┐  ┌──────────────────────┐ │   │
│  │  │ EventEmitter │  │   SSE EventEncoder   │ │   │
│  │  └──────────────┘  └──────────────────────┘ │   │
│  └──────────────────────────────────────────────┘   │
│                     │                               │
│  ┌──────────────────▼───────────────────────────┐   │
│  │           LLM服务层                           │   │
│  │  ┌─────────────────────────────────────────┐ │   │
│  │  │  阿里云百炼平台API                       │ │   │
│  │  │  - 调用千问模型                          │ │   │
│  │  │  - 流式响应处理                          │ │   │
│  │  │  - 消息格式转换                          │ │   │
│  │  └─────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 2.2 通信流程

```
用户 → 前端 → AG-UI客户端 → HTTP POST → AG-UI Agent → LLM → 事件流 → SSE → 前端 → 用户

详细流程：
1. 用户输入旅行需求
2. 前端构造RunAgentInput（包含messages、tools、state）
3. POST请求到 /api/v1/agent/trip-planner
4. Agent处理请求，调用阿里云LLM
5. LLM流式返回内容
6. Agent发出AG-UI事件（RUN_STARTED, TEXT_MESSAGE_*, TOOL_CALL_*, etc.）
7. SSE流式传输事件到前端
8. 前端EventSource接收事件
9. AgentSubscriber处理事件，更新UI
10. 如果需要工具，前端执行并返回结果
11. Agent继续处理直到完成
12. 发出RUN_FINISHED事件
```

---

## 三、后端实现（Python + FastAPI）

### 3.1 依赖安装

```bash
cd backend

# AG-UI相关（Python）
poetry add ag-ui-protocol  # AG-UI官方Python SDK（如果可用）

# 或手动安装相关依赖
poetry add pydantic
poetry add sse-starlette   # SSE支持

# 如果ag-ui-protocol不可用，我们手动实现AG-UI协议
```

**注意**: 本项目使用Python后端，AG-UI协议的Python实现基于官方SDK或手动实现。

### 3.2 AG-UI类型定义（Python）

创建 `app/schemas/agui.py`:

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, List, Union
from enum import Enum

# ============ 事件类型枚举 ============
class EventType(str, Enum):
    # 生命周期事件
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"
    STEP_STARTED = "STEP_STARTED"
    STEP_FINISHED = "STEP_FINISHED"
    
    # 文本消息事件
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    TEXT_MESSAGE_CHUNK = "TEXT_MESSAGE_CHUNK"  # 便捷事件
    
    # 工具调用事件
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    TOOL_CALL_CHUNK = "TOOL_CALL_CHUNK"  # 便捷事件
    
    # 状态管理事件
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"
    MESSAGES_SNAPSHOT = "MESSAGES_SNAPSHOT"
    
    # 特殊事件
    RAW = "RAW"
    CUSTOM = "CUSTOM"

# ============ 基础事件 ============
class BaseEvent(BaseModel):
    type: EventType
    timestamp: Optional[int] = None
    raw_event: Optional[Any] = None

# ============ 生命周期事件 ============
class RunStartedEvent(BaseEvent):
    type: Literal[EventType.RUN_STARTED] = EventType.RUN_STARTED
    thread_id: str
    run_id: str

class RunFinishedEvent(BaseEvent):
    type: Literal[EventType.RUN_FINISHED] = EventType.RUN_FINISHED
    thread_id: str
    run_id: str
    result: Optional[Any] = None

class RunErrorEvent(BaseEvent):
    type: Literal[EventType.RUN_ERROR] = EventType.RUN_ERROR
    message: str
    code: Optional[str] = None

# ============ 文本消息事件 ============
class TextMessageChunkEvent(BaseEvent):
    type: Literal[EventType.TEXT_MESSAGE_CHUNK] = EventType.TEXT_MESSAGE_CHUNK
    message_id: Optional[str] = None
    role: Optional[Literal["assistant"]] = "assistant"
    delta: Optional[str] = None

# ============ 工具调用事件 ============
class ToolCallChunkEvent(BaseEvent):
    type: Literal[EventType.TOOL_CALL_CHUNK] = EventType.TOOL_CALL_CHUNK
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None
    parent_message_id: Optional[str] = None
    delta: Optional[str] = None

# ============ 消息类型 ============
Role = Literal["user", "assistant", "system", "tool", "developer"]

class UserMessage(BaseModel):
    id: str
    role: Literal["user"] = "user"
    content: str

class AssistantMessage(BaseModel):
    id: str
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None

class ToolMessage(BaseModel):
    id: str
    role: Literal["tool"] = "tool"
    content: str
    tool_call_id: str

class SystemMessage(BaseModel):
    id: str
    role: Literal["system"] = "system"
    content: str

Message = Union[UserMessage, AssistantMessage, ToolMessage, SystemMessage]

# ============ 工具定义 ============
class Tool(BaseModel):
    name: str
    description: str
    parameters: Any  # JSON Schema

class Context(BaseModel):
    description: str
    value: str

# ============ Agent输入 ============
class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    tools: List[Tool]
    state: Any
    context: List[Context]
    forwarded_props: Optional[Any] = None
```

### 3.3 实现行程规划Agent（Python）

创建 `app/services/llm/agents/trip_planner_agent.py`:

```python
from typing import AsyncGenerator
import uuid
from app.schemas.agui import (
    BaseEvent,
    RunAgentInput,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageChunkEvent,
    ToolCallChunkEvent,
)

class TripPlannerAgent:
    """行程规划Agent（AG-UI协议实现）"""
    
    def __init__(self):
        self.agent_id = "trip-planner"
        self.thread_id = "default"
    
    async def run(self, input_data: RunAgentInput) -> AsyncGenerator[BaseEvent, None]:
        """
        运行Agent并生成AG-UI事件流
        
        Args:
            input_data: RunAgentInput包含messages, tools, state等
            
        Yields:
            BaseEvent: AG-UI标准事件
        """
        try:
            # 1. 发出RUN_STARTED事件
            yield RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
            
            # 2. 准备系统提示词
            system_prompt = self._build_system_prompt(input_data.tools)
            
            # 3. 调用LLM（这里需要集成阿里云API）
            message_id = f"msg_{uuid.uuid4()}"
            
            # 4. 流式发出文本消息事件
            # 示例：模拟LLM响应
            response_text = "我将为您规划一个精彩的旅行行程..."
            
            for chunk in response_text.split():
                yield TextMessageChunkEvent(
                    type=EventType.TEXT_MESSAGE_CHUNK,
                    message_id=message_id,
                    role="assistant",
                    delta=chunk + " "
                )
            
            # 5. 如果需要调用工具
            if input_data.tools:
                tool_call_id = f"tool_{uuid.uuid4()}"
                yield ToolCallChunkEvent(
                    type=EventType.TOOL_CALL_CHUNK,
                    tool_call_id=tool_call_id,
                    tool_call_name="searchPOI",
                    parent_message_id=message_id,
                    delta='{"keyword":"东京塔","city":"东京"}'
                )
            
            # 6. 发出RUN_FINISHED事件
            yield RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
            
        except Exception as error:
            yield RunErrorEvent(
                type=EventType.RUN_ERROR,
                message=str(error)
            )
    
    def _build_system_prompt(self, tools: list) -> str:
        """构建系统提示词"""
        tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in tools])
        return f"""你是一个专业的旅行规划师AI助手。

可用工具：
{tools_desc}

请使用工具搜索真实的POI信息，确保推荐的地点真实可靠。"""
```

### 3.4 实现SSE端点（FastAPI）

创建 `app/api/v1/endpoints/agent.py`:

```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.schemas.agui import RunAgentInput, BaseEvent
from app.services.llm.agents.trip_planner_agent import TripPlannerAgent
import json

router = APIRouter()

@router.post("/trip-planner")
async def trip_planner_agent(request: Request, input_data: RunAgentInput):
    """
    行程规划Agent端点（AG-UI协议）
    
    接受RunAgentInput，返回SSE事件流
    """
    # 验证Accept头
    accept_header = request.headers.get("accept", "")
    if "text/event-stream" not in accept_header:
        return {"error": "Accept header must include text/event-stream"}
    
    # 创建Agent实例
    agent = TripPlannerAgent()
    
    async def event_generator():
        """SSE事件生成器"""
        async for event in agent.run(input_data):
            # 转换为SSE格式
            # 将Pydantic模型转为dict，使用snake_case
            event_dict = event.model_dump(by_alias=True)
            event_json = json.dumps(event_dict)
            
            # SSE格式: data: {json}\n\n
            yield f"data: {event_json}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        }
    )
```

---

## 四、前端实现（React + TypeScript）

### 4.1 依赖安装

```bash
cd frontend

# RxJS用于Observable
npm install rxjs

# EventSource polyfill（可选，现代浏览器原生支持）
npm install eventsource
```

### 4.2 AG-UI类型定义（前端）

创建 `src/modules/llm/types/agui.types.ts`:

```typescript
// 复用与后端相同的类型定义
// 可以考虑将类型定义放在共享包中

export enum EventType {
  RUN_STARTED = 'RUN_STARTED',
  RUN_FINISHED = 'RUN_FINISHED',
  TEXT_MESSAGE_CHUNK = 'TEXT_MESSAGE_CHUNK',
  TOOL_CALL_CHUNK = 'TOOL_CALL_CHUNK',
  // ... 其他事件类型
}

export interface BaseEvent {
  type: EventType;
  timestamp?: number;
}

export interface TextMessageChunkEvent extends BaseEvent {
  type: EventType.TEXT_MESSAGE_CHUNK;
  messageId?: string;
  delta?: string;
}

// ... 其他事件类型定义
```

### 4.3 实现SSE客户端

创建 `src/modules/llm/services/sse-client.service.ts`:

```typescript
import { Observable } from 'rxjs';
import { BaseEvent, EventType } from '../types/agui.types';

export class SSEClientService {
  /**
   * 连接到AG-UI Agent端点并接收事件流
   */
  connect(url: string, input: any): Observable<BaseEvent> {
    return new Observable<BaseEvent>((observer) => {
      // 创建EventSource连接
      const eventSource = new EventSource(url);
      
      eventSource.onmessage = (event) => {
        try {
          // 解析SSE数据
          const data = JSON.parse(event.data);
          
          // 转换snake_case为camelCase
          const parsedEvent = this.snakeToCamel(data) as BaseEvent;
          
          // 发送到订阅者
          observer.next(parsedEvent);
          
          // 检查是否结束
          if (
            parsedEvent.type === EventType.RUN_FINISHED ||
            parsedEvent.type === EventType.RUN_ERROR
          ) {
            observer.complete();
            eventSource.close();
          }
        } catch (error) {
          console.error('Failed to parse SSE event:', error);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        observer.error(error);
        eventSource.close();
      };
      
      // 发送POST请求到端点
      this.sendRequest(url, input);
      
      // 清理函数
      return () => {
        eventSource.close();
      };
    });
  }
  
  private async sendRequest(url: string, input: any): Promise<void> {
    // 注意：EventSource不支持POST请求
    // 需要使用fetch API配合EventSource
    // 或者考虑使用fetch-event-source库
  }
  
  private snakeToCamel(obj: any): any {
    if (obj === null || typeof obj !== 'object') {
      return obj;
    }
    
    if (Array.isArray(obj)) {
      return obj.map(item => this.snakeToCamel(item));
    }
    
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = this.snakeToCamel(value);
    }
    return result;
  }
}
```

**注意**: 原生EventSource不支持POST请求，有两种解决方案：

1. **使用fetch-event-source库**（推荐）:
```bash
npm install @microsoft/fetch-event-source
```

2. **使用GET请求** + URL参数（不推荐，安全性较低）

### 4.4 更好的SSE客户端实现

```bash
npm install @microsoft/fetch-event-source
```

创建 `src/modules/llm/services/agui-client.service.ts`:

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { BaseEvent, RunAgentInput, EventType } from '../types/agui.types';

export class AguiClientService {
  private baseURL: string;
  
  constructor(baseURL: string = '/api/v1/agent') {
    this.baseURL = baseURL;
  }
  
  /**
   * 运行Agent并订阅事件流
   */
  async runAgent(
    agentName: string,
    input: RunAgentInput,
    handlers: {
      onEvent?: (event: BaseEvent) => void;
      onTextMessage?: (delta: string) => void;
      onToolCall?: (toolCall: any) => void;
      onStateUpdate?: (state: any) => void;
      onComplete?: () => void;
      onError?: (error: Error) => void;
    }
  ): Promise<void> {
    const url = `${this.baseURL}/${agentName}`;
    const token = localStorage.getItem('token');
    
    await fetchEventSource(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(input),
      
      onmessage: (event) => {
        try {
          const parsedEvent = JSON.parse(event.data) as BaseEvent;
          
          // 调用通用事件处理器
          handlers.onEvent?.(parsedEvent);
          
          // 根据事件类型调用特定处理器
          switch (parsedEvent.type) {
            case EventType.TEXT_MESSAGE_CHUNK:
              const textEvent = parsedEvent as any;
              handlers.onTextMessage?.(textEvent.delta);
              break;
              
            case EventType.TOOL_CALL_CHUNK:
              handlers.onToolCall?.(parsedEvent);
              break;
              
            case EventType.STATE_DELTA:
            case EventType.STATE_SNAPSHOT:
              const stateEvent = parsedEvent as any;
              handlers.onStateUpdate?.(stateEvent.snapshot || stateEvent.delta);
              break;
              
            case EventType.RUN_FINISHED:
              handlers.onComplete?.();
              break;
              
            case EventType.RUN_ERROR:
              const errorEvent = parsedEvent as any;
              handlers.onError?.(new Error(errorEvent.message));
              break;
          }
        } catch (error) {
          console.error('Failed to parse event:', error);
        }
      },
      
      onerror: (error) => {
        handlers.onError?.(error as Error);
        throw error; // 停止连接
      },
    });
  }
}
```

### 4.5 实现React Hook

创建 `src/modules/llm/hooks/useTripPlanner.ts`:

```typescript
import { useState, useCallback, useRef } from 'react';
import { AguiClientService } from '../services/agui-client.service';
import { RunAgentInput, Message, Tool } from '../types/agui.types';

export function useTripPlanner() {
  const [isPlanning, setIsPlanning] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [error, setError] = useState<Error | null>(null);
  const [agentState, setAgentState] = useState<any>({});
  
  const aguiClient = useRef(new AguiClientService());
  
  const planTrip = useCallback(async (
    userMessage: string,
    tools: Tool[]
  ) => {
    setIsPlanning(true);
    setStreamingText('');
    setError(null);
    
    const input: RunAgentInput = {
      threadId: `thread_${Date.now()}`,
      runId: `run_${Date.now()}`,
      messages: [
        {
          id: `msg_${Date.now()}`,
          role: 'user',
          content: userMessage,
        } as Message,
      ],
      tools,
      state: agentState,
      context: [],
    };
    
    try {
      await aguiClient.current.runAgent('trip-planner', input, {
        onTextMessage: (delta) => {
          setStreamingText((prev) => prev + delta);
        },
        
        onStateUpdate: (state) => {
          setAgentState(state);
        },
        
        onToolCall: (toolCall) => {
          console.log('Tool call:', toolCall);
          // 这里可以执行工具并返回结果
        },
        
        onComplete: () => {
          setIsPlanning(false);
        },
        
        onError: (err) => {
          setError(err);
          setIsPlanning(false);
        },
      });
    } catch (err: any) {
      setError(err);
      setIsPlanning(false);
    }
  }, [agentState]);
  
  return {
    planTrip,
    isPlanning,
    streamingText,
    error,
    agentState,
  };
}
```

### 4.6 使用示例（React组件）

```typescript
import { useTripPlanner } from '@modules/llm/hooks/useTripPlanner';
import { Tool } from '@modules/llm/types/agui.types';

function TripPlanningPage() {
  const { planTrip, isPlanning, streamingText, error } = useTripPlanner();
  
  // 定义前端工具
  const tools: Tool[] = [
    {
      name: 'searchPOI',
      description: '搜索景点、餐厅、酒店等POI',
      parameters: {
        type: 'object',
        properties: {
          keyword: { type: 'string', description: '搜索关键词' },
          city: { type: 'string', description: '城市名称' },
          type: { 
            type: 'string', 
            enum: ['景点', '餐厅', '酒店'],
            description: 'POI类型' 
          },
        },
        required: ['keyword', 'city'],
      },
    },
  ];
  
  const handleSubmit = async (userInput: string) => {
    await planTrip(userInput, tools);
  };
  
  return (
    <div>
      <h1>行程规划</h1>
      
      {isPlanning && (
        <div className="loading">
          <p>AI正在规划中...</p>
          <div className="streaming-text">
            {streamingText}
          </div>
        </div>
      )}
      
      {error && (
        <div className="error">错误: {error.message}</div>
      )}
      
      <button onClick={() => handleSubmit('帮我规划5天的东京之旅')}>
        开始规划
      </button>
    </div>
  );
}
```

---

## 五、AG-UI工具系统实现

### 5.1 前端工具定义

工具是在前端定义的，Agent通过TOOL_CALL事件请求调用，前端执行后返回结果。

创建 `src/modules/llm/tools/tool-registry.ts`:

```typescript
import { Tool } from '../types/agui.types';

/**
 * POI搜索工具
 */
export const searchPOITool: Tool = {
  name: 'searchPOI',
  description: '搜索指定城市的景点、餐厅、酒店等POI信息',
  parameters: {
    type: 'object',
    properties: {
      keyword: {
        type: 'string',
        description: '搜索关键词，如"东京塔"、"寿司店"等',
      },
      city: {
        type: 'string',
        description: '城市名称，如"东京"、"北京"等',
      },
      type: {
        type: 'string',
        enum: ['景点', '餐厅', '酒店', '交通'],
        description: 'POI类型',
      },
      limit: {
        type: 'number',
        description: '返回结果数量限制',
        default: 10,
      },
    },
    required: ['keyword', 'city'],
  },
};

/**
 * 路线计算工具
 */
export const calculateRouteTool: Tool = {
  name: 'calculateRoute',
  description: '计算两个地点之间的路线，支持多种交通方式',
  parameters: {
    type: 'object',
    properties: {
      origin: {
        type: 'string',
        description: '起点地址或POI名称',
      },
      destination: {
        type: 'string',
        description: '终点地址或POI名称',
      },
      mode: {
        type: 'string',
        enum: ['driving', 'transit', 'walking'],
        description: '交通方式：驾车、公交、步行',
        default: 'transit',
      },
    },
    required: ['origin', 'destination'],
  },
};

/**
 * 价格查询工具
 */
export const queryPriceTool: Tool = {
  name: 'queryPrice',
  description: '查询景点门票、餐厅人均、酒店价格等费用信息',
  parameters: {
    type: 'object',
    properties: {
      poiName: {
        type: 'string',
        description: 'POI名称',
      },
      priceType: {
        type: 'string',
        enum: ['门票', '人均消费', '房价'],
        description: '价格类型',
      },
    },
    required: ['poiName', 'priceType'],
  },
};

/**
 * 所有可用工具
 */
export const allTools: Tool[] = [
  searchPOITool,
  calculateRouteTool,
  queryPriceTool,
];
```

### 5.2 工具执行器

创建 `src/modules/llm/tools/tool-executor.ts`:

```typescript
import { mapService } from '@modules/map/services/baidu-map.service';

/**
 * 工具执行器
 * 当Agent请求调用工具时，前端执行工具并返回结果
 */
export class ToolExecutor {
  /**
   * 执行工具调用
   */
  async execute(toolName: string, args: any): Promise<string> {
    switch (toolName) {
      case 'searchPOI':
        return await this.executeSearchPOI(args);
        
      case 'calculateRoute':
        return await this.executeCalculateRoute(args);
        
      case 'queryPrice':
        return await this.executeQueryPrice(args);
        
      default:
        throw new Error(`Unknown tool: ${toolName}`);
    }
  }
  
  private async executeSearchPOI(args: {
    keyword: string;
    city: string;
    type?: string;
    limit?: number;
  }): Promise<string> {
    try {
      const results = await mapService.searchPOI(
        args.keyword,
        args.city,
        args.type,
        args.limit || 10
      );
      
      return JSON.stringify({
        success: true,
        data: results.map(poi => ({
          name: poi.name,
          address: poi.address,
          location: poi.location,
          rating: poi.rating,
          price: poi.price,
        })),
      });
    } catch (error: any) {
      return JSON.stringify({
        success: false,
        error: error.message,
      });
    }
  }
  
  private async executeCalculateRoute(args: {
    origin: string;
    destination: string;
    mode?: string;
  }): Promise<string> {
    try {
      const route = await mapService.calculateRoute(
        args.origin,
        args.destination,
        args.mode || 'transit'
      );
      
      return JSON.stringify({
        success: true,
        data: {
          distance: route.distance,
          duration: route.duration,
          steps: route.steps,
        },
      });
    } catch (error: any) {
      return JSON.stringify({
        success: false,
        error: error.message,
      });
    }
  }
  
  private async executeQueryPrice(args: {
    poiName: string;
    priceType: string;
  }): Promise<string> {
    // 这里可以调用价格查询API或返回估算值
    return JSON.stringify({
      success: true,
      data: {
        poi: args.poiName,
        type: args.priceType,
        price: 100, // 示例价格
        currency: 'CNY',
      },
    });
  }
}
```

---

## 六、AG-UI事件处理完整示例

### 6.1 事件订阅器（AgentSubscriber）

创建 `src/modules/llm/subscribers/message.subscriber.ts`:

```typescript
import { BaseEvent, EventType } from '../types/agui.types';

export class MessageSubscriber {
  private messageBuffer: Map<string, string> = new Map();
  private onUpdate: (message: string) => void;
  
  constructor(onUpdate: (message: string) => void) {
    this.onUpdate = onUpdate;
  }
  
  handleEvent(event: BaseEvent): void {
    switch (event.type) {
      case EventType.TEXT_MESSAGE_START:
        const startEvent = event as any;
        this.messageBuffer.set(startEvent.messageId, '');
        break;
        
      case EventType.TEXT_MESSAGE_CONTENT:
        const contentEvent = event as any;
        const current = this.messageBuffer.get(contentEvent.messageId) || '';
        const updated = current + contentEvent.delta;
        this.messageBuffer.set(contentEvent.messageId, updated);
        this.onUpdate(updated);
        break;
        
      case EventType.TEXT_MESSAGE_END:
        const endEvent = event as any;
        const final = this.messageBuffer.get(endEvent.messageId) || '';
        this.onUpdate(final);
        break;
        
      case EventType.TEXT_MESSAGE_CHUNK:
        const chunkEvent = event as any;
        if (chunkEvent.delta) {
          const messageId = chunkEvent.messageId || 'default';
          const curr = this.messageBuffer.get(messageId) || '';
          const upd = curr + chunkEvent.delta;
          this.messageBuffer.set(messageId, upd);
          this.onUpdate(upd);
        }
        break;
    }
  }
}
```

### 6.2 完整的Hook实现

```typescript
import { useState, useCallback, useRef, useEffect } from 'react';
import { AguiClientService } from '../services/agui-client.service';
import { MessageSubscriber } from '../subscribers/message.subscriber';
import { ToolExecutor } from '../tools/tool-executor';
import { allTools } from '../tools/tool-registry';
import { RunAgentInput } from '../types/agui.types';

export function useAguiAgent(agentName: string) {
  const [isRunning, setIsRunning] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [toolCalls, setToolCalls] = useState<any[]>([]);
  const [error, setError] = useState<Error | null>(null);
  
  const clientRef = useRef(new AguiClientService());
  const toolExecutorRef = useRef(new ToolExecutor());
  const messageSubscriberRef = useRef(
    new MessageSubscriber((text) => setStreamingText(text))
  );
  
  const runAgent = useCallback(async (userMessage: string) => {
    setIsRunning(true);
    setStreamingText('');
    setToolCalls([]);
    setError(null);
    
    const input: RunAgentInput = {
      threadId: `thread_${Date.now()}`,
      runId: `run_${Date.now()}`,
      messages: [
        {
          id: `msg_${Date.now()}`,
          role: 'user',
          content: userMessage,
        },
      ],
      tools: allTools, // 传递前端工具定义
      state: {},
      context: [],
    };
    
    try {
      await clientRef.current.runAgent(agentName, input, {
        onEvent: (event) => {
          messageSubscriberRef.current.handleEvent(event);
        },
        
        onToolCall: async (toolCall) => {
          // 记录工具调用
          setToolCalls((prev) => [...prev, toolCall]);
          
          // 如果工具调用完成，执行工具
          if (toolCall.type === 'TOOL_CALL_END') {
            // TODO: 执行工具并将结果发送回Agent
          }
        },
        
        onComplete: () => {
          setIsRunning(false);
        },
        
        onError: (err) => {
          setError(err);
          setIsRunning(false);
        },
      });
    } catch (err: any) {
      setError(err);
      setIsRunning(false);
    }
  }, [agentName]);
  
  return {
    runAgent,
    isRunning,
    streamingText,
    toolCalls,
    error,
  };
}
```

---

## 七、关键实现要点

### 7.1 事件顺序规范

AG-UI协议要求事件必须按照特定顺序发出：

```typescript
// ✅ 正确的事件顺序
1. RUN_STARTED
2. TEXT_MESSAGE_START (messageId: "msg1")
3. TEXT_MESSAGE_CONTENT (messageId: "msg1", delta: "Hello")
4. TEXT_MESSAGE_CONTENT (messageId: "msg1", delta: " world")
5. TEXT_MESSAGE_END (messageId: "msg1")
6. RUN_FINISHED

// 或使用便捷事件（自动处理start/end）
1. RUN_STARTED
2. TEXT_MESSAGE_CHUNK (messageId: "msg1", delta: "Hello")
3. TEXT_MESSAGE_CHUNK (messageId: "msg1", delta: " world")
4. TEXT_MESSAGE_CHUNK (messageId: "msg1", delta: "") // 空delta关闭消息
5. RUN_FINISHED

// ❌ 错误：缺少RUN_STARTED
TEXT_MESSAGE_START
TEXT_MESSAGE_CONTENT
...

// ❌ 错误：messageId不匹配
TEXT_MESSAGE_START (messageId: "msg1")
TEXT_MESSAGE_CONTENT (messageId: "msg2") // 错误！
```

### 7.2 工具调用流程

```typescript
// Agent请求调用工具
1. TOOL_CALL_START (toolCallId: "tool1", toolCallName: "searchPOI")
2. TOOL_CALL_ARGS (toolCallId: "tool1", delta: '{"keyword"')
3. TOOL_CALL_ARGS (toolCallId: "tool1", delta: ':"东京塔"}')
4. TOOL_CALL_END (toolCallId: "tool1")

// 前端执行工具
→ 前端收到完整的工具调用信息
→ 解析参数：{ keyword: "东京塔" }
→ 执行工具：调用地图API搜索
→ 获得结果：[{name: "东京塔", address: "..."}]

// 前端发送工具结果（作为新的消息）
POST /api/v1/agent/trip-planner
Body: {
  messages: [
    ...之前的消息,
    {
      id: "result_1",
      role: "tool",
      content: JSON.stringify(searchResults),
      toolCallId: "tool1"
    }
  ]
}

// Agent继续处理并响应
5. TEXT_MESSAGE_START (messageId: "msg2")
6. TEXT_MESSAGE_CONTENT (messageId: "msg2", delta: "根据搜索结果...")
7. TEXT_MESSAGE_END (messageId: "msg2")
8. RUN_FINISHED
```

### 7.3 状态同步

```typescript
// Agent更新状态（增量更新）
STATE_DELTA {
  delta: [
    { op: "add", path: "/currentDay", value: 1 },
    { op: "replace", path: "/progress", value: 0.2 }
  ]
}

// 前端应用状态更新
const newState = applyJsonPatch(currentState, delta);

// 或完整快照
STATE_SNAPSHOT {
  snapshot: {
    currentDay: 1,
    progress: 0.2,
    plannedPOIs: [...]
  }
}
```

---

## 八、测试与调试

### 8.1 测试AG-UI端点

```bash
# 测试基本连接
curl -N -X POST http://localhost:3000/api/v1/agent/trip-planner \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "threadId": "test-thread",
    "runId": "test-run",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "你好"
      }
    ],
    "tools": [],
    "state": {},
    "context": []
  }'

# 预期输出（SSE格式）:
data: {"type":"RUN_STARTED","thread_id":"test-thread","run_id":"test-run"}

data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"msg_123","delta":"你好！"}

data: {"type":"RUN_FINISHED","thread_id":"test-thread","run_id":"test-run"}
```

### 8.2 验证事件格式

创建测试文件 `backend/tests/unit/agui-events.test.ts`:

```typescript
import { EventEncoder } from '../src/services/llm/events/event-encoder';
import { EventType } from '../src/services/llm/types/agui.types';

describe('AG-UI Event Encoder', () => {
  let encoder: EventEncoder;
  
  beforeEach(() => {
    encoder = new EventEncoder();
  });
  
  test('should encode RUN_STARTED event', () => {
    const event = {
      type: EventType.RUN_STARTED,
      threadId: 'thread-1',
      runId: 'run-1',
    };
    
    const encoded = encoder.encode(event);
    expect(encoded).toContain('data: ');
    expect(encoded).toContain('"type":"RUN_STARTED"');
    expect(encoded).toContain('"thread_id":"thread-1"');
  });
  
  test('should encode TEXT_MESSAGE_CHUNK event', () => {
    const event = {
      type: EventType.TEXT_MESSAGE_CHUNK,
      messageId: 'msg-1',
      delta: 'Hello',
    };
    
    const encoded = encoder.encode(event);
    expect(encoded).toContain('"delta":"Hello"');
  });
});
```

### 8.3 调试技巧

**1. 使用AG-UI Dojo**（如果可用）:
```bash
# Clone AG-UI repository
git clone https://github.com/ag-ui-protocol/ag-ui.git
cd ag-ui
pnpm install
turbo run dev

# 访问 http://localhost:3000
# 选择你的集成进行测试
```

**2. 浏览器DevTools**:
- Network标签查看SSE连接
- EventStream选项卡查看实时事件
- Console查看事件日志

**3. 日志所有事件**:
```typescript
aguiClient.runAgent('trip-planner', input, {
  onEvent: (event) => {
    console.log('AG-UI Event:', event.type, event);
  },
});
```

---

## 九、性能优化

### 9.1 事件批处理

```typescript
// 避免过于频繁的小事件
// ❌ 错误：每个字符一个事件
TEXT_MESSAGE_CONTENT (delta: "你")
TEXT_MESSAGE_CONTENT (delta: "好")

// ✅ 正确：合理的批处理
TEXT_MESSAGE_CONTENT (delta: "你好")
TEXT_MESSAGE_CONTENT (delta: "，我是AI助手")
```

### 9.2 使用Binary Protocol（高性能场景）

```typescript
// 后端支持Binary编码
if (req.get('Accept')?.includes('application/octet-stream')) {
  // 使用AG-UI Binary Protocol
  res.setHeader('Content-Type', 'application/octet-stream');
  // ... Binary编码逻辑
}
```

### 9.3 连接池管理

```typescript
// 限制并发Agent运行数
const MAX_CONCURRENT_RUNS = 10;
const activeRuns = new Map();

// 在endpoint中检查
if (activeRuns.size >= MAX_CONCURRENT_RUNS) {
  return res.status(503).json({
    error: 'Too many concurrent requests',
  });
}
```

---

## 十、常见问题

### Q1: EventSource不支持POST请求怎么办？

**A**: 使用 `@microsoft/fetch-event-source` 库：

```bash
npm install @microsoft/fetch-event-source
```

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource(url, {
  method: 'POST',
  headers: { ... },
  body: JSON.stringify(input),
  onmessage: (event) => {
    // 处理事件
  },
});
```

### Q2: 如何处理工具调用的异步执行？

**A**: 工具调用需要新的Agent run：

```typescript
// 1. 收到TOOL_CALL_END事件
// 2. 执行工具获得结果
const result = await toolExecutor.execute(toolName, args);

// 3. 创建新的RunAgentInput，添加ToolMessage
const newInput = {
  ...previousInput,
  messages: [
    ...previousInput.messages,
    {
      id: 'result_1',
      role: 'tool',
      content: result,
      toolCallId: toolCall.id,
    },
  ],
};

// 4. 重新运行Agent
await client.runAgent(agentName, newInput, handlers);
```

### Q3: 如何实现中断和恢复（Human-in-the-Loop）？

**A**: 使用RUN_FINISHED的interrupt机制（Draft提案）：

```typescript
// Agent请求人工确认
RUN_FINISHED {
  outcome: "interrupt",
  interrupt: {
    id: "approval-1",
    reason: "human_approval",
    payload: {
      action: "预订酒店",
      details: "价格: ¥800/晚"
    }
  }
}

// 用户确认后，使用resume继续
RunAgentInput {
  resume: {
    interruptId: "approval-1",
    payload: { approved: true }
  }
}
```

### Q4: 如何处理大量历史消息？

**A**: 只发送必要的消息：

```typescript
// 发送最近的N条消息即可
const input = {
  messages: allMessages.slice(-10), // 只发送最近10条
  ...
};
```

---

## 十一、最佳实践

### ✅ DO

1. **始终发出RUN_STARTED和RUN_FINISHED** - 这是强制要求
2. **使用便捷事件** - TEXT_MESSAGE_CHUNK比START+CONTENT+END更简单
3. **提供详细的工具描述** - 帮助LLM正确使用工具
4. **验证工具参数** - 使用JSON Schema验证
5. **处理错误** - 发出RUN_ERROR事件而不是让请求失败
6. **记录所有事件** - 便于调试和审计

### ❌ DON'T

1. **不要跳过生命周期事件** - 必须有RUN_STARTED/FINISHED
2. **不要发送空delta** - TEXT_MESSAGE_CONTENT的delta必须非空（除非是CHUNK）
3. **不要混淆messageId** - 同一消息的所有事件必须使用相同的messageId
4. **不要阻塞事件流** - 快速发出事件，不要等待耗时操作
5. **不要在工具中调用Agent** - 避免循环依赖

---

## 十二、与其他协议的比较

| 特性 | AG-UI | MCP | A2A |
|-----|-------|-----|-----|
| **用途** | Agent↔UI通信 | Agent↔工具/数据 | Agent↔Agent |
| **方向** | 双向（Human-in-Loop） | 单向（Agent调用） | 双向（协作） |
| **流式** | ✅ 实时流式 | ❌ 请求响应 | ✅ 支持 |
| **状态** | ✅ 共享状态 | ❌ 无状态 | ✅ 状态传递 |
| **工具** | 前端定义 | 服务器定义 | Agent定义 |

**在本项目中**:
- **AG-UI**: 前端与行程规划Agent通信
- **MCP**: （可选）Agent连接外部数据源
- **A2A**: （可选）多Agent协作

---

## 十三、参考资源

### 官方文档
- **AG-UI官网**: https://docs.ag-ui.com/
- **GitHub仓库**: https://github.com/ag-ui-protocol/ag-ui
- **规范文档**: https://docs.ag-ui.com/concepts/events

### 相关协议
- **MCP（Model Context Protocol）**: Agent↔工具/上下文
- **A2A（Agent-to-Agent）**: Agent之间通信

### 学习资源
- **AG-UI Dojo**: 交互式示例和测试环境
- **CopilotKit**: AG-UI的生产级实现参考
- **LangGraph + AG-UI**: Python集成示例

### 本项目文档
- **AG-UI协议完整文档**: `doc/AG-UI.txt`
- **技术设计文档**: `doc/TECHNICAL_DESIGN.md`
- **项目结构说明**: `doc/PROJECT_STRUCTURE.md`

---

**文档版本**: v1.0  
**创建日期**: 2025-10-17  
**最后更新**: 2025-10-17

