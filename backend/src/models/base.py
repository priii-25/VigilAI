"""
Base model for all SQLAlchemy models
"""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
