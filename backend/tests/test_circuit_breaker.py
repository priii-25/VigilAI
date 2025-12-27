"""
Tests for Circuit Breaker pattern implementation
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.circuit_breaker import (
    ServiceCircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    with_circuit_breaker,
    CIRCUIT_BREAKERS,
    reset_all_circuit_breakers,
    get_all_circuit_breaker_states
)


class TestServiceCircuitBreaker:
    """Tests for ServiceCircuitBreaker class"""
    
    def setup_method(self):
        """Reset circuit breakers before each test"""
        reset_all_circuit_breakers()
    
    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=3)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_can_execute_when_closed(self):
        """Should allow execution when circuit is closed"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=3)
        assert breaker.can_execute() is True
    
    def test_records_success(self):
        """Should reset failure count on success"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=3)
        breaker.failure_count = 2
        breaker.record_success()
        assert breaker.failure_count == 0
    
    def test_opens_after_threshold_failures(self):
        """Should open circuit after threshold failures"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=3)
        
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.can_execute() is False
    
    def test_rejects_calls_when_open(self):
        """Should reject calls when circuit is open"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=1, recovery_timeout=60)
        breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.can_execute() is False
    
    def test_transitions_to_half_open_after_timeout(self):
        """Should transition to half-open after recovery timeout"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=1, recovery_timeout=1)
        breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should transition to half-open when checked
        assert breaker.can_execute() is True
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_closes_after_successful_half_open_calls(self):
        """Should close circuit after successful calls in half-open"""
        breaker = ServiceCircuitBreaker(
            "test",
            failure_threshold=1,
            recovery_timeout=0,
            half_open_max_calls=2
        )
        breaker.record_failure()
        
        # Force transition to half-open
        breaker.state = CircuitState.HALF_OPEN
        breaker.half_open_calls = 0
        breaker.success_count = 0
        
        # Record successful calls
        breaker.record_success()
        breaker.record_success()
        
        assert breaker.state == CircuitState.CLOSED
    
    def test_reopens_on_failure_in_half_open(self):
        """Should reopen circuit if failure occurs in half-open"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=1, recovery_timeout=0)
        breaker.record_failure()
        
        # Force transition to half-open
        breaker.state = CircuitState.HALF_OPEN
        
        # Record failure
        breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
    
    def test_get_state_returns_dict(self):
        """Should return state as dictionary"""
        breaker = ServiceCircuitBreaker("test", failure_threshold=3, recovery_timeout=30)
        state = breaker.get_state()
        
        assert state["name"] == "test"
        assert state["state"] == "closed"
        assert state["failure_threshold"] == 3
        assert state["recovery_timeout"] == 30


class TestCircuitBreakerDecorator:
    """Tests for with_circuit_breaker decorator"""
    
    def setup_method(self):
        """Reset circuit breakers before each test"""
        reset_all_circuit_breakers()
    
    @pytest.mark.asyncio
    async def test_decorator_allows_successful_call(self):
        """Decorator should allow successful function call"""
        @with_circuit_breaker("llm_api")
        async def success_func():
            return "success"
        
        result = await success_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_decorator_records_failure(self):
        """Decorator should record failure and re-raise exception"""
        @with_circuit_breaker("llm_api")
        async def failure_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await failure_func()
        
        breaker = CIRCUIT_BREAKERS["llm_api"]
        assert breaker.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_decorator_uses_fallback_when_open(self):
        """Decorator should use fallback when circuit is open"""
        async def fallback_func():
            return "fallback"
        
        @with_circuit_breaker("llm_api", fallback=fallback_func)
        async def main_func():
            return "main"
        
        # Force circuit open
        breaker = CIRCUIT_BREAKERS["llm_api"]
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = time.time()
        
        result = await main_func()
        assert result == "fallback"
    
    @pytest.mark.asyncio
    async def test_decorator_raises_error_when_open_no_fallback(self):
        """Decorator should raise error when open without fallback"""
        @with_circuit_breaker("llm_api")
        async def main_func():
            return "main"
        
        # Force circuit open
        breaker = CIRCUIT_BREAKERS["llm_api"]
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = time.time()
        
        with pytest.raises(CircuitBreakerOpenError):
            await main_func()


class TestCircuitBreakerRegistry:
    """Tests for circuit breaker registry functions"""
    
    def setup_method(self):
        reset_all_circuit_breakers()
    
    def test_reset_all_circuit_breakers(self):
        """Should reset all circuit breakers to closed"""
        # Open some circuits
        CIRCUIT_BREAKERS["llm_api"].state = CircuitState.OPEN
        CIRCUIT_BREAKERS["scraper"].state = CircuitState.HALF_OPEN
        
        reset_all_circuit_breakers()
        
        for breaker in CIRCUIT_BREAKERS.values():
            assert breaker.state == CircuitState.CLOSED
            assert breaker.failure_count == 0
    
    def test_get_all_circuit_breaker_states(self):
        """Should return states for all circuit breakers"""
        states = get_all_circuit_breaker_states()
        
        assert isinstance(states, list)
        assert len(states) == len(CIRCUIT_BREAKERS)
        
        names = [s["name"] for s in states]
        assert "llm_api" in names
        assert "scraper" in names
