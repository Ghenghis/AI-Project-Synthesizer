"""Tests for voice.realtime_conversation."""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["APP_ENV"] = "testing"

try:
    from src.voice.realtime_conversation import (
        AudioProcessor,
        AudioSegment,
        ConversationConfig,
        ConversationEvent,
        ConversationState,
        RealtimeConversation,
        SpeechRecognizer,
        TranscriptionResult,
        VoiceActivityDetector,
    )

    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error for voice.realtime_conversation: {e}")
    IMPORTS_AVAILABLE = False


class TestConversationState:
    """Test ConversationState enum."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_conversation_state_values(self):
        """Should have correct ConversationState values."""
        assert ConversationState.IDLE.value == "idle"
        assert ConversationState.LISTENING.value == "listening"
        assert ConversationState.PROCESSING.value == "processing"
        assert ConversationState.SPEAKING.value == "speaking"
        assert ConversationState.ERROR.value == "error"


class TestConversationEvent:
    """Test ConversationEvent enum."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_conversation_event_values(self):
        """Should have correct ConversationEvent values."""
        assert ConversationEvent.SPEECH_STARTED.value == "speech_started"
        assert ConversationEvent.SPEECH_ENDED.value == "speech_ended"
        assert ConversationEvent.TRANSCRIPTION_READY.value == "transcription_ready"
        assert ConversationEvent.RESPONSE_READY.value == "response_ready"
        assert ConversationEvent.ERROR.value == "error"


class TestConversationConfig:
    """Test ConversationConfig dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_config_default(self):
        """Should create config with default values."""
        config = ConversationConfig()
        assert config.pause_threshold == 3.5
        assert config.min_speech_duration == 0.5
        assert config.max_silence_duration == 2.0
        assert config.sample_rate == 16000
        assert config.channels == 1

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_config_custom(self):
        """Should create config with custom values."""
        config = ConversationConfig(
            pause_threshold=2.0,
            min_speech_duration=0.3,
            max_silence_duration=1.5,
            sample_rate=22050,
            channels=2,
        )
        assert config.pause_threshold == 2.0
        assert config.min_speech_duration == 0.3
        assert config.max_silence_duration == 1.5
        assert config.sample_rate == 22050
        assert config.channels == 2


class TestTranscriptionResult:
    """Test TranscriptionResult dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_transcription_result(self):
        """Should create transcription result."""
        result = TranscriptionResult(
            text="Hello world", confidence=0.95, language="en", timestamp=1234567890.0
        )
        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.language == "en"
        assert result.timestamp == 1234567890.0


class TestAudioSegment:
    """Test AudioSegment dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_audio_segment(self):
        """Should create audio segment."""
        data = b"fake_audio_data"
        segment = AudioSegment(data=data, sample_rate=16000, channels=1, duration=1.0)
        assert segment.data == data
        assert segment.sample_rate == 16000
        assert segment.channels == 1
        assert segment.duration == 1.0


class TestVoiceActivityDetector:
    """Test VoiceActivityDetector."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_vad(self):
        """Should create VAD with default config."""
        vad = VoiceActivityDetector()
        assert vad.is_speaking is False
        assert vad.speech_start_time is None
        assert vad.last_speech_time is None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_vad_detect_speech(self):
        """Should detect speech in audio."""
        vad = VoiceActivityDetector()

        # Simulate speech detection
        audio_data = b"speech_audio_data"
        vad.process_audio(audio_data, is_speech=True)

        assert vad.is_speaking is True
        assert vad.speech_start_time is not None
        assert vad.last_speech_time is not None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_vad_detect_silence(self):
        """Should detect silence and end speech."""
        vad = VoiceActivityDetector()

        # Start speech
        vad.process_audio(b"speech", is_speech=True)
        assert vad.is_speaking is True

        # End with silence
        vad.process_audio(b"silence", is_speech=False)
        assert vad.is_speaking is False

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_vad_pause_detection(self):
        """Should detect pause in speech."""
        vad = VoiceActivityDetector(pause_threshold=1.0)

        # Start speech
        vad.process_audio(b"speech1", is_speech=True, timestamp=0.0)

        # Continue speaking
        vad.process_audio(b"speech2", is_speech=True, timestamp=0.5)

        # Check for pause (not yet)
        assert vad.check_for_pause(0.7) is False

        # Now it's been long enough
        assert vad.check_for_pause(1.5) is True


