"""
Shared utilities for Gemini AI services
"""
import asyncio
import time
from loguru import logger
from typing import Optional

class GeminiRateLimiter:
    """
    Global rate limiter for Gemini API calls to respect free tier quotas.
    
    Free tier limits (Gemini 2.0 Flash):
    - 15 RPM (Requests Per Minute)
    - 1 million TPM (Tokens Per Minute)
    - 1,500 RPD (Requests Per Day)
    
    This limiter enforces a strict interval between requests to stay safely under the RPM limit.
    15 RPM = 1 request every 4 seconds. We use 4.5 seconds to be safe.
    """
    
    def __init__(self, requests_per_minute: int = 10):
        # Default to 10 RPM to be safe (1 request every 6 seconds)
        self.interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
        
    async def acquire(self):
        """
        Acquire permission to make a request.
        Waits if necessary to maintain the rate limit.
        """
        async with self._lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            
            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                logger.debug(f"Rate limiter: Waiting {wait_time:.2f}s before next Gemini call")
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()

# Global instance
# Using 12 RPM (1 req / 5s) to stay under 15 RPM limit with some buffer
gemini_limiter = GeminiRateLimiter(requests_per_minute=12)
