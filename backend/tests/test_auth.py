"""Authentication endpoint tests"""

import pytest
from fastapi.testclient import TestClient


class TestAuthRegistration:
    """Test user registration endpoint"""
    
    def test_register_success(self, client: TestClient, test_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        assert "user" in data
        user = data["user"]
        assert user["email"] == test_user_data["email"]
        assert user["name"] == test_user_data["name"]
        assert "id" in user
        assert "password" not in user  # Password should not be in response
    
    def test_register_duplicate_email(self, client: TestClient, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register with same email
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email"""
        invalid_data = {
            "email": "not-an-email",
            "password": "password123",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self, client: TestClient):
        """Test registration with too short password"""
        invalid_data = {
            "email": "test@example.com",
            "password": "12345",  # Only 5 characters
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error


class TestAuthLogin:
    """Test user login endpoint"""
    
    def test_login_success(self, client: TestClient, registered_user, test_user_data):
        """Test successful login"""
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check tokens
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        assert data["user"]["email"] == test_user_data["email"]
    
    def test_login_wrong_password(self, client: TestClient, registered_user, test_user_data):
        """Test login with wrong password"""
        login_data = {
            "email": test_user_data["email"],
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401


class TestAuthTokenRefresh:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, client: TestClient, registered_user):
        """Test successful token refresh"""
        refresh_token = registered_user["refresh_token"]
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should get new tokens
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != registered_user["access_token"]  # New token
    
    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_refresh_with_access_token(self, client: TestClient, registered_user):
        """Test refresh with access token (should fail)"""
        access_token = registered_user["access_token"]
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}  # Wrong token type
        )
        
        assert response.status_code == 401


class TestAuthProtectedRoutes:
    """Test protected routes requiring authentication"""
    
    def test_get_current_user_success(self, client: TestClient, registered_user):
        """Test getting current user info with valid token"""
        access_token = registered_user["access_token"]
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_user["user"]["email"]
        assert data["name"] == registered_user["user"]["name"]
    
    def test_get_current_user_no_token(self, client: TestClient):
        """Test accessing protected route without token"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # Forbidden without auth header
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test accessing protected route with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_test_protected_route(self, client: TestClient, registered_user):
        """Test the test protected route"""
        access_token = registered_user["access_token"]
        
        response = client.get(
            "/api/v1/auth/test-protected",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert registered_user["user"]["name"] in data["message"]


class TestPasswordSecurity:
    """Test password hashing and verification"""
    
    def test_password_not_returned(self, client: TestClient, test_user_data):
        """Test that password is never returned in responses"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        data = response.json()
        
        # Check all nested structures
        assert "password" not in str(data).lower() or "password_hash" not in str(data)
        assert "password" not in data.get("user", {})
    
    def test_password_is_hashed(self, client: TestClient, test_user_data, db_session):
        """Test that password is hashed in database"""
        from app.models.user import User
        
        # Register user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Check database
        user = db_session.query(User).filter(User.email == test_user_data["email"]).first()
        
        assert user is not None
        assert user.password_hash != test_user_data["password"]  # Should be hashed
        assert user.password_hash.startswith("$2b$")  # Bcrypt hash format

