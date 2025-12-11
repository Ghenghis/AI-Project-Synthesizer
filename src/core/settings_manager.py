"""
AI Project Synthesizer - Settings Manager

Comprehensive settings system with:
- Tabbed configuration panels
- Feature toggles
- Hotkey management
- Voice settings (no pause limits)
- Auto-continue options
- Automation controls
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from pydantic import BaseModel, Field


class SettingsTab(str, Enum):
    """Settings panel tabs."""
    GENERAL = "general"
    VOICE = "voice"
    AUTOMATION = "automation"
    HOTKEYS = "hotkeys"
    AI_ML = "ai_ml"
    WORKFLOWS = "workflows"
    ADVANCED = "advanced"


class VoiceMode(str, Enum):
    """Voice interaction modes."""
    PUSH_TO_TALK = "push_to_talk"
    CONTINUOUS = "continuous"
    AUTO_DETECT = "auto_detect"
    HOTKEY_TOGGLE = "hotkey_toggle"


class AutoContinueMode(str, Enum):
    """Auto-continue behavior."""
    DISABLED = "disabled"
    ON_COMPLETION = "on_completion"
    ON_SILENCE = "on_silence"
    CONTINUOUS = "continuous"


# ============================================
# Settings Models
# ============================================

class GeneralSettings(BaseModel):
    """General application settings."""
    theme: str = Field(default="dark", description="UI theme")
    language: str = Field(default="en", description="Interface language")
    auto_save: bool = Field(default=True, description="Auto-save settings")
    notifications_enabled: bool = Field(default=True, description="Show notifications")
    startup_check_updates: bool = Field(default=True, description="Check for updates on startup")
    log_level: str = Field(default="INFO", description="Logging level")
    output_directory: str = Field(default="G:/", description="Default output directory")
    max_concurrent_tasks: int = Field(default=5, description="Max parallel tasks")


class VoiceSettings(BaseModel):
    """Voice and speech settings."""
    # Voice mode
    mode: VoiceMode = Field(default=VoiceMode.HOTKEY_TOGGLE, description="Voice activation mode")

    # No pause limits
    pause_detection: bool = Field(default=False, description="Enable pause detection")
    pause_threshold_ms: int = Field(default=0, description="Pause threshold (0 = disabled)")
    max_recording_duration: int = Field(default=0, description="Max recording (0 = unlimited)")

    # Voice provider
    provider: str = Field(default="elevenlabs", description="TTS provider")
    voice_id: str = Field(default="rachel", description="Default voice")

    # Speech settings
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    stability: float = Field(default=0.5, description="Voice stability")
    similarity_boost: float = Field(default=0.75, description="Voice similarity")

    # Response settings
    auto_speak_responses: bool = Field(default=True, description="Auto-speak AI responses")
    speak_actions: bool = Field(default=True, description="Announce actions")
    speak_errors: bool = Field(default=True, description="Speak error messages")

    # Streaming
    stream_audio: bool = Field(default=True, description="Stream audio for low latency")

    # Hotkey
    hotkey: str = Field(default="ctrl+shift+v", description="Voice activation hotkey")
    hotkey_hold_mode: bool = Field(default=False, description="Hold hotkey to record")


class AutomationSettings(BaseModel):
    """Automation and auto-continue settings."""
    # Auto-continue
    auto_continue_mode: AutoContinueMode = Field(
        default=AutoContinueMode.ON_COMPLETION,
        description="Auto-continue behavior"
    )
    auto_continue_delay_ms: int = Field(default=500, description="Delay before auto-continue")

    # Auto-actions
    auto_fix_errors: bool = Field(default=True, description="Auto-fix detected errors")
    auto_retry_failed: bool = Field(default=True, description="Auto-retry failed operations")
    max_retries: int = Field(default=3, description="Max retry attempts")

    # Workflow automation
    auto_run_workflows: bool = Field(default=True, description="Auto-run scheduled workflows")
    auto_health_check: bool = Field(default=True, description="Auto health monitoring")
    health_check_interval_s: int = Field(default=300, description="Health check interval")

    # Response automation
    auto_execute_suggestions: bool = Field(default=False, description="Auto-execute AI suggestions")
    require_confirmation: bool = Field(default=True, description="Require confirmation for actions")

    # Background tasks
    background_research: bool = Field(default=True, description="Enable background research")
    background_indexing: bool = Field(default=True, description="Enable background indexing")


class HotkeySettings(BaseModel):
    """Hotkey configuration."""
    # Voice
    voice_toggle: str = Field(default="ctrl+shift+v", description="Toggle voice")
    voice_push_to_talk: str = Field(default="ctrl+space", description="Push to talk")
    voice_cancel: str = Field(default="escape", description="Cancel voice input")

    # Actions
    quick_search: str = Field(default="ctrl+shift+s", description="Quick search")
    quick_assemble: str = Field(default="ctrl+shift+a", description="Quick assemble")
    quick_chat: str = Field(default="ctrl+shift+c", description="Quick chat")

    # Navigation
    open_settings: str = Field(default="ctrl+,", description="Open settings")
    open_dashboard: str = Field(default="ctrl+shift+d", description="Open dashboard")

    # Automation
    pause_automation: str = Field(default="ctrl+shift+p", description="Pause automation")
    resume_automation: str = Field(default="ctrl+shift+r", description="Resume automation")

    # System
    emergency_stop: str = Field(default="ctrl+shift+escape", description="Emergency stop all")


class AIMLSettings(BaseModel):
    """AI/ML configuration."""
    # Provider priority
    primary_provider: str = Field(default="lmstudio", description="Primary LLM provider")
    fallback_provider: str = Field(default="ollama", description="Fallback provider")
    cloud_fallback: bool = Field(default=False, description="Use cloud as last resort")

    # Model settings
    default_model: str = Field(default="", description="Default model (empty = auto)")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: int = Field(default=4096, description="Max tokens per response")

    # Context
    context_window: int = Field(default=8192, description="Context window size")
    include_system_context: bool = Field(default=True, description="Include system context")

    # Features
    enable_function_calling: bool = Field(default=True, description="Enable function calling")
    enable_code_execution: bool = Field(default=False, description="Enable code execution")
    enable_web_search: bool = Field(default=True, description="Enable web search")

    # Agents
    enable_research_agent: bool = Field(default=True, description="Enable research agent")
    enable_synthesis_agent: bool = Field(default=True, description="Enable synthesis agent")
    enable_voice_agent: bool = Field(default=True, description="Enable voice agent")
    enable_automation_agent: bool = Field(default=True, description="Enable automation agent")

    # Learning
    learn_from_feedback: bool = Field(default=True, description="Learn from user feedback")
    save_conversation_history: bool = Field(default=True, description="Save conversations")


class WorkflowSettings(BaseModel):
    """Workflow configuration."""
    # n8n
    n8n_enabled: bool = Field(default=True, description="Enable n8n integration")
    n8n_url: str = Field(default="http://localhost:5678", description="n8n URL")
    n8n_auto_sync: bool = Field(default=True, description="Auto-sync workflows")

    # Scheduling
    enable_scheduled_workflows: bool = Field(default=True, description="Enable scheduled workflows")
    research_schedule: str = Field(default="0 */6 * * *", description="Research cron schedule")
    health_schedule: str = Field(default="*/5 * * * *", description="Health check cron")

    # Execution
    parallel_workflows: int = Field(default=3, description="Max parallel workflows")
    workflow_timeout_s: int = Field(default=300, description="Workflow timeout")

    # Metrics
    collect_metrics: bool = Field(default=True, description="Collect workflow metrics")
    metrics_retention_days: int = Field(default=30, description="Metrics retention")


class AdvancedSettings(BaseModel):
    """Advanced settings."""
    # Debug
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    verbose_logging: bool = Field(default=False, description="Verbose logging")

    # Performance
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL")

    # Security
    require_api_key_confirmation: bool = Field(default=True, description="Confirm API key usage")
    sanitize_outputs: bool = Field(default=True, description="Sanitize sensitive data")

    # Experimental
    experimental_features: bool = Field(default=False, description="Enable experimental features")
    beta_agents: bool = Field(default=False, description="Enable beta agents")


class AllSettings(BaseModel):
    """Complete settings configuration."""
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    automation: AutomationSettings = Field(default_factory=AutomationSettings)
    hotkeys: HotkeySettings = Field(default_factory=HotkeySettings)
    ai_ml: AIMLSettings = Field(default_factory=AIMLSettings)
    workflows: WorkflowSettings = Field(default_factory=WorkflowSettings)
    advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)


# ============================================
# Settings Manager
# ============================================

class SettingsManager:
    """
    Central settings management system.
    
    Features:
    - Load/save settings to file
    - Settings validation
    - Change notifications
    - Tab-based organization
    - Feature toggles
    """

    def __init__(self, settings_path: Optional[Path] = None):
        self._settings_path = settings_path or Path("config/settings.json")
        self._settings = AllSettings()
        self._listeners: Dict[str, List[Callable]] = {}
        self._loaded = False

    def load(self) -> AllSettings:
        """Load settings from file."""
        if self._settings_path.exists():
            try:
                data = json.loads(self._settings_path.read_text())
                self._settings = AllSettings(**data)
                self._loaded = True
            except Exception as e:
                print(f"Error loading settings: {e}, using defaults")
                self._settings = AllSettings()
        return self._settings

    def save(self):
        """Save settings to file."""
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(
            self._settings.model_dump_json(indent=2)
        )

    @property
    def settings(self) -> AllSettings:
        """Get current settings."""
        if not self._loaded:
            self.load()
        return self._settings

    def get_tab(self, tab: SettingsTab) -> BaseModel:
        """Get settings for a specific tab."""
        tab_map = {
            SettingsTab.GENERAL: self._settings.general,
            SettingsTab.VOICE: self._settings.voice,
            SettingsTab.AUTOMATION: self._settings.automation,
            SettingsTab.HOTKEYS: self._settings.hotkeys,
            SettingsTab.AI_ML: self._settings.ai_ml,
            SettingsTab.WORKFLOWS: self._settings.workflows,
            SettingsTab.ADVANCED: self._settings.advanced,
        }
        return tab_map[tab]

    def update(self, tab: SettingsTab, **kwargs):
        """Update settings for a tab."""
        current = self.get_tab(tab)
        for key, value in kwargs.items():
            if hasattr(current, key):
                setattr(current, key, value)
                self._notify(f"{tab.value}.{key}", value)

        if self._settings.general.auto_save:
            self.save()

    def toggle(self, tab: SettingsTab, feature: str) -> bool:
        """Toggle a boolean feature."""
        current = self.get_tab(tab)
        if hasattr(current, feature):
            current_value = getattr(current, feature)
            if isinstance(current_value, bool):
                new_value = not current_value
                setattr(current, feature, new_value)
                self._notify(f"{tab.value}.{feature}", new_value)

                if self._settings.general.auto_save:
                    self.save()

                return new_value
        return False

    def on_change(self, key: str, callback: Callable):
        """Register a change listener."""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def _notify(self, key: str, value: Any):
        """Notify listeners of a change."""
        for listener in self._listeners.get(key, []):
            try:
                listener(value)
            except Exception:
                pass

        # Also notify wildcard listeners
        for listener in self._listeners.get("*", []):
            try:
                listener(key, value)
            except Exception:
                pass

    def get_feature_toggles(self) -> Dict[str, Dict[str, bool]]:
        """Get all feature toggles organized by tab."""
        toggles = {}

        for tab in SettingsTab:
            tab_settings = self.get_tab(tab)
            tab_toggles = {}

            for field_name, field_value in tab_settings:
                if isinstance(field_value, bool):
                    tab_toggles[field_name] = field_value

            if tab_toggles:
                toggles[tab.value] = tab_toggles

        return toggles

    def export_settings(self) -> Dict[str, Any]:
        """Export all settings as dictionary."""
        return self._settings.model_dump()

    def import_settings(self, data: Dict[str, Any]):
        """Import settings from dictionary."""
        self._settings = AllSettings(**data)
        self.save()

    def reset_to_defaults(self, tab: Optional[SettingsTab] = None):
        """Reset settings to defaults."""
        if tab:
            defaults = {
                SettingsTab.GENERAL: GeneralSettings(),
                SettingsTab.VOICE: VoiceSettings(),
                SettingsTab.AUTOMATION: AutomationSettings(),
                SettingsTab.HOTKEYS: HotkeySettings(),
                SettingsTab.AI_ML: AIMLSettings(),
                SettingsTab.WORKFLOWS: WorkflowSettings(),
                SettingsTab.ADVANCED: AdvancedSettings(),
            }
            setattr(self._settings, tab.value, defaults[tab])
        else:
            self._settings = AllSettings()

        self.save()


# Global settings manager
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get or create settings manager."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
