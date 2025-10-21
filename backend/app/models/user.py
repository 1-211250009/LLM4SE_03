"""User database model"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class User(Base):
    """
    User model for authentication and user management
    
    Attributes:
        id: Unique user identifier (UUID)
        email: User email address (unique)
        password_hash: Hashed password (bcrypt)
        name: User display name
        avatar_url: Optional URL to user avatar image
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "users"
    
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique user identifier"
    )
    
    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique)"
    )
    
    password_hash = Column(
        String,
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    name = Column(
        String,
        nullable=False,
        comment="User display name"
    )
    
    avatar_url = Column(
        String,
        nullable=True,
        comment="URL to user avatar image"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Account creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"

