# AI旅行规划师 (AI Travel Planner)
> 一个基于AI的智能旅行规划Web应用，支持语音交互、智能行程规划、费用管理和多设备同步。

## ✨ 项目特性

- 🤖 **智能行程规划** - 基于大语言模型，根据用户需求自动生成个性化旅行路线
- 🎤 **语音交互** - 支持语音输入旅行需求和语音播报规划结果
- 🗺️ **地图可视化** - 基于百度地图，直观展示行程路线和POI信息
- 💰 **费用管理** - AI辅助预算分析，支持语音记录开销
- ☁️ **云端同步** - 数据云端存储，多设备无缝同步
- 🎨 **现代化UI** - 响应式设计，美观易用的交互界面

## 📚 文档导航

### 核心文档
- **[技术设计文档](doc/TECHNICAL_DESIGN.md)** - 完整的技术栈设计和架构说明
- **[项目结构说明](doc/PROJECT_STRUCTURE.md)** - 详细的目录结构和文件组织
- **[快速开始指南](doc/QUICK_START.md)** - 从零开始搭建开发环境
- **[需求文档](doc/REQUIREMENT.md)** - 项目需求和功能说明

### AG-UI协议文档
- **[AG-UI实现指南](doc/AG-UI_IMPLEMENTATION.md)** - AG-UI协议完整实现指南（含Python示例）
- **[AG-UI快速参考](doc/AG-UI_QUICK_REF.md)** - 事件类型和使用速查表
- **[AG-UI协议规范](doc/AG-UI.txt)** - AG-UI官方完整文档

### 阶段实现指南
- **[阶段1实现指南](doc/PHASE1_AUTH_GUIDE.md)** - 用户认证系统完整实现（Python + FastAPI）

## 🚀 快速开始

### 前置要求

- Node.js >= 20.0.0
- Python >= 3.11
- Poetry (Python包管理)
- Docker >= 24.0.0
- Docker Compose >= 2.0.0
- Git

### 一键启动（开发环境）

```bash
# 克隆项目
git clone git@github.com:1-211250009/LLM4SE_03.git
cd LLM4SE_03

# 启动数据库服务
docker-compose -f docker-compose.dev.yml up -d

# 安装并启动后端（Python + FastAPI）
cd backend
poetry install
cp ENV_TEMPLATE.txt .env  # 配置环境变量
alembic upgrade head  # 数据库迁移
poetry run uvicorn app.main:app --reload --port 8000

# 安装并启动前端（新终端）
cd frontend
npm install
cp ENV_TEMPLATE.txt .env  # 配置环境变量
npm run dev
```

访问 http://localhost:5173 查看前端应用，http://localhost:8000/docs 查看API文档。

### 生产环境部署

```bash
# 使用Docker Compose一键部署
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

详细的环境搭建步骤请查看 [快速开始指南](doc/QUICK_START.md)。

## 🏗️ 技术栈

### 前端
- **框架**: React 18 + TypeScript + Vite
- **UI库**: Ant Design + TailwindCSS
- **状态管理**: Zustand + React Query
- **路由**: React Router v6
- **地图**: 百度地图 JavaScript API
- **语音**: 科大讯飞 Web SDK

### 后端
- **框架**: Python 3.11 + FastAPI + Pydantic
- **数据库**: PostgreSQL + SQLAlchemy + Alembic
- **缓存**: Redis
- **认证**: JWT (PyJWT + passlib)
- **协议**: RESTful API + AG-UI Protocol (SSE)
- **LLM**: DeepSeek API (支持工具调用)

### 第三方服务
- **LLM**: DeepSeek API (deepseek-chat模型)
- **语音**: 科大讯飞开放平台（ASR + TTS）
- **地图**: 百度地图开放平台

## 📦 项目结构

```
ai-travel-planner/
├── frontend/           # 前端项目（React + TypeScript）
│   ├── src/
│   │   ├── pages/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── modules/    # 功能模块（语音、地图、LLM）
│   │   ├── services/   # API服务
│   │   └── store/      # 状态管理
│   └── ...
├── backend/            # 后端项目（Python + FastAPI）
│   ├── app/
│   │   ├── api/        # API路由
│   │   ├── models/     # 数据模型
│   │   ├── services/   # 业务逻辑层
│   │   ├── agents/     # AI Agent实现
│   │   ├── utils/      # 工具函数
│   │   └── ...
│   └── alembic/        # 数据库迁移
├── docker/             # Docker配置
├── docs/               # 项目文档
└── ...
```

详细结构请查看 [项目结构说明](doc/PROJECT_STRUCTURE.md)。

## 🎯 核心功能

### 1. 智能行程规划
用户通过语音或文字输入旅行需求（目的地、日期、预算、偏好等），AI自动生成包含交通、住宿、景点、餐厅等详细信息的个性化旅行路线。

**技术实现**:
- **AG-UI协议** - 事件驱动的AI交互协议
  - Server-Sent Events (SSE) 流式传输
  - 16种标准事件类型（RUN_STARTED, TEXT_MESSAGE_CHUNK等）
  - Observable事件流处理
- **前端工具系统** - Agent可调用前端能力（POI搜索、路线计算）
- **实时状态同步** - 规划进度实时显示
- 集成地图POI数据丰富行程内容

### 2. 语音交互
支持语音输入旅行需求、语音记录费用、AI语音播报等功能，提供更自然的交互体验。

**技术实现**:
- 科大讯飞实时流式语音识别（ASR）
- 科大讯飞在线语音合成（TTS）
- Web Audio API音频处理

### 3. 地图可视化
在地图上直观展示完整行程路线、景点标记、路线规划，支持POI搜索和路线计算。

**技术实现**:
- 百度地图JavaScript API GL版
- 自定义标记和信息窗口
- 多种交通方式路线规划

### 4. 费用管理
AI辅助预算分析和费用估算，支持语音或手动记录开销，实时统计和预算预警。

**技术实现**:
- LLM费用估算和分析
- 费用分类统计
- 可视化图表展示

## 🔑 API密钥配置

本项目需要以下第三方服务的API密钥：

1. **DeepSeek API** - https://platform.deepseek.com/
2. **科大讯飞开放平台** - https://www.xfyun.cn/
3. **百度地图开放平台** - https://lbsyun.baidu.com/

**重要提示**: 请勿将API密钥提交到代码库中！使用环境变量或配置文件管理密钥。

**配置方法**：
- **后端**: 在 `backend/.env` 文件中配置
- **前端**: 在应用设置页面输入或通过 `frontend/.env` 配置

**环境变量示例**：
```bash
# 后端 .env 文件
DEEPSEEK_API_KEY=your_deepseek_api_key_here
BAIDU_MAPS_API_KEY=your_baidu_maps_api_key_here
DATABASE_URL=postgresql://admin:password@localhost:5432/travel_planner
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key_here

