"""
Rate limiting middleware for production API security
Uses Redis for distributed rate limiting
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Callable
import time
import hashlib
from loguru import logger
from src.core.config import settings


class RateLimiter:
    """Redis-backed rate limiter"""
    
    def __init__(
        self,
        redis_client,
        requests_per_minute: int = 100,
        requests_per_hour: int = 1000,
        burst_limit: int = 20
    ):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier from request"""
        # Use user ID if authenticated, otherwise IP
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Get client IP, considering proxies
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Get endpoint identifier for granular rate limiting"""
        path = request.url.path
        method = request.method
        return hashlib.md5(f"{method}:{path}".encode()).hexdigest()[:8]
    
    async def is_rate_limited(self, request: Request) -> tuple[bool, dict]:
        """
        Check if request should be rate limited
        Returns (is_limited, rate_info)
        """
        client_id = self._get_client_identifier(request)
        endpoint_key = self._get_endpoint_key(request)
        now = int(time.time())
        
        # Keys for different rate limit windows
        minute_key = f"ratelimit:{client_id}:{endpoint_key}:minute:{now // 60}"
        hour_key = f"ratelimit:{client_id}:{endpoint_key}:hour:{now // 3600}"
        burst_key = f"ratelimit:{client_id}:{endpoint_key}:burst:{now}"
        
        try:
            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Increment counters
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            pipe.incr(burst_key)
            pipe.expire(burst_key, 1)
            
            results = await pipe.execute()
            
            minute_count = results[0]
            hour_count = results[2]
            burst_count = results[4]
            
            rate_info = {
                "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
                "X-RateLimit-Remaining-Minute": str(max(0, self.requests_per_minute - minute_count)),
                "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                "X-RateLimit-Remaining-Hour": str(max(0, self.requests_per_hour - hour_count)),
                "X-RateLimit-Reset": str((now // 60 + 1) * 60)
            }
            
            # Check limits
            if burst_count > self.burst_limit:
                logger.warning(f"Burst limit exceeded for {client_id}")
                return True, rate_info
            
            if minute_count > self.requests_per_minute:
                logger.warning(f"Minute rate limit exceeded for {client_id}")
                return True, rate_info
            
            if hour_count > self.requests_per_hour:
                logger.warning(f"Hour rate limit exceeded for {client_id}")
                return True, rate_info
            
            return False, rate_info
            
        except Exception as e:
            logger.error(f"Rate limiter error: {str(e)}")
            # Fail open - allow request if Redis is unavailable
            return False, {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(
        self,
        app,
        redis_client,
        requests_per_minute: int = 100,
        requests_per_hour: int = 1000,
        burst_limit: int = 20,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            redis_client,
            requests_per_minute,
            requests_per_hour,
            burst_limit
        )
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through rate limiter"""
        
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Check rate limit
        is_limited, rate_info = await self.rate_limiter.is_rate_limited(request)
        
        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please slow down.",
                    "retry_after": 60
                },
                headers=rate_info
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in rate_info.items():
            response.headers[key] = value
        
        return response


# Endpoint-specific rate limiters for sensitive operations
class EndpointRateLimits:
    """Configuration for endpoint-specific rate limits"""
    
    # Define stricter limits for sensitive endpoints
    LIMITS = {
        "/api/v1/auth/login": {"per_minute": 10, "per_hour": 50},
        "/api/v1/auth/register": {"per_minute": 5, "per_hour": 20},
        "/api/v1/competitors/scrape": {"per_minute": 5, "per_hour": 30},
        "/api/v1/logs/analyze": {"per_minute": 10, "per_hour": 100},
    }
    
    @classmethod
    def get_limits(cls, path: str) -> dict:
        """Get rate limits for specific endpoint"""
        for endpoint, limits in cls.LIMITS.items():
            if path.startswith(endpoint):
                return limits
        return {"per_minute": 100, "per_hour": 1000}
