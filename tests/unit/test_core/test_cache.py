"""
Unit tests for core cache module.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.cache import (
    CacheBackend,
    CacheEntry,
    MemoryCache,
)


class TestCacheEntry:
    """Test cache entry dataclass."""

    def test_create_entry(self):
        """Should create cache entry."""
        entry = CacheEntry(key="test", value="data", created_at=time.time())
        assert entry.key == "test"
        assert entry.value == "data"

    def test_entry_with_expiration(self):
        """Should track expiration time."""
        now = time.time()
        entry = CacheEntry(
            key="test",
            value="data",
            created_at=now,
            expires_at=now + 3600
        )
        assert entry.expires_at == now + 3600

    def test_is_expired_no_expiration(self):
        """Should not be expired if no expiration set."""
        entry = CacheEntry(key="test", value="data", created_at=time.time())
        assert entry.is_expired is False

    def test_is_expired_future(self):
        """Should not be expired if expiration in future."""
        entry = CacheEntry(
            key="test",
            value="data",
            created_at=time.time(),
            expires_at=time.time() + 3600
        )
        assert entry.is_expired is False

    def test_is_expired_past(self):
        """Should be expired if expiration in past."""
        entry = CacheEntry(
            key="test",
            value="data",
            created_at=time.time() - 7200,
            expires_at=time.time() - 3600
        )
        assert entry.is_expired is True

    def test_default_hits(self):
        """Should have zero hits by default."""
        entry = CacheEntry(key="test", value="data", created_at=time.time())
        assert entry.hits == 0


class TestMemoryCache:
    """Test in-memory cache backend."""

    def test_create_memory_cache(self):
        """Should create memory cache instance."""
        cache = MemoryCache()
        assert cache is not None

    def test_create_with_max_size(self):
        """Should create with custom max size."""
        cache = MemoryCache(max_size=500)
        assert cache._max_size == 500

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Should store and retrieve values."""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Should return None for nonexistent key."""
        cache = MemoryCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Should delete cached value."""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Should clear all cached values."""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        count = await cache.clear()
        assert count >= 0
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_stats(self):
        """Should return cache statistics."""
        cache = MemoryCache()
        stats = await cache.stats()
        assert isinstance(stats, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
