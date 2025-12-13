"""
AI Project Synthesizer - Unified Workflow Orchestrator

Central orchestrator that coordinates:
- LangChain workflows
- Pydantic AI agents
- n8n automation
- Voice interactions
- Project assembly
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.cache import cached, get_cache
from src.core.security import get_secure_logger
from src.core.telemetry import get_telemetry

secure_logger = get_secure_logger(__name__)


class WorkflowType(str, Enum):
    """Types of workflows."""
    RESEARCH = "research"
    SYNTHESIS = "synthesis"
    CONVERSATION = "conversation"
    VOICE = "voice"
    AUTOMATION = "automation"


class WorkflowEngine(str, Enum):
    """Workflow execution engines."""
    LANGCHAIN = "langchain"
    PYDANTIC_AI = "pydantic_ai"
    N8N = "n8n"
    NATIVE = "native"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    engine: WorkflowEngine
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: int = 60


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    id: str
    name: str
    workflow_type: WorkflowType
    steps: list[WorkflowStep]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0
    steps_completed: int = 0


class WorkflowOrchestrator:
    """
    Unified workflow orchestrator.

    Coordinates multiple workflow engines:
    - LangChain for LLM chains
    - Pydantic AI for type-safe agents
    - n8n for visual automation
    - Native Python for custom logic

    Usage:
        orchestrator = WorkflowOrchestrator()

        # Run a research workflow
        result = await orchestrator.research("machine learning chatbot")

        # Run a full synthesis workflow
        result = await orchestrator.synthesize_project("RAG chatbot", create_github=True)

        # Execute custom workflow
        result = await orchestrator.execute(workflow_definition)
    """

    def __init__(self):
        """Initialize orchestrator."""
        self._langchain = None
        self._n8n = None
        self._cache = get_cache()
        self._telemetry = get_telemetry()

    async def _get_langchain(self):
        """Get LangChain orchestrator."""
        if self._langchain is None:
            from src.workflows.langchain_integration import LangChainOrchestrator
            self._langchain = LangChainOrchestrator()
        return self._langchain

    async def _get_n8n(self):
        """Get n8n client."""
        if self._n8n is None:
            from src.workflows.n8n_integration import N8NClient
            self._n8n = N8NClient()
        return self._n8n

    # ============================================
    # High-Level Workflows
    # ============================================

    @cached(ttl_seconds=1800, key_prefix="research")
    async def research(
        self,
        query: str,
        platforms: list[str] = None,
        use_cache: bool = True,
    ) -> WorkflowResult:
        """
        Research workflow - Find resources for a project idea.

        Steps:
        1. Analyze query with LLM
        2. Search platforms in parallel
        3. Rank and filter results
        4. Generate recommendations
        """
        start_time = asyncio.get_event_loop().time()
        platforms = platforms or ["github", "huggingface", "kaggle"]

        try:
            # Step 1: Analyze query
            langchain = await self._get_langchain()
            analysis = await langchain.research(query)

            # Step 2: Search platforms
            from src.discovery.unified_search import create_unified_search
            search = create_unified_search()
            results = await search.search(query, platforms=platforms, max_results=10)

            # Step 3: Compile results
            duration = (asyncio.get_event_loop().time() - start_time) * 1000

            self._telemetry.track_search(platforms, len(results.repositories), duration)

            return WorkflowResult(
                workflow_id="research",
                success=True,
                data={
                    "query": query,
                    "analysis": analysis,
                    "results": [
                        {
                            "name": r.name,
                            "url": r.url,
                            "platform": r.platform,
                            "stars": r.stars,
                            "description": r.description,
                        }
                        for r in results.repositories
                    ],
                    "total": len(results.repositories),
                },
                duration_ms=duration,
                steps_completed=3,
            )

        except Exception as e:
            secure_logger.error(f"Research workflow failed: {e}")
            return WorkflowResult(
                workflow_id="research",
                success=False,
                errors=[str(e)],
                duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            )

    async def synthesize_project(
        self,
        idea: str,
        name: str | None = None,
        output_dir: str = "G:/",
        create_github: bool = True,
    ) -> WorkflowResult:
        """
        Full project synthesis workflow.

        Steps:
        1. Research resources
        2. Plan synthesis with LLM
        3. Download resources
        4. Assemble project structure
        5. Generate documentation
        6. Create GitHub repo (optional)
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Step 1: Research
            research_result = await self.research(idea)
            if not research_result.success:
                return research_result

            # Step 2: Plan with LangChain
            langchain = await self._get_langchain()
            synthesis_plan = await langchain.synthesize(
                idea,
                research_result.data.get("results", []),
            )

            # Step 3-6: Assemble project
            from src.synthesis.project_assembler import (
                AssemblerConfig,
                ProjectAssembler,
            )

            config = AssemblerConfig(
                base_output_dir=Path(output_dir),
                create_github_repo=create_github,
            )

            assembler = ProjectAssembler(config)
            project = await assembler.assemble(idea, name)

            duration = (asyncio.get_event_loop().time() - start_time) * 1000

            self._telemetry.track_assembly(
                success=True,
                resources_count=len(project.code_repos) + len(project.models),
                duration_ms=duration,
            )

            return WorkflowResult(
                workflow_id="synthesis",
                success=True,
                data={
                    "project_name": project.name,
                    "project_path": str(project.base_path),
                    "github_url": project.github_repo_url,
                    "resources": {
                        "code_repos": len(project.code_repos),
                        "models": len(project.models),
                        "datasets": len(project.datasets),
                        "papers": len(project.papers),
                    },
                    "synthesis_plan": synthesis_plan,
                },
                duration_ms=duration,
                steps_completed=6,
            )

        except Exception as e:
            secure_logger.error(f"Synthesis workflow failed: {e}")
            self._telemetry.track_error("synthesis_failed")
            return WorkflowResult(
                workflow_id="synthesis",
                success=False,
                errors=[str(e)],
                duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            )

    async def conversation(
        self,
        message: str,
        context: dict[str, Any] = None,
        use_voice: bool = False,
    ) -> WorkflowResult:
        """
        Conversation workflow with optional voice.

        Steps:
        1. Process message with Pydantic AI agent
        2. Execute detected action
        3. Generate response
        4. Speak response (if voice enabled)
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Step 1: Process with Pydantic AI
            from src.llm.pydantic_ai_agent import chat
            response = await chat(message, context)

            # Step 2: Execute action if detected
            action_result = None
            if response.action:
                action_result = await self._execute_action(
                    response.action,
                    response.parameters,
                )

            # Step 3: Generate final response
            final_message = response.message
            if action_result:
                final_message += f"\n\n{action_result}"

            # Step 4: Voice output
            audio_path = None
            if use_voice:
                from src.voice.elevenlabs_client import ElevenLabsClient
                client = ElevenLabsClient()
                audio_path = await client.generate_speech(final_message)

            return WorkflowResult(
                workflow_id="conversation",
                success=True,
                data={
                    "message": final_message,
                    "intent": response.intent,
                    "action": response.action,
                    "action_result": action_result,
                    "follow_up_questions": response.follow_up_questions,
                    "audio_path": audio_path,
                },
                duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                steps_completed=4 if use_voice else 3,
            )

        except Exception as e:
            secure_logger.error(f"Conversation workflow failed: {e}")
            return WorkflowResult(
                workflow_id="conversation",
                success=False,
                errors=[str(e)],
            )

    async def _execute_action(
        self,
        action: str,
        parameters: dict[str, Any],
    ) -> str | None:
        """Execute a detected action."""
        if action == "search":
            result = await self.research(parameters.get("query", ""))
            return f"Found {result.data.get('total', 0)} resources"

        elif action == "build":
            result = await self.synthesize_project(parameters.get("idea", ""))
            if result.success:
                return f"Project created at: {result.data.get('project_path')}"
            return f"Build failed: {result.errors}"

        return None

    # ============================================
    # Custom Workflow Execution
    # ============================================

    async def execute(self, workflow: WorkflowDefinition) -> WorkflowResult:
        """
        Execute a custom workflow definition.

        Supports mixed engines (LangChain, Pydantic AI, n8n).
        """
        start_time = asyncio.get_event_loop().time()
        results = {}
        errors = []
        steps_completed = 0

        # Build dependency graph
        pending = {step.name: step for step in workflow.steps}
        completed = set()

        while pending:
            # Find steps with satisfied dependencies
            ready = [
                name for name, step in pending.items()
                if all(dep in completed for dep in step.depends_on)
            ]

            if not ready:
                errors.append("Circular dependency detected")
                break

            # Execute ready steps in parallel
            tasks = []
            for name in ready:
                step = pending.pop(name)
                tasks.append(self._execute_step(step, results))

            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in zip(ready, step_results, strict=False):
                if isinstance(result, Exception):
                    errors.append(f"{name}: {result}")
                else:
                    results[name] = result
                    completed.add(name)
                    steps_completed += 1

        return WorkflowResult(
            workflow_id=workflow.id,
            success=len(errors) == 0,
            data=results,
            errors=errors,
            duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            steps_completed=steps_completed,
        )

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: dict[str, Any],
    ) -> Any:
        """Execute a single workflow step."""
        # Inject context into parameters
        params = {**step.parameters, "_context": context}

        if step.engine == WorkflowEngine.LANGCHAIN:
            langchain = await self._get_langchain()
            if step.action == "research":
                return await langchain.research(params.get("query", ""))
            elif step.action == "synthesize":
                return await langchain.synthesize(
                    params.get("idea", ""),
                    params.get("resources", []),
                )
            elif step.action == "chat":
                return await langchain.chat(params.get("message", ""))

        elif step.engine == WorkflowEngine.PYDANTIC_AI:
            from src.llm.pydantic_ai_agent import (
                chat,
                research_project,
                synthesize_project,
            )
            if step.action == "research":
                return await research_project(params.get("query", ""))
            elif step.action == "synthesize":
                return await synthesize_project(
                    params.get("idea", ""),
                    params.get("resources", []),
                )
            elif step.action == "chat":
                return await chat(params.get("message", ""))

        elif step.engine == WorkflowEngine.N8N:
            n8n = await self._get_n8n()
            return await n8n.execute_workflow(
                params.get("workflow_id", ""),
                params,
            )

        elif step.engine == WorkflowEngine.NATIVE:
            # Execute native Python function
            func = params.get("_function")
            if callable(func):
                return await func(**{k: v for k, v in params.items() if not k.startswith("_")})

        raise ValueError(f"Unknown engine/action: {step.engine}/{step.action}")


# Global orchestrator instance
_orchestrator: WorkflowOrchestrator | None = None


def get_orchestrator() -> WorkflowOrchestrator:
    """Get or create workflow orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestrator()
    return _orchestrator
