"""
Start Real-Time Voice Chat

Speak naturally, pause for 3.5 seconds, AI responds with voice.
Continuous back-and-forth conversation.

Usage:
    python start_voice_chat.py
    python start_voice_chat.py --pause 2.0 --voice josh
"""

import asyncio
import argparse

async def main(pause_threshold: float, voice: str):
    from src.voice.realtime_conversation import start_voice_chat
    
    def on_user(text):
        print(f"\n🎤 You: {text}")
    
    def on_ai(text):
        print(f"\n🤖 AI: {text[:200]}{'...' if len(text) > 200 else ''}")
    
    await start_voice_chat(
        pause_threshold=pause_threshold,
        voice=voice,
        on_user_speech=on_user,
        on_assistant_response=on_ai,
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time voice chat with AI")
    parser.add_argument("--pause", type=float, default=3.5, help="Seconds of silence before AI responds")
    parser.add_argument("--voice", type=str, default="rachel", help="Voice: rachel, josh, adam, bella, etc.")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("AI PROJECT SYNTHESIZER - VOICE CHAT")
    print("=" * 50)
    print(f"\nSettings:")
    print(f"  Pause threshold: {args.pause}s")
    print(f"  Voice: {args.voice}")
    print(f"\nRequirements:")
    print(f"  - Microphone connected")
    print(f"  - LM Studio running (for AI)")
    print(f"  - ElevenLabs API key configured")
    
    asyncio.run(main(args.pause, args.voice))
