"""
AI Project Synthesizer - Real-time Event System

Real-time event handling for:
- Workflow updates
- Agent status changes
- Search results streaming
- Health monitoring
- Notifications
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class EventType(str, Enum):
    """Types of real-time events."""
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PROGRESS = "workflow.progress"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_STEP = "agent.step"
    AGENT_COMPLETED = "agent.completed"
    AGENT_ERROR = "agent.error"

    # Search events
    SEARCH_STARTED = "search.started"
    SEARCH_RESULT = "search.result"
    SEARCH_COMPLETED = "search.completed"

    # Health events
    HEALTH_CHECK = "health.check"
    HEALTH_ALERT = "health.alert"
    HEALTH_RECOVERED = "health.recovered"

    # System events
    NOTIFICATION = "notification"
    ERROR = "error"
    LOG = "log"

    # Memory events
    BOOKMARK_ADDED = "bookmark.added"
    SEARCH_SAVED = "search.saved"

    # Voice events
    VOICE_STARTED = "voice.started"
    VOICE_TRANSCRIPTION = "voice.transcription"
    VOICE_RESPONSE = "voice.response"


@dataclass
class Event:
    """Real-time event."""
    type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "source": self.source,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventBus:
    """
    Central event bus for real-time communication.
    
    Features:
    - Pub/sub pattern
    - Async event handling
    - Event filtering
    - Event history
    """

    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._history: List[Event] = []
        self._max_history = max_history
        self._queues: Set[asyncio.Queue] = set()

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable,
    ):
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable):
        """Subscribe to all events."""
        self._global_subscribers.append(callback)

    def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable,
    ):
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type]
                if cb != callback
            ]

    async def publish(self, event: Event):
        """Publish an event."""
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Notify specific subscribers
        for callback in self._subscribers.get(event.type, []):
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                secure_logger.error(f"Event callback error: {e}")

        # Notify global subscribers
        for callback in self._global_subscribers:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                secure_logger.error(f"Global callback error: {e}")

        # Push to queues (for SSE/WebSocket)
        for queue in self._queues:
            try:
                await queue.put(event)
            except Exception:
                pass

    def emit(self, event_type: EventType, data: Dict[str, Any], source: str = "system"):
        """Emit an event (sync wrapper)."""
        event = Event(type=event_type, data=data, source=source)
        asyncio.create_task(self.publish(event))

    async def emit_async(self, event_type: EventType, data: Dict[str, Any], source: str = "system"):
        """Emit an event asynchronously."""
        event = Event(type=event_type, data=data, source=source)
        await self.publish(event)

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get event history."""
        events = self._history

        if event_type:
            events = [e for e in events if e.type == event_type]

        return events[-limit:]

    def create_queue(self) -> asyncio.Queue:
        """Create a queue for streaming events."""
        queue = asyncio.Queue()
        self._queues.add(queue)
        return queue

    def remove_queue(self, queue: asyncio.Queue):
        """Remove a queue."""
        self._queues.discard(queue)

    async def stream_events(
        self,
        event_types: Optional[List[EventType]] = None,
    ):
        """Async generator for streaming events."""
        queue = self.create_queue()

        try:
            while True:
                event = await queue.get()

                if event_types is None or event.type in event_types:
                    yield event
        finally:
            self.remove_queue(queue)


# Global event bus
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# ============================================
# Convenience Functions
# ============================================

def emit_workflow_event(
    workflow_id: str,
    status: str,
    progress: Optional[float] = None,
    message: str = "",
):
    """Emit a workflow event."""
    bus = get_event_bus()

    event_map = {
        "started": EventType.WORKFLOW_STARTED,
        "progress": EventType.WORKFLOW_PROGRESS,
        "completed": EventType.WORKFLOW_COMPLETED,
        "failed": EventType.WORKFLOW_FAILED,
    }

    event_type = event_map.get(status, EventType.WORKFLOW_PROGRESS)

    bus.emit(event_type, {
        "workflow_id": workflow_id,
        "status": status,
        "progress": progress,
        "message": message,
    }, source="workflow")


def emit_agent_event(
    agent_name: str,
    status: str,
    step: Optional[int] = None,
    output: Optional[str] = None,
):
    """Emit an agent event."""
    bus = get_event_bus()

    event_map = {
        "started": EventType.AGENT_STARTED,
        "step": EventType.AGENT_STEP,
        "completed": EventType.AGENT_COMPLETED,
        "error": EventType.AGENT_ERROR,
    }

    event_type = event_map.get(status, EventType.AGENT_STEP)

    bus.emit(event_type, {
        "agent": agent_name,
        "status": status,
        "step": step,
        "output": output,
    }, source="agent")


def emit_search_event(
    query: str,
    status: str,
    results: Optional[List[Dict]] = None,
    count: int = 0,
):
    """Emit a search event."""
    bus = get_event_bus()

    event_map = {
        "started": EventType.SEARCH_STARTED,
        "result": EventType.SEARCH_RESULT,
        "completed": EventType.SEARCH_COMPLETED,
    }

    event_type = event_map.get(status, EventType.SEARCH_RESULT)

    bus.emit(event_type, {
        "query": query,
        "status": status,
        "results": results,
        "count": count,
    }, source="search")


def emit_notification(
    title: str,
    message: str,
    level: str = "info",
):
    """Emit a notification event."""
    bus = get_event_bus()

    bus.emit(EventType.NOTIFICATION, {
        "title": title,
        "message": message,
        "level": level,
    }, source="notification")