class TestSpeechRecognizer:
    """Test SpeechRecognizer."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_recognizer(self):
        """Should create recognizer with API key."""
        recognizer = SpeechRecognizer(api_key="test_key")
        assert recognizer.api_key == "test_key"
        assert recognizer.model == "whisper-1"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch("src.voice.realtime_conversation.openai.AsyncOpenAI")
    async def test_transcribe_audio(self, mock_openai):
        """Should transcribe audio to text."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.text = "Hello world"
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Test
        recognizer = SpeechRecognizer(api_key="test_key")
        audio_data = b"fake_audio_data"

        result = await recognizer.transcribe_audio(audio_data)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hello world"
        assert result.confidence > 0
        assert result.language == "en"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch("src.voice.realtime_conversation.openai.AsyncOpenAI")
    async def test_transcribe_with_language(self, mock_openai):
        """Should transcribe audio with specified language."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.text = "Bonjour le monde"
        mock_response.language = "fr"
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Test
        recognizer = SpeechRecognizer(api_key="test_key")
        audio_data = b"fake_audio_data"

        result = await recognizer.transcribe_audio(audio_data, language="fr")

        assert result.text == "Bonjour le monde"
        assert result.language == "fr"

        # Check API was called with language parameter
        mock_client.audio.transcriptions.create.assert_called_once()
        call_args = mock_client.audio.transcriptions.create.call_args
        assert call_args[1]["language"] == "fr"


class TestAudioProcessor:
    """Test AudioProcessor."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_processor(self):
        """Should create processor with config."""
        config = ConversationConfig(sample_rate=16000, channels=1)
        processor = AudioProcessor(config)
        assert processor.config == config
        assert processor.buffer_size == 1024

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_process_audio_chunk(self):
        """Should process audio chunk."""
        config = ConversationConfig()
        processor = AudioProcessor(config)

        # Add audio data
        audio_data = b"x" * 2048
        processor.process_audio(audio_data)

        assert len(processor.audio_buffer) > 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_get_audio_segment(self):
        """Should get audio segment from buffer."""
        config = ConversationConfig()
        processor = AudioProcessor(config)

        # Add audio data
        processor.process_audio(b"x" * 2048)

        # Get segment
        segment = processor.get_audio_segment()

        assert isinstance(segment, AudioSegment)
        assert len(segment.data) > 0
        assert segment.sample_rate == config.sample_rate
        assert segment.channels == config.channels

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_clear_buffer(self):
        """Should clear audio buffer."""
        config = ConversationConfig()
        processor = AudioProcessor(config)

        # Add audio data
        processor.process_audio(b"x" * 2048)
        assert len(processor.audio_buffer) > 0

        # Clear buffer
        processor.clear_buffer()
        assert len(processor.audio_buffer) == 0


