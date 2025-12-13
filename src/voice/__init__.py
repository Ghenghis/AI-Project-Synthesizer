"""
AI Project Synthesizer - Voice Module

Voice AI integration including:
- ElevenLabs TTS and real-time voice
- Voice selection and management
- Auto-playback for LM Studio (tagged)
- Voice manager for unified control
"""

from src.voice.elevenlabs_client import (
    PREMADE_VOICES,
    ElevenLabsClient,
    Voice,
    VoiceSettings,
    create_elevenlabs_client,
)
from src.voice.manager import (
    AudioFormat,
    VoiceManager,
    VoiceProfile,
    VoiceProvider,
    get_voice_manager,
)
from src.voice.player import (
    PlaybackResult,
    VoicePlayer,
    get_voice_player,
    play_audio,
)

__all__ = [
    # ElevenLabs
    "ElevenLabsClient",
    "Voice",
    "VoiceSettings",
    "PREMADE_VOICES",
    "create_elevenlabs_client",
    # Player (LM Studio integration)
    "VoicePlayer",
    "PlaybackResult",
    "get_voice_player",
    "play_audio",
    # Voice Manager
    "VoiceManager",
    "VoiceProfile",
    "VoiceProvider",
    "AudioFormat",
    "get_voice_manager",
]
