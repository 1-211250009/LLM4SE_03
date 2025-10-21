# AI旅行规划师 - 快速开始指南

## 概述

本指南将帮助你快速搭建开发环境并开始开发AI旅行规划师项目。

---

## 一、前置准备

### 1.1 开发工具

请确保已安装以下工具：

#### 前端开发
- [ ] **Node.js** >= 20.0.0 ([下载](https://nodejs.org/))
- [ ] **npm** >= 9.0.0 或 **pnpm** >= 8.0.0

#### 后端开发
- [ ] **Python** >= 3.11 ([下载](https://www.python.org/downloads/))
- [ ] **Poetry** >= 1.7.0 ([安装](https://python-poetry.org/docs/#installation))

#### 通用工具
- [ ] **Docker** >= 24.0.0 ([下载](https://www.docker.com/))
- [ ] **Docker Compose** >= 2.0.0
- [ ] **Git** >= 2.40.0
- [ ] **VS Code** 或其他IDE ([下载](https://code.visualstudio.com/))

验证安装：
```bash
# 前端工具
node --version
npm --version

# 后端工具
python --version   # 应该 >= 3.11
poetry --version

# 通用工具
docker --version
docker-compose --version
git --version
```

### 1.2 第三方服务账号

在开始开发前，请注册并获取以下服务的API密钥：

#### 必需服务
1. **阿里云百炼平台** - LLM服务
   - 注册地址：https://bailian.console.aliyun.com/
   - 获取API Key
   - 记录：`ALIYUN_LLM_API_KEY`

2. **科大讯飞开放平台** - 语音识别和合成
   - 注册地址：https://www.xfyun.cn/
   - 创建应用，选择"语音听写(流式版)"和"在线语音合成"
   - 记录：`XFYUN_APP_ID`、`XFYUN_API_KEY`、`XFYUN_API_SECRET`

3. **百度地图开放平台** - 地图和POI服务
   - 注册地址：https://lbsyun.baidu.com/
   - 创建应用，选择"Web端(JSAPI GL)"和"Web服务API"
   - 记录：`BAIDU_MAP_AK`、`BAIDU_MAP_SK`

#### 可选服务
4. **文件存储** - 本地存储（可选，可后续添加）
   - 实现本地文件上传
   - 实现图片压缩

---

## 二、项目初始化

### 2.1 克隆/创建项目

```bash
# 如果是新项目，在GitHub创建仓库后克隆
git clone git@github.com:1-211250009/LLM4SE_03.git
cd LLM4SE_03

# 或者在本地初始化
mkdir LLM4SE_03
cd LLM4SE_03
git init
```

### 2.2 创建项目基础结构

```bash
# 创建主要目录
mkdir -p frontend backend docker docs scripts

# 创建配置文件
touch .gitignore .dockerignore .editorconfig
touch README.md CHANGELOG.md LICENSE
```

### 2.3 配置 `.gitignore`

创建 `.gitignore` 文件：

```gitignore
# 依赖
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# 环境变量
.env
.env.local
.env.*.local
*.env

# 构建输出
dist/
build/
out/
.next/

# 日志
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# 测试
coverage/
.nyc_output/

# 数据库
*.db
*.sqlite

# Docker
docker-compose.override.yml

# 其他
.cache/
.temp/
tmp/
```

---

## 三、后端项目初始化（Python + FastAPI）

### 3.1 初始化Python项目

```bash
cd backend

# 创建Python项目（使用Poetry）
poetry init --name llm4se-03-backend --python "^3.11"

# 或者直接创建pyproject.toml文件
```

### 3.2 安装依赖

```bash
# 核心依赖
poetry add fastapi uvicorn[standard]
poetry add sqlalchemy alembic
poetry add pydantic pydantic-settings
poetry add python-jose[cryptography]  # JWT
poetry add passlib[bcrypt]             # 密码加密
poetry add python-multipart            # 文件上传
poetry add slowapi                     # API限流
poetry add redis                       # Redis客户端
poetry add httpx                       # HTTP客户端

# AG-UI协议相关（Python SDK）
poetry add ag-ui-protocol  # 如果可用，或手动实现

# 开发依赖
poetry add --group dev pytest pytest-asyncio pytest-cov
poetry add --group dev black ruff mypy
poetry add --group dev httpx  # 用于测试

# 如果没有Poetry，使用pip
pip install fastapi uvicorn[standard] sqlalchemy alembic pydantic
```

### 3.3 创建pyproject.toml

创建 `pyproject.toml`（或通过`poetry init`生成）：

```toml
[tool.poetry]
name = "llm4se-03-backend"
version = "1.0.0"
description = "AI Travel Planner Backend API"
authors = ["Krisdar <your.email@example.com>"]
python = "^3.11"

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
psycopg2-binary = "^2.9.9"  # PostgreSQL驱动

[tool.poetry.group.dev.dependencies]
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

### 3.4 配置数据库（SQLAlchemy + Alembic）

**创建基础模型** `app/models/base.py`：

```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

**创建User模型** `app/models/user.py`：

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
```

**初始化Alembic**：

```bash
# 初始化Alembic（数据库迁移工具）
alembic init alembic

# 编辑 alembic.ini，设置数据库URL
# 或使用环境变量
```

### 3.5 配置环境变量

创建 `.env` 文件：

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
ALIYUN_LLM_API_KEY=your_aliyun_llm_api_key
ALIYUN_LLM_ENDPOINT=https://dashscope.aliyuncs.com/api/v1

# 科大讯飞
XFYUN_APP_ID=your_xfyun_app_id
XFYUN_API_KEY=your_xfyun_api_key
XFYUN_API_SECRET=your_xfyun_api_secret

# 百度地图
BAIDU_MAP_AK=your_baidu_map_ak
BAIDU_MAP_SK=your_baidu_map_sk

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# 日志
LOG_LEVEL=INFO
```

创建 `.env.example`（不包含真实密钥）：

```bash
cp .env .env.example
# 编辑.env.example，将所有密钥替换为占位符
```

### 3.6 创建基础代码结构

```bash
# 创建目录结构
mkdir -p app/{api/v1/endpoints,services,models,schemas,core,middleware,utils}
mkdir -p app/services/{llm/agents,voice,map}
mkdir -p tests/{unit,integration}
mkdir -p alembic/versions

# 创建__init__.py文件
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/services/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/core/__init__.py
touch app/middleware/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py

# 创建入口文件
touch app/main.py
```

**创建FastAPI应用** `app/main.py`：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="AI Travel Planner API",
    description="基于AG-UI协议的AI旅行规划师后端服务",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT
    }

# API路由
@app.get("/api/v1")
async def api_info():
    return {
        "message": "AI Travel Planner API v1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
```

**创建配置文件** `app/core/config.py`：

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 服务配置
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # 数据库
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30天
    
    # 第三方API
    ALIYUN_LLM_API_KEY: str = ""
    XFYUN_APP_ID: str = ""
    BAIDU_MAP_AK: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # 日志
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 3.8 启动Docker服务

创建 `docker-compose.dev.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: travel-planner-postgres
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

  redis:
    image: redis:7-alpine
    container_name: travel-planner-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

启动数据库服务：

```bash
# 从项目根目录
docker-compose -f docker-compose.dev.yml up -d

# 检查服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 3.7 配置数据库连接

**创建数据库配置** `app/core/database.py`：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.ENVIRONMENT == "development"
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 依赖注入：获取数据库会话
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.8 初始化Alembic迁移

```bash
cd backend

# 初始化Alembic
alembic init alembic

# 编辑 alembic/env.py，配置数据库连接
# 创建第一个迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 3.9 启动后端服务

```bash
# 开发模式（自动重载）
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用python直接运行
python app/main.py

# 或简化命令（在pyproject.toml中配置）
poetry run dev
```

测试后端服务：

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试API
curl http://localhost:8000/api/v1

# 查看自动生成的API文档
open http://localhost:8000/docs
```

---

## 四、前端项目初始化

### 4.1 创建Vite + React项目

```bash
cd frontend

# 使用Vite创建React + TypeScript项目
npm create vite@latest . -- --template react-ts

# 或者使用pnpm
pnpm create vite . -- --template react-ts
```

### 4.2 安装依赖

```bash
# 核心依赖
npm install react-router-dom axios zustand
npm install @tanstack/react-query
npm install antd @ant-design/icons
npm install dayjs

# AG-UI协议相关
npm install rxjs                           # Observable流处理
npm install @microsoft/fetch-event-source  # SSE客户端（支持POST）
npm install fast-json-patch                # JSON Patch操作

# 工具库
npm install react-hook-form zod
npm install framer-motion

# 开发依赖
npm install -D tailwindcss postcss autoprefixer
npm install -D @types/node
npm install -D eslint prettier
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

### 4.3 配置 TailwindCSS

```bash
# 初始化Tailwind
npx tailwindcss init -p
```

编辑 `tailwind.config.js`：

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
          100: '#e0f2fe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
```

在 `src/index.css` 添加：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 4.4 配置 Vite

编辑 `vite.config.ts`：

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
})
```

### 4.5 配置环境变量

创建 `.env` 文件：

```bash
# API配置
VITE_API_BASE_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:3000

# 百度地图
VITE_BAIDU_MAP_AK=your_baidu_map_ak

# 功能开关
VITE_ENABLE_VOICE=true
VITE_ENABLE_MAP=true
```

### 4.6 创建基础代码结构

```bash
cd src

# 创建目录结构
mkdir -p pages components/{layout,common} modules/{voice,map,llm}
mkdir -p services store hooks utils types styles config

# 创建基础文件
touch router.tsx
```

创建 `src/router.tsx`：

```typescript
import { createBrowserRouter } from 'react-router-dom';
import App from './App';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <div>Home Page - Coming Soon</div>,
      },
    ],
  },
]);
```

更新 `src/main.tsx`：

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { router } from './router'
import './index.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)
```

更新 `src/App.tsx`：

```typescript
import { Outlet } from 'react-router-dom'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">
            AI Travel Planner
          </h1>
        </div>
      </header>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default App
```

### 4.7 配置 package.json scripts

编辑 `package.json`：

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "lint": "eslint src --ext ts,tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx}\""
  }
}
```

### 4.8 启动前端服务

```bash
npm run dev
```

访问 http://localhost:5173

---

## 五、验证开发环境

### 5.1 检查清单

- [ ] 后端服务运行正常 (http://localhost:3000)
- [ ] 前端服务运行正常 (http://localhost:5173)
- [ ] PostgreSQL数据库连接成功
- [ ] Redis连接成功
- [ ] Prisma Studio可以打开
- [ ] 前端可以调用后端API（通过代理）

### 5.2 测试API连接

在前端创建测试组件：

```typescript
// src/pages/TestAPI.tsx
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function TestAPI() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    axios.get('/api/v1')
      .then(res => setData(res.data))
      .catch(err => setError(err.message));
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">API连接测试</h2>
      {data && <pre className="bg-gray-100 p-4 rounded">{JSON.stringify(data, null, 2)}</pre>}
      {error && <div className="text-red-500">Error: {error}</div>}
    </div>
  );
}
```

---

## 六、开发工具推荐

### VS Code 扩展

安装以下VS Code扩展以提升开发效率：

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "prisma.prisma",
    "bradlc.vscode-tailwindcss",
    "dsznajder.es7-react-js-snippets",
    "ms-vscode.vscode-typescript-next",
    "christian-kohler.path-intellisense",
    "wayou.vscode-todo-highlight"
  ]
}
```

创建 `.vscode/settings.json`：

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
    ["cx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ]
}
```

---

## 七、Git工作流设置

### 7.1 配置Git

```bash
# 设置用户信息
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 设置默认分支名
git config init.defaultBranch main
```

### 7.2 创建分支策略

```bash
# 创建开发分支
git checkout -b develop

# 创建功能分支（从develop分支）
git checkout -b feature/user-auth
git checkout -b feature/trip-planning
git checkout -b feature/voice-input
```

### 7.3 配置提交钩子

安装Husky：

```bash
# 在项目根目录
npm install -D husky lint-staged

# 初始化Husky
npx husky init
```

配置 `.husky/pre-commit`：

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

npx lint-staged
```

在根目录 `package.json` 添加：

```json
{
  "lint-staged": {
    "frontend/src/**/*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "backend/src/**/*.ts": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

---

## 八、下一步

现在你的开发环境已经搭建完成！接下来可以：

1. **阅读技术设计文档** - `TECHNICAL_DESIGN.md`
2. **查看项目结构** - `PROJECT_STRUCTURE.md`
3. **开始开发第一个功能** - 建议从用户认证系统开始（阶段1）
4. **编写测试** - 确保代码质量

### 推荐开发顺序

```
✅ 阶段0: 项目初始化（已完成）
→ 阶段1: 用户认证系统
→ 阶段2: LLM-Agent模块
→ 阶段3: 地图模块
→ 阶段4: 语音模块
→ ...
```

---

## 八、AG-UI协议快速入门

本项目使用AG-UI协议实现前端与AI Agent的通信。以下是快速入门指南。

### 8.1 AG-UI协议核心概念

**AG-UI（Agent User Interaction Protocol）** 是一个开放、轻量、事件驱动的协议。

**核心特性**:
- 📡 **事件驱动** - 16种标准事件类型
- 🌊 **流式响应** - 实时显示AI生成内容
- 🔧 **前端工具** - Agent可以调用前端能力
- 🔄 **状态同步** - 前后端状态实时同步

**详细文档**: 参见 [`doc/AG-UI_IMPLEMENTATION.md`](./AG-UI_IMPLEMENTATION.md)

### 8.2 后端：实现AG-UI Agent

**步骤1**: 定义AG-UI类型

```typescript
// src/services/llm/types/agui.types.ts
export enum EventType {
  RUN_STARTED = 'RUN_STARTED',
  RUN_FINISHED = 'RUN_FINISHED',
  TEXT_MESSAGE_CHUNK = 'TEXT_MESSAGE_CHUNK',
  // ... 其他事件类型
}

export interface BaseEvent {
  type: EventType;
  timestamp?: number;
}

export interface RunAgentInput {
  threadId: string;
  runId: string;
  messages: Message[];
  tools: Tool[];
  state: any;
  context: Context[];
}
```

**步骤2**: 实现Agent类

```typescript
// src/services/llm/agents/trip-planner.agent.ts
import { Observable } from 'rxjs';
import { AbstractAgent } from './abstract-agent';

export class TripPlannerAgent extends AbstractAgent {
  run(input: RunAgentInput): Observable<BaseEvent> {
    return new Observable<BaseEvent>((observer) => {
      // 1. 发出RUN_STARTED
      observer.next({
        type: EventType.RUN_STARTED,
        threadId: input.threadId,
        runId: input.runId,
      });
      
      // 2. 调用LLM，流式返回内容
      // 3. 发出TEXT_MESSAGE_CHUNK事件
      observer.next({
        type: EventType.TEXT_MESSAGE_CHUNK,
        messageId: 'msg_123',
        delta: 'AI生成的内容...',
      });
      
      // 4. 发出RUN_FINISHED
      observer.next({
        type: EventType.RUN_FINISHED,
        threadId: input.threadId,
        runId: input.runId,
      });
      
      observer.complete();
    });
  }
}
```

**步骤3**: 创建HTTP端点（SSE）

```typescript
// src/routes/agent.routes.ts
router.post('/trip-planner', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  
  const agent = new TripPlannerAgent();
  const eventStream = agent.run(req.body);
  
  eventStream.subscribe({
    next: (event) => {
      // SSE格式: data: {JSON}\n\n
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    },
    complete: () => res.end(),
  });
});
```

### 8.3 前端：连接AG-UI Agent

**步骤1**: 安装依赖

```bash
npm install rxjs @microsoft/fetch-event-source
```

**步骤2**: 实现SSE客户端

```typescript
// src/modules/llm/services/agui-client.service.ts
import { fetchEventSource } from '@microsoft/fetch-event-source';

export class AguiClientService {
  async runAgent(agentName: string, input: RunAgentInput, handlers: any) {
    await fetchEventSource(`/api/v1/agent/${agentName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(input),
      
      onmessage: (event) => {
        const parsedEvent = JSON.parse(event.data);
        
        // 处理TEXT_MESSAGE_CHUNK事件
        if (parsedEvent.type === 'TEXT_MESSAGE_CHUNK') {
          handlers.onTextMessage?.(parsedEvent.delta);
        }
      },
    });
  }
}
```

**步骤3**: 创建React Hook

```typescript
// src/modules/llm/hooks/useAgent.ts
export function useAgent(agentName: string) {
  const [text, setText] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  
  const runAgent = useCallback(async (userMessage: string) => {
    setIsRunning(true);
    setText('');
    
    const input = {
      threadId: 'thread-1',
      runId: `run_${Date.now()}`,
      messages: [{ id: 'msg-1', role: 'user', content: userMessage }],
      tools: [], // 工具定义
      state: {},
      context: [],
    };
    
    await client.runAgent(agentName, input, {
      onTextMessage: (delta) => setText((prev) => prev + delta),
    });
    
    setIsRunning(false);
  }, [agentName]);
  
  return { runAgent, text, isRunning };
}
```

**步骤4**: 在组件中使用

```typescript
function PlanningPage() {
  const { runAgent, text, isRunning } = useAgent('trip-planner');
  
  return (
    <div>
      <button onClick={() => runAgent('帮我规划东京5日游')}>
        开始规划
      </button>
      
      {isRunning && <div>规划中...</div>}
      <div>{text}</div>
    </div>
  );
}
```

### 8.4 定义前端工具

```typescript
// src/modules/llm/tools/tool-registry.ts
export const searchPOITool = {
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

// 工具执行器
export async function executeSearchPOI(args: any): Promise<string> {
  const results = await baiduMapAPI.search(args.keyword, args.city);
  return JSON.stringify({ success: true, data: results });
}
```

### 8.5 测试AG-UI连接

```bash
# 测试后端AG-UI端点
curl -N -X POST http://localhost:3000/api/v1/agent/trip-planner \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "threadId": "test",
    "runId": "run1",
    "messages": [{"id":"msg1","role":"user","content":"你好"}],
    "tools": [],
    "state": {},
    "context": []
  }'

# 预期输出（SSE流）:
# data: {"type":"RUN_STARTED","thread_id":"test","run_id":"run1"}
# data: {"type":"TEXT_MESSAGE_CHUNK","message_id":"msg_123","delta":"你好！"}
# data: {"type":"RUN_FINISHED","thread_id":"test","run_id":"run1"}
```

### 8.6 AG-UI关键文档

- **完整实现指南**: [`doc/AG-UI_IMPLEMENTATION.md`](./AG-UI_IMPLEMENTATION.md)
- **协议规范**: [`doc/AG-UI.txt`](./AG-UI.txt)
- **官方文档**: https://docs.ag-ui.com/

---

## 九、常见问题

### Q1: 数据库连接失败
```bash
# 检查Docker容器状态
docker-compose ps

# 查看PostgreSQL日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### Q2: 前端无法调用后端API
- 检查后端服务是否运行在3000端口
- 检查Vite代理配置
- 查看浏览器控制台和Network标签

### Q3: Prisma命令失败
```bash
# 重新生成Prisma Client
npx prisma generate

# 重置数据库
npx prisma migrate reset
```

### Q4: 端口被占用
```bash
# 查找占用端口的进程
lsof -i :3000
lsof -i :5173

# 杀死进程
kill -9 <PID>
```

---

## 十、资源链接

### 项目文档
- **技术设计**: `doc/TECHNICAL_DESIGN.md`
- **项目结构**: `doc/PROJECT_STRUCTURE.md`
- **开发清单**: `doc/CHECKLIST.md`
- **AG-UI实现指南**: `doc/AG-UI_IMPLEMENTATION.md`
- **AG-UI协议规范**: `doc/AG-UI.txt`

### 核心技术文档
- **AG-UI协议官网**: https://docs.ag-ui.com/
- **React官方文档**: https://react.dev/
- **Express文档**: https://expressjs.com/)
- **Prisma文档**: https://www.prisma.io/docs/
- **RxJS文档**: https://rxjs.dev/
- **Ant Design**: https://ant.design/

### 第三方服务
- **阿里云百炼平台**: https://bailian.console.aliyun.com/
- **科大讯飞开放平台**: https://www.xfyun.cn/
- **百度地图开放平台**: https://lbsyun.baidu.com/

---

**祝你开发顺利！🚀**

如有问题，请查看技术设计文档或创建Issue。

