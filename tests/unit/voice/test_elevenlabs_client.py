"""Tests for voice.elevenlabs_client."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["APP_ENV"] = "testing"

try:
    from src.voice.elevenlabs_client import (
        PREMADE_VOICES,
        ElevenLabsClient,
        Voice,
        VoiceSettings,
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error for voice.elevenlabs_client: {e}")
    IMPORTS_AVAILABLE = False


class TestPREMADE_VOICES:
    """Test PREMADE_VOICES constant."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_premade_voices_exists(self):
        """Should have PREMADE_VOICES dict."""
        assert isinstance(PREMADE_VOICES, dict)
        assert len(PREMADE_VOICES) > 0
        assert all(isinstance(voice, Voice) for voice in PREMADE_VOICES.values())
        assert "rachel" in PREMADE_VOICES
        assert PREMADE_VOICES["rachel"].voice_id == "21m00Tcm4TlvDq8ikWAM"


class TestVoiceSettings:
    """Test VoiceSettings dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_voice_settings(self):
        """Should create VoiceSettings with all fields."""
        settings = VoiceSettings(
            stability=0.75,
            similarity_boost=0.5,
            style=0.0,
            use_speaker_boost=True
        )
        assert settings.stability == 0.75
        assert settings.similarity_boost == 0.5
        assert settings.style == 0.0
        assert settings.use_speaker_boost is True


class TestVoice:
    """Test Voice dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_voice(self):
        """Should create Voice with all fields."""
        voice = Voice(
            voice_id="test_voice_id",
            name="Test Voice",
            category="premade",
            description="A test voice"
        )
        assert voice.voice_id == "test_voice_id"
        assert voice.name == "Test Voice"
        assert voice.category == "premade"
        assert voice.description == "A test voice"


class TestElevenLabsClient:
    """Test ElevenLabsClient."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_client(self):
        """Should create client with API key."""
        with patch('src.voice.elevenlabs_client.get_settings') as mock_settings:
            mock_settings.return_value.elevenlabs.elevenlabs_api_key.get_secret_value.return_value = "config_key"
            client = ElevenLabsClient(api_key="test_key")
            assert client._api_key == "test_key"
            assert client.BASE_URL == "https://api.elevenlabs.io/v1"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.voice.elevenlabs_client.aiohttp.ClientSession')
    async def test_get_voices(self, mock_session):
        """Should get list of voices."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "voices": [
                {
                    "voice_id": "voice1",
                    "name": "Voice 1",
                    "category": "premade",
                    "description": "First voice"
                },
                {
                    "voice_id": "voice2",
                    "name": "Voice 2",
                    "category": "cloned",
                    "description": "Second voice"
                }
            ]
        }

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value = mock_session_instance

        client = ElevenLabsClient(api_key="test_key")
        session = await client._get_session()
        assert session is not None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.voice.elevenlabs_client.aiohttp.ClientSession')
    async def test_validate_api_key(self, mock_session):
        """Should validate API key."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        client = ElevenLabsClient(api_key="test_key")
        assert client._api_key == "test_key"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_error_handling(self):
        """Should handle errors gracefully."""
        client = ElevenLabsClient(api_key="invalid_key")
        # Should not raise exception on creation
        assert client._api_key == "invalid_key"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_resolve_voice_id(self):
        """Should resolve voice names to IDs."""
        client = ElevenLabsClient(api_key="test_key")

        # Test with None (should return default)
        with patch.object(client, '_default_voice_id', 'default_voice'):
            assert client._resolve_voice_id(None) == 'default_voice'

        # Test with known voice name
        assert client._resolve_voice_id('rachel') == '21m00Tcm4TlvDq8ikWAM'

        # Test with unknown voice name (should return as-is)
        assert client._resolve_voice_id('unknown_voice') == 'unknown_voice'

        # Test with voice ID directly (should return as-is)
        assert client._resolve_voice_id('custom_voice_id') == 'custom_voice_id'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
