"""
AI Project Synthesizer - Voice Management System

Comprehensive voice management for:
- Voice selection and configuration
- Audio playback control
- Speech recognition
- Voice profiles
"""

import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from datetime import datetime

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class VoiceProvider(str, Enum):
    """Available voice providers."""
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    LOCAL = "local"


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
    
    def to_dict(self) -> Dict[str, Any]:
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
DEFAULT_VOICES: Dict[str, VoiceProfile] = {
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
        self._current_session: Optional[AudioSession] = None
        self._default_voice = "rachel"
        self._client = None
    
    async def _get_client(self):
        """Get ElevenLabs client."""
        if self._client is None:
            from src.voice.elevenlabs_client import ElevenLabsClient
            self._client = ElevenLabsClient()
        return self._client
    
    def list_voices(self) -> List[Dict[str, Any]]:
        """List available voice profiles."""
        return [p.to_dict() for p in self._profiles.values()]
    
    def get_voice(self, voice_id: str) -> Optional[VoiceProfile]:
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
        voice: Optional[str] = None,
        stream: bool = False,
    ) -> Optional[Path]:
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
            client = await self._get_client()
            
            if stream:
                await client.stream_speech(
                    text,
                    voice=profile.voice_id,
                    model=profile.model,
                )
                return None
            else:
                audio_path = await client.generate_speech(
                    text,
                    voice=profile.voice_id,
                    model=profile.model,
                    stability=profile.stability,
                    similarity_boost=profile.similarity_boost,
                )
                return audio_path
        
        except Exception as e:
            secure_logger.error(f"Speech generation failed: {e}")
            raise
    
    async def speak_fast(self, text: str, voice: Optional[str] = None):
        """Quick speech with streaming for low latency."""
        return await self.speak(text, voice, stream=True)
    
    def get_session(self) -> Optional[AudioSession]:
        """Get current audio session."""
        return self._current_session
    
    def start_session(self, voice: Optional[str] = None) -> AudioSession:
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
_voice_manager: Optional[VoiceManager] = None


def get_voice_manager() -> VoiceManager:
    """Get or create voice manager."""
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceManager()
    return _voice_manager
