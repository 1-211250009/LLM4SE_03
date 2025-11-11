# Docker 运行指南

本文档提供使用 Docker 镜像运行 AI旅行规划师 的完整指南。

## 📦 Docker 镜像地址

### 阿里云容器镜像仓库

**后端镜像**:
```bash
registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-backend:latest
```

**前端镜像**:
```bash
registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-frontend:latest
```

> **注意**: 请将 `your-namespace` 替换为您的实际阿里云镜像仓库命名空间。

## 🚀 快速开始

### 方式一：使用 Docker Compose（推荐）

#### 1. 下载 docker-compose.yml

```bash
# 克隆项目
git clone https://github.com/1-211250009/LLM4SE_03.git
cd LLM4SE_03
```

#### 2. 配置环境变量

创建 `docker.env` 文件（如果不存在）：

```bash
# 数据库配置
POSTGRES_DB=travel_planner
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password_here

# Redis配置
REDIS_PASSWORD=

# 后端配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API密钥配置（必需）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
BAIDU_MAPS_API_KEY=your_baidu_maps_api_key_here
XFYUN_APP_ID=your_xfyun_app_id_here
XFYUN_API_KEY=your_xfyun_api_key_here
XFYUN_API_SECRET=your_xfyun_api_secret_here

# CORS配置
CORS_ORIGINS=["http://localhost","http://localhost:80","http://localhost:5173"]
```

#### 3. 修改 docker-compose.yml

编辑 `docker-compose.yml`，将镜像地址替换为您的阿里云镜像地址：

```yaml
services:
  backend:
    image: registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-backend:latest
    # ... 其他配置

  frontend:
    image: registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-frontend:latest
    # ... 其他配置
```

#### 4. 启动服务

```bash
# 拉取镜像并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 5. 初始化数据库

```bash
# 进入后端容器执行数据库迁移
docker-compose exec backend alembic upgrade head
```

#### 6. 访问应用

- **前端**: http://localhost
- **后端API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 方式二：直接使用 Docker 命令

#### 1. 启动数据库和Redis

```bash
docker run -d \
  --name travel-planner-postgres \
  -e POSTGRES_DB=travel_planner \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:15-alpine

docker run -d \
  --name travel-planner-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 2. 启动后端

```bash
docker run -d \
  --name travel-planner-backend \
  --link travel-planner-postgres:postgres \
  --link travel-planner-redis:redis \
  -e DATABASE_URL=postgresql://admin:your_password@postgres:5432/travel_planner \
  -e REDIS_URL=redis://redis:6379 \
  -e SECRET_KEY=your-secret-key \
  -e DEEPSEEK_API_KEY=your_deepseek_api_key \
  -e BAIDU_MAPS_API_KEY=your_baidu_maps_api_key \
  -e XFYUN_APP_ID=your_xfyun_app_id \
  -e XFYUN_API_KEY=your_xfyun_api_key \
  -e XFYUN_API_SECRET=your_xfyun_api_secret \
  -p 8000:8000 \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-backend:latest
```

#### 3. 初始化数据库

```bash
docker exec travel-planner-backend alembic upgrade head
```

#### 4. 启动前端

```bash
docker run -d \
  --name travel-planner-frontend \
  --link travel-planner-backend:backend \
  -e VITE_API_BASE_URL=http://backend:8000 \
  -p 80:80 \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/llm4se03-frontend:latest
```

## 🔧 配置说明

### 必需的环境变量

#### 后端环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL数据库连接URL | `postgresql://admin:password@postgres:5432/travel_planner` |
| `REDIS_URL` | Redis连接URL | `redis://redis:6379` |
| `SECRET_KEY` | JWT签名密钥 | `your-secret-key-here` |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | `sk-xxx...` |
| `BAIDU_MAPS_API_KEY` | 百度地图API密钥 | `your_baidu_maps_key` |
| `XFYUN_APP_ID` | 科大讯飞应用ID | `your_app_id` |
| `XFYUN_API_KEY` | 科大讯飞API Key | `your_api_key` |
| `XFYUN_API_SECRET` | 科大讯飞API Secret | `your_api_secret` |

#### 前端环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `VITE_API_BASE_URL` | 后端API地址 | `http://localhost:8000` 或 `http://backend:8000` |

### 可选的环境变量

- `CORS_ORIGINS`: CORS允许的源（默认：`["http://localhost:5173","http://localhost:3000"]`）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token过期时间（默认：30分钟）
- `ALGORITHM`: JWT算法（默认：HS256）

## 📋 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 停止服务

```bash
docker-compose stop
```

### 重启服务

```bash
docker-compose restart
```

### 停止并删除容器

```bash
docker-compose down
```

### 停止并删除容器和卷（数据也会被删除）

```bash
docker-compose down -v
```

### 更新镜像

```bash
# 拉取最新镜像
docker-compose pull

# 重新构建并启动
docker-compose up -d --force-recreate
```

## 🔍 故障排查

### 1. 容器无法启动

```bash
# 查看容器日志
docker-compose logs backend
docker-compose logs frontend

# 检查容器状态
docker-compose ps
```

### 2. 数据库连接失败

```bash
# 检查PostgreSQL容器是否运行
docker-compose ps postgres

# 检查数据库连接
docker-compose exec postgres psql -U admin -d travel_planner -c "SELECT 1;"
```

### 3. 前端无法访问后端

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查网络连接
docker-compose exec frontend ping backend
```

### 4. API密钥错误

确保所有必需的环境变量都已正确配置：

```bash
# 检查环境变量
docker-compose exec backend env | grep -E "DEEPSEEK|BAIDU|XFYUN"
```

## 📝 数据持久化

Docker Compose 配置中已经设置了数据卷持久化：

- **PostgreSQL数据**: `postgres_data` 卷
- **Redis数据**: `redis_data` 卷

数据会保存在 Docker 卷中，即使删除容器也不会丢失数据。

### 备份数据

```bash
# 备份PostgreSQL数据
docker-compose exec postgres pg_dump -U admin travel_planner > backup.sql

# 恢复数据
docker-compose exec -T postgres psql -U admin travel_planner < backup.sql
```

## 🔐 安全建议

1. **生产环境配置**:
   - 修改默认密码
   - 使用强密钥（SECRET_KEY）
   - 配置HTTPS
   - 限制CORS源

2. **API密钥管理**:
   - 使用Docker secrets或环境变量文件
   - 不要将密钥提交到代码库
   - 定期轮换密钥

3. **网络安全**:
   - 使用Docker网络隔离
   - 配置防火墙规则
   - 限制端口暴露

## 📚 更多信息

- [项目README](README.md)
- [技术设计文档](doc/TECHNICAL_DESIGN.md)
- [快速开始指南](doc/QUICK_START.md)

## 🆘 获取帮助

如遇问题，请：
1. 查看日志：`docker-compose logs -f`
2. 检查GitHub Issues
3. 查看项目文档

---

**最后更新**: 2024年12月

