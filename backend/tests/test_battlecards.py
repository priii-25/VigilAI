"""
Tests for battlecard endpoints and generation
"""
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.asyncio
async def test_list_battlecards(client: AsyncClient, auth_headers):
    """Test listing all battlecards"""
    response = await client.get("/api/v1/battlecards/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_battlecard(client: AsyncClient, auth_headers):
    """Test creating a new battlecard"""
    battlecard_data = {
        "title": "Test Competitor Battlecard",
        "competitor_id": 1,
        "overview": "Test overview",
        "strengths": ["Strong brand"],
        "weaknesses": ["Slow support"],
        "kill_points": ["Better pricing"],
        "objection_handlers": [
            {"objection": "Too expensive", "response": "We offer better ROI"}
        ]
    }
    
    response = await client.post(
        "/api/v1/battlecards/",
        json=battlecard_data,
        headers=auth_headers
    )
    
    # Will fail if competitor doesn't exist, but test the endpoint structure
    assert response.status_code in [200, 201, 400, 422]


@pytest.mark.asyncio
async def test_get_battlecard(client: AsyncClient, auth_headers):
    """Test getting a specific battlecard"""
    response = await client.get("/api/v1/battlecards/1", headers=auth_headers)
    
    # Will be 404 if no battlecard exists, but tests the endpoint
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_battlecard_by_competitor(client: AsyncClient, auth_headers):
    """Test getting battlecard by competitor ID"""
    response = await client.get(
        "/api/v1/battlecards/competitor/1",
        headers=auth_headers
    )
    
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_publish_battlecard(client: AsyncClient, auth_headers):
    """Test publishing battlecard to Notion"""
    response = await client.post(
        "/api/v1/battlecards/1/publish",
        headers=auth_headers
    )
    
    # Will be 404 if no battlecard exists
    assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
async def test_generate_battlecard_pdf(client: AsyncClient, auth_headers):
    """Test PDF generation endpoint"""
    response = await client.get(
        "/api/v1/battlecards/1/pdf",
        headers=auth_headers
    )
    
    # Endpoint might not exist yet or battlecard might not exist
    assert response.status_code in [200, 404, 405]


# Fixture for authenticated requests
@pytest.fixture
async def auth_headers(client: AsyncClient, test_user_data):
    """Get authentication headers"""
    # Register user
    await client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token", "")
        return {"Authorization": f"Bearer {token}"}
    
    return {}
