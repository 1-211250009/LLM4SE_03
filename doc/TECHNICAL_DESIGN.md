# AI旅行规划师 - 技术设计文档

## 项目概述
一个基于AI的智能旅行规划Web应用，支持语音交互、智能行程规划、费用管理和多设备同步。

---

## 一、完整技术栈设计

### 1.1 前端技术栈

#### 核心框架
- **React 18** - UI框架，采用函数式组件和Hooks
- **TypeScript** - 类型安全，提高代码质量
- **Vite** - 快速的构建工具和开发服务器

#### 状态管理
- **Zustand** - 轻量级状态管理（全局用户状态、行程数据）
- **React Query (TanStack Query)** - 服务端状态管理和缓存

#### UI组件库
- **Ant Design** - 企业级UI组件库
- **TailwindCSS** - 原子化CSS框架，用于自定义样式
- **Framer Motion** - 动画库，提升用户体验

#### 地图相关
- **百度地图 JavaScript API v3.0** - 地图展示和路线规划
- **react-bmapgl** - React百度地图组件封装

#### 语音交互
- **科大讯飞 Web SDK** - 语音识别（ASR）和语音合成（TTS）
- **Web Audio API** - 音频录制和处理

#### AG-UI协议集成
- **RxJS** - Observable流处理（AG-UI事件流）
- **EventSource API** - 接收Server-Sent Events (SSE)

#### 工具库
- **Axios** - HTTP客户端
- **Day.js** - 日期处理
- **React Router v6** - 路由管理
- **React Hook Form** - 表单管理
- **Zod** - 运行时类型验证

### 1.2 后端技术栈

#### 核心框架
- **Python 3.11+** - 运行时环境
- **FastAPI** - 现代高性能Web框架
- **Pydantic** - 数据验证和类型安全
- **Uvicorn** - ASGI服务器

#### API协议
- **AG-UI Protocol** - LLM交互协议标准（事件驱动架构）
- **RESTful API** - 标准HTTP接口
- **Server-Sent Events (SSE)** - AG-UI流式响应传输（HTTP SSE）
- **HTTP Binary Protocol** - AG-UI高性能二进制传输（可选）

#### 数据库
- **PostgreSQL 15** - 主数据库（用户、行程数据）
- **Redis** - 缓存和会话管理
- **SQLAlchemy** - ORM框架，SQL工具包
- **Alembic** - 数据库迁移工具

#### 认证与授权
- **PyJWT** - JWT令牌生成和验证
- **passlib + bcrypt** - 密码加密
- **slowapi** - API限流中间件

#### LLM集成
- **阿里云百炼平台 SDK (Python)** - 主要LLM服务
- **OpenAI Python SDK** - 备选LLM服务
- **AG-UI Protocol (ag-ui-protocol)** - Python协议适配层

### 1.3 第三方服务集成

#### AI服务
- **阿里云百炼平台** - 千问模型，行程规划和预算分析
- **提示词工程** - 专门的行程规划和费用估算提示词模板

#### 语音服务
- **科大讯飞开放平台**
  - WebAPI 语音识别（实时流式）
  - 在线语音合成
  - 支持中英文混合识别

#### 地图服务
- **百度地图开放平台**
  - JavaScript API - 地图展示
  - Web服务API - 地理编码、路线规划
  - Place API - POI检索（景点、餐厅、酒店）

#### 文件存储
- **本地存储** - 用户上传的图片、语音文件存储

### 1.4 开发运维工具

#### 容器化
- **Docker** - 容器化部署
- **Docker Compose** - 本地开发环境编排

#### CI/CD
- **GitHub Actions** - 自动化构建和部署
- **阿里云容器镜像服务** - Docker镜像仓库

#### 代码质量
- **ESLint** - 代码规范检查
- **Prettier** - 代码格式化
- **Husky + lint-staged** - Git提交钩子

#### 测试
- **pytest** - Python单元测试框架
- **pytest-asyncio** - 异步测试支持
- **httpx** - 异步HTTP客户端（测试用）
- **Vitest** - 前端单元测试框架
- **React Testing Library** - React组件测试
- **Playwright** - E2E测试

#### 监控与日志
- **Python logging** - 标准日志库
- **Loguru** - 更优雅的日志解决方案（可选）
- **Uvicorn** - ASGI服务器（内置日志）

---

## 二、项目框架与模块划分

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端层 (Frontend)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  语音模块    │  │  地图模块    │  │   UI组件     │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │            │
│         └────────────────┼────────────────┘            │
│                          │                             │
│                   ┌──────▼──────┐                      │
│                   │  状态管理层  │                      │
│                   └──────┬──────┘                      │
└──────────────────────────┼──────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────▼──────────────────────────────┐
│                    后端层 (Backend)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ API网关层    │  │  认证中间件   │  │  限流中间件  │      │
│  └──────┬──────┘  └─────────────┘  └─────────────┘     │
│         │                                               │
│  ┌──────▼────────────────────────────────────────┐     │
│  │              业务逻辑层 (Services)              │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │     │
│  │  │LLM-Agent │ │  语音服务 │ │  地图服务 │       │     │
│  │  │  服务    │ │          │ │          │       │     │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘       │     │
│  │       │            │            │             │     │
│  │  ┌────▼────┐  ┌────▼────┐  ┌────▼────┐        │     │
│  │  │行程服务  │  │费用服务  │  │用户服务  │        │     │
│  │  └─────────┘  └─────────┘  └─────────┘        │     │
│  └───────────────────────┬──────────────────────┘     │
│                          │                             │
│  ┌───────────────────────▼──────────────────────┐     │
│  │            数据访问层 (Data Access)            │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │     │
│  │  │PostgreSQL│  │   Redis  │  │  Prisma  │    │     │
│  │  └──────────┘  └──────────┘  └──────────┘    │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│              第三方服务层 (External Services)         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │  阿里云百炼   │ │ 科大讯飞API  │ │ 百度地图API   │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 2.2 模块详细设计

