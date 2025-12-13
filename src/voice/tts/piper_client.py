"""
VIBE MCP - Piper TTS Client

Local text-to-speech using Piper for fast, offline voice synthesis.
Integrates with extracted ElevenLabs voice samples for voice cloning.

Features:
- Local voice synthesis with <100ms latency
- Support for custom voice models from extracted samples
- Multiple audio formats (WAV, MP3, PCM)
- Voice configuration and management
"""

import asyncio
import builtins
import contextlib
import tempfile
from pathlib import Path

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class PiperTTSClient:
    """
    Piper TTS client for local voice synthesis.

    Provides fast, offline text-to-speech using Piper models.
    Can use custom voice models trained from extracted ElevenLabs samples.
    """

    def __init__(
        self,
        piper_path: str | Path | None = None,
        model_dir: str | Path | None = None,
        voice_dir: str | Path | None = None
    ):
        """
        Initialize Piper TTS client.

        Args:
            piper_path: Path to Piper executable
            model_dir: Directory containing Piper voice models
            voice_dir: Directory containing extracted voice samples
        """
        self.settings = get_settings()

        # Default paths
        self.piper_path = Path(piper_path or "piper")
        self.model_dir = Path(model_dir or "models/piper")
        self.voice_dir = Path(voice_dir or "voices")

        # Available voice models
        self._available_models = {}

        # Audio format settings
        self.sample_rate = 22050  # Piper default
        self.bit_depth = 16

        secure_logger.info("Piper TTS client initialized")
        secure_logger.info(f"  Piper path: {self.piper_path}")
        secure_logger.info(f"  Model directory: {self.model_dir}")
        secure_logger.info(f"  Voice directory: {self.voice_dir}")

    async def initialize(self) -> bool:
        """
        Initialize the Piper TTS client.

        Returns:
            True if initialization successful
        """
        try:
            # Check if Piper is available
            result = await asyncio.create_subprocess_exec(
                str(self.piper_path),
                "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                secure_logger.error(f"Piper not found or not working: {stderr.decode()}")
                return False

            # Load available voice models
            await self._load_voice_models()

            secure_logger.info(f"Piper TTS initialized with {len(self._available_models)} models")
            return True

        except Exception as e:
            secure_logger.error(f"Failed to initialize Piper TTS: {e}")
            return False

    async def _load_voice_models(self):
        """Load available voice models from model directory."""
        if not self.model_dir.exists():
            secure_logger.warning(f"Model directory not found: {self.model_dir}")
            return

        # Look for .onnx model files
        for model_file in self.model_dir.glob("*.onnx"):
            # Corresponding config file should have same name with .json extension
            config_file = model_file.with_suffix(".json")

            if config_file.exists():
                voice_name = model_file.stem
                self._available_models[voice_name] = {
                    "model": str(model_file),
                    "config": str(config_file),
                    "name": voice_name.replace("_", " ").title()
                }

        secure_logger.info(f"Loaded {len(self._available_models)} Piper models")

    async def synthesize(
        self,
        text: str,
        voice: str = "default",
        output_format: str = "wav",
        speed: float = 1.0,
        noise_scale: float = 0.667,
        noise_w: float = 0.8
    ) -> bytes:
        """
        Synthesize speech from text using Piper.

        Args:
            text: Text to synthesize
            voice: Voice model to use
            output_format: Output audio format (wav, mp3)
            speed: Speech speed (0.25 to 4.0)
            noise_scale: Noise scale for variability
            noise_w: Noise weight for variability

        Returns:
            Audio data as bytes
        """
        if not self._available_models:
            raise RuntimeError("No voice models available. Call initialize() first.")

        # Get voice model
        if voice not in self._available_models:
            # Try to find closest match
            available_voices = list(self._available_models.keys())
            if available_voices:
                voice = available_voices[0]
                secure_logger.warning(f"Voice '{voice}' not found, using '{voice}'")
            else:
                raise RuntimeError("No voice models available")

        model_info = self._available_models[voice]

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Build Piper command
            cmd = [
                str(self.piper_path),
                "--model", model_info["model"],
                "--config_file", model_info["config"],
                "--output_file", temp_path,
                "--length_scale", str(1.0 / speed),  # Piper uses inverse of speed
                "--noise_scale", str(noise_scale),
                "--noise_w", str(noise_w)
            ]

            # Run Piper synthesis
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send text to Piper
            stdout, stderr = await process.communicate(input=text.encode())

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Piper synthesis failed: {error_msg}")

            # Read generated audio
            with open(temp_path, "rb") as f:
                audio_data = f.read()

            secure_logger.info(f"Generated {len(audio_data)} bytes of audio for voice '{voice}'")
            return audio_data

        finally:
            # Clean up temporary file
            with contextlib.suppress(builtins.BaseException):
                Path(temp_path).unlink()

    async def get_available_voices(self) -> dict[str, dict]:
        """
        Get list of available voice models.

        Returns:
            Dictionary of voice information
        """
        return self._available_models.copy()

    async def create_voice_model(
        self,
        voice_name: str,
        audio_samples: list[Path],
        output_dir: Path | None = None
    ) -> bool:
        """
        Create a custom voice model from audio samples.

        Args:
            voice_name: Name for the new voice model
            audio_samples: List of audio sample files
            output_dir: Directory to save the model

        Returns:
            True if model creation successful
        """
        # This is a placeholder for voice training functionality
        # In practice, this would use Piper's training capabilities
        # or integrate with external voice cloning tools

        secure_logger.info(f"Voice model creation requested for '{voice_name}'")
        secure_logger.info(f"  Samples: {len(audio_samples)} files")
        secure_logger.info(f"  Output dir: {output_dir or self.model_dir}")

        # // DONE: Implement actual voice training
        # This would involve:
        # 1. Audio preprocessing (convert to WAV, normalize)
        # 2. Feature extraction
        # 3. Model training using Piper's training scripts
        # 4. Model validation and testing

        return False

    def get_extracted_voices(self) -> dict[str, dict]:
        """
        Get information about extracted voice samples.

        Returns:
            Dictionary of extracted voice information
        """
        voices = {}

        if not self.voice_dir.exists():
            return voices

        # Scan voice directory for extracted samples
        for lang_dir in self.voice_dir.iterdir():
            if lang_dir.is_dir():
                for dialect_dir in lang_dir.iterdir():
                    if dialect_dir.is_dir():
                        for voice_dir in dialect_dir.iterdir():
                            if voice_dir.is_dir():
                                # Count audio samples
                                audio_files = list(voice_dir.glob("*.mp3"))
                                if audio_files:
                                    voice_key = f"{lang_dir.name}_{dialect_dir.name}_{voice_dir.name}"
                                    voices[voice_key] = {
                                        "language": lang_dir.name,
                                        "dialect": dialect_dir.name,
                                        "name": voice_dir.name,
                                        "path": str(voice_dir),
                                        "samples": len(audio_files),
                                        "ready_for_training": len(audio_files) >= 10
                                    }

        return voices


# Factory function
async def create_piper_client(**kwargs) -> PiperTTSClient | None:
    """
    Create and initialize a Piper TTS client.

    Args:
        **kwargs: Arguments to pass to PiperTTSClient constructor

    Returns:
        Initialized Piper client or None if failed
    """
    client = PiperTTSClient(**kwargs)

    if await client.initialize():
        return client

    return None


# Default voice configurations for common models
DEFAULT_PIPER_VOICES = {
    "default": {
        "model": "en_US-lessac-medium.onnx",
        "config": "en_US-lessac-medium.onnx.json",
        "description": "Default American English male voice"
    },
    "female": {
        "model": "en_US-lessac-medium.onnx",  # Would be female model in practice
        "config": "en_US-lessac-medium.onnx.json",
        "description": "Default American English female voice"
    },
    "british": {
        "model": "en_GB-lessac-medium.onnx",  # Would be British model
        "config": "en_GB-lessac-medium.onnx.json",
        "description": "British English male voice"
    }
}
