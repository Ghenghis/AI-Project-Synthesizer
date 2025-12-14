"""
Unit tests for core plugins module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.plugins import (
    Plugin,
    PluginManager,
    PluginMetadata,
    PluginType,
)


class TestPluginType:
    """Test PluginType enum."""

    def test_plugin_types_exist(self):
        """Should have all plugin types."""
        assert PluginType.PLATFORM.value == "platform"
        assert PluginType.SYNTHESIS.value == "synthesis"
        assert PluginType.ANALYSIS.value == "analysis"
        assert PluginType.VOICE.value == "voice"
        assert PluginType.LLM.value == "llm"


class TestPluginMetadata:
    """Test PluginMetadata dataclass."""

    def test_create_plugin_metadata(self):
        """Should create plugin metadata."""
        meta = PluginMetadata(
            name="test_plugin", version="1.0.0", description="A test plugin"
        )
        assert meta.name == "test_plugin"
        assert meta.version == "1.0.0"

    def test_plugin_metadata_defaults(self):
        """Should have correct defaults."""
        meta = PluginMetadata(name="test", version="1.0.0", description="Test")
        assert meta.author == ""
        assert meta.plugin_type == PluginType.PLATFORM


class TestPluginManager:
    """Test PluginManager functionality."""

    def test_create_plugin_manager(self):
        """Should create plugin manager instance."""
        manager = PluginManager()
        assert manager is not None

    def test_list_plugins(self):
        """Should list available plugins."""
        manager = PluginManager()
        plugins = manager.list_plugins()
        assert isinstance(plugins, list)

    def test_get_plugin(self):
        """Should get plugin if exists."""
        manager = PluginManager()
        plugin = manager.get_plugin("nonexistent")
        assert plugin is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
