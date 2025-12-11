"""
AI Project Synthesizer - Base Agent

Foundation for all AI agents with:
- LLM integration
- Tool execution
- Memory management
- Auto-continue support
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod


from src.core.security import get_secure_logger
from src.automation.metrics import ActionTimer, get_metrics_collector

secure_logger = get_secure_logger(__name__)

T = TypeVar("T")


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentConfig:
    """Agent configuration."""
    name: str
    description: str = ""

    # LLM settings
    provider: str = "lmstudio"
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096

    # Behavior
    auto_continue: bool = True
    max_iterations: int = 10
    timeout_seconds: int = 300

    # Features
    enable_tools: bool = True
    enable_memory: bool = True
    enable_voice: bool = False

    # Callbacks
    on_step: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    output: Any
    steps: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0
    iterations: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "steps": self.steps,
            "duration_ms": self.duration_ms,
            "iterations": self.iterations,
            "error": self.error,
            "metadata": self.metadata,
        }


class AgentTool:
    """Tool that an agent can use."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

    async def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)

    def to_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class BaseAgent(ABC):
    """
    Base class for all AI agents.

    Features:
    - LLM integration with multiple providers
    - Tool execution
    - Memory management
    - Auto-continue support
    - Metrics collection
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self._tools: Dict[str, AgentTool] = {}
        self._memory: List[Dict[str, Any]] = []
        self._current_task: Optional[str] = None
        self._iterations = 0
        self._llm_client = None

    async def _get_llm(self):
        """Get LLM client."""
        if self._llm_client is None:
            from src.llm import LMStudioClient, OllamaClient

            if self.config.provider == "lmstudio":
                self._llm_client = LMStudioClient()
            else:
                self._llm_client = OllamaClient()

        return self._llm_client

    def register_tool(self, tool: AgentTool):
        """Register a tool for the agent."""
        self._tools[tool.name] = tool

    def add_memory(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add to agent memory."""
        self._memory.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })

    def clear_memory(self):
        """Clear agent memory."""
        self._memory = []

    @abstractmethod
    async def _execute_step(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step. Override in subclasses."""
        pass

    @abstractmethod
    def _should_continue(self, step_result: Dict[str, Any]) -> bool:
        """Determine if agent should continue. Override in subclasses."""
        pass

    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Run the agent on a task.

        Args:
            task: Task description
            context: Optional context data

        Returns:
            AgentResult with output and metadata
        """
        self.status = AgentStatus.RUNNING
        self._current_task = task
        self._iterations = 0
        context = context or {}
        steps = []

        collector = get_metrics_collector()

        async with ActionTimer(f"agent_{self.config.name}", collector) as timer:
            try:
                # Add task to memory
                self.add_memory("user", task)

                while self._iterations < self.config.max_iterations:
                    self._iterations += 1

                    # Execute step
                    step_result = await self._execute_step(task, context)
                    steps.append(step_result)

                    # Callback
                    if self.config.on_step:
                        try:
                            self.config.on_step(step_result)
                        except Exception:
                            pass

                    # Check if should continue
                    if not self.config.auto_continue or not self._should_continue(step_result):
                        break

                    # Update context with step result
                    context["previous_step"] = step_result

                # Get final output
                output = steps[-1].get("output") if steps else None

                self.status = AgentStatus.COMPLETED

                result = AgentResult(
                    success=True,
                    output=output,
                    steps=steps,
                    duration_ms=timer.elapsed_ms,
                    iterations=self._iterations,
                )

                # Callback
                if self.config.on_complete:
                    try:
                        self.config.on_complete(result)
                    except Exception:
                        pass

                return result

            except Exception as e:
                self.status = AgentStatus.FAILED
                secure_logger.error(f"Agent {self.config.name} failed: {e}")

                result = AgentResult(
                    success=False,
                    output=None,
                    steps=steps,
                    duration_ms=timer.elapsed_ms,
                    iterations=self._iterations,
                    error=str(e),
                )

                # Callback
                if self.config.on_error:
                    try:
                        self.config.on_error(e)
                    except Exception:
                        pass

                return result

    async def cancel(self):
        """Cancel agent execution."""
        self.status = AgentStatus.CANCELLED

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "name": self.config.name,
            "status": self.status.value,
            "current_task": self._current_task,
            "iterations": self._iterations,
            "tools": list(self._tools.keys()),
            "memory_size": len(self._memory),
        }
