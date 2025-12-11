"""Test the conversational assistant."""
import asyncio
from src.assistant.core import ConversationalAssistant, AssistantConfig

async def test():
    print("=== Testing Conversational Assistant ===\n")
    
    # Create assistant with voice disabled for testing
    config = AssistantConfig(voice_enabled=False)
    assistant = ConversationalAssistant(config)
    
    # Test conversations
    conversations = [
        "Hello!",
        "I want to build a chatbot",
        "Discord bot with AI capabilities",
        "Find me machine learning projects on GitHub",
    ]
    
    for msg in conversations:
        print(f"User: {msg}")
        response = await assistant.chat(msg)
        print(f"Assistant: {response['text']}\n")
        print(f"Suggested actions: {response['actions']}\n")
        print("-" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(test())
