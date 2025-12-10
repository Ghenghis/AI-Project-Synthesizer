"""
AI Project Synthesizer - Ollama Client

Client for local LLM inference using Ollama.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CompletionResult:
    """Result from LLM completion."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    duration_ms: int


class OllamaClient:
    """
    Client for Ollama local LLM inference.
    
    Supports Qwen2.5-Coder and other code-focused models.
    
    Usage:
        client = OllamaClient()
        result = await client.complete("Explain this code: def foo(): pass")
        print(result.content)
    """
    
    DEFAULT_MODELS = {
        "fast": "qwen2.5-coder:7b-instruct-q8_0",
        "balanced": "qwen2.5-coder:14b-instruct-q4_K_M", 
        "powerful": "qwen2.5-coder:32b-instruct-q4_K_M",
    }
    
    def __init__(
        self,
        host: str = "http://localhost:11434",
        default_model: str = None,
        timeout: float = 120.0,
    ):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server URL
            default_model: Default model to use
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip("/")
        self.default_model = default_model or self.DEFAULT_MODELS["balanced"]
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.host,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to list models: {e}")
        return []
    
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
            model: Model to use (defaults to balanced)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            CompletionResult with generated content
        """
        import time
        start_time = time.time()
        
        model = model or self.default_model
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Make request
        client = await self._get_client()
        
        try:
            response = await client.post(
                "/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.text}")
            
            data = response.json()
            
            content = data.get("message", {}).get("content", "")
            tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
            
            return CompletionResult(
                content=content,
                model=model,
                tokens_used=tokens,
                finish_reason=data.get("done_reason", "stop"),
                duration_ms=int((time.time() - start_time) * 1000),
            )
            
        except httpx.TimeoutException:
            raise Exception(f"Ollama request timed out after {self.timeout}s")
        except Exception as e:
            logger.error(f"Ollama completion failed: {e}")
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
        prompts = {
            "explain": f"Explain this {language} code concisely:\n\n```{language}\n{code}\n```",
            "review": f"Review this {language} code for issues and improvements:\n\n```{language}\n{code}\n```",
            "refactor": f"Suggest refactoring for this {language} code:\n\n```{language}\n{code}\n```",
            "document": f"Generate docstrings for this {language} code:\n\n```{language}\n{code}\n```",
        }
        
        prompt = prompts.get(task, prompts["explain"])
        
        result = await self.complete(
            prompt=prompt,
            system_prompt="You are an expert code analyst. Be concise and specific.",
            temperature=0.3,
        )
        
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
        prompt = f"Generate {language} code for: {description}"
        
        if context:
            prompt += f"\n\nContext:\n```{language}\n{context}\n```"
        
        prompt += f"\n\nRespond with only the code, no explanations."
        
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
        
        return content
