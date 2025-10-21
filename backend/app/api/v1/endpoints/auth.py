"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    TokenResponse,
    UserOut,
    MessageResponse,
)
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账号并返回JWT令牌",
)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    创建新用户账号并自动登录，返回访问令牌和刷新令牌。
    
    - **email**: 邮箱地址（必须唯一）
    - **password**: 密码（至少6位）
    - **name**: 用户名
    
    Returns:
        TokenResponse: 包含access_token, refresh_token和用户信息
    """
    # Register user
    user = AuthService.register_user(db, user_data)
    
    # Create tokens
    tokens = AuthService.create_tokens(user.id)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserOut.model_validate(user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="使用邮箱和密码登录并获取JWT令牌",
)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    验证用户凭据并返回访问令牌和刷新令牌。
    
    - **email**: 邮箱地址
    - **password**: 密码
    
    Returns:
        TokenResponse: 包含access_token, refresh_token和用户信息
    """
    # Authenticate user
    user = AuthService.authenticate_user(db, user_data)
    
    # Create tokens
    tokens = AuthService.create_tokens(user.id)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserOut.model_validate(user)
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    
    使用有效的刷新令牌获取新的访问令牌和刷新令牌。
    
    - **refresh_token**: 刷新令牌
    
    Returns:
        TokenResponse: 新的access_token, refresh_token和用户信息
    """
    # Verify refresh token and get user ID
    user_id = AuthService.verify_refresh_token(token_data.refresh_token)
    
    # Get user
    user = AuthService.get_user_by_id(db, user_id)
    
    # Create new tokens
    tokens = AuthService.create_tokens(user.id)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserOut.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息（需要认证）",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    需要在请求头中包含有效的Bearer token：
    Authorization: Bearer <access_token>
    
    Returns:
        UserOut: 当前用户信息
    """
    return UserOut.model_validate(current_user)


@router.get(
    "/test-protected",
    response_model=MessageResponse,
    summary="测试受保护路由",
    description="测试JWT认证是否正常工作",
)
async def test_protected_route(
    current_user: User = Depends(get_current_user)
):
    """
    测试受保护路由
    
    此端点需要有效的JWT token才能访问。
    用于测试认证中间件是否正常工作。
    
    Returns:
        MessageResponse: 包含用户ID的确认消息
    """
    return MessageResponse(
        message=f"Hello {current_user.name}! Your user ID is {current_user.id}"
    )

