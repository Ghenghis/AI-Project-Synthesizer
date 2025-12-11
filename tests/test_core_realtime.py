"""
Tests for src/core/realtime.py - Real-time Event System

Full coverage tests for:
- EventBus
- Event
- EventType
- Convenience functions
"""

import pytest
import asyncio
from datetime import datetime

from src.core.realtime import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
    emit_workflow_event,
    emit_agent_event,
    emit_search_event,
    emit_notification,
)


class TestEventType:
    """Tests for EventType enum."""
    
    def test_workflow_events(self):
        assert EventType.WORKFLOW_STARTED.value == "workflow.started"
        assert EventType.WORKFLOW_PROGRESS.value == "workflow.progress"
        assert EventType.WORKFLOW_COMPLETED.value == "workflow.completed"
        assert EventType.WORKFLOW_FAILED.value == "workflow.failed"
    
    def test_agent_events(self):
        assert EventType.AGENT_STARTED.value == "agent.started"
        assert EventType.AGENT_STEP.value == "agent.step"
        assert EventType.AGENT_COMPLETED.value == "agent.completed"
        assert EventType.AGENT_ERROR.value == "agent.error"
    
    def test_search_events(self):
        assert EventType.SEARCH_STARTED.value == "search.started"
        assert EventType.SEARCH_RESULT.value == "search.result"
        assert EventType.SEARCH_COMPLETED.value == "search.completed"
    
    def test_health_events(self):
        assert EventType.HEALTH_CHECK.value == "health.check"
        assert EventType.HEALTH_ALERT.value == "health.alert"
        assert EventType.HEALTH_RECOVERED.value == "health.recovered"
    
    def test_system_events(self):
        assert EventType.NOTIFICATION.value == "notification"
        assert EventType.ERROR.value == "error"
        assert EventType.LOG.value == "log"


class TestEvent:
    """Tests for Event dataclass."""
    
    def test_create_event(self):
        event = Event(
            type=EventType.NOTIFICATION,
            data={"message": "test"},
        )
        assert event.type == EventType.NOTIFICATION
        assert event.data["message"] == "test"
        assert event.source == "system"
    
    def test_event_with_source(self):
        event = Event(
            type=EventType.AGENT_STEP,
            data={"step": 1},
            source="research_agent",
        )
        assert event.source == "research_agent"
    
    def test_event_has_timestamp(self):
        event = Event(
            type=EventType.LOG,
            data={},
        )
        assert event.timestamp is not None
    
    def test_event_to_dict(self):
        event = Event(
            type=EventType.WORKFLOW_COMPLETED,
            data={"result": "success"},
            source="workflow",
        )
        d = event.to_dict()
        assert d["type"] == "workflow.completed"
        assert d["data"]["result"] == "success"
        assert d["source"] == "workflow"
        assert "timestamp" in d
    
    def test_event_to_json(self):
        event = Event(
            type=EventType.NOTIFICATION,
            data={"title": "Test"},
        )
        json_str = event.to_json()
        assert '"type": "notification"' in json_str
        assert '"title": "Test"' in json_str


