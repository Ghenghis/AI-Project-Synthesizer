"""
AI Project Synthesizer - Lifecycle Management

Enterprise-grade lifecycle management with graceful shutdown,
signal handling, and cleanup procedures for production deployment.
"""

import asyncio
import signal
import logging
import threading
import time
from typing import Set, Callable, Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from contextlib import asynccontextmanager
import weakref

logger = logging.getLogger(__name__)


class ShutdownState(Enum):
    """Shutdown states."""
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN_COMPLETE = "shutdown_complete"


@dataclass
class ShutdownTask:
    """Task to execute during shutdown."""
    name: str
    func: Callable
    priority: int = 0  # Higher priority runs first
    timeout: float = 30.0
    required: bool = True  # Whether failure should abort shutdown


class LifecycleManager:
    """
    Manages application lifecycle with graceful shutdown.
    
    Handles signal registration, shutdown tasks, and cleanup procedures.
    Ensures all components shutdown properly without data loss.
    """

    def __init__(self, shutdown_timeout: float = 60.0):
        """
        Initialize lifecycle manager.
        
        Args:
            shutdown_timeout: Maximum time to wait for shutdown
        """
        self.shutdown_timeout = shutdown_timeout
        self._state = ShutdownState.RUNNING
        self._shutdown_tasks: List[ShutdownTask] = []
        self._running_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        self._shutdown_complete_event = asyncio.Event()
        self._lock = threading.Lock()
        self._startup_time = time.time()
        self._shutdown_reason: Optional[str] = None

        # Register signal handlers
        self._setup_signal_handlers()

        logger.info("LifecycleManager initialized")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        try:
            # Windows doesn't support SIGTERM properly
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, self._signal_handler)

            signal.signal(signal.SIGINT, self._signal_handler)

            # Windows-specific signals
            if hasattr(signal, 'SIGBREAK'):
                signal.signal(signal.SIGBREAK, self._signal_handler)

        except Exception as e:
            logger.warning(f"Failed to setup signal handlers: {e}")

    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        logger.info(f"Received signal {signal_name}, initiating graceful shutdown")
        self._shutdown_reason = f"Signal {signal_name}"

        # Trigger shutdown in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(self._shutdown_event.set)
            else:
                # If loop is not running, create new one for shutdown
                asyncio.run(self.shutdown())
        except Exception as e:
            logger.error(f"Failed to trigger shutdown: {e}")

    def add_shutdown_task(
        self,
        name: str,
        func: Callable,
        priority: int = 0,
        timeout: float = 30.0,
        required: bool = True
    ):
        """
        Add shutdown task.
        
        Args:
            name: Task name for logging
            func: Async function to execute
            priority: Higher priority runs first
            timeout: Task timeout
            required: Whether failure should abort shutdown
        """
        task = ShutdownTask(name, func, priority, timeout, required)

        with self._lock:
            self._shutdown_tasks.append(task)
            # Sort by priority (descending)
            self._shutdown_tasks.sort(key=lambda t: t.priority, reverse=True)

        logger.debug(f"Added shutdown task: {name} (priority={priority})")

    def remove_shutdown_task(self, name: str):
        """Remove shutdown task by name."""
        with self._lock:
            self._shutdown_tasks = [t for t in self._shutdown_tasks if t.name != name]

        logger.debug(f"Removed shutdown task: {name}")

    def track_task(self, task: asyncio.Task):
        """
        Track a running task for shutdown.
        
        Args:
            task: Task to track
        """
        self._running_tasks.add(task)

        # Remove task when done
        def cleanup(task_ref):
            try:
                task_obj = task_ref()
                if task_obj:
                    self._running_tasks.discard(task_obj)
            except Exception:
                pass

        task_ref = weakref.ref(task, cleanup)

    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._state != ShutdownState.RUNNING

    def is_shutdown_complete(self) -> bool:
        """Check if shutdown is complete."""
        return self._state == ShutdownState.SHUTDOWN_COMPLETE

    async def shutdown(self, reason: Optional[str] = None):
        """
        Execute graceful shutdown.
        
        Args:
            reason: Optional shutdown reason
        """
        if self._state != ShutdownState.RUNNING:
            logger.warning("Shutdown already in progress")
            return

        logger.info("=" * 60)
        logger.info("Starting graceful shutdown")
        if reason:
            logger.info(f"Shutdown reason: {reason}")
            self._shutdown_reason = reason
        logger.info("=" * 60)

        self._state = ShutdownState.SHUTTING_DOWN
        shutdown_start = time.time()

        try:
            # Cancel all running tasks
            await self._cancel_running_tasks()

            # Execute shutdown tasks
            await self._execute_shutdown_tasks()

            # Close any remaining resources
            await self._cleanup_resources()

            self._state = ShutdownState.SHUTDOWN_COMPLETE
            shutdown_duration = time.time() - shutdown_start

            logger.info("=" * 60)
            logger.info(f"Graceful shutdown completed in {shutdown_duration:.2f}s")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise
        finally:
            self._shutdown_complete_event.set()

    async def _cancel_running_tasks(self):
        """Cancel all tracked running tasks."""
        if not self._running_tasks:
            return

        logger.info(f"Cancelling {len(self._running_tasks)} running tasks")

        # Cancel all tasks
        for task in self._running_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._running_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._running_tasks, return_exceptions=True),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete within timeout")

        self._running_tasks.clear()
        logger.info("All running tasks cancelled")

    async def _execute_shutdown_tasks(self):
        """Execute all shutdown tasks."""
        if not self._shutdown_tasks:
            return

        logger.info(f"Executing {len(self._shutdown_tasks)} shutdown tasks")

        for task in self._shutdown_tasks:
            try:
                logger.info(f"Executing shutdown task: {task.name}")
                start_time = time.time()

                await asyncio.wait_for(task.func(), timeout=task.timeout)

                duration = time.time() - start_time
                logger.info(f"Shutdown task {task.name} completed in {duration:.2f}s")

            except asyncio.TimeoutError:
                error_msg = f"Shutdown task {task.name} timed out after {task.timeout}s"
                logger.error(error_msg)
                if task.required:
                    raise TimeoutError(error_msg)
            except Exception as e:
                error_msg = f"Shutdown task {task.name} failed: {e}"
                logger.error(error_msg)
                if task.required:
                    raise RuntimeError(error_msg)

        logger.info("All shutdown tasks completed")

    async def _cleanup_resources(self):
        """Cleanup any remaining resources."""
        logger.info("Cleaning up resources")

        # Add any additional cleanup logic here
        # For example: close database connections, flush logs, etc.

        logger.info("Resource cleanup completed")

    def get_status(self) -> Dict[str, Any]:
        """Get current lifecycle status."""
        uptime = time.time() - self._startup_time

        return {
            "state": self._state.value,
            "uptime_seconds": uptime,
            "shutdown_reason": self._shutdown_reason,
            "running_tasks": len(self._running_tasks),
            "shutdown_tasks": len(self._shutdown_tasks),
            "startup_time": self._startup_time,
        }


