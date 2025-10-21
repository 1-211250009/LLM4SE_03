# AI旅行规划师 - 项目结构

## 完整项目目录结构

```
LLM4SE_03/
├── frontend/                           # 前端项目
│   ├── public/                         # 静态资源
│   │   ├── favicon.ico
│   │   ├── logo.png
│   │   └── assets/                     # 图片、图标等
│   ├── src/
│   │   ├── main.tsx                    # 应用入口
│   │   ├── App.tsx                     # 根组件
│   │   ├── router.tsx                  # 路由配置
│   │   │
│   │   ├── pages/                      # 页面组件
│   │   │   ├── Home/
│   │   │   │   ├── index.tsx
│   │   │   │   ├── Home.module.css
│   │   │   │   └── components/
│   │   │   ├── Auth/
│   │   │   │   ├── Login.tsx
│   │   │   │   ├── Register.tsx
│   │   │   │   └── ForgotPassword.tsx
│   │   │   ├── TripPlanning/
│   │   │   │   ├── index.tsx
│   │   │   │   ├── VoiceInput.tsx
│   │   │   │   ├── PlanningProgress.tsx
│   │   │   │   └── ResultPreview.tsx
│   │   │   ├── TripDetail/
│   │   │   │   ├── index.tsx
│   │   │   │   ├── ItineraryTimeline.tsx
│   │   │   │   ├── MapView.tsx
│   │   │   │   └── POIList.tsx
│   │   │   ├── TripList/
│   │   │   │   ├── index.tsx
│   │   │   │   └── TripCard.tsx
│   │   │   ├── BudgetManagement/
│   │   │   │   ├── index.tsx
│   │   │   │   ├── BudgetOverview.tsx
│   │   │   │   ├── ExpenseList.tsx
│   │   │   │   ├── ExpenseForm.tsx
│   │   │   │   └── BudgetAnalysis.tsx
│   │   │   └── Profile/
│   │   │       ├── index.tsx
│   │   │       ├── UserInfo.tsx
│   │   │       ├── Settings.tsx
│   │   │       └── APIKeyConfig.tsx
│   │   │
│   │   ├── components/                 # 通用组件
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── MainLayout.tsx
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Dropdown.tsx
│   │   │   │   ├── Loading.tsx
│   │   │   │   ├── Empty.tsx
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   └── Toast.tsx
│   │   │   ├── trip/
│   │   │   │   ├── TripCard.tsx
│   │   │   │   ├── POICard.tsx
│   │   │   │   ├── RouteCard.tsx
│   │   │   │   └── DayPlanner.tsx
│   │   │   └── budget/
│   │   │       ├── BudgetChart.tsx
│   │   │       ├── ExpenseItem.tsx
│   │   │       ├── CategoryPicker.tsx
│   │   │       └── BudgetProgress.tsx
│   │   │
│   │   ├── modules/                    # 功能模块
│   │   │   ├── voice/                  # 语音模块
│   │   │   │   ├── components/
│   │   │   │   │   ├── VoiceButton.tsx
│   │   │   │   │   ├── VoiceWave.tsx
│   │   │   │   │   ├── VoiceFeedback.tsx
│   │   │   │   │   └── RecordingStatus.tsx
│   │   │   │   ├── services/
│   │   │   │   │   ├── xfyun-asr.service.ts
│   │   │   │   │   ├── xfyun-tts.service.ts
│   │   │   │   │   ├── audio-recorder.service.ts
│   │   │   │   │   └── voice-manager.service.ts
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useVoiceInput.ts
│   │   │   │   │   ├── useVoiceOutput.ts
│   │   │   │   │   └── useAudioRecorder.ts
│   │   │   │   ├── utils/
│   │   │   │   │   ├── audio-processor.ts
│   │   │   │   │   ├── pcm-converter.ts
│   │   │   │   │   └── vad-detector.ts
│   │   │   │   └── types/
│   │   │   │       └── voice.types.ts
│   │   │   │
│   │   │   ├── map/                    # 地图模块
│   │   │   │   ├── components/
│   │   │   │   │   ├── MapContainer.tsx
│   │   │   │   │   ├── RouteOverlay.tsx
│   │   │   │   │   ├── POIMarker.tsx
│   │   │   │   │   ├── InfoWindow.tsx
│   │   │   │   │   ├── SearchBox.tsx
│   │   │   │   │   └── MapControls.tsx
│   │   │   │   ├── services/
│   │   │   │   │   ├── baidu-map.service.ts
│   │   │   │   │   ├── geocoding.service.ts
│   │   │   │   │   ├── poi-search.service.ts
│   │   │   │   │   └── route-planning.service.ts
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useMap.ts
│   │   │   │   │   ├── usePOISearch.ts
│   │   │   │   │   ├── useRouteCalc.ts
│   │   │   │   │   └── useMapControls.ts
│   │   │   │   └── types/
│   │   │   │       ├── map.types.ts
│   │   │   │       ├── poi.types.ts
│   │   │   │       └── route.types.ts
│   │   │   │
│   │   │   └── llm/                    # LLM交互模块（AG-UI协议）
│   │   │       ├── components/
│   │   │       │   ├── ChatInterface.tsx
│   │   │       │   ├── StreamingResponse.tsx
│   │   │       │   ├── PlanningVisualization.tsx
│   │   │       │   └── ToolCallDisplay.tsx
│   │   │       ├── services/
│   │   │       │   ├── agui-agent.service.ts    # AG-UI Agent客户端
│   │   │       │   ├── sse-client.service.ts    # EventSource SSE客户端
│   │   │       │   └── event-handler.service.ts # AG-UI事件处理器
│   │   │       ├── subscribers/         # AG-UI事件订阅器
│   │   │       │   ├── message.subscriber.ts
│   │   │       │   ├── tool.subscriber.ts
│   │   │       │   └── state.subscriber.ts
│   │   │       ├── tools/               # 前端工具定义
│   │   │       │   ├── tool-registry.ts
│   │   │       │   └── tool-executor.ts
│   │   │       ├── hooks/
│   │   │       │   ├── useAgent.ts              # 通用Agent Hook
│   │   │       │   ├── useTripPlanner.ts        # 行程规划Agent Hook
│   │   │       │   ├── useBudgetAnalyzer.ts     # 费用分析Agent Hook
│   │   │       │   └── useAgentSubscriber.ts    # 事件订阅Hook
│   │   │       └── types/
│   │   │           ├── agui.types.ts     # AG-UI协议类型
│   │   │           ├── events.types.ts   # 事件类型定义
│   │   │           └── agent.types.ts    # Agent业务类型
│   │   │
│   │   ├── store/                      # 状态管理
│   │   │   ├── auth.store.ts
│   │   │   ├── trip.store.ts
│   │   │   ├── budget.store.ts
│   │   │   ├── map.store.ts
│   │   │   ├── voice.store.ts
│   │   │   └── app.store.ts
│   │   │
│   │   ├── services/                   # API服务
│   │   │   ├── api.service.ts
│   │   │   ├── auth.service.ts
│   │   │   ├── trip.service.ts
│   │   │   ├── budget.service.ts
│   │   │   ├── user.service.ts
│   │   │   └── upload.service.ts
│   │   │
│   │   ├── hooks/                      # 通用Hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useTrip.ts
│   │   │   ├── useBudget.ts
│   │   │   ├── useDebounce.ts
│   │   │   ├── useThrottle.ts
│   │   │   └── useLocalStorage.ts
│   │   │
│   │   ├── utils/                      # 工具函数
│   │   │   ├── format.ts
│   │   │   ├── validation.ts
│   │   │   ├── storage.ts
│   │   │   ├── date.ts
│   │   │   ├── currency.ts
│   │   │   └── request.ts
│   │   │
│   │   ├── types/                      # 类型定义
│   │   │   ├── api.types.ts
│   │   │   ├── trip.types.ts
│   │   │   ├── budget.types.ts
│   │   │   ├── user.types.ts
│   │   │   └── common.types.ts
│   │   │
│   │   ├── styles/                     # 样式文件
│   │   │   ├── globals.css
│   │   │   ├── variables.css
│   │   │   ├── reset.css
│   │   │   └── animations.css
│   │   │
│   │   └── config/                     # 配置文件
│   │       ├── env.ts
│   │       ├── api.config.ts
│   │       ├── map.config.ts
│   │       └── constants.ts
│   │
│   ├── tests/                          # 测试
│   │   ├── unit/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── utils/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── .env.example                    # 环境变量示例
│   ├── .eslintrc.json                  # ESLint配置
│   ├── .prettierrc                     # Prettier配置
│   ├── tsconfig.json                   # TypeScript配置
│   ├── vite.config.ts                  # Vite配置
│   ├── tailwind.config.js              # Tailwind配置
│   ├── package.json
│   └── README.md
│
├── backend/                            # 后端项目（Python + FastAPI）
│   ├── app/
│   │   ├── main.py                     # FastAPI应用入口
│   │   │
│   │   ├── api/                        # API路由层
│   │   │   ├── deps.py                 # 依赖注入
│   │   │   └── v1/
│   │   │       ├── api.py              # API路由聚合
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py          # 认证端点
│   │   │           ├── agent.py         # AG-UI Agent端点
│   │   │           ├── user.py          # 用户端点
│   │   │           ├── trip.py          # 行程端点
│   │   │           ├── budget.py        # 费用端点
│   │   │           ├── voice.py         # 语音端点
│   │   │           ├── map.py           # 地图端点
│   │   │           └── sync.py          # 同步端点
│   │   │
│   │   ├── services/                   # 业务逻辑层
│   │   │   ├── llm/                    # LLM Agent服务（AG-UI实现）
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agents/             # AG-UI Agent实现
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── abstract_agent.py        # AbstractAgent基类实现
│   │   │   │   │   ├── trip_planner_agent.py    # 行程规划Agent
│   │   │   │   │   ├── budget_analyzer_agent.py # 费用分析Agent
│   │   │   │   │   └── chat_assistant_agent.py  # 对话助手Agent
│   │   │   │   ├── events/             # AG-UI事件系统
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── event_emitter.py         # 事件发射器
│   │   │   │   │   ├── event_encoder.py         # SSE编码器
│   │   │   │   │   └── event_types.py           # 事件类型定义
│   │   │   │   ├── prompts/            # 提示词模板
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── trip_planning.py
│   │   │   │   │   ├── budget_analysis.py
│   │   │   │   │   └── system_prompt.py
│   │   │   │   ├── tools/              # 工具处理器
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── tool_executor.py         # 工具执行器
│   │   │   │   │   └── tool_validator.py        # 工具验证器
│   │   │   │   └── services/           # LLM服务集成
│   │   │   │       ├── __init__.py
│   │   │   │       ├── aliyun_llm_service.py    # 阿里云LLM API
│   │   │   │       └── message_converter.py     # 消息格式转换
│   │   │   │
│   │   │   ├── voice/                  # 语音服务
│   │   │   │   ├── __init__.py
│   │   │   │   └── xfyun_service.py
│   │   │   │
│   │   │   ├── map/                    # 地图服务
│   │   │   │   ├── __init__.py
│   │   │   │   ├── baidu_map_service.py
│   │   │   │   ├── geocoding_service.py
│   │   │   │   └── poi_search_service.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── trip_service.py
│   │   │   ├── budget_service.py
│   │   │   └── upload_service.py
│   │   │
│   │   ├── models/                     # SQLAlchemy模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── trip.py
│   │   │   ├── budget.py
│   │   │   └── base.py                 # 模型基类
│   │   │
│   │   ├── schemas/                    # Pydantic Schema
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # 认证Schema
│   │   │   ├── user.py                 # 用户Schema
│   │   │   ├── trip.py                 # 行程Schema
│   │   │   ├── budget.py               # 费用Schema
│   │   │   └── agui.py                 # AG-UI协议Schema
│   │   │
│   │   ├── middleware/                 # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # JWT认证
│   │   │   ├── rate_limit.py           # 限流
│   │   │   └── error_handler.py        # 错误处理
│   │   │
│   │   ├── core/                       # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # 配置管理
│   │   │   ├── security.py             # JWT、密码加密
│   │   │   └── database.py             # 数据库连接
│   │   │
│   │   └── utils/                      # 工具函数
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── validators.py
│   │
│   ├── alembic/                        # 数据库迁移（Alembic）
│   │   ├── versions/                   # 迁移版本
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── tests/                          # 测试
│   │   ├── __init__.py
│   │   ├── conftest.py                 # pytest配置
│   │   ├── unit/
│   │   │   ├── test_services.py
│   │   │   └── test_utils.py
│   │   ├── integration/
│   │   │   ├── test_api.py
│   │   │   └── test_database.py
│   │   └── fixtures/
│   │       └── test_data.py
│   │
│   ├── logs/                           # 日志文件
│   │   └── app.log
│   │
│   ├── .env.example                    # 环境变量示例
│   ├── .env                            # 环境变量（不提交）
│   ├── pyproject.toml                  # Poetry依赖管理
│   ├── poetry.lock                     # 依赖锁定文件
│   ├── pytest.ini                      # pytest配置
│   ├── .python-version                 # Python版本
│   └── README.md
│
├── docker/                             # Docker配置
│   ├── frontend/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   ├── backend/
│   │   └── Dockerfile
│   └── docker-compose.yml
│
├── .github/                            # GitHub配置
│   ├── workflows/
│   │   ├── ci.yml                      # CI工作流
│   │   ├── cd.yml                      # CD工作流
│   │   └── test.yml                    # 测试工作流
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
│
├── docs/                               # 项目文档
│   ├── architecture/
│   │   ├── system-design.md
│   │   ├── database-schema.md
│   │   └── api-design.md
│   ├── deployment/
│   │   ├── docker-guide.md
│   │   ├── environment-setup.md
│   │   └── troubleshooting.md
│   ├── development/
│   │   ├── getting-started.md
│   │   ├── coding-standards.md
│   │   └── git-workflow.md
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── postman-collection.json
│   └── user-guide/
│       ├── user-manual.md
│       └── faq.md
│
├── scripts/                            # 脚本文件
│   ├── setup.sh                        # 环境设置脚本
│   ├── build.sh                        # 构建脚本
│   ├── deploy.sh                       # 部署脚本
│   └── seed-data.sh                    # 数据填充脚本
│
├── .gitignore
├── .dockerignore
├── .editorconfig
├── README.md                           # 项目说明
├── TECHNICAL_DESIGN.md                 # 技术设计文档
├── PROJECT_STRUCTURE.md                # 项目结构文档(本文件)
├── CHANGELOG.md                        # 变更日志
└── LICENSE                             # 许可证
```

