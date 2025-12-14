"""
Unit tests for core.memory module.
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["APP_ENV"] = "testing"

from src.core.memory import Bookmark, MemoryEntry, MemoryStore, MemoryType, SearchEntry


class TestMemoryType:
    """Test MemoryType enum."""

    def test_memory_type_values(self):
        """Test all memory types are defined."""
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.SEARCH.value == "search"
        assert MemoryType.BOOKMARK.value == "bookmark"
        assert MemoryType.PREFERENCE.value == "preference"
        assert MemoryType.AGENT.value == "agent"
        assert MemoryType.WORKFLOW.value == "workflow"
        assert MemoryType.PROJECT.value == "project"
        assert MemoryType.NOTE.value == "note"


class TestMemoryEntry:
    """Test MemoryEntry dataclass."""

    def test_memory_entry_creation(self):
        """Test creating a memory entry."""
        entry = MemoryEntry(
            id="mem_001",
            type=MemoryType.CONVERSATION,
            content={"message": "Test memory content"}
        )

        assert entry.id == "mem_001"
        assert entry.content == {"message": "Test memory content"}
        assert entry.type == MemoryType.CONVERSATION

    def test_memory_entry_to_dict(self):
        """Test converting memory entry to dict."""
        entry = MemoryEntry(
            id="mem_002",
            type=MemoryType.SEARCH,
            content={"query": "test search"},
            tags=["test", "search"]
        )

        result = entry.to_dict()

        assert result["id"] == "mem_002"
        assert result["type"] == "search"
        assert "test" in result["tags"]


class TestSearchEntry:
    """Test SearchEntry dataclass."""

    def test_search_entry_creation(self):
        """Test creating a search entry."""
        entry = SearchEntry(
            id="search_001",
            query="machine learning",
            platforms=["github", "huggingface"],
            results_count=25
        )

        assert entry.id == "search_001"
        assert entry.query == "machine learning"
        assert "github" in entry.platforms

    def test_search_entry_to_dict(self):
        """Test converting search entry to dict."""
        entry = SearchEntry(
            id="search_002",
            query="test",
            platforms=["github"],
            results_count=10
        )

        result = entry.to_dict()
        assert result["id"] == "search_002"
        assert result["query"] == "test"


class TestBookmark:
    """Test Bookmark dataclass."""

    def test_bookmark_creation(self):
        """Test creating a bookmark."""
        bookmark = Bookmark(
            id="bm_001",
            name="Test Repo",
            url="https://github.com/test/repo",
            type="repo",
            description="A test repository"
        )

        assert bookmark.id == "bm_001"
        assert bookmark.name == "Test Repo"
        assert bookmark.type == "repo"


class TestMemoryStore:
    """Test MemoryStore class."""

    def test_store_initialization(self):
        """Test memory store initializes correctly."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(db_path=Path(tmpdir) / "test_memory.db")
            assert store is not None

    def test_get_memory(self):
        """Test getting memory from store."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(db_path=Path(tmpdir) / "test_memory.db")

            # get_memory returns None for non-existent entries
            result = store.get_memory("nonexistent")
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