# Global lifecycle manager
lifecycle = LifecycleManager()


class ResourceManager:
    """
    Manages resources that need cleanup during shutdown.
    """

    def __init__(self):
        self._resources: Dict[str, Callable] = {}
        self._lock = threading.Lock()

    def register(self, name: str, cleanup_func: Callable):
        """
        Register resource for cleanup.
        
        Args:
            name: Resource name
            cleanup_func: Async cleanup function
        """
        with self._lock:
            self._resources[name] = cleanup_func

        logger.debug(f"Registered resource: {name}")

    def unregister(self, name: str):
        """Unregister resource."""
        with self._lock:
            self._resources.pop(name, None)

        logger.debug(f"Unregistered resource: {name}")

    async def cleanup_all(self):
        """Cleanup all registered resources."""
        with self._lock:
            resources = dict(self._resources)

        if not resources:
            return

        logger.info(f"Cleaning up {len(resources)} resources")

        for name, cleanup_func in resources.items():
            try:
                logger.debug(f"Cleaning up resource: {name}")
                await cleanup_func()
                logger.debug(f"Resource {name} cleaned up")
            except Exception as e:
                logger.error(f"Failed to cleanup resource {name}: {e}")

        logger.info("All resources cleaned up")


# Global resource manager
resources = ResourceManager()


