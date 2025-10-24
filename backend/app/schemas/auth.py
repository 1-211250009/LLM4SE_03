"""Authentication schemas for request/response validation"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ===== Request Schemas =====

class UserRegister(BaseModel):
    """User registration request schema"""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Password (at least 6 characters)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User display name"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123",
                "name": "Zhang San"
            }
        }
    )


class UserLogin(BaseModel):
    """User login request schema"""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    )


class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    
    refresh_token: str = Field(..., description="Refresh token")


class UserProfileUpdate(BaseModel):
    """User profile update request schema"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User display name")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Zhang San",
                "bio": "热爱旅行的程序员",
                "phone": "+86 138 0013 8000"
            }
        }
    )


class PasswordChange(BaseModel):
    """Password change request schema"""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword123"
            }
        }
    )


class AvatarUploadResponse(BaseModel):
    """Avatar upload response schema"""
    
    avatar_url: str = Field(..., description="Uploaded avatar URL")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "avatar_url": "https://example.com/avatars/user123.jpg"
            }
        }
    )


# ===== Response Schemas =====

class UserOut(BaseModel):
    """User information response schema"""
    
    id: str = Field(..., description="User ID (UUID)")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, description="User biography")
    phone: Optional[str] = Field(None, description="User phone number")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2: allow ORM mode


class TokenResponse(BaseModel):
    """Authentication token response schema"""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserOut = Field(..., description="User information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "name": "Zhang San",
                    "avatar_url": None,
                    "created_at": "2025-10-20T10:00:00Z"
                }
            }
        }
    )


class MessageResponse(BaseModel):
    """Generic message response schema"""
    
    message: str = Field(..., description="Response message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response schema"""
    
    detail: str = Field(..., description="Error detail message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Email already registered"
            }
        }
    )

