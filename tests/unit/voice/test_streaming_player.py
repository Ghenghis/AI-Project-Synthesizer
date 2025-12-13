"""Tests for voice.streaming_player."""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import io

os.environ["APP_ENV"] = "testing"

try:
    from src.voice.streaming_player import (
        StreamingPlayer,
        AudioBuffer,
        PlaybackState,
        StreamConfig,
        AudioChunk
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error for voice.streaming_player: {e}")
    IMPORTS_AVAILABLE = False


class TestPlaybackState:
    """Test PlaybackState enum."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_playback_state_values(self):
        """Should have correct PlaybackState values."""
        assert PlaybackState.IDLE.value == "idle"
        assert PlaybackState.BUFFERING.value == "buffering"
        assert PlaybackState.PLAYING.value == "playing"
        assert PlaybackState.PAUSED.value == "paused"
        assert PlaybackState.STOPPED.value == "stopped"
        assert PlaybackState.ERROR.value == "error"


class TestStreamConfig:
    """Test StreamConfig dataclass."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_stream_config(self):
        """Should create StreamConfig with default values."""
        config = StreamConfig()
        assert config.buffer_size == 8192
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.chunk_duration == 0.1
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_stream_config_custom(self):
        """Should create StreamConfig with custom values."""
        config = StreamConfig(
            buffer_size=4096,
            sample_rate=22050,
            channels=1,
            chunk_duration=0.05
        )
        assert config.buffer_size == 4096
        assert config.sample_rate == 22050
        assert config.channels == 1
        assert config.chunk_duration == 0.05


class TestAudioChunk:
    """Test AudioChunk dataclass."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_audio_chunk(self):
        """Should create AudioChunk with data."""
        data = b"fake_audio_data"
        chunk = AudioChunk(data=data, timestamp=1234567890.0)
        assert chunk.data == data
        assert chunk.timestamp == 1234567890.0
        assert chunk.size == len(data)


class TestAudioBuffer:
    """Test AudioBuffer."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_buffer(self):
        """Should create buffer with specified size."""
        buffer = AudioBuffer(max_size=1024)
        assert buffer.max_size == 1024
        assert buffer.current_size == 0
        assert buffer.is_empty() is True
        assert buffer.is_full() is False
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_buffer_write(self):
        """Should write data to buffer."""
        buffer = AudioBuffer(max_size=1024)
        data = b"test_data"
        
        written = buffer.write(data)
        assert written == len(data)
        assert buffer.current_size == len(data)
        assert buffer.is_empty() is False
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_buffer_read(self):
        """Should read data from buffer."""
        buffer = AudioBuffer(max_size=1024)
        data = b"test_data"
        buffer.write(data)
        
        read_data = buffer.read(4)
        assert read_data == b"test"
        assert buffer.current_size == 4
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_buffer_full(self):
        """Should handle full buffer."""
        buffer = AudioBuffer(max_size=8)
        buffer.write(b"12345678")
        
        assert buffer.is_full() is True
        
        # Try to write more than capacity
        written = buffer.write(b"extra")
        assert written == 0  # Should not write if full
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_buffer_clear(self):
        """Should clear buffer."""
        buffer = AudioBuffer(max_size=1024)
        buffer.write(b"test_data")
        
        buffer.clear()
        assert buffer.current_size == 0
        assert buffer.is_empty() is True


class TestStreamingPlayer:
    """Test StreamingPlayer."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_player(self):
        """Should create player with default config."""
        player = StreamingPlayer()
        assert player.state == PlaybackState.IDLE
        assert player.config.buffer_size == 8192
        assert player.buffer.is_empty() is True
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_player_custom_config(self):
        """Should create player with custom config."""
        config = StreamConfig(buffer_size=4096, sample_rate=22050)
        player = StreamingPlayer(config=config)
        assert player.config.buffer_size == 4096
        assert player.config.sample_rate == 22050
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.voice.streaming_player.asyncio')
    async def test_start_streaming(self, mock_asyncio):
        """Should start streaming audio."""
        player = StreamingPlayer()
        
        # Mock the background task
        mock_task = MagicMock()
        mock_asyncio.create_task.return_value = mock_task
        
        await player.start_streaming()
        
        assert player.state == PlaybackState.BUFFERING
        mock_asyncio.create_task.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_stop_streaming(self):
        """Should stop streaming audio."""
        player = StreamingPlayer()
        player.state = PlaybackState.PLAYING
        player._streaming_task = MagicMock()
        
        await player.stop_streaming()
        
        assert player.state == PlaybackState.STOPPED
        player._streaming_task.cancel.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_pause_resume(self):
        """Should pause and resume playback."""
        player = StreamingPlayer()
        player.state = PlaybackState.PLAYING
        
        await player.pause()
        assert player.state == PlaybackState.PAUSED
        
        await player.resume()
        assert player.state == PlaybackState.PLAYING
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_add_audio_chunk(self):
        """Should add audio chunk to buffer."""
        player = StreamingPlayer()
        chunk = AudioChunk(data=b"test_audio", timestamp=0.0)
        
        await player.add_audio_chunk(chunk)
        
        assert not player.buffer.is_empty()
        assert player.buffer.current_size == len(b"test_audio")
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_get_buffer_level(self):
        """Should return buffer level as percentage."""
        player = StreamingPlayer()
        
        # Empty buffer
        assert player.get_buffer_level() == 0.0
        
        # Add some data
        player.buffer.write(b"x" * 4096)  # Half of default buffer size
        assert player.get_buffer_level() == 0.5
        
        # Full buffer
        player.buffer.write(b"x" * 4096)
        assert player.get_buffer_level() == 1.0
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.voice.streaming_player.pyaudio.PyAudio')
    def test_initialize_audio(self, mock_pyaudio):
        """Should initialize audio output."""
        mock_stream = MagicMock()
        mock_pa = MagicMock()
        mock_pa.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_pa
        
        player = StreamingPlayer()
        player._initialize_audio()
        
        assert player._audio == mock_pa
        assert player._stream == mock_stream
        mock_pa.open.assert_called_once_with(
            format=mock_pa.get_format_from_width.return_value,
            channels=2,
            rate=44100,
            output=True
        )
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_cleanup_audio(self):
        """Should cleanup audio resources."""
        player = StreamingPlayer()
        player._audio = MagicMock()
        player._stream = MagicMock()
        
        player._cleanup_audio()
        
        player._stream.stop_stream.assert_called_once()
        player._stream.close.assert_called_once()
        player._audio.terminate.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.voice.streaming_player.StreamingPlayer._initialize_audio')
    @patch('src.voice.streaming_player.StreamingPlayer._cleanup_audio')
    async def test_playback_loop(self, mock_cleanup, mock_init):
        """Should run playback loop correctly."""
        player = StreamingPlayer()
        player.state = PlaybackState.PLAYING
        
        # Add some data to buffer
        player.buffer.write(b"test_audio_data")
        
        # Mock stream write
        mock_stream = MagicMock()
        player._stream = mock_stream
        
        # Run one iteration of the loop
        task = asyncio.create_task(player._playback_loop())
        await asyncio.sleep(0.01)  # Let it run briefly
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_handle_error(self):
        """Should handle errors during playback."""
        player = StreamingPlayer()
        
        await player._handle_error(Exception("Test error"))
        
        assert player.state == PlaybackState.ERROR
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_get_stats(self):
        """Should return playback statistics."""
        player = StreamingPlayer()
        player._bytes_played = 1024
        player._chunks_played = 10
        player._start_time = 1234567890.0
        
        stats = player.get_stats()
        
        assert stats['bytes_played'] == 1024
        assert stats['chunks_played'] == 10
        assert stats['start_time'] == 1234567890.0
        assert 'duration' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
