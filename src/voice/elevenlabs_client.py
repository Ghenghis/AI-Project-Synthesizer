"""
AI Project Synthesizer - ElevenLabs Voice Client

Full-featured ElevenLabs integration for:
- Text-to-Speech (TTS)
- Real-time voice streaming (LOW LATENCY)
- Voice cloning
- Voice selection and management

SPEED OPTIMIZATION:
- Use eleven_turbo_v2_5 for fastest response
- Stream audio chunks for smooth playback without gaps
- PCM format for lowest latency
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


@dataclass
class Voice:
    """ElevenLabs voice information."""

    voice_id: str
    name: str
    category: str  # premade, cloned, generated
    description: str | None = None
    preview_url: str | None = None
    labels: dict[str, str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class VoiceSettings:
    """Voice generation settings."""

    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True


# Popular pre-made voices
PREMADE_VOICES = {
    "rachel": Voice(
        "21m00Tcm4TlvDq8ikWAM", "Rachel", "premade", "Calm, professional female"
    ),
    "domi": Voice(
        "AZnzlk1XvdvUeBnXmlld", "Domi", "premade", "Strong, confident female"
    ),
    "bella": Voice("EXAVITQu4vr4xnSDxMaL", "Bella", "premade", "Soft, gentle female"),
    "antoni": Voice(
        "ErXwobaYiN019PkySvjV", "Antoni", "premade", "Well-rounded, warm male"
    ),
    "elli": Voice(
        "MF3mGyEYCl7XYWbV9V6O", "Elli", "premade", "Young, expressive female"
    ),
    "josh": Voice("TxGEqnHWrfWFTfGW9XjX", "Josh", "premade", "Deep, narrative male"),
    "arnold": Voice(
        "VR6AewLTigWG4xSOukaG", "Arnold", "premade", "Crisp, authoritative male"
    ),
    "adam": Voice("pNInz6obpgDQGcFmaJgB", "Adam", "premade", "Deep, warm male"),
    "sam": Voice("yoZ06aMxZJJ28mfd3POQ", "Sam", "premade", "Dynamic, expressive male"),
}


class ElevenLabsClient:
    """
    ElevenLabs API client for voice synthesis.

    Features:
    - Text-to-Speech with multiple voices
    - Real-time streaming for low latency
    - Voice selection and management
    - Custom voice settings

    Example:
        client = ElevenLabsClient()

        # Simple TTS
        audio = await client.text_to_speech("Hello world!")

        # Stream audio in real-time
        async for chunk in client.stream_speech("Long text here..."):
            play_audio(chunk)

        # Use specific voice
        audio = await client.text_to_speech(
            "Hello!",
            voice="josh",  # or voice_id
        )
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str | None = None):
        """Initialize ElevenLabs client."""
        settings = get_settings()
        self._api_key = (
            api_key or settings.elevenlabs.elevenlabs_api_key.get_secret_value()
        )

        if not self._api_key:
            secure_logger.warning("ElevenLabs API key not configured")

        # Load settings
        self._default_voice_id = settings.elevenlabs.default_voice_id
        self._tts_model = settings.elevenlabs.tts_model
        self._realtime_model = settings.elevenlabs.realtime_model
        self._output_format = settings.elevenlabs.output_format

        self._default_settings = VoiceSettings(
            stability=settings.elevenlabs.stability,
            similarity_boost=settings.elevenlabs.similarity_boost,
            style=settings.elevenlabs.style,
            use_speaker_boost=settings.elevenlabs.use_speaker_boost,
        )

        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "xi-api-key": self._api_key,
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _resolve_voice_id(self, voice: str | None) -> str:
        """Resolve voice name or ID to voice ID."""
        if voice is None:
            return self._default_voice_id

        # Check if it's a known voice name
        voice_lower = voice.lower()
        if voice_lower in PREMADE_VOICES:
            return PREMADE_VOICES[voice_lower].voice_id

        # Assume it's a voice ID
        return voice

    async def text_to_speech(
        self,
        text: str,
        voice: str | None = None,
        model: str | None = None,
        settings: VoiceSettings | None = None,
        output_format: str | None = None,
    ) -> bytes:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert
            voice: Voice name (rachel, josh, etc.) or voice_id
            model: TTS model to use
            settings: Voice settings
            output_format: Audio format

        Returns:
            Audio bytes
        """
        if not self._api_key:
            raise ValueError("ElevenLabs API key not configured")

        voice_id = self._resolve_voice_id(voice)
        model_id = model or self._tts_model
        voice_settings = settings or self._default_settings
        fmt = output_format or self._output_format

        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": voice_settings.stability,
                "similarity_boost": voice_settings.similarity_boost,
                "style": voice_settings.style,
                "use_speaker_boost": voice_settings.use_speaker_boost,
            },
        }

        session = await self._get_session()

        async with session.post(
            url,
            json=payload,
            params={"output_format": fmt},
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"ElevenLabs API error: {response.status} - {error}")

            audio_data = await response.read()
            secure_logger.info(f"Generated {len(audio_data)} bytes of audio")
            return audio_data

    async def stream_speech(
        self,
        text: str,
        voice: str | None = None,
        model: str | None = None,
        settings: VoiceSettings | None = None,
        chunk_size: int = 1024,
    ) -> AsyncIterator[bytes]:
        """
        Stream text-to-speech audio in real-time.

        Args:
            text: Text to convert
            voice: Voice name or ID
            model: TTS model (defaults to realtime model)
            settings: Voice settings
            chunk_size: Size of audio chunks

        Yields:
            Audio chunks as bytes
        """
        if not self._api_key:
            raise ValueError("ElevenLabs API key not configured")

        voice_id = self._resolve_voice_id(voice)
        model_id = model or self._realtime_model  # Use faster model for streaming
        voice_settings = settings or self._default_settings

        url = f"{self.BASE_URL}/text-to-speech/{voice_id}/stream"

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": voice_settings.stability,
                "similarity_boost": voice_settings.similarity_boost,
                "style": voice_settings.style,
                "use_speaker_boost": voice_settings.use_speaker_boost,
            },
        }

        session = await self._get_session()

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"ElevenLabs API error: {response.status} - {error}")

            async for chunk in response.content.iter_chunked(chunk_size):
                yield chunk

    async def get_voices(self) -> list[Voice]:
        """Get all available voices."""
        if not self._api_key:
            return list(PREMADE_VOICES.values())

        url = f"{self.BASE_URL}/voices"
        session = await self._get_session()

        async with session.get(url) as response:
            if response.status != 200:
                secure_logger.warning("Failed to fetch voices, using premade list")
                return list(PREMADE_VOICES.values())

            data = await response.json()
            voices = []

            for v in data.get("voices", []):
                voice = Voice(
                    voice_id=v["voice_id"],
                    name=v["name"],
                    category=v.get("category", "unknown"),
                    description=v.get("description"),
                    preview_url=v.get("preview_url"),
                    labels=v.get("labels", {}),
                )
                voices.append(voice)

            return voices

    async def get_voice(self, voice_id: str) -> Voice | None:
        """Get specific voice details."""
        url = f"{self.BASE_URL}/voices/{voice_id}"
        session = await self._get_session()

        async with session.get(url) as response:
            if response.status != 200:
                return None

            v = await response.json()
            return Voice(
                voice_id=v["voice_id"],
                name=v["name"],
                category=v.get("category", "unknown"),
                description=v.get("description"),
                preview_url=v.get("preview_url"),
                labels=v.get("labels", {}),
            )

    async def save_audio(
        self,
        text: str,
        output_path: Path,
        voice: str | None = None,
        **kwargs,
    ) -> Path:
        """
        Generate and save audio to file.

        Args:
            text: Text to convert
            output_path: Path to save audio
            voice: Voice name or ID
            **kwargs: Additional TTS arguments

        Returns:
            Path to saved file
        """
        audio = await self.text_to_speech(text, voice=voice, **kwargs)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio)

        secure_logger.info(f"Saved audio to {output_path}")
        return output_path

    async def get_user_info(self) -> dict[str, Any]:
        """Get user subscription info."""
        url = f"{self.BASE_URL}/user"
        session = await self._get_session()

        async with session.get(url) as response:
            if response.status != 200:
                return {}
            return await response.json()

    async def get_usage(self) -> dict[str, Any]:
        """Get character usage info."""
        url = f"{self.BASE_URL}/user/subscription"
        session = await self._get_session()

        async with session.get(url) as response:
            if response.status != 200:
                return {}
            return await response.json()


def create_elevenlabs_client() -> ElevenLabsClient | None:
    """Factory function to create ElevenLabs client if API key is available."""
    settings = get_settings()

    if settings.elevenlabs.elevenlabs_api_key.get_secret_value():
        return ElevenLabsClient()

    return None
