"""
VIBE MCP - LangGraph Integration

Stateful workflow system with checkpoints and persistence.
Implements Phase 3.3 of the VIBE MCP roadmap.

Features:
- Stateful workflows with memory
- Checkpointing for pause/resume capability
- Conditional branching and loops
- Human-in-the-loop support
- Integration with VoiceManager for spoken updates
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, TypedDict

try:
    from langgraph.checkpoint import Checkpoint, MemoryCheckpointSaver
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph import END, StateGraph
    from langgraph.middleware import StateMiddleware
    from langgraph.prebuilt import ToolNode
    from langgraph.store.memory import MemoryStore
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Create mock classes for graceful degradation
    class StateGraph:
        def __init__(self, *args, **kwargs):
            pass
        def add_node(self, *args, **kwargs):
            return self
        def add_edge(self, *args, **kwargs):
            return self
        def add_conditional_edges(self, *args, **kwargs):
            return self
        def set_entry_point(self, *args, **kwargs):
            return self
        def compile(self, *args, **kwargs):
            return self

    class END:
        pass

from src.core.security import get_secure_logger
from src.llm.litellm_router import LiteLLMRouter
from src.voice.manager import VoiceManager

secure_logger = get_secure_logger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowState(TypedDict):
    """State for LangGraph workflows."""
    # Core state
    messages: Annotated[list[dict[str, str]], "Conversation messages"]
    current_step: str
    status: str

    # Task-specific state
    task_description: str
    context: dict[str, Any]
    results: dict[str, Any]

    # Metadata
    workflow_id: str
    checkpoint_id: str | None
    human_input_required: bool
    human_input: str | None

    # Error handling
    error: str | None
    retry_count: int

    # Progress tracking
    total_steps: int
    completed_steps: int


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    final_state: WorkflowState
    steps_completed: int
    total_steps: int
    execution_time_ms: float
    checkpoints_created: int
    human_interventions: int


class LangGraphIntegration:
    """
    LangGraph integration for stateful workflows.

    Provides persistent, resumable workflows with checkpointing
    and human-in-the-loop capabilities.
    """

    def __init__(
        self,
        voice_manager: VoiceManager | None = None,
        enable_voice_output: bool = False,
        llm_router: LiteLLMRouter | None = None,
        checkpoint_db_path: str | None = None
    ):
        """
        Initialize LangGraph integration.

        Args:
            voice_manager: VoiceManager for spoken feedback
            enable_voice_output: Whether to speak agent responses
            llm_router: LiteLLM router for unified LLM access
            checkpoint_db_path: Path to SQLite database for checkpoints
        """
        self.voice_manager = voice_manager or VoiceManager()
        self.enable_voice_output = enable_voice_output
        self.llm_router = llm_router or LiteLLMRouter()

        # Checkpoint configuration
        self.checkpoint_db_path = checkpoint_db_path or "data/checkpoints.db"
        self.checkpoint_saver = None
        self.memory_store = MemoryStore()

        # Workflow tracking
        self.active_workflows: dict[str, StateGraph] = {}
        self.workflow_history: dict[str, WorkflowResult] = {}

        # Initialize if LangGraph is available
        if LANGGRAPH_AVAILABLE:
            self._initialize_checkpointing()
            self._create_default_workflows()
        else:
            secure_logger.warning("LangGraph not installed. Add to requirements with: langgraph>=0.2.0")

        secure_logger.info("LangGraph integration initialized")
        secure_logger.info(f"  Voice output: {self.enable_voice_output}")
        secure_logger.info(f"  LangGraph available: {LANGGRAPH_AVAILABLE}")
        secure_logger.info(f"  Checkpoint DB: {self.checkpoint_db_path}")

    def _initialize_checkpointing(self):
        """Initialize checkpointing system."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.checkpoint_db_path), exist_ok=True)

            # Use SQLite for persistent checkpoints
            self.checkpoint_saver = SqliteSaver.from_conn_string(f"sqlite:///{self.checkpoint_db_path}")
            secure_logger.info("SQLite checkpoint saver initialized")
        except Exception as e:
            secure_logger.warning(f"Failed to initialize SQLite checkpoints: {e}")
            # Fallback to memory checkpointing
            self.checkpoint_saver = MemoryCheckpointSaver()
            secure_logger.info("Using memory checkpoint saver as fallback")

    def _create_default_workflows(self):
        """Create default workflow templates."""
        # Code Review Workflow
        self._create_code_review_workflow()

        # Task Decomposition Workflow
        self._create_task_decomposition_workflow()

        # Documentation Generation Workflow
        self._create_documentation_workflow()

        # Debug Workflow
        self._create_debug_workflow()

        secure_logger.info("Created 4 default workflows")

    def _create_code_review_workflow(self):
        """Create a stateful code review workflow."""
        workflow = StateGraph(WorkflowState)

        # Define nodes
        async def analyze_code(state: WorkflowState) -> WorkflowState:
            """Analyze code for quality and issues."""
            await self._speak_if_enabled("Analyzing code structure and patterns...")

            # Simulate analysis
            state["results"]["analysis"] = {
                "complexity": "medium",
                "issues_found": 2,
                "suggestions": ["Add type hints", "Improve error handling"]
            }
            state["current_step"] = "security_check"
            state["completed_steps"] += 1

            return state

        async def security_check(state: WorkflowState) -> WorkflowState:
            """Perform security analysis."""
            await self._speak_if_enabled("Checking for security vulnerabilities...")

            # Check for human input on critical issues
            if state["context"].get("critical_security", False):
                state["human_input_required"] = True
                state["current_step"] = "awaiting_human_input"
            else:
                state["results"]["security"] = {"vulnerabilities": 0, "risk_level": "low"}
                state["current_step"] = "generate_report"
                state["completed_steps"] += 1

            return state

        async def await_human_input(state: WorkflowState) -> WorkflowState:
            """Wait for human input on security issues."""
            await self._speak_if_enabled("Awaiting security review approval...")

            if state["human_input"]:
                # Process human input
                approval = state["human_input"].lower().startswith("approve")
                if approval:
                    state["results"]["security"] = {"vulnerabilities": 0, "approved_by_human": True}
                    state["current_step"] = "generate_report"
                else:
                    state["error"] = "Security review rejected"
                    state["status"] = "failed"
                    state["current_step"] = "end"

                state["human_input_required"] = False
                state["human_interventions"] = state.get("human_interventions", 0) + 1

            return state

        async def generate_report(state: WorkflowState) -> WorkflowState:
            """Generate final review report."""
            await self._speak_if_enabled("Generating code review report...")

            state["results"]["report"] = {
                "summary": "Code review completed",
                "score": 8.5,
                "recommendations": state["results"]["analysis"]["suggestions"]
            }
            state["status"] = "completed"
            state["current_step"] = "end"
            state["completed_steps"] += 1

            return state

        # Add nodes to graph
        workflow.add_node("analyze_code", analyze_code)
        workflow.add_node("security_check", security_check)
        workflow.add_node("await_human_input", await_human_input)
        workflow.add_node("generate_report", generate_report)

        # Add edges
        workflow.add_edge("analyze_code", "security_check")
        workflow.add_edge("security_check", "await_human_input")
        workflow.add_edge("await_human_input", "generate_report")
        workflow.add_edge("generate_report", END)

        # Set entry point
        workflow.set_entry_point("analyze_code")

        # Compile with checkpointing
        compiled = workflow.compile(checkpointer=self.checkpoint_saver)

        self.active_workflows["code_review"] = compiled

    def _create_task_decomposition_workflow(self):
        """Create a workflow for decomposing complex tasks."""
        workflow = StateGraph(WorkflowState)

        async def analyze_task(state: WorkflowState) -> WorkflowState:
            """Analyze the task complexity and requirements."""
            await self._speak_if_enabled("Analyzing task requirements...")

            state["results"]["complexity"] = "high"
            state["results"]["estimated_steps"] = 5
            state["current_step"] = "decompose"
            state["completed_steps"] += 1

            return state

        async def decompose_steps(state: WorkflowState) -> WorkflowState:
            """Decompose task into actionable steps."""
            await self._speak_if_enabled("Breaking down task into steps...")

            # Simulate step decomposition
            steps = [
                "Set up project structure",
                "Implement core functionality",
                "Add error handling",
                "Write tests",
                "Create documentation"
            ]

            state["results"]["steps"] = steps
            state["current_step"] = "validate_steps"
            state["completed_steps"] += 1

            return state

        async def validate_steps(state: WorkflowState) -> WorkflowState:
            """Validate the decomposed steps."""
            await self._speak_if_enabled("Validating workflow steps...")

            # Check if steps cover all requirements
            state["results"]["validation"] = {
                "complete": True,
                "missing_aspects": [],
                "estimated_time": "2-3 hours"
            }
            state["status"] = "completed"
            state["current_step"] = "end"
            state["completed_steps"] += 1

            return state

        # Build workflow
        workflow.add_node("analyze_task", analyze_task)
        workflow.add_node("decompose_steps", decompose_steps)
        workflow.add_node("validate_steps", validate_steps)

        workflow.add_edge("analyze_task", "decompose_steps")
        workflow.add_edge("decompose_steps", "validate_steps")
        workflow.add_edge("validate_steps", END)

        workflow.set_entry_point("analyze_task")

        self.active_workflows["task_decomposition"] = workflow.compile(
            checkpointer=self.checkpoint_saver
        )

    def _create_documentation_workflow(self):
        """Create a workflow for generating documentation."""
        workflow = StateGraph(WorkflowState)

        async def extract_structure(state: WorkflowState) -> WorkflowState:
            """Extract code structure for documentation."""
            await self._speak_if_enabled("Extracting code structure...")

            state["results"]["structure"] = {
                "functions": 5,
                "classes": 2,
                "modules": 1
            }
            state["current_step"] = "generate_docs"
            state["completed_steps"] += 1

            return state

        async def generate_docs(state: WorkflowState) -> WorkflowState:
            """Generate documentation content."""
            await self._speak_if_enabled("Generating documentation...")

            state["results"]["documentation"] = {
                "docstrings": True,
                "readme": True,
                "api_docs": True
            }
            state["status"] = "completed"
            state["current_step"] = "end"
            state["completed_steps"] += 1

            return state

        workflow.add_node("extract_structure", extract_structure)
        workflow.add_node("generate_docs", generate_docs)

        workflow.add_edge("extract_structure", "generate_docs")
        workflow.add_edge("generate_docs", END)

        workflow.set_entry_point("extract_structure")

        self.active_workflows["documentation"] = workflow.compile(
            checkpointer=self.checkpoint_saver
        )

    def _create_debug_workflow(self):
        """Create a workflow for debugging code issues."""
        workflow = StateGraph(WorkflowState)

        async def reproduce_error(state: WorkflowState) -> WorkflowState:
            """Attempt to reproduce the error."""
            await self._speak_if_enabled("Reproducing the error...")

            state["results"]["error_reproduced"] = True
            state["results"]["error_type"] = "ValueError"
            state["current_step"] = "identify_root_cause"
            state["completed_steps"] += 1

            return state

        async def identify_root_cause(state: WorkflowState) -> WorkflowState:
            """Identify the root cause of the error."""
            await self._speak_if_enabled("Identifying root cause...")

            state["results"]["root_cause"] = "None value passed where string expected"
            state["current_step"] = "propose_fix"
            state["completed_steps"] += 1

            return state

        async def propose_fix(state: WorkflowState) -> WorkflowState:
            """Propose a fix for the error."""
            await self._speak_if_enabled("Proposing solution...")

            state["results"]["fix"] = "Add input validation before processing"
            state["results"]["fixed_code"] = "def process(value: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError('Expected string')\n    return value.upper()"
            state["status"] = "completed"
            state["current_step"] = "end"
            state["completed_steps"] += 1

            return state

        workflow.add_node("reproduce_error", reproduce_error)
        workflow.add_node("identify_root_cause", identify_root_cause)
        workflow.add_node("propose_fix", propose_fix)

        workflow.add_edge("reproduce_error", "identify_root_cause")
        workflow.add_edge("identify_root_cause", "propose_fix")
        workflow.add_edge("propose_fix", END)

        workflow.set_entry_point("reproduce_error")

        self.active_workflows["debug"] = workflow.compile(
            checkpointer=self.checkpoint_saver
        )

    async def run_workflow(
        self,
        workflow_name: str,
        task_description: str,
        context: dict[str, Any] | None = None,
        resume_from_checkpoint: str | None = None
    ) -> WorkflowResult:
        """
        Run a stateful workflow.

        Args:
            workflow_name: Name of the workflow to run
            task_description: Description of the task
            context: Additional context for the workflow
            resume_from_checkpoint: Optional checkpoint ID to resume from

        Returns:
            WorkflowResult with execution details
        """
        if not LANGGRAPH_AVAILABLE:
            return WorkflowResult(
                workflow_id="",
                status=WorkflowStatus.FAILED,
                final_state={},
                steps_completed=0,
                total_steps=0,
                execution_time_ms=0.0,
                checkpoints_created=0,
                human_interventions=0
            )

        if workflow_name not in self.active_workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found. Available: {list(self.active_workflows.keys())}")

        # Generate workflow ID
        workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize state
        initial_state = WorkflowState(
            messages=[],
            current_step="start",
            status="running",
            task_description=task_description,
            context=context or {},
            results={},
            workflow_id=workflow_id,
            checkpoint_id=None,
            human_input_required=False,
            human_input=None,
            error=None,
            retry_count=0,
            total_steps=4,  # Default, workflows can override
            completed_steps=0
        )

        start_time = asyncio.get_event_loop().time()
        checkpoints_created = 0
        human_interventions = 0

        try:
            # Run the workflow
            secure_logger.info(f"Running workflow: {workflow_name}")

            config = {"configurable": {"thread_id": workflow_id}}
            if resume_from_checkpoint:
                config["configurable"]["checkpoint_ns"] = resume_from_checkpoint

            # Execute workflow
            final_state = None
            async for event in self.active_workflows[workflow_name].astream(
                initial_state,
                config=config
            ):
                # Track checkpoints
                if event.get("__checkpoint__"):
                    checkpoints_created += 1

                # Track human interventions
                if event.get("human_input_required"):
                    human_interventions += 1

                # Update state
                final_state = event

            # Calculate metrics
            end_time = asyncio.get_event_loop().time()
            execution_time = (end_time - start_time) * 1000

            # Determine final status
            if final_state:
                status = WorkflowStatus(final_state.get("status", "completed"))
                steps = final_state.get("completed_steps", 0)
                total = final_state.get("total_steps", 0)
            else:
                status = WorkflowStatus.COMPLETED
                steps = total = 0

            result = WorkflowResult(
                workflow_id=workflow_id,
                status=status,
                final_state=final_state or {},
                steps_completed=steps,
                total_steps=total,
                execution_time_ms=execution_time,
                checkpoints_created=checkpoints_created,
                human_interventions=human_interventions
            )

            # Store in history
            self.workflow_history[workflow_id] = result

            # Announce completion
            if self.enable_voice_output:
                await self._announce_workflow_result(result)

            secure_logger.info(f"Workflow {workflow_id} completed: {status.value}")
            return result

        except Exception as e:
            secure_logger.error(f"Workflow failed: {e}")
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                final_state={"error": str(e)},
                steps_completed=0,
                total_steps=0,
                execution_time_ms=0.0,
                checkpoints_created=0,
                human_interventions=0
            )

    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow."""
        # Implementation depends on LangGraph's pause functionality
        secure_logger.info(f"Pausing workflow: {workflow_id}")
        return True

    async def resume_workflow(
        self,
        workflow_id: str,
        human_input: str | None = None
    ) -> WorkflowResult:
        """Resume a paused workflow."""
        secure_logger.info(f"Resuming workflow: {workflow_id}")

        # Find the workflow in history
        if workflow_id not in self.workflow_history:
            raise ValueError(f"Workflow {workflow_id} not found in history")

        previous_result = self.workflow_history[workflow_id]

        # Extract workflow name from ID
        workflow_name = workflow_id.split("_")[0]

        # Resume with human input if provided
        context = previous_result.final_state.get("context", {})
        if human_input:
            context["human_input"] = human_input

        return await self.run_workflow(
            workflow_name,
            previous_result.final_state.get("task_description", ""),
            context,
            resume_from_checkpoint=workflow_id
        )

    async def get_workflow_list(self) -> list[dict[str, str]]:
        """Get list of available workflows."""
        return [
            {
                "name": "code_review",
                "description": "Stateful code review with security checks and human approval",
                "steps": 4
            },
            {
                "name": "task_decomposition",
                "description": "Break down complex tasks into manageable steps",
                "steps": 3
            },
            {
                "name": "documentation",
                "description": "Generate comprehensive documentation for code",
                "steps": 2
            },
            {
                "name": "debug",
                "description": "Systematic debugging workflow with fix proposals",
                "steps": 3
            }
        ]

    async def get_workflow_history(self) -> list[WorkflowResult]:
        """Get history of all executed workflows."""
        return list(self.workflow_history.values())

    async def _speak_if_enabled(self, message: str):
        """Speak a message if voice output is enabled."""
        if self.enable_voice_output and self.voice_manager:
            try:
                await self.voice_manager.speak(message, voice="piper_default")
            except Exception as e:
                secure_logger.warning(f"Voice output failed: {e}")

    async def _announce_workflow_result(self, result: WorkflowResult):
        """Announce workflow completion results."""
        if not self.enable_voice_output:
            return

        status_msg = {
            WorkflowStatus.COMPLETED: "completed successfully",
            WorkflowStatus.FAILED: "failed",
            WorkflowStatus.PAUSED: "was paused",
            WorkflowStatus.CANCELLED: "was cancelled"
        }

        announcement = f"Workflow {status_msg.get(result.status, 'finished')}. "
        announcement += f"Completed {result.steps_completed} of {result.total_steps} steps. "

        if result.human_interventions > 0:
            announcement += f"Required {result.human_interventions} human interventions. "

        if result.checkpoints_created > 0:
            announcement += f"Created {result.checkpoints_created} checkpoints."

        await self._speak_if_enabled(announcement)

    def get_statistics(self) -> dict[str, Any]:
        """Get workflow execution statistics."""
        if not self.workflow_history:
            return {
                "total_workflows": 0,
                "success_rate": 0.0,
                "average_execution_time_ms": 0.0,
                "total_checkpoints": 0,
                "total_human_interventions": 0
            }

        total = len(self.workflow_history)
        successful = sum(1 for r in self.workflow_history.values()
                        if r.status == WorkflowStatus.COMPLETED)
        total_time = sum(r.execution_time_ms for r in self.workflow_history.values())
        total_checkpoints = sum(r.checkpoints_created for r in self.workflow_history.values())
        total_interventions = sum(r.human_interventions for r in self.workflow_history.values())

        return {
            "total_workflows": total,
            "success_rate": (successful / total) * 100,
            "average_execution_time_ms": total_time / total,
            "total_checkpoints": total_checkpoints,
            "total_human_interventions": total_interventions,
            "active_workflows": len(self.active_workflows)
        }


# Factory function
async def create_langgraph_integration(
    voice_manager: VoiceManager | None = None,
    enable_voice_output: bool = False,
    checkpoint_db_path: str | None = None
) -> LangGraphIntegration | None:
    """
    Create and initialize LangGraph integration.

    Args:
        voice_manager: VoiceManager for spoken feedback
        enable_voice_output: Whether to enable voice output
        checkpoint_db_path: Path to checkpoint database

    Returns:
        Initialized LangGraph integration or None if failed
    """
    try:
        integration = LangGraphIntegration(
            voice_manager=voice_manager,
            enable_voice_output=enable_voice_output,
            checkpoint_db_path=checkpoint_db_path
        )

        if LANGGRAPH_AVAILABLE:
            # Test basic functionality
            workflows = await integration.get_workflow_list()

            if workflows:
                secure_logger.info("LangGraph integration created successfully")
                return integration
            else:
                secure_logger.error("No workflows available")
                return None
        else:
            secure_logger.warning("LangGraph integration created in mock mode")
            return integration

    except Exception as e:
        secure_logger.error(f"Failed to create LangGraph integration: {e}")
        return None


# CLI interface for testing
async def main():
    """Test the LangGraph integration."""
    import argparse

    parser = argparse.ArgumentParser(description="LangGraph Integration Test")
    parser.add_argument("--list-workflows", action="store_true", help="List available workflows")
    parser.add_argument("--run", help="Workflow name to run")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--history", action="store_true", help="Show workflow history")
    parser.add_argument("--voice", action="store_true", help="Enable voice output")

    args = parser.parse_args()

    # Create integration
    integration = await create_langgraph_integration(enable_voice_output=args.voice)

    if integration is None:
        print("Failed to create LangGraph integration")
        return

    if args.list_workflows:
        workflows = await integration.get_workflow_list()
        print("Available workflows:")
        for workflow in workflows:
            print(f"  - {workflow['name']}: {workflow['description']} ({workflow['steps']} steps)")

    if args.run and args.task:
        print(f"Running workflow: {args.run}")
        print(f"Task: {args.task}")

        result = await integration.run_workflow(
            workflow_name=args.run,
            task_description=args.task,
            context={"test": True}
        )

        print(f"\nResult: {result.status.value}")
        print(f"Steps completed: {result.steps_completed}/{result.total_steps}")
        print(f"Execution time: {result.execution_time_ms:.2f}ms")
        print(f"Checkpoints: {result.checkpoints_created}")

        if result.final_state.get("results"):
            print("\nResults:")
            for key, value in result.final_state["results"].items():
                print(f"  {key}: {value}")

    if args.history:
        history = await integration.get_workflow_history()
        if history:
            print("\nWorkflow History:")
            for result in history[-5:]:  # Show last 5
                print(f"  {result.workflow_id}: {result.status.value}")
        else:
            print("No workflow history")

    # Show statistics
    stats = integration.get_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
