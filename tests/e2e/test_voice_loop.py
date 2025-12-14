"""
E2E Voice Loop Tests

End-to-end tests for the complete voice system including ASR, TTS, and VoiceManager.
Implements Phase 6.2 of the VIBE MCP roadmap.
"""

import asyncio
import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pytest
import soundfile as sf

from src.voice.manager import VoiceManager
from src.voice.tts.piper_client import PiperTTSClient

# Mock problematic imports for GLM ASR
try:
    from src.voice.asr.glm_asr_client import GLMASRClient

    GLM_ASR_AVAILABLE = True
except (ImportError, RuntimeError, ModuleNotFoundError) as e:
    GLM_ASR_AVAILABLE = False
    GLMASRClient = None
    print(f"Warning: GLM ASR not available: {e}")

# Check if Piper TTS is available
PIPER_AVAILABLE = False
try:
    import os

    # Try to create a client to check if binary is available
    import tempfile

    from src.voice.tts.piper_client import PiperTTSClient

    client = PiperTTSClient()
    # Check if piper binary exists
    if os.path.exists(client.piper_path) or shutil.which("piper"):
        PIPER_AVAILABLE = True
    else:
        print(f"Warning: Piper binary not found at {client.piper_path}")
except (ImportError, RuntimeError, ModuleNotFoundError, Exception) as e:
    print(f"Warning: Piper TTS not available: {e}")
    PiperTTSClient = None
from src.llm.litellm_router import LiteLLMRouter, TaskType


