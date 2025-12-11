"""
Tests for new professional features:
- Caching
- Plugins
- Telemetry
- Health checks
- Version management
"""

import pytest
import asyncio
from pathlib import Path
import tempfile


class TestCaching:
    """Test caching layer."""
    
    @pytest.mark.asyncio
    async def test_memory_cache_set_get(self):
        """Test memory cache set and get."""
        from src.core.cache import MemoryCache
        
        cache = MemoryCache()
        
        await cache.set("test_key", {"data": "value"})
        result = await cache.get("test_key")
        
        assert result == {"data": "value"}
    
    @pytest.mark.asyncio
    async def test_memory_cache_expiration(self):
        """Test cache expiration."""
        from src.core.cache import MemoryCache
        import time
        
        cache = MemoryCache()
        
        await cache.set("expire_key", "value", ttl_seconds=1)
        
        # Should exist immediately
        assert await cache.get("expire_key") == "value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert await cache.get("expire_key") is None
    
    @pytest.mark.asyncio
    async def test_memory_cache_stats(self):
        """Test cache statistics."""
        from src.core.cache import MemoryCache
        
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        await cache.get("key1")
        await cache.get("key1")
        await cache.get("missing")
        
        stats = await cache.stats()
        
        assert stats["entries"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
    
    @pytest.mark.asyncio
    async def test_sqlite_cache(self, tmp_path):
        """Test SQLite cache."""
        from src.core.cache import SQLiteCache
        
        db_path = tmp_path / "test.db"
        cache = SQLiteCache(db_path)
        
        try:
            await cache.set("key", {"nested": {"data": 123}})
            result = await cache.get("key")
            
            assert result == {"nested": {"data": 123}}
        finally:
            # Ensure cache is closed before cleanup
            if hasattr(cache, 'close'):
                await cache.close()
            elif hasattr(cache, '_conn') and cache._conn:
                cache._conn.close()
    
    @pytest.mark.asyncio
    async def test_cache_manager(self):
        """Test cache manager."""
        from src.core.cache import CacheManager
        
        cache = CacheManager(backend="memory")
        
        await cache.set("test", [1, 2, 3])
        result = await cache.get("test")
        
        assert result == [1, 2, 3]
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        from src.core.cache import CacheManager
        
        cache = CacheManager(backend="memory")
        
        key1 = cache.cache_key("query", platform="github")
        key2 = cache.cache_key("query", platform="github")
        key3 = cache.cache_key("different", platform="github")
        
        assert key1 == key2
        assert key1 != key3


class TestPlugins:
    """Test plugin system."""
    
    def test_plugin_metadata(self):
        """Test plugin metadata creation."""
        from src.core.plugins import PluginMetadata, PluginType
        
        meta = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            plugin_type=PluginType.PLATFORM,
        )
        
        assert meta.name == "test-plugin"
        assert meta.version == "1.0.0"
        assert meta.plugin_type == PluginType.PLATFORM
    
    def test_plugin_manager_creation(self):
        """Test plugin manager creation."""
        from src.core.plugins import PluginManager
        
        manager = PluginManager()
        
        assert manager is not None
        assert len(manager.list_plugins()) == 0
    
    def test_plugin_registration(self):
        """Test plugin registration."""
        from src.core.plugins import (
            PluginManager, PlatformPlugin, PluginMetadata, PluginType
        )
        
        class TestPlugin(PlatformPlugin):
            @property
            def metadata(self):
                return PluginMetadata(
                    name="test",
                    version="1.0.0",
                    description="Test",
                    plugin_type=PluginType.PLATFORM,
                )
            
            async def search(self, query, max_results=10):
                return []
        
        manager = PluginManager()
        plugin = TestPlugin()
        
        result = manager.register_plugin(plugin)
        
        assert result is True
        assert len(manager.list_plugins()) == 1
        assert manager.get_plugin("test") is plugin


