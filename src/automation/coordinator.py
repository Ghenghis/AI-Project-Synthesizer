"""
AI Project Synthesizer - Automation Coordinator

Central coordinator for seamless automation:
- n8n workflow management
- Event-driven actions
- Scheduled tasks
- Real-time monitoring
- Self-healing operations
"""

import asyncio
import json
from typing import Optional, List, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from src.automation.metrics import ActionTimer, get_metrics_collector, MetricsCollector
from src.automation.testing import IntegrationTester, get_default_tests, TestSuiteResult
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class EventType(str, Enum):
    """System event types."""
    SEARCH_STARTED = "search_started"
    SEARCH_COMPLETED = "search_completed"
    SYNTHESIS_STARTED = "synthesis_started"
    SYNTHESIS_COMPLETED = "synthesis_completed"
    VOICE_STARTED = "voice_started"
    VOICE_COMPLETED = "voice_completed"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK = "health_check"
    TEST_COMPLETED = "test_completed"
    WORKFLOW_TRIGGERED = "workflow_triggered"


@dataclass
class SystemEvent:
    """A system event."""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"


@dataclass
class ScheduledTask:
    """A scheduled task."""
    name: str
    task_func: Callable[[], Awaitable[Any]]
    interval_seconds: int
    last_run: Optional[datetime] = None
    enabled: bool = True
    run_immediately: bool = False


@dataclass
class AutomationConfig:
    """Automation configuration."""
    # n8n settings
    n8n_url: str = "http://localhost:5678"
    n8n_enabled: bool = True
    
    # Health check settings
    health_check_interval: int = 60  # seconds
    
    # Auto-recovery settings
    auto_recovery_enabled: bool = True
    max_recovery_attempts: int = 3
    
    # Metrics settings
    metrics_retention_hours: int = 24
    
    # Testing settings
    run_tests_on_startup: bool = True
    test_interval_hours: int = 6


