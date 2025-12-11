"""
AI Project Synthesizer - Hotkey Manager

Global hotkey system for:
- Voice activation (no pause limits)
- Quick actions
- Automation control
- System commands
"""

import asyncio
from typing import Optional, Dict, Callable, Any, List
from dataclasses import dataclass
from enum import Enum

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)

# Try importing keyboard library
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    keyboard = None


class HotkeyAction(str, Enum):
    """Available hotkey actions."""
    # Voice
    VOICE_TOGGLE = "voice_toggle"
    VOICE_PUSH_TO_TALK = "voice_push_to_talk"
    VOICE_CANCEL = "voice_cancel"

    # Quick actions
    QUICK_SEARCH = "quick_search"
    QUICK_ASSEMBLE = "quick_assemble"
    QUICK_CHAT = "quick_chat"

    # Navigation
    OPEN_SETTINGS = "open_settings"
    OPEN_DASHBOARD = "open_dashboard"

    # Automation
    PAUSE_AUTOMATION = "pause_automation"
    RESUME_AUTOMATION = "resume_automation"

    # System
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class HotkeyBinding:
    """Hotkey binding configuration."""
    action: HotkeyAction
    keys: str
    description: str
    enabled: bool = True
    callback: Optional[Callable] = None
    is_hold: bool = False  # True for push-to-talk style