#### 2.2.1 LLM-Agent模块

**职责**: 处理与大语言模型的交互，生成行程规划和费用预算

**设计模式**: 采用AG-UI协议的Server Implementation模式

**子模块**:
```
llm-agent/
├── agents/               # AG-UI Agent实现
│   ├── abstract-agent.ts # 继承AG-UI AbstractAgent基类
│   ├── trip-planner.agent.ts   # 行程规划Agent
│   ├── budget-analyzer.agent.ts # 费用分析Agent
│   └── chat-assistant.agent.ts  # 对话助手Agent
├── events/               # AG-UI事件处理
│   ├── event-emitter.ts  # 事件发射器
│   ├── event-encoder.ts  # SSE/Binary编码器
│   └── event-types.ts    # AG-UI事件类型定义
├── prompts/              # 提示词模板
│   ├── trip-planning.ts  # 行程规划提示词
│   ├── budget-analysis.ts # 费用分析提示词
│   └── optimization.ts   # 行程优化提示词
├── tools/                # AG-UI Frontend Tools
│   ├── poi-search.tool.ts     # POI搜索工具定义
│   ├── route-calc.tool.ts     # 路线计算工具定义
│   └── price-query.tool.ts    # 价格查询工具定义
├── services/             # LLM服务集成
│   ├── aliyun-llm.service.ts  # 阿里云LLM API封装
│   └── context-manager.ts     # 对话上下文管理
└── types/                # 类型定义
    ├── agui.types.ts     # AG-UI协议类型
    └── agent.types.ts    # Agent业务类型
```

**核心功能（基于AG-UI协议）**:
- **事件驱动架构**: 通过Observable流发出16种标准AG-UI事件
- **流式响应**: 支持Server-Sent Events (SSE)和Binary Protocol
- **消息管理**: 维护符合AG-UI规范的消息历史（User/Assistant/Tool/System）
- **工具系统**: 前端定义Tools，Agent调用并返回结果
- **状态同步**: 通过STATE_SNAPSHOT和STATE_DELTA事件同步状态
- **生命周期管理**: RUN_STARTED → STEP_* → RUN_FINISHED/RUN_ERROR

**AG-UI Agent接口设计**:
```typescript
import { AbstractAgent, RunAgentInput, BaseEvent } from '@ag-ui/core';
import { Observable } from 'rxjs';

// 行程规划Agent（继承AG-UI AbstractAgent）
class TripPlannerAgent extends AbstractAgent {
  run(input: RunAgentInput): Observable<BaseEvent> {
    return new Observable<BaseEvent>((observer) => {
      // 1. 发出RUN_STARTED事件
      observer.next({
        type: EventType.RUN_STARTED,
        threadId: input.threadId,
        runId: input.runId,
      });

      // 2. 处理用户消息，调用LLM
      // 3. 流式发出TEXT_MESSAGE_* 或 TOOL_CALL_* 事件
      // 4. 更新状态通过STATE_DELTA事件
      
      // 5. 发出RUN_FINISHED事件
      observer.next({
        type: EventType.RUN_FINISHED,
        threadId: input.threadId,
        runId: input.runId,
      });

      observer.complete();
    });
  }
}

// Agent工具定义（Frontend Tools）
interface TripPlannerTools {
  searchPOI: Tool;      // POI搜索工具
  calculateRoute: Tool; // 路线计算工具
  queryPrice: Tool;     // 价格查询工具
}
```

#### 2.2.2 地图模块

**职责**: 地图展示、POI检索、路线规划、地理编码

**子模块**:
```
map-module/
├── components/           # 地图组件
│   ├── MapContainer.tsx  # 地图容器
│   ├── RouteOverlay.tsx  # 路线覆盖层
│   ├── POIMarker.tsx     # POI标记
│   └── InfoWindow.tsx    # 信息窗口
├── services/             # 地图服务
│   ├── baidu-map.ts      # 百度地图API封装
│   ├── geocoding.ts      # 地理编码服务
│   ├── poi-search.ts     # POI搜索服务
│   └── route-planning.ts # 路线规划服务
├── hooks/                # React Hooks
│   ├── useMap.ts         # 地图实例Hook
│   ├── usePOISearch.ts   # POI搜索Hook
│   └── useRouteCalc.ts   # 路线计算Hook
└── types/                # 类型定义
    ├── map.types.ts
    └── poi.types.ts
```

**核心功能**:
- 百度地图初始化和配置
- 交互式地图展示（缩放、拖拽、定位）
- POI（景点、餐厅、酒店）搜索和展示
- 多种交通方式的路线规划
- 自定义标记和信息窗口
- 地理编码和逆地理编码

**接口设计**:
```typescript
interface IMapService {
  initMap(container: HTMLElement, options: MapOptions): void;
  addMarker(poi: POI): Marker;
  searchPOI(keyword: string, city: string): Promise<POI[]>;
  calculateRoute(start: Point, end: Point, mode: TransportMode): Promise<Route>;
  geocode(address: string): Promise<Point>;
}
```

#### 2.2.3 语音模块

**职责**: 语音输入、语音识别、语音合成、音频管理

**子模块**:
```
voice-module/
├── components/           # 语音组件
│   ├── VoiceInput.tsx    # 语音输入按钮
│   ├── VoiceWave.tsx     # 语音波形动画
│   └── VoiceFeedback.tsx # 语音反馈提示
├── services/             # 语音服务
│   ├── xfyun-asr.ts      # 讯飞语音识别
│   ├── xfyun-tts.ts      # 讯飞语音合成
│   └── audio-recorder.ts # 音频录制
├── hooks/                # React Hooks
│   ├── useVoiceInput.ts  # 语音输入Hook
│   ├── useVoiceOutput.ts # 语音输出Hook
│   └── useAudioRecorder.ts # 录音Hook
├── utils/                # 工具函数
│   ├── audio-process.ts  # 音频处理
│   └── pcm-convert.ts    # PCM格式转换
└── types/                # 类型定义
    └── voice.types.ts
```

