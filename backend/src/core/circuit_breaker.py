"""
Circuit Breaker pattern for fault-tolerant external calls
Prevents cascading failures in distributed systems
"""
from functools import wraps
from loguru import logger
from enum import Enum
from typing import Callable, Optional, Any
import time
import threading
import asyncio


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class ServiceCircuitBreaker:
    """
    Circuit breaker with configurable thresholds
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing if service recovered
    
    Example usage:
        breaker = ServiceCircuitBreaker("llm_api", failure_threshold=3)
        
        if breaker.can_execute():
            try:
                result = call_external_api()
                breaker.record_success()
            except Exception:
                breaker.record_failure()
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            half_open_max_calls: Number of test calls in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """Check if request can proceed"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and time.time() - self.last_failure_time >= self.recovery_timeout:
                    self._transition_to_half_open()
                    return True
                return False
            
            # Half-open: allow limited calls
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
    
    def record_success(self):
        """Record successful call"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self._transition_to_closed()
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self.failure_count >= self.failure_threshold:
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        logger.warning(
            f"Circuit breaker '{self.name}' OPENED after {self.failure_count} failures. "
            f"Recovery in {self.recovery_timeout}s"
        )
    
    def _transition_to_half_open(self):
        """Transition to HALF-OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        logger.info(f"Circuit breaker '{self.name}' testing recovery (HALF-OPEN)")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        logger.info(f"Circuit breaker '{self.name}' recovered (CLOSED)")
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting calls"""
    pass


# Pre-configured circuit breakers for different services
CIRCUIT_BREAKERS = {
    "llm_api": ServiceCircuitBreaker("llm_api", failure_threshold=3, recovery_timeout=60),
    "scraper": ServiceCircuitBreaker("scraper", failure_threshold=5, recovery_timeout=120),
    "notion_api": ServiceCircuitBreaker("notion_api", failure_threshold=3, recovery_timeout=60),
    "slack_api": ServiceCircuitBreaker("slack_api", failure_threshold=3, recovery_timeout=60),
    "salesforce_api": ServiceCircuitBreaker("salesforce_api", failure_threshold=3, recovery_timeout=60),
    "perplexity_api": ServiceCircuitBreaker("perplexity_api", failure_threshold=3, recovery_timeout=60),
}


def get_circuit_breaker(name: str) -> Optional[ServiceCircuitBreaker]:
    """Get circuit breaker by name"""
    return CIRCUIT_BREAKERS.get(name)


def with_circuit_breaker(
    breaker_name: str,
    fallback: Optional[Callable] = None,
    exceptions_to_track: tuple = (Exception,)
):
    """
    Decorator to wrap function with circuit breaker
    
    Args:
        breaker_name: Name of circuit breaker to use
        fallback: Optional fallback function if circuit is open
        exceptions_to_track: Tuple of exception types that count as failures
    
    Usage:
        @with_circuit_breaker("llm_api", fallback=get_cached_result)
        async def call_llm(prompt: str) -> str:
            return await llm_client.generate(prompt)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            breaker = CIRCUIT_BREAKERS.get(breaker_name)
            if not breaker:
                logger.warning(f"Circuit breaker '{breaker_name}' not found, executing without protection")
                return await func(*args, **kwargs)
            
            if not breaker.can_execute():
                logger.warning(f"Circuit breaker '{breaker_name}' is OPEN, rejecting call to {func.__name__}")
                if fallback:
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{breaker_name}' is open. "
                    f"Service will recover in {breaker.recovery_timeout}s"
                )
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except exceptions_to_track as e:
                breaker.record_failure()
                logger.error(f"Circuit breaker '{breaker_name}' recorded failure: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            breaker = CIRCUIT_BREAKERS.get(breaker_name)
            if not breaker:
                return func(*args, **kwargs)
            
            if not breaker.can_execute():
                if fallback:
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpenError(f"Circuit breaker '{breaker_name}' is open")
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except exceptions_to_track as e:
                breaker.record_failure()
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def reset_all_circuit_breakers():
    """Reset all circuit breakers to closed state (for testing)"""
    for breaker in CIRCUIT_BREAKERS.values():
        breaker.state = CircuitState.CLOSED
        breaker.failure_count = 0
        breaker.success_count = 0
    logger.info("All circuit breakers reset to CLOSED state")


def get_all_circuit_breaker_states() -> list:
    """Get states of all circuit breakers"""
    return [breaker.get_state() for breaker in CIRCUIT_BREAKERS.values()]
