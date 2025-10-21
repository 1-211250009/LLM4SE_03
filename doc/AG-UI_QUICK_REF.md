# AG-UI协议快速参考

## 📋 AG-UI事件类型速查表

### 生命周期事件（Lifecycle Events）

| 事件类型 | 说明 | 必需 | 字段 |
|---------|------|------|------|
| `RUN_STARTED` | Agent运行开始 | ✅ 必需 | `threadId`, `runId` |
| `RUN_FINISHED` | Agent运行成功结束 | ✅ 必需 | `threadId`, `runId`, `result?` |
| `RUN_ERROR` | Agent运行出错 | ⚠️ 错误时 | `message`, `code?` |
| `STEP_STARTED` | 步骤开始 | ❌ 可选 | `stepName` |
| `STEP_FINISHED` | 步骤结束 | ❌ 可选 | `stepName` |

### 文本消息事件（Text Message Events）

| 事件类型 | 说明 | 使用场景 | 字段 |
|---------|------|----------|------|
| `TEXT_MESSAGE_START` | 消息开始 | 显式控制 | `messageId`, `role` |
| `TEXT_MESSAGE_CONTENT` | 消息内容块 | 流式内容 | `messageId`, `delta` |
| `TEXT_MESSAGE_END` | 消息结束 | 显式控制 | `messageId` |
| `TEXT_MESSAGE_CHUNK` | 消息块（便捷） | ⭐ 推荐 | `messageId?`, `role?`, `delta?` |

**推荐使用**: `TEXT_MESSAGE_CHUNK` - 自动处理start/end

### 工具调用事件（Tool Call Events）

| 事件类型 | 说明 | 字段 |
|---------|------|------|
| `TOOL_CALL_START` | 工具调用开始 | `toolCallId`, `toolCallName`, `parentMessageId?` |
| `TOOL_CALL_ARGS` | 工具参数块 | `toolCallId`, `delta` |
| `TOOL_CALL_END` | 工具调用结束 | `toolCallId` |
| `TOOL_CALL_RESULT` | 工具执行结果 | `messageId`, `toolCallId`, `content`, `role?` |
| `TOOL_CALL_CHUNK` | 工具调用块（便捷） | `toolCallId?`, `toolCallName?`, `delta?` |

### 状态管理事件（State Management Events）

| 事件类型 | 说明 | 使用场景 | 字段 |
|---------|------|----------|------|
| `STATE_SNAPSHOT` | 完整状态快照 | 初始化、重置 | `snapshot` |
| `STATE_DELTA` | 增量状态更新 | ⭐ 推荐 | `delta` (JSON Patch) |
| `MESSAGES_SNAPSHOT` | 消息历史快照 | 同步历史 | `messages` |

### 特殊事件（Special Events）

| 事件类型 | 说明 | 字段 |
|---------|------|------|
| `RAW` | 原始事件透传 | `event`, `source?` |
| `CUSTOM` | 自定义事件 | `name`, `value` |

---

## 🔄 标准事件流程

### 最小事件流（Hello World）

```
RUN_STARTED
  ↓
TEXT_MESSAGE_CHUNK (delta: "Hello world!")
  ↓
RUN_FINISHED
```

### 完整对话流程

```
RUN_STARTED (threadId, runId)
  ↓
TEXT_MESSAGE_START (messageId: "msg1", role: "assistant")
  ↓
TEXT_MESSAGE_CONTENT (messageId: "msg1", delta: "你好")
TEXT_MESSAGE_CONTENT (messageId: "msg1", delta: "！")
  ↓
TEXT_MESSAGE_END (messageId: "msg1")
  ↓
RUN_FINISHED (threadId, runId)
```

### 带工具调用的流程

```
RUN_STARTED
  ↓
TOOL_CALL_START (toolCallId: "tc1", toolCallName: "searchPOI")
  ↓
TOOL_CALL_ARGS (toolCallId: "tc1", delta: '{"keyword"')
TOOL_CALL_ARGS (toolCallId: "tc1", delta: ':"东京塔"}')
  ↓
TOOL_CALL_END (toolCallId: "tc1")
  ↓
【前端执行工具，发送ToolMessage】
  ↓
【新的Agent run，处理工具结果】
  ↓
TEXT_MESSAGE_CHUNK (delta: "根据搜索结果...")
  ↓
RUN_FINISHED
```

