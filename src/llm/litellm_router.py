"""
VIBE MCP - LiteLLM Router

Unified LLM access using LiteLLM for routing across 100+ providers.
Implements intelligent routing based on task type, cost, and availability.

Features:
- Unified API for 100+ LLM providers
- Intelligent routing based on task type
- Cost tracking and optimization
- Automatic fallback chains
- Rate limiting and retry logic

Routing Strategy:
- simple → ollama/llama3.1 (free, fast)
- coding → claude-sonnet or deepseek-coder (quality)
- reasoning → claude-opus or o1 (deep thinking)
- fast → groq/llama-70b (<100ms)
- long_context → claude-3.5 or gemini-pro (200K+ context)

Usage:
    router = LiteLLMRouter()

    # Simple completion
    result = await router.complete("Explain this code", task_type="coding")

    # Chat completion
    result = await router.chat([
        {"role": "user", "content": "Build a FastAPI app"}
    ], task_type="coding")
"""

import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Try to import litellm
try:
    import litellm
    from litellm import acompletion

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("LiteLLM not installed. Using fallback routing.")


class TaskType(Enum):
    """Task types for routing decisions."""

    SIMPLE = "simple"  # Simple questions, formatting
    CODING = "coding"  # Code generation, review
    REASONING = "reasoning"  # Complex analysis, planning
    FAST = "fast"  # Low-latency requirements
    LONG_CONTEXT = "long_context"  # Large documents
    CREATIVE = "creative"  # Creative writing
    CHAT = "chat"  # Conversational


class Provider(Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    TOGETHER = "together"
    LMSTUDIO = "lmstudio"


@dataclass
class ModelConfig:
    """Configuration for a model."""

    provider: Provider
    model_id: str
    display_name: str
    max_tokens: int = 4096
    context_window: int = 8192
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    supports_streaming: bool = True
    supports_functions: bool = False
    is_local: bool = False
    priority: int = 1  # Lower = higher priority


@dataclass
class CompletionResult:
    """Result from LLM completion."""

    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)
    latency_ms: float = 0.0
    cost: float = 0.0
    finish_reason: str = "stop"
    raw_response: Any = None


@dataclass
class RouterConfig:
    """Configuration for LiteLLM router."""

    # Default models by task type
    default_models: dict = field(
        default_factory=lambda: {
            TaskType.SIMPLE: "ollama/llama3.1",
            TaskType.CODING: "anthropic/claude-sonnet-4-20250514",
            TaskType.REASONING: "anthropic/claude-sonnet-4-20250514",
            TaskType.FAST: "groq/llama-3.1-70b-versatile",
            TaskType.LONG_CONTEXT: "anthropic/claude-sonnet-4-20250514",
            TaskType.CREATIVE: "anthropic/claude-sonnet-4-20250514",
            TaskType.CHAT: "ollama/llama3.1",
        }
    )

    # Fallback chains
    fallback_chains: dict = field(
        default_factory=lambda: {
            "anthropic": [
                "openai/gpt-4o",
                "groq/llama-3.1-70b-versatile",
                "ollama/llama3.1",
            ],
            "openai": [
                "anthropic/claude-sonnet-4-20250514",
                "groq/llama-3.1-70b-versatile",
                "ollama/llama3.1",
            ],
            "groq": ["ollama/llama3.1", "anthropic/claude-sonnet-4-20250514"],
            "ollama": [
                "groq/llama-3.1-70b-versatile",
                "anthropic/claude-sonnet-4-20250514",
            ],
        }
    )

    # Rate limiting
    max_retries: int = 3
    retry_delay: float = 1.0

    # Cost tracking
    track_costs: bool = True
    max_cost_per_request: float = 1.0  # USD

    # Timeouts
    timeout: int = 120

    # Local preference
    prefer_local: bool = True
    local_only: bool = False