**核心功能**:
- 实时语音识别（流式ASR）
- 语音合成播放（TTS）
- 音频录制和格式转换
- 语音活动检测（VAD）
- 多语言支持（中英文）
- 语音状态管理（录音中、识别中、播放中）

**接口设计**:
```typescript
interface IVoiceService {
  startRecording(): Promise<void>;
  stopRecording(): Promise<AudioData>;
  recognizeSpeech(audio: AudioData): Promise<string>;
  synthesizeSpeech(text: string): Promise<AudioBuffer>;
  playAudio(buffer: AudioBuffer): Promise<void>;
}
```

#### 2.2.4 后端接口模块

**职责**: API路由、业务逻辑编排、数据访问、第三方服务集成

**技术栈**: Python + FastAPI + SQLAlchemy

**子模块**:
```
backend/
├── app/
│   ├── api/              # API路由层
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py      # 认证端点
│   │   │   │   ├── agent.py     # AG-UI Agent端点
│   │   │   │   ├── trip.py      # 行程端点
│   │   │   │   ├── budget.py    # 费用端点
│   │   │   │   ├── voice.py     # 语音端点
│   │   │   │   └── map.py       # 地图端点
│   │   │   └── api.py           # API路由聚合
│   │   └── deps.py               # 依赖注入
│   ├── services/         # 业务逻辑层
│   │   ├── llm/          # LLM服务
│   │   │   ├── agents/   # AG-UI Agent实现
│   │   │   ├── events/   # 事件处理
│   │   │   └── services/ # LLM调用
│   │   ├── voice/        # 语音服务
│   │   │   └── xfyun_service.py
│   │   ├── map/          # 地图服务
│   │   │   └── baidu_map_service.py
│   │   ├── auth_service.py
│   │   ├── trip_service.py
│   │   └── budget_service.py
│   ├── models/           # SQLAlchemy模型
│   │   ├── user.py
│   │   ├── trip.py
│   │   └── budget.py
│   ├── schemas/          # Pydantic Schema (请求/响应)
│   │   ├── auth.py
│   │   ├── trip.py
│   │   └── budget.py
│   ├── core/             # 核心配置
│   │   ├── config.py     # 配置管理
│   │   ├── security.py   # JWT、密码加密
│   │   └── database.py   # 数据库连接
│   ├── middleware/       # 中间件
│   │   ├── auth.py       # JWT认证
│   │   ├── rate_limit.py # 限流
│   │   └── error_handler.py # 错误处理
│   └── utils/            # 工具函数
│       ├── logger.py
│       └── validators.py
├── alembic/              # 数据库迁移
│   ├── versions/
│   └── env.py
├── tests/                # 测试
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── main.py               # FastAPI应用入口
├── pyproject.toml        # Poetry依赖管理
└── .env                  # 环境变量
```

**核心功能**:
- RESTful API接口（FastAPI自动生成OpenAPI文档）
- SSE流式响应（AG-UI协议）
- JWT认证和授权
- Pydantic自动请求验证
- 统一异常处理
- API限流和防护
- 结构化日志记录

**API设计规范**:
```typescript
// ========== 认证接口 (RESTful) ==========
POST   /api/v1/auth/register          # 注册
POST   /api/v1/auth/login             # 登录
POST   /api/v1/auth/refresh           # 刷新Token

// ========== AG-UI协议端点 (SSE Stream) ==========
POST   /api/v1/agent/trip-planner     # 行程规划Agent
  Header: Accept: text/event-stream
  Body: RunAgentInput {
    threadId, runId, messages, tools, state, context
  }
  Response: Server-Sent Events流

POST   /api/v1/agent/budget-analyzer  # 费用分析Agent
  Header: Accept: text/event-stream
  Body: RunAgentInput
  Response: SSE流（AG-UI事件）

POST   /api/v1/agent/chat-assistant   # 对话助手Agent
  Header: Accept: text/event-stream 或 application/octet-stream
  Body: RunAgentInput
  Response: SSE流或Binary流

// ========== 行程管理接口 (RESTful) ==========
GET    /api/v1/trips                  # 获取行程列表
POST   /api/v1/trips                  # 创建行程
GET    /api/v1/trips/:id              # 获取行程详情
PUT    /api/v1/trips/:id              # 更新行程
DELETE /api/v1/trips/:id              # 删除行程

// ========== 费用管理接口 (RESTful) ==========
GET    /api/v1/budget/:tripId         # 获取行程预算
POST   /api/v1/budget/:tripId/expense # 添加开销
GET    /api/v1/budget/analysis        # 预算分析

// ========== 语音接口 (RESTful) ==========
POST   /api/v1/voice/asr              # 语音识别
POST   /api/v1/voice/tts              # 语音合成

// ========== 地图接口 (RESTful) ==========
POST   /api/v1/map/geocode            # 地理编码
POST   /api/v1/map/poi/search         # POI搜索
POST   /api/v1/map/route              # 路线规划

// ========== AG-UI事件类型说明 ==========
// 生命周期事件: RUN_STARTED, RUN_FINISHED, RUN_ERROR, STEP_STARTED, STEP_FINISHED
// 文本消息事件: TEXT_MESSAGE_START, TEXT_MESSAGE_CONTENT, TEXT_MESSAGE_END, TEXT_MESSAGE_CHUNK
// 工具调用事件: TOOL_CALL_START, TOOL_CALL_ARGS, TOOL_CALL_END, TOOL_CALL_RESULT
// 状态管理事件: STATE_SNAPSHOT, STATE_DELTA, MESSAGES_SNAPSHOT
// 特殊事件: RAW, CUSTOM
```

