"""
Change Detection - Only trigger AI when content actually changed.
Prevents unnecessary LLM calls and costs.

Rule: Run LLM only if data changed
"""
import hashlib
from typing import Optional, Tuple, Dict
from loguru import logger
from datetime import datetime


class ChangeDetector:
    """
    Detects meaningful changes in content before AI processing.
    
    Saves costs by only processing content that has actually changed.
    
    Example usage:
        detector = ChangeDetector(redis_client)
        
        if await detector.should_process("competitor:123:pricing", new_content):
            # Content changed, process it
            result = await ai_processor.analyze(new_content)
        else:
            # Content unchanged, skip AI processing
            logger.info("No changes detected, skipping AI processing")
    """
    
    def __init__(self, redis_client, default_ttl: int = 86400 * 7):
        """
        Initialize change detector.
        
        Args:
            redis_client: Async Redis client
            default_ttl: Default TTL for stored hashes (7 days)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.prefix = "vigilai:content_hash:"
    
    def compute_hash(self, content: str) -> str:
        """
        Compute content hash for comparison.
        
        Args:
            content: Content string
            
        Returns:
            SHA-256 hash (first 32 characters)
        """
        if not content:
            return "empty"
        
        # Normalize whitespace for more stable hashing
        normalized = " ".join(content.split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    async def has_changed(
        self,
        key: str,
        new_content: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check if content has changed since last check.
        
        Args:
            key: Unique identifier (e.g., "competitor:123:pricing")
            new_content: Current content
            
        Returns:
            (has_changed, previous_hash, new_hash)
        """
        full_key = f"{self.prefix}{key}"
        new_hash = self.compute_hash(new_content)
        
        # Get previous hash
        previous = await self.redis.get(full_key)
        previous_hash = previous.decode() if previous else None
        
        if previous_hash == new_hash:
            logger.debug(f"No change detected for {key} (hash: {new_hash[:8]})")
            return False, previous_hash, new_hash
        
        # Update stored hash
        await self.redis.setex(full_key, self.default_ttl, new_hash)
        
        if previous_hash:
            logger.info(
                f"Change detected for {key}: {previous_hash[:8]} -> {new_hash[:8]}"
            )
        else:
            logger.info(f"First observation for {key}: {new_hash[:8]}")
        
        return True, previous_hash, new_hash
    
    async def should_process(
        self,
        key: str,
        new_content: str,
        force: bool = False
    ) -> bool:
        """
        Determine if content should be processed by AI.
        
        Args:
            key: Content identifier
            new_content: Current content
            force: Force processing even if unchanged
            
        Returns:
            True if AI processing should run
        """
        if force:
            logger.info(f"Force processing for {key}")
            # Still update the hash
            new_hash = self.compute_hash(new_content)
            await self.redis.setex(
                f"{self.prefix}{key}",
                self.default_ttl,
                new_hash
            )
            return True
        
        has_changed, _, _ = await self.has_changed(key, new_content)
        return has_changed
    
    async def get_last_hash(self, key: str) -> Optional[str]:
        """Get the last stored hash for a key"""
        full_key = f"{self.prefix}{key}"
        result = await self.redis.get(full_key)
        return result.decode() if result else None
    
    async def clear_hash(self, key: str) -> bool:
        """
        Clear stored hash to force reprocessing.
        
        Args:
            key: Content identifier
            
        Returns:
            True if hash existed and was cleared
        """
        full_key = f"{self.prefix}{key}"
        result = await self.redis.delete(full_key)
        if result:
            logger.info(f"Cleared hash for {key}, will reprocess on next check")
        return result > 0
    
    async def get_change_stats(self, pattern: str = "*") -> Dict:
        """
        Get statistics about tracked content.
        
        Args:
            pattern: Key pattern to match
            
        Returns:
            Statistics about tracked keys
        """
        search_pattern = f"{self.prefix}{pattern}"
        keys = []
        
        cursor = 0
        while True:
            cursor, batch = await self.redis.scan(
                cursor, match=search_pattern, count=100
            )
            keys.extend(batch)
            if cursor == 0:
                break
        
        return {
            "tracked_content_count": len(keys),
            "pattern": pattern
        }


class ContentDiffTracker:
    """
    Tracks detailed diffs between content versions.
    
    Useful for understanding what specifically changed.
    """
    
    def __init__(self, redis_client, max_history: int = 5):
        """
        Initialize diff tracker.
        
        Args:
            redis_client: Async Redis client
            max_history: Maximum number of versions to keep
        """
        self.redis = redis_client
        self.max_history = max_history
        self.prefix = "vigilai:content_history:"
    
    async def record_version(
        self,
        key: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Record a new content version.
        
        Args:
            key: Content identifier
            content: Content to record
            metadata: Optional metadata about this version
            
        Returns:
            Version ID (timestamp-based)
        """
        import json
        
        full_key = f"{self.prefix}{key}"
        version_id = datetime.utcnow().isoformat()
        
        version_data = {
            "version_id": version_id,
            "content": content[:10000],  # Limit size
            "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "recorded_at": version_id,
            "metadata": metadata or {}
        }
        
        # Add to list (most recent first)
        await self.redis.lpush(full_key, json.dumps(version_data))
        
        # Trim to max history
        await self.redis.ltrim(full_key, 0, self.max_history - 1)
        
        return version_id
    
    async def get_history(self, key: str) -> list:
        """
        Get version history for content.
        
        Args:
            key: Content identifier
            
        Returns:
            List of version records, most recent first
        """
        import json
        
        full_key = f"{self.prefix}{key}"
        versions = await self.redis.lrange(full_key, 0, -1)
        
        return [json.loads(v) for v in versions]
    
    async def get_latest(self, key: str) -> Optional[Dict]:
        """Get most recent version"""
        import json
        
        full_key = f"{self.prefix}{key}"
        latest = await self.redis.lindex(full_key, 0)
        
        return json.loads(latest) if latest else None
    
    async def compare_versions(
        self,
        key: str,
        version1: int = 0,
        version2: int = 1
    ) -> Optional[Dict]:
        """
        Compare two versions of content.
        
        Args:
            key: Content identifier
            version1: Index of first version (0 = most recent)
            version2: Index of second version
            
        Returns:
            Comparison dict with both versions
        """
        history = await self.get_history(key)
        
        if len(history) <= max(version1, version2):
            return None
        
        return {
            "version1": history[version1],
            "version2": history[version2],
            "hash_changed": history[version1]["hash"] != history[version2]["hash"]
        }


async def with_change_detection(
    redis_client,
    key: str,
    content: str,
    processor_func,
    force: bool = False
):
    """
    Utility function to run processor only if content changed.
    
    Args:
        redis_client: Async Redis client
        key: Content identifier
        content: Current content
        processor_func: Async function to call if content changed
        force: Force processing
        
    Returns:
        Processor result or None if no change
    """
    detector = ChangeDetector(redis_client)
    
    if await detector.should_process(key, content, force=force):
        return await processor_func(content)
    
    logger.debug(f"Skipping processor for {key} - no changes")
    return None
