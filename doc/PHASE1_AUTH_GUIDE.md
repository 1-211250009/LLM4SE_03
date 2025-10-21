# 阶段1：用户认证系统实现指南（Python + FastAPI）

## 📋 阶段概述

**目标**: 实现完整的用户认证系统（注册、登录、JWT认证、权限控制）

**技术栈**:
- 后端: Python 3.11 + FastAPI + SQLAlchemy
- 前端: React 18 + TypeScript + Zustand
- 数据库: PostgreSQL 15
- 认证: JWT (PyJWT + passlib[bcrypt])

**预计时间**: 3-4天

---

## 📦 必需的依赖和工具

### 开发工具

✅ **必须安装**:
- Python >= 3.11
- Poetry >= 1.7.0
- Node.js >= 20.0.0
- Docker + Docker Compose
- Git

验证安装：
```bash
python --version   # 应显示 3.11.x 或更高
poetry --version
node --version
docker --version
```

### Python依赖清单

```bash
# 进入后端目录
cd backend

# 使用Poetry安装所有依赖
poetry add fastapi==0.110.0
poetry add "uvicorn[standard]==0.27.0"
poetry add sqlalchemy==2.0.25
poetry add alembic==1.13.1
poetry add pydantic==2.6.1
poetry add pydantic-settings==2.1.0
poetry add "python-jose[cryptography]==3.3.0"  # JWT
poetry add "passlib[bcrypt]==1.7.4"            # 密码加密
poetry add python-multipart==0.0.9
poetry add psycopg2-binary==2.9.9              # PostgreSQL驱动

# 开发依赖
poetry add --group dev pytest==8.0.0
poetry add --group dev pytest-asyncio==0.23.2
poetry add --group dev httpx==0.26.0
poetry add --group dev black==24.1.1
poetry add --group dev ruff==0.2.0
```

或使用`requirements.txt`:

```txt
fastapi==0.110.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
pydantic==2.6.1
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
psycopg2-binary==2.9.9
```

---

## 🗂️ 目录结构

创建以下目录结构：

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI应用入口
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # 依赖注入（get_db, get_current_user等）
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # 路由聚合
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── auth.py        # 认证端点
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # SQLAlchemy Base
│   │   └── user.py                # User模型
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── auth.py                # Pydantic Schema
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py        # 认证业务逻辑
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库连接
│   │   └── security.py            # JWT和密码工具
│   │
│   └── middleware/
│       ├── __init__.py
│       └── auth.py                # JWT认证中间件
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_auth.py
│
├── .env
├── .env.example
├── pyproject.toml
├── poetry.lock
└── alembic.ini
```

---

## 📝 详细实现步骤

### 步骤1: 配置管理（15分钟）

**创建** `app/core/config.py`：

```python
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    PROJECT_NAME: str = "AI Travel Planner API"
    VERSION: str = "1.0.0"
    
    # 数据库
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT配置
    SECRET_KEY: str  # 至少32字符
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30天
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # 日志
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### 步骤2: 安全工具（30分钟）

**创建** `app/core/security.py`：

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 步骤3: 数据库配置（20分钟）

**创建** `app/core/database.py`：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.ENVIRONMENT == "development"
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 依赖注入：获取数据库会话
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**创建** `app/models/base.py`：

```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

### 步骤4: 用户模型（20分钟）

**创建** `app/models/user.py`：

```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import uuid

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
```

### 步骤5: Pydantic Schema（30分钟）

**创建** `app/schemas/auth.py`：

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

# ===== 请求Schema =====

class UserRegister(BaseModel):
    """用户注册请求"""
    email: EmailStr
    password: str = Field(min_length=6, max_length=100, description="密码，至少6位")
    name: str = Field(min_length=1, max_length=100, description="用户名")

class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    """刷新令牌请求"""
    refresh_token: str

# ===== 响应Schema =====

class UserOut(BaseModel):
    """用户信息响应"""
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2

class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
```

### 步骤6: 认证服务（45分钟）

**创建** `app/services/auth_service.py`：

```python
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)

class AuthService:
    """认证服务"""
    
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        """注册新用户"""
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 创建新用户
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            name=user_data.name
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate_user(db: Session, user_data: UserLogin) -> User:
        """验证用户凭据"""
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        return user
    
    @staticmethod
    def create_tokens(user_id: str) -> dict:
        """创建访问令牌和刷新令牌"""
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def verify_refresh_token(refresh_token: str) -> str:
        """验证刷新令牌并返回user_id"""
        payload = decode_token(refresh_token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return user_id
```

