# 本地 Docker 打包和运行指南

本文档提供在本地 Docker 环境打包和运行项目的完整步骤。

## 🚀 快速开始

### 方式一：使用 Docker Compose（最简单，推荐）

#### 1. 构建并启动所有服务

```bash
# 进入项目目录
cd /Users/yanhaoxiang/Workspace/LLM4SE_03

# 构建镜像并启动所有服务（包括数据库、Redis、后端、前端）
docker-compose up -d --build

# 查看启动日志
docker-compose logs -f
```

#### 2. 初始化数据库

```bash
# 等待数据库启动后，执行数据库迁移
docker-compose exec backend alembic upgrade head
```

#### 3. 访问应用

- **前端**: http://localhost
- **后端API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

#### 4. 查看服务状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 5. 停止服务

```bash
# 停止服务（保留容器）
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和卷（数据也会删除）
docker-compose down -v
```

---

## 方式二：手动构建和运行（分步操作）

### 步骤 1: 构建后端镜像

```bash
# 进入后端目录
cd backend

# 构建镜像
docker build -t llm4se03-backend:latest .

# 查看构建的镜像
docker images | grep llm4se03-backend

# 返回项目根目录
cd ..
```

### 步骤 2: 构建前端镜像

```bash
# 进入前端目录
cd frontend

# 构建镜像
docker build -t llm4se03-frontend:latest .

# 查看构建的镜像
docker images | grep llm4se03-frontend

# 返回项目根目录
cd ..
```

### 步骤 3: 启动数据库和 Redis

```bash
# 启动 PostgreSQL
docker run -d \
  --name travel-planner-postgres \
  -e POSTGRES_DB=travel_planner \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# 启动 Redis
docker run -d \
  --name travel-planner-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine

# 检查容器是否运行
docker ps
```

### 步骤 4: 启动后端容器

```bash
docker run -d \
  --name travel-planner-backend \
  --link travel-planner-postgres:postgres \
  --link travel-planner-redis:redis \
  -e DATABASE_URL=postgresql://admin:password@postgres:5432/travel_planner \
  -e REDIS_URL=redis://redis:6379 \
  -e SECRET_KEY=your-secret-key-here \
  -e ALGORITHM=HS256 \
  -e ACCESS_TOKEN_EXPIRE_MINUTES=30 \
  -e CORS_ORIGINS='["http://localhost:5173","http://localhost:3000","http://localhost","http://localhost:80"]' \
  -e DEEPSEEK_API_KEY=your_deepseek_api_key \
  -e BAIDU_MAPS_API_KEY=your_baidu_maps_api_key \
  -e XFYUN_APP_ID=your_xfyun_app_id \
  -e XFYUN_API_KEY=your_xfyun_api_key \
  -e XFYUN_API_SECRET=your_xfyun_api_secret \
  -p 8000:8000 \
  llm4se03-backend:latest
```

### 步骤 5: 初始化数据库

```bash
# 等待后端容器启动（约10秒）
sleep 10

# 执行数据库迁移
docker exec travel-planner-backend alembic upgrade head
```

### 步骤 6: 启动前端容器

```bash
docker run -d \
  --name travel-planner-frontend \
  --link travel-planner-backend:backend \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  -p 80:80 \
  llm4se03-frontend:latest
```

### 步骤 7: 验证服务

```bash
# 查看所有容器
docker ps

# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端
curl http://localhost/
```

---

## 📋 常用命令

### 查看容器状态

```bash
# 查看运行中的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 查看特定容器
docker ps | grep travel-planner
```

### 查看日志

```bash
# 查看后端日志
docker logs travel-planner-backend

# 实时查看日志
docker logs -f travel-planner-backend

# 查看最近100行日志
docker logs --tail=100 travel-planner-backend

# 使用 docker-compose 查看日志
docker-compose logs -f backend
```

### 进入容器

```bash
# 进入后端容器
docker exec -it travel-planner-backend bash

# 进入前端容器
docker exec -it travel-planner-frontend sh

# 在容器中执行命令
docker exec travel-planner-backend ls -la
docker exec travel-planner-backend alembic upgrade head
```

### 停止和删除容器

```bash
# 停止容器
docker stop travel-planner-backend
docker stop travel-planner-frontend
docker stop travel-planner-postgres
docker stop travel-planner-redis

# 启动容器
docker start travel-planner-backend

# 重启容器
docker restart travel-planner-backend

# 删除容器（需要先停止）
docker rm travel-planner-backend

# 强制删除运行中的容器
docker rm -f travel-planner-backend

# 删除所有相关容器
docker rm -f travel-planner-backend travel-planner-frontend travel-planner-postgres travel-planner-redis
```

### 管理镜像

```bash
# 查看所有镜像
docker images

# 删除镜像
docker rmi llm4se03-backend:latest

# 删除未使用的镜像
docker image prune

# 查看镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

---

## 🔧 配置环境变量

### 方式一：在 docker-compose.yml 中直接配置

编辑 `docker-compose.yml`，在 `backend` 服务的 `environment` 部分添加：

```yaml
environment:
  - DEEPSEEK_API_KEY=your_deepseek_api_key
  - BAIDU_MAPS_API_KEY=your_baidu_maps_api_key
  - XFYUN_APP_ID=your_xfyun_app_id
  - XFYUN_API_KEY=your_xfyun_api_key
  - XFYUN_API_SECRET=your_xfyun_api_secret