class TestTelemetry:
    """Test telemetry system."""
    
    def test_telemetry_disabled_by_default(self):
        """Test telemetry is disabled by default."""
        from src.core.telemetry import TelemetryCollector
        
        telemetry = TelemetryCollector()
        
        assert telemetry.is_enabled() is False
    
    def test_telemetry_enable_disable(self):
        """Test enabling and disabling telemetry."""
        from src.core.telemetry import TelemetryCollector, TelemetryConfig
        
        config = TelemetryConfig(local_storage_path=Path("/tmp/test_telemetry.json"))
        telemetry = TelemetryCollector(config)
        
        telemetry.enable()
        assert telemetry.is_enabled() is True
        
        telemetry.disable()
        assert telemetry.is_enabled() is False
    
    def test_telemetry_no_tracking_when_disabled(self):
        """Test no events tracked when disabled."""
        from src.core.telemetry import TelemetryCollector
        
        telemetry = TelemetryCollector()
        
        telemetry.track("test_event", {"key": "value"})
        
        assert len(telemetry._events) == 0
    
    def test_telemetry_tracking_when_enabled(self, tmp_path):
        """Test events tracked when enabled."""
        from src.core.telemetry import TelemetryCollector, TelemetryConfig
        from unittest.mock import patch
        
        config = TelemetryConfig(
            enabled=True,
            local_storage_path=tmp_path / "test_telemetry.json",
        )
        
        # Mock file operations to avoid permission issues
        with patch.object(TelemetryCollector, '_load_config'), \
             patch.object(TelemetryCollector, '_save_events'):
            telemetry = TelemetryCollector(config)
            telemetry.config.enabled = True  # Ensure enabled after mock
            
            telemetry.track("test_event", {"platform": "github", "count": 10})
            
            assert len(telemetry._events) == 1
            assert telemetry._events[0].event_type == "test_event"
    
    def test_telemetry_sanitizes_properties(self, tmp_path):
        """Test that telemetry sanitizes properties."""
        from src.core.telemetry import TelemetryCollector, TelemetryConfig
        from unittest.mock import patch
        
        config = TelemetryConfig(
            enabled=True,
            local_storage_path=tmp_path / "test_telemetry.json",
        )
        
        # Mock file operations to avoid permission issues
        with patch.object(TelemetryCollector, '_load_config'), \
             patch.object(TelemetryCollector, '_save_events'):
            telemetry = TelemetryCollector(config)
            telemetry.config.enabled = True  # Ensure enabled after mock
            
            # Try to track with potentially sensitive data
            telemetry.track("test", {
                "platform": "github",  # Allowed
                "api_key": "secret123",  # Not allowed
                "password": "hunter2",  # Not allowed
                "count": 5,  # Allowed
            })
            
            props = telemetry._events[0].properties
            
            assert "platform" in props
            assert "count" in props
            assert "api_key" not in props
            assert "password" not in props
    
    def test_anonymous_id_generation(self):
        """Test anonymous ID is generated."""
        from src.core.telemetry import TelemetryCollector
        
        telemetry = TelemetryCollector()
        
        assert telemetry.config.anonymous_id
        assert len(telemetry.config.anonymous_id) == 16


class TestHealthChecks:
    """Test health check system."""
    
    def test_health_status_enum(self):
        """Test health status enum."""
        from src.core.health import HealthStatus
        
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
    
    def test_component_health_creation(self):
        """Test component health creation."""
        from src.core.health import ComponentHealth, HealthStatus
        
        health = ComponentHealth(
            name="test_component",
            status=HealthStatus.HEALTHY,
            message="All good",
            latency_ms=50.0,
        )
        
        assert health.name == "test_component"
        assert health.status == HealthStatus.HEALTHY
        assert health.latency_ms == 50.0
    
    def test_system_health_to_dict(self):
        """Test system health serialization."""
        from src.core.health import SystemHealth, ComponentHealth, HealthStatus
        
        health = SystemHealth(
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            uptime_seconds=100.0,
            components=[
                ComponentHealth(
                    name="test",
                    status=HealthStatus.HEALTHY,
                    message="OK",
                )
            ],
        )
        
        data = health.to_dict()
        
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert len(data["components"]) == 1


class TestVersioning:
    """Test version management."""
    
    def test_get_version(self):
        """Test getting version."""
        from src.core.version import get_version
        
        version = get_version()
        
        assert version
        assert "." in version
    
    def test_version_info_parsing(self):
        """Test version info parsing."""
        from src.core.version import VersionInfo
        
        info = VersionInfo.parse("1.2.3")
        
        assert info.major == 1
        assert info.minor == 2
        assert info.patch == 3
    
    def test_version_info_with_prerelease(self):
        """Test version with prerelease."""
        from src.core.version import VersionInfo
        
        info = VersionInfo.parse("1.0.0-beta.1")
        
        assert info.major == 1
        assert info.prerelease == "beta.1"
    
    def test_version_bumping(self):
        """Test version bumping."""
        from src.core.version import VersionInfo
        
        info = VersionInfo(1, 2, 3)
        
        major = info.bump_major()
        assert str(major) == "2.0.0"
        
        minor = info.bump_minor()
        assert str(minor) == "1.3.0"
        
        patch = info.bump_patch()
        assert str(patch) == "1.2.4"
    
    def test_build_info(self):
        """Test build info."""
        from src.core.version import get_build_info
        
        info = get_build_info()
        
        assert "version" in info
        assert "python_version" in info
        assert "components" in info