### 步骤7: 依赖注入（30分钟）

**创建** `app/api/deps.py`：

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

# HTTP Bearer认证方案
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户（依赖注入）"""
    token = credentials.credentials
    
    # 解码令牌
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查令牌类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # 获取用户ID
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
```

### 步骤8: API端点实现（1小时）

**创建** `app/api/v1/endpoints/auth.py`：

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    TokenResponse,
    UserOut,
    MessageResponse
)
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    - **email**: 邮箱地址（必需，唯一）
    - **password**: 密码（必需，至少6位）
    - **name**: 用户名（必需）
    """
    # 注册用户
    user = AuthService.register_user(db, user_data)
    
    # 创建令牌
    tokens = AuthService.create_tokens(user.id)
    
    return TokenResponse(
        **tokens,
        user=UserOut.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **email**: 邮箱地址
    - **password**: 密码
    """
    # 验证用户
    user = AuthService.authenticate_user(db, user_data)
    
    # 创建令牌
    tokens = AuthService.create_tokens(user.id)
    
    return TokenResponse(
        **tokens,
        user=UserOut.model_validate(user)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    # 验证刷新令牌
    user_id = AuthService.verify_refresh_token(token_data.refresh_token)
    
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 创建新令牌
    tokens = AuthService.create_tokens(user.id)
    
    return TokenResponse(
        **tokens,
        user=UserOut.model_validate(user)
    )

@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息（需要认证）
    """
    return UserOut.model_validate(current_user)
```

### 步骤9: 路由聚合（15分钟）

**创建** `app/api/v1/api.py`：

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter()

# 包含认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 后续添加其他路由
# api_router.include_router(trip.router, prefix="/trips", tags=["行程"])
```

### 步骤10: 更新主应用（20分钟）

**更新** `app/main.py`：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="基于AG-UI协议的AI旅行规划师后端服务",
    docs_url="/docs",
    redoc_url="/redoc"
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
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION
    }

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
```

### 步骤11: 数据库迁移（30分钟）

```bash
# 初始化Alembic
cd backend
alembic init alembic

# 编辑 alembic/env.py，设置target_metadata
```

**编辑** `alembic/env.py`：

```python
from app.models.base import Base
from app.models.user import User  # 导入所有模型

# ...

target_metadata = Base.metadata
```

**编辑** `alembic.ini`：

```ini
# 使用环境变量
sqlalchemy.url = 
```

**创建迁移脚本**：

```bash
# 创建初始迁移
alembic revision --autogenerate -m "Initial migration - create users table"

# 执行迁移
alembic upgrade head

# 查看迁移历史
alembic history
```

### 步骤12: 前端认证实现（见QUICK_START.md第四章）

前端部分保持不变，使用React + TypeScript + Zustand。

唯一变化：API基础URL改为 `http://localhost:8000`

---

## 🧪 测试验证

### 测试1: 启动服务

```bash
# 1. 启动Docker服务
docker-compose -f docker-compose.dev.yml up -d

# 2. 启动后端
cd backend
poetry run uvicorn app.main:app --reload --port 8000

# 预期输出:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

### 测试2: 健康检查

```bash
curl http://localhost:8000/health

# 预期输出:
# {"status":"ok","environment":"development","version":"1.0.0"}
```

### 测试3: 查看API文档

访问 http://localhost:8000/docs

你应该看到自动生成的Swagger UI文档，包含所有API端点。

### 测试4: 注册用户

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "name": "Test User"
  }'

# 预期输出:
# {
#   "access_token": "eyJhbGciOi...",
#   "refresh_token": "eyJhbGciOi...",
#   "token_type": "bearer",
#   "user": {
#     "id": "uuid...",
#     "email": "test@example.com",
#     "name": "Test User",
#     ...
#   }
# }
```

### 测试5: 登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456"
  }'
```

### 测试6: 获取用户信息（需要认证）

```bash
# 使用上一步获取的access_token
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# 预期输出: 用户信息
```

### 测试7: 运行单元测试

**创建** `tests/test_auth.py`：

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"

def test_login():
    # 先注册
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logintest@example.com",
            "password": "password123",
            "name": "Login Test"
        }
    )
    
    # 再登录
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "logintest@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_get_current_user():
    # 注册并获取token
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "metest@example.com",
            "password": "password123",
            "name": "Me Test"
        }
    )
    token = reg_response.json()["access_token"]
    
    # 获取用户信息
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "metest@example.com"
```