#### 2.2.5 前端实现模块

**职责**: 用户界面、交互逻辑、状态管理、路由管理

**子模块**:
```
frontend/
├── src/
│   ├── pages/            # 页面组件
│   │   ├── Home/         # 首页
│   │   ├── Login/        # 登录页
│   │   ├── Register/     # 注册页
│   │   ├── TripPlanning/ # 行程规划页
│   │   ├── TripDetail/   # 行程详情页
│   │   ├── BudgetManagement/ # 费用管理页
│   │   └── Profile/      # 个人中心
│   ├── components/       # 通用组件
│   │   ├── layout/       # 布局组件
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── common/       # 通用组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Loading.tsx
│   │   ├── trip/         # 行程相关组件
│   │   │   ├── TripCard.tsx
│   │   │   ├── ItineraryTimeline.tsx
│   │   │   └── POICard.tsx
│   │   └── budget/       # 费用相关组件
│   │       ├── BudgetChart.tsx
│   │       ├── ExpenseList.tsx
│   │       └── BudgetSummary.tsx
│   ├── modules/          # 功能模块
│   │   ├── voice/        # 语音模块
│   │   ├── map/          # 地图模块
│   │   └── llm/          # LLM交互模块
│   ├── store/            # 状态管理
│   │   ├── auth.store.ts
│   │   ├── trip.store.ts
│   │   ├── budget.store.ts
│   │   └── app.store.ts
│   ├── services/         # API服务
│   │   ├── api.service.ts
│   │   ├── auth.service.ts
│   │   ├── trip.service.ts
│   │   └── websocket.service.ts
│   ├── hooks/            # 自定义Hooks
│   │   ├── useAuth.ts
│   │   ├── useTrip.ts
│   │   └── useBudget.ts
│   ├── utils/            # 工具函数
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   └── storage.ts
│   ├── types/            # 类型定义
│   │   ├── api.types.ts
│   │   ├── trip.types.ts
│   │   └── user.types.ts
│   ├── styles/           # 样式文件
│   │   ├── globals.css
│   │   └── variables.css
│   ├── App.tsx           # 根组件
│   ├── main.tsx          # 入口文件
│   └── router.tsx        # 路由配置
├── public/               # 静态资源
└── index.html            # HTML模板
```

**核心功能**:
- 响应式UI设计
- 组件化开发
- 状态管理和数据流
- 路由导航
- 表单处理和验证
- 错误边界和异常处理
- 国际化支持（可选）

### 2.3 模块间通信

#### 前端模块间通信
- **Event Bus**: 跨组件事件通信
- **Zustand Store**: 全局状态共享
- **Props/Context**: 父子组件通信

#### 前后端通信
- **HTTP/HTTPS**: RESTful API调用
- **WebSocket**: 实时双向通信（流式响应）
- **JSON**: 数据交换格式

#### 后端服务间通信
- **Service Layer**: 服务间直接调用
- **Event Emitter**: 异步事件通知
- **Redis Pub/Sub**: 跨进程通信（可选）

---

## 三、项目阶段规划

### 阶段0: 项目初始化（1-2天）

**目标**: 搭建开发环境和基础框架

**任务清单**:
- [ ] 创建Git仓库，设置.gitignore
- [ ] 初始化前端项目（Vite + React + TypeScript）
- [ ] 初始化后端项目（Node.js + Express + TypeScript）
- [ ] 配置ESLint、Prettier、Husky
- [ ] 搭建Docker开发环境
- [ ] 配置PostgreSQL和Redis
- [ ] 配置Prisma ORM
- [ ] 创建基础项目结构和目录
- [ ] 编写README和开发文档

**验收标准**:
- ✅ 前后端项目可以正常启动
- ✅ 数据库连接成功
- ✅ 代码提交自动触发lint检查
- ✅ Docker Compose可以一键启动所有服务

**测试验证**:
```bash
# 启动开发环境
docker-compose up -d

# 访问前端
curl http://localhost:5173

# 访问后端
curl http://localhost:3000/health

# 测试数据库连接
npx prisma db push
```

---

### 阶段1: 用户认证系统（3-4天）

**目标**: 实现完整的用户注册、登录、认证功能

**任务清单**:

**后端**:
- [ ] 设计用户数据模型（Prisma Schema）
- [ ] 实现用户注册接口（密码加密）
- [ ] 实现用户登录接口（JWT生成）
- [ ] 实现Token刷新接口
- [ ] 实现JWT认证中间件
- [ ] 实现用户信息查询接口
- [ ] 编写单元测试

**前端**:
- [ ] 创建登录页面UI
- [ ] 创建注册页面UI
- [ ] 实现表单验证
- [ ] 实现认证状态管理（Zustand）
- [ ] 实现路由守卫
- [ ] 实现Token自动刷新
- [ ] 实现退出登录功能

**验收标准**:
- ✅ 用户可以成功注册账号
- ✅ 用户可以使用账号密码登录
- ✅ JWT Token正确生成和验证
- ✅ 受保护的路由需要登录才能访问
- ✅ Token过期后自动刷新
- ✅ 所有接口通过单元测试

**测试验证**:
```bash
# 测试注册
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456","name":"Test User"}'

# 测试登录
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'

# 运行测试
npm run test:auth
```

---

### 阶段2: LLM-Agent模块开发（5-6天）

**目标**: 实现基于AG-UI协议的LLM交互，完成行程规划和费用预算功能

**任务清单**:

**AG-UI协议实现（核心）**:
- [ ] 安装AG-UI依赖（RxJS用于Observable）
- [ ] 定义AG-UI事件类型（16种标准事件）
- [ ] 实现AbstractAgent基类扩展
- [ ] 实现事件流Observable生成器
- [ ] 实现SSE事件编码器（EventEncoder）
- [ ] 实现消息格式转换（AG-UI ↔ 阿里云API）
- [ ] 实现状态管理（StateSnapshot/StateDelta）
- [ ] 测试事件流完整性

