"""
User model for authentication
"""
from sqlalchemy import Column, Integer, String, Boolean
from src.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User entity"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Role-based access
    role = Column(String(50), default="user")  # admin, pmm, sales, user
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