## 数据库表结构概览

### 用户相关表

```
users
├── id (UUID, PK)
├── email (String, Unique)
├── password_hash (String)
├── name (String)
├── avatar_url (String?)
├── created_at (DateTime)
├── updated_at (DateTime)
└── deleted_at (DateTime?)

user_preferences
├── id (UUID, PK)
├── user_id (UUID, FK -> users)
├── language (String)
├── currency (String)
├── theme (String)
└── api_keys (JSON)
```

### 行程相关表

```
trips
├── id (UUID, PK)
├── user_id (UUID, FK -> users)
├── title (String)
├── destination (String)
├── start_date (DateTime)
├── end_date (DateTime)
├── days (Int)
├── travelers_count (Int)
├── budget (Decimal)
├── preferences (JSON)
├── status (Enum: draft, planning, confirmed, completed)
├── created_at (DateTime)
└── updated_at (DateTime)

itineraries
├── id (UUID, PK)
├── trip_id (UUID, FK -> trips)
├── day (Int)
├── date (DateTime)
├── title (String)
└── description (String?)

itinerary_items
├── id (UUID, PK)
├── itinerary_id (UUID, FK -> itineraries)
├── order (Int)
├── type (Enum: poi, route, note)
├── start_time (DateTime?)
├── end_time (DateTime?)
├── poi_id (UUID?, FK -> pois)
├── title (String)
├── description (String?)
├── address (String?)
├── location (JSON)  // {lat, lng}
└── metadata (JSON)  // 额外信息

pois
├── id (UUID, PK)
├── name (String)
├── type (Enum: attraction, restaurant, hotel, transport)
├── address (String)
├── location (JSON)  // {lat, lng}
├── phone (String?)
├── website (String?)
├── opening_hours (JSON?)
├── rating (Decimal?)
├── price_level (Int?)
├── images (JSON)
└── metadata (JSON)
```

