"""
AI Project Synthesizer - Rate Limiter

Token bucket rate limiter for API calls.
Supports both synchronous and asynchronous usage.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    """State of a rate limiter."""
    tokens: float
    last_update: float
    requests_made: int = 0
    requests_denied: int = 0


class RateLimiter:
    """
    Token bucket rate limiter.

    Implements token bucket algorithm for smooth rate limiting.
    Supports configurable rates and burst sizes.

    Example:
        limiter = RateLimiter(requests_per_hour=5000, burst_size=100)

        async def make_request():
            await limiter.acquire()
            # Make API call

    Attributes:
        requests_per_hour: Maximum requests per hour
        burst_size: Maximum burst of requests
        tokens: Current token count
    """

    def __init__(
        self,
        requests_per_hour: int = 5000,
        burst_size: int = 100,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_hour: Maximum requests allowed per hour
            burst_size: Maximum tokens that can accumulate
        """
        self.requests_per_hour = requests_per_hour
        self.burst_size = min(burst_size, requests_per_hour)

        # Calculate tokens per second
        self._tokens_per_second = requests_per_hour / 3600

        # Initialize state
        self._tokens = float(self.burst_size)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

        # Statistics
        self._requests_made = 0
        self._requests_denied = 0
        self._wait_time_total = 0.0

        logger.debug(
            f"RateLimiter initialized: {requests_per_hour}/hr, "
            f"burst={burst_size}"
        )

    @property
    def tokens(self) -> float:
        """Current available tokens."""
        self._refill()
        return self._tokens

    @property
    def state(self) -> RateLimitState:
        """Get current state."""
        return RateLimitState(
            tokens=self.tokens,
            last_update=self._last_update,
            requests_made=self._requests_made,
            requests_denied=self._requests_denied,
        )

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update

        # Add tokens for elapsed time
        new_tokens = elapsed * self._tokens_per_second
        self._tokens = min(self.burst_size, self._tokens + new_tokens)
        self._last_update = now

    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Time waited in seconds
        """
        async with self._lock:
            wait_time = 0.0

            while True:
                self._refill()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    self._requests_made += 1
                    self._wait_time_total += wait_time
                    return wait_time

                # Calculate wait time
                needed = tokens - self._tokens
                sleep_time = needed / self._tokens_per_second

                # Cap at reasonable amount
                sleep_time = min(sleep_time, 60.0)

                logger.debug(f"Rate limited, waiting {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                wait_time += sleep_time

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if acquired, False if would need to wait
        """
        self._refill()

        if self._tokens >= tokens:
            self._tokens -= tokens
            self._requests_made += 1
            return True

        self._requests_denied += 1
        return False

    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until tokens will be available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds until available (0 if available now)
        """
        self._refill()

        if self._tokens >= tokens:
            return 0.0

        needed = tokens - self._tokens
        return needed / self._tokens_per_second

    def reset(self) -> None:
        """Reset rate limiter to initial state."""
        self._tokens = float(self.burst_size)
        self._last_update = time.monotonic()
        self._requests_made = 0
        self._requests_denied = 0
        self._wait_time_total = 0.0

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "requests_made": self._requests_made,
            "requests_denied": self._requests_denied,
            "total_wait_time": self._wait_time_total,
            "current_tokens": self.tokens,
            "tokens_per_second": self._tokens_per_second,
        }


class MultiRateLimiter:
    """
    Manages rate limiters for multiple endpoints.

    Example:
        limiter = MultiRateLimiter({
            "search": RateLimiter(requests_per_hour=30),
            "repos": RateLimiter(requests_per_hour=5000),
        })

        await limiter.acquire("search")
    """

    def __init__(self, limiters: Optional[dict[str, RateLimiter]] = None):
        self.limiters = limiters or {}
        self._default = RateLimiter()

    def add_limiter(self, name: str, limiter: RateLimiter) -> None:
        """Add a rate limiter for an endpoint."""
        self.limiters[name] = limiter

    async def acquire(self, endpoint: str, tokens: int = 1) -> float:
        """Acquire tokens for an endpoint."""
        limiter = self.limiters.get(endpoint, self._default)
        return await limiter.acquire(tokens)

    def try_acquire(self, endpoint: str, tokens: int = 1) -> bool:
        """Try to acquire tokens for an endpoint."""
        limiter = self.limiters.get(endpoint, self._default)
        return limiter.try_acquire(tokens)


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts based on API responses.

    Automatically adjusts rate based on 429 responses and
    rate limit headers.
    """

    def __init__(
        self,
        initial_rate: int = 1000,
        min_rate: int = 60,
        max_rate: int = 5000,
    ):
        super().__init__(requests_per_hour=initial_rate)
        self.min_rate = min_rate
        self.max_rate = max_rate
        self._current_rate = initial_rate

    def report_success(self) -> None:
        """Report successful request."""
        # Gradually increase rate
        if self._current_rate < self.max_rate:
            self._current_rate = min(
                self.max_rate,
                int(self._current_rate * 1.01),
            )
            self._update_rate()

    def report_rate_limited(self, retry_after: Optional[int] = None) -> None:
        """Report rate limit hit."""
        # Reduce rate significantly
        self._current_rate = max(
            self.min_rate,
            int(self._current_rate * 0.5),
        )
        self._update_rate()

        logger.warning(f"Rate limited, reducing to {self._current_rate}/hr")

    def set_rate_from_headers(self, remaining: int, reset_time: int) -> None:
        """Set rate based on API headers."""
        if reset_time > 0 and remaining > 0:
            # Calculate sustainable rate
            new_rate = int((remaining / reset_time) * 3600)
            self._current_rate = max(self.min_rate, min(self.max_rate, new_rate))
            self._update_rate()

    def _update_rate(self) -> None:
        """Update internal rate."""
        self.requests_per_hour = self._current_rate
        self._tokens_per_second = self._current_rate / 3600
