"""
Unit tests for core circuit breaker module.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

from src.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerStats,
    CircuitBreakerError,
    CircuitOpenError,
)


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration."""
    
    def test_default_config(self):
        """Should create config with defaults."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold >= 1
        assert config.recovery_timeout > 0
        assert config.success_threshold >= 1
    
    def test_custom_config(self):
        """Should create config with custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=60.0,
            success_threshold=3
        )
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 3
    
    def test_invalid_failure_threshold(self):
        """Should reject invalid failure threshold."""
        with pytest.raises(ValueError):
            CircuitBreakerConfig(failure_threshold=0)
    
    def test_invalid_recovery_timeout(self):
        """Should reject invalid recovery timeout."""
        with pytest.raises(ValueError):
            CircuitBreakerConfig(recovery_timeout=0)


class TestCircuitBreakerStats:
    """Test circuit breaker stats."""
    
    def test_default_stats(self):
        """Should have default values."""
        stats = CircuitBreakerStats()
        assert stats.failures == 0
        assert stats.successes == 0
        assert stats.total_calls == 0
    
    def test_failure_rate_zero_calls(self):
        """Should return 0% failure rate with no calls."""
        stats = CircuitBreakerStats()
        assert stats.failure_rate == 0.0
    
    def test_failure_rate_calculation(self):
        """Should calculate failure rate correctly."""
        stats = CircuitBreakerStats(failures=2, total_calls=10)
        assert stats.failure_rate == 20.0


class TestCircuitState:
    """Test circuit state enum."""
    
    def test_states_exist(self):
        """Should have all required states."""
        assert CircuitState.CLOSED is not None
        assert CircuitState.OPEN is not None
        assert CircuitState.HALF_OPEN is not None
    
    def test_state_values(self):
        """Should have correct string values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_initial_state_closed(self):
        """Should start in closed state."""
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_breaker_name(self):
        """Should have correct name."""
        cb = CircuitBreaker(name="my_circuit")
        assert cb.name == "my_circuit"
    
    def test_default_name(self):
        """Should use default name."""
        cb = CircuitBreaker()
        assert cb.name == "default"
    
    def test_custom_config(self):
        """Should accept custom config."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config=config, name="test")
        assert cb.config.failure_threshold == 5
    
    def test_stats_property(self):
        """Should return stats."""
        cb = CircuitBreaker(name="test")
        stats = cb.stats
        assert isinstance(stats, CircuitBreakerStats)
    
    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Should execute successful calls."""
        cb = CircuitBreaker(name="test")
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_failed_call_records_failure(self):
        """Should track failures."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config=config, name="test")
        
        async def fail_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        
        assert cb._failure_count >= 1
    
    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        """Should open after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config=config, name="test")
        
        async def fail_func():
            raise ValueError("test error")
        
        # Trigger failures to open circuit
        for _ in range(3):
            try:
                await cb.call(fail_func)
            except (ValueError, CircuitOpenError):
                pass
        
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerErrors:
    """Test circuit breaker error classes."""
    
    def test_circuit_breaker_error(self):
        """Should create base error."""
        error = CircuitBreakerError("test")
        assert str(error) == "test"
    
    def test_circuit_open_error(self):
        """Should create open error."""
        error = CircuitOpenError("circuit is open")
        assert isinstance(error, CircuitBreakerError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
