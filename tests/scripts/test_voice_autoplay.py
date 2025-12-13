"""Test voice auto-play for LM Studio integration."""
import asyncio


async def test():
    print("=== Testing Voice Auto-Play (LM Studio Integration) ===\n")

    from src.mcp_server.tools import handle_assistant_voice

    # Test with auto-play enabled (default for LM Studio)
    result = await handle_assistant_voice({
        "text": "Hello! This is a test of the auto-play feature for LM Studio.",
        "voice": "rachel",
        "auto_play": True,
    })

    if result.get("success"):
        print("✅ Voice generated!")
        print(f"   Voice: {result['voice']}")
        print(f"   Audio size: {result['audio_size_bytes']:,} bytes")
        print(f"   Playback status: {result['playback_status']}")
        if result.get("note"):
            print(f"   Note: {result['note']}")
    else:
        print(f"❌ Error: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(test())