**运行测试**：

```bash
cd backend

# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/test_auth.py

# 查看覆盖率
poetry run pytest --cov=app --cov-report=html
```

---

## ✅ 阶段1完成检查清单

### 后端检查

- [ ] ✅ FastAPI应用可以启动（端口8000）
- [ ] ✅ 可以访问 http://localhost:8000/docs
- [ ] ✅ 数据库连接成功
- [ ] ✅ Alembic迁移执行成功
- [ ] ✅ users表已创建
- [ ] ✅ POST /api/v1/auth/register 可以注册用户
- [ ] ✅ POST /api/v1/auth/login 可以登录
- [ ] ✅ POST /api/v1/auth/refresh 可以刷新token
- [ ] ✅ GET /api/v1/auth/me 需要认证
- [ ] ✅ 密码已加密存储（bcrypt）
- [ ] ✅ JWT token正确生成和验证
- [ ] ✅ 所有pytest测试通过

### 前端检查

- [ ] ✅ React应用可以启动（端口5173）
- [ ] ✅ 登录页面正常显示
- [ ] ✅ 注册页面正常显示
- [ ] ✅ 可以成功注册新用户
- [ ] ✅ 可以成功登录
- [ ] ✅ Token正确存储到localStorage/zustand
- [ ] ✅ 未登录访问/会跳转到/login
- [ ] ✅ 登录后可以访问受保护页面
- [ ] ✅ 可以退出登录
- [ ] ✅ Token过期自动刷新

### 集成检查

- [ ] ✅ 前端可以调用后端API
- [ ] ✅ CORS配置正确
- [ ] ✅ 前后端Token传递正常
- [ ] ✅ API错误正确显示在前端

---

## 🚀 快速启动命令（完整流程）

```bash
# ===== 第1步：启动Docker服务 =====
docker-compose -f docker-compose.dev.yml up -d

# ===== 第2步：后端设置 =====
cd backend

# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑.env，填入真实配置

# 初始化数据库
alembic upgrade head

# 启动后端
poetry run uvicorn app.main:app --reload --port 8000

# ===== 第3步：前端设置（新终端） =====
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑.env: VITE_API_BASE_URL=http://localhost:8000

# 启动前端
npm run dev

# ===== 第4步：验证 =====
# 访问 http://localhost:5173 - 前端应用
# 访问 http://localhost:8000/docs - API文档
```

---

## ⚠️ 常见问题

### Q1: Poetry安装失败

```bash
# 使用官方安装脚本
curl -sSL https://install.python-poetry.org | python3 -

# 或使用pip
pip install poetry

# 配置Poetry在项目内创建虚拟环境
poetry config virtualenvs.in-project true
```

### Q2: PostgreSQL连接失败

```bash
# 检查Docker容器状态
docker ps | grep postgres

# 查看日志
docker logs travel-planner-postgres

# 测试连接
psql postgresql://admin:password@localhost:5432/travel_planner
```

### Q3: Alembic迁移失败

```bash
# 查看当前迁移状态
alembic current

# 回滚到上一个版本
alembic downgrade -1

# 重新迁移
alembic upgrade head

# 如果出错，删除alembic_version表重新开始
```

### Q4: 导入错误 (ModuleNotFoundError)

```bash
# 确保在虚拟环境中
poetry shell

# 或使用poetry run
poetry run python app/main.py

# 检查PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

---

## 📚 参考资源

### Python + FastAPI
- **FastAPI官方文档**: https://fastapi.tiangolo.com/
- **SQLAlchemy文档**: https://docs.sqlalchemy.org/
- **Alembic文档**: https://alembic.sqlalchemy.org/
- **Pydantic文档**: https://docs.pydantic.dev/
- **Poetry文档**: https://python-poetry.org/docs/

### 相关项目文档
- **技术设计**: `doc/TECHNICAL_DESIGN.md`
- **项目结构**: `doc/PROJECT_STRUCTURE.md`
- **开发清单**: `doc/CHECKLIST.md`

---

**祝你开发顺利！🚀**

完成阶段1后，你就拥有了：
✅ 完整的用户认证系统
✅ JWT令牌机制
✅ 受保护的API端点
✅ 为后续功能打下坚实基础！

