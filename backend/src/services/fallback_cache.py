"""
Fallback Cache - Graceful degradation when services fail.
Serves cached/stale data when live data unavailable.

Examples:
- LLM down → use cached summary
- Scraper blocked → use last version
- API timeout → return stale data with warning
"""
from typing import Optional, Any, Callable
from datetime import datetime
from loguru import logger
import json
import asyncio


class FallbackCache:
    """
    Cache with fallback support for graceful degradation.
    
    Keeps stale data longer than normal TTL to serve as fallback
    when live data sources are unavailable.
    
    Example usage:
        cache = FallbackCache(redis_client)
        
        data, is_stale = await cache.get_with_fallback(
            "competitor:123:pricing",
            fetch_func=scrape_pricing,
            ttl=3600  # 1 hour fresh
        )
        
        if is_stale:
            # Warn user data may be outdated
            logger.warning("Using stale cached data")
    """
    
    def __init__(
        self,
        redis_client,
        stale_ttl: int = 86400,  # 24 hours
        max_stale_age: int = 86400 * 7  # 7 days
    ):
        """
        Initialize fallback cache.
        
        Args:
            redis_client: Async Redis client
            stale_ttl: How long to keep stale data beyond TTL
            max_stale_age: Maximum age of stale data to serve
        """
        self.redis = redis_client
        self.stale_ttl = stale_ttl
        self.max_stale_age = max_stale_age
        self.prefix = "vigilai:fallback:"
    
    async def get_with_fallback(
        self,
        key: str,
        fetch_func: Callable,
        ttl: int = 3600,
        allow_stale: bool = True,
        max_stale_seconds: Optional[int] = None
    ) -> tuple[Any, bool]:
        """
        Get data with automatic fallback to stale cache.
        
        Args:
            key: Cache key
            fetch_func: Async function to fetch fresh data
            ttl: Cache TTL for fresh data
            allow_stale: Whether to serve stale data on failure
            max_stale_seconds: Maximum age of stale data to accept
            
        Returns:
            (data, is_stale)
            
        Raises:
            Original exception if fetch fails and no fallback available
        """
        full_key = f"{self.prefix}{key}"
        max_stale = max_stale_seconds or self.max_stale_age
        
        try:
            # Try to fetch fresh data
            if asyncio.iscoroutinefunction(fetch_func):
                fresh_data = await fetch_func()
            else:
                fresh_data = fetch_func()
            
            # Cache it
            await self._cache_data(full_key, fresh_data, ttl)
            
            return fresh_data, False
            
        except Exception as e:
            logger.warning(f"Failed to fetch fresh data for {key}: {e}")
            
            if not allow_stale:
                raise
            
            # Try to get cached data
            cached = await self._get_cached(full_key, max_stale)
            
            if cached:
                age = cached.get("age_seconds", 0)
                logger.info(
                    f"Using stale cache for {key} (age: {age:.0f}s)"
                )
                return cached["data"], True
            
            # No fallback available
            logger.error(f"No fallback available for {key}")
            raise
    
    async def _cache_data(self, key: str, data: Any, ttl: int):
        """Cache data with timestamp"""
        cache_entry = {
            "data": data,
            "cached_at": datetime.utcnow().isoformat(),
            "ttl": ttl
        }
        
        # Keep beyond TTL for fallback
        total_ttl = ttl + self.stale_ttl
        
        await self.redis.setex(
            key,
            total_ttl,
            json.dumps(cache_entry, default=str)
        )
    
    async def _get_cached(
        self,
        key: str,
        max_stale_seconds: int
    ) -> Optional[dict]:
        """Get cached data if within acceptable staleness"""
        cached = await self.redis.get(key)
        if not cached:
            return None
        
        try:
            entry = json.loads(cached)
        except json.JSONDecodeError:
            return None
        
        cached_at = datetime.fromisoformat(entry["cached_at"])
        age = (datetime.utcnow() - cached_at).total_seconds()
        
        if age > max_stale_seconds:
            logger.warning(
                f"Cached data too stale: {age:.0f}s > {max_stale_seconds}s"
            )
            return None
        
        entry["age_seconds"] = age
        return entry
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get fresh cached data (within TTL).
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if expired/missing
        """
        full_key = f"{self.prefix}{key}"
        cached = await self.redis.get(full_key)
        
        if not cached:
            return None
        
        try:
            entry = json.loads(cached)
        except json.JSONDecodeError:
            return None
        
        cached_at = datetime.fromisoformat(entry["cached_at"])
        age = (datetime.utcnow() - cached_at).total_seconds()
        
        # Check if within original TTL (fresh)
        if age <= entry.get("ttl", 3600):
            return entry["data"]
        
        # Data is stale
        return None
    
    async def get_with_metadata(self, key: str) -> Optional[dict]:
        """
        Get cached data with metadata (age, staleness).
        
        Returns:
            Dict with data, age_seconds, is_stale, cached_at
        """
        full_key = f"{self.prefix}{key}"
        cached = await self.redis.get(full_key)
        
        if not cached:
            return None
        
        try:
            entry = json.loads(cached)
        except json.JSONDecodeError:
            return None
        
        cached_at = datetime.fromisoformat(entry["cached_at"])
        age = (datetime.utcnow() - cached_at).total_seconds()
        ttl = entry.get("ttl", 3600)
        
        return {
            "data": entry["data"],
            "cached_at": entry["cached_at"],
            "age_seconds": age,
            "is_stale": age > ttl,
            "freshness_percent": max(0, 100 - (age / ttl * 100))
        }
    
    async def set(
        self,
        key: str,
        data: Any,
        ttl: int = 3600
    ):
        """
        Set cache with fallback support.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Fresh TTL in seconds
        """
        full_key = f"{self.prefix}{key}"
        await self._cache_data(full_key, data, ttl)
    
    async def invalidate(self, key: str) -> bool:
        """
        Invalidate cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry existed and was deleted
        """
        full_key = f"{self.prefix}{key}"
        result = await self.redis.delete(full_key)
        return result > 0
    
    async def warm_cache(
        self,
        key: str,
        fetch_func: Callable,
        ttl: int = 3600
    ) -> bool:
        """
        Pre-populate cache for fallback.
        
        Useful for warming cache before expected traffic.
        
        Args:
            key: Cache key
            fetch_func: Function to fetch data
            ttl: TTL for cached data
            
        Returns:
            True if cache was warmed successfully
        """
        try:
            if asyncio.iscoroutinefunction(fetch_func):
                data = await fetch_func()
            else:
                data = fetch_func()
            
            await self.set(key, data, ttl)
            logger.info(f"Warmed cache for {key}")
            return True
        except Exception as e:
            logger.warning(f"Failed to warm cache for {key}: {e}")
            return False


class GracefulDegradation:
    """
    Utilities for graceful degradation strategies.
    """
    
    def __init__(self, redis_client):
        self.fallback_cache = FallbackCache(redis_client)
    
    async def with_fallback(
        self,
        operation_name: str,
        primary_func: Callable,
        fallback_func: Optional[Callable] = None,
        cache_key: Optional[str] = None,
        ttl: int = 3600
    ) -> tuple[Any, str]:
        """
        Execute with fallback strategy.
        
        Priority:
        1. Primary function
        2. Cached data
        3. Fallback function
        4. Raise exception
        
        Args:
            operation_name: Name for logging
            primary_func: Primary async function
            fallback_func: Optional fallback function
            cache_key: Optional cache key for caching results
            ttl: Cache TTL
            
        Returns:
            (result, source) where source is "primary", "cache", or "fallback"
        """
        # Try primary
        try:
            if asyncio.iscoroutinefunction(primary_func):
                result = await primary_func()
            else:
                result = primary_func()
            
            # Cache if key provided
            if cache_key:
                await self.fallback_cache.set(cache_key, result, ttl)
            
            return result, "primary"
            
        except Exception as e:
            logger.warning(f"{operation_name} primary failed: {e}")
        
        # Try cache
        if cache_key:
            cached = await self.fallback_cache.get_with_metadata(cache_key)
            if cached:
                logger.info(
                    f"{operation_name} using cached data "
                    f"(age: {cached['age_seconds']:.0f}s)"
                )
                return cached["data"], "cache"
        
        # Try fallback
        if fallback_func:
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    result = await fallback_func()
                else:
                    result = fallback_func()
                
                logger.info(f"{operation_name} using fallback")
                return result, "fallback"
                
            except Exception as e:
                logger.error(f"{operation_name} fallback also failed: {e}")
        
        raise RuntimeError(
            f"{operation_name} failed with no available fallback"
        )


def with_graceful_fallback(
    cache_key: str,
    ttl: int = 3600,
    fallback_value: Any = None
):
    """
    Decorator for graceful degradation.
    
    Usage:
        @with_graceful_fallback("competitor:123:analysis", ttl=3600)
        async def get_competitor_analysis(competitor_id: int):
            return await ai_analyzer.analyze(competitor_id)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            from src.core.redis import get_redis
            redis = await get_redis()
            cache = FallbackCache(redis)
            
            async def fetch():
                return await func(*args, **kwargs)
            
            try:
                data, is_stale = await cache.get_with_fallback(
                    cache_key,
                    fetch,
                    ttl=ttl
                )
                
                if is_stale:
                    logger.warning(
                        f"Returning stale data for {func.__name__}"
                    )
                
                return data
                
            except Exception as e:
                if fallback_value is not None:
                    logger.warning(
                        f"Using fallback value for {func.__name__}: {e}"
                    )
                    return fallback_value
                raise
        
        return wrapper
    return decorator
