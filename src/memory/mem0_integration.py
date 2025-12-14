"""
VIBE MCP - Mem0 Integration

Advanced memory system using Mem0 for persistent, intelligent context retention.
Implements the "vibe coding" principle of learning from user interactions.

Features:
- Multi-category memory storage
- Semantic search across memories
- Context retrieval for tasks
- Memory decay and relevance scoring
- Fallback to local storage if Mem0 unavailable

Memory Categories:
- PREFERENCE: User preferences (style, tools, frameworks)
- DECISION: Project decisions (architecture, tech stack)
- PATTERN: Code patterns (reusable components, idioms)
- ERROR_SOLUTION: Error fixes that worked
- CONTEXT: General project context

Usage:
    memory = MemorySystem()

    # Remember user preferences
    await memory.remember_preference("User prefers tabs over spaces")

    # Remember error solutions
    await memory.remember_error_solution(
        error="ModuleNotFoundError: cv2",
        solution="pip install opencv-python"
    )

    # Get relevant context for a task
    context = await memory.get_context_for_task("build a FastAPI app")
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import mem0
try:
    from mem0 import Memory
    from mem0.configs.base import MemoryConfig as Mem0Config

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.warning("Mem0 not installed. Using local fallback storage.")

# Import LiteLLM router for advanced features
try:
    from src.llm.litellm_router import LiteLLMRouter, TaskType

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class MemoryCategory(Enum):
    """Categories for organizing memories."""

    PREFERENCE = "preference"  # User preferences
    DECISION = "decision"  # Project decisions
    PATTERN = "pattern"  # Code patterns
    ERROR_SOLUTION = "error_solution"  # Error fixes
    CONTEXT = "context"  # General context
    LEARNING = "learning"  # Things learned during sessions
    COMPONENT = "component"  # Reusable components
    WORKFLOW = "workflow"  # Workflow patterns

    # Map to memory types for advanced features
    @property
    def memory_type(self) -> str:
        """Map category to memory type."""
        mapping = {
            MemoryCategory.PREFERENCE: "semantic",
            MemoryCategory.DECISION: "semantic",
            MemoryCategory.PATTERN: "procedural",
            MemoryCategory.ERROR_SOLUTION: "procedural",
            MemoryCategory.CONTEXT: "episodic",
            MemoryCategory.LEARNING: "reflective",
            MemoryCategory.COMPONENT: "procedural",
            MemoryCategory.WORKFLOW: "procedural",
        }
        return mapping.get(self, "episodic")


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str
    content: str
    category: MemoryCategory
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    relevance_score: float = 1.0
    access_count: int = 0

    # Advanced fields for enhanced functionality
    agent_id: str | None = None
    session_id: str | None = None
    importance_score: float = 0.5
    consolidated: bool = False
    last_consolidated: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "relevance_score": self.relevance_score,
            "access_count": self.access_count,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "importance_score": self.importance_score,
            "consolidated": self.consolidated,
            "last_consolidated": self.last_consolidated.isoformat()
            if self.last_consolidated
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            category=MemoryCategory(data["category"]),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            relevance_score=data.get("relevance_score", 1.0),
            access_count=data.get("access_count", 0),
            agent_id=data.get("agent_id"),
            session_id=data.get("session_id"),
            importance_score=data.get("importance_score", 0.5),
            consolidated=data.get("consolidated", False),
            last_consolidated=datetime.fromisoformat(data["last_consolidated"])
            if data.get("last_consolidated")
            else None,
        )


@dataclass
class MemoryConfig:
    """Configuration for memory system."""

    # Mem0 settings
    user_id: str = "vibe_mcp_user"

    # Local fallback settings
    storage_path: Path = field(
        default_factory=lambda: Path.home() / ".vibe_mcp" / "memory"
    )

    # Memory limits
    max_memories_per_category: int = 1000
    max_search_results: int = 10

    # Decay settings
    enable_decay: bool = True
    decay_rate: float = 0.01  # Per day
    min_relevance: float = 0.1

    # LLM settings for Mem0
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"

    # Advanced settings
    enable_consolidation: bool = True
    consolidation_interval: int = 24  # hours
    consolidation_threshold: int = 100  # memories per category
    enable_analytics: bool = True
    cache_ttl: int = 3600  # seconds


class LocalMemoryStore:
    """Local fallback memory storage using JSON files."""

    def __init__(self, storage_path: Path):
        """Initialize local storage."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._memories: dict[str, MemoryEntry] = {}
        self._load()

    def _get_storage_file(self) -> Path:
        """Get the storage file path."""
        return self.storage_path / "memories.json"

    def _load(self) -> None:
        """Load memories from disk."""
        storage_file = self._get_storage_file()
        if storage_file.exists():
            try:
                data = json.loads(storage_file.read_text(encoding="utf-8"))
                self._memories = {k: MemoryEntry.from_dict(v) for k, v in data.items()}
                logger.info(f"Loaded {len(self._memories)} memories from local storage")
            except Exception as e:
                logger.error(f"Failed to load memories: {e}")
                self._memories = {}

    def _save(self) -> None:
        """Save memories to disk."""
        storage_file = self._get_storage_file()
        try:
            data = {k: v.to_dict() for k, v in self._memories.items()}
            storage_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")

    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for content."""
        hash_input = f"{content}{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def add(
        self,
        content: str,
        category: MemoryCategory,
        tags: list[str] = None,
        metadata: dict = None,
    ) -> MemoryEntry:
        """Add a memory."""
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            category=category,
            tags=tags or [],
            metadata=metadata or {},
        )
        self._memories[entry.id] = entry
        self._save()
        return entry

    def search(
        self,
        query: str,
        category: MemoryCategory | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Search memories (simple keyword matching for local store)."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for entry in self._memories.values():
            # Filter by category if specified
            if category and entry.category != category:
                continue

            # Simple relevance scoring based on word overlap
            content_lower = entry.content.lower()
            content_words = set(content_lower.split())

            # Check for matches
            overlap = query_words & content_words
            if overlap or query_lower in content_lower:
                score = len(overlap) / len(query_words) if query_words else 0
                if query_lower in content_lower:
                    score += 0.5
                results.append((entry, score))

        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results[:limit]]

    def get(self, memory_id: str) -> MemoryEntry | None:
        """Get a specific memory."""
        entry = self._memories.get(memory_id)
        if entry:
            entry.access_count += 1
            entry.updated_at = datetime.now()
            self._save()
        return entry

    def update(self, memory_id: str, content: str) -> MemoryEntry | None:
        """Update a memory."""
        if memory_id in self._memories:
            self._memories[memory_id].content = content
            self._memories[memory_id].updated_at = datetime.now()
            self._save()
            return self._memories[memory_id]
        return None

    def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        if memory_id in self._memories:
            del self._memories[memory_id]
            self._save()
            return True
        return False

    def get_by_category(self, category: MemoryCategory) -> list[MemoryEntry]:
        """Get all memories in a category."""
        return [e for e in self._memories.values() if e.category == category]

    def get_all(self) -> list[MemoryEntry]:
        """Get all memories."""
        return list(self._memories.values())

    def clear(self) -> None:
        """Clear all memories."""
        self._memories.clear()
        self._save()


class MemorySystem:
    """
    Advanced memory system for VIBE MCP.

    Uses Mem0 for intelligent memory management with semantic search,
    falling back to local storage if Mem0 is unavailable.

    Enhanced features:
    - Memory consolidation and summarization
    - Multi-agent memory support
    - Advanced analytics and insights
    - Intelligent caching
    """

    def __init__(self, config: MemoryConfig | None = None):
        """Initialize memory system."""
        self.config = config or MemoryConfig()
        self._mem0: Memory | None = None
        self._local_store: LocalMemoryStore | None = None

        # Advanced features
        self._llm_router: LiteLLMRouter | None = None
        self._cache: dict[str, list[dict]] = {}
        self._cache_expiry: dict[str, datetime] = {}
        self._consolidation_history: list[dict] = []
        self._analytics: dict[str, Any] = {
            "total_additions": 0,
            "total_searches": 0,
            "category_stats": {cat.value: 0 for cat in MemoryCategory},
            "agent_stats": {},
            "consolidations": 0,
        }

        self._initialize()

    def _initialize(self) -> None:
        """Initialize the appropriate storage backend."""
        if MEM0_AVAILABLE:
            try:
                # Configure Mem0 with enhanced settings
                mem0_config = {
                    "llm": {
                        "provider": self.config.llm_provider,
                        "config": {
                            "model": self.config.llm_model,
                            "temperature": 0.1,
                        },
                    },
                    "embedder": {
                        "provider": self.config.llm_provider,
                        "config": {
                            "model": self.config.embedding_model,
                        },
                    },
                    "vector_store": {
                        "provider": "chroma",
                        "config": {
                            "collection_name": "vibe_mcp_memories",
                            "path": self.config.storage_path / "chroma",
                        },
                    },
                    "version": "v1.1",
                }

                self._mem0 = Memory.from_config(mem0_config)
                logger.info("Mem0 initialized successfully")

                # Initialize LiteLLM router for advanced features
                if LITELLM_AVAILABLE:
                    self._llm_router = LiteLLMRouter()

            except Exception as e:
                logger.warning(f"Failed to initialize Mem0: {e}. Using local fallback.")
                self._local_store = LocalMemoryStore(self.config.storage_path)
        else:
            logger.info("Using local memory storage (Mem0 not available)")
            self._local_store = LocalMemoryStore(self.config.storage_path)

    @property
    def is_mem0_active(self) -> bool:
        """Check if Mem0 is the active backend."""
        return self._mem0 is not None

    async def add(
        self,
        content: str,
        category: MemoryCategory = MemoryCategory.CONTEXT,
        tags: list[str] | None = None,
        metadata: dict | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        importance: float = 0.5,
    ) -> str:
        """
        Add a memory.

        Args:
            content: The memory content
            category: Memory category
            tags: Optional tags for filtering
            metadata: Optional metadata
            agent_id: ID of the agent adding the memory
            session_id: ID of the current session
            importance: Importance score (0-1)

        Returns:
            Memory ID
        """
        tags = tags or []
        metadata = metadata or {}
        metadata.update(
            {
                "category": category.value,
                "tags": tags,
                "memory_type": category.memory_type,
                "agent_id": agent_id,
                "session_id": session_id,
                "importance": importance,
            }
        )

        # Update analytics
        self._analytics["total_additions"] += 1
        self._analytics["category_stats"][category.value] += 1

        if agent_id:
            if agent_id not in self._analytics["agent_stats"]:
                self._analytics["agent_stats"][agent_id] = {
                    "additions": 0,
                    "searches": 0,
                }
            self._analytics["agent_stats"][agent_id]["additions"] += 1

        # Invalidate cache
        self._invalidate_cache(category)

        if self._mem0:
            try:
                result = self._mem0.add(
                    content,
                    user_id=self.config.user_id,
                    metadata=metadata,
                )
                memory_id = result.get("id", "")
                logger.debug(f"Added memory to Mem0: {memory_id}")

                # Check if consolidation is needed
                await self._check_consolidation(category)

                return memory_id
            except Exception as e:
                logger.error(f"Mem0 add failed: {e}")
                # Fall through to local store

        if self._local_store:
            entry = self._local_store.add(content, category, tags, metadata)
            # Update entry with advanced fields
            entry.agent_id = agent_id
            entry.session_id = session_id
            entry.importance_score = importance
            self._local_store._save()
            logger.debug(f"Added memory to local store: {entry.id}")
            return entry.id

        raise RuntimeError("No memory backend available")

    async def search(
        self,
        query: str,
        category: MemoryCategory | None = None,
        limit: int | None = None,
        agent_id: str | None = None,
    ) -> list[dict]:
        """
        Search memories.

        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results
            agent_id: Optional agent filter

        Returns:
            List of matching memories
        """
        limit = limit or self.config.max_search_results

        # Update analytics
        self._analytics["total_searches"] += 1
        if agent_id:
            if agent_id not in self._analytics["agent_stats"]:
                self._analytics["agent_stats"][agent_id] = {
                    "additions": 0,
                    "searches": 0,
                }
            self._analytics["agent_stats"][agent_id]["searches"] += 1

        # Check cache first
        cache_key = f"{query}_{category}_{agent_id}_{limit}"
        if cache_key in self._cache:
            if datetime.now() < self._cache_expiry.get(cache_key, datetime.min):
                return self._cache[cache_key]

        if self._mem0:
            try:
                # Build filters
                filters = {}
                if category:
                    filters["category"] = category.value
                if agent_id:
                    filters["agent_id"] = agent_id

                results = self._mem0.search(
                    query,
                    user_id=self.config.user_id,
                    limit=limit,
                    filters=filters if filters else None,
                )

                # Cache results
                self._cache[cache_key] = results
                self._cache_expiry[cache_key] = datetime.now() + timedelta(
                    seconds=self.config.cache_ttl
                )

                return results
            except Exception as e:
                logger.error(f"Mem0 search failed: {e}")

        if self._local_store:
            entries = self._local_store.search(query, category, limit)

            # Filter by agent if specified
            if agent_id:
                entries = [e for e in entries if e.agent_id == agent_id]

            results = [e.to_dict() for e in entries]

            # Cache results
            self._cache[cache_key] = results
            self._cache_expiry[cache_key] = datetime.now() + timedelta(
                seconds=self.config.cache_ttl
            )

            return results

        return []

    async def get(self, memory_id: str) -> dict | None:
        """Get a specific memory by ID."""
        if self._mem0:
            try:
                result = self._mem0.get(memory_id)
                return result
            except Exception as e:
                logger.error(f"Mem0 get failed: {e}")

        if self._local_store:
            entry = self._local_store.get(memory_id)
            return entry.to_dict() if entry else None

        return None

    async def update(self, memory_id: str, content: str) -> bool:
        """Update a memory."""
        if self._mem0:
            try:
                self._mem0.update(memory_id, content)
                return True
            except Exception as e:
                logger.error(f"Mem0 update failed: {e}")

        if self._local_store:
            result = self._local_store.update(memory_id, content)
            return result is not None

        return False

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        if self._mem0:
            try:
                self._mem0.delete(memory_id)
                return True
            except Exception as e:
                logger.error(f"Mem0 delete failed: {e}")

        if self._local_store:
            return self._local_store.delete(memory_id)

        return False

    async def get_all(self, category: MemoryCategory | None = None) -> list[dict]:
        """Get all memories, optionally filtered by category."""
        if self._mem0:
            try:
                results = self._mem0.get_all(user_id=self.config.user_id)
                if category:
                    results = [
                        r
                        for r in results
                        if r.get("metadata", {}).get("category") == category.value
                    ]
                return results
            except Exception as e:
                logger.error(f"Mem0 get_all failed: {e}")

        if self._local_store:
            if category:
                entries = self._local_store.get_by_category(category)
            else:
                entries = self._local_store.get_all()
            return [e.to_dict() for e in entries]

        return []

    # ========================================================================
    # CONVENIENCE METHODS FOR COMMON MEMORY TYPES
    # ========================================================================

    async def remember_preference(
        self,
        preference: str,
        tags: list[str] | None = None,
    ) -> str:
        """Remember a user preference."""
        return await self.add(
            preference,
            category=MemoryCategory.PREFERENCE,
            tags=tags or ["preference"],
        )

    async def remember_decision(
        self,
        decision: str,
        project: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Remember a project decision."""
        metadata = {"project": project} if project else {}
        return await self.add(
            decision,
            category=MemoryCategory.DECISION,
            tags=tags or ["decision"],
            metadata=metadata,
        )

    async def remember_pattern(
        self,
        pattern: str,
        language: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Remember a code pattern."""
        metadata = {"language": language} if language else {}
        return await self.add(
            pattern,
            category=MemoryCategory.PATTERN,
            tags=tags or ["pattern"],
            metadata=metadata,
        )

    async def remember_error_solution(
        self,
        error: str,
        solution: str,
        tags: list[str] | None = None,
    ) -> str:
        """Remember an error and its solution."""
        content = f"Error: {error}\nSolution: {solution}"
        return await self.add(
            content,
            category=MemoryCategory.ERROR_SOLUTION,
            tags=tags or ["error", "solution"],
            metadata={"error": error, "solution": solution},
        )

    async def remember_component(
        self,
        name: str,
        description: str,
        path: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Remember a reusable component."""
        content = f"Component: {name}\nDescription: {description}"
        if path:
            content += f"\nPath: {path}"
        return await self.add(
            content,
            category=MemoryCategory.COMPONENT,
            tags=tags or ["component", name],
            metadata={"name": name, "path": path},
        )

    async def remember_learning(
        self,
        learning: str,
        source: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Remember something learned during a session."""
        metadata = {"source": source} if source else {}
        return await self.add(
            learning,
            category=MemoryCategory.LEARNING,
            tags=tags or ["learning"],
            metadata=metadata,
        )

    # ========================================================================
    # CONTEXT RETRIEVAL
    # ========================================================================

    async def get_context_for_task(
        self,
        task_description: str,
        include_categories: list[MemoryCategory] | None = None,
        limit: int = 10,
    ) -> dict:
        """
        Get relevant context for a task.

        Args:
            task_description: Description of the task
            include_categories: Categories to include (default: all)
            limit: Maximum memories per category

        Returns:
            Dictionary with categorized relevant memories
        """
        categories = include_categories or list(MemoryCategory)

        context = {
            "task": task_description,
            "memories": {},
            "summary": "",
        }

        all_relevant = []

        for category in categories:
            results = await self.search(
                task_description, category=category, limit=limit
            )
            if results:
                context["memories"][category.value] = results
                all_relevant.extend(results)

        # Build summary
        if all_relevant:
            summary_parts = []

            # Preferences
            prefs = context["memories"].get(MemoryCategory.PREFERENCE.value, [])
            if prefs:
                summary_parts.append(f"User preferences: {len(prefs)} relevant")

            # Decisions
            decisions = context["memories"].get(MemoryCategory.DECISION.value, [])
            if decisions:
                summary_parts.append(f"Past decisions: {len(decisions)} relevant")

            # Patterns
            patterns = context["memories"].get(MemoryCategory.PATTERN.value, [])
            if patterns:
                summary_parts.append(f"Code patterns: {len(patterns)} available")

            # Error solutions
            errors = context["memories"].get(MemoryCategory.ERROR_SOLUTION.value, [])
            if errors:
                summary_parts.append(f"Error solutions: {len(errors)} known")

            context["summary"] = "; ".join(summary_parts)
        else:
            context["summary"] = "No relevant memories found"

        return context

    async def get_user_preferences(self) -> list[dict]:
        """Get all user preferences."""
        return await self.get_all(category=MemoryCategory.PREFERENCE)

    async def get_error_solutions(self, error_query: str | None = None) -> list[dict]:
        """Get error solutions, optionally filtered by query."""
        if error_query:
            return await self.search(
                error_query, category=MemoryCategory.ERROR_SOLUTION
            )
        return await self.get_all(category=MemoryCategory.ERROR_SOLUTION)

    # ========================================================================
    # ADVANCED MEMORY MANAGEMENT
    # ========================================================================

    async def consolidate_memories(
        self,
        category: MemoryCategory | None = None,
        agent_id: str | None = None,
    ) -> dict:
        """
        Consolidate old memories to save space and improve relevance.

        Args:
            category: Category to consolidate (None for all)
            agent_id: Agent to consolidate for (None for all)

        Returns:
            Consolidation report
        """
        if not self._llm_router:
            logger.warning("LiteLLM router not available for consolidation")
            return {"success": False, "error": "LLM router not available"}

        categories = [category] if category else list(MemoryCategory)
        report = {
            "success": True,
            "consolidated": {},
            "total_consolidated": 0,
            "timestamp": datetime.now().isoformat(),
        }

        for cat in categories:
            # Get old memories for category
            memories = await self.get_all(category=cat)

            # Filter by agent if specified
            if agent_id:
                memories = [
                    m
                    for m in memories
                    if m.get("metadata", {}).get("agent_id") == agent_id
                ]

            # Filter for consolidation candidates
            cutoff_date = datetime.now() - timedelta(
                days=self.config.consolidation_interval
            )
            candidates = [
                m
                for m in memories
                if datetime.fromisoformat(m["created_at"]) < cutoff_date
                and not m.get("metadata", {}).get("consolidated", False)
                and len(memories) > self.config.consolidation_threshold
            ]

            if len(candidates) < 5:  # Need at least 5 to consolidate
                continue

            # Group memories by similarity (simplified - by tags)
            groups = {}
            for memory in candidates:
                tags = memory.get("tags", [])
                key = tags[0] if tags else "untagged"
                if key not in groups:
                    groups[key] = []
                groups[key].append(memory)

            # Consolidate each group
            for group_key, group_memories in groups.items():
                if len(group_memories) < 3:
                    continue

                # Create summary using LLM
                memories_text = "\n".join(
                    [f"- {m['content']}" for m in group_memories[:10]]
                )

                prompt = f"""
                Summarize these related memories into a concise, comprehensive summary:
                Category: {cat.value}
                Group: {group_key}

                Memories:
                {memories_text}

                Create a summary that captures the key information and insights.
                """

                try:
                    result = await self._llm_router.complete(
                        prompt=prompt, task_type=TaskType.SIMPLE, max_tokens=500
                    )

                    # Add consolidated memory
                    consolidated_id = await self.add(
                        content=result.content,
                        category=cat,
                        tags=["consolidated", group_key],
                        metadata={
                            "consolidated": True,
                            "original_count": len(group_memories),
                            "date_range": (
                                min(m["created_at"] for m in group_memories),
                                max(m["created_at"] for m in group_memories),
                            ),
                            "agent_id": agent_id,
                        },
                        importance=sum(
                            m.get("metadata", {}).get("importance", 0.5)
                            for m in group_memories
                        )
                        / len(group_memories),
                    )

                    # Mark original memories as consolidated
                    for memory in group_memories:
                        memory["metadata"]["consolidated"] = True
                        memory["metadata"]["consolidated_into"] = consolidated_id
                        await self.update(memory["id"], memory["content"])

                    report["consolidated"][cat.value] = {
                        "groups": len(groups),
                        "memories": len(candidates),
                        "consolidated_id": consolidated_id,
                    }
                    report["total_consolidated"] += len(candidates)

                except Exception as e:
                    logger.error(f"Failed to consolidate {cat.value}/{group_key}: {e}")
                    continue

        # Update analytics
        self._analytics["consolidations"] += 1
        self._consolidation_history.append(report)

        # Clear cache
        self._cache.clear()
        self._cache_expiry.clear()

        return report

    async def get_memory_insights(
        self,
        agent_id: str | None = None,
        category: MemoryCategory | None = None,
    ) -> dict:
        """
        Get detailed insights about stored memories.

        Args:
            agent_id: Filter by agent
            category: Filter by category

        Returns:
            Insights dictionary
        """
        insights = {
            "summary": {},
            "patterns": [],
            "recommendations": [],
            "agent_breakdown": {},
        }

        # Get memories
        memories = await self.get_all(category=category)

        if agent_id:
            memories = [
                m for m in memories if m.get("metadata", {}).get("agent_id") == agent_id
            ]

        if not memories:
            return insights

        # Basic stats
        insights["summary"] = {
            "total_memories": len(memories),
            "avg_importance": sum(
                m.get("metadata", {}).get("importance", 0.5) for m in memories
            )
            / len(memories),
            "oldest_memory": min(m["created_at"] for m in memories),
            "newest_memory": max(m["created_at"] for m in memories),
            "consolidated_count": sum(
                1 for m in memories if m.get("metadata", {}).get("consolidated", False)
            ),
        }

        # Category breakdown
        category_counts = {}
        for memory in memories:
            cat = memory.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        insights["summary"]["by_category"] = category_counts

        # Agent breakdown
        agent_counts = {}
        for memory in memories:
            agent = memory.get("metadata", {}).get("agent_id", "unknown")
            if agent not in agent_counts:
                agent_counts[agent] = {"count": 0, "categories": {}}
            agent_counts[agent]["count"] += 1
            cat = memory.get("category", "unknown")
            agent_counts[agent]["categories"][cat] = (
                agent_counts[agent]["categories"].get(cat, 0) + 1
            )
        insights["agent_breakdown"] = agent_counts

        # Identify patterns
        if len(memories) > 10:
            # Most common tags
            all_tags = []
            for memory in memories:
                all_tags.extend(memory.get("tags", []))

            from collections import Counter

            tag_counts = Counter(all_tags)
            insights["patterns"] = [
                {"type": "top_tags", "data": tag_counts.most_common(5)}
            ]

        # Generate recommendations
        recommendations = []

        # Check if consolidation is needed
        for cat, count in category_counts.items():
            if count > self.config.consolidation_threshold:
                recommendations.append(
                    f"Consider consolidating {cat} memories ({count} items)"
                )

        # Check for low importance memories
        low_importance = sum(
            1 for m in memories if m.get("metadata", {}).get("importance", 0.5) < 0.3
        )
        if low_importance > len(memories) * 0.5:
            recommendations.append(
                "Many memories have low importance scores - consider reviewing and updating"
            )

        insights["recommendations"] = recommendations

        return insights

    async def export_memories(
        self,
        format: str = "json",
        category: MemoryCategory | None = None,
        agent_id: str | None = None,
    ) -> str:
        """
        Export memories to a file.

        Args:
            format: Export format (json, csv, markdown)
            category: Filter by category
            agent_id: Filter by agent

        Returns:
            Path to exported file
        """
        memories = await self.get_all(category=category)

        if agent_id:
            memories = [
                m for m in memories if m.get("metadata", {}).get("agent_id") == agent_id
            ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = self.config.storage_path / "exports"
        export_dir.mkdir(exist_ok=True)

        if format == "json":
            file_path = export_dir / f"memories_{timestamp}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(memories, f, indent=2, ensure_ascii=False)

        elif format == "csv":
            import csv

            file_path = export_dir / f"memories_{timestamp}.csv"
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["id", "content", "category", "tags", "created_at", "importance"]
                )
                for m in memories:
                    writer.writerow(
                        [
                            m["id"],
                            m["content"],
                            m.get("category", ""),
                            ",".join(m.get("tags", [])),
                            m["created_at"],
                            m.get("metadata", {}).get("importance", ""),
                        ]
                    )

        elif format == "markdown":
            file_path = export_dir / f"memories_{timestamp}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(
                    f"# Memory Export\n\nGenerated: {datetime.now().isoformat()}\n\n"
                )

                # Group by category
                grouped = {}
                for m in memories:
                    cat = m.get("category", "unknown")
                    if cat not in grouped:
                        grouped[cat] = []
                    grouped[cat].append(m)

                for cat, cat_memories in grouped.items():
                    f.write(f"\n## {cat.title()} ({len(cat_memories)})\n\n")
                    for m in cat_memories:
                        f.write(f"### {m['id']}\n\n")
                        f.write(f"**Created:** {m['created_at']}\n\n")
                        f.write(f"**Tags:** {', '.join(m.get('tags', []))}\n\n")
                        f.write(f"{m['content']}\n\n---\n\n")

        return str(file_path)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _invalidate_cache(self, category: MemoryCategory | None = None):
        """Invalidate cache entries."""
        keys_to_remove = []
        for key in self._cache:
            if category is None or str(category) in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_expiry:
                del self._cache_expiry[key]

    async def _check_consolidation(self, category: MemoryCategory):
        """Check if consolidation is needed for a category."""
        if not self.config.enable_consolidation:
            return

        memories = await self.get_all(category=category)

        if len(memories) > self.config.consolidation_threshold:
            logger.info(f"Consolidation threshold reached for {category.value}")
            # Run consolidation in background
            asyncio.create_task(self.consolidate_memories(category=category))

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_stats(self) -> dict:
        """Get memory system statistics."""
        all_memories = await self.get_all()

        category_counts = {}
        for category in MemoryCategory:
            category_memories = [
                m
                for m in all_memories
                if m.get("category") == category.value
                or m.get("metadata", {}).get("category") == category.value
            ]
            category_counts[category.value] = len(category_memories)

        return {
            "total_memories": len(all_memories),
            "by_category": category_counts,
            "backend": "mem0" if self.is_mem0_active else "local",
            "analytics": self._analytics,
            "cache_size": len(self._cache),
            "consolidation_history": self._consolidation_history[
                -5:
            ],  # Last 5 consolidations
        }


# Global instance
_memory_system: MemorySystem | None = None


def get_memory_system() -> MemorySystem:
    """Get or create global memory system instance."""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
    return _memory_system


# Factory function for enhanced initialization
async def create_memory_system(
    config: MemoryConfig | None = None,
    llm_router: LiteLLMRouter | None = None,
) -> MemorySystem:
    """
    Create and initialize memory system with enhanced features.

    Args:
        config: Memory configuration
        llm_router: LiteLLM router for advanced features

    Returns:
        Initialized memory system
    """
    system = MemorySystem(config)

    # Override LLM router if provided
    if llm_router:
        system._llm_router = llm_router

    # Test basic functionality
    test_id = await system.add(
        content="Memory system initialized",
        category=MemoryCategory.CONTEXT,
        tags=["system", "test"],
        importance=0.1,
    )

    # Verify it was added
    test_memory = await system.get(test_id)
    if test_memory:
        logger.info("Memory system created and tested successfully")
        await system.delete(test_id)  # Clean up test memory
        return system
    else:
        logger.error("Memory system failed basic test")
        raise RuntimeError("Memory system initialization failed")
