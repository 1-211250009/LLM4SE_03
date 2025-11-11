# 如何运行项目 - 简明指南

> **最后更新**: 2025-01-20（重构后版本）

## 📋 前置准备

### 必需软件
- Node.js >= 20.0.0
- Python >= 3.11
- PostgreSQL >= 15（或使用Docker）
- Redis（或使用Docker）

### 必需API密钥
1. **百度地图API Key** (必需) - https://lbsyun.baidu.com/
2. **DeepSeek API Key** (必需) - https://platform.deepseek.com/
3. **科大讯飞** (可选) - https://www.xfyun.cn/

---

## 🚀 方式一：使用Docker（推荐）

这是最简单的运行方式，一键启动所有服务。

### 步骤

```bash
# 1. 克隆项目（如果还没有）
git clone <your-repo-url>
cd LLM4SE_03

# 2. 配置环境变量
# 编辑 docker.env 文件，填入API密钥
vim docker.env

# 必须配置以下变量：
# DEEPSEEK_API_KEY=your_deepseek_api_key
# BAIDU_MAPS_AK=your_baidu_maps_api_key

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志（可选）
docker-compose logs -f
```

### 访问应用

- **前端应用**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 停止服务

```bash
docker-compose down
```

---

## 💻 方式二：本地开发运行

适合开发调试，支持热重载。

### 第一步：启动数据库和Redis

```bash
# 使用Docker启动数据库
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 验证服务启动
docker-compose -f docker-compose.dev.yml ps
```

### 第二步：配置并启动后端

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并配置环境变量
cp ENV_TEMPLATE.txt .env

# 3. 编辑.env文件，填入以下必需配置：
# vim .env
```

**后端必需配置 (`backend/.env`)**:
```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/travel_planner

# Redis配置  
REDIS_URL=redis://localhost:6379

# JWT密钥（随机生成）
SECRET_KEY=your-secret-key-change-this-in-production-at-least-32-chars

# DeepSeek API（必需）
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 百度地图API（必需）
BAIDU_MAPS_AK=your_baidu_maps_api_key_here
```

```bash
# 4. 安装Python依赖
pip install -r requirements.txt

# 5. 执行数据库迁移（重要！）
alembic upgrade head

# 6. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 第三步：配置并启动前端

**打开新终端**

```bash
# 1. 进入前端目录
cd frontend

# 2. 创建并配置环境变量
cp ENV_TEMPLATE.txt .env

# 3. 编辑.env文件
# vim .env
```

**前端必需配置 (`frontend/.env`)**:
```bash
# API地址
VITE_API_BASE_URL=http://localhost:8000

# 百度地图API（必需）
VITE_BAIDU_MAPS_API_KEY=your_baidu_maps_api_key_here

# 科大讯飞语音（可选，不配置则禁用语音功能）
VITE_ENABLE_VOICE=false
# VITE_XUNFEI_APP_ID=
# VITE_XUNFEI_API_KEY=
# VITE_XUNFEI_API_SECRET=
```

```bash
# 4. 安装Node.js依赖
npm install

# 5. 启动前端开发服务器
npm run dev
```

### 访问应用

- **前端应用**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 🎯 首次使用指南

### 1. 注册账号

1. 访问 http://localhost:5173
2. 点击"立即注册"
3. 填写邮箱、密码、姓名
4. 点击注册

### 2. 创建第一个行程

**方式A：使用AI助手**
1. 登录后，导航到"行程规划"页面
2. 点击右下角的AI助手图标
3. 输入：`我想去北京玩3天，预算5000元，喜欢历史文化`
4. AI会自动生成行程建议

**方式B：手动创建**
1. 导航到"行程管理"页面
2. 点击"创建新行程"
3. 填写行程信息
4. 保存行程

### 3. 查看行程详情

1. 在行程列表中点击任意行程
2. 查看行程详情页面
   - 左侧：行程时间轴，显示所有节点
   - 右侧：地图视图，显示节点位置
   - 顶部：预算统计

### 4. 记录费用

1. 导航到"费用管理"页面
2. 选择行程
3. 点击"添加费用"
4. 填写金额、类别、描述
5. (可选) 关联到具体行程节点

---

## 🔧 常见问题

### Q1: 后端启动报错 "ModuleNotFoundError"

**解决方案**:
```bash
cd backend
pip install -r requirements.txt
# 确保所有依赖都已安装
```

### Q2: 前端启动后页面空白

**解决方案**:
1. 检查浏览器控制台是否有错误
2. 确认后端服务已启动
3. 检查`.env`文件中的`VITE_API_BASE_URL`配置

### Q3: 数据库连接失败

**解决方案**:
```bash
# 检查PostgreSQL是否运行
docker-compose -f docker-compose.dev.yml ps

# 重启数据库
docker-compose -f docker-compose.dev.yml restart postgres

# 检查连接字符串
# backend/.env中的DATABASE_URL是否正确
```

### Q4: 地图不显示

**解决方案**:
1. 检查百度地图API密钥是否配置
2. 在浏览器控制台查看是否有加载错误
3. 确认API密钥有效且配额充足

### Q5: 语音功能不可用

这是**正常现象**！语音功能是可选的：
- 如果不配置科大讯飞API，语音按钮会显示禁用状态
- 不影响其他功能的使用
- 如需启用，请参考 `doc/VOICE_SETUP_GUIDE.md`

### Q6: LLM回复很慢或超时

**解决方案**:
1. 检查DeepSeek API密钥是否有效
2. 检查网络连接
3. 查看后端日志：`docker-compose logs -f backend`

### Q7: 执行数据库迁移后报错

**解决方案**:
```bash
# 查看当前迁移状态
cd backend
alembic current

# 回滚到上一个版本
alembic downgrade -1

# 重新执行迁移
alembic upgrade head

# 如果还有问题，查看迁移历史
alembic history
```

---

## 📊 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 (本地开发) | 5173 | Vite开发服务器 |
| 前端 (Docker) | 80 | Nginx生产服务器 |
| 后端 | 8000 | FastAPI服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存服务 |

---

## 🛠️ 高级配置

### 使用Poetry管理Python依赖

```bash
cd backend

# 安装Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 启动服务
poetry run uvicorn app.main:app --reload
```

### 配置科大讯飞语音（可选）

参考 `doc/VOICE_SETUP_GUIDE.md` 完整配置指南。

### 生产环境部署

参考 `doc/DOCKER_SETUP.md` Docker部署指南。

---

## 📞 获取帮助

如果遇到问题：

1. **查看文档**:
   - `doc/PROJECT_RUN.md` - 详细运行指南
   - `doc/QUICK_START.md` - 快速开始指南
   - `doc/VOICE_SETUP_GUIDE.md` - 语音配置指南
   - `doc/REFACTORING_SUMMARY.md` - 重构说明

2. **检查日志**:
   ```bash
   # Docker模式
   docker-compose logs -f
   
   # 本地开发模式
   # 查看后端终端输出
   # 查看前端浏览器控制台
   ```

3. **提交Issue**: 在GitHub上提交问题

---

## ✅ 运行成功检查清单

- [ ] 后端服务启动成功，访问 http://localhost:8000/docs 能看到API文档
- [ ] 前端应用启动成功，访问 http://localhost:5173 能看到登录页面
- [ ] 数据库连接正常，可以注册新用户
- [ ] 能够登录并访问主页面
- [ ] 地图能够正常显示
- [ ] AI助手能够正常对话
- [ ] 可以创建和查看行程

---

**祝您使用愉快！🎉**

