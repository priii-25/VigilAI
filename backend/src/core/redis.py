"""
Redis connection and caching utilities
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
from src.core.config import settings

# Create Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=10,
    decode_responses=True
)


async def get_redis() -> redis.Redis:
    """Get Redis client"""
    return redis.Redis(connection_pool=redis_pool)


class CacheManager:
    """Redis cache manager with common operations"""
    
    def __init__(self):
        self.redis_client = None
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if not self.redis_client:
            self.redis_client = await get_redis()
        return self.redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        client = await self.get_client()
        value = await client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (default 1 hour)"""
        client = await self.get_client()
        if not isinstance(value, str):
            value = json.dumps(value)
        return await client.setex(key, ttl, value)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        client = await self.get_client()
        return await client.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        client = await self.get_client()
        return await client.exists(key) > 0
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        client = await self.get_client()
        keys = await client.keys(pattern)
        if keys:
            return await client.delete(*keys)
        return 0


cache_manager = CacheManager()