**LLM服务集成**:
- [ ] 申请阿里云百炼平台API Key
- [ ] 封装阿里云LLM API调用（转换为AG-UI格式）
- [ ] 实现流式响应转换（阿里云流 → AG-UI事件）
- [ ] 实现错误处理（发出RUN_ERROR事件）
- [ ] 实现对话历史管理（Messages数组）

**前端工具定义（Frontend Tools）**:
- [ ] 定义POI搜索工具（Tool Schema）
- [ ] 定义路线计算工具（Tool Schema）
- [ ] 定义价格查询工具（Tool Schema）
- [ ] 实现工具执行处理器
- [ ] 实现工具结果返回（ToolMessage）

**行程规划Agent**:
- [ ] 实现TripPlannerAgent类（继承AbstractAgent）
- [ ] 设计行程规划提示词模板
- [ ] 实现run()方法（发出AG-UI事件流）
- [ ] 实现工具调用流程（TOOL_CALL_* 事件）
- [ ] 实现行程生成逻辑（流式TEXT_MESSAGE_*事件）
- [ ] 实现状态更新（STATE_DELTA事件）
- [ ] 集成地图POI工具

**费用预算Agent**:
- [ ] 实现BudgetAnalyzerAgent类
- [ ] 设计费用估算提示词模板
- [ ] 实现预算分析逻辑
- [ ] 实现费用分类和统计
- [ ] 实现预算预警功能

**HTTP端点实现**:
- [ ] POST /api/v1/agent/trip-planner - AG-UI端点（返回SSE流）
- [ ] POST /api/v1/agent/budget-analyzer - AG-UI端点
- [ ] POST /api/v1/agent/chat-assistant - AG-UI端点
- [ ] 实现SSE响应流处理

**前端AG-UI客户端**:
- [ ] 实现AG-UI事件订阅器（AgentSubscriber）
- [ ] 实现EventSource SSE客户端
- [ ] 实现事件处理器（onTextMessageContent等）
- [ ] 实现流式UI更新
- [ ] 实现工具调用UI交互

**验收标准**:
- ✅ Agent正确发出所有必需的AG-UI事件
- ✅ 事件顺序符合AG-UI规范（RUN_STARTED → ... → RUN_FINISHED）
- ✅ SSE流式响应正常工作
- ✅ 可以成功调用阿里云LLM API并转换响应
- ✅ 前端工具可以被Agent调用
- ✅ 工具执行结果正确返回给Agent
- ✅ 输入旅行需求后能生成合理的行程
- ✅ 行程包含景点、餐厅、酒店、交通信息
- ✅ 能够估算详细的费用预算
- ✅ 流式响应实时显示规划过程

**测试验证**:
```bash
# 测试AG-UI行程规划Agent（SSE流式响应）
curl -X POST http://localhost:3000/api/v1/agent/trip-planner \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "threadId": "thread-123",
    "runId": "run-456",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "帮我规划一个5天的东京之旅，预算10000元，2人，喜欢美食、动漫、亲子活动"
      }
    ],
    "tools": [
      {
        "name": "searchPOI",
        "description": "搜索景点、餐厅、酒店等POI",
        "parameters": {...}
      }
    ],
    "state": {},
    "context": []
  }'

# 预期输出（SSE事件流）:
# data: {"type":"RUN_STARTED","threadId":"thread-123","runId":"run-456"}
# data: {"type":"TEXT_MESSAGE_START","messageId":"msg-2","role":"assistant"}
# data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg-2","delta":"我将为您..."}
# data: {"type":"TOOL_CALL_START","toolCallId":"tool-1","toolCallName":"searchPOI"}
# data: {"type":"TOOL_CALL_ARGS","toolCallId":"tool-1","delta":"{\"keyword\":\"东京塔\"}"}
# data: {"type":"TOOL_CALL_END","toolCallId":"tool-1"}
# ...
# data: {"type":"RUN_FINISHED","threadId":"thread-123","runId":"run-456"}

# 运行Agent测试
npm run test:agent
```

---

### 阶段3: 地图模块开发（4-5天）

**目标**: 集成百度地图，实现地图展示、POI搜索、路线规划

**任务清单**:

**百度地图集成**:
- [ ] 申请百度地图API Key
- [ ] 前端集成百度地图JavaScript API
- [ ] 后端集成百度地图Web服务API
- [ ] 实现地图配置管理

**地图展示**:
- [ ] 实现地图容器组件
- [ ] 实现地图初始化和配置
- [ ] 实现地图交互（缩放、拖拽、定位）
- [ ] 实现自定义地图样式

**POI搜索**:
- [ ] 实现POI搜索接口
- [ ] 实现POI标记展示
- [ ] 实现POI信息窗口
- [ ] 实现POI分类筛选
- [ ] 实现POI详情展示

**路线规划**:
- [ ] 实现路线计算接口
- [ ] 实现路线覆盖层展示
- [ ] 支持多种交通方式（驾车、公交、步行）
- [ ] 显示路线详情（距离、时间、费用）
- [ ] 实现途径点路线规划

**行程地图可视化**:
- [ ] 在地图上展示完整行程
- [ ] 按天展示行程路线
- [ ] 实现行程点击查看详情
- [ ] 实现行程编辑（拖拽调整）

**API接口**:
- [ ] POST /api/v1/map/poi/search - POI搜索
- [ ] POST /api/v1/map/route - 路线规划
- [ ] POST /api/v1/map/geocode - 地理编码

**验收标准**:
- ✅ 地图正常加载和显示
- ✅ 可以搜索景点、餐厅、酒店
- ✅ POI标记正确显示在地图上
- ✅ 点击标记显示详细信息
- ✅ 可以规划不同交通方式的路线
- ✅ 行程在地图上完整可视化

