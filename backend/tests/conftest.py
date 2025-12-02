"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

from src.main import app
from src.core.config import settings
from src.models.base import Base

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_vigilai"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@vigilai.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "role": "user"
    }


@pytest.fixture
def test_competitor_data():
    """Test competitor data"""
    return {
        "name": "Test Competitor",
        "domain": "testcompetitor.com",
        "description": "A test competitor",
        "industry": "Technology",
        "pricing_url": "https://testcompetitor.com/pricing",
        "careers_url": "https://testcompetitor.com/careers",
        "blog_url": "https://testcompetitor.com/blog"
    }