class TestVoiceLoop:
    """Test complete voice loop functionality."""

    @pytest.fixture
    async def voice_manager(self):
        """Create voice manager for testing."""
        manager = VoiceManager()
        yield manager
        # No cleanup method available

    @pytest.fixture
    @pytest.mark.skipif(not PIPER_AVAILABLE, reason="Piper TTS not available")
    async def piper_client(self):
        """Create Piper TTS client for testing."""
        client = PiperTTSClient()
        await client.initialize()
        yield client
        # No cleanup method available

    @pytest.fixture
    @pytest.mark.skipif(
        not GLM_ASR_AVAILABLE,
        reason="GLM ASR not available due to missing dependencies",
    )
    async def asr_client(self):
        """Create GLM ASR client for testing."""
        client = GLMASRClient()
        await client.initialize()
        yield client
        await client.cleanup()

    @pytest.fixture
    def test_audio_file(self):
        """Create a test audio file."""
        # Generate a simple sine wave for testing
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * frequency * t) * 0.5

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, sample_rate)
            yield f.name

        # Cleanup
        os.unlink(f.name)

    @pytest.fixture
    def sample_text(self):
        """Sample text for TTS testing."""
        return "Hello, this is a test of the voice system. The quick brown fox jumps over the lazy dog."

    # ========================================================================
    # TTS TESTS
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PIPER_AVAILABLE, reason="Piper TTS not available")
    async def test_piper_tts_basic(self, piper_client, sample_text):
        """Test basic Piper TTS functionality."""
        # Generate speech
        audio_data = await piper_client.synthesize(sample_text)

        assert audio_data is not None
        assert len(audio_data) > 0
        assert isinstance(audio_data, np.ndarray)
        assert audio_data.dtype == np.float32

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PIPER_AVAILABLE, reason="Piper TTS not available")
    async def test_piper_tts_save_to_file(self, piper_client, sample_text):
        """Test saving TTS output to file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        try:
            # Generate speech and save manually
            audio_data = await piper_client.synthesize(sample_text)

            # Save to file using soundfile
            sf.write(
                output_path,
                np.frombuffer(audio_data, dtype=np.float32),
                piper_client.sample_rate,
            )

            assert os.path.exists(output_path)

            # Verify file contents
            audio, sample_rate = sf.read(output_path)
            assert len(audio) > 0
            assert sample_rate == piper_client.sample_rate

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PIPER_AVAILABLE, reason="Piper TTS not available")
    async def test_piper_tts_voices(self, piper_client):
        """Test different voice options."""
        voices = await piper_client.get_available_voices()

        assert len(voices) > 0

        # Test with first available voice
        if voices:
            voice_name = list(voices.keys())[0]
            audio = await piper_client.synthesize("Testing voice", voice=voice_name)

            assert audio is not None
            assert len(audio) > 0

    # ========================================================================
    # ASR TESTS
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not GLM_ASR_AVAILABLE,
        reason="GLM ASR not available due to missing dependencies",
    )
    async def test_glm_asr_basic(self, asr_client, test_audio_file):
        """Test basic GLM ASR functionality."""
        # Transcribe audio
        result = await asr_client.transcribe_file(test_audio_file)

        assert result is not None
        assert "text" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not GLM_ASR_AVAILABLE,
        reason="GLM ASR not available due to missing dependencies",
    )
    async def test_glm_asr_with_timestamps(self, asr_client, test_audio_file):
        """Test ASR with timestamp extraction."""
        result = await asr_client.transcribe_file(
            test_audio_file, include_timestamps=True
        )

        assert result is not None
        assert "text" in result
        assert "segments" in result

        if result["segments"]:
            segment = result["segments"][0]
            assert "start" in segment
            assert "end" in segment
            assert "text" in segment

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not GLM_ASR_AVAILABLE,
        reason="GLM ASR not available due to missing dependencies",
    )
    async def test_glm_asr_streaming(self, asr_client):
        """Test streaming ASR."""
        # Generate test audio chunks
        sample_rate = 16000
        chunk_duration = 0.5  # 500ms chunks
        chunk_samples = int(sample_rate * chunk_duration)

        # Create test audio
        t = np.linspace(0, chunk_duration, chunk_samples)
        audio_chunk = np.sin(2 * np.pi * 440 * t) * 0.5

        transcriptions = []

        async for result in asr_client.transcribe_stream(
            [audio_chunk for _ in range(4)]
        ):
            assert "text" in result
            transcriptions.append(result["text"])

        # Verify we got transcriptions
        assert len(transcriptions) > 0

    # ========================================================================
    # VOICE MANAGER TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_voice_manager_initialization(self, voice_manager):
        """Test voice manager initialization."""
        assert voice_manager._tts_clients is not None
        assert voice_manager._asr_clients is not None
        assert len(voice_manager._tts_clients) > 0
        assert len(voice_manager._asr_clients) > 0

    @pytest.mark.asyncio
    async def test_voice_manager_tts_fallback(self, voice_manager, sample_text):
        """Test TTS provider fallback."""
        # Try to synthesize with fallback
        audio = await voice_manager.synthesize(sample_text)

        assert audio is not None
        assert len(audio) > 0

    @pytest.mark.asyncio
    async def test_voice_manager_asr_fallback(self, voice_manager, test_audio_file):
        """Test ASR provider fallback."""
        # Try to transcribe with fallback
        result = await voice_manager.transcribe(test_audio_file)

        assert result is not None
        assert "text" in result
        assert "provider" in result

    @pytest.mark.asyncio
    async def test_voice_manager_provider_selection(self, voice_manager):
        """Test explicit provider selection."""
        # Test with specific providers
        providers = await voice_manager.list_providers()

        if "piper" in providers["tts"]:
            audio = await voice_manager.synthesize("Test", tts_provider="piper")
            assert audio is not None

        if "glm_asr" in providers["asr"]:
            result = await voice_manager.transcribe(
                test_audio_file, asr_provider="glm_asr"
            )
            assert result is not None

    # ========================================================================
    # END-TO-END VOICE LOOP TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_complete_voice_loop_text_to_speech(self, voice_manager):
        """Test text to speech in the voice loop."""
        input_text = "This is a test of the complete voice system."

        # Step 1: Text to Speech
        audio = await voice_manager.synthesize(input_text)

        assert audio is not None
        assert len(audio) > 0

        # Step 2: Save and verify
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, 16000)

            # Verify the file
            verify_audio, sr = sf.read(f.name)
            assert len(verify_audio) > 0
            assert sr == 16000

            os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_complete_voice_loop_speech_to_text(
        self, voice_manager, test_audio_file
    ):
        """Test speech to text in the voice loop."""
        # Step 1: Speech to Text
        result = await voice_manager.transcribe(test_audio_file)

        assert result is not None
        assert "text" in result
        assert "provider" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_voice_loop_with_llm(self, voice_manager):
        """Test voice loop integrated with LLM."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key provided")

        # Create LLM router
        llm_router = LiteLLMRouter()

        # Step 1: User input (text for this test)
        user_input = "What is Python?"

        # Step 2: Get LLM response
        llm_response = await llm_router.complete(
            prompt=user_input, task_type=TaskType.SIMPLE, max_tokens=100
        )

        assert llm_response.content is not None

        # Step 3: Convert response to speech
        audio = await voice_manager.synthesize(llm_response.content)

        assert audio is not None
        assert len(audio) > 0

        # Step 4: Save the response
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, 16000)
            os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_voice_loop_conversation(self, voice_manager):
        """Test a multi-turn conversation through voice."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key provided")

        llm_router = LiteLLMRouter()
        conversation_history = []

        # Simulate conversation turns
        user_inputs = [
            "Hello, can you help me?",
            "What is machine learning?",
            "Can you give me an example?",
        ]

        for user_input in user_inputs:
            # Add to history
            conversation_history.append({"role": "user", "content": user_input})

            # Get LLM response
            llm_response = await llm_router.chat(
                messages=conversation_history, task_type=TaskType.SIMPLE, max_tokens=50
            )

            # Add response to history
            conversation_history.append(
                {"role": "assistant", "content": llm_response.content}
            )

            # Convert to speech
            audio = await voice_manager.synthesize(llm_response.content)

            assert audio is not None
            assert len(audio) > 0

            # Simulate processing delay
            await asyncio.sleep(0.1)

        # Verify conversation
        assert len(conversation_history) == 6  # 3 user + 3 assistant

    @pytest.mark.asyncio
    async def test_voice_loop_performance(self, voice_manager, sample_text):
        """Test voice loop performance metrics."""
        # Measure TTS latency
        start_time = time.time()
        audio = await voice_manager.synthesize(sample_text)
        tts_latency = time.time() - start_time

        assert tts_latency < 5.0  # Should complete within 5 seconds
        assert len(audio) > 0

        # Calculate real-time factor
        audio_duration = len(audio) / 16000  # Assuming 16kHz sample rate
        rtf = tts_latency / audio_duration

        # RTF should be less than 1 (faster than real-time)
        assert rtf < 1.0

        print(f"TTS Latency: {tts_latency:.2f}s")
        print(f"Audio Duration: {audio_duration:.2f}s")
        print(f"Real-Time Factor: {rtf:.2f}")

    @pytest.mark.asyncio
    async def test_voice_loop_error_handling(self, voice_manager):
        """Test error handling in voice loop."""
        # Test with invalid audio file
        with pytest.raises(Exception):
            await voice_manager.transcribe("nonexistent.wav")

        # Test with empty text
        audio = await voice_manager.synthesize("")
        # Should handle gracefully (either return empty or minimal audio)
        assert audio is not None

        # Test with very long text
        long_text = "Test " * 1000
        audio = await voice_manager.synthesize(long_text)
        assert audio is not None
        assert len(audio) > 0

    @pytest.mark.asyncio
    async def test_voice_loop_concurrent_requests(self, voice_manager):
        """Test handling concurrent voice requests."""
        texts = [
            "First test message",
            "Second test message",
            "Third test message",
        ]

        # Process multiple requests concurrently
        tasks = [voice_manager.synthesize(text) for text in texts]

        results = await asyncio.gather(*tasks)

        # Verify all results
        assert len(results) == len(texts)
        for audio in results:
            assert audio is not None
            assert len(audio) > 0

    @pytest.mark.asyncio
    async def test_voice_loop_quality_metrics(self, voice_manager, sample_text):
        """Test voice quality metrics."""
        # Generate audio
        audio = await voice_manager.synthesize(sample_text)

        # Basic quality checks
        assert audio is not None
        assert len(audio) > 0

        # Check audio properties
        assert np.max(np.abs(audio)) <= 1.0  # Should not clip
        assert np.std(audio) > 0.01  # Should have some variance

        # Check for silence at beginning/end
        silence_threshold = 0.01
        start_silence = np.sum(np.abs(audio[:100]) < silence_threshold) / 100
        end_silence = np.sum(np.abs(audio[-100:]) < silence_threshold) / 100

        # Should not be completely silent
        assert start_silence < 1.0
        assert end_silence < 1.0


# Voice loop test runner
class VoiceLoopTestRunner:
    """Runner for voice loop tests with detailed reporting."""

    def __init__(self):
        self.results: list[dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    async def run_voice_loop_tests(self) -> dict[str, Any]:
        """Run all voice loop tests."""
        self.start_time = datetime.now()

        print("\n" + "=" * 80)
        print("VIBE MCP - Voice Loop E2E Test Suite")
        print(f"Started at: {self.start_time}")
        print("=" * 80)

        test_results = {
            "start_time": self.start_time.isoformat(),
            "tests": [],
            "summary": {},
        }

        # Test categories
        test_categories = [
            ("TTS Tests", self._run_tts_tests),
            ("ASR Tests", self._run_asr_tests),
            ("Voice Manager Tests", self._run_voice_manager_tests),
            ("E2E Voice Loop Tests", self._run_e2e_tests),
        ]

        for category_name, test_func in test_categories:
            print(f"\n{'=' * 60}")
            print(f"Running {category_name}")
            print(f"{'=' * 60}")

            try:
                category_results = await test_func()
                test_results["tests"].extend(category_results)
                print(f"\n✓ {category_name} completed")
            except Exception as e:
                print(f"\n✗ {category_name} failed: {e}")
                test_results["tests"].append(
                    {
                        "category": category_name,
                        "status": "FAILED",
                        "error": str(e),
                    }
                )

        self.end_time = datetime.now()

        # Generate summary
        total_tests = len(test_results["tests"])
        passed_tests = sum(
            1 for t in test_results["tests"] if t.get("status") == "PASSED"
        )
        failed_tests = total_tests - passed_tests

        test_results["end_time"] = self.end_time.isoformat()
        test_results["duration"] = (self.end_time - self.start_time).total_seconds()
        test_results["summary"] = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100)
            if total_tests > 0
            else 0,
        }

        return test_results

    async def _run_tts_tests(self) -> list[dict[str, Any]]:
        """Run TTS-specific tests."""
        results = []

        # Test basic TTS
        try:
            client = PiperTTSClient()
            await client.initialize()

            audio = await client.synthesize("Test message")
            assert audio is not None and len(audio) > 0

            results.append(
                {
                    "name": "Basic TTS",
                    "status": "PASSED",
                    "duration": 0.5,
                }
            )

            await client.cleanup()

        except Exception as e:
            results.append(
                {
                    "name": "Basic TTS",
                    "status": "FAILED",
                    "error": str(e),
                }
            )

        return results

    async def _run_asr_tests(self) -> list[dict[str, Any]]:
        """Run ASR-specific tests."""
        results = []

        # Test basic ASR
        try:
            client = GLMASRClient()
            await client.initialize()

            # Create test audio
            sample_rate = 16000
            duration = 1.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = np.sin(2 * np.pi * 440 * t) * 0.5

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, audio, sample_rate)

                result = await client.transcribe_file(f.name)
                assert result is not None
                assert "text" in result

                os.unlink(f.name)

            results.append(
                {
                    "name": "Basic ASR",
                    "status": "PASSED",
                    "duration": 1.0,
                }
            )

            await client.cleanup()

        except Exception as e:
            results.append(
                {
                    "name": "Basic ASR",
                    "status": "FAILED",
                    "error": str(e),
                }
            )

        return results

    async def _run_voice_manager_tests(self) -> list[dict[str, Any]]:
        """Run voice manager tests."""
        results = []

        try:
            manager = VoiceManager()
            await manager.initialize()

            # Test provider listing
            providers = await manager.list_providers()
            assert "tts" in providers
            assert "asr" in providers

            results.append(
                {
                    "name": "Voice Manager Initialization",
                    "status": "PASSED",
                    "duration": 0.5,
                }
            )

            # Test synthesis
            audio = await manager.synthesize("Test synthesis")
            assert audio is not None and len(audio) > 0

            results.append(
                {
                    "name": "Voice Manager Synthesis",
                    "status": "PASSED",
                    "duration": 1.0,
                }
            )

            await manager.cleanup()

        except Exception as e:
            results.append(
                {
                    "name": "Voice Manager Tests",
                    "status": "FAILED",
                    "error": str(e),
                }
            )

        return results

    async def _run_e2e_tests(self) -> list[dict[str, Any]]:
        """Run end-to-end tests."""
        results = []

        try:
            manager = VoiceManager()
            await manager.initialize()

            # Test complete loop
            input_text = "Testing the complete voice loop from text to speech and back."

            # Text to speech
            audio = await manager.synthesize(input_text)
            assert audio is not None

            # Save and transcribe back
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, audio, 16000)

                result = await manager.transcribe(f.name)
                assert result is not None

                os.unlink(f.name)

            results.append(
                {
                    "name": "Complete Voice Loop",
                    "status": "PASSED",
                    "duration": 2.0,
                }
            )

            # Test performance
            start_time = time.time()
            audio = await manager.synthesize("Performance test message")
            latency = time.time() - start_time

            assert latency < 5.0

            results.append(
                {
                    "name": "Voice Loop Performance",
                    "status": "PASSED",
                    "duration": latency,
                    "metrics": {"latency": latency},
                }
            )

            await manager.cleanup()

        except Exception as e:
            results.append(
                {
                    "name": "E2E Tests",
                    "status": "FAILED",
                    "error": str(e),
                }
            )

        return results


# Main test runner
async def main():
    """Run voice loop E2E tests."""
    runner = VoiceLoopTestRunner()

    # Run tests
    results = await runner.run_voice_loop_tests()

    # Print summary
    print("\n" + "=" * 80)
    print("VOICE LOOP TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Duration: {results['duration']:.2f} seconds")

    # Save results
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"voice_loop_test_report_{timestamp}.json"

    with open(report_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed report saved to: {report_file}")

    return results["summary"]["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
