"""
AI Project Synthesizer - Ollama Provider

Native Ollama provider using the Ollama API directly.
Supports all Ollama-specific features including model management.
"""

import time
from typing import Optional, List, Dict, Any, AsyncIterator

import httpx

from src.llm.providers.base import (
    LLMProvider,
    ProviderConfig,
    CompletionResult,
    StreamChunk,
    ProviderCapabilities,
)
from src.core.circuit_breaker import circuit_breaker, CircuitBreakerConfig
from src.core.security import get_secure_logger
from src.core.observability import correlation_manager, track_performance, metrics

secure_logger = get_secure_logger(__name__)

OLLAMA_BREAKER = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=30.0,
    success_threshold=2,
    timeout=120.0,
)


class OllamaProvider(LLMProvider):
    """
    Native Ollama provider using Ollama's REST API.
    
    Features:
    - Native Ollama API support
    - Model pulling and management
    - Streaming completions
    - Model information retrieval
    
    Usage:
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            name="ollama",
            host="http://localhost:11434",
        )
        provider = OllamaProvider(config)
        result = await provider.complete("Hello!")
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        self.base_url = config.host.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=config.timeout,
        )

        self.capabilities = ProviderCapabilities(
            streaming=True,
            function_calling=False,
            vision=True,  # Ollama supports vision models
            embeddings=True,
            code_completion=True,
            chat=True,
            max_context_length=32768,
            supports_system_prompt=True,
            supports_json_mode=True,
        )

    @circuit_breaker("ollama", OLLAMA_BREAKER)
    @track_performance("ollama_available")
    async def is_available(self) -> bool:
        """Check if Ollama server is available."""
        correlation_id = correlation_manager.get_correlation_id()

        try:
            response = await self.client.get("/api/tags")
            is_healthy = response.status_code == 200

            if is_healthy:
                data = response.json()
                model_count = len(data.get("models", []))
                secure_logger.info(
                    "Ollama server available",
                    extra={
                        "correlation_id": correlation_id,
                        "model_count": model_count,
                    }
                )
                metrics.increment("llm_health_check_success", tags={"provider": "ollama"})

            return is_healthy

        except Exception as e:
            secure_logger.warning(
                f"Ollama server unavailable: {str(e)[:100]}",
                extra={"correlation_id": correlation_id}
            )
            metrics.increment("llm_health_check_failure", tags={"provider": "ollama"})
            return False

    @circuit_breaker("ollama", OLLAMA_BREAKER)
    @track_performance("ollama_list_models")
    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            secure_logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a model."""
        try:
            response = await self.client.post(
                "/api/show",
                json={"name": model}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            response = await self.client.post(
                "/api/pull",
                json={"name": model},
                timeout=600.0,  # Model pulls can take a while
            )
            return response.status_code == 200
        except Exception as e:
            secure_logger.error(f"Failed to pull model {model}: {e}")
            return False

    @circuit_breaker("ollama", OLLAMA_BREAKER)
    @track_performance("ollama_complete")
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> CompletionResult:
        """Generate completion using Ollama API."""
        correlation_id = correlation_manager.get_correlation_id()
        start_time = time.time()

        model = model or self.config.default_model or "qwen2.5-coder:7b-instruct-q8_0"

        # Build request
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if system_prompt:
            request_data["system"] = system_prompt

        secure_logger.info(
            "Starting Ollama completion",
            extra={
                "correlation_id": correlation_id,
                "model": model,
                "prompt_length": len(prompt),
            }
        )

        try:
            response = await self.client.post(
                "/api/generate",
                json=request_data,
                timeout=self.config.timeout,
            )

            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.status_code}")

            data = response.json()
            duration_ms = int((time.time() - start_time) * 1000)

            content = data.get("response", "")

            # Ollama provides eval_count for tokens
            tokens_used = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

            secure_logger.info(
                "Ollama completion successful",
                extra={
                    "correlation_id": correlation_id,
                    "model": model,
                    "tokens_used": tokens_used,
                    "duration_ms": duration_ms,
                }
            )

            metrics.increment("llm_completions_success", tags={"provider": "ollama"})
            metrics.record_histogram("llm_completion_tokens", tokens_used, tags={"provider": "ollama"})
            metrics.record_timer("llm_completion_duration", duration_ms / 1000, tags={"provider": "ollama"})

            return CompletionResult(
                content=content,
                model=model,
                provider="ollama",
                tokens_used=tokens_used,
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                finish_reason="stop" if data.get("done") else "length",
                duration_ms=duration_ms,
                metadata={
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "eval_duration": data.get("eval_duration"),
                }
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            secure_logger.error(
                f"Ollama completion failed: {str(e)[:200]}",
                extra={
                    "correlation_id": correlation_id,
                    "model": model,
                    "duration_ms": duration_ms,
                }
            )
            metrics.increment("llm_completions_error", tags={"provider": "ollama"})
            raise

    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using Ollama API."""
        model = model or self.config.default_model or "qwen2.5-coder:7b-instruct-q8_0"

        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if system_prompt:
            request_data["system"] = system_prompt

        try:
            async with self.client.stream(
                "POST",
                "/api/generate",
                json=request_data,
                timeout=self.config.timeout,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)

                        content = data.get("response", "")
                        is_done = data.get("done", False)

                        yield StreamChunk(
                            content=content,
                            finish_reason="stop" if is_done else None,
                            is_final=is_done,
                        )

        except Exception as e:
            secure_logger.error(f"Ollama stream failed: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
