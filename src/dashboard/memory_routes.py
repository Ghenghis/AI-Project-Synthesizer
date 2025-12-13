"""
AI Project Synthesizer - Memory & Bookmarks API Routes

API endpoints for:
- Memory management
- Search history
- Bookmarks
- Conversation history
- Real-time events (SSE)
"""

import contextlib
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core.memory import (
    Bookmark,
    MemoryEntry,
    MemoryType,
    SearchEntry,
    get_memory_store,
)
from src.core.realtime import (
    EventType,
    emit_notification,
    get_event_bus,
)
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)

router = APIRouter(prefix="/api", tags=["memory"])


# Request models
class MemoryRequest(BaseModel):
    type: str
    content: dict[str, Any]
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class BookmarkRequest(BaseModel):
    name: str
    url: str
    type: str  # repo, model, dataset, paper, project
    description: str = ""
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class SearchHistoryRequest(BaseModel):
    query: str
    platforms: list[str]
    results_count: int
    filters: dict[str, Any] = {}


class MessageRequest(BaseModel):
    session_id: str
    role: str
    content: str
    metadata: dict[str, Any] = {}


# ============================================
# Memory Endpoints
# ============================================

@router.post("/memory")
async def save_memory(request: MemoryRequest) -> dict[str, Any]:
    """Save a memory entry."""
    store = get_memory_store()

    try:
        memory_type = MemoryType(request.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid memory type: {request.type}")

    entry = MemoryEntry(
        id=f"mem_{datetime.now().timestamp()}",
        type=memory_type,
        content=request.content,
        tags=request.tags,
        metadata=request.metadata,
    )

    memory_id = store.save_memory(entry)

    return {"success": True, "id": memory_id}


@router.get("/memory")
async def get_memories(
    type: str | None = None,
    tags: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Get memories with optional filtering."""
    store = get_memory_store()

    memory_type = None
    if type:
        try:
            memory_type = MemoryType(type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid memory type: {type}")

    tag_list = tags.split(",") if tags else None

    entries = store.search_memories(type=memory_type, tags=tag_list, limit=limit)

    return {
        "memories": [e.to_dict() for e in entries],
        "count": len(entries),
    }


@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str) -> dict[str, Any]:
    """Get a specific memory entry."""
    store = get_memory_store()
    entry = store.get_memory(memory_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Memory not found")

    return entry.to_dict()


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str) -> dict[str, Any]:
    """Delete a memory entry."""
    store = get_memory_store()
    deleted = store.delete_memory(memory_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {"success": True, "deleted": memory_id}


# ============================================
# Search History Endpoints
# ============================================

@router.post("/search-history")
async def save_search(request: SearchHistoryRequest) -> dict[str, Any]:
    """Save a search to history."""
    store = get_memory_store()

    entry = SearchEntry(
        id=f"search_{datetime.now().timestamp()}",
        query=request.query,
        platforms=request.platforms,
        results_count=request.results_count,
        filters=request.filters,
    )

    search_id = store.save_search(entry)

    # Emit event
    emit_notification("Search Saved", f"Saved search: {request.query}", "info")

    return {"success": True, "id": search_id}


@router.get("/search-history")
async def get_search_history(limit: int = 50) -> dict[str, Any]:
    """Get search history."""
    store = get_memory_store()
    entries = store.get_search_history(limit=limit)

    return {
        "searches": [e.to_dict() for e in entries],
        "count": len(entries),
    }


@router.get("/search-history/{search_id}/replay")
async def replay_search(search_id: str) -> dict[str, Any]:
    """Get search details for replay."""
    store = get_memory_store()
    entry = store.replay_search(search_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Search not found")

    return entry.to_dict()


# ============================================
# Bookmark Endpoints
# ============================================

@router.post("/bookmarks")
async def save_bookmark(request: BookmarkRequest) -> dict[str, Any]:
    """Save a bookmark."""
    store = get_memory_store()

    bookmark = Bookmark(
        id=f"bm_{datetime.now().timestamp()}",
        name=request.name,
        url=request.url,
        type=request.type,
        description=request.description,
        tags=request.tags,
        metadata=request.metadata,
    )

    bookmark_id = store.save_bookmark(bookmark)

    # Emit event
    from src.core.realtime import EventType, get_event_bus
    bus = get_event_bus()
    bus.emit(EventType.BOOKMARK_ADDED, {
        "id": bookmark_id,
        "name": request.name,
        "url": request.url,
        "type": request.type,
    })

    return {"success": True, "id": bookmark_id}


@router.get("/bookmarks")
async def get_bookmarks(
    type: str | None = None,
    tags: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Get bookmarks with optional filtering."""
    store = get_memory_store()

    tag_list = tags.split(",") if tags else None
    bookmarks = store.get_bookmarks(type=type, tags=tag_list, limit=limit)

    return {
        "bookmarks": [b.to_dict() for b in bookmarks],
        "count": len(bookmarks),
    }


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str) -> dict[str, Any]:
    """Delete a bookmark."""
    store = get_memory_store()
    deleted = store.delete_bookmark(bookmark_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return {"success": True, "deleted": bookmark_id}


# ============================================
# Conversation Endpoints
# ============================================

@router.post("/conversations/message")
async def save_message(request: MessageRequest) -> dict[str, Any]:
    """Save a conversation message."""
    store = get_memory_store()

    msg_id = store.save_message(
        session_id=request.session_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )

    return {"success": True, "id": msg_id}


@router.get("/conversations/{session_id}")
async def get_conversation(session_id: str, limit: int = 100) -> dict[str, Any]:
    """Get conversation history."""
    store = get_memory_store()
    messages = store.get_conversation(session_id, limit=limit)

    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }


# ============================================
# Real-time Events (SSE)
# ============================================

@router.get("/events/stream")
async def stream_events():
    """Server-Sent Events stream for real-time updates."""
    bus = get_event_bus()

    async def event_generator():
        async for event in bus.stream_events():
            yield f"data: {event.to_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/events/history")
async def get_event_history(
    type: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Get event history."""
    bus = get_event_bus()

    event_type = None
    if type:
        with contextlib.suppress(ValueError):
            event_type = EventType(type)

    events = bus.get_history(event_type=event_type, limit=limit)

    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.post("/events/emit")
async def emit_event(data: dict[str, Any]) -> dict[str, Any]:
    """Emit a custom event."""
    bus = get_event_bus()

    event_type_str = data.get("type", "notification")
    try:
        event_type = EventType(event_type_str)
    except ValueError:
        event_type = EventType.NOTIFICATION

    await bus.emit_async(
        event_type,
        data.get("data", {}),
        source=data.get("source", "api"),
    )

    return {"success": True, "type": event_type.value}


# ============================================
# Workflow State Endpoints
# ============================================

@router.post("/workflow-state/{workflow_id}")
async def save_workflow_state(workflow_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """Save workflow state."""
    store = get_memory_store()
    state_id = store.save_workflow_state(workflow_id, state)

    return {"success": True, "id": state_id}


@router.get("/workflow-state/{workflow_id}")
async def get_workflow_state(workflow_id: str) -> dict[str, Any]:
    """Get workflow state."""
    store = get_memory_store()
    state = store.get_workflow_state(workflow_id)

    if state is None:
        raise HTTPException(status_code=404, detail="Workflow state not found")

    return {"workflow_id": workflow_id, "state": state}
