"""Test fast streaming voice - optimized for speed and smooth playback."""

import asyncio
import time


async def test():
    print("=== Testing FAST Streaming Voice ===\n")
    print("This uses turbo model + streaming for lowest latency.\n")

    from src.voice.streaming_player import speak_fast

    text = "Hello! This is a test of the fast streaming voice. Notice how the audio starts playing immediately without waiting for the full generation. This creates smooth, natural speech without any gaps or pauses."

    print(f"Speaking: '{text[:50]}...'\n")

    start = time.time()
    success = await speak_fast(text, voice="rachel")
    elapsed = time.time() - start

    if success:
        print("\n✅ Streaming complete!")
        print(f"   Total time: {elapsed:.2f}s")
        print("   Mode: Streaming (audio plays as it generates)")
        print("   Model: eleven_turbo_v2_5 (fastest)")
    else:
        print("\n❌ Streaming failed")


if __name__ == "__main__":
    asyncio.run(test())