### 带状态更新的流程

```
RUN_STARTED
  ↓
STATE_SNAPSHOT (snapshot: { currentStep: "planning" })
  ↓
TEXT_MESSAGE_CHUNK (delta: "正在规划...")
  ↓
STATE_DELTA (delta: [{ op: "replace", path: "/currentStep", value: "searching" }])
  ↓
TEXT_MESSAGE_CHUNK (delta: "正在搜索景点...")
  ↓
RUN_FINISHED
```

---

## 📝 RunAgentInput结构

```typescript
{
  threadId: string;        // 会话线程ID
  runId: string;           // 本次运行ID
  messages: Message[];     // 消息历史
  tools: Tool[];           // 可用工具列表
  state: any;              // 当前状态
  context: Context[];      // 上下文信息
  forwardedProps?: any;    // 转发属性
}
```

### Message类型

```typescript
// 用户消息
{
  id: string;
  role: "user";
  content: string;
}

// 助手消息
{
  id: string;
  role: "assistant";
  content?: string;
  toolCalls?: ToolCall[];
}

// 工具结果消息
{
  id: string;
  role: "tool";
  content: string;
  toolCallId: string;
}

// 系统消息
{
  id: string;
  role: "system";
  content: string;
}
```

### Tool定义

```typescript
{
  name: string;           // 工具名称
  description: string;    // 工具描述（LLM使用）
  parameters: {           // JSON Schema
    type: "object";
    properties: { ... };
    required: string[];
  }
}
```

---

## 🔧 工具调用流程

### 1. 前端定义工具

```typescript
const searchPOITool = {
  name: 'searchPOI',
  description: '搜索景点、餐厅、酒店',
  parameters: {
    type: 'object',
    properties: {
      keyword: { type: 'string', description: '搜索关键词' },
      city: { type: 'string', description: '城市名称' },
    },
    required: ['keyword', 'city'],
  },
};
```

### 2. 发送到Agent

```typescript
const input: RunAgentInput = {
  threadId: 'thread-1',
  runId: 'run-1',
  messages: [{ id: 'msg-1', role: 'user', content: '推荐东京景点' }],
  tools: [searchPOITool], // ← 传递工具定义
  state: {},
  context: [],
};

POST /api/v1/agent/trip-planner
Body: input
```

### 3. Agent请求调用工具

```
Agent发出:
TOOL_CALL_START (toolCallId: "tc1", toolCallName: "searchPOI")
TOOL_CALL_ARGS (toolCallId: "tc1", delta: '{"keyword":"东京塔","city":"东京"}')
TOOL_CALL_END (toolCallId: "tc1")
```

### 4. 前端执行工具

```typescript
// 监听TOOL_CALL_END事件
onToolCallEnd: async ({ toolCallName, toolCallArgs }) => {
  // 执行工具
  const result = await executeSearchPOI(toolCallArgs);
  
  // 构造ToolMessage
  const toolMessage = {
    id: 'result-1',
    role: 'tool',
    content: JSON.stringify(result),
    toolCallId: 'tc1',
  };
  
  // 发送新的RunAgentInput，包含工具结果
  const newInput = {
    ...previousInput,
    messages: [...previousInput.messages, toolMessage],
  };
  
  // 重新运行Agent
  await runAgent(newInput);
}
```

### 5. Agent处理工具结果

```
Agent收到ToolMessage，继续生成响应:
TEXT_MESSAGE_CHUNK (delta: "根据搜索结果，推荐以下景点：...")
```

---

## 🌊 SSE格式示例

### 请求

```http
POST /api/v1/agent/trip-planner HTTP/1.1
Host: localhost:3000
Content-Type: application/json
Accept: text/event-stream
Authorization: Bearer <token>

{
  "threadId": "thread-123",
  "runId": "run-456",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "帮我规划东京3日游"
    }
  ],
  "tools": [],
  "state": {},
  "context": []
}
```

### 响应（SSE流）