@asynccontextmanager
async def managed_resource(name: str, cleanup_func: Callable):
    """
    Context manager for managed resources.
    
    Args:
        name: Resource name
        cleanup_func: Cleanup function
    """
    resources.register(name, cleanup_func)
    try:
        yield
    finally:
        try:
            await cleanup_func()
        finally:
            resources.unregister(name)


def track_async_task(coro):
    """
    Decorator to track async tasks for shutdown.
    
    Args:
        coro: Coroutine to track
        
    Returns:
        Tracked task
    """
    task = asyncio.create_task(coro)
    lifecycle.track_task(task)
    return task


def shutdown_on_signal(shutdown_func: Callable, priority: int = 0):
    """
    Decorator to register function for shutdown.
    
    Args:
        shutdown_func: Function to call during shutdown
        priority: Shutdown priority
        
    Returns:
        Original function
    """
    # Generate unique task name
    task_name = f"{shutdown_func.__name__}_{id(shutdown_func)}"

    lifecycle.add_shutdown_task(
        name=task_name,
        func=shutdown_func,
        priority=priority
    )

    return shutdown_func


def get_lifecycle_status() -> Dict[str, Any]:
    """Get global lifecycle status."""
    return lifecycle.get_status()


async def wait_for_shutdown_signal():
    """Wait for shutdown signal."""
    await lifecycle.wait_for_shutdown()


async def initiate_shutdown(reason: Optional[str] = None):
    """Initiate graceful shutdown."""
    await lifecycle.shutdown(reason)


def is_shutting_down() -> bool:
    """Check if shutdown is in progress."""
    return lifecycle.is_shutting_down()


# Built-in shutdown tasks
async def shutdown_logging():
    """Flush logging during shutdown."""
    try:
        import logging
        for handler in logging.root.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
    except Exception as e:
        logger.error(f"Failed to flush logging: {e}")


async def shutdown_metrics():
    """Finalize metrics during shutdown."""
    try:
        from src.core.observability import metrics
        # Log final metrics summary
        summary = metrics.get_all_metrics()
        logger.info(f"Final metrics: {len(summary)} metrics collected")
    except Exception as e:
        logger.error(f"Failed to finalize metrics: {e}")


# Register built-in shutdown tasks
lifecycle.add_shutdown_task("logging", shutdown_logging, priority=100)
lifecycle.add_shutdown_task("metrics", shutdown_metrics, priority=90)


class BackgroundTaskManager:
    """
    Manages background tasks with proper lifecycle integration.
    """

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._tasks: Set[asyncio.Task] = set()

    async def submit(self, coro, name: Optional[str] = None):
        """
        Submit background task.
        
        Args:
            coro: Coroutine to run
            name: Optional task name
            
        Returns:
            Task handle
        """
        async def wrapped_task():
            async with self._semaphore:
                try:
                    return await coro
                except Exception as e:
                    if name:
                        logger.error(f"Background task {name} failed: {e}")
                    else:
                        logger.error(f"Background task failed: {e}")
                    raise
                finally:
                    self._tasks.discard(task)

        task = asyncio.create_task(wrapped_task())
        self._tasks.add(task)
        lifecycle.track_task(task)

        return task

    async def wait_all(self, timeout: Optional[float] = None):
        """Wait for all tasks to complete."""
        if not self._tasks:
            return

        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Background tasks did not complete within timeout")


# Global background task manager
background_tasks = BackgroundTaskManager()
