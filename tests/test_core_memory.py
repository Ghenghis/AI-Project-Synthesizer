"""
Tests for src/core/memory.py - Memory System

Full coverage tests for:
- MemoryStore
- MemoryEntry
- SearchEntry
- Bookmark
- Conversations
- Workflow state
"""

import tempfile
from pathlib import Path

import pytest

from src.core.memory import (
    Bookmark,
    MemoryEntry,
    MemoryStore,
    MemoryType,
    SearchEntry,
    get_memory_store,
)


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_create_memory_entry(self):
        entry = MemoryEntry(
            id="test_1",
            type=MemoryType.CONVERSATION,
            content={"message": "hello"},
        )
        assert entry.id == "test_1"
        assert entry.type == MemoryType.CONVERSATION
        assert entry.content == {"message": "hello"}
        assert entry.tags == []

    def test_memory_entry_with_tags(self):
        entry = MemoryEntry(
            id="test_2",
            type=MemoryType.SEARCH,
            content={"query": "test"},
            tags=["tag1", "tag2"],
        )
        assert entry.tags == ["tag1", "tag2"]

    def test_memory_entry_to_dict(self):
        entry = MemoryEntry(
            id="test_3",
            type=MemoryType.BOOKMARK,
            content={"url": "https://example.com"},
            tags=["test"],
            metadata={"source": "manual"},
        )
        d = entry.to_dict()
        assert d["id"] == "test_3"
        assert d["type"] == "bookmark"
        assert d["content"]["url"] == "https://example.com"
        assert d["tags"] == ["test"]
        assert d["metadata"]["source"] == "manual"

    def test_all_memory_types(self):
        types = [
            MemoryType.CONVERSATION,
            MemoryType.SEARCH,
            MemoryType.BOOKMARK,
            MemoryType.PREFERENCE,
            MemoryType.AGENT,
            MemoryType.WORKFLOW,
            MemoryType.PROJECT,
            MemoryType.NOTE,
        ]
        for t in types:
            entry = MemoryEntry(id=f"test_{t.value}", type=t, content={})
            assert entry.type == t


class TestSearchEntry:
    """Tests for SearchEntry dataclass."""

    def test_create_search_entry(self):
        entry = SearchEntry(
            id="search_1",
            query="machine learning",
            platforms=["github", "huggingface"],
            results_count=25,
        )
        assert entry.id == "search_1"
        assert entry.query == "machine learning"
        assert entry.platforms == ["github", "huggingface"]
        assert entry.results_count == 25

    def test_search_entry_with_filters(self):
        entry = SearchEntry(
            id="search_2",
            query="python",
            platforms=["github"],
            results_count=10,
            filters={"language": "python", "min_stars": 100},
        )
        assert entry.filters["language"] == "python"
        assert entry.filters["min_stars"] == 100

    def test_search_entry_to_dict(self):
        entry = SearchEntry(
            id="search_3",
            query="test",
            platforms=["github"],
            results_count=5,
        )
        d = entry.to_dict()
        assert d["id"] == "search_3"
        assert d["query"] == "test"
        assert "timestamp" in d


class TestBookmark:
    """Tests for Bookmark dataclass."""

    def test_create_bookmark(self):
        bookmark = Bookmark(
            id="bm_1",
            name="Test Repo",
            url="https://github.com/test/repo",
            type="repo",
        )
        assert bookmark.id == "bm_1"
        assert bookmark.name == "Test Repo"
        assert bookmark.type == "repo"

    def test_bookmark_with_tags(self):
        bookmark = Bookmark(
            id="bm_2",
            name="ML Model",
            url="https://huggingface.co/model",
            type="model",
            tags=["ml", "nlp"],
            description="A test model",
        )
        assert bookmark.tags == ["ml", "nlp"]
        assert bookmark.description == "A test model"

    def test_bookmark_to_dict(self):
        bookmark = Bookmark(
            id="bm_3",
            name="Dataset",
            url="https://kaggle.com/dataset",
            type="dataset",
            metadata={"size": "1GB"},
        )
        d = bookmark.to_dict()
        assert d["id"] == "bm_3"
        assert d["type"] == "dataset"
        assert d["metadata"]["size"] == "1GB"