# Pre-configured models
MODELS = {
    # Ollama (Local, Free)
    "ollama/llama3.1": ModelConfig(
        provider=Provider.OLLAMA,
        model_id="llama3.1",
        display_name="Llama 3.1 8B",
        context_window=128000,
        is_local=True,
        priority=1,
    ),
    "ollama/qwen2.5-coder": ModelConfig(
        provider=Provider.OLLAMA,
        model_id="qwen2.5-coder",
        display_name="Qwen 2.5 Coder",
        context_window=32768,
        is_local=True,
        priority=1,
    ),
    "ollama/deepseek-coder-v2": ModelConfig(
        provider=Provider.OLLAMA,
        model_id="deepseek-coder-v2",
        display_name="DeepSeek Coder V2",
        context_window=128000,
        is_local=True,
        priority=1,
    ),
    # Anthropic (Cloud)
    "anthropic/claude-sonnet-4-20250514": ModelConfig(
        provider=Provider.ANTHROPIC,
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        context_window=200000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        supports_functions=True,
        priority=2,
    ),
    "anthropic/claude-3-5-haiku-20241022": ModelConfig(
        provider=Provider.ANTHROPIC,
        model_id="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        context_window=200000,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.005,
        supports_functions=True,
        priority=2,
    ),
    # OpenAI (Cloud)
    "openai/gpt-4o": ModelConfig(
        provider=Provider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        context_window=128000,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        supports_functions=True,
        priority=2,
    ),
    "openai/gpt-4o-mini": ModelConfig(
        provider=Provider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        context_window=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        supports_functions=True,
        priority=2,
    ),
    # Groq (Fast Cloud)
    "groq/llama-3.1-70b-versatile": ModelConfig(
        provider=Provider.GROQ,
        model_id="llama-3.1-70b-versatile",
        display_name="Llama 3.1 70B (Groq)",
        context_window=128000,
        cost_per_1k_input=0.00059,
        cost_per_1k_output=0.00079,
        priority=1,
    ),
    "groq/llama-3.1-8b-instant": ModelConfig(
        provider=Provider.GROQ,
        model_id="llama-3.1-8b-instant",
        display_name="Llama 3.1 8B Instant (Groq)",
        context_window=128000,
        cost_per_1k_input=0.00005,
        cost_per_1k_output=0.00008,
        priority=1,
    ),
    # DeepSeek (Coding)
    "deepseek/deepseek-coder": ModelConfig(
        provider=Provider.DEEPSEEK,
        model_id="deepseek-coder",
        display_name="DeepSeek Coder",
        context_window=128000,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        priority=2,
    ),
}


