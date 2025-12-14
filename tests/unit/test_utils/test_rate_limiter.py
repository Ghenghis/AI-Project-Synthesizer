"""
Unit tests for utils rate limiter module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.utils.rate_limiter import (
    RateLimiter,
    RateLimitState,
)


class TestRateLimitState:
    """Test RateLimitState dataclass."""

    def test_create_state(self):
        """Should create rate limit state."""
        state = RateLimitState(tokens=100.0, last_update=0.0)
        assert state.tokens == 100.0
        assert state.last_update == 0.0

    def test_state_defaults(self):
        """Should have correct defaults."""
        state = RateLimitState(tokens=50.0, last_update=1.0)
        assert state.requests_made == 0
        assert state.requests_denied == 0


class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_create_limiter(self):
        """Should create rate limiter instance."""
        limiter = RateLimiter()
        assert limiter is not None

    def test_create_limiter_with_params(self):
        """Should create limiter with custom params."""
        limiter = RateLimiter(requests_per_hour=1000, burst_size=50)
        assert limiter.requests_per_hour == 1000
        assert limiter.burst_size == 50

    def test_limiter_has_acquire_method(self):
        """Should have acquire method."""
        limiter = RateLimiter()
        assert hasattr(limiter, "acquire")

    @pytest.mark.asyncio
    async def test_acquire_token(self):
        """Should acquire token successfully."""
        limiter = RateLimiter(requests_per_hour=5000, burst_size=100)
        result = await limiter.acquire()
        # Returns wait time (0.0 means no wait needed)
        assert result >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
