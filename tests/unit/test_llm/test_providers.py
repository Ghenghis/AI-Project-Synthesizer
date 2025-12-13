"""
Unit tests for LLM providers module.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.llm.providers.base import (
    ProviderConfig,
    ProviderStatus,
    ProviderCapabilities,
    ProviderType,
)


class TestProviderType:
    """Test ProviderType enum."""
    
    def test_local_providers(self):
        """Should have local provider types."""
        assert ProviderType.OLLAMA.value == "ollama"
        assert ProviderType.LMSTUDIO.value == "lmstudio"
    
    def test_cloud_providers(self):
        """Should have cloud provider types."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"


class TestProviderConfig:
    """Test ProviderConfig dataclass."""
    
    def test_create_provider_config(self):
        """Should create provider config."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            name="test_provider",
            host="http://localhost:11434"
        )
        assert config.name == "test_provider"
        assert config.host == "http://localhost:11434"
    
    def test_config_defaults(self):
        """Should have correct defaults."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            name="test",
            host="localhost"
        )
        assert config.enabled is True
        assert config.timeout == 120.0


class TestProviderStatus:
    """Test ProviderStatus enum."""
    
    def test_status_values(self):
        """Should have all status values."""
        assert ProviderStatus.HEALTHY.value == "healthy"
        assert ProviderStatus.DEGRADED.value == "degraded"
        assert ProviderStatus.UNHEALTHY.value == "unhealthy"


class TestProviderCapabilities:
    """Test ProviderCapabilities dataclass."""
    
    def test_create_capabilities(self):
        """Should create capabilities."""
        caps = ProviderCapabilities(
            streaming=True,
            function_calling=False,
            vision=False
        )
        assert caps.streaming is True
        assert caps.function_calling is False
    
    def test_capability_defaults(self):
        """Should have correct defaults."""
        caps = ProviderCapabilities()
        assert caps.streaming is True
        assert caps.chat is True
        assert caps.max_context_length == 8192


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
