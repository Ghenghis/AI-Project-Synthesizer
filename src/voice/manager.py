"""
AI Project Synthesizer - Voice Management System

Comprehensive voice management for:
- Voice selection and configuration
- Audio playback control
- Speech recognition
- Voice profiles
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.security import get_secure_logger
from src.voice.elevenlabs_client import VoiceSettings

secure_logger = get_secure_logger(__name__)


class VoiceProvider(str, Enum):
    """Available voice providers."""
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    LOCAL = "local"
    PIPER = "piper"


class AudioFormat(str, Enum):
    """Audio output formats."""
    MP3 = "mp3"
    WAV = "wav"
    PCM = "pcm"


@dataclass
class VoiceProfile:
    """Voice profile configuration."""
    id: str
    name: str
    provider: VoiceProvider
    voice_id: str
    description: str = ""
    language: str = "en"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    speed: float = 1.0
    model: str = "eleven_turbo_v2_5"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "voice_id": self.voice_id,
            "description": self.description,
            "language": self.language,
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "speed": self.speed,
            "model": self.model,
        }


# Pre-defined voice profiles
DEFAULT_VOICES: dict[str, VoiceProfile] = {
    # ElevenLabs voices (existing)
    "rachel": VoiceProfile(
        id="rachel",
        name="Rachel",
        provider=VoiceProvider.ELEVENLABS,
        voice_id="21m00Tcm4TlvDq8ikWAM",
        description="Calm, professional female voice",
        stability=0.5,
        similarity_boost=0.75,
    ),
    "domi": VoiceProfile(
        id="domi",
        name="Domi",
        provider=VoiceProvider.ELEVENLABS,
        voice_id="AZnzlk1XvdvUeBnXmlld",
        description="Strong, confident female voice",
        stability=0.5,
        similarity_boost=0.75,
    ),
    "bella": VoiceProfile(
        id="bella",
        name="Bella",
        provider=VoiceProvider.ELEVENLABS,
        voice_id="EXAVITQu4vr4xnSDxMaL",
        description="Soft, friendly female voice",
        stability=0.5,
        similarity_boost=0.75,
    ),
    "josh": VoiceProfile(
        id="josh",
        name="Josh",
        provider=VoiceProvider.ELEVENLABS,
        voice_id="TxGEqnHWrfWFTfGW9XjX",
        description="Deep, authoritative male voice",
        stability=0.5,
        similarity_boost=0.75,
    ),

    # Piper TTS voices (new local voices)
    "piper_default": VoiceProfile(
        id="piper_default",
        name="Piper Default",
        provider=VoiceProvider.PIPER,
        voice_id="en_US-lessac-medium",
        description="Local American English male voice",
        speed=1.0,
        model="piper",
    ),
    "piper_female": VoiceProfile(
        id="piper_female",
        name="Piper Female",
        provider=VoiceProvider.PIPER,
        voice_id="en_US-lessac-medium",  # Would be female model
        description="Local American English female voice",
        speed=1.0,
        model="piper",
    ),
    "piper_british": VoiceProfile(
        id="piper_british",
        name="Piper British",
        provider=VoiceProvider.PIPER,
        voice_id="en_GB-lessac-medium",
        description="Local British English male voice",
        speed=1.0,
        model="piper",
    ),
    "rachel_local": VoiceProfile(
        id="rachel_local",
        name="Rachel (Local)",
        provider=VoiceProvider.PIPER,
        voice_id="rachel_cloned",
        description="Local clone of Rachel voice from extracted samples",
        speed=1.0,
        model="piper",
    ),
    "adam": VoiceProfile(
        id="adam",
        name="Adam",
        provider=VoiceProvider.ELEVENLABS,
        voice_id="pNInz6obpgDQGcFmaJgB",
        description="Warm, natural male voice",
        stability=0.5,
        similarity_boost=0.75,
    ),
}


@dataclass
class AudioSession:
    """Active audio session."""
    id: str
    profile: VoiceProfile
    started_at: datetime = field(default_factory=datetime.now)
    is_playing: bool = False
    volume: float = 1.0
    muted: bool = False


class VoiceManager:
    """
    Central voice management system.

    Features:
    - Voice profile management
    - Text-to-speech generation
    - Audio playback control
    - Session management

    Usage:
        manager = VoiceManager()

        # Speak with default voice
        await manager.speak("Hello, world!")

        # Speak with specific voice
        await manager.speak("Hello!", voice="josh")

        # Get available voices
        voices = manager.list_voices()
    """

    def __init__(self):
        self._profiles = dict(DEFAULT_VOICES)
        self._current_session: AudioSession | None = None
        self._default_voice = "piper_default"  # Switch to local by default
        self._elevenlabs_client = None
        self._piper_client = None

    async def _get_elevenlabs_client(self):
        """Get ElevenLabs client."""
        if self._elevenlabs_client is None:
            from src.voice.elevenlabs_client import ElevenLabsClient
            self._elevenlabs_client = ElevenLabsClient()
        return self._elevenlabs_client

    async def _get_piper_client(self):
        """Get Piper TTS client."""
        if self._piper_client is None:
            from src.voice.tts.piper_client import create_piper_client
            self._piper_client = await create_piper_client()
            if self._piper_client is None:
                raise RuntimeError("Failed to initialize Piper TTS client")
        return self._piper_client

    def list_voices(self) -> list[dict[str, Any]]:
        """List available voice profiles."""
        return [p.to_dict() for p in self._profiles.values()]

    def get_voice(self, voice_id: str) -> VoiceProfile | None:
        """Get a voice profile by ID."""
        return self._profiles.get(voice_id)

    def add_voice(self, profile: VoiceProfile):
        """Add a custom voice profile."""
        self._profiles[profile.id] = profile

    def set_default_voice(self, voice_id: str):
        """Set the default voice."""
        if voice_id in self._profiles:
            self._default_voice = voice_id

    async def speak(
        self,
        text: str,
        voice: str | None = None,
        stream: bool = False,
    ) -> Path | None:
        """
        Generate and play speech.

        Args:
            text: Text to speak
            voice: Voice profile ID (uses default if not specified)
            stream: Whether to stream audio

        Returns:
            Path to audio file if not streaming
        """
        voice_id = voice or self._default_voice
        profile = self._profiles.get(voice_id)

        if not profile:
            secure_logger.warning(f"Voice not found: {voice_id}, using default")
            profile = self._profiles[self._default_voice]

        try:
            # Route to appropriate provider based on voice profile
            if profile.provider == VoiceProvider.ELEVENLABS:
                client = await self._get_elevenlabs_client()

                if stream:
                    await client.stream_speech(
                        text,
                        voice=profile.voice_id,
                        model=profile.model,
                        settings=VoiceSettings(
                            stability=profile.stability,
                            similarity_boost=profile.similarity_boost,
                            style=profile.style,
                            use_speaker_boost=True,
                        ),
                    )
                else:
                    audio_data = await client.text_to_speech(
                        text,
                        voice=profile.voice_id,
                        model=profile.model,
                        settings=VoiceSettings(
                            stability=profile.stability,
                            similarity_boost=profile.similarity_boost,
                            style=profile.style,
                            use_speaker_boost=True,
                        ),
                    )

            elif profile.provider == VoiceProvider.PIPER:
                client = await self._get_piper_client()

                # Piper doesn't support streaming in the same way
                if stream:
                    secure_logger.warning("Streaming not fully supported with Piper TTS")

                audio_data = await client.synthesize(
                    text,
                    voice=profile.voice_id,
                    speed=profile.speed,
                )

            else:
                raise RuntimeError(f"Unsupported voice provider: {profile.provider}")

            if not stream:
                return audio_data

        except Exception as e:
            secure_logger.error(f"Speech generation failed: {e}")
            raise

    async def speak_fast(self, text: str, voice: str | None = None):
        """Quick speech with streaming for low latency."""
        return await self.speak(text, voice, stream=True)

    def get_session(self) -> AudioSession | None:
        """Get current audio session."""
        return self._current_session

    def start_session(self, voice: str | None = None) -> AudioSession:
        """Start a new audio session."""
        voice_id = voice or self._default_voice
        profile = self._profiles.get(voice_id, self._profiles[self._default_voice])

        self._current_session = AudioSession(
            id=f"session_{datetime.now().timestamp()}",
            profile=profile,
        )
        return self._current_session

    def end_session(self):
        """End current audio session."""
        self._current_session = None


# Global voice manager instance
_voice_manager: VoiceManager | None = None


def get_voice_manager() -> VoiceManager:
    """Get or create voice manager."""
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceManager()
    return _voice_manager
