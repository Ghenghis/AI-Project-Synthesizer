"""
AI Project Synthesizer - Voice Player

Auto-plays audio for MCP clients that don't have native audio playback.
Tagged for: LM Studio (requires this for voice playback)

Other MCP clients may have native audio support and won't need this.
"""

import asyncio
import base64
import platform
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


@dataclass
class PlaybackResult:
    """Result of audio playback."""

    success: bool
    duration_ms: int = 0
    error: str | None = None


class VoicePlayer:
    """
    Cross-platform audio player for voice output.

    LM STUDIO INTEGRATION:
    LM Studio's MCP implementation doesn't auto-play audio.
    This player decodes base64 audio and plays it through system speakers.

    Usage:
        player = VoicePlayer()
        await player.play_base64(audio_base64, format="mp3")
    """

    def __init__(self, temp_dir: Path | None = None):
        """Initialize voice player."""
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "ai_synthesizer_voice"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._current_process: subprocess.Popen | None = None
        self.system = platform.system()

    async def play_base64(
        self,
        audio_base64: str,
        format: str = "mp3",
        wait: bool = True,
    ) -> PlaybackResult:
        """
        Play base64-encoded audio.

        Args:
            audio_base64: Base64-encoded audio data
            format: Audio format (mp3, wav, etc.)
            wait: Wait for playback to complete

        Returns:
            PlaybackResult with success status
        """
        try:
            # Decode base64
            audio_bytes = base64.b64decode(audio_base64)
            return await self.play_bytes(audio_bytes, format, wait)
        except Exception as e:
            secure_logger.error(f"Failed to decode audio: {e}")
            return PlaybackResult(success=False, error=str(e))

    async def play_bytes(
        self,
        audio_bytes: bytes,
        format: str = "mp3",
        wait: bool = True,
    ) -> PlaybackResult:
        """
        Play audio from bytes.

        Args:
            audio_bytes: Raw audio data
            format: Audio format
            wait: Wait for playback to complete

        Returns:
            PlaybackResult with success status
        """
        # Save to temp file
        temp_file = self.temp_dir / f"voice_output.{format}"
        temp_file.write_bytes(audio_bytes)

        return await self.play_file(temp_file, wait)

    async def play_file(
        self,
        file_path: Path,
        wait: bool = True,
    ) -> PlaybackResult:
        """
        Play audio file through system speakers.

        Args:
            file_path: Path to audio file
            wait: Wait for playback to complete

        Returns:
            PlaybackResult with success status
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return PlaybackResult(success=False, error=f"File not found: {file_path}")

        try:
            # Stop any current playback
            await self.stop()

            # Platform-specific playback
            if self.system == "Windows":
                result = await self._play_windows(file_path, wait)
            elif self.system == "Darwin":  # macOS
                result = await self._play_macos(file_path, wait)
            else:  # Linux
                result = await self._play_linux(file_path, wait)

            secure_logger.info(f"Audio playback completed: {file_path.name}")
            return result

        except Exception as e:
            secure_logger.error(f"Playback error: {e}")
            return PlaybackResult(success=False, error=str(e))

    async def _play_windows(self, file_path: Path, wait: bool) -> PlaybackResult:
        """Play audio on Windows using PowerShell."""
        # Use Windows Media Player COM object for reliable playback
        ps_script = f'''
Add-Type -AssemblyName presentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open("{file_path.absolute()}")
$player.Play()
Start-Sleep -Milliseconds 500
while ($player.NaturalDuration.HasTimeSpan -and $player.Position -lt $player.NaturalDuration.TimeSpan) {{
    Start-Sleep -Milliseconds 100
}}
$player.Close()
'''

        if wait:
            # Run synchronously
            process = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()
            return PlaybackResult(success=process.returncode == 0)
        else:
            # Run in background
            self._current_process = subprocess.Popen(
                ["powershell", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return PlaybackResult(success=True)

    async def _play_macos(self, file_path: Path, wait: bool) -> PlaybackResult:
        """Play audio on macOS using afplay."""
        cmd = ["afplay", str(file_path)]

        if wait:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()
            return PlaybackResult(success=process.returncode == 0)
        else:
            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return PlaybackResult(success=True)

    async def _play_linux(self, file_path: Path, wait: bool) -> PlaybackResult:
        """Play audio on Linux using available player."""
        # Try different players
        players = [
            ["mpv", "--no-video", str(file_path)],
            ["ffplay", "-nodisp", "-autoexit", str(file_path)],
            ["aplay", str(file_path)],  # For WAV
            ["paplay", str(file_path)],  # PulseAudio
        ]

        for cmd in players:
            try:
                if wait:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await process.wait()
                    if process.returncode == 0:
                        return PlaybackResult(success=True)
                else:
                    self._current_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return PlaybackResult(success=True)
            except FileNotFoundError:
                continue

        return PlaybackResult(success=False, error="No audio player found")

    async def stop(self):
        """Stop current playback."""
        if self._current_process:
            try:
                self._current_process.terminate()
                self._current_process = None
            except Exception:
                pass

    def cleanup(self):
        """Clean up temp files."""
        try:
            for f in self.temp_dir.glob("voice_output.*"):
                f.unlink()
        except Exception:
            pass


# Global player instance
_player: VoicePlayer | None = None


def get_voice_player() -> VoicePlayer:
    """Get or create global voice player."""
    global _player
    if _player is None:
        _player = VoicePlayer()
    return _player


async def play_audio(
    audio_base64: str, format: str = "mp3", wait: bool = True
) -> PlaybackResult:
    """
    Convenience function to play base64 audio.

    LM STUDIO: Call this after assistant_speak to hear the voice.

    Args:
        audio_base64: Base64-encoded audio
        format: Audio format
        wait: Wait for completion

    Returns:
        PlaybackResult
    """
    player = get_voice_player()
    return await player.play_base64(audio_base64, format, wait)