### 费用相关表

```
budgets
├── id (UUID, PK)
├── trip_id (UUID, FK -> trips)
├── total_budget (Decimal)
├── currency (String)
├── estimated_expenses (JSON)  // 预估费用明细
└── created_at (DateTime)

expenses
├── id (UUID, PK)
├── trip_id (UUID, FK -> trips)
├── budget_id (UUID, FK -> budgets)
├── user_id (UUID, FK -> users)
├── category (Enum: transport, accommodation, food, ticket, shopping, other)
├── amount (Decimal)
├── currency (String)
├── date (DateTime)
├── description (String?)
├── receipt_url (String?)  // 凭证图片
└── created_at (DateTime)

budget_categories
├── id (UUID, PK)
├── budget_id (UUID, FK -> budgets)
├── category (String)
├── allocated_amount (Decimal)
└── spent_amount (Decimal)
```

### AI交互相关表

```
conversations
├── id (UUID, PK)
├── user_id (UUID, FK -> users)
├── trip_id (UUID?, FK -> trips)
├── title (String)
├── created_at (DateTime)
└── updated_at (DateTime)

messages
├── id (UUID, PK)
├── conversation_id (UUID, FK -> conversations)
├── role (Enum: user, assistant, system)
├── content (Text)
├── metadata (JSON)  // 语音、图片等附加信息
└── created_at (DateTime)
```

