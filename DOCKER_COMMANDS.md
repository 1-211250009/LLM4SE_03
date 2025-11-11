# Docker 命令行打包和运行教程

本文档提供使用命令行打包和运行 Docker 的完整教程。

## 📋 目录

1. [基础准备](#基础准备)
2. [构建 Docker 镜像](#构建-docker-镜像)
3. [运行 Docker 容器](#运行-docker-容器)
4. [使用 Docker Compose](#使用-docker-compose)
5. [推送镜像到仓库](#推送镜像到仓库)
6. [常用命令速查](#常用命令速查)

---

## 基础准备

### 1. 检查 Docker 环境

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 检查 Docker 是否运行
docker ps
```

### 2. 进入项目目录

```bash
cd /Users/yanhaoxiang/Workspace/LLM4SE_03
```

---

## 构建 Docker 镜像

### 方式一：使用 docker build 命令（手动构建）

#### 1. 构建后端镜像

```bash
# 进入后端目录
cd backend

# 构建镜像（带标签）
docker build -t llm4se03-backend:latest .

# 或者指定完整的镜像地址（用于推送到仓库）
docker build -t registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-backend:latest .

# 返回项目根目录
cd ..
```

**参数说明**:
- `-t`: 指定镜像名称和标签
- `.`: 构建上下文（当前目录）

#### 2. 构建前端镜像

```bash
# 进入前端目录
cd frontend

# 构建镜像
docker build -t llm4se03-frontend:latest .

# 或者指定完整的镜像地址
docker build -t registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-frontend:latest .

# 返回项目根目录
cd ..
```

#### 3. 查看构建的镜像

```bash
# 查看所有镜像
docker images

# 查看特定镜像
docker images | grep llm4se03

# 查看镜像详细信息
docker inspect llm4se03-backend:latest
```

### 方式二：使用构建脚本（推荐）

```bash
# 构建所有镜像（不推送）
./build-docker.sh build all

# 只构建后端
./build-docker.sh build backend

# 只构建前端
./build-docker.sh build frontend

# 指定版本号构建
VERSION=v1.0.0 ./build-docker.sh build all
```

### 方式三：使用 docker-compose 构建

```bash
# 构建所有服务
docker-compose build

# 构建特定服务
docker-compose build backend
docker-compose build frontend

# 强制重新构建（不使用缓存）
docker-compose build --no-cache

# 构建并启动
docker-compose up --build
```

---

## 运行 Docker 容器

### 方式一：使用 docker run 命令（手动运行）

#### 1. 启动数据库和 Redis

```bash
# 启动 PostgreSQL
docker run -d \
  --name travel-planner-postgres \
  -e POSTGRES_DB=travel_planner \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15-alpine

# 启动 Redis
docker run -d \
  --name travel-planner-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 2. 启动后端容器

```bash
docker run -d \
  --name travel-planner-backend \
  --link travel-planner-postgres:postgres \
  --link travel-planner-redis:redis \
  -e DATABASE_URL=postgresql://admin:password@postgres:5432/travel_planner \
  -e REDIS_URL=redis://redis:6379 \
  -e SECRET_KEY=your-secret-key-here \
  -e DEEPSEEK_API_KEY=your_deepseek_api_key \
  -e BAIDU_MAPS_API_KEY=your_baidu_maps_api_key \
  -e XFYUN_APP_ID=your_xfyun_app_id \
  -e XFYUN_API_KEY=your_xfyun_api_key \
  -e XFYUN_API_SECRET=your_xfyun_api_secret \
  -p 8000:8000 \
  llm4se03-backend:latest
```

#### 3. 初始化数据库

```bash
# 进入后端容器
docker exec -it travel-planner-backend bash

# 执行数据库迁移
alembic upgrade head

# 退出容器
exit
```

#### 4. 启动前端容器

```bash
docker run -d \
  --name travel-planner-frontend \
  --link travel-planner-backend:backend \
  -e VITE_API_BASE_URL=http://backend:8000 \
  -p 80:80 \
  llm4se03-frontend:latest
```

### 方式二：使用 docker-compose（推荐）

#### 1. 创建环境变量文件

创建 `.env` 文件：

```bash
cat > .env << EOF
DEEPSEEK_API_KEY=your_deepseek_api_key_here
BAIDU_MAPS_API_KEY=your_baidu_maps_api_key_here
XFYUN_APP_ID=your_xfyun_app_id_here
XFYUN_API_KEY=your_xfyun_api_key_here
XFYUN_API_SECRET=your_xfyun_api_secret_here
EOF
```

#### 2. 启动所有服务

```bash
# 使用开发配置启动（会构建镜像）
docker-compose -f docker-compose.yml up -d

# 使用生产配置启动（使用预构建镜像）
docker-compose -f docker-compose.prod.yml --env-file .env up -d

# 查看启动日志
docker-compose logs -f

# 后台启动并查看日志
docker-compose up -d && docker-compose logs -f
```

#### 3. 初始化数据库

```bash
# 执行数据库迁移
docker-compose exec backend alembic upgrade head

# 或者使用生产配置
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### 4. 查看服务状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看特定服务状态
docker-compose ps backend
docker-compose ps frontend
```

#### 5. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# 查看最近100行日志
docker-compose logs --tail=100 backend

# 查看特定时间的日志
docker-compose logs --since 10m backend
```

---

## 使用 Docker Compose

### 常用命令

```bash
# 启动服务（后台运行）
docker-compose up -d

# 启动服务（前台运行，查看日志）
docker-compose up

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和卷（数据也会删除）
docker-compose down -v

# 重启服务
docker-compose restart

# 重启特定服务
docker-compose restart backend

# 重新构建并启动
docker-compose up -d --build

# 强制重新创建容器
docker-compose up -d --force-recreate

# 扩展服务（运行多个实例）
docker-compose up -d --scale backend=2
```

### 管理服务

```bash
# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh

# 执行命令
docker-compose exec backend python -c "print('Hello')"
docker-compose exec backend alembic upgrade head

# 查看服务资源使用
docker-compose top

# 暂停服务
docker-compose pause

# 恢复服务
docker-compose unpause
```

---

## 推送镜像到仓库

### 1. 登录到阿里云容器镜像仓库

```bash
# 登录（会提示输入用户名和密码）
docker login registry.cn-hangzhou.aliyuncs.com

# 或者使用环境变量
echo "your_password" | docker login registry.cn-hangzhou.aliyuncs.com -u "your_username" --password-stdin
```

### 2. 标记镜像

```bash
# 标记后端镜像
docker tag llm4se03-backend:latest \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-backend:latest

# 标记前端镜像
docker tag llm4se03-frontend:latest \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-frontend:latest
```

### 3. 推送镜像

```bash
# 推送后端镜像
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-backend:latest

# 推送前端镜像
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-frontend:latest

# 推送所有标签
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-backend --all-tags
```

### 4. 使用构建脚本推送

```bash
# 设置环境变量
export ALIYUN_DOCKER_USERNAME=your_username
export ALIYUN_DOCKER_PASSWORD=your_password
export DOCKER_NAMESPACE=your-namespace

# 构建并推送所有镜像
./build-docker.sh all all

# 只推送（不构建）
./build-docker.sh push all
```

---

## 常用命令速查

### 镜像管理

```bash
# 列出所有镜像
docker images

# 删除镜像
docker rmi llm4se03-backend:latest

# 删除未使用的镜像
docker image prune

# 删除所有未使用的镜像
docker image prune -a

# 查看镜像历史
docker history llm4se03-backend:latest

# 导出镜像
docker save llm4se03-backend:latest -o backend.tar

# 导入镜像
docker load -i backend.tar
```

### 容器管理

```bash
# 列出运行中的容器
docker ps

# 列出所有容器（包括停止的）
docker ps -a

# 停止容器
docker stop travel-planner-backend

# 启动容器
docker start travel-planner-backend

# 重启容器
docker restart travel-planner-backend

# 删除容器
docker rm travel-planner-backend

# 强制删除运行中的容器
docker rm -f travel-planner-backend

# 删除所有停止的容器
docker container prune

# 查看容器日志
docker logs travel-planner-backend

# 实时查看日志
docker logs -f travel-planner-backend

# 查看最近100行日志
docker logs --tail=100 travel-planner-backend

# 进入容器
docker exec -it travel-planner-backend bash

# 在容器中执行命令
docker exec travel-planner-backend ls -la

# 查看容器资源使用
docker stats travel-planner-backend

# 查看所有容器资源使用
docker stats
```

### 网络管理

```bash
# 列出网络
docker network ls

# 创建网络
docker network create app-network

# 删除网络
docker network rm app-network

# 查看网络详情
docker network inspect app-network
```

### 卷管理

```bash
# 列出卷
docker volume ls

# 查看卷详情
docker volume inspect postgres_data

# 删除卷
docker volume rm postgres_data

# 删除未使用的卷
docker volume prune
```

### 清理命令

```bash
# 清理所有未使用的资源
docker system prune

# 清理所有未使用的资源（包括镜像）
docker system prune -a

# 清理所有未使用的资源（包括卷）
docker system prune -a --volumes
```

---

## 完整示例：从零开始

### 步骤 1: 构建镜像

```bash
# 进入项目目录
cd /Users/yanhaoxiang/Workspace/LLM4SE_03

# 构建后端镜像
cd backend
docker build -t llm4se03-backend:latest .
cd ..

# 构建前端镜像
cd frontend
docker build -t llm4se03-frontend:latest .
cd ..
```

### 步骤 2: 启动数据库

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
```

### 步骤 3: 启动后端

```bash
docker run -d \
  --name travel-planner-backend \
  --link travel-planner-postgres:postgres \
  --link travel-planner-redis:redis \
  -e DATABASE_URL=postgresql://admin:password@postgres:5432/travel_planner \
  -e REDIS_URL=redis://redis:6379 \
  -e SECRET_KEY=your-secret-key \
  -e DEEPSEEK_API_KEY=your_key \
  -e BAIDU_MAPS_API_KEY=your_key \
  -e XFYUN_APP_ID=your_id \
  -e XFYUN_API_KEY=your_key \
  -e XFYUN_API_SECRET=your_secret \
  -p 8000:8000 \
  llm4se03-backend:latest
```

### 步骤 4: 初始化数据库

```bash
docker exec travel-planner-backend alembic upgrade head
```

### 步骤 5: 启动前端

```bash
docker run -d \
  --name travel-planner-frontend \
  --link travel-planner-backend:backend \
  -e VITE_API_BASE_URL=http://backend:8000 \
  -p 80:80 \
  llm4se03-frontend:latest
```

### 步骤 6: 验证服务

```bash
# 检查所有容器
docker ps

# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端
curl http://localhost/
```

---

## 使用 Docker Compose 的完整示例

### 步骤 1: 创建环境变量文件

```bash
cat > .env << EOF
DEEPSEEK_API_KEY=your_deepseek_api_key
BAIDU_MAPS_API_KEY=your_baidu_maps_api_key
XFYUN_APP_ID=your_xfyun_app_id
XFYUN_API_KEY=your_xfyun_api_key
XFYUN_API_SECRET=your_xfyun_api_secret
EOF
```

### 步骤 2: 启动所有服务

```bash
# 构建并启动
docker-compose up -d --build

# 或者使用生产配置
docker-compose -f docker-compose.prod.yml --env-file .env up -d
```

### 步骤 3: 初始化数据库

```bash
docker-compose exec backend alembic upgrade head
```

### 步骤 4: 查看日志

```bash
docker-compose logs -f
```

### 步骤 5: 访问应用

- 前端: http://localhost
- 后端API: http://localhost:8000/docs

---

## 故障排查

### 查看容器日志

```bash
# 查看所有日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend

# 实时查看日志
docker-compose logs -f backend

# 查看最近100行
docker-compose logs --tail=100 backend
```

### 进入容器调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 检查网络连接
docker-compose exec backend ping postgres
docker-compose exec backend ping redis
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend

# 强制重新创建
docker-compose up -d --force-recreate backend
```

### 清理和重建

```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器和卷
docker-compose down -v

# 重新构建并启动
docker-compose up -d --build
```

---

## 提示和最佳实践

1. **使用 docker-compose**: 对于多容器应用，使用 docker-compose 更方便
2. **环境变量**: 使用 `.env` 文件管理敏感信息
3. **数据持久化**: 使用 Docker 卷保存数据
4. **健康检查**: 配置健康检查确保服务正常运行
5. **日志管理**: 定期查看日志，及时发现问题
6. **资源清理**: 定期清理未使用的镜像和容器

---

**最后更新**: 2024年12月

