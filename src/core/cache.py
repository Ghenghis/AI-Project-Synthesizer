"""
AI Project Synthesizer - Caching Layer

Multi-backend caching for faster repeated operations:
- SQLite (default, no dependencies)
- Redis (optional, for distributed caching)
- Memory (fast, non-persistent)

Caches:
- Search results
- API responses
- Downloaded resource metadata
"""

import asyncio
import json
import hashlib
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, TypeVar, Generic
from datetime import datetime, timedelta

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A cached item with metadata."""
    key: str
    value: T
    created_at: float
    expires_at: Optional[float] = None
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> int:
        """Clear all cache entries. Returns count deleted."""
        pass
    
    @abstractmethod
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache (fast, non-persistent)."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None
        
        entry.hits += 1
        self._hits += 1
        return entry.value
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        # Evict if at capacity
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
        )
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def clear(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count
    
    async def stats(self) -> Dict[str, Any]:
        return {
            "backend": "memory",
            "entries": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
        }
    
    def _evict_oldest(self):
        """Evict oldest entry."""
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]


class SQLiteCache(CacheBackend):
    """SQLite-based persistent cache."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or Path(".cache/synthesizer_cache.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at REAL,
                    expires_at REAL,
                    hits INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)")
            conn.commit()
    
    async def get(self, key: str) -> Optional[Any]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            value, expires_at = row
            
            # Check expiration
            if expires_at and time.time() > expires_at:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None
            
            # Update hits
            conn.execute("UPDATE cache SET hits = hits + 1 WHERE key = ?", (key,))
            conn.commit()
            
            return json.loads(value)
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, value, created_at, expires_at, hits)
                VALUES (?, ?, ?, ?, 0)
            """, (key, json.dumps(value), time.time(), expires_at))
            conn.commit()
        
        return True
    
    async def delete(self, key: str) -> bool:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    async def clear(self) -> int:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("DELETE FROM cache")
            conn.commit()
            return cursor.rowcount
    
    async def stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(hits) FROM cache")
            count, total_hits = cursor.fetchone()
            
            return {
                "backend": "sqlite",
                "db_path": str(self._db_path),
                "entries": count or 0,
                "total_hits": total_hits or 0,
            }
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),)
            )
            conn.commit()
            return cursor.rowcount


class RedisCache(CacheBackend):
    """Redis-based distributed cache (optional)."""
    
    def __init__(self, url: str = "redis://localhost:6379", prefix: str = "synth:"):
        self._url = url
        self._prefix = prefix
        self._client = None
    
    async def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(self._url)
            except ImportError:
                raise RuntimeError("Redis not installed. Run: pip install redis")
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            value = await client.get(self._prefix + key)
            if value:
                return json.loads(value)
        except Exception as e:
            secure_logger.warning(f"Redis get error: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        try:
            client = await self._get_client()
            await client.set(
                self._prefix + key,
                json.dumps(value),
                ex=ttl_seconds,
            )
            return True
        except Exception as e:
            secure_logger.warning(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            result = await client.delete(self._prefix + key)
            return result > 0
        except Exception as e:
            secure_logger.warning(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> int:
        try:
            client = await self._get_client()
            keys = await client.keys(self._prefix + "*")
            if keys:
                return await client.delete(*keys)
        except Exception as e:
            secure_logger.warning(f"Redis clear error: {e}")
        return 0
    
    async def stats(self) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            info = await client.info()
            keys = await client.keys(self._prefix + "*")
            return {
                "backend": "redis",
                "url": self._url,
                "entries": len(keys),
                "memory_used": info.get("used_memory_human", "unknown"),
            }
        except Exception as e:
            return {"backend": "redis", "error": str(e)}


class CacheManager:
    """
    Unified cache manager with multiple backends.
    
    Usage:
        cache = CacheManager()
        
        # Cache search results
        await cache.set("search:ml", results, ttl=3600)
        
        # Get cached results
        results = await cache.get("search:ml")
    """
    
    def __init__(self, backend: str = "sqlite"):
        """
        Initialize cache manager.
        
        Args:
            backend: "memory", "sqlite", or "redis"
        """
        if backend == "memory":
            self._backend = MemoryCache()
        elif backend == "redis":
            self._backend = RedisCache()
        else:
            self._backend = SQLiteCache()
        
        self._backend_name = backend
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        return await self._backend.get(key)
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set cached value with TTL."""
        return await self._backend.set(key, value, ttl_seconds)
    
    async def delete(self, key: str) -> bool:
        """Delete cached value."""
        return await self._backend.delete(key)
    
    async def clear(self) -> int:
        """Clear all cache."""
        return await self._backend.clear()
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return await self._backend.stats()
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Global cache instance
_cache: Optional[CacheManager] = None


def get_cache(backend: str = "sqlite") -> CacheManager:
    """Get or create cache manager."""
    global _cache
    if _cache is None:
        _cache = CacheManager(backend)
    return _cache


def cached(ttl_seconds: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Usage:
        @cached(ttl_seconds=3600, key_prefix="search")
        async def search_repos(query: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            key = key_prefix + ":" + cache.cache_key(*args, **kwargs)
            
            # Try to get from cache
            result = await cache.get(key)
            if result is not None:
                secure_logger.debug(f"Cache hit: {key}")
                return result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl_seconds)
            secure_logger.debug(f"Cache set: {key}")
            
            return result
        
        return wrapper
    return decorator
