"""
AI Project Synthesizer - Real-Time Voice Conversation

Instant back-and-forth voice chat:
1. Listens to user via microphone
2. Detects silence (configurable pause threshold)
3. Transcribes speech to text
4. Sends to AI assistant
5. Speaks response immediately (streaming)
6. Loops back to listening

PAUSE DETECTION:
- Default: 3.5 seconds of silence triggers response
- Configurable via pause_threshold parameter

PROACTIVE RESEARCH (when user is idle):
- 30s idle: Light research (quick project search)
- 60s idle: Medium research (more projects + papers)
- 120s idle: Deep research (synthesis recommendations)
- AI presents findings when user returns!
"""

import asyncio
import threading
import queue
import time
import wave
import tempfile
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class ConversationState(str, Enum):
    """Current state of the conversation."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    RESEARCHING = "researching"  # AI is proactively researching


@dataclass
class ConversationConfig:
    """Configuration for real-time conversation."""
    # Pause detection
    pause_threshold: float = 3.5  # Seconds of silence to trigger response
    min_speech_duration: float = 0.5  # Minimum speech to process

    # Proactive research (when user is idle)
    enable_proactive_research: bool = True
    research_after_idle: float = 30.0  # Start researching after this many seconds

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024

    # Voice settings
    voice: str = "rachel"

    # Silence detection
    silence_threshold: int = 500  # Audio level below this = silence

    # Callbacks
    on_state_change: Optional[Callable[[ConversationState], None]] = None
    on_user_speech: Optional[Callable[[str], None]] = None
    on_assistant_response: Optional[Callable[[str], None]] = None


class RealtimeConversation:
    """
    Real-time voice conversation with AI.

    Listens continuously, detects pauses, responds with voice.

    Usage:
        conv = RealtimeConversation()
        await conv.start()
        # Now talking back and forth!
        # Say something, pause for 3.5s, AI responds
        await conv.stop()
    """

    def __init__(self, config: Optional[ConversationConfig] = None):
        """Initialize conversation."""
        self.config = config or ConversationConfig()
        self.state = ConversationState.IDLE
        self._running = False
        self._audio_queue = queue.Queue()
        self._listen_thread: Optional[threading.Thread] = None
        self._last_user_speech: float = time.time()
        self._research_presented: bool = False

        # Components
        self._assistant = None
        self._voice_player = None
        self._transcriber = None
        self._research_engine = None

    async def start(self):
        """Start the conversation loop."""
        if self._running:
            return

        self._running = True
        self._set_state(ConversationState.LISTENING)

        # Initialize components
        await self._init_components()

        # Start listening thread
        self._listen_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
        )
        self._listen_thread.start()

        # Start proactive research if enabled
        if self.config.enable_proactive_research:
            await self._research_engine.start_monitoring()

        # Start processing loop
        await self._process_loop()

    async def stop(self):
        """Stop the conversation."""
        self._running = False
        self._set_state(ConversationState.IDLE)

        if self._research_engine:
            await self._research_engine.stop_monitoring()

        if self._listen_thread:
            self._listen_thread.join(timeout=2)

    async def _init_components(self):
        """Initialize AI and voice components."""
        # Assistant
        from src.assistant.core import ConversationalAssistant, AssistantConfig
        self._assistant = ConversationalAssistant(AssistantConfig(
            voice_enabled=False,  # We handle voice separately
        ))

        # Voice player
        from src.voice.streaming_player import get_streaming_player
        self._voice_player = get_streaming_player()

        # Proactive research engine
        if self.config.enable_proactive_research:
            from src.assistant.proactive_research import ProactiveResearchEngine, ResearchConfig

            def on_research_complete(result):
                secure_logger.info(f"Research ready: {result.summary()}")
                self._research_presented = False  # New research available

            self._research_engine = ProactiveResearchEngine(ResearchConfig(
                light_research_after=self.config.research_after_idle,
                medium_research_after=self.config.research_after_idle * 2,
                deep_research_after=self.config.research_after_idle * 4,
                on_research_complete=on_research_complete,
            ))

        secure_logger.info("Real-time conversation initialized")

    def _set_state(self, state: ConversationState):
        """Update state and notify."""
        self.state = state
        if self.config.on_state_change:
            self.config.on_state_change(state)

    def _listen_loop(self):
        """Background thread that captures audio."""
        try:
            import pyaudio
        except ImportError:
            secure_logger.error("PyAudio required for voice input. Install with: pip install pyaudio")
            return

        p = pyaudio.PyAudio()

        stream = p.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )

        audio_buffer = []
        silence_start = None
        speech_detected = False

        try:
            while self._running:
                if self.state != ConversationState.LISTENING:
                    time.sleep(0.1)
                    continue

                # Read audio chunk
                data = stream.read(self.config.chunk_size, exception_on_overflow=False)

                # Check audio level
                level = self._get_audio_level(data)
                is_silence = level < self.config.silence_threshold

                if not is_silence:
                    # Speech detected
                    speech_detected = True
                    silence_start = None
                    audio_buffer.append(data)
                else:
                    # Silence
                    if speech_detected:
                        audio_buffer.append(data)

                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= self.config.pause_threshold:
                            # Pause threshold reached - process speech
                            if len(audio_buffer) > 0:
                                audio_data = b''.join(audio_buffer)
                                self._audio_queue.put(audio_data)

                            # Reset
                            audio_buffer = []
                            silence_start = None
                            speech_detected = False

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def _get_audio_level(self, data: bytes) -> int:
        """Get audio level from raw data."""
        import struct

        # Convert bytes to samples
        count = len(data) // 2
        samples = struct.unpack(f'{count}h', data)

        # Return max absolute value
        return max(abs(s) for s in samples) if samples else 0

    async def _process_loop(self):
        """Main processing loop."""
        while self._running:
            try:
                # Check for audio to process
                try:
                    audio_data = self._audio_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

                # User is active - update research engine
                self._last_user_speech = time.time()
                if self._research_engine:
                    self._research_engine.user_active()

                # Process the audio
                self._set_state(ConversationState.PROCESSING)

                # Transcribe
                text = await self._transcribe(audio_data)

                if text and len(text.strip()) > 0:
                    secure_logger.info(f"User said: {text}")

                    if self.config.on_user_speech:
                        self.config.on_user_speech(text)

                    # Update research context
                    if self._research_engine:
                        self._research_engine.set_context(text)

                    # Check if we have research to present first
                    research_intro = ""
                    if self._research_engine and not self._research_presented:
                        result = self._research_engine.get_latest_research()
                        if result and result.projects:
                            self._research_presented = True
                            research_intro = f"While you were thinking, I found {len(result.projects)} relevant projects and {len(result.papers)} research papers. "

                    # Get AI response
                    response = await self._assistant.chat(text)
                    response_text = research_intro + response["text"]

                    # If we have detailed research, offer to share it
                    if self._research_engine and not self._research_presented:
                        result = self._research_engine.get_latest_research()
                        if result and result.recommendations:
                            response_text += " Would you like me to share my research findings?"

                    secure_logger.info(f"Assistant: {response_text[:100]}...")

                    if self.config.on_assistant_response:
                        self.config.on_assistant_response(response_text)

                    # Speak response
                    self._set_state(ConversationState.SPEAKING)
                    await self._speak(response_text)

                # Back to listening
                self._set_state(ConversationState.LISTENING)

            except Exception as e:
                secure_logger.error(f"Processing error: {e}")
                self._set_state(ConversationState.LISTENING)

    async def _transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio to text using Whisper or cloud API."""
        # Save audio to temp file
        temp_file = Path(tempfile.gettempdir()) / "speech_input.wav"

        with wave.open(str(temp_file), 'wb') as wav:
            wav.setnchannels(self.config.channels)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.config.sample_rate)
            wav.writeframes(audio_data)

        # Try OpenAI Whisper API
        try:
            from src.core.config import get_settings
            settings = get_settings()
            api_key = settings.llm.openai_api_key.get_secret_value()

            if api_key:
                import httpx

                async with httpx.AsyncClient() as client:
                    with open(temp_file, 'rb') as f:
                        response = await client.post(
                            "https://api.openai.com/v1/audio/transcriptions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            files={"file": ("audio.wav", f, "audio/wav")},
                            data={"model": "whisper-1"},
                            timeout=30,
                        )

                    if response.status_code == 200:
                        return response.json().get("text", "")
        except Exception as e:
            secure_logger.warning(f"Whisper API error: {e}")

        # Fallback: try local whisper
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(temp_file))
            return result.get("text", "")
        except ImportError:
            secure_logger.warning("Local whisper not available")
        except Exception as e:
            secure_logger.warning(f"Local whisper error: {e}")

        return ""

    async def _speak(self, text: str):
        """Speak text using streaming voice."""
        from src.voice.streaming_player import speak_fast
        await speak_fast(text, voice=self.config.voice)


