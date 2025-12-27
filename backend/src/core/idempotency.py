"""
Idempotency handling for safe request retries
Prevents duplicate processing of the same request

Key concepts:
- Same request = same result
- Safe retries without side effects
- Content deduplication before processing
"""
from typing import Optional, Any, Tuple
from functools import wraps
import hashlib
import json
from loguru import logger


class IdempotencyManager:
    """
    Redis-backed idempotency key management.
    
    Ensures that the same operation produces the same result,
    enabling safe retries without duplicate side effects.
    
    Use cases:
    - API request deduplication
    - Content hash-based processing
    - Preventing duplicate AI processing
    
    Example usage:
        manager = IdempotencyManager(redis_client)
        
        # Check before processing
        is_duplicate, cached = await manager.check_and_set("order:123")
        if is_duplicate:
            return cached
        
        # Process and store result
        result = await process_order()
        await manager.set_result("order:123", result)
    """
    
    def __init__(self, redis_client, default_ttl: int = 3600):
        """
        Initialize idempotency manager.
        
        Args:
            redis_client: Async Redis client
            default_ttl: Default TTL for idempotency keys in seconds
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.prefix = "vigilai:idempotency:"
    
    def generate_content_hash(self, content: Any) -> str:
        """
        Generate hash for content deduplication.
        
        Args:
            content: Any JSON-serializable content
            
        Returns:
            16-character hash string
        """
        if isinstance(content, str):
            content_str = content
        elif isinstance(content, bytes):
            content_str = content.decode('utf-8', errors='ignore')
        else:
            content_str = json.dumps(content, sort_keys=True, default=str)
        
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    async def check_and_set(
        self,
        key: str,
        result: Any = None,
        ttl: Optional[int] = None
    ) -> Tuple[bool, Optional[Any]]:
        """
        Check if key exists and set if not.
        
        Args:
            key: Idempotency key
            result: Optional result to store immediately
            ttl: Optional custom TTL
            
        Returns:
            (is_duplicate, cached_result)
        """
        full_key = f"{self.prefix}{key}"
        ttl = ttl or self.default_ttl
        
        # Try to get existing result
        existing = await self.redis.get(full_key)
        if existing:
            logger.debug(f"Idempotent hit for key: {key}")
            try:
                cached_data = json.loads(existing)
                return True, cached_data.get("result")
            except json.JSONDecodeError:
                return True, None
        
        # Set new key
        if result is not None:
            data = {"status": "complete", "result": result}
        else:
            data = {"status": "processing"}
        
        await self.redis.setex(
            full_key,
            ttl,
            json.dumps(data, default=str)
        )
        
        return False, None
    
    async def set_result(
        self,
        key: str,
        result: Any,
        ttl: Optional[int] = None
    ):
        """
        Set result for idempotency key.
        
        Args:
            key: Idempotency key
            result: Result to store
            ttl: Optional custom TTL
        """
        full_key = f"{self.prefix}{key}"
        data = {"status": "complete", "result": result}
        
        await self.redis.setex(
            full_key,
            ttl or self.default_ttl,
            json.dumps(data, default=str)
        )
    
    async def set_error(
        self,
        key: str,
        error: str,
        ttl: Optional[int] = None
    ):
        """
        Set error result for idempotency key.
        
        Args:
            key: Idempotency key
            error: Error message
            ttl: Optional custom TTL (default shorter for errors)
        """
        full_key = f"{self.prefix}{key}"
        data = {"status": "error", "error": error}
        
        # Shorter TTL for errors to allow retry
        await self.redis.setex(
            full_key,
            ttl or min(300, self.default_ttl),  # Max 5 min for errors
            json.dumps(data, default=str)
        )
    
    async def should_process_content(
        self,
        content: Any,
        operation: str = "default"
    ) -> Tuple[bool, str]:
        """
        Check if content should be processed (deduplication).
        
        Useful for preventing duplicate AI processing of same content.
        
        Args:
            content: Content to check
            operation: Operation type for key namespacing
            
        Returns:
            (should_process, content_hash)
        """
        content_hash = self.generate_content_hash(content)
        key = f"{operation}:{content_hash}"
        
        is_duplicate, _ = await self.check_and_set(key)
        
        if is_duplicate:
            logger.debug(f"Content already processed: {operation}:{content_hash[:8]}")
        
        return not is_duplicate, content_hash
    
    async def invalidate(self, key: str) -> bool:
        """
        Invalidate an idempotency key.
        
        Args:
            key: Idempotency key to invalidate
            
        Returns:
            True if key existed and was deleted
        """
        full_key = f"{self.prefix}{key}"
        result = await self.redis.delete(full_key)
        return result > 0
    
    async def get_status(self, key: str) -> Optional[str]:
        """
        Get status of an idempotency key.
        
        Args:
            key: Idempotency key
            
        Returns:
            Status string ("processing", "complete", "error") or None
        """
        full_key = f"{self.prefix}{key}"
        existing = await self.redis.get(full_key)
        
        if existing:
            try:
                data = json.loads(existing)
                return data.get("status")
            except json.JSONDecodeError:
                return None
        return None


def idempotent(
    key_header: str = "X-Idempotency-Key",
    key_param: Optional[str] = None,
    ttl: int = 3600
):
    """
    Decorator to make endpoint idempotent.
    
    Checks for idempotency key in headers or query params.
    If key exists and was previously processed, returns cached result.
    
    Usage:
        @router.post("/orders")
        @idempotent(key_header="X-Idempotency-Key")
        async def create_order(request: Request, order: OrderCreate):
            ...
    
    Args:
        key_header: Header name for idempotency key
        key_param: Optional query parameter name for idempotency key
        ttl: TTL for cached results
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import Request, HTTPException
            
            # Find request in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('request')
            
            if not request:
                # No request object, execute normally
                return await func(*args, **kwargs)
            
            # Get idempotency key from header or param
            idem_key = request.headers.get(key_header)
            if not idem_key and key_param:
                idem_key = request.query_params.get(key_param)
            
            if not idem_key:
                # No idempotency key provided, execute normally
                return await func(*args, **kwargs)
            
            # Check for duplicate request
            from src.core.redis import get_redis
            redis = await get_redis()
            manager = IdempotencyManager(redis, default_ttl=ttl)
            
            is_duplicate, cached = await manager.check_and_set(idem_key)
            
            if is_duplicate:
                status = await manager.get_status(idem_key)
                
                if status == "processing":
                    raise HTTPException(
                        status_code=409,
                        detail="Request is currently being processed"
                    )
                
                if status == "error":
                    raise HTTPException(
                        status_code=409,
                        detail="Previous request failed. Retry without idempotency key to reprocess."
                    )
                
                if cached is not None:
                    logger.info(f"Returning cached result for idempotency key: {idem_key}")
                    return cached
            
            try:
                result = await func(*args, **kwargs)
                await manager.set_result(idem_key, result)
                return result
            except Exception as e:
                await manager.set_error(idem_key, str(e))
                raise
        
        return wrapper
    return decorator


class ContentDeduplicator:
    """
    Utility for content-based deduplication.
    
    Useful for preventing duplicate processing of scraped content
    or AI-generated content.
    """
    
    def __init__(self, redis_client, namespace: str = "content"):
        self.redis = redis_client
        self.prefix = f"vigilai:dedup:{namespace}:"
        self.ttl = 86400 * 7  # 7 days
    
    async def is_duplicate(self, content: str) -> Tuple[bool, str]:
        """
        Check if content is a duplicate.
        
        Args:
            content: Content to check
            
        Returns:
            (is_duplicate, content_hash)
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        key = f"{self.prefix}{content_hash}"
        
        exists = await self.redis.exists(key)
        
        if not exists:
            await self.redis.setex(key, self.ttl, "1")
        
        return bool(exists), content_hash
    
    async def mark_seen(self, content_hash: str):
        """Mark content hash as seen"""
        key = f"{self.prefix}{content_hash}"
        await self.redis.setex(key, self.ttl, "1")
