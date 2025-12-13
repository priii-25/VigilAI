"""
Tests for Rate Limiting Middleware
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import Request
from starlette.testclient import TestClient

from src.core.rate_limiter import (
    RateLimiter,
    RateLimitMiddleware,
    EndpointRateLimits
)


class TestRateLimiter:
    """Test RateLimiter class"""
    
    @pytest.fixture
    def mock_redis(self):
        redis = MagicMock()
        redis.pipeline.return_value = MagicMock()
        return redis
    
    @pytest.fixture
    def rate_limiter(self, mock_redis):
        return RateLimiter(
            redis_client=mock_redis,
            requests_per_minute=100,
            requests_per_hour=1000,
            burst_limit=20
        )
    
    def test_get_client_identifier_with_user(self, rate_limiter):
        """Test client identification with authenticated user"""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = "user123"
        mock_request.headers = {}
        
        client_id = rate_limiter._get_client_identifier(mock_request)
        
        assert client_id == "user:user123"
    
    def test_get_client_identifier_with_ip(self, rate_limiter):
        """Test client identification with IP address"""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock(spec=[])  # No user_id attribute
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        
        # Make getattr return None for user_id
        del mock_request.state.user_id
        
        client_id = rate_limiter._get_client_identifier(mock_request)
        
        assert "192.168.1.100" in client_id
    
    def test_get_client_identifier_with_forwarded(self, rate_limiter):
        """Test client identification with X-Forwarded-For header"""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock(spec=[])
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1, 10.0.0.2"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        client_id = rate_limiter._get_client_identifier(mock_request)
        
        assert "10.0.0.1" in client_id
    
    def test_get_endpoint_key(self, rate_limiter):
        """Test endpoint key generation"""
        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/competitors"
        mock_request.method = "GET"
        
        key1 = rate_limiter._get_endpoint_key(mock_request)
        
        # Same endpoint should give same key
        key2 = rate_limiter._get_endpoint_key(mock_request)
        assert key1 == key2
        
        # Different endpoint should give different key
        mock_request.url.path = "/api/v1/battlecards"
        key3 = rate_limiter._get_endpoint_key(mock_request)
        assert key1 != key3


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware"""
    
    def test_exclude_paths_health(self):
        """Test health endpoint is excluded"""
        mock_redis = MagicMock()
        mock_app = MagicMock()
        
        middleware = RateLimitMiddleware(
            app=mock_app,
            redis_client=mock_redis
        )
        
        assert "/health" in middleware.exclude_paths
        assert "/docs" in middleware.exclude_paths
    
    def test_custom_exclude_paths(self):
        """Test custom exclude paths"""
        mock_redis = MagicMock()
        mock_app = MagicMock()
        
        middleware = RateLimitMiddleware(
            app=mock_app,
            redis_client=mock_redis,
            exclude_paths=["/custom", "/admin"]
        )
        
        assert "/custom" in middleware.exclude_paths
        assert "/admin" in middleware.exclude_paths


class TestEndpointRateLimits:
    """Test endpoint-specific rate limit configuration"""
    
    def test_get_limits_auth_login(self):
        """Test limits for login endpoint"""
        limits = EndpointRateLimits.get_limits("/api/v1/auth/login")
        
        assert limits['per_minute'] == 10
        assert limits['per_hour'] == 50
    
    def test_get_limits_auth_register(self):
        """Test limits for register endpoint"""
        limits = EndpointRateLimits.get_limits("/api/v1/auth/register")
        
        assert limits['per_minute'] == 5
        assert limits['per_hour'] == 20
    
    def test_get_limits_scrape(self):
        """Test limits for scrape endpoint"""
        limits = EndpointRateLimits.get_limits("/api/v1/competitors/scrape")
        
        assert limits['per_minute'] == 5
        assert limits['per_hour'] == 30
    
    def test_get_limits_default(self):
        """Test default limits for unknown endpoint"""
        limits = EndpointRateLimits.get_limits("/api/v1/unknown")
        
        assert limits['per_minute'] == 100
        assert limits['per_hour'] == 1000
    
    def test_get_limits_logs_analyze(self):
        """Test limits for log analysis endpoint"""
        limits = EndpointRateLimits.get_limits("/api/v1/logs/analyze")
        
        assert limits['per_minute'] == 10
        assert limits['per_hour'] == 100


class TestRateLimitIntegration:
    """Integration tests for rate limiting"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_check_success(self):
        """Test successful rate limit check"""
        mock_redis = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[
            5,    # minute count
            True, # minute expire
            50,   # hour count
            True, # hour expire
            1,    # burst count
            True  # burst expire
        ])
        mock_redis.pipeline.return_value = mock_pipe
        
        rate_limiter = RateLimiter(
            redis_client=mock_redis,
            requests_per_minute=100,
            requests_per_hour=1000,
            burst_limit=20
        )
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock(spec=[])
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "GET"
        
        is_limited, rate_info = await rate_limiter.is_rate_limited(mock_request)
        
        assert is_limited is False
        assert "X-RateLimit-Limit-Minute" in rate_info
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded"""
        mock_redis = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[
            150,  # minute count - exceeds limit
            True,
            500,
            True,
            5,
            True
        ])
        mock_redis.pipeline.return_value = mock_pipe
        
        rate_limiter = RateLimiter(
            redis_client=mock_redis,
            requests_per_minute=100,
            requests_per_hour=1000,
            burst_limit=20
        )
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock(spec=[])
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "GET"
        
        is_limited, rate_info = await rate_limiter.is_rate_limited(mock_request)
        
        assert is_limited is True