class TestMemoryStore:
    """Tests for MemoryStore class."""

    @pytest.fixture
    def temp_store(self):
        """Create a temporary memory store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_memory.db"
            store = MemoryStore(db_path=db_path)
            yield store

    def test_init_creates_db(self, temp_store):
        assert temp_store._db_path.exists()

    def test_save_and_get_memory(self, temp_store):
        entry = MemoryEntry(
            id="mem_1",
            type=MemoryType.NOTE,
            content={"text": "test note"},
        )
        temp_store.save_memory(entry)

        retrieved = temp_store.get_memory("mem_1")
        assert retrieved is not None
        assert retrieved.id == "mem_1"
        assert retrieved.content["text"] == "test note"

    def test_get_nonexistent_memory(self, temp_store):
        result = temp_store.get_memory("nonexistent")
        assert result is None

    def test_search_memories_by_type(self, temp_store):
        # Save multiple memories
        for i in range(5):
            temp_store.save_memory(
                MemoryEntry(
                    id=f"conv_{i}",
                    type=MemoryType.CONVERSATION,
                    content={"msg": f"message {i}"},
                )
            )
        for i in range(3):
            temp_store.save_memory(
                MemoryEntry(
                    id=f"note_{i}",
                    type=MemoryType.NOTE,
                    content={"text": f"note {i}"},
                )
            )

        convs = temp_store.search_memories(type=MemoryType.CONVERSATION)
        assert len(convs) == 5

        notes = temp_store.search_memories(type=MemoryType.NOTE)
        assert len(notes) == 3

    def test_search_memories_by_tags(self, temp_store):
        temp_store.save_memory(
            MemoryEntry(
                id="tagged_1",
                type=MemoryType.NOTE,
                content={},
                tags=["important", "work"],
            )
        )
        temp_store.save_memory(
            MemoryEntry(
                id="tagged_2",
                type=MemoryType.NOTE,
                content={},
                tags=["personal"],
            )
        )

        results = temp_store.search_memories(tags=["important"])
        assert len(results) == 1
        assert results[0].id == "tagged_1"

    def test_search_memories_limit(self, temp_store):
        for i in range(20):
            temp_store.save_memory(
                MemoryEntry(
                    id=f"mem_{i}",
                    type=MemoryType.NOTE,
                    content={},
                )
            )

        results = temp_store.search_memories(limit=5)
        assert len(results) == 5

    def test_delete_memory(self, temp_store):
        temp_store.save_memory(
            MemoryEntry(
                id="to_delete",
                type=MemoryType.NOTE,
                content={},
            )
        )

        assert temp_store.get_memory("to_delete") is not None

        deleted = temp_store.delete_memory("to_delete")
        assert deleted is True

        assert temp_store.get_memory("to_delete") is None

    def test_delete_nonexistent_memory(self, temp_store):
        deleted = temp_store.delete_memory("nonexistent")
        assert deleted is False

    def test_save_and_get_search_history(self, temp_store):
        entry = SearchEntry(
            id="search_1",
            query="test query",
            platforms=["github"],
            results_count=10,
        )
        temp_store.save_search(entry)

        history = temp_store.get_search_history()
        assert len(history) == 1
        assert history[0].query == "test query"

    def test_replay_search(self, temp_store):
        entry = SearchEntry(
            id="search_replay",
            query="replay test",
            platforms=["github", "huggingface"],
            results_count=15,
            filters={"language": "python"},
        )
        temp_store.save_search(entry)

        replayed = temp_store.replay_search("search_replay")
        assert replayed is not None
        assert replayed.query == "replay test"
        assert replayed.filters["language"] == "python"

    def test_replay_nonexistent_search(self, temp_store):
        result = temp_store.replay_search("nonexistent")
        assert result is None

    def test_save_and_get_bookmarks(self, temp_store):
        bookmark = Bookmark(
            id="bm_test",
            name="Test Bookmark",
            url="https://example.com",
            type="repo",
        )
        temp_store.save_bookmark(bookmark)

        bookmarks = temp_store.get_bookmarks()
        assert len(bookmarks) == 1
        assert bookmarks[0].name == "Test Bookmark"

    def test_get_bookmarks_by_type(self, temp_store):
        temp_store.save_bookmark(
            Bookmark(
                id="bm_repo",
                name="Repo",
                url="https://github.com/test",
                type="repo",
            )
        )
        temp_store.save_bookmark(
            Bookmark(
                id="bm_model",
                name="Model",
                url="https://huggingface.co/model",
                type="model",
            )
        )

        repos = temp_store.get_bookmarks(type="repo")
        assert len(repos) == 1
        assert repos[0].type == "repo"

    def test_delete_bookmark(self, temp_store):
        temp_store.save_bookmark(
            Bookmark(
                id="bm_delete",
                name="To Delete",
                url="https://example.com",
                type="repo",
            )
        )

        deleted = temp_store.delete_bookmark("bm_delete")
        assert deleted is True

        bookmarks = temp_store.get_bookmarks()
        assert len(bookmarks) == 0

    def test_save_and_get_conversation(self, temp_store):
        session_id = "session_1"

        temp_store.save_message(session_id, "user", "Hello")
        temp_store.save_message(session_id, "assistant", "Hi there!")
        temp_store.save_message(session_id, "user", "How are you?")

        messages = temp_store.get_conversation(session_id)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"

    def test_conversation_with_metadata(self, temp_store):
        temp_store.save_message(
            "session_meta",
            "user",
            "Test message",
            metadata={"source": "voice"},
        )

        messages = temp_store.get_conversation("session_meta")
        assert messages[0]["metadata"]["source"] == "voice"

    def test_save_and_get_workflow_state(self, temp_store):
        workflow_id = "workflow_1"
        state = {
            "step": 3,
            "status": "running",
            "data": {"key": "value"},
        }

        temp_store.save_workflow_state(workflow_id, state)

        retrieved = temp_store.get_workflow_state(workflow_id)
        assert retrieved is not None
        assert retrieved["step"] == 3
        assert retrieved["status"] == "running"

    def test_get_nonexistent_workflow_state(self, temp_store):
        result = temp_store.get_workflow_state("nonexistent")
        assert result is None

    def test_update_workflow_state(self, temp_store):
        workflow_id = "workflow_update"

        temp_store.save_workflow_state(workflow_id, {"step": 1})
        temp_store.save_workflow_state(workflow_id, {"step": 2})

        state = temp_store.get_workflow_state(workflow_id)
        assert state["step"] == 2


class TestGetMemoryStore:
    """Tests for get_memory_store function."""

    def test_get_memory_store_singleton(self):
        store1 = get_memory_store()
        store2 = get_memory_store()
        assert store1 is store2

    def test_memory_store_is_functional(self):
        store = get_memory_store()
        assert store is not None
        assert hasattr(store, "save_memory")
        assert hasattr(store, "get_memory")
