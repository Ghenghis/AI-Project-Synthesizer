"""
AI Project Synthesizer - OpenAI-Compatible Provider

Generic provider for any OpenAI-compatible API including:
- LM Studio
- LocalAI
- vLLM
- Text Generation WebUI (with OpenAI extension)
- Ollama (OpenAI mode)
- Any other OpenAI-compatible server
"""

import time
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from src.core.circuit_breaker import CircuitBreakerConfig, circuit_breaker
from src.core.observability import correlation_manager, metrics, track_performance
from src.core.security import get_secure_logger
from src.llm.providers.base import (
    CompletionResult,
    LLMProvider,
    ProviderCapabilities,
    ProviderConfig,
    StreamChunk,
)

secure_logger = get_secure_logger(__name__)

# Circuit breaker config for OpenAI-compatible providers
OPENAI_COMPAT_BREAKER = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=30.0,
    success_threshold=2,
    timeout=60.0,
)


class OpenAICompatibleProvider(LLMProvider):
    """
    Generic provider for OpenAI-compatible APIs.

    Works with any server that implements the OpenAI API spec:
    - LM Studio (localhost:1234)
    - LocalAI (localhost:8080)
    - vLLM (localhost:8000)
    - Text Generation WebUI (localhost:5000)
    - Ollama OpenAI mode (localhost:11434/v1)

    Usage:
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI_COMPATIBLE,
            name="my-local-llm",
            host="http://localhost:1234",
            api_key="not-needed",
        )
        provider = OpenAICompatibleProvider(config)
        result = await provider.complete("Hello!")
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        # Initialize OpenAI client with custom base URL
        base_url = config.host.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=config.api_key or "not-needed",
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

        # Set capabilities
        self.capabilities = ProviderCapabilities(
            streaming=True,
            function_calling=False,
            vision=False,
            embeddings=False,
            code_completion=True,
            chat=True,
            max_context_length=32768,
            supports_system_prompt=True,
            supports_json_mode=False,
        )

    @circuit_breaker("openai_compatible", OPENAI_COMPAT_BREAKER)
    @track_performance("openai_compatible_available")
    async def is_available(self) -> bool:
        """Check if the OpenAI-compatible server is available."""
        correlation_id = correlation_manager.get_correlation_id()

        try:
            models = await self.client.models.list()
            model_count = len(list(models))

            secure_logger.info(
                "OpenAI-compatible server available",
                extra={
                    "correlation_id": correlation_id,
                    "provider": self.name,
                    "model_count": model_count,
                },
            )

            metrics.increment("llm_health_check_success", tags={"provider": self.name})
            return True

        except Exception as e:
            secure_logger.warning(
                f"OpenAI-compatible server unavailable: {str(e)[:100]}",
                extra={
                    "correlation_id": correlation_id,
                    "provider": self.name,
                },
            )
            metrics.increment("llm_health_check_failure", tags={"provider": self.name})
            return False

    @circuit_breaker("openai_compatible", OPENAI_COMPAT_BREAKER)
    @track_performance("openai_compatible_list_models")
    async def list_models(self) -> list[str]:
        """List available models from the server."""
        try:
            models = await self.client.models.list()
            return [model.id for model in models]
        except Exception as e:
            secure_logger.error(f"Failed to list models: {e}")
            return []

    @circuit_breaker("openai_compatible", OPENAI_COMPAT_BREAKER)
    @track_performance("openai_compatible_complete")
    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> CompletionResult:
        """Generate completion using OpenAI-compatible API."""
        correlation_id = correlation_manager.get_correlation_id()
        start_time = time.time()

        model = model or self.config.default_model or "local-model"

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        secure_logger.info(
            "Starting completion",
            extra={
                "correlation_id": correlation_id,
                "provider": self.name,
                "model": model,
                "prompt_length": len(prompt),
            },
        )

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = (
                response.usage.completion_tokens if response.usage else 0
            )

            secure_logger.info(
                "Completion successful",
                extra={
                    "correlation_id": correlation_id,
                    "provider": self.name,
                    "model": model,
                    "tokens_used": tokens_used,
                    "duration_ms": duration_ms,
                },
            )

            metrics.increment("llm_completions_success", tags={"provider": self.name})
            metrics.record_histogram(
                "llm_completion_tokens", tokens_used, tags={"provider": self.name}
            )
            metrics.record_timer(
                "llm_completion_duration",
                duration_ms / 1000,
                tags={"provider": self.name},
            )

            return CompletionResult(
                content=content,
                model=model,
                provider=self.name,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=response.choices[0].finish_reason or "stop",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            secure_logger.error(
                f"Completion failed: {str(e)[:200]}",
                extra={
                    "correlation_id": correlation_id,
                    "provider": self.name,
                    "model": model,
                    "duration_ms": duration_ms,
                },
            )
            metrics.increment("llm_completions_error", tags={"provider": self.name})
            raise

    async def stream(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using OpenAI-compatible API."""
        model = model or self.config.default_model or "local-model"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamChunk(
                        content=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                        is_final=chunk.choices[0].finish_reason is not None,
                    )

        except Exception as e:
            secure_logger.error(f"Stream failed: {e}")
            raise

    async def close(self):
        """Close the client."""
        await self.client.close()