**测试验证**:
```bash
# 测试POI搜索
curl -X POST http://localhost:3000/api/v1/map/poi/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "keyword": "东京塔",
    "city": "东京",
    "type": "景点"
  }'

# 测试路线规划
curl -X POST http://localhost:3000/api/v1/map/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "origin": "东京站",
    "destination": "浅草寺",
    "mode": "transit"
  }'
```

---

### 阶段4: 语音模块开发（4-5天）

**目标**: 集成科大讯飞语音服务，实现语音输入和语音合成

**任务清单**:

**科大讯飞集成**:
- [ ] 申请科大讯飞API Key
- [ ] 前端集成讯飞Web SDK
- [ ] 后端集成讯飞WebAPI
- [ ] 实现API Key配置管理

**语音识别（ASR）**:
- [ ] 实现音频录制功能
- [ ] 实现实时流式识别
- [ ] 实现音频格式转换（PCM）
- [ ] 实现识别结果处理
- [ ] 实现语音活动检测（VAD）
- [ ] 支持中英文混合识别

**语音合成（TTS）**:
- [ ] 实现文字转语音接口
- [ ] 实现语音播放功能
- [ ] 支持多种音色选择
- [ ] 实现语音队列管理

**语音交互UI**:
- [ ] 实现语音输入按钮组件
- [ ] 实现语音波形动画
- [ ] 实现录音状态提示
- [ ] 实现识别结果实时显示
- [ ] 实现语音错误提示

**语音与LLM集成**:
- [ ] 语音输入触发行程规划
- [ ] AI回复自动语音播报
- [ ] 语音添加费用记录
- [ ] 语音查询行程信息

**API接口**:
- [ ] POST /api/v1/voice/asr - 语音识别
- [ ] POST /api/v1/voice/tts - 语音合成
- [ ] WS /ws/voice/stream - 流式语音识别

**验收标准**:
- ✅ 可以录制音频并上传
- ✅ 语音识别准确率高（中文）
- ✅ 识别结果实时显示
- ✅ 文字可以转换为语音播放
- ✅ 语音可以触发行程规划
- ✅ 语音可以添加费用记录

**测试验证**:
```bash
# 测试语音识别
curl -X POST http://localhost:3000/api/v1/voice/asr \
  -H "Authorization: Bearer <token>" \
  -F "audio=@test.wav"

# 测试语音合成
curl -X POST http://localhost:3000/api/v1/voice/tts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"text": "您的行程已生成", "voice": "xiaoyan"}' \
  --output output.mp3
```

---

### 阶段5: 行程管理功能（3-4天）

**目标**: 实现完整的行程CRUD，行程详情展示，行程分享

**任务清单**:

**数据模型**:
- [ ] 设计行程数据模型（Trip, Itinerary, POI）
- [ ] 创建数据库迁移
- [ ] 实现数据访问层

**行程管理API**:
- [ ] GET /api/v1/trips - 获取行程列表
- [ ] POST /api/v1/trips - 创建行程
- [ ] GET /api/v1/trips/:id - 获取行程详情
- [ ] PUT /api/v1/trips/:id - 更新行程
- [ ] DELETE /api/v1/trips/:id - 删除行程
- [ ] POST /api/v1/trips/:id/share - 分享行程

**前端页面**:
- [ ] 行程列表页（卡片展示）
- [ ] 行程详情页（时间轴展示）
- [ ] 行程编辑页（拖拽排序）
- [ ] 行程创建向导

**行程展示**:
- [ ] 时间轴展示每日行程
- [ ] 地图展示行程路线
- [ ] POI卡片展示详细信息
- [ ] 图片画廊展示

**行程编辑**:
- [ ] 添加/删除行程点
- [ ] 调整行程顺序（拖拽）
- [ ] 修改行程时间
- [ ] 添加自定义备注

**验收标准**:
- ✅ 可以查看所有行程列表
- ✅ 可以查看行程详细信息
- ✅ 可以手动创建和编辑行程
- ✅ 可以删除行程
- ✅ 行程按时间轴清晰展示
- ✅ 行程在地图上可视化

**测试验证**:
```bash
# 测试获取行程列表
curl http://localhost:3000/api/v1/trips \
  -H "Authorization: Bearer <token>"

# 测试创建行程
curl -X POST http://localhost:3000/api/v1/trips \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d @trip-data.json

# 运行集成测试
npm run test:trip
```

---

### 阶段6: 费用管理功能（3-4天）

**目标**: 实现费用预算、费用记录、费用分析功能

**任务清单**:

**数据模型**:
- [ ] 设计费用数据模型（Budget, Expense, Category）
- [ ] 创建数据库迁移

**费用管理API**:
- [ ] GET /api/v1/budget/:tripId - 获取行程预算
- [ ] POST /api/v1/budget/:tripId - 创建预算
- [ ] POST /api/v1/budget/:tripId/expense - 添加开销
- [ ] PUT /api/v1/budget/expense/:id - 更新开销
- [ ] DELETE /api/v1/budget/expense/:id - 删除开销
- [ ] GET /api/v1/budget/analysis - 费用分析

**前端页面**:
- [ ] 费用管理页面
- [ ] 费用添加对话框（支持语音）
- [ ] 费用列表和分类展示
- [ ] 预算进度条
- [ ] 费用统计图表

**费用分析**:
- [ ] 费用分类统计（交通、住宿、餐饮、门票等）
- [ ] 预算vs实际对比
- [ ] 费用趋势图
- [ ] 超支预警
- [ ] 费用占比饼图

**语音费用记录**:
- [ ] 语音输入费用信息
- [ ] AI解析费用内容（金额、类别、备注）
- [ ] 自动创建费用记录

