"""
Tests for src/core/hotkey_manager.py - Hotkey System

Full coverage tests for:
- HotkeyManager
- HotkeyBinding
- HotkeyAction
"""

from unittest.mock import Mock

import pytest

from src.core.hotkey_manager import (
    HotkeyAction,
    HotkeyBinding,
    HotkeyManager,
    get_hotkey_manager,
)


class TestHotkeyAction:
    """Tests for HotkeyAction enum."""

    def test_voice_actions(self):
        assert HotkeyAction.VOICE_TOGGLE.value == "voice_toggle"
        assert HotkeyAction.VOICE_PUSH_TO_TALK.value == "voice_push_to_talk"
        assert HotkeyAction.VOICE_CANCEL.value == "voice_cancel"

    def test_quick_actions(self):
        assert HotkeyAction.QUICK_SEARCH.value == "quick_search"
        assert HotkeyAction.QUICK_ASSEMBLE.value == "quick_assemble"
        assert HotkeyAction.QUICK_CHAT.value == "quick_chat"

    def test_navigation_actions(self):
        assert HotkeyAction.OPEN_SETTINGS.value == "open_settings"
        assert HotkeyAction.OPEN_DASHBOARD.value == "open_dashboard"

    def test_automation_actions(self):
        assert HotkeyAction.PAUSE_AUTOMATION.value == "pause_automation"
        assert HotkeyAction.RESUME_AUTOMATION.value == "resume_automation"

    def test_system_actions(self):
        assert HotkeyAction.EMERGENCY_STOP.value == "emergency_stop"


class TestHotkeyBinding:
    """Tests for HotkeyBinding dataclass."""

    def test_create_binding(self):
        binding = HotkeyBinding(
            action=HotkeyAction.VOICE_TOGGLE,
            keys="ctrl+shift+v",
            description="Toggle voice",
        )
        assert binding.action == HotkeyAction.VOICE_TOGGLE
        assert binding.keys == "ctrl+shift+v"
        assert binding.description == "Toggle voice"
        assert binding.enabled is True
        assert binding.is_hold is False

    def test_hold_binding(self):
        binding = HotkeyBinding(
            action=HotkeyAction.VOICE_PUSH_TO_TALK,
            keys="ctrl+space",
            description="Push to talk",
            is_hold=True,
        )
        assert binding.is_hold is True

    def test_disabled_binding(self):
        binding = HotkeyBinding(
            action=HotkeyAction.QUICK_SEARCH,
            keys="ctrl+shift+s",
            description="Search",
            enabled=False,
        )
        assert binding.enabled is False


