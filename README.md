# 使用文档

本文档供助教验收项目使用，如操作遇到问题或故障，可以直接在公网环境下访问 http://travel.vibe.holger.host。

## 代码仓库拉取

```bash
git clone git@github.com:1-211250009/LLM4SE_03.git
```

## 数据库配置

项目使用 Docker Compose 自动启动数据库，无需手动配置。

数据库配置（已在 docker-compose.yml 中配置）：
- PostgreSQL: 数据库名 `travel_planner`，用户名 `admin`，密码 `password`，端口 `5432`
- Redis: 端口 `6379`

## 项目运行

### 方式一：使用预构建镜像（推荐）

```bash
# 1. 拉取镜像
docker pull crpi-xwthsolplptwao7o.cn-shanghai.personal.cr.aliyuncs.com/haoxiangyan/llm4se03-backend:latest
docker pull crpi-xwthsolplptwao7o.cn-shanghai.personal.cr.aliyuncs.com/haoxiangyan/llm4se03-frontend:latest

# 2. 配置环境变量
cp ENV_EXAMPLE .env
# 编辑 .env 文件，填入必需的 API 密钥（DEEPSEEK_API_KEY、BAIDU_MAP_AK、BAIDU_MAP_SK 等）

# 3. 修改 docker-compose.prod.yml 中的镜像地址
将第46行后端镜像地址改为：crpi-xwthsolplptwao7o.cn-shanghai.personal.cr.aliyuncs.com/haoxiangyan/llm4se03-backend:latest
将第82行前端镜像地址改为：crpi-xwthsolplptwao7o.cn-shanghai.personal.cr.aliyuncs.com/haoxiangyan/llm4se03-frontend:latest

# 4. 启动服务
docker-compose -f docker-compose.prod.yml --env-file .env up -d

# 5. 初始化数据库
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. 访问应用
# 前端: http://localhost:28810
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 方式二：使用源码构建

```bash
# 1. 配置环境变量
cp ENV_EXAMPLE .env
# 编辑 .env 文件，填入必需的 API 密钥

# 2. 启动服务（会自动构建镜像）
docker-compose up -d --build

# 3. 初始化数据库
docker-compose exec backend alembic upgrade head

# 4. 访问应用
# 前端: http://localhost:28810
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```