class LiteLLMRouter:
    """
    Unified LLM router using LiteLLM.

    Routes requests to the optimal model based on task type,
    with automatic fallback and cost tracking.
    """

    def __init__(self, config: RouterConfig | None = None):
        """Initialize the router."""
        self.config = config or RouterConfig()
        self._cost_tracker: dict = {"total": 0.0, "by_model": {}}
        self._request_count = 0
        self._error_count = 0

        # Configure LiteLLM if available
        if LITELLM_AVAILABLE:
            litellm.set_verbose = False
            # Set up callbacks for cost tracking
            if self.config.track_costs:
                litellm.success_callback = [self._on_success]

    def _on_success(self, _kwargs, completion_response, start_time, end_time):
        """Callback for successful completions (cost tracking)."""
        try:
            model = _kwargs.get("model", "unknown")
            usage = completion_response.get("usage", {})

            # Calculate cost
            model_config = MODELS.get(model)
            if model_config:
                input_cost = (
                    usage.get("prompt_tokens", 0) / 1000
                ) * model_config.cost_per_1k_input
                output_cost = (
                    usage.get("completion_tokens", 0) / 1000
                ) * model_config.cost_per_1k_output
                total_cost = input_cost + output_cost

                self._cost_tracker["total"] += total_cost
                if model not in self._cost_tracker["by_model"]:
                    self._cost_tracker["by_model"][model] = 0.0
                self._cost_tracker["by_model"][model] += total_cost
        except Exception as e:
            logger.debug(f"Cost tracking error: {e}")

    def _get_model_for_task(self, task_type: TaskType) -> str:
        """Get the appropriate model for a task type."""
        # Check if local-only mode
        if self.config.local_only:
            return "ollama/llama3.1"

        # Get default model for task type
        model = self.config.default_models.get(task_type, "ollama/llama3.1")

        # If prefer_local and task is simple, use local
        if self.config.prefer_local and task_type in [TaskType.SIMPLE, TaskType.CHAT]:
            return "ollama/llama3.1"

        return model

    def _get_fallback_chain(self, model: str) -> list[str]:
        """Get fallback chain for a model."""
        provider = model.split("/")[0] if "/" in model else model
        return self.config.fallback_chains.get(provider, ["ollama/llama3.1"])

    async def complete(
        self,
        prompt: str,
        task_type: TaskType = TaskType.SIMPLE,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs,
    ) -> CompletionResult:
        """
        Generate a completion.

        Args:
            prompt: The prompt to complete
            task_type: Type of task for routing
            model: Override model selection
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            **kwargs: Additional arguments for the LLM

        Returns:
            CompletionResult with the generated text
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(
            messages=messages,
            task_type=task_type,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            **kwargs,
        )

    async def chat(
        self,
        messages: list[dict],
        task_type: TaskType = TaskType.CHAT,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs,
    ) -> CompletionResult:
        """
        Generate a chat completion.

        Args:
            messages: Chat messages
            task_type: Type of task for routing
            model: Override model selection
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            **kwargs: Additional arguments for the LLM

        Returns:
            CompletionResult with the generated text
        """
        # Select model
        selected_model = model or self._get_model_for_task(task_type)
        fallback_chain = self._get_fallback_chain(selected_model)

        # Try primary model and fallbacks
        models_to_try = [selected_model] + fallback_chain
        last_error = None

        for attempt_model in models_to_try:
            try:
                result = await self._call_model(
                    model=attempt_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=stream,
                    **kwargs,
                )
                self._request_count += 1
                return result

            except Exception as e:
                logger.warning(f"Model {attempt_model} failed: {e}")
                last_error = e
                self._error_count += 1
                continue

        # All models failed
        raise RuntimeError(f"All models failed. Last error: {last_error}")

    async def _call_model(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        stream: bool,
        **kwargs,
    ) -> CompletionResult:
        """Call a specific model."""
        start_time = time.time()

        if not LITELLM_AVAILABLE:
            # Fallback to local Ollama client
            return await self._fallback_ollama(messages, max_tokens, temperature)

        try:
            response = await acompletion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
                timeout=self.config.timeout,
                **kwargs,
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract content
            if stream:
                # Handle streaming response
                content = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
            else:
                content = response.choices[0].message.content

            # Calculate cost
            usage = (
                response.usage.model_dump()
                if hasattr(response, "usage") and response.usage
                else {}
            )
            model_config = MODELS.get(model)
            cost = 0.0
            if model_config and usage:
                input_cost = (
                    usage.get("prompt_tokens", 0) / 1000
                ) * model_config.cost_per_1k_input
                output_cost = (
                    usage.get("completion_tokens", 0) / 1000
                ) * model_config.cost_per_1k_output
                cost = input_cost + output_cost

            return CompletionResult(
                content=content,
                model=model,
                provider=model.split("/")[0] if "/" in model else "unknown",
                usage=usage,
                latency_ms=latency_ms,
                cost=cost,
                finish_reason=response.choices[0].finish_reason
                if response.choices
                else "stop",
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"LiteLLM call failed for {model}: {e}")
            raise

    async def _fallback_ollama(
        self,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> CompletionResult:
        """Fallback to direct Ollama call when LiteLLM unavailable."""
        from src.llm.ollama_client import OllamaClient

        start_time = time.time()
        client = OllamaClient()

        # Convert messages to prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        result = await client.complete(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        latency_ms = (time.time() - start_time) * 1000

        return CompletionResult(
            content=result.content,
            model="ollama/llama3.1",
            provider="ollama",
            usage={
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
            },
            latency_ms=latency_ms,
            cost=0.0,  # Local is free
        )

    async def stream(
        self,
        prompt: str,
        task_type: TaskType = TaskType.SIMPLE,
        model: str | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a completion.

        Args:
            prompt: The prompt to complete
            task_type: Type of task for routing
            model: Override model selection
            **kwargs: Additional arguments

        Yields:
            Chunks of generated text
        """
        selected_model = model or self._get_model_for_task(task_type)

        if not LITELLM_AVAILABLE:
            # Fallback - just return full response
            result = await self.complete(prompt, task_type, model, **kwargs)
            yield result.content
            return

        messages = [{"role": "user", "content": prompt}]

        response = await acompletion(
            model=selected_model,
            messages=messages,
            stream=True,
            timeout=self.config.timeout,
            **kwargs,
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_stats(self) -> dict:
        """Get router statistics."""
        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1) * 100,
            "total_cost": self._cost_tracker["total"],
            "cost_by_model": self._cost_tracker["by_model"],
            "litellm_available": LITELLM_AVAILABLE,
        }

    def get_available_models(self) -> list[dict]:
        """Get list of available models."""
        return [
            {
                "id": model_id,
                "name": config.display_name,
                "provider": config.provider.value,
                "context_window": config.context_window,
                "is_local": config.is_local,
                "cost_per_1k": config.cost_per_1k_input + config.cost_per_1k_output,
            }
            for model_id, config in MODELS.items()
        ]

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._cost_tracker = {"total": 0.0, "by_model": {}}
        self._request_count = 0
        self._error_count = 0


# Global instance
_router: LiteLLMRouter | None = None


def get_litellm_router() -> LiteLLMRouter:
    """Get or create global LiteLLM router instance."""
    global _router
    if _router is None:
        _router = LiteLLMRouter()
    return _router
