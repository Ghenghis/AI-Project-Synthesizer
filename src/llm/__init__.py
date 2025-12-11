"""
AI Project Synthesizer - LLM Orchestration Layer

Manages multiple LLM providers including:
- Local: Ollama, LM Studio, LocalAI, vLLM, Text Generation WebUI, KoboldAI, llama.cpp
- Cloud: OpenAI, Anthropic, Groq, Together, OpenRouter, Mistral, DeepSeek, Cohere, Fireworks
"""

from src.llm.ollama_client import OllamaClient
from src.llm.lmstudio_client import LMStudioClient
from src.llm.router import LLMRouter, TaskComplexity, ProviderType

# New provider system
from src.llm.providers import (
    LLMProvider,
    ProviderConfig,
    CompletionResult,
    ProviderCapabilities,
    ProviderStatus,
    ProviderRegistry,
    get_provider_registry,
)

__all__ = [
    # Legacy clients
    "OllamaClient",
    "LMStudioClient",
    "LLMRouter",
    "TaskComplexity",
    "ProviderType",

    # New provider system
    "LLMProvider",
    "ProviderConfig",
    "CompletionResult",
    "ProviderCapabilities",
    "ProviderStatus",
    "ProviderRegistry",
    "get_provider_registry",
]