async def start_voice_chat(
    pause_threshold: float = 3.5,
    voice: str = "rachel",
    on_user_speech: Optional[Callable[[str], None]] = None,
    on_assistant_response: Optional[Callable[[str], None]] = None,
):
    """
    Start a real-time voice conversation.

    Speak naturally, pause for 3.5 seconds, AI responds.

    Args:
        pause_threshold: Seconds of silence before AI responds
        voice: Voice to use for responses
        on_user_speech: Callback when user speaks
        on_assistant_response: Callback when AI responds

    Example:
        await start_voice_chat(
            pause_threshold=3.5,
            voice="josh",
            on_user_speech=lambda t: print(f"You: {t}"),
            on_assistant_response=lambda t: print(f"AI: {t}"),
        )
    """
    config = ConversationConfig(
        pause_threshold=pause_threshold,
        voice=voice,
        on_user_speech=on_user_speech,
        on_assistant_response=on_assistant_response,
    )

    conv = RealtimeConversation(config)

    print("\n🎤 Voice chat started!")
    print(f"   Speak naturally, pause for {pause_threshold}s to get a response.")
    print("   Press Ctrl+C to stop.\n")

    try:
        await conv.start()
    except KeyboardInterrupt:
        print("\n\n👋 Voice chat ended.")
        await conv.stop()
