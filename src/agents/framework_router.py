"""
VIBE MCP - Framework Router

Unified interface for all agent frameworks with dynamic selection.
Implements Phase 3.5 of the VIBE MCP roadmap.

Features:
- Consistent interface across AutoGen, Swarm, LangGraph, and CrewAI
- Dynamic framework selection based on task characteristics
- Automatic fallback handling
- Framework-agnostic task execution
- Performance metrics and optimization
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# Import all framework integrations
from src.agents.autogen_integration import AutoGenIntegration
from src.agents.crewai_integration import CrewAIIntegration
from src.agents.langgraph_integration import LangGraphIntegration
from src.agents.swarm_integration import SwarmIntegration
from src.core.security import get_secure_logger
from src.llm.litellm_router import LiteLLMRouter
from src.voice.manager import VoiceManager

secure_logger = get_secure_logger(__name__)


class TaskType(Enum):
    """Types of tasks that can be executed."""
    CODE_REVIEW = "code_review"
    QUICK_FIX = "quick_fix"
    TASK_DECOMPOSITION = "task_decomposition"
    DOCUMENTATION = "documentation"
    SECURITY_AUDIT = "security_audit"
    STATEFUL_WORKFLOW = "stateful_workflow"
    TEAM_COLLABORATION = "team_collaboration"
    DEBUGGING = "debugging"
    FEATURE_DEVELOPMENT = "feature_development"


class TaskComplexity(Enum):
    """Complexity levels for tasks."""
    SIMPLE = "simple"      # Single agent, quick response
    MEDIUM = "medium"      # May require multiple steps
    COMPLEX = "complex"    # Requires multiple agents or workflows
    ENTERPRISE = "enterprise"  # Large-scale, full team needed


class FrameworkType(Enum):
    """Available agent frameworks."""
    AUTOGEN = "autogen"
    SWARM = "swarm"
    LANGGRAPH = "langgraph"
    CREWAI = "crewai"


@dataclass
class TaskRequest:
    """A unified task request for any framework."""
    task_id: str
    task_type: TaskType
    description: str
    complexity: TaskComplexity
    context: dict[str, Any] = field(default_factory=dict)
    force_framework: FrameworkType | None = None
    enable_voice: bool = False
    require_persistence: bool = False
    require_human_input: bool = False
    team_size: int = 1


@dataclass
class AgentResult:
    """Unified result from any agent framework."""
    task_id: str
    success: bool
    output: str
    framework_used: FrameworkType
    execution_time_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    # Common metrics
    quality_score: float = 0.0
    tokens_used: int = 0
    error_message: str | None = None

    # Framework-specific metrics
    agent_count: int = 1
    checkpoint_count: int = 0
    human_interventions: int = 0

    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


class FrameworkRouter:
    """
    Unified router for all agent frameworks.

    Provides a consistent interface and automatically selects
    the optimal framework based on task characteristics.
    """

    def __init__(
        self,
        voice_manager: VoiceManager | None = None,
        llm_router: LiteLLMRouter | None = None
    ):
        """
        Initialize the framework router.

        Args:
            voice_manager: VoiceManager for spoken feedback
            llm_router: LiteLLM router for unified LLM access
        """
        self.voice_manager = voice_manager
        self.llm_router = llm_router or LiteLLMRouter()

        # Framework integrations
        self.integrations: dict[FrameworkType, Any] = {}

        # Performance tracking
        self.execution_history: list[AgentResult] = []
        self.framework_performance: dict[FrameworkType, dict[str, float]] = {
            ft: {"success_rate": 0.0, "avg_time": 0.0, "usage_count": 0}
            for ft in FrameworkType
        }

        # Initialize all integrations
        self._initialize_integrations()

        secure_logger.info("Framework Router initialized")
        secure_logger.info(f"  Available frameworks: {list(self.integrations.keys())}")

    def _initialize_integrations(self):
        """Initialize all framework integrations."""
        # AutoGen - for complex code review
        try:
            self.integrations[FrameworkType.AUTOGEN] = AutoGenIntegration(
                voice_manager=self.voice_manager,
                enable_voice_output=False,
                llm_router=self.llm_router
            )
            secure_logger.info("AutoGen integration loaded")
        except Exception as e:
            secure_logger.warning(f"Failed to load AutoGen: {e}")

        # Swarm - for quick handoffs
        try:
            self.integrations[FrameworkType.SWARM] = SwarmIntegration(
                voice_manager=self.voice_manager,
                enable_voice_output=False,
                llm_router=self.llm_router
            )
            secure_logger.info("Swarm integration loaded")
        except Exception as e:
            secure_logger.warning(f"Failed to load Swarm: {e}")

        # LangGraph - for stateful workflows
        try:
            self.integrations[FrameworkType.LANGGRAPH] = LangGraphIntegration(
                voice_manager=self.voice_manager,
                enable_voice_output=False,
                llm_router=self.llm_router
            )
            secure_logger.info("LangGraph integration loaded")
        except Exception as e:
            secure_logger.warning(f"Failed to load LangGraph: {e}")

        # CrewAI - for team collaboration
        try:
            self.integrations[FrameworkType.CREWAI] = CrewAIIntegration(
                voice_manager=self.voice_manager,
                enable_voice_output=False,
                llm_router=self.llm_router
            )
            secure_logger.info("CrewAI integration loaded")
        except Exception as e:
            secure_logger.warning(f"Failed to load CrewAI: {e}")

    def select_framework(
        self,
        task: TaskRequest
    ) -> list[FrameworkType]:
        """
        Select the best framework(s) for a task.

        Returns ordered list of frameworks to try (primary first).
        """
        if task.force_framework:
            return [task.force_framework]

        # Score each framework based on task characteristics
        framework_scores = {}

        for framework in FrameworkType:
            if framework not in self.integrations:
                continue

            score = self._score_framework_for_task(framework, task)
            framework_scores[framework] = score

        # Sort by score (highest first)
        sorted_frameworks = sorted(
            framework_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [fw for fw, _ in sorted_frameworks]

    def _score_framework_for_task(
        self,
        framework: FrameworkType,
        task: TaskRequest
    ) -> float:
        """Score a framework's suitability for a task."""
        score = 0.0

        # Base scores for each framework
        base_scores = {
            FrameworkType.AUTOGEN: 7.0,    # Good for complex analysis
            FrameworkType.SWARM: 9.0,      # Excellent for quick tasks
            FrameworkType.LANGGRAPH: 8.0,  # Great for workflows
            FrameworkType.CREWAI: 6.0      # Best for large teams
        }

        score = base_scores.get(framework, 0.0)

        # Adjust based on task type
        task_type_bonus = {
            FrameworkType.AUTOGEN: {
                TaskType.CODE_REVIEW: 3.0,
                TaskType.SECURITY_AUDIT: 2.0
            },
            FrameworkType.SWARM: {
                TaskType.QUICK_FIX: 2.0,
                TaskType.DOCUMENTATION: 1.5,
                TaskType.TASK_DECOMPOSITION: 1.0
            },
            FrameworkType.LANGGRAPH: {
                TaskType.STATEFUL_WORKFLOW: 3.0,
                TaskType.DEBUGGING: 2.0,
                TaskType.FEATURE_DEVELOPMENT: 1.5
            },
            FrameworkType.CREWAI: {
                TaskType.TEAM_COLLABORATION: 3.0,
                TaskType.FEATURE_DEVELOPMENT: 2.5,
                TaskType.SECURITY_AUDIT: 2.0
            }
        }

        if framework in task_type_bonus:
            score += task_type_bonus[framework].get(task.task_type, 0.0)

        # Adjust based on complexity
        if task.complexity == TaskComplexity.SIMPLE:
            if framework == FrameworkType.SWARM:
                score += 2.0
            elif framework == FrameworkType.CREWAI:
                score -= 2.0
        elif task.complexity == TaskComplexity.ENTERPRISE:
            if framework == FrameworkType.CREWAI:
                score += 2.0
            elif framework == FrameworkType.SWARM:
                score -= 2.0

        # Adjust based on requirements
        if task.require_persistence and framework == FrameworkType.LANGGRAPH:
            score += 2.0

        if task.require_human_input and framework == FrameworkType.LANGGRAPH:
            score += 1.5

        if task.team_size > 3 and framework == FrameworkType.CREWAI:
            score += 2.0

        # Adjust based on historical performance
        perf = self.framework_performance[framework]
        if perf["usage_count"] > 0:
            score += perf["success_rate"] / 10
            score -= min(perf["avg_time"] / 1000, 1.0)  # Penalize slow frameworks

        return score

    async def execute_task(self, task: TaskRequest) -> AgentResult:
        """
        Execute a task using the optimal framework.

        Args:
            task: The task to execute

        Returns:
            AgentResult with the execution outcome
        """
        # Select frameworks to try
        frameworks = self.select_framework(task)

        if not frameworks:
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output="No suitable framework available",
                framework_used=FrameworkType.AUTOGEN,  # Default
                execution_time_ms=0.0,
                error_message="All frameworks failed to initialize"
            )

        # Try each framework in order
        for framework in frameworks:
            try:
                secure_logger.info(f"Trying framework: {framework.value}")

                # Execute with the selected framework
                result = await self._execute_with_framework(framework, task)

                # Update performance metrics
                self._update_performance_metrics(framework, result)

                # Store in history
                self.execution_history.append(result)

                # Return if successful
                if result.success:
                    secure_logger.info(f"Task completed with {framework.value}")
                    return result

                # Continue to next framework if this failed
                secure_logger.warning(f"{framework.value} failed: {result.error_message}")

            except Exception as e:
                secure_logger.error(f"Framework {framework.value} crashed: {e}")
                continue

        # All frameworks failed
        return AgentResult(
            task_id=task.task_id,
            success=False,
            output="All frameworks failed to execute the task",
            framework_used=frameworks[0] if frameworks else FrameworkType.AUTOGEN,
            execution_time_ms=0.0,
            error_message="No framework could handle the task"
        )

    async def _execute_with_framework(
        self,
        framework: FrameworkType,
        task: TaskRequest
    ) -> AgentResult:
        """Execute a task with a specific framework."""
        start_time = asyncio.get_event_loop().time()
        result = None

        try:
            if framework == FrameworkType.AUTOGEN:
                result = await self._execute_with_autogen(task)
            elif framework == FrameworkType.SWARM:
                result = await self._execute_with_swarm(task)
            elif framework == FrameworkType.LANGGRAPH:
                result = await self._execute_with_langgraph(task)
            elif framework == FrameworkType.CREWAI:
                result = await self._execute_with_crewai(task)
            else:
                raise ValueError(f"Unknown framework: {framework}")

        finally:
            # Calculate execution time
            end_time = asyncio.get_event_loop().time()
            execution_time = (end_time - start_time) * 1000

            # Update the result with execution time
            if result is not None:
                result.execution_time_ms = execution_time
                result.completed_at = datetime.now()

            # Return result if it exists, otherwise create a failure result
            if result is None:
                result = AgentResult(
                    task_id=task.task_id,
                    success=False,
                    output="Framework execution failed",
                    framework_used=framework,
                    execution_time_ms=execution_time,
                    error_message="Exception during execution"
                )

            return result

    async def _execute_with_autogen(self, task: TaskRequest) -> AgentResult:
        """Execute task using AutoGen."""
        integration = self.integrations[FrameworkType.AUTOGEN]

        # Map task to AutoGen code review
        if task.task_type in [TaskType.CODE_REVIEW, TaskType.SECURITY_AUDIT]:
            autogen_result = await integration.review_code(
                code=task.context.get("code", ""),
                file_path=task.context.get("file_path", "unknown.py"),
                context=task.description
            )

            return AgentResult(
                task_id=task.task_id,
                success=autogen_result.approved,
                output=autogen_result.agent_consensus,
                framework_used=FrameworkType.AUTOGEN,
                execution_time_ms=0.0,  # Will be set by caller
                metadata={
                    "security_issues": autogen_result.security_issues,
                    "suggestions": autogen_result.suggestions
                },
                quality_score=autogen_result.code_quality_score,
                agent_count=2  # Code reviewer + security analyst
            )
        else:
            # Default fallback
            return AgentResult(
                task_id=task.task_id,
                success=False,
                output="AutoGen only supports code review tasks",
                framework_used=FrameworkType.AUTOGEN,
                execution_time_ms=0.0,
                error_message="Unsupported task type for AutoGen"
            )

    async def _execute_with_swarm(self, task: TaskRequest) -> AgentResult:
        """Execute task using Swarm."""
        integration = self.integrations[FrameworkType.SWARM]

        # Map task to Swarm agents
        if task.task_type == TaskType.QUICK_FIX:
            swarm_result = await integration.quick_fix(
                code=task.context.get("code", ""),
                error_message=task.context.get("error")
            )

            return AgentResult(
                task_id=task.task_id,
                success=True,
                output=swarm_result,
                framework_used=FrameworkType.SWARM,
                execution_time_ms=0.0,
                quality_score=8.0,  # Assume good quality for quick fixes
                agent_count=1
            )

        elif task.task_type == TaskType.DOCUMENTATION:
            swarm_result = await integration.generate_docs(
                code=task.context.get("code", ""),
                doc_type=task.context.get("doc_type", "docstring")
            )

            return AgentResult(
                task_id=task.task_id,
                success=True,
                output=swarm_result,
                framework_used=FrameworkType.SWARM,
                execution_time_ms=0.0,
                quality_score=7.5,
                agent_count=1
            )

        elif task.task_type == TaskType.TASK_DECOMPOSITION:
            swarm_result = await integration.quick_handoff(
                agent_name="task_decomposer",
                message=task.description
            )

            return AgentResult(
                task_id=task.task_id,
                success=swarm_result.success,
                output=swarm_result.response,
                framework_used=FrameworkType.SWARM,
                execution_time_ms=0.0,
                metadata={"handoffs": swarm_result.handoff_count},
                quality_score=7.0,
                agent_count=1 + swarm_result.handoff_count
            )
        else:
            # Try general handoff
            swarm_result = await integration.quick_handoff(
                agent_name="code_helper",
                message=task.description
            )

            return AgentResult(
                task_id=task.task_id,
                success=swarm_result.success,
                output=swarm_result.response,
                framework_used=FrameworkType.SWARM,
                execution_time_ms=0.0,
                metadata={"handoffs": swarm_result.handoff_count},
                quality_score=6.5,
                agent_count=1 + swarm_result.handoff_count
            )

    async def _execute_with_langgraph(self, task: TaskRequest) -> AgentResult:
        """Execute task using LangGraph."""
        integration = self.integrations[FrameworkType.LANGGRAPH]

        # Map task to LangGraph workflows
        workflow_map = {
            TaskType.CODE_REVIEW: "code_review",
            TaskType.TASK_DECOMPOSITION: "task_decomposition",
            TaskType.DOCUMENTATION: "documentation",
            TaskType.DEBUGGING: "debug"
        }

        workflow_name = workflow_map.get(task.task_type, "code_review")

        langgraph_result = await integration.run_workflow(
            workflow_name=workflow_name,
            task_description=task.description,
            context=task.context
        )

        # Extract output from final state
        output = "Workflow completed"
        if langgraph_result.final_state.get("results"):
            if langgraph_result.final_state["results"].get("report"):
                output = langgraph_result.final_state["results"]["report"].get("summary", output)
            elif langgraph_result.final_state["results"].get("steps"):
                output = "\n".join(langgraph_result.final_state["results"]["steps"])

        return AgentResult(
            task_id=task.task_id,
            success=langgraph_result.status.value == "completed",
            output=output,
            framework_used=FrameworkType.LANGGRAPH,
            execution_time_ms=langgraph_result.execution_time_ms,
            metadata={
                "status": langgraph_result.status.value,
                "steps_completed": langgraph_result.steps_completed,
                "total_steps": langgraph_result.total_steps
            },
            quality_score=8.0 if langgraph_result.status.value == "completed" else 4.0,
            checkpoint_count=langgraph_result.checkpoints_created,
            human_interventions=langgraph_result.human_interventions,
            agent_count=langgraph_result.total_steps
        )

    async def _execute_with_crewai(self, task: TaskRequest) -> AgentResult:
        """Execute task using CrewAI."""
        integration = self.integrations[FrameworkType.CREWAI]

        # Map task to CrewAI teams
        if task.task_type == TaskType.FEATURE_DEVELOPMENT:
            crewai_result = await integration.create_feature(
                feature_description=task.description,
                requirements=task.context.get("requirements", [])
            )

            return AgentResult(
                task_id=task.task_id,
                success=crewai_result.success,
                output=crewai_result.final_output,
                framework_used=FrameworkType.CREWAI,
                execution_time_ms=crewai_result.execution_time_ms,
                metadata={"team": "development"},
                quality_score=crewai_result.quality_score,
                agent_count=4  # Development team size
            )

        elif task.task_type == TaskType.SECURITY_AUDIT:
            crewai_result = await integration.audit_security(
                codebase_description=task.description,
                focus_areas=task.context.get("focus_areas", [])
            )

            return AgentResult(
                task_id=task.task_id,
                success=crewai_result.success,
                output=crewai_result.final_output,
                framework_used=FrameworkType.CREWAI,
                execution_time_ms=crewai_result.execution_time_ms,
                metadata={"team": "security_audit"},
                quality_score=crewai_result.quality_score,
                agent_count=4  # Security team size
            )

        elif task.task_type == TaskType.DOCUMENTATION:
            crewai_result = await integration.generate_documentation(
                project_description=task.description,
                doc_type=task.context.get("doc_type", "user_guide")
            )

            return AgentResult(
                task_id=task.task_id,
                success=crewai_result.success,
                output=crewai_result.final_output,
                framework_used=FrameworkType.CREWAI,
                execution_time_ms=crewai_result.execution_time_ms,
                metadata={"team": "documentation"},
                quality_score=crewai_result.quality_score,
                agent_count=4  # Documentation team size
            )
        else:
            # Default to development team
            crewai_result = await integration.create_feature(
                feature_description=task.description,
                requirements=[]
            )

            return AgentResult(
                task_id=task.task_id,
                success=crewai_result.success,
                output=crewai_result.final_output,
                framework_used=FrameworkType.CREWAI,
                execution_time_ms=crewai_result.execution_time_ms,
                metadata={"team": "development"},
                quality_score=crewai_result.quality_score,
                agent_count=4
            )

    def _update_performance_metrics(
        self,
        framework: FrameworkType,
        result: AgentResult
    ):
        """Update performance metrics for a framework."""
        metrics = self.framework_performance[framework]

        # Update usage count
        metrics["usage_count"] += 1

        # Update success rate (exponential moving average)
        alpha = 0.1  # Learning rate
        if metrics["usage_count"] == 1:
            metrics["success_rate"] = 100.0 if result.success else 0.0
        else:
            current_success = 100.0 if result.success else 0.0
            metrics["success_rate"] = (
                alpha * current_success +
                (1 - alpha) * metrics["success_rate"]
            )

        # Update average time (exponential moving average)
        if metrics["usage_count"] == 1:
            metrics["avg_time"] = result.execution_time_ms
        else:
            metrics["avg_time"] = (
                alpha * result.execution_time_ms +
                (1 - alpha) * metrics["avg_time"]
            )

    async def get_framework_status(self) -> dict[str, Any]:
        """Get status of all frameworks."""
        status = {}

        for framework, integration in self.integrations.items():
            metrics = self.framework_performance[framework]

            status[framework.value] = {
                "available": integration is not None,
                "usage_count": metrics["usage_count"],
                "success_rate": metrics["success_rate"],
                "average_time_ms": metrics["avg_time"]
            }

            # Get framework-specific stats
            if integration:
                try:
                    if hasattr(integration, 'get_statistics'):
                        fw_stats = integration.get_statistics()
                        status[framework.value]["framework_stats"] = fw_stats
                except Exception as e:
                    secure_logger.warning(f"Failed to get stats for {framework.value}: {e}")

        return status

    async def get_execution_history(self, limit: int = 10) -> list[AgentResult]:
        """Get recent execution history."""
        return self.execution_history[-limit:]

    def get_optimal_framework_for_task_type(self, task_type: TaskType) -> FrameworkType:
        """Get the historically best framework for a task type."""
        # Filter history by task type
        relevant_results = [
            r for r in self.execution_history
            if r.metadata.get("task_type") == task_type.value
        ]

        if not relevant_results:
            # Return default based on task type
            defaults = {
                TaskType.CODE_REVIEW: FrameworkType.AUTOGEN,
                TaskType.QUICK_FIX: FrameworkType.SWARM,
                TaskType.STATEFUL_WORKFLOW: FrameworkType.LANGGRAPH,
                TaskType.TEAM_COLLABORATION: FrameworkType.CREWAI
            }
            return defaults.get(task_type, FrameworkType.SWARM)

        # Find framework with best success rate and quality
        framework_scores = {}
        for result in relevant_results:
            fw = result.framework_used
            if fw not in framework_scores:
                framework_scores[fw] = {"success": 0, "total": 0, "quality": 0}

            framework_scores[fw]["total"] += 1
            if result.success:
                framework_scores[fw]["success"] += 1
            framework_scores[fw]["quality"] += result.quality_score

        # Calculate best framework
        best_framework = None
        best_score = -1

        for fw, scores in framework_scores.items():
            success_rate = scores["success"] / scores["total"]
            avg_quality = scores["quality"] / scores["total"]
            combined_score = (success_rate * 0.7) + (avg_quality / 10 * 0.3)

            if combined_score > best_score:
                best_score = combined_score
                best_framework = fw

        return best_framework or FrameworkType.SWARM