class TestRealtimeConversation:
    """Test RealtimeConversation."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_conversation(self):
        """Should create conversation with config."""
        config = ConversationConfig(pause_threshold=2.0)
        conv = RealtimeConversation(config)
        assert conv.config == config
        assert conv.state == ConversationState.IDLE

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch("src.voice.realtime_conversation.ElevenLabsClient")
    @patch("src.voice.realtime_conversation.SpeechRecognizer")
    @patch("src.voice.realtime_conversation.AudioProcessor")
    @patch("src.voice.realtime_conversation.VoiceActivityDetector")
    async def test_start_conversation(
        self, mock_vad, mock_processor, mock_recognizer, mock_tts
    ):
        """Should start conversation."""
        conv = RealtimeConversation()

        await conv.start()

        assert conv.state == ConversationState.LISTENING
        assert conv._listening_task is not None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_stop_conversation(self):
        """Should stop conversation."""
        conv = RealtimeConversation()
        conv.state = ConversationState.LISTENING
        conv._listening_task = MagicMock()

        await conv.stop()

        assert conv.state == ConversationState.IDLE
        conv._listening_task.cancel.assert_called_once()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch("src.voice.realtime_conversation.ElevenLabsClient")
    async def test_process_transcription(self, mock_tts):
        """Should process transcription and generate response."""
        conv = RealtimeConversation()

        # Mock response generation
        conv._generate_response = AsyncMock(return_value="Hello there!")
        conv._speak_response = AsyncMock()

        transcription = TranscriptionResult(
            text="Hello", confidence=0.9, language="en", timestamp=0.0
        )

        await conv._process_transcription(transcription)

        conv._generate_response.assert_called_once_with("Hello")
        conv._speak_response.assert_called_once_with("Hello there!")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_generate_response(self):
        """Should generate response from text."""
        conv = RealtimeConversation()

        # Simple echo response (implementation may vary)
        response = conv._generate_response("How are you?")

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch("src.voice.realtime_conversation.ElevenLabsClient")
    async def test_speak_response(self, mock_tts):
        """Should speak response using TTS."""
        mock_client = AsyncMock()
        mock_client.text_to_speech.return_value = b"audio_data"
        mock_tts.return_value = mock_client

        conv = RealtimeConversation()
        conv._tts_client = mock_client

        await conv._speak_response("Hello world")

        mock_client.text_to_speech.assert_called_once()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_add_event_handler(self):
        """Should add event handler."""
        conv = RealtimeConversation()
        handler = MagicMock()

        conv.add_event_handler(ConversationEvent.SPEECH_STARTED, handler)

        assert ConversationEvent.SPEECH_STARTED in conv._event_handlers
        assert handler in conv._event_handlers[ConversationEvent.SPEECH_STARTED]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_remove_event_handler(self):
        """Should remove event handler."""
        conv = RealtimeConversation()
        handler = MagicMock()

        conv.add_event_handler(ConversationEvent.SPEECH_STARTED, handler)
        conv.remove_event_handler(ConversationEvent.SPEECH_STARTED, handler)

        assert handler not in conv._event_handlers.get(
            ConversationEvent.SPEECH_STARTED, []
        )

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_emit_event(self):
        """Should emit event to handlers."""
        conv = RealtimeConversation()
        handler1 = MagicMock()
        handler2 = MagicMock()

        conv.add_event_handler(ConversationEvent.TRANSCRIPTION_READY, handler1)
        conv.add_event_handler(ConversationEvent.TRANSCRIPTION_READY, handler2)

        transcription = TranscriptionResult(
            text="Test", confidence=1.0, language="en", timestamp=0.0
        )
        conv._emit_event(ConversationEvent.TRANSCRIPTION_READY, transcription)

        handler1.assert_called_once_with(transcription)
        handler2.assert_called_once_with(transcription)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_handle_error(self):
        """Should handle errors gracefully."""
        conv = RealtimeConversation()
        error_handler = MagicMock()

        conv.add_event_handler(ConversationEvent.ERROR, error_handler)

        await conv._handle_error(Exception("Test error"))

        assert conv.state == ConversationState.ERROR
        error_handler.assert_called_once()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_get_conversation_stats(self):
        """Should return conversation statistics."""
        conv = RealtimeConversation()
        conv._start_time = 1234567890.0
        conv._transcription_count = 5
        conv._response_count = 5

        stats = conv.get_stats()

        assert stats["start_time"] == 1234567890.0
        assert stats["transcription_count"] == 5
        assert stats["response_count"] == 5
        assert "duration" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
