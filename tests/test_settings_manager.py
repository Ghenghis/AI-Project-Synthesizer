"""
Tests for src/core/settings_manager.py - Settings System

Full coverage tests for:
- All settings models
- SettingsManager
- Feature toggles
- Import/export
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.core.settings_manager import (
    SettingsManager,
    SettingsTab,
    AllSettings,
    GeneralSettings,
    VoiceSettings,
    AutomationSettings,
    HotkeySettings,
    AIMLSettings,
    WorkflowSettings,
    AdvancedSettings,
    VoiceMode,
    AutoContinueMode,
    get_settings_manager,
)


class TestSettingsTab:
    """Tests for SettingsTab enum."""
    
    def test_all_tabs(self):
        tabs = [
            SettingsTab.GENERAL,
            SettingsTab.VOICE,
            SettingsTab.AUTOMATION,
            SettingsTab.HOTKEYS,
            SettingsTab.AI_ML,
            SettingsTab.WORKFLOWS,
            SettingsTab.ADVANCED,
        ]
        assert len(tabs) == 7
        assert SettingsTab.GENERAL.value == "general"
        assert SettingsTab.VOICE.value == "voice"


class TestVoiceMode:
    """Tests for VoiceMode enum."""
    
    def test_all_modes(self):
        assert VoiceMode.PUSH_TO_TALK.value == "push_to_talk"
        assert VoiceMode.CONTINUOUS.value == "continuous"
        assert VoiceMode.AUTO_DETECT.value == "auto_detect"
        assert VoiceMode.HOTKEY_TOGGLE.value == "hotkey_toggle"


class TestAutoContinueMode:
    """Tests for AutoContinueMode enum."""
    
    def test_all_modes(self):
        assert AutoContinueMode.DISABLED.value == "disabled"
        assert AutoContinueMode.ON_COMPLETION.value == "on_completion"
        assert AutoContinueMode.ON_SILENCE.value == "on_silence"
        assert AutoContinueMode.CONTINUOUS.value == "continuous"


class TestGeneralSettings:
    """Tests for GeneralSettings model."""
    
    def test_defaults(self):
        settings = GeneralSettings()
        assert settings.theme == "dark"
        assert settings.language == "en"
        assert settings.auto_save is True
        assert settings.notifications_enabled is True
        assert settings.log_level == "INFO"
        assert settings.output_directory == "G:/"
        assert settings.max_concurrent_tasks == 5
    
    def test_custom_values(self):
        settings = GeneralSettings(
            theme="light",
            language="es",
            auto_save=False,
            max_concurrent_tasks=10,
        )
        assert settings.theme == "light"
        assert settings.language == "es"
        assert settings.auto_save is False
        assert settings.max_concurrent_tasks == 10


class TestVoiceSettings:
    """Tests for VoiceSettings model."""
    
    def test_defaults(self):
        settings = VoiceSettings()
        assert settings.mode == VoiceMode.HOTKEY_TOGGLE
        assert settings.pause_detection is False
        assert settings.pause_threshold_ms == 0
        assert settings.max_recording_duration == 0
        assert settings.provider == "elevenlabs"
        assert settings.voice_id == "rachel"
        assert settings.auto_speak_responses is True
        assert settings.stream_audio is True
        assert settings.hotkey == "ctrl+shift+v"
    
    def test_no_pause_limits(self):
        settings = VoiceSettings()
        # Verify no pause limits by default
        assert settings.pause_detection is False
        assert settings.pause_threshold_ms == 0
        assert settings.max_recording_duration == 0


class TestAutomationSettings:
    """Tests for AutomationSettings model."""
    
    def test_defaults(self):
        settings = AutomationSettings()
        assert settings.auto_continue_mode == AutoContinueMode.ON_COMPLETION
        assert settings.auto_continue_delay_ms == 500
        assert settings.auto_fix_errors is True
        assert settings.auto_retry_failed is True
        assert settings.max_retries == 3
        assert settings.auto_run_workflows is True
        assert settings.auto_health_check is True
        assert settings.require_confirmation is True


class TestHotkeySettings:
    """Tests for HotkeySettings model."""
    
    def test_defaults(self):
        settings = HotkeySettings()
        assert settings.voice_toggle == "ctrl+shift+v"
        assert settings.voice_push_to_talk == "ctrl+space"
        assert settings.voice_cancel == "escape"
        assert settings.quick_search == "ctrl+shift+s"
        assert settings.emergency_stop == "ctrl+shift+escape"


class TestAIMLSettings:
    """Tests for AIMLSettings model."""
    
    def test_defaults(self):
        settings = AIMLSettings()
        assert settings.primary_provider == "lmstudio"
        assert settings.fallback_provider == "ollama"
        assert settings.cloud_fallback is False
        assert settings.temperature == 0.7
        assert settings.max_tokens == 4096
        assert settings.enable_function_calling is True
        assert settings.enable_research_agent is True


class TestWorkflowSettings:
    """Tests for WorkflowSettings model."""
    
    def test_defaults(self):
        settings = WorkflowSettings()
        assert settings.n8n_enabled is True
        assert settings.n8n_url == "http://localhost:5678"
        assert settings.enable_scheduled_workflows is True
        assert settings.collect_metrics is True


class TestAdvancedSettings:
    """Tests for AdvancedSettings model."""
    
    def test_defaults(self):
        settings = AdvancedSettings()
        assert settings.debug_mode is False
        assert settings.verbose_logging is False
        assert settings.cache_enabled is True
        assert settings.experimental_features is False


class TestAllSettings:
    """Tests for AllSettings model."""
    
    def test_defaults(self):
        settings = AllSettings()
        assert isinstance(settings.general, GeneralSettings)
        assert isinstance(settings.voice, VoiceSettings)
        assert isinstance(settings.automation, AutomationSettings)
        assert isinstance(settings.hotkeys, HotkeySettings)
        assert isinstance(settings.ai_ml, AIMLSettings)
        assert isinstance(settings.workflows, WorkflowSettings)
        assert isinstance(settings.advanced, AdvancedSettings)
    
    def test_nested_access(self):
        settings = AllSettings()
        assert settings.general.theme == "dark"
        assert settings.voice.mode == VoiceMode.HOTKEY_TOGGLE
        assert settings.automation.auto_fix_errors is True


class TestSettingsManager:
    """Tests for SettingsManager class."""
    
    @pytest.fixture
    def temp_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            manager = SettingsManager(settings_path=settings_path)
            yield manager
    
    def test_create_manager(self, temp_manager):
        assert temp_manager is not None
    
    def test_load_creates_defaults(self, temp_manager):
        settings = temp_manager.load()
        assert isinstance(settings, AllSettings)
    
    def test_save_and_load(self, temp_manager):
        temp_manager.settings.general.theme = "light"
        temp_manager.save()
        
        # Create new manager with same path
        new_manager = SettingsManager(settings_path=temp_manager._settings_path)
        loaded = new_manager.load()
        
        assert loaded.general.theme == "light"
    
    def test_get_tab(self, temp_manager):
        general = temp_manager.get_tab(SettingsTab.GENERAL)
        assert isinstance(general, GeneralSettings)
        
        voice = temp_manager.get_tab(SettingsTab.VOICE)
        assert isinstance(voice, VoiceSettings)
    
    def test_update_settings(self, temp_manager):
        temp_manager.update(SettingsTab.GENERAL, theme="light", language="fr")
        
        assert temp_manager.settings.general.theme == "light"
        assert temp_manager.settings.general.language == "fr"
    
    def test_toggle_feature(self, temp_manager):
        # Toggle auto_save (default True)
        new_value = temp_manager.toggle(SettingsTab.GENERAL, "auto_save")
        assert new_value is False
        
        # Toggle back
        new_value = temp_manager.toggle(SettingsTab.GENERAL, "auto_save")
        assert new_value is True
    
    def test_toggle_nonexistent_feature(self, temp_manager):
        result = temp_manager.toggle(SettingsTab.GENERAL, "nonexistent")
        assert result is False
    
    def test_on_change_callback(self, temp_manager):
        changes = []
        
        def callback(value):
            changes.append(value)
        
        temp_manager.on_change("general.theme", callback)
        temp_manager.update(SettingsTab.GENERAL, theme="light")
        
        assert len(changes) == 1
        assert changes[0] == "light"
    
    def test_wildcard_callback(self, temp_manager):
        changes = []
        
        def callback(key, value):
            changes.append((key, value))
        
        temp_manager.on_change("*", callback)
        temp_manager.update(SettingsTab.GENERAL, theme="light")
        
        assert len(changes) == 1
        assert changes[0][0] == "general.theme"
    
    def test_get_feature_toggles(self, temp_manager):
        toggles = temp_manager.get_feature_toggles()
        
        assert "general" in toggles
        assert "auto_save" in toggles["general"]
        assert "voice" in toggles
        assert "automation" in toggles
    
    def test_export_settings(self, temp_manager):
        exported = temp_manager.export_settings()
        
        assert "general" in exported
        assert "voice" in exported
        assert exported["general"]["theme"] == "dark"
    
    def test_import_settings(self, temp_manager):
        data = {
            "general": {"theme": "light"},
            "voice": {"mode": "continuous"},
        }
        
        temp_manager.import_settings(data)
        
        assert temp_manager.settings.general.theme == "light"
    
    def test_reset_to_defaults_single_tab(self, temp_manager):
        temp_manager.settings.general.theme = "light"
        temp_manager.reset_to_defaults(SettingsTab.GENERAL)
        
        assert temp_manager.settings.general.theme == "dark"
    
    def test_reset_to_defaults_all(self, temp_manager):
        temp_manager.settings.general.theme = "light"
        temp_manager.settings.voice.mode = VoiceMode.CONTINUOUS
        
        temp_manager.reset_to_defaults()
        
        assert temp_manager.settings.general.theme == "dark"
        assert temp_manager.settings.voice.mode == VoiceMode.HOTKEY_TOGGLE


class TestGetSettingsManager:
    """Tests for get_settings_manager function."""
    
    def test_singleton(self):
        manager1 = get_settings_manager()
        manager2 = get_settings_manager()
        assert manager1 is manager2
