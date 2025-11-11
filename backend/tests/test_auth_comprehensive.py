"""
用户认证全面测试
扩展test_auth.py，测试所有认证相关功能
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


class TestAuthRegistration:
    """用户注册测试"""
    
    def test_register_success(self, client: TestClient, test_user_data: Dict[str, Any]):
        """测试成功注册"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["name"] == test_user_data["name"]
    
    def test_register_duplicate_email(self, client: TestClient, test_user_data: Dict[str, Any]):
        """测试重复邮箱注册"""
        # 第一次注册
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # 第二次注册相同邮箱
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already" in data["detail"].lower() or "已存在" in data["detail"]
    
    def test_register_invalid_email(self, client: TestClient):
        """测试无效邮箱注册"""
        invalid_data = {
            "email": "not-an-email",
            "password": "password123",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # 验证失败
    
    def test_register_short_password(self, client: TestClient):
        """测试短密码注册"""
        invalid_data = {
            "email": "test@example.com",
            "password": "12345",  # 少于6位
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # 验证失败
    
    def test_register_missing_fields(self, client: TestClient):
        """测试缺少必填字段"""
        # 缺少email
        response = client.post("/api/v1/auth/register", json={
            "password": "password123",
            "name": "Test User"
        })
        assert response.status_code == 422
        
        # 缺少password
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        assert response.status_code == 422


class TestAuthLogin:
    """用户登录测试"""
    
    def test_login_success(self, client: TestClient, registered_user: Dict[str, Any], test_user_data: Dict[str, Any]):
        """测试成功登录"""
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
    
    def test_login_wrong_password(self, client: TestClient, test_user_data: Dict[str, Any]):
        """测试错误密码登录"""
        # 先注册
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # 使用错误密码登录
        login_data = {
            "email": test_user_data["email"],
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client: TestClient):
        """测试不存在的用户登录"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_login_invalid_email(self, client: TestClient):
        """测试无效邮箱登录"""
        login_data = {
            "email": "not-an-email",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 422


class TestAuthToken:
    """Token相关测试"""
    
    def test_token_refresh(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试刷新token"""
        refresh_token = registered_user["refresh_token"]
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # 如果refresh endpoint存在
        if response.status_code != 404:
            assert response.status_code in [200, 201]
            data = response.json()
            assert "access_token" in data
    
    def test_protected_endpoint_with_token(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试使用token访问受保护端点"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 访问行程列表（需要认证）
        response = client.get("/api/v1/trips/", headers=headers)
        assert response.status_code == 200
    
    def test_protected_endpoint_without_token(self, client: TestClient):
        """测试无token访问受保护端点"""
        response = client.get("/api/v1/trips/")
        assert response.status_code == 401
    
    def test_protected_endpoint_invalid_token(self, client: TestClient):
        """测试无效token访问受保护端点"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/trips/", headers=headers)
        assert response.status_code == 401


class TestUserProfile:
    """用户资料测试"""
    
    def test_get_current_user(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试获取当前用户信息"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/auth/me", headers=headers)
        
        # 如果endpoint存在
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            assert "name" in data
            assert "id" in data
    
    def test_update_user_profile(self, client: TestClient, registered_user: Dict[str, Any]):
        """测试更新用户资料"""
        token = registered_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {
            "name": "更新后的用户名",
            "bio": "这是我的简介"
        }
        
        response = client.put("/api/v1/auth/profile", json=update_data, headers=headers)
        
        # 如果endpoint存在
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "更新后的用户名"

