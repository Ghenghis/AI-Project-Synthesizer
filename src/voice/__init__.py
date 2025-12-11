"""
AI Project Synthesizer - Voice Module

Voice AI integration including:
- ElevenLabs TTS and real-time voice
- Voice selection and management
- Auto-playback for LM Studio (tagged)
- Voice manager for unified control
"""

from src.voice.elevenlabs_client import (
    ElevenLabsClient,
    Voice,
    VoiceSettings,
    PREMADE_VOICES,
    create_elevenlabs_client,
)
from src.voice.player import (
    VoicePlayer,
    PlaybackResult,
    get_voice_player,
    play_audio,
)
from src.voice.manager import (
    VoiceManager,
    VoiceProfile,
    VoiceProvider,
    AudioFormat,
    get_voice_manager,
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
