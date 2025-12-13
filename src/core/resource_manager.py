"""
Resource manager for preventing resource leaks.
"""

import asyncio
import contextlib
import logging
import os
from typing import Any
from weakref import WeakSet

import psutil

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages and tracks resources to prevent leaks.

    Tracks:
    - Browser instances
    - Database connections
    - File handles
    - Subprocesses
    - Async tasks
    """

    def __init__(self):
        self._active_resources: dict[str, WeakSet] = {
            "browsers": WeakSet(),
            "connections": WeakSet(),
            "files": WeakSet(),
            "processes": WeakSet(),
            "tasks": WeakSet(),
        }
        self._cleanup_callbacks: list[callable] = []
        self._shutdown = False

        # Register cleanup on exit
        import atexit
        atexit.register(self.cleanup_all)

    def register(self, resource: Any, resource_type: str) -> None:
        """
        Register a resource for tracking.

        Args:
            resource: Resource to track
            resource_type: Type of resource (browsers, connections, etc.)
        """
        if resource_type not in self._active_resources:
            self._active_resources[resource_type] = WeakSet()

        self._active_resources[resource_type].add(resource)
        logger.debug(f"Registered {resource_type}: {type(resource).__name__}")

    def unregister(self, resource: Any, resource_type: str) -> None:
        """Unregister a resource."""
        if resource_type in self._active_resources:
            self._active_resources[resource_type].discard(resource)

    def add_cleanup_callback(self, callback: callable) -> None:
        """Add a cleanup callback to be called on shutdown."""
        self._cleanup_callbacks.append(callback)

    async def cleanup_type(self, resource_type: str) -> int:
        """
        Clean up all resources of a specific type.

        Args:
            resource_type: Type of resources to clean

        Returns:
            Number of resources cleaned up
        """
        if resource_type not in self._active_resources:
            return 0

        count = 0
        resources = list(self._active_resources[resource_type])

        for resource in resources:
            try:
                if hasattr(resource, 'close'):
                    if asyncio.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()
                    count += 1
                elif hasattr(resource, 'terminate'):
                    resource.terminate()
                    count += 1
                elif hasattr(resource, 'cancel'):
                    resource.cancel()
                    count += 1
            except Exception as e:
                logger.error(f"Error cleaning up {resource_type}: {e}")

        self._active_resources[resource_type].clear()
        logger.info(f"Cleaned up {count} {resource_type}")
        return count

    def cleanup_all(self) -> None:
        """Clean up all tracked resources."""
        if self._shutdown:
            return

        self._shutdown = True
        total_cleaned = 0

        for resource_type in self._active_resources:
            try:
                # Always run sync cleanup for reliability
                total_cleaned += self._sync_cleanup_type(resource_type)
            except Exception as e:
                logger.error(f"Error during cleanup of {resource_type}: {e}")

        # Run cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}")

        logger.info("Resource manager shutdown complete")

    def _sync_cleanup_type(self, resource_type: str) -> int:
        """Synchronous cleanup for when no event loop is available."""
        count = 0
        resources = list(self._active_resources[resource_type])

        for resource in resources:
            try:
                if hasattr(resource, 'close'):
                    resource.close()
                    count += 1
                elif hasattr(resource, 'terminate'):
                    resource.terminate()
                    count += 1
                elif hasattr(resource, 'cancel'):
                    resource.cancel()
                    count += 1
            except Exception as e:
                logger.error(f"Error cleaning up {resource_type}: {e}")

        self._active_resources[resource_type].clear()
        return count

    def get_stats(self) -> dict[str, int]:
        """Get statistics on active resources."""
        stats = {}
        for resource_type, resources in self._active_resources.items():
            stats[resource_type] = len(resources)
        return stats

    def check_for_leaks(self) -> dict[str, list[str]]:
        """
        Check for potential resource leaks.

        Returns:
            Dictionary of resource types with leaked resources
        """
        leaks = {}

        for resource_type, resources in self._active_resources.items():
            if resources:
                leaks[resource_type] = [
                    f"{type(r).__name__}: {getattr(r, '__repr__', str)(r)}"
                    for r in list(resources)[:5]  # Limit to 5 per type
                ]

        return leaks


# Global resource manager instance
resource_manager = ResourceManager()


@contextlib.asynccontextmanager
async def managed_browser(browser_factory):
    """
    Context manager for browser instances.

    Args:
        browser_factory: Async function that creates a browser

    Yields:
        Browser instance that will be cleaned up
    """
    browser = None
    try:
        browser = await browser_factory()
        resource_manager.register(browser, "browsers")
        yield browser
    finally:
        if browser:
            resource_manager.unregister(browser, "browsers")
            try:
                await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


@contextlib.asynccontextmanager
async def managed_process(process_factory):
    """
    Context manager for subprocess processes.

    Args:
        process_factory: Function that creates a process

    Yields:
        Process instance that will be cleaned up
    """
    process = None
    try:
        process = process_factory()
        resource_manager.register(process, "processes")
        yield process
    finally:
        if process:
            resource_manager.unregister(process, "processes")
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error terminating process: {e}")


class ResourceLeakDetector:
    """Detects resource leaks by monitoring system resources."""

    def __init__(self):
        self.baseline = self._get_current_usage()

    def _get_current_usage(self) -> dict[str, float]:
        """Get current resource usage."""
        process = psutil.Process(os.getpid())
        return {
            "fds": process.num_fds() if hasattr(process, 'num_fds') else 0,
            "threads": process.num_threads(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
        }

    def check_for_leaks(self, threshold: float = 1.5) -> dict[str, bool]:
        """
        Check if resources have increased beyond threshold.

        Args:
            threshold: Multiplier for baseline to consider a leak

        Returns:
            Dictionary indicating which resources might be leaking
        """
        current = self._get_current_usage()
        leaks = {}

        for key, baseline_value in self.baseline.items():
            if key == "cpu_percent":
                continue  # CPU varies too much

            current_value = current[key]
            if baseline_value > 0:
                ratio = current_value / baseline_value
                leaks[key] = ratio > threshold

                if leaks[key]:
                    logger.warning(
                        f"Potential leak detected for {key}: "
                        f"{current_value:.2f} vs baseline {baseline_value:.2f}"
                    )

        return leaks


# Periodic leak checker
async def start_leak_monitor(interval: int = 60):
    """
    Start monitoring for resource leaks.

    Args:
        interval: Check interval in seconds
    """
    detector = ResourceLeakDetector()

    while True:
        await asyncio.sleep(interval)
        detector.check_for_leaks()
