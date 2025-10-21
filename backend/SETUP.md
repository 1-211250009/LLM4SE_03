# 后端快速启动指南

## 📋 准备工作

### 1. 确认工具已安装

```bash
python --version   # 应该 >= 3.11
poetry --version   # 推荐使用Poetry
docker --version   # 用于PostgreSQL
```

### 2. 启动数据库服务

从项目根目录启动Docker服务：

```bash
cd ..  # 返回项目根目录
docker-compose -f docker-compose.dev.yml up -d

# 验证服务状态
docker ps | grep postgres
docker ps | grep redis
```

---

## 🚀 快速启动（3步完成）

### 步骤1：安装依赖

```bash
# 方式A：使用Poetry（推荐）
poetry install

# 方式B：使用pip
pip install -r requirements.txt
```

### 步骤2：配置环境变量

```bash
# 复制环境变量模板
cp ENV_TEMPLATE.txt .env

# 编辑.env文件
# 最小配置（其他可以保持默认）：
```

**编辑 `.env`，至少修改以下内容**：

```bash
# 必须修改
DATABASE_URL=postgresql://admin:password@localhost:5432/travel_planner
SECRET_KEY=请改为一个随机的32字符以上的字符串

# 其他保持默认即可
ENVIRONMENT=development
PORT=8000
```

### 步骤3：数据库迁移

```bash
# 创建初始迁移
poetry run alembic revision --autogenerate -m "Initial migration - create users table"

# 执行迁移（创建表）
poetry run alembic upgrade head

# 查看迁移状态
poetry run alembic current
```

**如果出现错误**，请确认：
- ✅ Docker的PostgreSQL已启动
- ✅ DATABASE_URL配置正确
- ✅ 数据库`travel_planner`已创建（通常Docker会自动创建）

### 步骤4：启动服务

```bash
# 开发模式（自动重载）
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用简化命令
poetry run dev
```

**服务启动成功标志**：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 AI Travel Planner API v1.0.0 starting...
📝 Environment: development
🌐 CORS origins: ['http://localhost:5173', 'http://localhost:3000']
📚 API docs: http://0.0.0.0:8000/docs
INFO:     Application startup complete.
```

---

## ✅ 验证安装

### 测试1: 健康检查

```bash
curl http://localhost:8000/health
```

**预期输出**：
```json
{
  "status": "ok",
  "environment": "development",
  "version": "1.0.0",
  "service": "backend"
}
```

### 测试2: 访问API文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

你应该看到4个认证相关的端点。

### 测试3: 测试注册接口

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "name": "测试用户"
  }'
```

**预期输出**：
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "test@example.com",
    "name": "测试用户",
    ...
  }
}
```

### 测试4: 测试登录接口

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'
```

### 测试5: 运行pytest测试

```bash
# 运行所有测试
poetry run pytest

# 查看详细输出
poetry run pytest -v

# 查看覆盖率
poetry run pytest --cov=app
```

**预期**：所有测试应该通过 ✅

---

## 🔧 开发工作流

### 日常开发流程

```bash
# 1. 启动服务（开发模式）
poetry run dev

# 2. 访问 http://localhost:8000/docs 测试API

# 3. 修改代码后会自动重载

# 4. 提交前运行测试
poetry run pytest
```

### 修改数据库模型

```bash
# 1. 修改 app/models/xxx.py

# 2. 创建迁移
poetry run alembic revision --autogenerate -m "描述你的修改"

# 3. 检查生成的迁移文件（alembic/versions/xxx.py）

# 4. 执行迁移
poetry run alembic upgrade head

# 如果需要回滚
poetry run alembic downgrade -1
```

---

## ⚠️ 常见问题

### Q1: poetry install 很慢

```bash
# 使用国内镜像
poetry source add --priority=primary aliyun https://mirrors.aliyun.com/pypi/simple/

# 或配置pip镜像
poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/
```

### Q2: 数据库连接失败

```bash
# 检查PostgreSQL容器状态
docker ps | grep postgres

# 查看日志
docker logs travel-planner-postgres

# 测试连接
psql postgresql://admin:password@localhost:5432/travel_planner

# 或使用Python测试
python -c "from app.core.database import engine; print(engine.connect())"
```

### Q3: Alembic找不到模型

确保在 `alembic/env.py` 中导入了所有模型：
```python
from app.models.user import User
from app.models.trip import Trip  # 添加新模型时需要导入
```

### Q4: ModuleNotFoundError

```bash
# 确保在虚拟环境中
poetry shell

# 或使用poetry run
poetry run python app/main.py

# 设置PYTHONPATH
export PYTHONPATH="${PWD}:${PYTHONPATH}"
```

---

## 📚 下一步

完成后端启动后，你可以：

1. ✅ 在 http://localhost:8000/docs 测试所有API
2. ✅ 运行 `poetry run pytest` 确保所有测试通过
3. ✅ 继续阅读 `../doc/PHASE1_AUTH_GUIDE.md` 了解更多细节
4. ✅ 开始前端开发（见前端README）

---

**祝你开发顺利！🚀**

如有问题请查看：
- **完整实现指南**: `../doc/PHASE1_AUTH_GUIDE.md`
- **技术设计**: `../doc/TECHNICAL_DESIGN.md`
- **项目结构**: `../doc/PROJECT_STRUCTURE.md`