# Factory function
async def create_framework_router(
    voice_manager: VoiceManager | None = None,
    llm_router: LiteLLMRouter | None = None
) -> FrameworkRouter:
    """
    Create and initialize the framework router.

    Args:
        voice_manager: VoiceManager for spoken feedback
        llm_router: LiteLLM router for unified LLM access

    Returns:
        Initialized FrameworkRouter
    """
    router = FrameworkRouter(
        voice_manager=voice_manager,
        llm_router=llm_router
    )

    # Test that at least one framework is available
    if not router.integrations:
        raise RuntimeError("No agent frameworks could be initialized")

    secure_logger.info(f"Framework router created with {len(router.integrations)} frameworks")
    return router


# CLI interface for testing
async def main():
    """Test the framework router."""
    import argparse

    parser = argparse.ArgumentParser(description="Framework Router Test")
    parser.add_argument("--status", action="store_true", help="Show framework status")
    parser.add_argument("--code-review", help="Code to review")
    parser.add_argument("--quick-fix", help="Code to fix")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--framework", help="Force specific framework")
    parser.add_argument("--history", action="store_true", help="Show execution history")

    args = parser.parse_args()

    # Create router
    router = await create_framework_router()

    if args.status:
        status = await router.get_framework_status()
        print("Framework Status:")
        for fw, info in status.items():
            print(f"\n  {fw}:")
            print(f"    Available: {info['available']}")
            print(f"    Usage Count: {info['usage_count']}")
            print(f"    Success Rate: {info['success_rate']:.1f}%")
            print(f"    Avg Time: {info['average_time_ms']:.2f}ms")

    if args.code_review:
        task = TaskRequest(
            task_id="test_review",
            task_type=TaskType.CODE_REVIEW,
            description="Review this code",
            complexity=TaskComplexity.MEDIUM,
            context={"code": args.code_review, "file_path": "test.py"},
            force_framework=FrameworkType(args.framework) if args.framework else None
        )

        print("Executing code review...")
        result = await router.execute_task(task)

        print(f"\nResult: {'Success' if result.success else 'Failed'}")
        print(f"Framework: {result.framework_used.value}")
        print(f"Quality Score: {result.quality_score:.1f}/10")
        print(f"Execution Time: {result.execution_time_ms:.2f}ms")
        print(f"\nOutput:\n{result.output[:500]}...")

    if args.quick_fix:
        task = TaskRequest(
            task_id="test_fix",
            task_type=TaskType.QUICK_FIX,
            description="Fix this code",
            complexity=TaskComplexity.SIMPLE,
            context={"code": args.quick_fix},
            force_framework=FrameworkType(args.framework) if args.framework else None
        )

        print("Executing quick fix...")
        result = await router.execute_task(task)

        print(f"\nResult: {'Success' if result.success else 'Failed'}")
        print(f"Framework: {result.framework_used.value}")
        print(f"\nOutput:\n{result.output[:500]}...")

    if args.task:
        task = TaskRequest(
            task_id="test_task",
            task_type=TaskType.TASK_DECOMPOSITION,
            description=args.task,
            complexity=TaskComplexity.MEDIUM,
            force_framework=FrameworkType(args.framework) if args.framework else None
        )

        print(f"Executing task: {args.task}")
        result = await router.execute_task(task)

        print(f"\nResult: {'Success' if result.success else 'Failed'}")
        print(f"Framework: {result.framework_used.value}")
        print(f"\nOutput:\n{result.output[:500]}...")

    if args.history:
        history = await router.get_execution_history()
        if history:
            print("\nRecent Executions:")
            for result in history:
                print(f"  {result.task_id}: {result.framework_used.value} - "
                      f"{'✓' if result.success else '✗'} ({result.quality_score:.1f}/10)")
        else:
            print("No execution history")


if __name__ == "__main__":
    asyncio.run(main())
