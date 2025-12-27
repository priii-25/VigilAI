"""
Dead Letter Queue (DLQ) for handling failed tasks
Enables retry with exponential backoff, monitoring, and analysis of failures

Flow: Task fails → Retry (3x with backoff) → DLQ → Manual/Auto recovery
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger
import json
import asyncio


class DeadLetterQueue:
    """
    Redis-backed dead letter queue for failed tasks
    
    Features:
    - Automatic retry with exponential backoff
    - Dead letter storage for permanent failures
    - Statistics and monitoring
    - Manual retry capability
    
    Example usage:
        dlq = DeadLetterQueue(redis_client)
        
        try:
            await process_task(task_data)
        except Exception as e:
            await dlq.add_failed_task("process_task", task_data, str(e))
    """
    
    def __init__(
        self,
        redis_client,
        max_retries: int = 3,
        retry_delays: Optional[List[int]] = None,
        dlq_retention_days: int = 7
    ):
        """
        Initialize DLQ.
        
        Args:
            redis_client: Async Redis client
            max_retries: Maximum retry attempts before moving to DLQ
            retry_delays: Delays between retries in seconds (exponential backoff)
            dlq_retention_days: Days to keep dead letters
        """
        self.redis = redis_client
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [60, 300, 900]  # 1min, 5min, 15min
        self.dlq_retention_days = dlq_retention_days
        
        # Redis keys
        self.dlq_key = "vigilai:dlq:dead_letters"
        self.retry_key = "vigilai:dlq:retry_queue"
        self.stats_key = "vigilai:dlq:stats"
    
    async def add_failed_task(
        self,
        task_name: str,
        task_args: Dict,
        error: str,
        retry_count: int = 0,
        task_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add failed task to retry queue or DLQ.
        
        Args:
            task_name: Name of the failed task
            task_args: Task arguments for retry
            error: Error message/details
            retry_count: Current retry attempt (0 = first failure)
            task_id: Optional unique task ID
            metadata: Optional additional metadata
            
        Returns:
            Task ID
        """
        task_id = task_id or f"{task_name}:{datetime.utcnow().timestamp()}"
        
        task_data = {
            "id": task_id,
            "task_name": task_name,
            "args": task_args,
            "error": str(error)[:5000],  # Limit error size
            "retry_count": retry_count,
            "failed_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "status": "pending_retry" if retry_count < self.max_retries else "dead"
        }
        
        if retry_count < self.max_retries:
            # Schedule retry with exponential backoff
            delay = self.retry_delays[min(retry_count, len(self.retry_delays) - 1)]
            retry_at = datetime.utcnow().timestamp() + delay
            
            await self.redis.zadd(
                self.retry_key,
                {json.dumps(task_data): retry_at}
            )
            
            # Update stats
            await self._increment_stat("retries_scheduled")
            
            logger.warning(
                f"Task {task_name} (id={task_id}) scheduled for retry "
                f"#{retry_count + 1} in {delay}s"
            )
        else:
            # Max retries exceeded, move to DLQ
            await self.redis.lpush(self.dlq_key, json.dumps(task_data))
            
            # Update stats
            await self._increment_stat("dead_letters")
            
            logger.error(
                f"Task {task_name} (id={task_id}) moved to DLQ after "
                f"{self.max_retries} failed retries. Error: {error[:200]}"
            )
        
        return task_id
    
    async def get_pending_retries(self, limit: int = 100) -> List[Dict]:
        """
        Get tasks ready for retry.
        
        Returns:
            List of task data dicts ready for retry
        """
        now = datetime.utcnow().timestamp()
        
        # Get tasks where retry_at <= now
        tasks = await self.redis.zrangebyscore(
            self.retry_key, "-inf", now, start=0, num=limit
        )
        
        result = []
        for task_json in tasks:
            task_data = json.loads(task_json)
            result.append(task_data)
            # Remove from retry queue
            await self.redis.zrem(self.retry_key, task_json)
        
        if result:
            logger.info(f"Retrieved {len(result)} tasks ready for retry")
        
        return result
    
    async def get_dead_letters(
        self,
        limit: int = 100,
        task_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Get tasks in DLQ.
        
        Args:
            limit: Maximum number of dead letters to return
            task_name: Optional filter by task name
            
        Returns:
            List of dead letter task dicts
        """
        tasks = await self.redis.lrange(self.dlq_key, 0, limit - 1)
        result = [json.loads(t) for t in tasks]
        
        if task_name:
            result = [t for t in result if t["task_name"] == task_name]
        
        return result
    
    async def retry_dead_letter(self, task_id: str) -> bool:
        """
        Manually retry a dead letter task.
        
        Args:
            task_id: ID of dead letter to retry
            
        Returns:
            True if task was found and re-queued
        """
        tasks = await self.redis.lrange(self.dlq_key, 0, -1)
        
        for task_json in tasks:
            task_data = json.loads(task_json)
            if task_data["id"] == task_id:
                # Reset retry count and re-queue
                task_data["retry_count"] = 0
                task_data["status"] = "pending_retry"
                task_data["manually_retried_at"] = datetime.utcnow().isoformat()
                
                await self.redis.lrem(self.dlq_key, 1, task_json)
                await self.redis.zadd(
                    self.retry_key,
                    {json.dumps(task_data): datetime.utcnow().timestamp()}
                )
                
                await self._increment_stat("manual_retries")
                logger.info(f"Dead letter task {task_id} queued for retry")
                return True
        
        logger.warning(f"Dead letter task {task_id} not found")
        return False
    
    async def delete_dead_letter(self, task_id: str) -> bool:
        """
        Delete a dead letter task (acknowledge and remove).
        
        Args:
            task_id: ID of dead letter to delete
            
        Returns:
            True if task was found and deleted
        """
        tasks = await self.redis.lrange(self.dlq_key, 0, -1)
        
        for task_json in tasks:
            task_data = json.loads(task_json)
            if task_data["id"] == task_id:
                await self.redis.lrem(self.dlq_key, 1, task_json)
                await self._increment_stat("acknowledged")
                logger.info(f"Dead letter task {task_id} acknowledged and removed")
                return True
        
        return False
    
    async def get_stats(self) -> Dict:
        """
        Get DLQ statistics.
        
        Returns:
            Dict with queue counts and statistics
        """
        dlq_count = await self.redis.llen(self.dlq_key)
        pending_count = await self.redis.zcard(self.retry_key)
        
        stats = await self.redis.hgetall(self.stats_key)
        # Handle both bytes (real Redis) and strings (mocks)
        if stats:
            parsed = {}
            for k, v in stats.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = int(v.decode() if isinstance(v, bytes) else v)
                parsed[key] = val
            stats = parsed
        else:
            stats = {}
        
        return {
            "dead_letter_count": dlq_count,
            "pending_retry_count": pending_count,
            "total_retries_scheduled": stats.get("retries_scheduled", 0),
            "total_dead_letters": stats.get("dead_letters", 0),
            "total_manual_retries": stats.get("manual_retries", 0),
            "total_acknowledged": stats.get("acknowledged", 0)
        }
    
    async def _increment_stat(self, stat_name: str, amount: int = 1):
        """Increment a statistic counter"""
        await self.redis.hincrby(self.stats_key, stat_name, amount)
    
    async def cleanup_old_dead_letters(self) -> int:
        """
        Remove dead letters older than retention period.
        
        Returns:
            Number of dead letters removed
        """
        cutoff = datetime.utcnow().timestamp() - (self.dlq_retention_days * 86400)
        tasks = await self.redis.lrange(self.dlq_key, 0, -1)
        
        removed = 0
        for task_json in tasks:
            task_data = json.loads(task_json)
            failed_at = datetime.fromisoformat(task_data["failed_at"]).timestamp()
            
            if failed_at < cutoff:
                await self.redis.lrem(self.dlq_key, 1, task_json)
                removed += 1
        
        if removed:
            logger.info(f"Cleaned up {removed} old dead letters")
        
        return removed


class DLQRetryProcessor:
    """
    Processor for retrying tasks from the DLQ retry queue.
    
    Run as a background task to process pending retries.
    """
    
    def __init__(
        self,
        dlq: DeadLetterQueue,
        task_handlers: Dict[str, callable],
        check_interval: int = 30
    ):
        """
        Initialize retry processor.
        
        Args:
            dlq: DeadLetterQueue instance
            task_handlers: Dict mapping task names to handler functions
            check_interval: Seconds between retry queue checks
        """
        self.dlq = dlq
        self.task_handlers = task_handlers
        self.check_interval = check_interval
        self._running = False
    
    async def start(self):
        """Start the retry processor loop"""
        self._running = True
        logger.info("DLQ Retry Processor started")
        
        while self._running:
            try:
                await self._process_retries()
            except Exception as e:
                logger.error(f"Error in DLQ retry processor: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the retry processor"""
        self._running = False
        logger.info("DLQ Retry Processor stopped")
    
    async def _process_retries(self):
        """Process pending retries"""
        tasks = await self.dlq.get_pending_retries()
        
        for task_data in tasks:
            task_name = task_data["task_name"]
            handler = self.task_handlers.get(task_name)
            
            if not handler:
                logger.error(f"No handler for task: {task_name}")
                await self.dlq.add_failed_task(
                    task_name,
                    task_data["args"],
                    f"No handler registered for task: {task_name}",
                    retry_count=self.dlq.max_retries,  # Send directly to DLQ
                    task_id=task_data["id"]
                )
                continue
            
            try:
                logger.info(f"Retrying task {task_name} (attempt {task_data['retry_count'] + 1})")
                
                if asyncio.iscoroutinefunction(handler):
                    await handler(**task_data["args"])
                else:
                    handler(**task_data["args"])
                
                logger.info(f"Task {task_name} succeeded on retry")
                
            except Exception as e:
                logger.warning(f"Task {task_name} failed on retry: {e}")
                await self.dlq.add_failed_task(
                    task_name,
                    task_data["args"],
                    str(e),
                    retry_count=task_data["retry_count"] + 1,
                    task_id=task_data["id"],
                    metadata=task_data.get("metadata")
                )
