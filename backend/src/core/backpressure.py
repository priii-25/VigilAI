"""
Backpressure control for preventing system overload.
Slows down producers when consumers are lagging.

Key concept: Don't overwhelm downstream services
Example: Pause scraping if AI processor queue > threshold
"""
from typing import Dict, Optional
from loguru import logger
import asyncio


class BackpressureController:
    """
    Controls flow between producers and consumers.
    
    Monitors queue depths and applies backpressure when
    consumers can't keep up with producers.
    
    Example:
        controller = BackpressureController(redis)
        
        # Before submitting work
        if await controller.check_backpressure("ai_processor_queue"):
            await controller.wait_for_capacity("ai_processor_queue")
        
        # Now safe to submit
        await submit_to_queue(task)
    """
    
    def __init__(self, redis_client):
        """
        Initialize backpressure controller.
        
        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client
        
        # Queue thresholds (can be customized)
        self.thresholds: Dict[str, int] = {
            "scraper_queue": 100,
            "ai_processor_queue": 50,
            "notification_queue": 200,
            "battlecard_queue": 30,
            "default": 100
        }
        
        # Celery queue prefix
        self.celery_prefix = "celery"
    
    def set_threshold(self, queue_name: str, threshold: int):
        """Set threshold for a specific queue"""
        self.thresholds[queue_name] = threshold
        logger.debug(f"Set backpressure threshold for {queue_name}: {threshold}")
    
    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get current queue length.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Number of items in queue
        """
        # Try different queue key patterns
        keys_to_try = [
            f"{self.celery_prefix}:{queue_name}",
            f"vigilai:{queue_name}",
            queue_name
        ]
        
        for key in keys_to_try:
            length = await self.redis.llen(key)
            if length > 0:
                return length
        
        return 0
    
    async def check_backpressure(self, queue_name: str) -> bool:
        """
        Check if backpressure should be applied.
        
        Args:
            queue_name: Queue to check
            
        Returns:
            True if producer should pause/slow down
        """
        threshold = self.thresholds.get(queue_name, self.thresholds["default"])
        queue_length = await self.get_queue_length(queue_name)
        
        if queue_length > threshold:
            logger.warning(
                f"Backpressure triggered for {queue_name}: "
                f"{queue_length}/{threshold} items (threshold exceeded)"
            )
            return True
        
        return False
    
    async def get_pressure_level(self, queue_name: str) -> float:
        """
        Get pressure level as percentage of threshold.
        
        Args:
            queue_name: Queue to check
            
        Returns:
            Pressure level (0.0 to 1.0+, >1.0 means over threshold)
        """
        threshold = self.thresholds.get(queue_name, self.thresholds["default"])
        queue_length = await self.get_queue_length(queue_name)
        
        return queue_length / threshold if threshold > 0 else 0.0
    
    async def wait_for_capacity(
        self,
        queue_name: str,
        check_interval: float = 5.0,
        max_wait: float = 300.0,
        target_pressure: float = 0.8
    ):
        """
        Wait until queue has capacity.
        
        Blocks until queue pressure is below target or max wait exceeded.
        
        Args:
            queue_name: Queue to monitor
            check_interval: Seconds between checks
            max_wait: Maximum seconds to wait
            target_pressure: Target pressure level (0.8 = 80% of threshold)
            
        Raises:
            BackpressureTimeoutError: If max wait exceeded
        """
        total_waited = 0
        
        while True:
            pressure = await self.get_pressure_level(queue_name)
            
            if pressure < target_pressure:
                if total_waited > 0:
                    logger.info(
                        f"Backpressure relieved for {queue_name} "
                        f"(pressure: {pressure:.1%}, waited: {total_waited}s)"
                    )
                return
            
            if total_waited >= max_wait:
                logger.error(
                    f"Backpressure timeout for {queue_name}: "
                    f"waited {max_wait}s, pressure still at {pressure:.1%}"
                )
                raise BackpressureTimeoutError(
                    f"Queue {queue_name} still overloaded after {max_wait}s "
                    f"(pressure: {pressure:.1%})"
                )
            
            logger.info(
                f"Waiting for {queue_name} capacity... "
                f"(pressure: {pressure:.1%}, waited: {total_waited}s)"
            )
            
            await asyncio.sleep(check_interval)
            total_waited += check_interval
    
    async def get_all_pressures(self) -> Dict[str, float]:
        """
        Get pressure levels for all monitored queues.
        
        Returns:
            Dict mapping queue names to pressure levels
        """
        pressures = {}
        for queue_name in self.thresholds:
            if queue_name != "default":
                pressures[queue_name] = await self.get_pressure_level(queue_name)
        return pressures
    
    async def should_throttle(
        self,
        queue_name: str,
        throttle_threshold: float = 0.7
    ) -> bool:
        """
        Check if producer should throttle (slow down) based on pressure.
        
        Different from backpressure which blocks entirely.
        Throttling means reducing rate, not stopping.
        
        Args:
            queue_name: Queue to check
            throttle_threshold: Pressure level at which to start throttling
            
        Returns:
            True if producer should slow down
        """
        pressure = await self.get_pressure_level(queue_name)
        return pressure >= throttle_threshold
    
    async def get_recommended_delay(
        self,
        queue_name: str,
        base_delay: float = 0.0,
        max_delay: float = 10.0
    ) -> float:
        """
        Get recommended delay based on queue pressure.
        
        Higher pressure = longer delay (adaptive rate limiting).
        
        Args:
            queue_name: Queue to check
            base_delay: Base delay when no pressure
            max_delay: Maximum delay when at/over threshold
            
        Returns:
            Recommended delay in seconds
        """
        pressure = await self.get_pressure_level(queue_name)
        
        if pressure < 0.5:
            return base_delay
        
        # Linear interpolation from 0.5 pressure to 1.0
        # At 0.5 pressure: base_delay
        # At 1.0 pressure: max_delay
        factor = min(1.0, (pressure - 0.5) / 0.5)
        return base_delay + (max_delay - base_delay) * factor


