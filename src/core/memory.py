"""
AI Project Synthesizer - Memory System

Persistent memory for:
- Conversation history
- Search history
- Bookmarks
- User preferences
- Agent memories
- Workflow state
"""

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class MemoryType(str, Enum):
    """Types of memory entries."""

    CONVERSATION = "conversation"
    SEARCH = "search"
    BOOKMARK = "bookmark"
    PREFERENCE = "preference"
    AGENT = "agent"
    WORKFLOW = "workflow"
    PROJECT = "project"
    NOTE = "note"


@dataclass
class MemoryEntry:
    """Single memory entry."""

    id: str
    type: MemoryType
    content: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class SearchEntry:
    """Search history entry."""

    id: str
    query: str
    platforms: list[str]
    results_count: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    filters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Bookmark:
    """Bookmark entry."""

    id: str
    name: str
    url: str
    type: str  # repo, model, dataset, paper, project
    description: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MemoryStore:
    """
    SQLite-based persistent memory store.

    Features:
    - Conversation history
    - Search history with replay
    - Bookmarks with tags
    - Agent memory persistence
    - Workflow state tracking
    """

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path or Path("data/memory.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        # Memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Search history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                platforms TEXT NOT NULL,
                results_count INTEGER,
                timestamp TEXT NOT NULL,
                filters TEXT
            )
        """)

        # Bookmarks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Workflow state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_states (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                state TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_searches_query ON searches(query)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_type ON bookmarks(type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)"
        )

        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    # ============================================
    # Memory Operations
    # ============================================

    def save_memory(self, entry: MemoryEntry) -> str:
        """Save a memory entry."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO memories
            (id, type, content, tags, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entry.id,
                entry.type.value,
                json.dumps(entry.content),
                json.dumps(entry.tags),
                entry.created_at,
                datetime.now().isoformat(),
                json.dumps(entry.metadata),
            ),
        )

        conn.commit()
        conn.close()
        return entry.id

    def get_memory(self, memory_id: str) -> MemoryEntry | None:
        """Get a memory entry by ID."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return MemoryEntry(
                id=row[0],
                type=MemoryType(row[1]),
                content=json.loads(row[2]),
                tags=json.loads(row[3]) if row[3] else [],
                created_at=row[4],
                updated_at=row[5],
                metadata=json.loads(row[6]) if row[6] else {},
            )
        return None

    def search_memories(
        self,
        type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """Search memories by type and tags."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM memories WHERE 1=1"
        params = []

        if type:
            query += " AND type = ?"
            params.append(type.value)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        entries = []
        for row in rows:
            entry = MemoryEntry(
                id=row[0],
                type=MemoryType(row[1]),
                content=json.loads(row[2]),
                tags=json.loads(row[3]) if row[3] else [],
                created_at=row[4],
                updated_at=row[5],
                metadata=json.loads(row[6]) if row[6] else {},
            )

            # Filter by tags if specified
            if tags:
                if any(t in entry.tags for t in tags):
                    entries.append(entry)
            else:
                entries.append(entry)

        return entries

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ============================================
    # Search History
    # ============================================

    def save_search(self, entry: SearchEntry) -> str:
        """Save a search to history."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO searches
            (id, query, platforms, results_count, timestamp, filters)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                entry.id,
                entry.query,
                json.dumps(entry.platforms),
                entry.results_count,
                entry.timestamp,
                json.dumps(entry.filters),
            ),
        )

        conn.commit()
        conn.close()
        return entry.id

    def get_search_history(self, limit: int = 50) -> list[SearchEntry]:
        """Get recent search history."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM searches ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            SearchEntry(
                id=row[0],
                query=row[1],
                platforms=json.loads(row[2]),
                results_count=row[3],
                timestamp=row[4],
                filters=json.loads(row[5]) if row[5] else {},
            )
            for row in rows
        ]

    def replay_search(self, search_id: str) -> SearchEntry | None:
        """Get a search for replay."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM searches WHERE id = ?", (search_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return SearchEntry(
                id=row[0],
                query=row[1],
                platforms=json.loads(row[2]),
                results_count=row[3],
                timestamp=row[4],
                filters=json.loads(row[5]) if row[5] else {},
            )
        return None

    # ============================================
    # Bookmarks
    # ============================================

    def save_bookmark(self, bookmark: Bookmark) -> str:
        """Save a bookmark."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO bookmarks
            (id, name, url, type, description, tags, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                bookmark.id,
                bookmark.name,
                bookmark.url,
                bookmark.type,
                bookmark.description,
                json.dumps(bookmark.tags),
                bookmark.created_at,
                json.dumps(bookmark.metadata),
            ),
        )

        conn.commit()
        conn.close()
        return bookmark.id

    def get_bookmarks(
        self,
        type: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> list[Bookmark]:
        """Get bookmarks with optional filtering."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM bookmarks WHERE 1=1"
        params = []

        if type:
            query += " AND type = ?"
            params.append(type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        bookmarks = []
        for row in rows:
            bookmark = Bookmark(
                id=row[0],
                name=row[1],
                url=row[2],
                type=row[3],
                description=row[4] or "",
                tags=json.loads(row[5]) if row[5] else [],
                created_at=row[6],
                metadata=json.loads(row[7]) if row[7] else {},
            )

            if tags:
                if any(t in bookmark.tags for t in tags):
                    bookmarks.append(bookmark)
            else:
                bookmarks.append(bookmark)

        return bookmarks

    def delete_bookmark(self, bookmark_id: str) -> bool:
        """Delete a bookmark."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ============================================
    # Conversations
    # ============================================

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> str:
        """Save a conversation message."""
        conn = self._get_conn()
        cursor = conn.cursor()

        msg_id = f"msg_{datetime.now().timestamp()}"

        cursor.execute(
            """
            INSERT INTO conversations
            (id, session_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                msg_id,
                session_id,
                role,
                content,
                datetime.now().isoformat(),
                json.dumps(metadata or {}),
            ),
        )

        conn.commit()
        conn.close()
        return msg_id

    def get_conversation(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get conversation history for a session."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, content, timestamp, metadata
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """,
            (session_id, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "role": row[0],
                "content": row[1],
                "timestamp": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
            }
            for row in rows
        ]

    # ============================================
    # Workflow State
    # ============================================

    def save_workflow_state(self, workflow_id: str, state: dict[str, Any]) -> str:
        """Save workflow state."""
        conn = self._get_conn()
        cursor = conn.cursor()

        state_id = f"state_{workflow_id}"

        cursor.execute(
            """
            INSERT OR REPLACE INTO workflow_states
            (id, workflow_id, state, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                state_id,
                workflow_id,
                json.dumps(state),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()
        return state_id

    def get_workflow_state(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow state."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT state FROM workflow_states WHERE workflow_id = ?", (workflow_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None


# Global memory store
_memory_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    """Get or create memory store."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
