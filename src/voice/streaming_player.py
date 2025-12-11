"""
AI Project Synthesizer - Streaming Voice Player

OPTIMIZED FOR SPEED AND SMOOTH PLAYBACK:
- Streams audio chunks as they arrive (no waiting for full generation)
- Uses turbo model for fastest response
- PCM format for lowest latency
- Buffer management for smooth transitions without gaps

LM STUDIO INTEGRATION:
This provides seamless voice output for MCP clients without native audio.
"""

import asyncio
import wave
import tempfile
import subprocess
import platform
import struct
from pathlib import Path
from typing import Optional, AsyncIterator, Callable
from dataclasses import dataclass
import threading
import queue
import time

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


@dataclass
class StreamConfig:
    """Configuration for streaming playback."""
    # Model selection (turbo = fastest)
    model: str = "eleven_turbo_v2_5"  # Fastest model
    
    # Voice settings optimized for speed
    stability: float = 0.5
    similarity_boost: float = 0.8
    style: float = 0.0
    
    # Output format (pcm = lowest latency)
    output_format: str = "pcm_24000"  # 24kHz PCM for speed
    
    # Buffer settings for smooth playback
    chunk_size: int = 4096  # Bytes per chunk
    buffer_chunks: int = 2  # Pre-buffer before playing
    
    # Latency optimization
    optimize_streaming_latency: int = 4  # 0-4, higher = lower latency


