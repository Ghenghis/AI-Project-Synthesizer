"""
AI Project Synthesizer - Conversational Assistant

The intelligent assistant that talks to users via voice + text,
asks clarifying questions, and completes tasks.
"""

from src.assistant.core import (
    ConversationalAssistant,
    AssistantConfig,
    AssistantState,
    TaskType,
    Message,
    TaskContext,
    get_assistant,
)

__all__ = [
    "ConversationalAssistant",
    "AssistantConfig",
    "AssistantState",
    "TaskType",
    "Message",
    "TaskContext",
    "get_assistant",
]
