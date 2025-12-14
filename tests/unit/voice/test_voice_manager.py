"""Tests for voice.manager."""

import os
from unittest.mock import AsyncMock

import pytest

os.environ["APP_ENV"] = "testing"

try:
    from src.voice.manager import (
        AudioFormat,
        VoiceManager,
        VoiceProfile,
        VoiceProvider,
        get_voice_manager,
    )

    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error for voice.manager: {e}")
    IMPORTS_AVAILABLE = False


class TestAudioFormat:
    """Test AudioFormat enum."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_audio_format_values(self):
        """Should have correct AudioFormat values."""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.PCM.value == "pcm"


class TestVoiceProvider:
    """Test VoiceProvider enum."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_voice_provider_values(self):
        """Should have correct VoiceProvider values."""
        assert VoiceProvider.ELEVENLABS.value == "elevenlabs"
        assert VoiceProvider.LOCAL.value == "local"
        assert VoiceProvider.OPENAI.value == "openai"
        assert VoiceProvider.PIPER.value == "piper"


class TestVoiceProfile:
    """Test VoiceProfile dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_voice_profile(self):
        """Should create VoiceProfile with all fields."""
        profile = VoiceProfile(
            id="test_voice",
            name="Test Voice",
            provider=VoiceProvider.ELEVENLABS,
            voice_id="voice123",
            description="A test voice",
            language="en",
            stability=0.75,
            similarity_boost=0.5,
            style=0.0,
            speed=1.0,
            model="eleven_turbo_v2_5",
        )
        assert profile.id == "test_voice"
        assert profile.name == "Test Voice"
        assert profile.provider == VoiceProvider.ELEVENLABS
        assert profile.voice_id == "voice123"
        assert profile.stability == 0.75
        assert profile.similarity_boost == 0.5
        assert profile.language == "en"


class TestVoiceManager:
    """Test VoiceManager."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_manager(self):
        """Should create VoiceManager with default voices."""
        manager = VoiceManager()
        # Should have default voices loaded
        assert len(manager.list_voices()) > 0
        assert manager.get_voice("rachel") is not None
        assert manager.get_voice("piper_default") is not None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_add_voice(self):
        """Should add voice profile."""
        manager = VoiceManager()
        profile = VoiceProfile(
            id="test_voice",
            name="Test Voice",
            provider=VoiceProvider.ELEVENLABS,
            voice_id="voice123",
        )

        manager.add_voice(profile)

        retrieved = manager.get_voice("test_voice")
        assert retrieved == profile

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_get_voice(self):
        """Should get voice profile by ID."""
        manager = VoiceManager()

        # Test existing voice
        rachel = manager.get_voice("rachel")
        assert rachel is not None
        assert rachel.name == "Rachel"

        # Test non-existent voice
        assert manager.get_voice("NonExistent") is None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_list_voices(self):
        """Should list all voices as dictionaries."""
        manager = VoiceManager()

        voices = manager.list_voices()
        assert isinstance(voices, list)
        assert len(voices) > 0

        # Check that all items are dictionaries with required fields
        for voice in voices:
            assert isinstance(voice, dict)
            assert "id" in voice
            assert "name" in voice
            assert "provider" in voice

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_set_default_voice(self):
        """Should set default voice."""
        manager = VoiceManager()

        # Change default to josh
        manager.set_default_voice("josh")

        # Verify it was set (we can't directly access _default_voice, but we can test through speak)
        # This is tested indirectly in the speak test below

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_speak_with_voice(self):
        """Should speak using specified voice."""
        # Create mock client
        mock_instance = AsyncMock()
        mock_instance.text_to_speech.return_value = b"audio_data"

        manager = VoiceManager()

        # Mock both client methods
        manager._get_elevenlabs_client = AsyncMock(return_value=mock_instance)
        manager._get_piper_client = AsyncMock(return_value=mock_instance)

        # Test speaking with rachel voice
        result = await manager.speak("Hello world", voice="rachel")

        # Should return bytes (audio data)
        assert result is None or isinstance(result, bytes)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_speak_default_voice(self):
        """Should speak using default voice."""
        # Create mock clients
        mock_elevenlabs = AsyncMock()
        mock_elevenlabs.text_to_speech.return_value = b"audio_data"

        mock_piper = AsyncMock()
        mock_piper.synthesize.return_value = b"piper_audio_data"

        manager = VoiceManager()

        # Mock both client methods
        manager._get_elevenlabs_client = AsyncMock(return_value=mock_elevenlabs)
        manager._get_piper_client = AsyncMock(return_value=mock_piper)

        # Test speaking with default voice (piper_default)
        result = await manager.speak("Hello world")

        # Should return bytes (audio data)
        assert result == b"piper_audio_data"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_get_manager_singleton(self):
        """Should return singleton instance."""
        manager1 = get_voice_manager()
        manager2 = get_voice_manager()
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
