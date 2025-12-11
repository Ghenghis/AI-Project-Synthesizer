"""
AI Project Synthesizer - LLM Router

Intelligent routing between local and cloud LLMs based on task complexity.
"""

import logging
from enum import Enum
from dataclasses import dataclass

from src.llm.ollama_client import OllamaClient, CompletionResult
from src.llm.lmstudio_client import LMStudioClient

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """LLM provider types."""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TaskComplexity(Enum):
    """Task complexity levels for routing decisions."""
    SIMPLE = "simple"      # Formatting, simple questions
    MODERATE = "moderate"  # Code review, basic analysis
    COMPLEX = "complex"    # Architecture, multi-file reasoning


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    provider: ProviderType
    model: str
    reason: str
    estimated_tokens: int = 0


class LLMRouter:
    """
    Intelligent router between local and cloud LLMs.

    Routing strategy:
    - Simple tasks → Local (Ollama 7B or LM Studio fast model)
    - Moderate tasks → Local (Ollama 14B or LM Studio balanced model)
    - Complex tasks → Cloud API when enabled, else largest local

    Supports multiple providers with intelligent fallback:
    - Preferred provider (configurable: ollama, lmstudio, openai, anthropic)
    - Fallback between local providers (Ollama ↔ LM Studio)
    - Cloud fallback when enabled

    Usage:
        router = LLMRouter()
        result = await router.complete(
            prompt="Explain this code",
            complexity=TaskComplexity.SIMPLE
        )
    """

    # Token thresholds for routing
    CONTEXT_THRESHOLD_LOCAL = 32000  # Max context for local models
    CONTEXT_THRESHOLD_7B = 8000      # Recommended for 7B
    CONTEXT_THRESHOLD_14B = 16000    # Recommended for 14B

    def __init__(
        self,
        preferred_provider: str = "ollama",
        ollama_client: OllamaClient = None,
        lmstudio_client: LMStudioClient = None,
        cloud_enabled: bool = False,
        cloud_threshold: float = 0.7,
        model_size_preference: str = "medium",
        fallback_enabled: bool = True,
    ):
        """
        Initialize the router.

        Args:
            preferred_provider: Preferred provider (ollama, lmstudio, openai, anthropic)
            ollama_client: Ollama client instance
            lmstudio_client: LM Studio client instance
            cloud_enabled: Whether to use cloud APIs
            cloud_threshold: Complexity threshold for cloud (0-1)
            model_size_preference: Model size preference (tiny, small, medium, large)
            fallback_enabled: Enable fallback between providers
        """
        self.preferred_provider = ProviderType(preferred_provider.lower())
        self.fallback_enabled = fallback_enabled
        self.cloud_enabled = cloud_enabled
        self.cloud_threshold = cloud_threshold
        self.model_size_preference = model_size_preference

        # Initialize clients
        self.ollama_client = ollama_client or OllamaClient()
        self.lmstudio_client = lmstudio_client or LMStudioClient()

        # Size-based model configurations (optimized for 7B and smaller)
        self.local_models = {
            "ollama": {
                "tiny": "qwen2.5-coder:1.5b-instruct",      # < 2B parameters
                "small": "qwen2.5-coder:3b-instruct",      # 2-4B parameters
                "medium": "qwen2.5-coder:7b-instruct-q8_0", # 4-7B parameters (DEFAULT)
                "large": "qwen2.5-coder:14b-instruct-q4_K_M", # 8-14B parameters
            },
            "lmstudio": {
                "tiny": "local-model-tiny",      # User's < 2B model
                "small": "local-model-small",    # User's 2-4B model
                "medium": "local-model-medium",  # User's 4-7B model (DEFAULT)
                "large": "local-model-large",    # User's 8-14B model
            }
        }

        self._cloud_client = None  # Lazy initialization

    async def check_provider_health(self, provider: ProviderType) -> bool:
        """
        Check if a provider is available.

        Args:
            provider: Provider to check

        Returns:
            True if provider is healthy
        """
        try:
            if provider == ProviderType.OLLAMA:
                return await self.ollama_client.is_available()
            elif provider == ProviderType.LMSTUDIO:
                return await self.lmstudio_client.is_available()
            elif provider in [ProviderType.OPENAI, ProviderType.ANTHROPIC]:
                # // DONE: Implement cloud provider health checks
                return self.cloud_enabled
            return False
        except Exception as e:
            logger.warning(f"Health check failed for {provider}: {e}")
            return False

    async def get_best_provider(self) -> ProviderType:
        """
        Get the best available provider with fallback logic.

        Returns:
            Best available provider
        """
        # Try preferred provider first
        if await self.check_provider_health(self.preferred_provider):
            return self.preferred_provider

        if not self.fallback_enabled:
            logger.warning(f"Preferred provider {self.preferred_provider} unavailable, fallback disabled")
            return self.preferred_provider

        # Try other local providers
        local_providers = [ProviderType.OLLAMA, ProviderType.LMSTUDIO]
        for provider in local_providers:
            if provider != self.preferred_provider and await self.check_provider_health(provider):
                logger.info(f"Falling back from {self.preferred_provider} to {provider}")
                return provider

        # Fall back to cloud if enabled
        if self.cloud_enabled:
            logger.info("Local providers unavailable, falling back to cloud")
            return ProviderType.OPENAI  # Default to OpenAI for cloud fallback

        # No providers available
        logger.error("No LLM providers available")
        return self.preferred_provider

    def estimate_complexity(
        self,
        prompt: str,
        context_length: int = None,
    ) -> TaskComplexity:
        """
        Estimate task complexity from prompt.

        Heuristics:
        - Short prompts with simple questions → Simple
        - Code review, single file analysis → Moderate
        - Architecture, multi-file, long context → Complex
        """
        # Estimate context length
        if context_length is None:
            context_length = len(prompt) // 4  # Rough token estimate

        # Simple heuristics
        keywords_simple = ["format", "fix typo", "rename", "what is", "explain briefly"]
        keywords_complex = ["architecture", "design", "refactor entire", "across files", "system"]

        prompt_lower = prompt.lower()

        # Check for simple tasks
        if any(kw in prompt_lower for kw in keywords_simple):
            return TaskComplexity.SIMPLE

        # Check for complex tasks
        if any(kw in prompt_lower for kw in keywords_complex):
            return TaskComplexity.COMPLEX

        # Context-based routing
        if context_length > self.CONTEXT_THRESHOLD_14B:
            return TaskComplexity.COMPLEX
        elif context_length > self.CONTEXT_THRESHOLD_7B:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    def route(
        self,
        complexity: TaskComplexity,
        context_length: int = 0,
        preferred_provider: ProviderType = None,
    ) -> RoutingDecision:
        """
        Decide which model to use based on size preference and task complexity.

        Args:
            complexity: Task complexity
            context_length: Estimated context length in tokens
            preferred_provider: Override preferred provider

        Returns:
            RoutingDecision with model selection
        """
        provider = preferred_provider or self.preferred_provider

        # Get model based on size preference
        model = self.local_models.get(provider.value, {}).get(self.model_size_preference, "local-model")

        # Adjust model selection based on task complexity and size preference
        if complexity == TaskComplexity.SIMPLE:
            # For simple tasks, use smaller models for speed
            if self.model_size_preference == "large":
                size_to_use = "medium"
            elif self.model_size_preference == "medium":
                size_to_use = "small"
            else:
                size_to_use = self.model_size_preference
            model = self.local_models.get(provider.value, {}).get(size_to_use, model)
            reason = f"Simple task → {size_to_use} {provider.value} model for speed"

        elif complexity == TaskComplexity.MODERATE:
            # For moderate tasks, use preferred size but consider context
            if context_length > self.CONTEXT_THRESHOLD_7B and self.model_size_preference == "small":
                size_to_use = "medium"
                model = self.local_models.get(provider.value, {}).get(size_to_use, model)
                reason = f"Moderate task with long context → {size_to_use} {provider.value} model"
            else:
                size_to_use = self.model_size_preference
                model = self.local_models.get(provider.value, {}).get(size_to_use, model)
                reason = f"Moderate task → {size_to_use} {provider.value} model"

        else:  # COMPLEX
            # For complex tasks, use larger models if available
            if self.model_size_preference == "tiny":
                size_to_use = "small"
            elif self.model_size_preference == "small":
                size_to_use = "medium"
            elif self.model_size_preference == "medium":
                size_to_use = "large"
            else:
                size_to_use = self.model_size_preference

            # Fall back to cloud if enabled and we need more power
            if size_to_use == "large" and self.cloud_enabled:
                return RoutingDecision(
                    provider=ProviderType.OPENAI,
                    model="gpt-4-turbo-preview",
                    reason="Complex task → cloud API (GPT-4)",
                    estimated_tokens=context_length,
                )

            model = self.local_models.get(provider.value, {}).get(size_to_use, model)
            reason = f"Complex task → {size_to_use} {provider.value} model"

        return RoutingDecision(
            provider=provider,
            model=model,
            reason=reason,
            estimated_tokens=context_length,
        )

    async def complete(
        self,
        prompt: str,
        complexity: TaskComplexity = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        """
        Complete prompt with automatic routing and fallback.

        Args:
            prompt: User prompt
            complexity: Override complexity (auto-detected if None)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            CompletionResult from chosen model
        """
        # Estimate complexity if not provided
        if complexity is None:
            complexity = self.estimate_complexity(prompt)

        # Get best available provider
        best_provider = await self.get_best_provider()

        # Get routing decision
        context_length = len(prompt) // 4
        decision = self.route(complexity, context_length, best_provider)

        logger.info(f"Routing: {decision.reason}")

        # Execute with chosen provider
        try:
            if decision.provider == ProviderType.OLLAMA:
                return await self.ollama_client.complete(
                    prompt=prompt,
                    model=decision.model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            elif decision.provider == ProviderType.LMSTUDIO:
                return await self.lmstudio_client.complete(
                    prompt=prompt,
                    model=decision.model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            elif decision.provider in [ProviderType.OPENAI, ProviderType.ANTHROPIC]:
                # Cloud completion (to be implemented)
                return await self._cloud_complete(
                    prompt=prompt,
                    model=decision.model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                raise ValueError(f"Unknown provider: {decision.provider}")

        except Exception as e:
            logger.error(f"Completion failed with {decision.provider}: {e}")

            # Try fallback if enabled and this wasn't already a fallback
            if self.fallback_enabled and decision.provider == self.preferred_provider:
                logger.info("Primary provider failed, trying fallback providers")

                # Try other local providers
                for fallback_provider in [ProviderType.OLLAMA, ProviderType.LMSTUDIO]:
                    if fallback_provider != decision.provider:
                        try:
                            if await self.check_provider_health(fallback_provider):
                                logger.info(f"Falling back to {fallback_provider}")

                                if fallback_provider == ProviderType.OLLAMA:
                                    return await self.ollama_client.complete(
                                        prompt=prompt,
                                        model=self.local_models["ollama"]["medium"],
                                        system_prompt=system_prompt,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                    )
                                else:  # LMSTUDIO
                                    return await self.lmstudio_client.complete(
                                        prompt=prompt,
                                        model=self.local_models["lmstudio"]["medium"],
                                        system_prompt=system_prompt,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                    )
                        except Exception as fallback_error:
                            logger.warning(f"Fallback to {fallback_provider} also failed: {fallback_error}")
                            continue

                # Try cloud as last resort
                if self.cloud_enabled:
                    logger.info("Local fallbacks failed, trying cloud")
                    return await self._cloud_complete(
                        prompt=prompt,
                        model="gpt-4-turbo-preview",
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

            # No fallback worked, re-raise original error
            raise

    async def _cloud_complete(
        self,
        prompt: str,
        model: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        """Cloud completion (placeholder for cloud API integration)."""
        # For now, fall back to local
        logger.warning("Cloud API not configured, falling back to local")
        return await self.local_client.complete(
            prompt=prompt,
            model=self.local_models["powerful"],
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
