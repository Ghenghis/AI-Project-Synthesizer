"""
VIBE MCP - Memory Module

Persistent memory system using Mem0 for intelligent context retention.
Enables agents to remember user preferences, project decisions, code patterns,
and error solutions across sessions.

Components:
- mem0_integration: Core Mem0 wrapper with enhanced features
- memory_types: Memory categories and schemas

Usage:
    from src.memory import MemorySystem, MemoryCategory

    memory = MemorySystem()

    # Add memories
    await memory.add("User prefers FastAPI over Flask", category=MemoryCategory.PREFERENCE)

    # Search memories
    results = await memory.search("what framework does user prefer")

    # Get context for a task
    context = await memory.get_context_for_task("build an API")
"""

from src.memory.mem0_integration import (
    MemoryCategory,
    MemoryConfig,
    MemoryEntry,
    MemorySystem,
    get_memory_system,
)

__all__ = [
    "MemorySystem",
    "MemoryEntry",
    "MemoryCategory",
    "MemoryConfig",
    "get_memory_system",
]