## 关键配置文件说明

### 前端配置

#### `vite.config.ts`
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@modules': path.resolve(__dirname, './src/modules'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@store': path.resolve(__dirname, './src/store'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:3000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['antd', 'framer-motion'],
          'utils-vendor': ['axios', 'dayjs', 'zustand'],
        },
      },
    },
  },
})
```

#### `tailwind.config.js`
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
        },
      },
    },
  },
  plugins: [],
}
```

### 后端配置

#### `pyproject.toml` (Poetry依赖管理)
```toml
[tool.poetry]
name = "llm4se-03-backend"
version = "1.0.0"
description = "AI Travel Planner Backend API"
authors = ["Krisdar <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.0"
alembic = "^1.13.0"
pydantic = "^2.6.0"
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.9"
slowapi = "^0.1.9"
redis = "^5.0.0"
httpx = "^0.26.0"
ag-ui-protocol = "^0.1.0"  # AG-UI Python SDK

[tool.poetry.dev-dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
black = "^24.0.0"
ruff = "^0.2.0"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### `app/models/user.py` (SQLAlchemy模型)
```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系（后续定义）
    # trips = relationship("Trip", back_populates="user")
```

#### `app/schemas/auth.py` (Pydantic Schema)
```python
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    name: str = Field(min_length=1, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class UserOut(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: str | None = None
    
    class Config:
        from_attributes = True  # Pydantic v2
```

### Docker配置

#### `docker-compose.yml`
```yaml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: travel_planner
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # 后端服务（Python + FastAPI）
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: production
      DATABASE_URL: postgresql://admin:password@postgres:5432/travel_planner
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - app-network

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

## 环境变量配置

### 前端 `.env.example`
```bash
# API配置
VITE_API_BASE_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:3000

# 百度地图
VITE_BAIDU_MAP_AK=your_baidu_map_key

# 功能开关
VITE_ENABLE_VOICE=true
VITE_ENABLE_MAP=true
```

### 后端 `.env` (Python + FastAPI)
```bash
# 服务配置
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0

# 数据库
DATABASE_URL=postgresql://admin:password@localhost:5432/travel_planner

# Redis
REDIS_URL=redis://localhost:6379

# JWT配置
SECRET_KEY=your_secret_key_at_least_32_characters_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7天
REFRESH_TOKEN_EXPIRE_MINUTES=43200  # 30天

# 阿里云百炼平台
ALIYUN_LLM_API_KEY=sk-xxxxxxxxxxxx
ALIYUN_LLM_ENDPOINT=https://dashscope.aliyuncs.com/api/v1

# 科大讯飞
XFYUN_APP_ID=your_app_id
XFYUN_API_KEY=your_api_key
XFYUN_API_SECRET=your_api_secret

# 百度地图
BAIDU_MAP_AK=your_baidu_map_key
BAIDU_MAP_SK=your_baidu_map_secret_key

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# 日志
LOG_LEVEL=INFO
```

## 启动命令

### 开发环境

```bash
# 启动Docker服务（PostgreSQL + Redis）
docker-compose -f docker-compose.dev.yml up -d

# ===== 后端设置 =====
cd backend

# 安装Python依赖（使用Poetry）
poetry install

# 或使用pip
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动后端开发服务器
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或
python -m uvicorn app.main:app --reload

# ===== 前端设置 =====
cd frontend

# 安装依赖
npm install

# 启动前端开发服务器
npm run dev
```

### 生产环境

```bash
# 构建Docker镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f
```

## 测试命令

```bash
# ===== 前端测试 =====
cd frontend
npm run test              # 运行单元测试
npm run test:coverage     # 生成覆盖率报告
npm run test:e2e          # 运行E2E测试

# ===== 后端测试（Python） =====
cd backend
poetry run pytest                    # 运行所有测试
poetry run pytest tests/unit         # 运行单元测试
poetry run pytest tests/integration  # 运行集成测试
poetry run pytest --cov=app          # 生成覆盖率报告

# 或使用pytest直接
pytest
pytest --cov=app --cov-report=html
```

---

**文档版本**: v1.0  
**创建日期**: 2025-10-16

