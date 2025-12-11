"""
AI Project Synthesizer - LLM Provider Registry

Unified interface for multiple LLM providers including:
- Ollama (local)
- LM Studio (local, OpenAI-compatible)
- OpenAI (cloud)
- Anthropic (cloud)
- Groq (cloud, fast inference)
- Together AI (cloud)
- OpenRouter (cloud, multi-model)
- Local AI (self-hosted)
- Text Generation WebUI (local)
- vLLM (local/cloud)
- Kobold AI (local)
"""

from src.llm.providers.base import (
    LLMProvider,
    ProviderConfig,
    CompletionResult,
    ProviderCapabilities,
    ProviderStatus,
)
from src.llm.providers.registry import ProviderRegistry, get_provider_registry

__all__ = [
    "LLMProvider",
    "ProviderConfig", 
    "CompletionResult",
    "ProviderCapabilities",
    "ProviderStatus",
    "ProviderRegistry",
    "get_provider_registry",
]