class StreamingVoicePlayer:
    """
    Real-time streaming voice player.
    
    Plays audio as it's generated - no waiting for full audio.
    Optimized for smooth transitions without gaps.
    
    Usage:
        player = StreamingVoicePlayer()
        await player.speak("Hello, this plays immediately!")
    """
    
    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize streaming player."""
        self.config = config or StreamConfig()
        self._api_key = None
        self._playing = False
        self._audio_queue = queue.Queue()
        self._player_thread: Optional[threading.Thread] = None
        self.system = platform.system()
        
        self._init_api_key()
    
    def _init_api_key(self):
        """Get ElevenLabs API key."""
        try:
            from src.core.config import get_settings
            settings = get_settings()
            self._api_key = settings.elevenlabs.elevenlabs_api_key.get_secret_value()
        except Exception:
            pass
    
    async def speak(
        self,
        text: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
        on_chunk: Optional[Callable[[bytes], None]] = None,
    ) -> bool:
        """
        Speak text with streaming playback.
        
        Audio starts playing as soon as first chunks arrive.
        No gaps between chunks for smooth output.
        
        Args:
            text: Text to speak
            voice_id: ElevenLabs voice ID
            on_chunk: Optional callback for each audio chunk
        
        Returns:
            True if successful
        """
        if not self._api_key:
            secure_logger.error("ElevenLabs API key not configured")
            return False
        
        # Start player thread
        self._playing = True
        self._start_player_thread()
        
        try:
            # Stream audio from ElevenLabs
            async for chunk in self._stream_audio(text, voice_id):
                self._audio_queue.put(chunk)
                if on_chunk:
                    on_chunk(chunk)
            
            # Signal end of audio
            self._audio_queue.put(None)
            
            # Wait for playback to complete
            if self._player_thread:
                self._player_thread.join(timeout=30)
            
            return True
            
        except Exception as e:
            secure_logger.error(f"Streaming error: {e}")
            self._playing = False
            return False
    
    async def _stream_audio(
        self,
        text: str,
        voice_id: str,
    ) -> AsyncIterator[bytes]:
        """Stream audio from ElevenLabs API."""
        import aiohttp
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "text": text,
            "model_id": self.config.model,
            "voice_settings": {
                "stability": self.config.stability,
                "similarity_boost": self.config.similarity_boost,
                "style": self.config.style,
            },
        }
        
        params = {
            "output_format": self.config.output_format,
            "optimize_streaming_latency": self.config.optimize_streaming_latency,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                params=params,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"ElevenLabs API error: {response.status} - {error}")
                
                # Stream chunks as they arrive
                async for chunk in response.content.iter_chunked(self.config.chunk_size):
                    yield chunk
    
    def _start_player_thread(self):
        """Start background audio player thread."""
        if self._player_thread and self._player_thread.is_alive():
            return
        
        self._player_thread = threading.Thread(
            target=self._player_loop,
            daemon=True,
        )
        self._player_thread.start()
    
    def _player_loop(self):
        """Background thread that plays audio chunks."""
        if self.system == "Windows":
            self._play_windows_stream()
        elif self.system == "Darwin":
            self._play_macos_stream()
        else:
            self._play_linux_stream()
    
    def _play_windows_stream(self):
        """Play streaming audio on Windows using winsound or pyaudio."""
        try:
            import pyaudio
            self._play_with_pyaudio()
        except ImportError:
            # Fallback: collect all chunks and play as file
            self._play_collected_chunks()
    
    def _play_with_pyaudio(self):
        """Play using PyAudio for lowest latency."""
        import pyaudio
        
        # PCM 24000Hz, 16-bit, mono
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True,
            frames_per_buffer=self.config.chunk_size // 2,
        )
        
        try:
            while self._playing:
                try:
                    chunk = self._audio_queue.get(timeout=0.1)
                    if chunk is None:
                        break
                    stream.write(chunk)
                except queue.Empty:
                    continue
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def _play_collected_chunks(self):
        """Collect chunks and play as file (fallback)."""
        chunks = []
        
        while self._playing:
            try:
                chunk = self._audio_queue.get(timeout=0.1)
                if chunk is None:
                    break
                chunks.append(chunk)
            except queue.Empty:
                continue
        
        if not chunks:
            return
        
        # Save as WAV and play
        audio_data = b''.join(chunks)
        temp_file = Path(tempfile.gettempdir()) / "stream_voice.wav"
        
        # Write PCM data as WAV
        with wave.open(str(temp_file), 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(24000)
            wav.writeframes(audio_data)
        
        # Play the file
        if self.system == "Windows":
            subprocess.run(
                ["powershell", "-Command", f'(New-Object Media.SoundPlayer "{temp_file}").PlaySync()'],
                capture_output=True,
            )
        elif self.system == "Darwin":
            subprocess.run(["afplay", str(temp_file)], capture_output=True)
        else:
            subprocess.run(["aplay", str(temp_file)], capture_output=True)
    
    def _play_macos_stream(self):
        """Play streaming audio on macOS."""
        try:
            import pyaudio
            self._play_with_pyaudio()
        except ImportError:
            self._play_collected_chunks()
    
    def _play_linux_stream(self):
        """Play streaming audio on Linux."""
        try:
            import pyaudio
            self._play_with_pyaudio()
        except ImportError:
            self._play_collected_chunks()
    
    def stop(self):
        """Stop current playback."""
        self._playing = False
        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break


# Singleton instance
_streaming_player: Optional[StreamingVoicePlayer] = None


def get_streaming_player() -> StreamingVoicePlayer:
    """Get or create streaming player."""
    global _streaming_player
    if _streaming_player is None:
        _streaming_player = StreamingVoicePlayer()
    return _streaming_player


async def speak_fast(
    text: str,
    voice: str = "rachel",
) -> bool:
    """
    Quick function for fast, smooth voice output.
    
    Uses turbo model + streaming for lowest latency.
    
    Args:
        text: Text to speak
        voice: Voice name or ID
    
    Returns:
        True if successful
    """
    from src.voice.elevenlabs_client import PREMADE_VOICES
    
    # Resolve voice name to ID
    voice_id = voice
    if voice.lower() in PREMADE_VOICES:
        voice_id = PREMADE_VOICES[voice.lower()].voice_id
    
    player = get_streaming_player()
    return await player.speak(text, voice_id)