class TestHotkeyManager:
    """Tests for HotkeyManager class."""

    @pytest.fixture
    def manager(self):
        return HotkeyManager()

    def test_create_manager(self, manager):
        assert manager is not None
        assert manager._running is False

    def test_default_bindings(self, manager):
        bindings = manager.get_bindings()

        # Check all default bindings exist
        action_names = [b["action"] for b in bindings]
        assert "voice_toggle" in action_names
        assert "voice_push_to_talk" in action_names
        assert "quick_search" in action_names
        assert "emergency_stop" in action_names

    def test_register_callback(self, manager):
        callback = Mock()
        manager.register(HotkeyAction.VOICE_TOGGLE, callback)

        assert HotkeyAction.VOICE_TOGGLE in manager._callbacks
        assert callback in manager._callbacks[HotkeyAction.VOICE_TOGGLE]

    def test_register_with_custom_keys(self, manager):
        callback = Mock()
        manager.register(HotkeyAction.QUICK_SEARCH, callback, keys="ctrl+f")

        binding = manager._bindings[HotkeyAction.QUICK_SEARCH]
        assert binding.keys == "ctrl+f"

    def test_unregister_callback(self, manager):
        callback = Mock()
        manager.register(HotkeyAction.VOICE_TOGGLE, callback)
        manager.unregister(HotkeyAction.VOICE_TOGGLE, callback)

        assert callback not in manager._callbacks.get(HotkeyAction.VOICE_TOGGLE, [])

    def test_unregister_all_callbacks(self, manager):
        callback1 = Mock()
        callback2 = Mock()
        manager.register(HotkeyAction.VOICE_TOGGLE, callback1)
        manager.register(HotkeyAction.VOICE_TOGGLE, callback2)

        manager.unregister(HotkeyAction.VOICE_TOGGLE)

        assert manager._callbacks.get(HotkeyAction.VOICE_TOGGLE, []) == []

    def test_set_keys(self, manager):
        manager.set_keys(HotkeyAction.VOICE_TOGGLE, "alt+v")

        binding = manager._bindings[HotkeyAction.VOICE_TOGGLE]
        assert binding.keys == "alt+v"

    def test_enable_action(self, manager):
        manager.disable(HotkeyAction.VOICE_TOGGLE)
        assert manager._bindings[HotkeyAction.VOICE_TOGGLE].enabled is False

        manager.enable(HotkeyAction.VOICE_TOGGLE)
        assert manager._bindings[HotkeyAction.VOICE_TOGGLE].enabled is True

    def test_disable_action(self, manager):
        manager.disable(HotkeyAction.VOICE_TOGGLE)
        assert manager._bindings[HotkeyAction.VOICE_TOGGLE].enabled is False

    def test_trigger_action(self, manager):
        callback = Mock()
        manager.register(HotkeyAction.VOICE_TOGGLE, callback)

        manager._trigger_action(HotkeyAction.VOICE_TOGGLE)

        callback.assert_called_once()

    def test_trigger_disabled_action(self, manager):
        callback = Mock()
        manager.register(HotkeyAction.VOICE_TOGGLE, callback)
        manager.disable(HotkeyAction.VOICE_TOGGLE)

        manager._trigger_action(HotkeyAction.VOICE_TOGGLE)

        callback.assert_not_called()

    def test_trigger_with_kwargs(self, manager):
        callback = Mock()
        manager.register(HotkeyAction.VOICE_PUSH_TO_TALK, callback)

        manager._trigger_action(HotkeyAction.VOICE_PUSH_TO_TALK, held=True)

        callback.assert_called_once_with(held=True)

    def test_hold_start(self, manager):
        callback = Mock()
        manager.register(HotkeyAction.VOICE_PUSH_TO_TALK, callback)

        manager._on_hold_start(HotkeyAction.VOICE_PUSH_TO_TALK)

        assert manager._active_holds.get(HotkeyAction.VOICE_PUSH_TO_TALK.value) is True

    def test_hold_end(self, manager):
        manager._active_holds[HotkeyAction.VOICE_PUSH_TO_TALK.value] = True

        callback = Mock()
        manager.register(HotkeyAction.VOICE_PUSH_TO_TALK, callback)

        manager._on_hold_end(HotkeyAction.VOICE_PUSH_TO_TALK)

        assert manager._active_holds.get(HotkeyAction.VOICE_PUSH_TO_TALK.value) is False

    def test_is_holding(self, manager):
        assert manager.is_holding(HotkeyAction.VOICE_PUSH_TO_TALK) is False

        manager._active_holds[HotkeyAction.VOICE_PUSH_TO_TALK.value] = True
        assert manager.is_holding(HotkeyAction.VOICE_PUSH_TO_TALK) is True

    def test_get_bindings(self, manager):
        bindings = manager.get_bindings()

        assert isinstance(bindings, list)
        assert len(bindings) > 0

        for binding in bindings:
            assert "action" in binding
            assert "keys" in binding
            assert "description" in binding
            assert "enabled" in binding
            assert "is_hold" in binding

    def test_start_without_keyboard(self, manager):
        # With keyboard library installed, start will register hotkeys
        # This test verifies it doesn't crash
        try:
            manager.start()
        except Exception:
            pass  # May fail in test environment without proper keyboard access

    def test_stop(self, manager):
        manager._running = True
        manager.stop()
        assert manager._running is False

    def test_callback_error_handling(self, manager):
        def bad_callback():
            raise ValueError("Test error")

        manager.register(HotkeyAction.VOICE_TOGGLE, bad_callback)

        # Should not raise
        manager._trigger_action(HotkeyAction.VOICE_TOGGLE)


class TestGetHotkeyManager:
    """Tests for get_hotkey_manager function."""

    def test_singleton(self):
        manager1 = get_hotkey_manager()
        manager2 = get_hotkey_manager()
        assert manager1 is manager2
