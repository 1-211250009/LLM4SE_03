"""Authentication service for user registration and login"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from typing import Dict


class AuthService:
    """
    Authentication service handling user registration, login, and token management
    """
    
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        """
        Register a new user
        
        Args:
            db: Database session
            user_data: User registration data (email, password, name)
            
        Returns:
            Created User object
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=password_hash,
            name=user_data.name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def authenticate_user(db: Session, user_data: UserLogin) -> User:
        """
        Authenticate user credentials
        
        Args:
            db: Database session
            user_data: User login data (email, password)
            
        Returns:
            User object if credentials are valid
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by email
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    @staticmethod
    def create_tokens(user_id: str) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user
        
        Args:
            user_id: User ID (UUID string)
            
        Returns:
            Dictionary with access_token, refresh_token, and token_type
        """
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def verify_refresh_token(refresh_token: str) -> str:
        """
        Verify refresh token and extract user ID
        
        Args:
            refresh_token: JWT refresh token string
            
        Returns:
            User ID from token payload
            
        Raises:
            HTTPException: If token is invalid or wrong type
        """
        payload = decode_token(refresh_token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type, expected refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user ID
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID (UUID string)
            
        Returns:
            User object
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    
    @staticmethod
    def update_user_profile(db: Session, user_id: str, profile_data: dict) -> User:
        """
        Update user profile information
        
        Args:
            db: Database session
            user_id: User ID (UUID string)
            profile_data: Profile data to update (name, bio, phone)
            
        Returns:
            Updated User object
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update only provided fields
        for field, value in profile_data.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: str, current_password: str, new_password: str) -> User:
        """
        Change user password
        
        Args:
            db: Database session
            user_id: User ID (UUID string)
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Updated User object
            
        Raises:
            HTTPException: If current password is incorrect or user not found
        """
        print(f"修改密码请求 - 用户ID: {user_id}")
        print(f"当前密码长度: {len(current_password) if current_password else 0}")
        print(f"新密码长度: {len(new_password) if new_password else 0}")
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"用户未找到: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        print(f"找到用户: {user.email}")
        
        # Verify current password
        password_valid = verify_password(current_password, user.password_hash)
        print(f"密码验证结果: {password_valid}")
        
        if not password_valid:
            print("当前密码验证失败")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        
        db.commit()
        db.refresh(user)
        
        print("密码修改成功")
        return user
    
    @staticmethod
    def update_avatar(db: Session, user_id: str, avatar_url: str) -> User:
        """
        Update user avatar URL
        
        Args:
            db: Database session
            user_id: User ID (UUID string)
            avatar_url: New avatar URL
            
        Returns:
            Updated User object
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        print(f"更新前头像URL: {user.avatar_url}")
        user.avatar_url = avatar_url
        print(f"更新后头像URL: {user.avatar_url}")
        
        db.commit()
        db.refresh(user)
        
        print(f"刷新后头像URL: {user.avatar_url}")
        return user

