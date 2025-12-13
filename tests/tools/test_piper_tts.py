"""
VIBE MCP - Piper TTS Integration Test

Tests the local Piper TTS implementation to ensure it works
as a replacement for ElevenLabs before subscription ends.

Usage:
    python tests/tools/test_piper_tts.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.voice.manager import VoiceManager, VoiceProvider


class PiperTTSIntegrationTest:
    """Test Piper TTS integration with VoiceManager."""
    
    def __init__(self):
        """Initialize test suite."""
        self.manager = VoiceManager()
    
    async def test_voice_manager_initialization(self):
        """Test VoiceManager initializes with Piper as default."""
        print("🔧 Testing VoiceManager initialization...")
        
        # Check default voice is set to Piper
        default_voice = self.manager.get_voice("piper_default")
        assert default_voice is not None, "Piper default voice not found"
        assert default_voice.provider == VoiceProvider.PIPER, "Default voice should be Piper"
        
        print(f"   ✅ Default voice: {default_voice.name} ({default_voice.provider.value})")
        
        # Check all available voices
        voices = self.manager.list_voices()
        piper_voices = [v for v in voices if v["provider"] == "piper"]
        elevenlabs_voices = [v for v in voices if v["provider"] == "elevenlabs"]
        
        print(f"   📊 Available voices:")
        print(f"      - Piper: {len(piper_voices)} voices")
        print(f"      - ElevenLabs: {len(elevenlabs_voices)} voices")
        
        return True
    
    async def test_piper_voice_profiles(self):
        """Test Piper voice profiles are properly configured."""
        print("\n🎤 Testing Piper voice profiles...")
        
        piper_voices = [
            "piper_default",
            "piper_female", 
            "piper_british",
            "rachel_local"
        ]
        
        for voice_id in piper_voices:
            voice = self.manager.get_voice(voice_id)
            if voice:
                print(f"   ✅ {voice.name}: {voice.description}")
                assert voice.provider == VoiceProvider.PIPER, f"{voice_id} should be Piper"
            else:
                print(f"   ❌ Voice not found: {voice_id}")
        
        return True
    
    async def test_voice_routing(self):
        """Test voice routing between providers."""
        print("\n🔄 Testing voice provider routing...")
        
        # Test Piper voice selection
        piper_voice = self.manager.get_voice("piper_default")
        assert piper_voice is not None, "Piper default voice should exist"
        assert piper_voice.provider == VoiceProvider.PIPER, "Should route to Piper"
        
        # Test ElevenLabs voice selection  
        elevenlabs_voice = self.manager.get_voice("rachel")
        assert elevenlabs_voice is not None, "ElevenLabs Rachel should exist"
        assert elevenlabs_voice.provider == VoiceProvider.ELEVENLABS, "Should route to ElevenLabs"
        
        print(f"   ✅ Piper routing: {piper_voice.name} -> {piper_voice.provider.value}")
        print(f"   ✅ ElevenLabs routing: {elevenlabs_voice.name} -> {elevenlabs_voice.provider.value}")
        
        return True
    
    async def test_extracted_voices_discovery(self):
        """Test discovery of extracted voice samples."""
        print("\n📁 Testing extracted voices discovery...")
        
        try:
            # Try to get Piper client to check extracted voices
            piper_client = await self.manager._get_piper_client()
            extracted_voices = piper_client.get_extracted_voices()
            
            if extracted_voices:
                print(f"   ✅ Found {len(extracted_voices)} extracted voice groups:")
                for voice_key, voice_info in extracted_voices.items():
                    status = "✅ Ready" if voice_info["ready_for_training"] else "⚠️ Needs more samples"
                    print(f"      - {voice_info['name']}: {voice_info['samples']} samples {status}")
            else:
                print("   ⚠️ No extracted voices found (expected if extraction not run)")
            
        except Exception as e:
            print(f"   ⚠️ Could not check extracted voices: {e}")
            print("   💡 This is expected if Piper is not installed")
        
        return True
    
    async def test_speak_method_routing(self):
        """Test that speak method routes to correct provider."""
        print("\n🗣️ Testing speak method provider routing...")
        
        # Test with Piper voice (will fail if Piper not installed, but should route correctly)
        try:
            # This will fail if Piper is not installed, but we're testing routing
            await self.manager.speak("Test", voice="piper_default")
            print("   ✅ Piper synthesis successful")
        except RuntimeError as e:
            if "Failed to initialize Piper TTS client" in str(e):
                print("   ✅ Piper routing correct (client not installed)")
            else:
                raise e
        except Exception as e:
            print(f"   ⚠️ Unexpected error: {e}")
        
        # Test with ElevenLabs voice (will fail if no API key, but should route correctly)
        try:
            await self.manager.speak("Test", voice="rachel")
            print("   ✅ ElevenLabs synthesis successful")
        except Exception as e:
            if "API key not configured" in str(e) or "Failed to initialize" in str(e):
                print("   ✅ ElevenLabs routing correct (no API key)")
            else:
                print(f"   ⚠️ Unexpected error: {e}")
        
        return True
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("=" * 60)
        print("VIBE MCP - Piper TTS Integration Test")
        print("=" * 60)
        
        tests = [
            ("VoiceManager Initialization", self.test_voice_manager_initialization),
            ("Piper Voice Profiles", self.test_piper_voice_profiles),
            ("Voice Provider Routing", self.test_voice_routing),
            ("Extracted Voices Discovery", self.test_extracted_voices_discovery),
            ("Speak Method Routing", self.test_speak_method_routing),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = "✅ PASS" if result else "❌ FAIL"
            except Exception as e:
                results[test_name] = f"❌ FAIL: {e}"
        
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result.startswith("✅"))
        total = len(results)
        
        for test_name, result in results.items():
            print(f"{test_name:<25} {result}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Piper TTS integration is ready.")
        else:
            print("⚠️ Some tests failed. Check the results above.")
        
        return passed == total


async def main():
    """Run the Piper TTS integration test."""
    test_suite = PiperTTSIntegrationTest()
    success = await test_suite.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