```

### 方式二：使用 .env 文件

创建 `.env` 文件：

```bash
cat > .env << EOF
DEEPSEEK_API_KEY=your_deepseek_api_key
BAIDU_MAPS_API_KEY=your_baidu_maps_api_key
XFYUN_APP_ID=your_xfyun_app_id
XFYUN_API_KEY=your_xfyun_api_key
XFYUN_API_SECRET=your_xfyun_api_secret
EOF
```

然后使用：

```bash
docker-compose --env-file .env up -d
```

---

## 🐛 故障排查

### 1. 容器无法启动

```bash
# 查看容器日志
docker logs travel-planner-backend

# 查看容器状态
docker ps -a | grep travel-planner-backend

# 检查容器配置
docker inspect travel-planner-backend
```

### 2. 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 测试数据库连接
docker exec travel-planner-postgres psql -U admin -d travel_planner -c "SELECT 1;"

# 检查后端日志中的数据库连接错误
docker logs travel-planner-backend | grep -i database
```

### 3. 端口被占用

```bash
# 检查端口占用
lsof -i :8000
lsof -i :80
lsof -i :5432

# 修改端口映射（例如将8000改为8001）
docker run -d ... -p 8001:8000 llm4se03-backend:latest
```

### 4. 镜像构建失败

```bash
# 查看构建日志
docker build -t llm4se03-backend:latest . 2>&1 | tee build.log

# 不使用缓存重新构建
docker build --no-cache -t llm4se03-backend:latest .
```

### 5. 前端无法访问后端

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查网络连接
docker exec travel-planner-frontend ping backend

# 检查环境变量
docker exec travel-planner-frontend env | grep VITE_API_BASE_URL
```

---

## 📝 完整示例脚本

创建一个 `run-local.sh` 脚本：

```bash
#!/bin/bash

echo "=== 本地 Docker 运行脚本 ==="

# 1. 构建镜像
echo "1. 构建后端镜像..."
cd backend
docker build -t llm4se03-backend:latest .
cd ..

echo "2. 构建前端镜像..."
cd frontend
docker build -t llm4se03-frontend:latest .
cd ..

# 2. 启动数据库
echo "3. 启动 PostgreSQL..."
docker run -d \
  --name travel-planner-postgres \
  -e POSTGRES_DB=travel_planner \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

echo "4. 启动 Redis..."
docker run -d \
  --name travel-planner-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine

# 等待数据库启动
echo "5. 等待数据库启动..."
sleep 5

# 3. 启动后端
echo "6. 启动后端..."
docker run -d \
  --name travel-planner-backend \
  --link travel-planner-postgres:postgres \
  --link travel-planner-redis:redis \
  -e DATABASE_URL=postgresql://admin:password@postgres:5432/travel_planner \
  -e REDIS_URL=redis://redis:6379 \
  -e SECRET_KEY=local-secret-key \
  -e DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-your_key} \
  -e BAIDU_MAPS_API_KEY=${BAIDU_MAPS_API_KEY:-your_key} \
  -e XFYUN_APP_ID=${XFYUN_APP_ID:-your_id} \
  -e XFYUN_API_KEY=${XFYUN_API_KEY:-your_key} \
  -e XFYUN_API_SECRET=${XFYUN_API_SECRET:-your_secret} \
  -p 8000:8000 \
  llm4se03-backend:latest

# 等待后端启动
echo "7. 等待后端启动..."
sleep 10

# 4. 初始化数据库
echo "8. 初始化数据库..."
docker exec travel-planner-backend alembic upgrade head

# 5. 启动前端
echo "9. 启动前端..."
docker run -d \
  --name travel-planner-frontend \
  --link travel-planner-backend:backend \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  -p 80:80 \
  llm4se03-frontend:latest

echo ""
echo "=== 启动完成 ==="
echo "前端: http://localhost"
echo "后端API: http://localhost:8000/docs"
echo ""
echo "查看日志: docker logs -f travel-planner-backend"
echo "停止服务: docker stop travel-planner-backend travel-planner-frontend travel-planner-postgres travel-planner-redis"
```

---

## ✅ 快速检查清单

运行前检查：

- [ ] Docker 已安装并运行 (`docker ps`)
- [ ] 端口 80, 8000, 5432, 6379 未被占用
- [ ] 已配置 API 密钥（DeepSeek、百度地图、科大讯飞）
- [ ] 有足够的磁盘空间

运行后检查：

- [ ] 所有容器都在运行 (`docker ps`)
- [ ] 后端健康检查通过 (`curl http://localhost:8000/health`)
- [ ] 前端可以访问 (`curl http://localhost/`)
- [ ] 数据库迁移成功 (`docker logs travel-planner-backend | grep alembic`)

---

**提示**: 最简单的方式是使用 `docker-compose up -d --build`，它会自动处理所有依赖关系。