# 前端 .env 文件
VITE_API_BASE_URL=http://localhost:8000
VITE_BAIDU_MAPS_API_KEY=your_baidu_maps_api_key_here
VITE_XUNFEI_APP_ID=your_xunfei_app_id_here
VITE_XUNFEI_API_KEY=your_xunfei_api_key_here
VITE_XUNFEI_API_SECRET=your_xunfei_api_secret_here
```

**AG-UI协议说明**：
- 本项目使用AG-UI协议实现AI Agent通信
- AG-UI是事件驱动的开放协议，支持流式响应和工具调用
- 详细实现请参考 [AG-UI实现指南](doc/AG-UI_IMPLEMENTATION.md)

详细配置说明请查看 [快速开始指南](doc/QUICK_START.md)。

## 🧪 测试

```bash
# 后端测试
cd backend
poetry run pytest         # 运行所有测试
poetry run pytest --cov   # 生成覆盖率报告

# 前端测试
cd frontend
npm run test              # 运行单元测试
npm run test:e2e          # 运行E2E测试

# 集成测试
docker-compose up -d
npm run test:integration  # 运行集成测试
```

### 测试覆盖率

- **后端**: 目标覆盖率 > 80%
- **前端**: 目标覆盖率 > 70%
- **集成测试**: 覆盖主要用户流程

## 📝 开发计划

项目分为11个阶段开发，每个阶段约3-6天，总计约7周完成：

- [x] **阶段0**: 项目初始化
- [x] **阶段1**: 用户认证系统
- [x] **阶段2**: LLM-Agent模块开发
- [x] **阶段3**: 地图模块开发
- [x] **阶段4**: 语音模块开发
- [x] **阶段5**: 行程管理功能
- [x] **阶段6**: 费用管理功能
- [x] **阶段7**: 前端UI/UX优化
- [x] **阶段8**: 云端同步功能
- [x] **阶段9**: 测试与Bug修复
- [x] **阶段10**: Docker部署与CI/CD
- [x] **阶段11**: 文档与交付

## ✅ 项目完成状态

**当前版本**: v1.0.0  
**完成度**: 100%  
**最后更新**: 2024年12月

### 已实现功能

#### 核心功能
- ✅ **用户认证系统** - 注册、登录、JWT认证、用户资料管理
- ✅ **智能行程规划** - 基于DeepSeek LLM的AI行程规划，支持工具调用
- ✅ **地图可视化** - 百度地图集成，POI搜索、路线规划、标记管理
- ✅ **语音交互** - 科大讯飞语音识别和合成，支持语音输入和播报
- ✅ **费用管理** - 预算分析、费用记录、统计图表
- ✅ **行程管理** - 行程创建、编辑、删除、详情查看

#### 技术特性
- ✅ **AG-UI协议** - 完整实现AG-UI协议，支持流式响应和工具调用
- ✅ **响应式设计** - 现代化UI/UX，支持多设备访问
- ✅ **实时通信** - Server-Sent Events (SSE) 实时数据流
- ✅ **Docker部署** - 完整的Docker化部署方案
- ✅ **CI/CD** - GitHub Actions自动化测试和部署

#### 第三方集成
- ✅ **DeepSeek API** - LLM服务集成，支持工具调用
- ✅ **百度地图API** - 地图服务和POI搜索
- ✅ **科大讯飞API** - 语音识别和合成服务
- ✅ **PostgreSQL** - 数据持久化存储
- ✅ **Redis** - 缓存和会话管理

详细的阶段规划请查看 [技术设计文档](doc/TECHNICAL_DESIGN.md)。

## 🐳 Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

Docker镜像已发布到阿里云容器镜像仓库，可直接拉取使用。

## 🤝 贡献

欢迎提交Issue和Pull Request！

提交代码前请确保：
- 通过所有测试
- 符合代码规范（ESLint + Prettier）
- 更新相关文档

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 创建 [GitHub Issue](https://github.com/1-211250009/LLM4SE_03/issues)
- 发送邮件至：your.email@example.com

---

**Made with ❤️ by Krisdar(Haoxiang Yan)**