```
data: {"type":"RUN_STARTED","thread_id":"thread-123","run_id":"run-456"}

data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"msg_789","role":"assistant","delta":"好的"}

data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"msg_789","delta":"，我将为您"}

data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"msg_789","delta":"规划一个"}

data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"msg_789","delta":"精彩的东京3日游行程"}

data: {"type":"STATE_DELTA","delta":[{"op":"add","path":"/progress","value":0.3}]}

data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"msg_789","delta":""}

data: {"type":"RUN_FINISHED","thread_id":"thread-123","run_id":"run-456"}
```

**注意**: 
- 每个事件以 `data: ` 开头
- 事件之间用空行分隔
- 字段名使用snake_case（thread_id, message_id等）

---

## ⚠️ 常见错误

### ❌ 错误1: 缺少生命周期事件

```typescript
// ❌ 错误：没有RUN_STARTED
TEXT_MESSAGE_CHUNK (...)
RUN_FINISHED

// ✅ 正确：必须有RUN_STARTED和RUN_FINISHED
RUN_STARTED
TEXT_MESSAGE_CHUNK (...)
RUN_FINISHED
```

### ❌ 错误2: messageId不一致

```typescript
// ❌ 错误
TEXT_MESSAGE_START (messageId: "msg1")
TEXT_MESSAGE_CONTENT (messageId: "msg2") // 错误！
TEXT_MESSAGE_END (messageId: "msg1")

// ✅ 正确
TEXT_MESSAGE_START (messageId: "msg1")
TEXT_MESSAGE_CONTENT (messageId: "msg1")
TEXT_MESSAGE_END (messageId: "msg1")
```

### ❌ 错误3: 空的delta

```typescript
// ❌ 错误：TEXT_MESSAGE_CONTENT的delta不能为空
TEXT_MESSAGE_CONTENT (messageId: "msg1", delta: "")

// ✅ 正确：使用空delta关闭CHUNK事件
TEXT_MESSAGE_CHUNK (messageId: "msg1", delta: "")
```

### ❌ 错误4: EventSource使用POST

```typescript
// ❌ 错误：原生EventSource不支持POST
const es = new EventSource('/api/agent');

// ✅ 正确：使用fetch-event-source
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource('/api/agent', {
  method: 'POST',
  body: JSON.stringify(input),
  ...
});
```

---

## 📊 JSON Patch操作（STATE_DELTA）

### 基本操作

```typescript
// add - 添加属性
{ op: "add", path: "/newProperty", value: "value" }

// replace - 替换值
{ op: "replace", path: "/existingProperty", value: "newValue" }

// remove - 删除属性
{ op: "remove", path: "/propertyToDelete" }

// move - 移动值
{ op: "move", path: "/destination", from: "/source" }

// copy - 复制值
{ op: "copy", path: "/destination", from: "/source" }

// test - 测试值（验证）
{ op: "test", path: "/property", value: "expectedValue" }
```

### 示例

```typescript
// 当前状态
{
  "currentDay": 1,
  "progress": 0.2,
  "pois": ["东京塔"]
}

// 应用Delta
STATE_DELTA {
  delta: [
    { op: "replace", path: "/currentDay", value: 2 },
    { op: "replace", path: "/progress", value: 0.4 },
    { op: "add", path: "/pois/-", value: "浅草寺" }
  ]
}

// 结果状态
{
  "currentDay": 2,
  "progress": 0.4,
  "pois": ["东京塔", "浅草寺"]
}
```

---

## 🎯 使用指南

### 后端：发出事件

```typescript
import { Observable } from 'rxjs';

run(input: RunAgentInput): Observable<BaseEvent> {
  return new Observable<BaseEvent>((observer) => {
    // 1. 开始
    observer.next({ type: 'RUN_STARTED', threadId: input.threadId, runId: input.runId });
    
    // 2. 内容（便捷事件）
    observer.next({ type: 'TEXT_MESSAGE_CHUNK', messageId: 'msg1', delta: 'Hello' });
    observer.next({ type: 'TEXT_MESSAGE_CHUNK', messageId: 'msg1', delta: ' World' });
    observer.next({ type: 'TEXT_MESSAGE_CHUNK', messageId: 'msg1', delta: '' }); // 关闭
    
    // 3. 结束
    observer.next({ type: 'RUN_FINISHED', threadId: input.threadId, runId: input.runId });
    observer.complete();
  });
}
```