class HotkeyManager:
    """
    Global hotkey management system.
    
    Features:
    - Register/unregister hotkeys
    - Hold-to-activate mode (for voice)
    - Action callbacks
    - Enable/disable individual hotkeys
    """

    def __init__(self):
        self._bindings: Dict[HotkeyAction, HotkeyBinding] = {}
        self._active_holds: Dict[str, bool] = {}
        self._running = False
        self._callbacks: Dict[HotkeyAction, List[Callable]] = {}
        self._setup_default_bindings()

    def _setup_default_bindings(self):
        """Set up default hotkey bindings."""
        defaults = [
            HotkeyBinding(
                action=HotkeyAction.VOICE_TOGGLE,
                keys="ctrl+shift+v",
                description="Toggle voice input",
            ),
            HotkeyBinding(
                action=HotkeyAction.VOICE_PUSH_TO_TALK,
                keys="ctrl+space",
                description="Push to talk (hold)",
                is_hold=True,
            ),
            HotkeyBinding(
                action=HotkeyAction.VOICE_CANCEL,
                keys="escape",
                description="Cancel voice input",
            ),
            HotkeyBinding(
                action=HotkeyAction.QUICK_SEARCH,
                keys="ctrl+shift+s",
                description="Quick search",
            ),
            HotkeyBinding(
                action=HotkeyAction.QUICK_ASSEMBLE,
                keys="ctrl+shift+a",
                description="Quick assemble project",
            ),
            HotkeyBinding(
                action=HotkeyAction.QUICK_CHAT,
                keys="ctrl+shift+c",
                description="Quick chat",
            ),
            HotkeyBinding(
                action=HotkeyAction.OPEN_SETTINGS,
                keys="ctrl+,",
                description="Open settings",
            ),
            HotkeyBinding(
                action=HotkeyAction.OPEN_DASHBOARD,
                keys="ctrl+shift+d",
                description="Open dashboard",
            ),
            HotkeyBinding(
                action=HotkeyAction.PAUSE_AUTOMATION,
                keys="ctrl+shift+p",
                description="Pause automation",
            ),
            HotkeyBinding(
                action=HotkeyAction.RESUME_AUTOMATION,
                keys="ctrl+shift+r",
                description="Resume automation",
            ),
            HotkeyBinding(
                action=HotkeyAction.EMERGENCY_STOP,
                keys="ctrl+shift+escape",
                description="Emergency stop all",
            ),
        ]

        for binding in defaults:
            self._bindings[binding.action] = binding

    def register(
        self,
        action: HotkeyAction,
        callback: Callable,
        keys: Optional[str] = None,
    ):
        """Register a callback for a hotkey action."""
        if action not in self._callbacks:
            self._callbacks[action] = []
        self._callbacks[action].append(callback)

        if keys and action in self._bindings:
            self._bindings[action].keys = keys

    def unregister(self, action: HotkeyAction, callback: Optional[Callable] = None):
        """Unregister a callback."""
        if callback and action in self._callbacks:
            self._callbacks[action] = [
                cb for cb in self._callbacks[action] if cb != callback
            ]
        elif action in self._callbacks:
            self._callbacks[action] = []

    def set_keys(self, action: HotkeyAction, keys: str):
        """Update hotkey binding."""
        if action in self._bindings:
            old_keys = self._bindings[action].keys
            self._bindings[action].keys = keys

            # Re-register if running
            if self._running and KEYBOARD_AVAILABLE:
                try:
                    keyboard.remove_hotkey(old_keys)
                except:
                    pass
                self._register_keyboard_hotkey(self._bindings[action])

    def enable(self, action: HotkeyAction):
        """Enable a hotkey."""
        if action in self._bindings:
            self._bindings[action].enabled = True

    def disable(self, action: HotkeyAction):
        """Disable a hotkey."""
        if action in self._bindings:
            self._bindings[action].enabled = False

    def _trigger_action(self, action: HotkeyAction, **kwargs):
        """Trigger callbacks for an action."""
        binding = self._bindings.get(action)
        if not binding or not binding.enabled:
            return

        secure_logger.debug(f"Hotkey triggered: {action.value}")

        for callback in self._callbacks.get(action, []):
            try:
                result = callback(**kwargs)
                # Handle async callbacks
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                secure_logger.error(f"Hotkey callback error: {e}")

    def _register_keyboard_hotkey(self, binding: HotkeyBinding):
        """Register a single keyboard hotkey."""
        if not KEYBOARD_AVAILABLE:
            return

        if binding.is_hold:
            # Hold-to-activate (push to talk)
            keyboard.on_press_key(
                binding.keys.split("+")[-1],
                lambda e: self._on_hold_start(binding.action),
                suppress=False,
            )
            keyboard.on_release_key(
                binding.keys.split("+")[-1],
                lambda e: self._on_hold_end(binding.action),
                suppress=False,
            )
        else:
            # Toggle hotkey
            keyboard.add_hotkey(
                binding.keys,
                lambda a=binding.action: self._trigger_action(a),
                suppress=False,
            )

    def _on_hold_start(self, action: HotkeyAction):
        """Handle hold key press."""
        self._active_holds[action.value] = True
        self._trigger_action(action, held=True, started=True)

    def _on_hold_end(self, action: HotkeyAction):
        """Handle hold key release."""
        if self._active_holds.get(action.value):
            self._active_holds[action.value] = False
            self._trigger_action(action, held=False, ended=True)

    def start(self):
        """Start listening for hotkeys."""
        if not KEYBOARD_AVAILABLE:
            secure_logger.warning("Keyboard library not available, hotkeys disabled")
            return

        self._running = True

        for binding in self._bindings.values():
            if binding.enabled:
                self._register_keyboard_hotkey(binding)

        secure_logger.info("Hotkey manager started")

    def stop(self):
        """Stop listening for hotkeys."""
        self._running = False

        if KEYBOARD_AVAILABLE:
            keyboard.unhook_all()

        secure_logger.info("Hotkey manager stopped")

    def get_bindings(self) -> List[Dict[str, Any]]:
        """Get all hotkey bindings."""
        return [
            {
                "action": b.action.value,
                "keys": b.keys,
                "description": b.description,
                "enabled": b.enabled,
                "is_hold": b.is_hold,
            }
            for b in self._bindings.values()
        ]

    def is_holding(self, action: HotkeyAction) -> bool:
        """Check if a hold key is currently held."""
        return self._active_holds.get(action.value, False)


# Global hotkey manager
_hotkey_manager: Optional[HotkeyManager] = None


def get_hotkey_manager() -> HotkeyManager:
    """Get or create hotkey manager."""
    global _hotkey_manager
    if _hotkey_manager is None:
        _hotkey_manager = HotkeyManager()
    return _hotkey_manager
