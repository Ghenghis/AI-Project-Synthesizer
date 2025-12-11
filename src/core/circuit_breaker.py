"""
AI Project Synthesizer - Circuit Breaker Pattern

Enterprise-grade circuit breaker implementation for external API calls.
Prevents cascade failures and provides automatic recovery with configurable thresholds.
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 60.0      # Seconds to wait before trying again
    success_threshold: int = 2          # Successes needed to close circuit
    timeout: float = 30.0               # Call timeout in seconds
    expected_exception: type = Exception  # Exception type that counts as failure

    def __post_init__(self):
        """Validate configuration."""
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold must be > 0")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")
        if self.success_threshold <= 0:
            raise ValueError("success_threshold must be > 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    failures: int = 0
    successes: int = 0
    total_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.failures / self.total_calls) * 100


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit is open."""
    pass


class CircuitTimeoutError(CircuitBreakerError):
    """Raised when call times out."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for protecting external service calls.
    
    Implements the circuit breaker pattern to prevent cascade failures.
    Automatically opens when failures exceed threshold, closes when service recovers.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None, name: str = "default"):
        """
        Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
            name: Name for logging and monitoring
        """
        self.config = config or CircuitBreakerConfig()
        self.name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change = time.time()
        self._stats = CircuitBreakerStats()

        logger.info(f"CircuitBreaker '{name}' initialized with config: {self.config}")

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get current statistics."""
        self._stats.failures = self._failure_count
        self._stats.successes = self._success_count
        self._stats.last_failure_time = self._last_failure_time
        return self._stats

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset from OPEN to HALF_OPEN."""
        if self._state != CircuitState.OPEN:
            return False

        if self._last_failure_time is None:
            return False

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.recovery_timeout

    def _record_failure(self):
        """Record a failure and potentially open circuit."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._stats.last_failure_time = self._last_failure_time

        if self._state == CircuitState.HALF_OPEN:
            # Immediate failure in half-open state
            self._state = CircuitState.OPEN
            self._stats.state_changes += 1
            logger.warning(f"Circuit '{self.name}' returned to OPEN state")
        elif self._failure_count >= self.config.failure_threshold:
            # Open circuit due to too many failures
            self._state = CircuitState.OPEN
            self._stats.state_changes += 1
            logger.warning(
                f"Circuit '{self.name}' opened after {self._failure_count} failures"
            )

    def _record_success(self):
        """Record a success and potentially close circuit."""
        self._success_count += 1
        self._stats.last_success_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            if self._success_count >= self.config.success_threshold:
                # Close circuit after enough successes
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._stats.state_changes += 1
                logger.info(f"Circuit '{self.name}' closed after recovery")
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            self._failure_count = max(0, self._failure_count - 1)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function return value
            
        Raises:
            CircuitOpenError: If circuit is open
            CircuitTimeoutError: If call times out
            Exception: Original exception if call fails
        """
        # Check if circuit should attempt reset
        if self._should_attempt_reset():
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0
            self._stats.state_changes += 1
            logger.info(f"Circuit '{self.name}' moved to HALF_OPEN for testing")

        # Reject calls if circuit is open
        if self._state == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit '{self.name}' is open")

        # Execute call with timeout
        try:
            self._stats.total_calls += 1

            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )

            self._record_success()
            return result

        except asyncio.TimeoutError as e:
            self._record_failure()
            raise CircuitTimeoutError(f"Call timed out after {self.config.timeout}s") from e
        except self.config.expected_exception as e:
            self._record_failure()
            logger.warning(f"Circuit '{self.name}' recorded failure: {type(e).__name__}")
            raise
        except Exception as e:
            # Unexpected exceptions also count as failures
            self._record_failure()
            logger.error(f"Circuit '{self.name}' unexpected error: {type(e).__name__}: {e}")
            raise

    def reset(self):
        """Manually reset circuit to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._stats.state_changes += 1
        logger.info(f"Circuit '{self.name}' manually reset to CLOSED")

    def force_open(self):
        """Manually force circuit to open state."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        self._stats.state_changes += 1
        logger.warning(f"Circuit '{self.name}' manually forced to OPEN")

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "stats": {
                "failures": self._stats.failures,
                "successes": self._stats.successes,
                "total_calls": self._stats.total_calls,
                "failure_rate": self._stats.failure_rate,
                "state_changes": self._stats.state_changes,
            }
        }


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create circuit breaker by name.
        
        Args:
            name: Circuit breaker name
            config: Configuration for new breaker
            
        Returns:
            Circuit breaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(config, name)
        return self._breakers[name]

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()


# Global registry
_registry = CircuitBreakerRegistry()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
    timeout: float = 30.0,
    expected_exception: type = Exception
):
    """
    Decorator for applying circuit breaker to async functions.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        recovery_timeout: Seconds to wait before retry
        success_threshold: Successes needed to close
        timeout: Call timeout
        expected_exception: Exception type that counts as failure
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exception=expected_exception
        )

        breaker = _registry.get_breaker(name, config)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        # Add circuit breaker methods to wrapper
        wrapper.get_status = breaker.get_status
        wrapper.reset = breaker.reset
        wrapper.force_open = breaker.force_open

        return wrapper

    return decorator


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """
    Get circuit breaker from global registry.
    
    Args:
        name: Circuit breaker name
        
    Returns:
        Circuit breaker or None if not found
    """
    return _registry._breakers.get(name)


def get_all_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers."""
    return _registry.get_all_status()


def reset_all_circuit_breakers():
    """Reset all circuit breakers."""
    _registry.reset_all()


# Pre-configured breakers for common services
GITHUB_BREAKER_CONFIG = CircuitBreakerConfig(
    failure_threshold=10,
    recovery_timeout=300.0,  # 5 minutes
    success_threshold=3,
    timeout=30.0,
    expected_exception=Exception
)

HUGGINGFACE_BREAKER_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=180.0,  # 3 minutes
    success_threshold=2,
    timeout=45.0,
    expected_exception=Exception
)

OLLAMA_BREAKER_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=60.0,   # 1 minute
    success_threshold=2,
    timeout=120.0,  # 2 minutes for LLM calls
    expected_exception=Exception
)
