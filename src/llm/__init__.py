"""
AI Project Synthesizer - LLM Orchestration Layer

Manages multiple LLM providers including:
- Local: Ollama, LM Studio, LocalAI, vLLM, Text Generation WebUI, KoboldAI, llama.cpp
- Cloud: OpenAI, Anthropic, Groq, Together, OpenRouter, Mistral, DeepSeek, Cohere, Fireworks
"""

# LiteLLM unified router
from src.llm.litellm_router import (
    LiteLLMRouter,
    RouterConfig,
    TaskType,
    get_litellm_router,
)
from src.llm.lmstudio_client import LMStudioClient
from src.llm.ollama_client import OllamaClient

# New provider system
from src.llm.providers import (
    CompletionResult,
    LLMProvider,
    ProviderCapabilities,
    ProviderConfig,
    ProviderRegistry,
    ProviderStatus,
    get_provider_registry,
)
from src.llm.router import LLMRouter, ProviderType, TaskComplexity

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
    # LiteLLM unified router
    "LiteLLMRouter",
    "TaskType",
    "RouterConfig",
    "get_litellm_router",
]
