"""
Mock LLM services for testing.
"""

from typing import Any
from unittest.mock import AsyncMock


class MockLiteLLMRouter:
    """Mock LiteLLM router for testing."""

    def __init__(self):
        self.completion = AsyncMock()
        self.responses = []
        self.call_count = 0

    def set_response(self, response: str):
        """Set the next response to return."""
        self.responses.append(response)

    async def complete(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Mock completion method."""
        self.call_count += 1
        if self.responses:
            response = self.responses.pop(0)
        else:
            response = f"Mock response to: {prompt[:50]}..."

        return {
            "choices": [{"message": {"content": response}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        }


class MockOllamaClient:
    """Mock Ollama client for testing."""

    def __init__(self):
        self.generate = AsyncMock()
        self.models = ["qwen2.5-coder", "llama3.1", "mistral"]
        self.responses = []

    def set_response(self, response: str):
        """Set the next response to return."""
        self.responses.append(response)

    async def generate(self, model: str, prompt: str, **kwargs) -> dict[str, Any]:
        """Mock generate method."""
        if self.responses:
            response = self.responses.pop(0)
        else:
            response = f"Mock {model} response to: {prompt[:50]}..."

        return {
            "response": response,
            "model": model,
            "created_at": "2024-01-01T00:00:00Z",
            "done": True,
        }

    def list_models(self) -> list[str]:
        """List available models."""
        return self.models


class MockMemorySystem:
    """Mock memory system for testing."""

    def __init__(self):
        self.memories = []
        self.add_memory = AsyncMock(side_effect=self._add_memory)
        self.search_memories = AsyncMock(side_effect=self._search_memories)

    def set_memories(self, memories: list[dict[str, Any]]):
        """Set memories to return from search."""
        self.memories = memories

    async def _add_memory(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Mock add memory method."""
        memory = {
            "id": f"mock_memory_{len(self.memories)}",
            "content": content,
            "metadata": metadata or {},
            "created_at": "2024-01-01T00:00:00Z",
        }
        self.memories.append(memory)
        return memory

    async def _search_memories(
        self, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Mock search memories method."""
        return self.memories[:limit]
