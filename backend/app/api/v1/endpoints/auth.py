"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    TokenResponse,
    UserOut,
    MessageResponse,
    UserProfileUpdate,
    PasswordChange,
    AvatarUploadResponse,
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


@router.get(
    "/profile",
    response_model=UserOut,
    summary="获取用户详细信息",
    description="获取当前登录用户的完整个人信息（需要认证）",
)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    获取用户详细信息
    
    获取当前登录用户的完整个人信息，包括个人简介、手机号等。
    
    Returns:
        UserOut: 用户详细信息
    """
    print(f"获取用户信息 - 用户ID: {current_user.id}")
    print(f"当前头像URL: {current_user.avatar_url}")
    return UserOut.model_validate(current_user)


@router.put(
    "/profile",
    response_model=UserOut,
    summary="更新用户信息",
    description="更新当前登录用户的个人信息（需要认证）",
)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户信息
    
    更新当前登录用户的个人信息，包括姓名、个人简介、手机号等。
    
    - **name**: 用户姓名（可选）
    - **bio**: 个人简介（可选）
    - **phone**: 手机号（可选）
    
    Returns:
        UserOut: 更新后的用户信息
    """
    # Convert Pydantic model to dict, excluding None values
    update_data = profile_data.model_dump(exclude_unset=True)
    
    # Update user profile
    updated_user = AuthService.update_user_profile(db, current_user.id, update_data)
    
    return UserOut.model_validate(updated_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="修改密码",
    description="修改当前登录用户的密码（需要认证）",
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    
    修改当前登录用户的密码，需要验证当前密码。
    
    - **current_password**: 当前密码
    - **new_password**: 新密码（至少6位）
    
    Returns:
        MessageResponse: 修改成功消息
    """
    try:
        # Change password
        AuthService.change_password(
            db, 
            current_user.id, 
            password_data.current_password, 
            password_data.new_password
        )
        
        return MessageResponse(message="密码修改成功")
    except HTTPException as e:
        # 重新抛出HTTP异常以保持状态码
        raise e
    except Exception as e:
        # 记录其他异常并返回500错误
        print(f"修改密码时发生未知错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码时发生内部错误"
        )


@router.post(
    "/upload-avatar",
    response_model=AvatarUploadResponse,
    summary="上传头像",
    description="上传用户头像（需要认证）",
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传头像
    
    上传用户头像文件并更新头像URL。
    
    - **file**: 头像图片文件 (支持 jpg, png, gif 格式)
    
    Returns:
        AvatarUploadResponse: 包含头像URL的响应
    """
    print(f"头像上传请求 - 用户ID: {current_user.id}")
    print(f"文件名: {file.filename}")
    print(f"文件类型: {file.content_type}")
    print(f"文件大小: {file.size}")
    
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        print(f"文件类型验证失败: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持图片文件格式"
        )
    
    # 验证文件大小 (限制为5MB)
    if file.size and file.size > 5 * 1024 * 1024:
        print(f"文件大小验证失败: {file.size} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过5MB"
        )
    
    try:
        # 读取文件内容
        print("开始读取文件内容...")
        file_content = await file.read()
        print(f"文件内容读取成功，大小: {len(file_content)} bytes")
        
        # 生成唯一文件名
        import time
        import hashlib
        import os
        
        timestamp = int(time.time())
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        
        print(f"文件扩展名: {file_extension}")
        
        # 确保文件扩展名是安全的
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        if file_extension.lower() not in allowed_extensions:
            print(f"文件扩展名不在允许列表中，使用默认扩展名")
            file_extension = 'jpg'
        
        # 生成文件名
        filename = f"{current_user.id}_{timestamp}_{file_hash}.{file_extension}"
        print(f"生成的文件名: {filename}")
        
        # 保存文件到本地
        upload_dir = "uploads/avatars"
        print(f"创建上传目录: {upload_dir}")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        print(f"文件保存路径: {file_path}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        print("文件保存成功")
        
        # 生成访问URL
        avatar_url = f"/static/avatars/{filename}"
        print(f"生成的头像URL: {avatar_url}")
        
        # Update avatar URL in database
        print("开始更新数据库...")
        updated_user = AuthService.update_avatar(db, current_user.id, avatar_url)
        print("数据库更新成功")
        
        return AvatarUploadResponse(avatar_url=avatar_url)
        
    except Exception as e:
        print(f"头像上传处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="头像上传处理失败"
        )

