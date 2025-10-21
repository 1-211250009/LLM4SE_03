# AI旅行规划师 - 后端服务

基于 Python + FastAPI + SQLAlchemy 的后端API服务。

## 技术栈

- **Python**: 3.11+
- **FastAPI**: 0.110.0 - 现代高性能Web框架
- **SQLAlchemy**: 2.0+ - ORM
- **Alembic**: 数据库迁移
- **Pydantic**: 数据验证
- **PostgreSQL**: 主数据库
- **Redis**: 缓存
- **PyJWT**: JWT认证
- **Passlib**: 密码加密

## 快速开始

### 前置要求

- Python >= 3.11
- Poetry >= 1.7.0
- PostgreSQL (通过Docker)
- Redis (通过Docker)

### 安装依赖

```bash
# 使用Poetry安装
poetry install

# 或使用pip
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 复制环境变量模板
cp ENV_TEMPLATE.txt .env

# 编辑.env文件，填入真实配置
# 至少需要配置：
# - DATABASE_URL
# - SECRET_KEY
```

### 数据库迁移

```bash
# 初始化Alembic（首次运行）
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head

# 查看迁移历史
alembic history
```

### 启动服务

```bash
# 开发模式（自动重载）
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Poetry脚本
poetry run dev

# 或直接运行
python app/main.py
```

服务启动后访问：
- **API文档（Swagger UI）**: http://localhost:8000/docs
- **API文档（ReDoc）**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## API端点

### 认证相关

| 端点 | 方法 | 功能 | 认证 |
|------|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 | ❌ |
| `/api/v1/auth/login` | POST | 用户登录 | ❌ |
| `/api/v1/auth/refresh` | POST | 刷新令牌 | ❌ |
| `/api/v1/auth/me` | GET | 获取当前用户信息 | ✅ |
| `/api/v1/auth/test-protected` | GET | 测试受保护路由 | ✅ |

### 示例请求

**注册**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "User Name"
  }'
```

**登录**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**获取当前用户**:
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## 测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试文件
poetry run pytest tests/test_auth.py

# 运行测试并查看覆盖率
poetry run pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 项目结构

```
backend/
├── app/
│   ├── api/              # API路由
│   │   ├── deps.py       # 依赖注入
│   │   └── v1/
│   │       ├── api.py    # 路由聚合
│   │       └── endpoints/
│   │           └── auth.py
│   ├── core/             # 核心配置
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/           # SQLAlchemy模型
│   │   ├── base.py
│   │   └── user.py
│   ├── schemas/          # Pydantic Schema
│   │   └── auth.py
│   ├── services/         # 业务逻辑
│   │   └── auth_service.py
│   └── main.py           # FastAPI应用
├── alembic/              # 数据库迁移
├── tests/                # 测试
├── pyproject.toml        # Poetry配置
└── README.md
```

## 开发指南

### 代码格式化

```bash
# 使用Black格式化代码
poetry run black app tests

# 使用Ruff检查代码
poetry run ruff check app tests
```

### 添加新的API端点

1. 在 `app/api/v1/endpoints/` 创建新文件
2. 定义路由（APIRouter）
3. 在 `app/api/v1/api.py` 中注册路由
4. 创建对应的Schema（app/schemas/）
5. 创建对应的Service（app/services/）
6. 编写测试

### 数据库迁移工作流

```bash
# 1. 修改models/下的模型
# 2. 创建迁移
alembic revision --autogenerate -m "描述变更"

# 3. 检查生成的迁移文件
# 4. 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL连接URL | `postgresql://user:pass@localhost:5432/dbname` |
| `SECRET_KEY` | JWT密钥（至少32字符） | `your-secret-key-here` |
| `CORS_ORIGINS` | CORS允许的源（JSON数组） | `["http://localhost:5173"]` |
| `ENVIRONMENT` | 环境（development/production） | `development` |

完整环境变量列表请参考 `ENV_TEMPLATE.txt`。

## 常见问题

### Q: 如何重置数据库？

```bash
# 回滚所有迁移
alembic downgrade base

# 重新执行所有迁移
alembic upgrade head
```

### Q: 如何查看生成的SQL？

在 `app/core/config.py` 中，development环境下会自动开启SQL日志。

### Q: Poetry命令不生效？

确保在虚拟环境中：
```bash
poetry shell
# 或使用
poetry run <command>
```

## 相关文档

- **技术设计**: `../doc/TECHNICAL_DESIGN.md`
- **阶段1实现指南**: `../doc/PHASE1_AUTH_GUIDE.md`
- **API文档**: http://localhost:8000/docs (启动服务后)

## 许可证

MIT License

