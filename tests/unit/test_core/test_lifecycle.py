"""
Unit tests for core.lifecycle module.
"""

import os

import pytest

os.environ["APP_ENV"] = "testing"

from src.core.lifecycle import LifecycleManager, ShutdownState, ShutdownTask


class TestShutdownState:
    """Test ShutdownState enum."""

    def test_shutdown_state_values(self):
        """Test all shutdown states are defined."""
        assert ShutdownState.RUNNING.value == "running"
        assert ShutdownState.SHUTTING_DOWN.value == "shutting_down"
        assert ShutdownState.SHUTDOWN_COMPLETE.value == "shutdown_complete"


class TestShutdownTask:
    """Test ShutdownTask dataclass."""

    def test_shutdown_task_creation(self):
        """Test creating a shutdown task."""

        def cleanup():
            pass

        task = ShutdownTask(
            name="cleanup_task", func=cleanup, priority=10, timeout=30.0, required=True
        )

        assert task.name == "cleanup_task"
        assert task.priority == 10
        assert task.timeout == 30.0
        assert task.required == True


class TestLifecycleManager:
    """Test LifecycleManager class."""

    def test_manager_initialization(self):
        """Test manager initializes correctly."""
        manager = LifecycleManager()
        assert manager is not None
        assert manager._state == ShutdownState.RUNNING

    def test_manager_with_custom_timeout(self):
        """Test manager with custom shutdown timeout."""
        manager = LifecycleManager(shutdown_timeout=120.0)
        assert manager.shutdown_timeout == 120.0

    def test_add_shutdown_task(self):
        """Test adding shutdown tasks."""
        manager = LifecycleManager()

        def cleanup():
            pass

        manager.add_shutdown_task(name="test_cleanup", func=cleanup, priority=5)

        assert len(manager._shutdown_tasks) >= 1

    def test_is_shutting_down(self):
        """Test is_shutting_down method."""
        manager = LifecycleManager()

        assert manager.is_shutting_down() == False

        manager._state = ShutdownState.SHUTTING_DOWN
        assert manager.is_shutting_down() == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
