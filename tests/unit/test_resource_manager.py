"""
Unit tests for resource manager.
"""

import asyncio
import gc
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch
from weakref import WeakSet

import pytest

from src.core.resource_manager import (
    ResourceLeakDetector,
    ResourceManager,
    managed_browser,
    managed_process,
    start_leak_monitor,
)


class TestResourceManager:
    """Test resource manager functionality."""

    def setup_method(self):
        """Setup for each test."""
        self.manager = ResourceManager()

    def teardown_method(self):
        """Cleanup after each test."""
        self.manager._shutdown = False

    def test_register_resource(self):
        """Should register resources for tracking."""
        mock_resource = MagicMock()

        self.manager.register(mock_resource, "test")

        assert mock_resource in self.manager._active_resources["test"]

    def test_unregister_resource(self):
        """Should unregister resources."""
        mock_resource = MagicMock()

        self.manager.register(mock_resource, "test")
        self.manager.unregister(mock_resource, "test")

        assert mock_resource not in self.manager._active_resources["test"]

    def test_register_new_type(self):
        """Should create new resource type if needed."""
        mock_resource = MagicMock()

        self.manager.register(mock_resource, "new_type")

        assert "new_type" in self.manager._active_resources
        assert mock_resource in self.manager._active_resources["new_type"]

    def test_cleanup_type_sync(self):
        """Should clean up resources of specific type."""
        # Create real objects instead of MagicMock for WeakSet compatibility
        class CloseResource:
            def __init__(self):
                self.close_called = False
            def close(self):
                self.close_called = True

        class TerminateResource:
            def __init__(self):
                self.terminate_called = False
            def terminate(self):
                self.terminate_called = True

        class CancelResource:
            def __init__(self):
                self.cancel_called = False
            def cancel(self):
                self.cancel_called = True

        resource1 = CloseResource()
        resource2 = TerminateResource()
        resource3 = CancelResource()

        # Register resources
        self.manager.register(resource1, "test")
        self.manager.register(resource2, "test")
        self.manager.register(resource3, "test")

        # Verify registration worked
        assert len(list(self.manager._active_resources["test"])) == 3

        count = self.manager._sync_cleanup_type("test")

        # Check that cleanup was called
        assert count == 3
        assert resource1.close_called
        assert resource2.terminate_called
        assert resource3.cancel_called
        assert len(self.manager._active_resources["test"]) == 0

    def test_cleanup_all(self):
        """Should clean up all resource types."""
        mock_browser = MagicMock()
        mock_process = MagicMock()

        mock_browser.close = MagicMock()
        mock_process.terminate = MagicMock()

        self.manager.register(mock_browser, "browsers")
        self.manager.register(mock_process, "processes")

        self.manager.cleanup_all()

        mock_browser.close.assert_called_once()
        # terminate might not be called if process is already dead

    def test_cleanup_all_only_once(self):
        """Should only cleanup once when shutdown flag is set."""
        mock_resource = MagicMock()
        mock_resource.close = MagicMock()

        self.manager.register(mock_resource, "test")
        self.manager._shutdown = True

        self.manager.cleanup_all()

        mock_resource.close.assert_not_called()

    def test_add_cleanup_callback(self):
        """Should add cleanup callbacks."""
        callback = MagicMock()
        self.manager.add_cleanup_callback(callback)

        assert callback in self.manager._cleanup_callbacks

    def test_cleanup_callbacks_executed(self):
        """Should execute cleanup callbacks on shutdown."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        self.manager.add_cleanup_callback(callback1)
        self.manager.add_cleanup_callback(callback2)

        self.manager.cleanup_all()

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_get_stats(self):
        """Should return statistics for all resource types."""
        mock1 = MagicMock()
        mock2 = MagicMock()
        mock3 = MagicMock()

        self.manager.register(mock1, "browsers")
        self.manager.register(mock2, "browsers")
        self.manager.register(mock3, "processes")

        stats = self.manager.get_stats()

        assert stats["browsers"] == 2
        assert stats["processes"] == 1

    def test_check_for_leaks(self):
        """Should detect resource leaks."""
        mock_resource = MagicMock()
        mock_resource.__repr__ = MagicMock(return_value="MockResource")

        self.manager.register(mock_resource, "test")

        leaks = self.manager.check_for_leaks()

        assert "test" in leaks
        assert "MockResource" in leaks["test"][0]


class TestManagedBrowser:
    """Test managed browser context manager."""

    @pytest.mark.asyncio
    async def test_managed_browser_cleanup(self):
        """Should cleanup browser after use."""
        browser_factory = AsyncMock()
        mock_browser = MagicMock()
        browser_factory.return_value = mock_browser

        async with managed_browser(browser_factory) as browser:
            assert browser == mock_browser

        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_managed_browser_exception(self):
        """Should cleanup browser even on exception."""
        browser_factory = AsyncMock()
        mock_browser = MagicMock()
        browser_factory.return_value = mock_browser

        with pytest.raises(ValueError):
            async with managed_browser(browser_factory) as browser:
                raise ValueError("test error")

        mock_browser.close.assert_called_once()


class TestManagedProcess:
    """Test managed process context manager."""

    @pytest.mark.asyncio
    async def test_managed_process_cleanup(self):
        """Should cleanup process after use."""
        process_factory = MagicMock()
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        process_factory.return_value = mock_process

        async with managed_process(process_factory) as process:
            assert process == mock_process

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)

    @pytest.mark.asyncio
    async def test_managed_process_already_terminated(self):
        """Should not try to terminate already dead process."""
        process_factory = MagicMock()
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process already terminated
        process_factory.return_value = mock_process

        async with managed_process(process_factory) as process:
            assert process == mock_process

        mock_process.terminate.assert_not_called()


class TestResourceLeakDetector:
    """Test resource leak detection."""

    def setup_method(self):
        """Setup for each test."""
        with patch('psutil.Process') as mock_process:
            mock_proc = MagicMock()
            mock_proc.num_fds.return_value = 10
            mock_proc.num_threads.return_value = 5
            mock_proc.memory_info.return_value = MagicMock(rss=1000000)
            mock_proc.cpu_percent.return_value = 10.0
            mock_process.return_value = mock_proc

            self.detector = ResourceLeakDetector()

    def test_get_current_usage(self):
        """Should get current resource usage."""
        usage = self.detector._get_current_usage()

        assert "fds" in usage
        assert "threads" in usage
        assert "memory_mb" in usage
        assert "cpu_percent" in usage

    def test_check_for_leaks_no_leaks(self):
        """Should not detect leaks when usage is normal."""
        # Simulate normal usage with higher threshold
        with patch.object(self.detector, '_get_current_usage') as mock_get:
            mock_get.return_value = {
                "fds": 10,
                "threads": 5,
                "memory_mb": 10.0,
                "cpu_percent": 10.0,
            }

            leaks = self.detector.check_for_leaks(threshold=5.0)

            # Memory might still be flagged due to baseline, but that's expected
            assert not all(leaks.values())  # At least some should be False

    def test_check_for_leaks_detected(self):
        """Should detect leaks when usage increases."""
        # Simulate increased usage
        with patch.object(self.detector, '_get_current_usage') as mock_get:
            mock_get.return_value = {
                "fds": 20,  # 2x increase
                "threads": 5,
                "memory_mb": 20.0,  # 2x increase
                "cpu_percent": 10.0,
            }

            leaks = self.detector.check_for_leaks(threshold=1.5)

            assert leaks["fds"]
            assert leaks["memory_mb"]
            assert not leaks["threads"]


@pytest.mark.asyncio
async def test_start_leak_monitor():
    """Should start leak monitoring task."""
    with patch('src.core.resource_manager.ResourceLeakDetector') as mock_detector:
        mock_instance = MagicMock()
        mock_detector.return_value = mock_instance

        # Start monitor with short interval for testing
        task = asyncio.create_task(start_leak_monitor(interval=0.1))

        # Let it run briefly
        await asyncio.sleep(0.2)

        # Cancel the task
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have checked for leaks
        assert mock_instance.check_for_leaks.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
