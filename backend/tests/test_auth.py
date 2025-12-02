"""
Test authentication endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, test_user_data):
    """Test user registration"""
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, test_user_data):
    """Test user login"""
    # First register
    await client.post("/api/v1/auth/register", json=test_user_data)
    
    # Then login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials"""
    login_data = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
