"""
Mock voice services for testing.
"""

from pathlib import Path
from typing import Any


class MockVoicePlayer:
    """Mock voice player for testing."""

    def __init__(self):
        self.played_files = []
        self.played_audio = []
        self.is_playing = False
        self.current_process = None
        self.system = "Windows"  # Mock system

    async def play_file(self, file_path: Path, wait: bool = True) -> dict[str, Any]:
        """Mock play file."""
        self.played_files.append((str(file_path), wait))
        if wait:
            self.is_playing = False
        else:
            self.is_playing = True
        return {"success": True, "file": str(file_path)}

    async def play_base64(
        self, audio_base64: str, format: str = "mp3", wait: bool = True
    ) -> dict[str, Any]:
        """Mock play base64 audio."""
        self.played_audio.append((audio_base64[:50], format, wait))
        if wait:
            self.is_playing = False
        else:
            self.is_playing = True
        return {"success": True, "format": format}

    async def play_bytes(self, audio_data: bytes, wait: bool = True) -> dict[str, Any]:
        """Mock play bytes."""
        if wait:
            self.is_playing = False
        else:
            self.is_playing = True
        return {"success": True}

    async def play_base64(
        self, audio_base64: str, format: str = "mp3", wait: bool = True
    ) -> dict[str, Any]:
        """Mock play base64 audio."""
        self.played_audio.append((audio_base64[:50], format, wait))
        if wait:
            self.is_playing = False
        else:
            self.is_playing = True
        return {"success": True, "format": format}

    async def stop(self):
        """Mock stop playback."""
        self.is_playing = False
        self.current_process = None

    async def get_volume(self) -> float:
        """Mock get volume."""
        return 0.8

    async def set_volume(self, volume: float):
        """Mock set volume."""


class MockASRClient:
    """Mock Automatic Speech Recognition client."""

    def __init__(self):
        self.transcriptions = []
        self.languages = ["en", "zh", "es", "fr", "de"]

    def set_transcription(self, text: str):
        """Set the next transcription to return."""
        self.transcriptions.append(text)

    async def transcribe_file(
        self, audio_path: str, language: str = "en"
    ) -> dict[str, Any]:
        """Mock transcribe audio file."""
        if self.transcriptions:
            text = self.transcriptions.pop(0)
        else:
            text = f"Mock transcription for {Path(audio_path).name}"

        return {"text": text, "language": language, "confidence": 0.95, "duration": 2.5}

    async def transcribe_stream(
        self, audio_stream, language: str = "en"
    ) -> dict[str, Any]:
        """Mock transcribe audio stream."""
        return {
            "text": "Mock stream transcription",
            "language": language,
            "confidence": 0.90,
        }

    def get_supported_languages(self) -> list[str]:
        """Get supported languages."""
        return self.languages


class MockTTSClient:
    """Mock Text-to-Speech client."""

    def __init__(self):
        self.synthesized_texts = []
        self.voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    async def synthesize(
        self, text: str, voice: str = "alloy", format: str = "mp3"
    ) -> bytes:
        """Mock synthesize text to speech."""
        self.synthesized_texts.append((text, voice, format))
        # Return mock audio data
        return b"mock_audio_data_" + text.encode()[:50]

    async def synthesize_stream(self, text: str, voice: str = "alloy"):
        """Mock synthesize with streaming."""
        # Mock streaming generator
        yield b"chunk1_"
        yield b"chunk2_"
        yield text.encode()[:50]

    def get_available_voices(self) -> list[str]:
        """Get available voices."""
        return self.voices

    async def get_voice_sample(self, voice: str) -> bytes:
        """Get voice sample."""
        return f"mock_sample_for_{voice}".encode()