### 前端：接收事件

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource('/api/v1/agent/trip-planner', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  },
  body: JSON.stringify(runAgentInput),
  
  onmessage: (event) => {
    const parsedEvent = JSON.parse(event.data);
    
    switch (parsedEvent.type) {
      case 'RUN_STARTED':
        console.log('Agent开始运行');
        break;
        
      case 'TEXT_MESSAGE_CHUNK':
        if (parsedEvent.delta) {
          appendToUI(parsedEvent.delta);
        }
        break;
        
      case 'TOOL_CALL_CHUNK':
        handleToolCall(parsedEvent);
        break;
        
      case 'RUN_FINISHED':
        console.log('Agent运行完成');
        break;
        
      case 'RUN_ERROR':
        console.error('Agent错误:', parsedEvent.message);
        break;
    }
  },
});
```

---

## 🛠️ 工具定义模板

### 基础工具

```typescript
const basicTool: Tool = {
  name: 'toolName',
  description: '工具的详细描述，帮助LLM理解何时使用',
  parameters: {
    type: 'object',
    properties: {
      param1: {
        type: 'string',
        description: '参数描述',
      },
      param2: {
        type: 'number',
        description: '参数描述',
      },
    },
    required: ['param1'],
  },
};
```

### 带枚举的工具

```typescript
const advancedTool: Tool = {
  name: 'searchPOI',
  description: '搜索指定类型的POI',
  parameters: {
    type: 'object',
    properties: {
      keyword: {
        type: 'string',
        description: '搜索关键词',
      },
      type: {
        type: 'string',
        enum: ['景点', '餐厅', '酒店'],
        description: 'POI类型',
      },
      limit: {
        type: 'number',
        description: '返回结果数量',
        default: 10,
      },
    },
    required: ['keyword'],
  },
};
```

---

## 🚀 快速测试命令

### 测试最简单的Agent

```bash
# 后端代码（最小实现）
router.post('/agent/test', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.write('data: {"type":"RUN_STARTED","thread_id":"t1","run_id":"r1"}\n\n');
  res.write('data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"m1","delta":"Hello"}\n\n');
  res.write('data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"m1","delta":""}\n\n');
  res.write('data: {"type":"RUN_FINISHED","thread_id":"t1","run_id":"r1"}\n\n');
  res.end();
});

# 测试
curl -N -H "Accept: text/event-stream" http://localhost:3000/api/v1/agent/test
```

### 测试前端EventSource

```javascript
// 浏览器Console
const es = new EventSource('/api/v1/agent/test');
es.onmessage = (event) => {
  console.log('Event:', JSON.parse(event.data));
};
```

### 测试fetch-event-source

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource('/api/v1/agent/test', {
  method: 'POST',
  onmessage: (event) => {
    console.log('Event:', JSON.parse(event.data));
  },
});
```

---

## 📚 参考链接

- **完整实现指南**: [AG-UI_IMPLEMENTATION.md](./AG-UI_IMPLEMENTATION.md)
- **协议完整规范**: [AG-UI.txt](./AG-UI.txt)
- **官方文档**: https://docs.ag-ui.com/
- **GitHub仓库**: https://github.com/ag-ui-protocol/ag-ui

---

## 💡 最佳实践

### ✅ DO

- ✅ 使用`TEXT_MESSAGE_CHUNK`和`TOOL_CALL_CHUNK`（更简单）
- ✅ 始终发出`RUN_STARTED`和`RUN_FINISHED`
- ✅ 使用有意义的threadId和runId
- ✅ 工具描述要详细清晰
- ✅ 验证工具参数符合schema
- ✅ 处理错误并发出`RUN_ERROR`
- ✅ 记录所有事件用于调试

### ❌ DON'T

- ❌ 不要跳过生命周期事件
- ❌ 不要在`TEXT_MESSAGE_CONTENT`中发送空delta
- ❌ 不要混淆messageId
- ❌ 不要阻塞事件流
- ❌ 不要在工具中递归调用Agent
- ❌ 不要在生产环境暴露原始错误信息

---

**文档版本**: v1.0  
**最后更新**: 2025-10-17

