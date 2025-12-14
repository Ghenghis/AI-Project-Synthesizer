"""
AI Project Synthesizer - Base LLM Provider Interface

Abstract base class and common types for all LLM providers.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderType(Enum):
    """Supported LLM provider types."""

    # Local Providers
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    LMSTUDIO_MCP = "lmstudio_mcp"
    LOCALAI = "localai"
    TEXTGEN_WEBUI = "textgen_webui"
    VLLM = "vllm"
    KOBOLDAI = "koboldai"
    LLAMACPP = "llamacpp"

    # Cloud Providers
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    TOGETHER = "together"
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"
    COHERE = "cohere"
    FIREWORKS = "fireworks"
    DEEPSEEK = "deepseek"

    # Generic OpenAI-Compatible
    OPENAI_COMPATIBLE = "openai_compatible"


class ProviderStatus(Enum):
    """Provider health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderCapabilities:
    """Capabilities supported by a provider."""

    streaming: bool = True
    function_calling: bool = False
    vision: bool = False
    embeddings: bool = False
    code_completion: bool = True
    chat: bool = True
    max_context_length: int = 8192
    supports_system_prompt: bool = True
    supports_json_mode: bool = False


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    provider_type: ProviderType
    name: str
    host: str
    api_key: str | None = None
    default_model: str | None = None
    timeout: float = 120.0
    max_retries: int = 3
    enabled: bool = True
    priority: int = 0  # Lower = higher priority for fallback

    # Model size tiers
    model_tiny: str | None = None
    model_small: str | None = None
    model_medium: str | None = None
    model_large: str | None = None

    # Additional settings
    extra_headers: dict[str, str] = field(default_factory=dict)
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionResult:
    """Result from LLM completion."""

    content: str
    model: str
    provider: str
    tokens_used: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"
    duration_ms: int = 0
    cached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    """Chunk from streaming completion."""

    content: str
    finish_reason: str | None = None
    is_final: bool = False


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration."""
        self.config = config
        self.capabilities = ProviderCapabilities()
        self._last_health_check: float = 0
        self._health_status: ProviderStatus = ProviderStatus.UNKNOWN

    @property
    def name(self) -> str:
        """Provider name."""
        return self.config.name

    @property
    def provider_type(self) -> ProviderType:
        """Provider type."""
        return self.config.provider_type

    @property
    def is_local(self) -> bool:
        """Whether this is a local provider."""
        local_types = {
            ProviderType.OLLAMA,
            ProviderType.LMSTUDIO,
            ProviderType.LMSTUDIO_MCP,
            ProviderType.LOCALAI,
            ProviderType.TEXTGEN_WEBUI,
            ProviderType.VLLM,
            ProviderType.KOBOLDAI,
            ProviderType.LLAMACPP,
        }
        return self.config.provider_type in local_types

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available and healthy."""

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models from this provider."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> CompletionResult:
        """Generate completion for prompt."""

    async def stream(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion for prompt (optional, not all providers support)."""
        # Default implementation: return full completion as single chunk
        result = await self.complete(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        yield StreamChunk(content=result.content, finish_reason="stop", is_final=True)

    async def health_check(self) -> ProviderStatus:
        """Perform health check and return status."""
        try:
            is_healthy = await self.is_available()
            self._health_status = (
                ProviderStatus.HEALTHY if is_healthy else ProviderStatus.UNHEALTHY
            )
            self._last_health_check = time.time()
            return self._health_status
        except Exception:
            self._health_status = ProviderStatus.UNHEALTHY
            self._last_health_check = time.time()
            return self._health_status

    def get_model_for_size(self, size: str) -> str:
        """Get model name for given size tier."""
        size_map = {
            "tiny": self.config.model_tiny,
            "small": self.config.model_small,
            "medium": self.config.model_medium,
            "large": self.config.model_large,
        }
        model = size_map.get(size) or self.config.default_model
        return model or "default"

    async def close(self):
        """Clean up provider resources."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, type={self.provider_type.value})"
