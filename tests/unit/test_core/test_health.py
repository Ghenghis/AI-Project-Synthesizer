"""
Unit tests for core health module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.health import (
    ComponentHealth,
    HealthChecker,
    HealthStatus,
)


class TestHealthStatus:
    """Test health status enum."""

    def test_status_values(self):
        """Should have all status values."""
        assert HealthStatus.HEALTHY is not None
        assert HealthStatus.DEGRADED is not None
        assert HealthStatus.UNHEALTHY is not None


class TestComponentHealth:
    """Test component health dataclass."""

    def test_create_healthy_component(self):
        """Should create healthy component."""
        health = ComponentHealth(
            name="test_component",
            status=HealthStatus.HEALTHY,
            message="All systems operational"
        )
        assert health.name == "test_component"
        assert health.status == HealthStatus.HEALTHY

    def test_create_unhealthy_component(self):
        """Should create unhealthy component."""
        health = ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message="Connection failed"
        )
        assert health.status == HealthStatus.UNHEALTHY
        assert "Connection failed" in health.message


class TestHealthChecker:
    """Test health checker functionality."""

    def test_create_health_checker(self):
        """Should create health checker instance."""
        checker = HealthChecker()
        assert checker is not None

    @pytest.mark.asyncio
    async def test_check_all(self):
        """Should check all components health."""
        checker = HealthChecker()
        result = await checker.check_all()
        assert result is not None

    def test_has_check_all_method(self):
        """Should have check_all method."""
        checker = HealthChecker()
        assert hasattr(checker, 'check_all')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
