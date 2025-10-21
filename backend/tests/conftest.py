"""Pytest configuration and fixtures"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.models.base import Base
from app.core.database import get_db

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test database engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test
    
    Yields:
        Database session
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """
    Create a test client with database session override
    
    Args:
        db_session: Test database session
        
    Yields:
        FastAPI test client
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """
    Test user data fixture
    
    Returns:
        Dictionary with test user data
    """
    return {
        "email": "test@example.com",
        "password": "test password123",
        "name": "Test User"
    }


@pytest.fixture
def registered_user(client: TestClient, test_user_data):
    """
    Create and return a registered user with tokens
    
    Args:
        client: Test client
        test_user_data: Test user data
        
    Returns:
        Registration response with tokens and user info
    """
    response = client.post("/api/v1/auth/register", json=test_user_data)
    return response.json()