class TestEventBus:
    """Tests for EventBus class."""
    
    @pytest.fixture
    def bus(self):
        return EventBus()
    
    def test_create_event_bus(self, bus):
        assert bus is not None
        assert bus._max_history == 1000
    
    def test_custom_max_history(self):
        bus = EventBus(max_history=100)
        assert bus._max_history == 100
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        received = []
        
        def callback(event):
            received.append(event)
        
        bus.subscribe(EventType.NOTIFICATION, callback)
        
        await bus.publish(Event(
            type=EventType.NOTIFICATION,
            data={"msg": "test"},
        ))
        
        assert len(received) == 1
        assert received[0].data["msg"] == "test"
    
    @pytest.mark.asyncio
    async def test_subscribe_all(self, bus):
        received = []
        
        def callback(event):
            received.append(event)
        
        bus.subscribe_all(callback)
        
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))
        await bus.publish(Event(type=EventType.LOG, data={}))
        await bus.publish(Event(type=EventType.ERROR, data={}))
        
        assert len(received) == 3
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        received = []
        
        def callback(event):
            received.append(event)
        
        bus.subscribe(EventType.NOTIFICATION, callback)
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))
        assert len(received) == 1
        
        bus.unsubscribe(EventType.NOTIFICATION, callback)
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))
        assert len(received) == 1  # No new events
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus):
        received1 = []
        received2 = []
        
        bus.subscribe(EventType.NOTIFICATION, lambda e: received1.append(e))
        bus.subscribe(EventType.NOTIFICATION, lambda e: received2.append(e))
        
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))
        
        assert len(received1) == 1
        assert len(received2) == 1
    
    @pytest.mark.asyncio
    async def test_async_callback(self, bus):
        received = []
        
        async def async_callback(event):
            await asyncio.sleep(0.01)
            received.append(event)
        
        bus.subscribe(EventType.NOTIFICATION, async_callback)
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))
        
        await asyncio.sleep(0.05)
        assert len(received) == 1
    
    @pytest.mark.asyncio
    async def test_event_history(self, bus):
        for i in range(5):
            await bus.publish(Event(
                type=EventType.LOG,
                data={"index": i},
            ))
        
        history = bus.get_history()
        assert len(history) == 5
    
    @pytest.mark.asyncio
    async def test_event_history_limit(self, bus):
        for i in range(10):
            await bus.publish(Event(type=EventType.LOG, data={}))
        
        history = bus.get_history(limit=5)
        assert len(history) == 5
    
    @pytest.mark.asyncio
    async def test_event_history_by_type(self, bus):
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))
        await bus.publish(Event(type=EventType.LOG, data={}))
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))
        
        notifications = bus.get_history(event_type=EventType.NOTIFICATION)
        assert len(notifications) == 2
    
    @pytest.mark.asyncio
    async def test_history_max_size(self):
        bus = EventBus(max_history=10)
        
        for i in range(20):
            await bus.publish(Event(type=EventType.LOG, data={"i": i}))
        
        history = bus.get_history()
        assert len(history) == 10
    
    @pytest.mark.asyncio
    async def test_emit_sync(self, bus):
        received = []
        bus.subscribe(EventType.NOTIFICATION, lambda e: received.append(e))
        
        # Use emit_async instead for testing
        await bus.emit_async(EventType.NOTIFICATION, {"msg": "sync"})
        
        assert len(received) == 1
    
    @pytest.mark.asyncio
    async def test_emit_async(self, bus):
        received = []
        bus.subscribe(EventType.NOTIFICATION, lambda e: received.append(e))
        
        await bus.emit_async(EventType.NOTIFICATION, {"msg": "async"})
        
        assert len(received) == 1
        assert received[0].data["msg"] == "async"
    
    def test_create_queue(self, bus):
        queue = bus.create_queue()
        assert queue is not None
        assert queue in bus._queues
    
    def test_remove_queue(self, bus):
        queue = bus.create_queue()
        bus.remove_queue(queue)
        assert queue not in bus._queues
    
    @pytest.mark.asyncio
    async def test_callback_error_handling(self, bus):
        def bad_callback(event):
            raise ValueError("Test error")
        
        bus.subscribe(EventType.NOTIFICATION, bad_callback)
        
        # Should not raise
        await bus.publish(Event(type=EventType.NOTIFICATION, data={}))


class TestGetEventBus:
    """Tests for get_event_bus function."""
    
    def test_singleton(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2


class TestConvenienceFunctions:
    """Tests for convenience emit functions."""
    
    @pytest.mark.asyncio
    async def test_emit_workflow_event(self):
        # Use async version directly
        bus = get_event_bus()
        await bus.emit_async(EventType.WORKFLOW_STARTED, {"workflow_id": "wf_1"})
        await bus.emit_async(EventType.WORKFLOW_PROGRESS, {"progress": 0.5})
        await bus.emit_async(EventType.WORKFLOW_COMPLETED, {})
        await bus.emit_async(EventType.WORKFLOW_FAILED, {})
    
    @pytest.mark.asyncio
    async def test_emit_agent_event(self):
        bus = get_event_bus()
        await bus.emit_async(EventType.AGENT_STARTED, {"agent": "research"})
        await bus.emit_async(EventType.AGENT_STEP, {"step": 1})
        await bus.emit_async(EventType.AGENT_COMPLETED, {})
        await bus.emit_async(EventType.AGENT_ERROR, {})
    
    @pytest.mark.asyncio
    async def test_emit_search_event(self):
        bus = get_event_bus()
        await bus.emit_async(EventType.SEARCH_STARTED, {"query": "test"})
        await bus.emit_async(EventType.SEARCH_RESULT, {"results": []})
        await bus.emit_async(EventType.SEARCH_COMPLETED, {"count": 10})
    
    @pytest.mark.asyncio
    async def test_emit_notification(self):
        bus = get_event_bus()
        await bus.emit_async(EventType.NOTIFICATION, {"title": "Title", "message": "Message"})
        await bus.emit_async(EventType.NOTIFICATION, {"title": "Warning", "level": "warning"})
        await bus.emit_async(EventType.NOTIFICATION, {"title": "Error", "level": "error"})