**验收标准**:
- ✅ 可以设置行程预算
- ✅ 可以添加费用记录
- ✅ 可以使用语音添加费用
- ✅ 费用按类别统计展示
- ✅ 实时显示预算使用情况
- ✅ 超支时有预警提示
- ✅ 费用分析图表清晰美观

**测试验证**:
```bash
# 测试添加费用
curl -X POST http://localhost:3000/api/v1/budget/123/expense \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "amount": 150,
    "category": "餐饮",
    "description": "晚餐",
    "date": "2025-10-20"
  }'

# 测试费用分析
curl http://localhost:3000/api/v1/budget/analysis?tripId=123 \
  -H "Authorization: Bearer <token>"
```

---

### 阶段7: 前端UI/UX优化（3-4天）

**目标**: 优化用户界面，提升用户体验，实现响应式设计

**任务清单**:

**UI优化**:
- [ ] 设计统一的视觉风格
- [ ] 优化颜色主题和配色方案
- [ ] 优化字体和排版
- [ ] 添加图标和插图
- [ ] 优化按钮和表单样式

**动画效果**:
- [ ] 页面切换动画
- [ ] 组件加载动画
- [ ] 语音波形动画
- [ ] 地图标记动画
- [ ] 行程卡片悬停效果

**响应式设计**:
- [ ] 移动端适配（375px-768px）
- [ ] 平板端适配（768px-1024px）
- [ ] 桌面端适配（>1024px）
- [ ] 测试不同设备和屏幕尺寸

**交互优化**:
- [ ] 优化Loading状态
- [ ] 优化空状态展示
- [ ] 优化错误提示
- [ ] 添加操作反馈
- [ ] 添加引导提示

**性能优化**:
- [ ] 图片懒加载
- [ ] 路由懒加载
- [ ] 组件代码分割
- [ ] 防抖和节流
- [ ] 虚拟滚动（长列表）

**可访问性**:
- [ ] 键盘导航支持
- [ ] ARIA标签
- [ ] 语义化HTML
- [ ] 对比度检查

**验收标准**:
- ✅ UI美观现代，符合Material Design或类似规范
- ✅ 动画流畅不卡顿
- ✅ 移动端体验良好
- ✅ 首屏加载时间<3秒
- ✅ 交互反馈及时明确

**测试验证**:
- 在Chrome DevTools中测试不同设备
- 使用Lighthouse进行性能评分
- 使用WebPageTest测试加载速度

---

### 阶段8: 云端同步功能（2-3天）

**目标**: 实现数据云端存储和多设备同步

**任务清单**:

**数据同步**:
- [ ] 实现行程数据云端存储
- [ ] 实现费用数据云端存储
- [ ] 实现用户偏好设置同步
- [ ] 实现增量同步逻辑
- [ ] 实现冲突解决策略

**离线支持（可选）**:
- [ ] 实现本地数据缓存
- [ ] 实现离线浏览
- [ ] 实现离线编辑
- [ ] 实现自动同步

**文件上传**:
- [ ] 实现本地文件存储
- [ ] 实现图片上传
- [ ] 实现图片压缩
- [ ] 实现语音文件存储

**API接口**:
- [ ] POST /api/v1/sync/push - 推送数据
- [ ] GET /api/v1/sync/pull - 拉取数据
- [ ] GET /api/v1/sync/status - 同步状态

**验收标准**:
- ✅ 数据自动保存到云端
- ✅ 不同设备登录可以看到相同数据
- ✅ 图片可以上传和显示
- ✅ 数据修改实时同步

**测试验证**:
```bash
# 测试数据同步
curl -X POST http://localhost:3000/api/v1/sync/push \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d @sync-data.json
```

---

### 阶段9: 测试与Bug修复（4-5天）

**目标**: 全面测试系统，修复Bug，确保系统稳定性

**任务清单**:

**单元测试**:
- [ ] 后端Service层单元测试
- [ ] 后端Controller层单元测试
- [ ] 前端组件单元测试
- [ ] 前端Hook单元测试
- [ ] 测试覆盖率>70%

**集成测试**:
- [ ] API接口集成测试
- [ ] 数据库操作测试
- [ ] 第三方服务集成测试
- [ ] WebSocket通信测试

**E2E测试**:
- [ ] 用户注册登录流程
- [ ] 行程创建和编辑流程
- [ ] 费用管理流程
- [ ] 语音交互流程

**功能测试**:
- [ ] 测试所有核心功能
- [ ] 测试边界情况
- [ ] 测试错误处理
- [ ] 测试性能

**兼容性测试**:
- [ ] 测试Chrome浏览器
- [ ] 测试Safari浏览器
- [ ] 测试Firefox浏览器
- [ ] 测试移动端浏览器

**Bug修复**:
- [ ] 收集和整理Bug清单
- [ ] 按优先级修复Bug
- [ ] 回归测试
- [ ] 确认所有Bug已解决

**验收标准**:
- ✅ 所有单元测试通过
- ✅ 所有集成测试通过
- ✅ E2E测试通过
- ✅ 无严重Bug和阻塞性Bug
- ✅ 测试覆盖率达标

**测试验证**:
```bash
# 运行所有测试
npm run test

# 运行E2E测试
npm run test:e2e

# 生成测试覆盖率报告
npm run test:coverage
```

---

### 阶段10: Docker部署与CI/CD（3-4天）

**目标**: 容器化部署，搭建CI/CD流程，发布到阿里云

**任务清单**:

**Docker化**:
- [ ] 编写前端Dockerfile
- [ ] 编写后端Dockerfile
- [ ] 编写docker-compose.yml（生产环境）
- [ ] 优化镜像大小（多阶段构建）
- [ ] 配置环境变量

**CI/CD流程**:
- [ ] 配置GitHub Actions工作流
- [ ] 自动运行测试
- [ ] 自动构建Docker镜像
- [ ] 推送到阿里云容器镜像仓库
- [ ] 自动部署（可选）

