"""Test the full system - Assistant + Voice + Search."""

import asyncio
from pathlib import Path


async def test_voice():
    """Test ElevenLabs voice generation."""
    print("=== Testing Voice (ElevenLabs) ===\n")

    from src.voice.elevenlabs_client import PREMADE_VOICES, ElevenLabsClient

    # Show available voices
    print("Available voices:")
    for name, voice in PREMADE_VOICES.items():
        print(f"  - {name}: {voice.description}")
    print()

    client = ElevenLabsClient()

    # Test TTS
    text = (
        "Hello! I'm your AI assistant. I can help you find and build amazing projects."
    )
    print(f"Generating voice for: '{text}'")

    try:
        audio = await client.text_to_speech(text, voice="rachel")

        # Save to file
        output_path = Path("test_output.mp3")
        output_path.write_bytes(audio)
        print(f"✅ Voice generated! Saved to {output_path} ({len(audio):,} bytes)")
        print(f"   Play with: start {output_path}")

        await client.close()
        return True
    except Exception as e:
        print(f"❌ Voice error: {e}")
        return False


async def test_search():
    """Test multi-platform search."""
    print("\n=== Testing Search (GitHub + HuggingFace + Kaggle) ===\n")

    from src.discovery.unified_search import create_unified_search

    search = create_unified_search()
    print(f"Available platforms: {search.available_platforms}")

    # Search all platforms
    result = await search.search(
        query="machine learning",
        platforms=None,  # All platforms
        max_results=3,
    )

    print(f"\nFound {len(result.repositories)} results across platforms:")
    for repo in result.repositories:
        print(f"  [{repo.platform}] {repo.full_name}: {repo.stars} ⭐")

    return len(result.repositories) > 0


async def test_assistant():
    """Test conversational assistant."""
    print("\n=== Testing Assistant ===\n")

    from src.assistant.core import AssistantConfig, ConversationalAssistant

    # Test without voice first
    config = AssistantConfig(voice_enabled=False)
    assistant = ConversationalAssistant(config)

    # Conversation flow
    messages = [
        "Hello!",
        "I want to build a Discord bot",
        "With AI chat capabilities using a local LLM",
    ]

    for msg in messages:
        print(f"You: {msg}")
        response = await assistant.chat(msg)
        print(f"Assistant: {response['text'][:200]}...")
        print(f"Actions: {response['actions']}\n")

    return True


async def test_assistant_with_voice():
    """Test assistant with voice enabled."""
    print("\n=== Testing Assistant WITH Voice ===\n")

    from src.assistant.core import AssistantConfig, ConversationalAssistant

    config = AssistantConfig(
        voice_enabled=True,
        auto_speak=True,
        voice_id="josh",  # Deep, narrative voice
    )
    assistant = ConversationalAssistant(config)

    response = await assistant.chat("Tell me about yourself in one sentence.")

    if response.get("audio"):
        output_path = Path("assistant_voice.mp3")
        output_path.write_bytes(response["audio"])
        print(f"✅ Assistant spoke! Audio saved to {output_path}")
        print(f"   Text: {response['text']}")
    else:
        print(f"Assistant (text only): {response['text']}")

    return True


async def test_mcp_tools():
    """Test MCP tool handlers."""
    print("\n=== Testing MCP Tools ===\n")

    from src.mcp_server.tools import (
        handle_assistant_chat,
        handle_get_voices,
    )

    # Test get_voices
    voices = await handle_get_voices({})
    print(f"Available voices: {[v['name'] for v in voices['voices']]}")

    # Test assistant_chat
    result = await handle_assistant_chat(
        {
            "message": "Search for Python web frameworks on GitHub",
            "voice_enabled": False,
        }
    )

    if result.get("success"):
        print("✅ MCP assistant_chat works!")
        print(f"   Response preview: {result['response'][:150]}...")
    else:
        print(f"❌ Error: {result.get('message')}")

    return result.get("success", False)


async def main():
    print("=" * 60)
    print("AI PROJECT SYNTHESIZER - FULL SYSTEM TEST")
    print("=" * 60)

    results = {}

    # Test 1: Voice
    results["voice"] = await test_voice()

    # Test 2: Search
    results["search"] = await test_search()

    # Test 3: Assistant (text)
    results["assistant"] = await test_assistant()

    # Test 4: Assistant with voice
    results["assistant_voice"] = await test_assistant_with_voice()

    # Test 5: MCP Tools
    results["mcp_tools"] = await test_mcp_tools()

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test}: {status}")

    all_passed = all(results.values())
    print(
        f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
