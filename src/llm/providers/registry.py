"""
AI Project Synthesizer - Provider Registry

Central registry for managing multiple LLM providers with:
- Dynamic provider registration
- Health monitoring
- Automatic fallback
- Load balancing
"""

import asyncio
from typing import Optional, List, Dict, Type
from dataclasses import dataclass
import time

from src.llm.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderType,
    ProviderStatus,
    CompletionResult,
)
from src.core.security import get_secure_logger
from src.core.observability import correlation_manager

secure_logger = get_secure_logger(__name__)


@dataclass
class ProviderInfo:
    """Information about a registered provider."""
    provider: LLMProvider
    config: ProviderConfig
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_check: float = 0
    success_count: int = 0
    failure_count: int = 0


class ProviderRegistry:
    """
    Central registry for LLM providers.
    
    Features:
    - Register multiple providers
    - Health monitoring with automatic status updates
    - Intelligent fallback between providers
    - Priority-based provider selection
    - Metrics and logging
    
    Usage:
        registry = ProviderRegistry()
        registry.register_provider(ollama_config)
        registry.register_provider(lmstudio_config)
        
        # Get best available provider
        provider = await registry.get_best_provider()
        result = await provider.complete("Hello!")
        
        # Or use unified completion with automatic fallback
        result = await registry.complete("Hello!")
    """

    def __init__(self):
        self._providers: Dict[str, ProviderInfo] = {}
        self._provider_classes: Dict[ProviderType, Type[LLMProvider]] = {}
        self._default_provider: Optional[str] = None
        self._health_check_interval: float = 60.0
        self._lock = asyncio.Lock()

        # Register built-in provider classes
        self._register_builtin_providers()

    def _register_builtin_providers(self):
        """Register built-in provider implementations."""
        from src.llm.providers.openai_compatible import OpenAICompatibleProvider
        from src.llm.providers.ollama import OllamaProvider

        # Native Ollama provider
        self._provider_classes[ProviderType.OLLAMA] = OllamaProvider

        # OpenAI-compatible providers (most local servers)
        openai_compat_types = [
            ProviderType.LMSTUDIO,
            ProviderType.LMSTUDIO_MCP,
            ProviderType.LOCALAI,
            ProviderType.VLLM,
            ProviderType.TEXTGEN_WEBUI,
            ProviderType.OPENAI_COMPATIBLE,
            ProviderType.OPENAI,
            ProviderType.GROQ,
            ProviderType.TOGETHER,
            ProviderType.OPENROUTER,
            ProviderType.MISTRAL,
            ProviderType.FIREWORKS,
            ProviderType.DEEPSEEK,
            ProviderType.COHERE,
            ProviderType.KOBOLDAI,
            ProviderType.LLAMACPP,
        ]

        for provider_type in openai_compat_types:
            self._provider_classes[provider_type] = OpenAICompatibleProvider

    def register_provider_class(
        self,
        provider_type: ProviderType,
        provider_class: Type[LLMProvider]
    ):
        """Register a custom provider class."""
        self._provider_classes[provider_type] = provider_class

    def register_provider(self, config: ProviderConfig) -> str:
        """
        Register a new provider with the registry.
        
        Args:
            config: Provider configuration
            
        Returns:
            Provider name/ID
        """
        provider_class = self._provider_classes.get(config.provider_type)
        if not provider_class:
            raise ValueError(f"No provider class registered for type: {config.provider_type}")

        provider = provider_class(config)

        self._providers[config.name] = ProviderInfo(
            provider=provider,
            config=config,
        )

        if self._default_provider is None:
            self._default_provider = config.name

        secure_logger.info(
            f"Registered provider: {config.name}",
            extra={
                "provider_type": config.provider_type.value,
                "host": config.host,
                "priority": config.priority,
            }
        )

        return config.name

    def unregister_provider(self, name: str):
        """Remove a provider from the registry."""
        if name in self._providers:
            del self._providers[name]
            if self._default_provider == name:
                self._default_provider = next(iter(self._providers), None)

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a specific provider by name."""
        info = self._providers.get(name)
        return info.provider if info else None

    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def get_provider_info(self, name: str) -> Optional[ProviderInfo]:
        """Get detailed info about a provider."""
        return self._providers.get(name)

    async def check_provider_health(self, name: str) -> ProviderStatus:
        """Check health of a specific provider."""
        info = self._providers.get(name)
        if not info:
            return ProviderStatus.UNKNOWN

        try:
            status = await info.provider.health_check()
            info.status = status
            info.last_check = time.time()

            if status == ProviderStatus.HEALTHY:
                info.success_count += 1
            else:
                info.failure_count += 1

            return status

        except Exception as e:
            secure_logger.warning(f"Health check failed for {name}: {e}")
            info.status = ProviderStatus.UNHEALTHY
            info.failure_count += 1
            return ProviderStatus.UNHEALTHY

    async def check_all_health(self) -> Dict[str, ProviderStatus]:
        """Check health of all providers."""
        results = {}

        tasks = [
            self.check_provider_health(name)
            for name in self._providers
        ]

        statuses = await asyncio.gather(*tasks, return_exceptions=True)

        for name, status in zip(self._providers.keys(), statuses):
            if isinstance(status, Exception):
                results[name] = ProviderStatus.UNHEALTHY
            else:
                results[name] = status

        return results

    async def get_best_provider(
        self,
        require_local: bool = False,
        exclude: Optional[List[str]] = None
    ) -> Optional[LLMProvider]:
        """
        Get the best available provider.
        
        Args:
            require_local: Only consider local providers
            exclude: Provider names to exclude
            
        Returns:
            Best available provider or None
        """
        exclude = exclude or []

        # Sort by priority (lower = higher priority)
        candidates = sorted(
            [
                info for name, info in self._providers.items()
                if name not in exclude
                and info.config.enabled
                and (not require_local or info.provider.is_local)
            ],
            key=lambda x: x.config.priority
        )

        for info in candidates:
            # Check if health check is recent enough
            if time.time() - info.last_check > self._health_check_interval:
                await self.check_provider_health(info.config.name)

            if info.status == ProviderStatus.HEALTHY:
                return info.provider

        # No healthy providers, try first enabled one anyway
        for info in candidates:
            return info.provider

        return None

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider_name: Optional[str] = None,
        fallback: bool = True,
        **kwargs
    ) -> CompletionResult:
        """
        Complete prompt with automatic provider selection and fallback.
        
        Args:
            prompt: User prompt
            model: Model to use (optional)
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            provider_name: Specific provider to use
            fallback: Enable fallback to other providers
            **kwargs: Additional provider-specific arguments
            
        Returns:
            CompletionResult from successful provider
        """
        correlation_id = correlation_manager.get_correlation_id()
        excluded = []

        while True:
            # Get provider
            if provider_name and provider_name not in excluded:
                provider = self.get_provider(provider_name)
            else:
                provider = await self.get_best_provider(exclude=excluded)

            if not provider:
                raise RuntimeError("No available LLM providers")

            try:
                result = await provider.complete(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                # Update success count
                info = self._providers.get(provider.name)
                if info:
                    info.success_count += 1

                return result

            except Exception as e:
                secure_logger.warning(
                    f"Provider {provider.name} failed: {e}",
                    extra={"correlation_id": correlation_id}
                )

                # Update failure count
                info = self._providers.get(provider.name)
                if info:
                    info.failure_count += 1
                    info.status = ProviderStatus.DEGRADED

                if not fallback:
                    raise

                excluded.append(provider.name)

                # Check if we've exhausted all providers
                if len(excluded) >= len(self._providers):
                    raise RuntimeError(f"All providers failed. Last error: {e}")

    async def close_all(self):
        """Close all provider connections."""
        for info in self._providers.values():
            try:
                await info.provider.close()
            except Exception as e:
                secure_logger.warning(f"Error closing provider {info.config.name}: {e}")


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


# Pre-configured provider configs for common services
PROVIDER_PRESETS: Dict[str, ProviderConfig] = {
    "ollama": ProviderConfig(
        provider_type=ProviderType.OLLAMA,
        name="ollama",
        host="http://localhost:11434",
        api_key="ollama",
        default_model="qwen2.5-coder:7b-instruct-q8_0",
        model_tiny="qwen2.5-coder:1.5b-instruct",
        model_small="qwen2.5-coder:3b-instruct",
        model_medium="qwen2.5-coder:7b-instruct-q8_0",
        model_large="qwen2.5-coder:14b-instruct-q4_K_M",
        priority=0,
    ),
    "lmstudio": ProviderConfig(
        provider_type=ProviderType.LMSTUDIO,
        name="lmstudio",
        host="http://localhost:1234",
        api_key="lm-studio",
        default_model="local-model",
        model_tiny="local-model-tiny",
        model_small="local-model-small",
        model_medium="local-model-medium",
        model_large="local-model-large",
        priority=1,
    ),
    "localai": ProviderConfig(
        provider_type=ProviderType.LOCALAI,
        name="localai",
        host="http://localhost:8080",
        api_key="localai",
        default_model="gpt-3.5-turbo",
        priority=2,
    ),
    "vllm": ProviderConfig(
        provider_type=ProviderType.VLLM,
        name="vllm",
        host="http://localhost:8000",
        api_key="vllm",
        default_model="default",
        priority=2,
    ),
    "textgen_webui": ProviderConfig(
        provider_type=ProviderType.TEXTGEN_WEBUI,
        name="textgen_webui",
        host="http://localhost:5000",
        api_key="textgen",
        default_model="default",
        priority=2,
    ),
    "groq": ProviderConfig(
        provider_type=ProviderType.GROQ,
        name="groq",
        host="https://api.groq.com/openai",
        default_model="llama-3.1-70b-versatile",
        model_small="llama-3.1-8b-instant",
        model_medium="llama-3.1-70b-versatile",
        model_large="llama-3.1-70b-versatile",
        priority=10,
    ),
    "together": ProviderConfig(
        provider_type=ProviderType.TOGETHER,
        name="together",
        host="https://api.together.xyz",
        default_model="meta-llama/Llama-3-70b-chat-hf",
        priority=10,
    ),
    "openrouter": ProviderConfig(
        provider_type=ProviderType.OPENROUTER,
        name="openrouter",
        host="https://openrouter.ai/api",
        default_model="anthropic/claude-3.5-sonnet",
        priority=10,
    ),
    "openai": ProviderConfig(
        provider_type=ProviderType.OPENAI,
        name="openai",
        host="https://api.openai.com",
        default_model="gpt-4-turbo-preview",
        model_small="gpt-3.5-turbo",
        model_medium="gpt-4-turbo-preview",
        model_large="gpt-4-turbo-preview",
        priority=20,
    ),
    "deepseek": ProviderConfig(
        provider_type=ProviderType.DEEPSEEK,
        name="deepseek",
        host="https://api.deepseek.com",
        default_model="deepseek-coder",
        model_small="deepseek-coder",
        model_medium="deepseek-coder",
        model_large="deepseek-coder",
        priority=15,
    ),
    "mistral": ProviderConfig(
        provider_type=ProviderType.MISTRAL,
        name="mistral",
        host="https://api.mistral.ai",
        default_model="mistral-large-latest",
        model_small="mistral-small-latest",
        model_medium="mistral-medium-latest",
        model_large="mistral-large-latest",
        priority=15,
    ),
}
