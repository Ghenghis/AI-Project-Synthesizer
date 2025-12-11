"""
AI Project Synthesizer - LM Studio Client

Client for local LLM inference using LM Studio.
LM Studio provides an OpenAI-compatible API for local model serving.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from openai import AsyncOpenAI

from src.core.circuit_breaker import circuit_breaker, OLLAMA_BREAKER_CONFIG
from src.core.security import get_secure_logger
from src.core.observability import correlation_manager, track_performance, metrics

secure_logger = get_secure_logger(__name__)


@dataclass
class CompletionResult:
    """Result from LLM completion."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    duration_ms: int


class LMStudioClient:
    """
    Client for LM Studio local LLM inference.
    
    Uses OpenAI-compatible API to communicate with LM Studio.
    Supports any model loaded in LM Studio.
    
    Usage:
        client = LMStudioClient()
        result = await client.complete("Explain this code: def foo(): pass")
        print(result.content)
    """

    def __init__(
        self,
        host: str = "http://localhost:1234",
        api_key: str = "lm-studio",  # LM Studio doesn't require real API key
        default_model: str = None,
        timeout: float = 120.0,
    ):
        """
        Initialize LM Studio client.
        
        Args:
            host: LM Studio server URL (default: localhost:1234)
            api_key: API key (LM Studio accepts any string)
            default_model: Default model to use
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model or "local-model"  # Generic name
        self.timeout = timeout
        self._client: Optional[AsyncOpenAI] = None

    async def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=f"{self.host}/v1",
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Close the client."""
        if self._client:
            await self._client.close()
            self._client = None

    @circuit_breaker(
        name="lmstudio_health_check",
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=10.0,
        expected_exception=Exception
    )
    @track_performance("lmstudio_health_check")
    async def is_available(self) -> bool:
        """Check if LM Studio is available."""
        correlation_id = correlation_manager.get_correlation_id()

        try:
            client = await self._get_client()
            # Use models endpoint to check availability
            models = await client.models.list()

            secure_logger.info(
                "LM Studio health check successful",
                correlation_id=correlation_id,
                available_models=len(models.data)
            )

            metrics.increment("lmstudio_health_success_total")
            return True

        except Exception as e:
            secure_logger.warning(
                "LM Studio health check failed",
                correlation_id=correlation_id,
                error=str(e)[:200]
            )
            metrics.increment("lmstudio_health_error_total")
            return False

    @circuit_breaker(
        name="lmstudio_list_models",
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=10.0,
        expected_exception=Exception
    )
    @track_performance("lmstudio_list_models")
    async def list_models(self) -> List[str]:
        """List available models."""
        correlation_id = correlation_manager.get_correlation_id()

        try:
            client = await self._get_client()
            models = await client.models.list()

            model_names = [model.id for model in models.data]

            secure_logger.info(
                "LM Studio models listed",
                correlation_id=correlation_id,
                model_count=len(model_names)
            )

            metrics.increment("lmstudio_list_models_success_total")
            metrics.record_histogram("lmstudio_model_count", len(model_names))

            return model_names

        except Exception as e:
            secure_logger.error(
                "Failed to list LM Studio models",
                correlation_id=correlation_id,
                error=str(e)[:200]
            )
            metrics.increment("lmstudio_list_models_error_total")
            return []

    @circuit_breaker(
        name="lmstudio_complete",
        failure_threshold=OLLAMA_BREAKER_CONFIG.failure_threshold,
        recovery_timeout=OLLAMA_BREAKER_CONFIG.recovery_timeout,
        success_threshold=OLLAMA_BREAKER_CONFIG.success_threshold,
        timeout=OLLAMA_BREAKER_CONFIG.timeout,
        expected_exception=Exception
    )
    @track_performance("lmstudio_complete")
    async def complete(
        self,
        prompt: str,
        model: str = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> CompletionResult:
        """
        Generate completion from prompt.
        
        Args:
            prompt: User prompt
            model: Model to use (defaults to configured default)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            CompletionResult with generated content
        """
        import time
        start_time = time.time()

        correlation_id = correlation_manager.get_correlation_id()
        model = model or self.default_model

        secure_logger.info(
            "LM Studio completion request",
            correlation_id=correlation_id,
            model=model,
            prompt_length=len(prompt),
            temperature=temperature
        )

        metrics.increment("lmstudio_completion_requests_total", tags={"model": model})

        try:
            client = await self._get_client()

            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Make completion request
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )

            if stream:
                # Handle streaming response
                content = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content

                tokens_used = len(content.split())  # Rough estimate
                finish_reason = "stop"
            else:
                # Handle non-streaming response
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0
                finish_reason = response.choices[0].finish_reason or "stop"

            duration_ms = int((time.time() - start_time) * 1000)

            result = CompletionResult(
                content=content,
                model=model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                duration_ms=duration_ms,
            )

            secure_logger.info(
                "LM Studio completion successful",
                correlation_id=correlation_id,
                model=model,
                tokens_used=tokens_used,
                duration_ms=duration_ms
            )

            metrics.increment("lmstudio_completion_success_total", tags={"model": model})
            metrics.record_histogram("lmstudio_completion_tokens", tokens_used, tags={"model": model})
            metrics.record_histogram("lmstudio_completion_duration", duration_ms, tags={"model": model})

            return result

        except Exception as e:
            secure_logger.error(
                "LM Studio completion failed",
                correlation_id=correlation_id,
                model=model,
                error=str(e)[:200],
                error_type=type(e).__name__
            )

            metrics.increment("lmstudio_completion_error_total", tags={"model": model, "error_type": type(e).__name__})
            raise

    async def analyze_code(
        self,
        code: str,
        language: str = "python",
        task: str = "explain",
    ) -> str:
        """
        Analyze code with appropriate prompt.
        
        Args:
            code: Source code to analyze
            language: Programming language
            task: Analysis task (explain, review, refactor, etc.)
            
        Returns:
            Analysis result as string
        """
        correlation_id = correlation_manager.get_correlation_id()

        prompts = {
            "explain": f"Explain this {language} code concisely:\n\n```{language}\n{code}\n```",
            "review": f"Review this {language} code for issues and improvements:\n\n```{language}\n{code}\n```",
            "refactor": f"Suggest refactoring for this {language} code:\n\n```{language}\n{code}\n```",
            "document": f"Generate docstrings for this {language} code:\n\n```{language}\n{code}\n```",
        }

        prompt = prompts.get(task, prompts["explain"])

        secure_logger.info(
            "LM Studio code analysis",
            correlation_id=correlation_id,
            task=task,
            language=language,
            code_length=len(code)
        )

        result = await self.complete(
            prompt=prompt,
            system_prompt="You are an expert code analyst. Be concise and specific.",
            temperature=0.3,
        )

        metrics.increment("lmstudio_code_analysis_total", tags={"task": task, "language": language})
        return result.content

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: str = None,
    ) -> str:
        """
        Generate code from description.
        
        Args:
            description: What to generate
            language: Target language
            context: Optional context code
            
        Returns:
            Generated code
        """
        correlation_id = correlation_manager.get_correlation_id()

        prompt = f"Generate {language} code for: {description}"

        if context:
            prompt += f"\n\nContext:\n```{language}\n{context}\n```"

        prompt += "\n\nRespond with only the code, no explanations."

        secure_logger.info(
            "LM Studio code generation",
            correlation_id=correlation_id,
            language=language,
            description_length=len(description),
            has_context=bool(context)
        )

        result = await self.complete(
            prompt=prompt,
            system_prompt="You are an expert programmer. Generate clean, well-documented code.",
            temperature=0.2,
        )

        # Extract code from response
        content = result.content

        # Try to extract from code blocks
        if "```" in content:
            lines = content.split("```")
            for i, block in enumerate(lines):
                if i % 2 == 1:  # Inside code block
                    # Remove language identifier
                    code_lines = block.split("\n")
                    if code_lines and code_lines[0].strip() in ["python", "javascript", "typescript", language]:
                        code_lines = code_lines[1:]
                    return "\n".join(code_lines).strip()

        metrics.increment("lmstudio_code_generation_total", tags={"language": language})
        return content

    async def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name (uses default if None)
            
        Returns:
            Model information dictionary
        """
        model = model or self.default_model
        correlation_id = correlation_manager.get_correlation_id()

        try:
            client = await self._get_client()
            models = await client.models.list()

            # Find the model
            for model_info in models.data:
                if model_info.id == model:
                    return {
                        "id": model_info.id,
                        "created": model_info.created,
                        "owned_by": model_info.owned_by,
                        "object": model_info.object,
                    }

            return {"id": model, "status": "not_found"}

        except Exception as e:
            secure_logger.error(
                "Failed to get LM Studio model info",
                correlation_id=correlation_id,
                model=model,
                error=str(e)[:200]
            )
            return {"id": model, "status": "error", "error": str(e)}