class AutomationCoordinator:
    """
    Central automation coordinator.
    
    Manages:
    - n8n workflow orchestration
    - Event handling and routing
    - Scheduled tasks
    - Health monitoring
    - Auto-recovery
    
    Usage:
        coordinator = AutomationCoordinator()
        await coordinator.start()
        
        # Emit events
        coordinator.emit(EventType.SEARCH_COMPLETED, {"results": 10})
        
        # Get status
        status = coordinator.get_status()
    """
    
    def __init__(self, config: Optional[AutomationConfig] = None):
        self.config = config or AutomationConfig()
        self._running = False
        self._events: List[SystemEvent] = []
        self._event_handlers: Dict[EventType, List[Callable]] = {}
        self._scheduled_tasks: Dict[str, ScheduledTask] = {}
        self._metrics = get_metrics_collector()
        self._tester = IntegrationTester()
        self._n8n = None
        self._background_tasks: List[asyncio.Task] = []
        
        # Register default tests
        self._tester.register_many(get_default_tests())
        
        # Register default event handlers
        self._register_default_handlers()
        
        # Register default scheduled tasks
        self._register_default_tasks()
    
    def _register_default_handlers(self):
        """Register default event handlers."""
        # Log all events
        self.on(EventType.SEARCH_COMPLETED, self._log_event)
        self.on(EventType.SYNTHESIS_COMPLETED, self._log_event)
        self.on(EventType.ERROR_OCCURRED, self._handle_error)
        self.on(EventType.HEALTH_CHECK, self._handle_health_check)
    
    def _register_default_tasks(self):
        """Register default scheduled tasks."""
        # Health check
        self.schedule(ScheduledTask(
            name="health_check",
            task_func=self._run_health_check,
            interval_seconds=self.config.health_check_interval,
            run_immediately=True,
        ))
        
        # Metrics cleanup
        self.schedule(ScheduledTask(
            name="metrics_cleanup",
            task_func=self._cleanup_metrics,
            interval_seconds=3600,  # Every hour
        ))
        
        # Integration tests
        if self.config.run_tests_on_startup:
            self.schedule(ScheduledTask(
                name="integration_tests",
                task_func=self._run_integration_tests,
                interval_seconds=self.config.test_interval_hours * 3600,
                run_immediately=True,
            ))
    
    async def start(self):
        """Start the automation coordinator."""
        if self._running:
            return
        
        self._running = True
        secure_logger.info("Automation coordinator starting...")
        
        # Initialize n8n client
        if self.config.n8n_enabled:
            from src.workflows.n8n_integration import N8NClient
            self._n8n = N8NClient()
            
            if await self._n8n.health_check():
                secure_logger.info("n8n connection established")
            else:
                secure_logger.warning("n8n not available")
        
        # Start scheduler
        task = asyncio.create_task(self._scheduler_loop())
        self._background_tasks.append(task)
        
        # Start event processor
        task = asyncio.create_task(self._event_processor_loop())
        self._background_tasks.append(task)
        
        secure_logger.info("Automation coordinator started")
    
    async def stop(self):
        """Stop the automation coordinator."""
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
        if self._n8n:
            await self._n8n.close()
        
        secure_logger.info("Automation coordinator stopped")
    
    # ============================================
    # Event System
    # ============================================
    
    def emit(self, event_type: EventType, data: Dict[str, Any] = None, source: str = "system"):
        """Emit a system event."""
        event = SystemEvent(
            event_type=event_type,
            data=data or {},
            source=source,
        )
        self._events.append(event)
        
        # Keep only recent events
        if len(self._events) > 1000:
            self._events = self._events[-500:]
    
    def on(self, event_type: EventType, handler: Callable):
        """Register an event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _event_processor_loop(self):
        """Process events in background."""
        processed_count = 0
        
        while self._running:
            try:
                # Process new events
                while processed_count < len(self._events):
                    event = self._events[processed_count]
                    await self._process_event(event)
                    processed_count += 1
                
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                secure_logger.error(f"Event processor error: {e}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event: SystemEvent):
        """Process a single event."""
        handlers = self._event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                secure_logger.error(f"Event handler error: {e}")
    
    async def _log_event(self, event: SystemEvent):
        """Log an event."""
        secure_logger.info(
            f"Event: {event.event_type.value}",
            extra={"data": event.data, "source": event.source},
        )
    
    async def _handle_error(self, event: SystemEvent):
        """Handle error events."""
        error = event.data.get("error", "Unknown error")
        source = event.source
        
        secure_logger.error(f"Error from {source}: {error}")
        
        # Auto-recovery if enabled
        if self.config.auto_recovery_enabled:
            await self._attempt_recovery(source, event.data)
    
    async def _handle_health_check(self, event: SystemEvent):
        """Handle health check events."""
        status = event.data.get("status", "unknown")
        
        if status != "healthy":
            secure_logger.warning(f"Health check: {status}")
    
    # ============================================
    # Scheduler
    # ============================================
    
    def schedule(self, task: ScheduledTask):
        """Schedule a task."""
        self._scheduled_tasks[task.name] = task
    
    def unschedule(self, name: str):
        """Unschedule a task."""
        self._scheduled_tasks.pop(name, None)
    
    async def _scheduler_loop(self):
        """Run scheduled tasks."""
        while self._running:
            try:
                now = datetime.now()
                
                for name, task in self._scheduled_tasks.items():
                    if not task.enabled:
                        continue
                    
                    should_run = False
                    
                    if task.run_immediately and task.last_run is None:
                        should_run = True
                    elif task.last_run is None:
                        should_run = True
                    elif (now - task.last_run).total_seconds() >= task.interval_seconds:
                        should_run = True
                    
                    if should_run:
                        task.last_run = now
                        asyncio.create_task(self._run_scheduled_task(task))
                
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                secure_logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)
    
    async def _run_scheduled_task(self, task: ScheduledTask):
        """Run a scheduled task."""
        async with ActionTimer(f"scheduled_{task.name}", self._metrics):
            try:
                await task.task_func()
            except Exception as e:
                secure_logger.error(f"Scheduled task {task.name} failed: {e}")
                self.emit(EventType.ERROR_OCCURRED, {
                    "error": str(e),
                    "task": task.name,
                }, source="scheduler")
    
    # ============================================
    # Built-in Tasks
    # ============================================
    
    async def _run_health_check(self):
        """Run system health check."""
        from src.core.health import check_health
        
        health = await check_health()
        
        self.emit(EventType.HEALTH_CHECK, {
            "status": health.status.value,
            "components": [c.name for c in health.components if c.status.value == "healthy"],
        })
    
    async def _cleanup_metrics(self):
        """Cleanup old metrics."""
        # Metrics collector handles its own cleanup
        pass
    
    async def _run_integration_tests(self) -> TestSuiteResult:
        """Run integration tests."""
        result = await self._tester.run_all()
        
        self.emit(EventType.TEST_COMPLETED, {
            "total": result.total,
            "passed": result.passed,
            "failed": result.failed,
            "success_rate": result.success_rate,
        })
        
        return result
    
    async def _attempt_recovery(self, source: str, data: Dict[str, Any]):
        """Attempt auto-recovery from error."""
        secure_logger.info(f"Attempting recovery for {source}")
        
        # Simple recovery strategies
        if "connection" in str(data.get("error", "")).lower():
            # Wait and retry
            await asyncio.sleep(5)
            secure_logger.info(f"Recovery: waited 5s for {source}")
    
    # ============================================
    # n8n Integration
    # ============================================
    
    async def trigger_n8n_workflow(
        self,
        workflow_id: str,
        data: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """Trigger an n8n workflow."""
        if not self._n8n:
            return None
        
        async with ActionTimer("n8n_workflow", self._metrics):
            result = await self._n8n.execute_workflow(workflow_id, data)
            
            self.emit(EventType.WORKFLOW_TRIGGERED, {
                "workflow_id": workflow_id,
                "success": result is not None,
            })
            
            return result.data if result else None
    
    async def setup_n8n_workflows(self) -> Dict[str, str]:
        """Set up default n8n workflows."""
        if not self._n8n:
            return {}
        
        from src.workflows.n8n_integration import setup_n8n_workflows
        return await setup_n8n_workflows(self._n8n)
    
    # ============================================
    # Status & Monitoring
    # ============================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status."""
        return {
            "running": self._running,
            "n8n_enabled": self.config.n8n_enabled,
            "scheduled_tasks": list(self._scheduled_tasks.keys()),
            "event_count": len(self._events),
            "recent_events": [
                {
                    "type": e.event_type.value,
                    "timestamp": e.timestamp.isoformat(),
                    "source": e.source,
                }
                for e in self._events[-10:]
            ],
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return self._metrics.get_summary()
    
    async def run_tests(self, category: str = None) -> TestSuiteResult:
        """Run tests on demand."""
        if category:
            return await self._tester.run_category(category)
        return await self._tester.run_all()


# Global coordinator instance
_coordinator: Optional[AutomationCoordinator] = None


def get_coordinator() -> AutomationCoordinator:
    """Get or create automation coordinator."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AutomationCoordinator()
    return _coordinator


async def start_automation():
    """Start the automation system."""
    coordinator = get_coordinator()
    await coordinator.start()
    return coordinator
