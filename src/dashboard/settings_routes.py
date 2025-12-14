"""
AI Project Synthesizer - Settings API Routes

API endpoints for settings management:
- Get/update settings by tab
- Feature toggles
- Hotkey management
- Export/import settings
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.hotkey_manager import HotkeyAction, get_hotkey_manager
from src.core.security import get_secure_logger
from src.core.settings_manager import (
    SettingsTab,
    get_settings_manager,
)

secure_logger = get_secure_logger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


# Request models
class UpdateSettingsRequest(BaseModel):
    """Request to update settings."""

    updates: dict[str, Any]


class ToggleFeatureRequest(BaseModel):
    """Request to toggle a feature."""

    feature: str


class UpdateHotkeyRequest(BaseModel):
    """Request to update a hotkey."""

    action: str
    keys: str


# ============================================
# Settings Endpoints
# ============================================


@router.get("")
async def get_all_settings() -> dict[str, Any]:
    """Get all settings."""
    manager = get_settings_manager()
    return manager.export_settings()


@router.get("/tabs")
async def get_tabs() -> dict[str, Any]:
    """Get available settings tabs."""
    return {
        "tabs": [
            {"id": "general", "name": "General", "icon": "settings"},
            {"id": "voice", "name": "Voice", "icon": "mic"},
            {"id": "automation", "name": "Automation", "icon": "zap"},
            {"id": "hotkeys", "name": "Hotkeys", "icon": "keyboard"},
            {"id": "ai_ml", "name": "AI/ML", "icon": "brain"},
            {"id": "workflows", "name": "Workflows", "icon": "git-branch"},
            {"id": "advanced", "name": "Advanced", "icon": "sliders"},
        ]
    }


@router.get("/{tab}")
async def get_tab_settings(tab: str) -> dict[str, Any]:
    """Get settings for a specific tab."""
    try:
        settings_tab = SettingsTab(tab)
        manager = get_settings_manager()
        tab_settings = manager.get_tab(settings_tab)
        return tab_settings.model_dump()
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Tab not found: {tab}")


@router.put("/{tab}")
async def update_tab_settings(
    tab: str, request: UpdateSettingsRequest
) -> dict[str, Any]:
    """Update settings for a specific tab."""
    try:
        settings_tab = SettingsTab(tab)
        manager = get_settings_manager()
        manager.update(settings_tab, **request.updates)

        return {
            "success": True,
            "tab": tab,
            "updated": list(request.updates.keys()),
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Tab not found: {tab}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{tab}/toggle")
async def toggle_feature(tab: str, request: ToggleFeatureRequest) -> dict[str, Any]:
    """Toggle a boolean feature."""
    try:
        settings_tab = SettingsTab(tab)
        manager = get_settings_manager()
        new_value = manager.toggle(settings_tab, request.feature)

        return {
            "success": True,
            "tab": tab,
            "feature": request.feature,
            "enabled": new_value,
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Tab not found: {tab}")


@router.get("/toggles/all")
async def get_all_toggles() -> dict[str, Any]:
    """Get all feature toggles."""
    manager = get_settings_manager()
    return manager.get_feature_toggles()


@router.post("/reset")
async def reset_settings(tab: str | None = None) -> dict[str, Any]:
    """Reset settings to defaults."""
    manager = get_settings_manager()

    if tab:
        try:
            settings_tab = SettingsTab(tab)
            manager.reset_to_defaults(settings_tab)
            return {"success": True, "reset": tab}
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Tab not found: {tab}")
    else:
        manager.reset_to_defaults()
        return {"success": True, "reset": "all"}


@router.post("/export")
async def export_settings() -> dict[str, Any]:
    """Export all settings."""
    manager = get_settings_manager()
    return {
        "success": True,
        "settings": manager.export_settings(),
    }


@router.post("/import")
async def import_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Import settings."""
    manager = get_settings_manager()
    manager.import_settings(settings)
    return {"success": True, "imported": True}


# ============================================
# Hotkey Endpoints
# ============================================


@router.get("/hotkeys/bindings")
async def get_hotkey_bindings() -> dict[str, Any]:
    """Get all hotkey bindings."""
    manager = get_hotkey_manager()
    return {"bindings": manager.get_bindings()}


@router.put("/hotkeys/{action}")
async def update_hotkey(action: str, request: UpdateHotkeyRequest) -> dict[str, Any]:
    """Update a hotkey binding."""
    try:
        hotkey_action = HotkeyAction(action)
        manager = get_hotkey_manager()
        manager.set_keys(hotkey_action, request.keys)

        return {
            "success": True,
            "action": action,
            "keys": request.keys,
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Action not found: {action}")


@router.post("/hotkeys/{action}/enable")
async def enable_hotkey(action: str) -> dict[str, Any]:
    """Enable a hotkey."""
    try:
        hotkey_action = HotkeyAction(action)
        manager = get_hotkey_manager()
        manager.enable(hotkey_action)
        return {"success": True, "action": action, "enabled": True}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Action not found: {action}")


@router.post("/hotkeys/{action}/disable")
async def disable_hotkey(action: str) -> dict[str, Any]:
    """Disable a hotkey."""
    try:
        hotkey_action = HotkeyAction(action)
        manager = get_hotkey_manager()
        manager.disable(hotkey_action)
        return {"success": True, "action": action, "enabled": False}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Action not found: {action}")


# ============================================
# Voice Settings Shortcuts
# ============================================


@router.get("/voice/quick")
async def get_voice_quick_settings() -> dict[str, Any]:
    """Get quick voice settings."""
    manager = get_settings_manager()
    voice = manager.settings.voice

    return {
        "mode": voice.mode.value,
        "pause_detection": voice.pause_detection,
        "auto_speak_responses": voice.auto_speak_responses,
        "hotkey": voice.hotkey,
        "voice_id": voice.voice_id,
        "stream_audio": voice.stream_audio,
    }


@router.post("/voice/toggle-pause")
async def toggle_voice_pause() -> dict[str, Any]:
    """Toggle voice pause detection."""
    manager = get_settings_manager()
    new_value = manager.toggle(SettingsTab.VOICE, "pause_detection")
    return {"pause_detection": new_value}


@router.post("/voice/toggle-auto-speak")
async def toggle_auto_speak() -> dict[str, Any]:
    """Toggle auto-speak responses."""
    manager = get_settings_manager()
    new_value = manager.toggle(SettingsTab.VOICE, "auto_speak_responses")
    return {"auto_speak_responses": new_value}


# ============================================
# Automation Settings Shortcuts
# ============================================


@router.get("/automation/quick")
async def get_automation_quick_settings() -> dict[str, Any]:
    """Get quick automation settings."""
    manager = get_settings_manager()
    auto = manager.settings.automation

    return {
        "auto_continue_mode": auto.auto_continue_mode.value,
        "auto_fix_errors": auto.auto_fix_errors,
        "auto_retry_failed": auto.auto_retry_failed,
        "auto_run_workflows": auto.auto_run_workflows,
        "require_confirmation": auto.require_confirmation,
    }


@router.post("/automation/toggle-auto-continue")
async def toggle_auto_continue() -> dict[str, Any]:
    """Toggle auto-continue."""
    manager = get_settings_manager()
    # Cycle through modes
    current = manager.settings.automation.auto_continue_mode
    from src.core.settings_manager import AutoContinueMode

    modes = list(AutoContinueMode)
    current_idx = modes.index(current)
    next_mode = modes[(current_idx + 1) % len(modes)]

    manager.update(SettingsTab.AUTOMATION, auto_continue_mode=next_mode)
    return {"auto_continue_mode": next_mode.value}
