"""
Unit tests for LLM router module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.router import (
    LLMRouter,
    ProviderType,
    TaskComplexity,
)


class TestProviderType:
    """Test ProviderType enum."""

    def test_local_providers(self):
        """Should have local provider types."""
        assert ProviderType.OLLAMA is not None
        assert ProviderType.LMSTUDIO is not None

    def test_cloud_providers(self):
        """Should have cloud provider types."""
        assert ProviderType.OPENAI is not None
        assert ProviderType.ANTHROPIC is not None


class TestTaskComplexity:
    """Test TaskComplexity enum."""

    def test_complexity_levels(self):
        """Should have complexity levels."""
        assert TaskComplexity.SIMPLE is not None
        # Check that enum has values
        assert len(list(TaskComplexity)) > 0


class TestLLMRouter:
    """Test LLMRouter functionality."""

    def test_create_router(self):
        """Should create LLM router instance."""
        router = LLMRouter()
        assert router is not None

    def test_router_has_route_method(self):
        """Should have route method."""
        router = LLMRouter()
        assert hasattr(router, "route") or hasattr(router, "complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