**部署配置**:
- [ ] 配置Nginx反向代理
- [ ] 配置HTTPS证书
- [ ] 配置数据库连接
- [ ] 配置Redis连接
- [ ] 配置API Key管理

**监控与日志**:
- [ ] 配置应用日志
- [ ] 配置错误监控
- [ ] 配置性能监控
- [ ] 配置健康检查

**文档**:
- [ ] 编写部署文档
- [ ] 编写环境配置说明
- [ ] 编写API Key获取说明
- [ ] 编写故障排查指南

**验收标准**:
- ✅ 可以通过Docker一键部署
- ✅ GitHub提交自动触发CI/CD
- ✅ Docker镜像成功推送到阿里云
- ✅ 应用可以公网访问
- ✅ HTTPS配置正常
- ✅ 所有功能在生产环境正常工作

**测试验证**:
```bash
# 构建Docker镜像
docker build -t llm4se-03:latest .

# 运行Docker容器
docker-compose -f docker-compose.prod.yml up -d

# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

---

### 阶段11: 文档与交付（2-3天）

**目标**: 完善文档，准备项目交付

**任务清单**:

**用户文档**:
- [ ] 编写用户使用指南
- [ ] 录制功能演示视频
- [ ] 编写FAQ
- [ ] 准备功能截图

**开发文档**:
- [ ] 更新README.md
- [ ] 编写架构设计文档
- [ ] 编写API文档（Swagger/OpenAPI）
- [ ] 编写数据库设计文档
- [ ] 编写模块说明文档

**部署文档**:
- [ ] 编写Docker部署指南
- [ ] 编写环境配置说明
- [ ] 编写API Key配置说明
- [ ] 编写故障排查指南

**提交准备**:
- [ ] 准备API Key（3个月有效期）
- [ ] 编写项目说明PDF
- [ ] 包含GitHub repo地址
- [ ] 包含Docker镜像下载地址
- [ ] 包含演示视频链接
- [ ] 整理Git提交历史

**代码审查**:
- [ ] 移除所有硬编码的API Key
- [ ] 移除测试代码和注释
- [ ] 统一代码风格
- [ ] 添加必要的注释

**验收标准**:
- ✅ README文档完整清晰
- ✅ 可以根据文档成功部署
- ✅ API文档完整准确
- ✅ 代码中无API Key泄露
- ✅ Git提交历史完整
- ✅ 提交PDF包含所有必要信息

---

## 四、项目时间线总结

| 阶段 | 任务 | 预计时间 | 累计时间 |
|-----|------|---------|---------|
| 阶段0 | 项目初始化 | 1-2天 | 2天 |
| 阶段1 | 用户认证系统 | 3-4天 | 6天 |
| 阶段2 | LLM-Agent模块 | 5-6天 | 12天 |
| 阶段3 | 地图模块 | 4-5天 | 17天 |
| 阶段4 | 语音模块 | 4-5天 | 22天 |
| 阶段5 | 行程管理 | 3-4天 | 26天 |
| 阶段6 | 费用管理 | 3-4天 | 30天 |
| 阶段7 | UI/UX优化 | 3-4天 | 34天 |
| 阶段8 | 云端同步 | 2-3天 | 37天 |
| 阶段9 | 测试与修复 | 4-5天 | 42天 |
| 阶段10 | Docker与CI/CD | 3-4天 | 46天 |
| 阶段11 | 文档与交付 | 2-3天 | **49天** |

**总计**: 约**6-7周**完成全部开发和交付

---

## 五、风险与应对

### 5.1 技术风险

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| LLM API调用失败或超时 | 行程生成失败 | 实现重试机制、降级策略、错误提示 |
| 第三方API限额或限流 | 功能受限 | 实现请求缓存、批量处理、升级套餐 |
| AG-UI协议兼容性问题 | LLM交互异常 | 详细测试、协议版本控制、备选方案 |
| 语音识别准确率低 | 用户体验差 | 提供文字输入备选、优化语音参数 |
| 地图API配额超限 | 地图功能不可用 | 合理缓存、控制调用频率 |

### 5.2 进度风险

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 某个模块开发超时 | 整体进度延迟 | 预留缓冲时间、及时调整优先级 |
| 第三方服务申请延迟 | 开发阻塞 | 提前申请、准备备选方案 |
| Bug修复时间超预期 | 交付延期 | 持续测试、及早发现问题 |

### 5.3 质量风险

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 测试不充分 | 生产环境故障 | 建立完整测试体系、提高覆盖率 |
| 安全漏洞 | 数据泄露 | 安全审计、输入验证、权限控制 |
| 性能问题 | 用户体验差 | 性能测试、代码优化、缓存策略 |

---

## 六、附录

### 6.1 需要申请的第三方服务

- [x] **阿里云百炼平台**: https://bailian.console.aliyun.com/
- [x] **科大讯飞开放平台**: https://www.xfyun.cn/
- [x] **百度地图开放平台**: https://lbsyun.baidu.com/
- [x] **阿里云容器镜像服务**: https://cr.console.aliyun.com/

### 6.2 开发工具推荐

- **IDE**: VS Code / WebStorm
- **API测试**: Postman / Insomnia
- **数据库管理**: DBeaver / TablePlus
- **版本控制**: GitHub Desktop / SourceTree
- **原型设计**: Figma / Sketch
- **项目管理**: GitHub Projects / Trello

### 6.3 学习资源

- **AG-UI协议**: https://docs.ag-ui.com/introduction，仓库中 doc/AG-UI.txt
- **React官方文档**: https://react.dev/
- **TypeScript官方文档**: https://www.typescriptlang.org/
- **Prisma文档**: https://www.prisma.io/docs/
- **百度地图API文档**: https://lbsyun.baidu.com/index.php?title=jspopularGL
- **科大讯飞Web API文档**: https://www.xfyun.cn/doc/