class BackpressureTimeoutError(Exception):
    """Raised when backpressure wait times out"""
    pass


def with_backpressure(
    queue_name: str,
    max_wait: float = 60.0
):
    """
    Decorator to apply backpressure before function execution.
    
    Waits for queue capacity before executing the decorated function.
    
    Usage:
        @with_backpressure("ai_processor_queue")
        async def process_with_ai(data):
            # Will wait if queue is too full
            await submit_to_ai_queue(data)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            from src.core.redis import get_redis
            redis = await get_redis()
            controller = BackpressureController(redis)
            
            # Wait for capacity
            await controller.wait_for_capacity(queue_name, max_wait=max_wait)
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class AdaptiveRateLimiter:
    """
    Rate limiter that adapts based on downstream pressure.
    
    Automatically slows down when consumers are struggling.
    """
    
    def __init__(
        self,
        redis_client,
        base_rate: float = 10.0,  # requests per second
        min_rate: float = 1.0,
        queue_name: str = "default"
    ):
        self.redis = redis_client
        self.base_rate = base_rate
        self.min_rate = min_rate
        self.queue_name = queue_name
        self.controller = BackpressureController(redis_client)
    
    async def get_current_rate(self) -> float:
        """Get current adaptive rate based on pressure"""
        pressure = await self.controller.get_pressure_level(self.queue_name)
        
        if pressure < 0.5:
            return self.base_rate
        
        # Reduce rate as pressure increases
        # At 100% pressure, rate = min_rate
        factor = 1.0 - min(1.0, (pressure - 0.5) / 0.5)
        return self.min_rate + (self.base_rate - self.min_rate) * factor
    
    async def get_delay(self) -> float:
        """Get delay between requests based on current rate"""
        rate = await self.get_current_rate()
        return 1.0 / rate if rate > 0 else 1.0
