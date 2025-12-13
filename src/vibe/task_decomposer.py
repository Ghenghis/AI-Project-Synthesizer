"""
Task Decomposer for VIBE MCP

Breaks complex requests into structured phases:
- Analyzes request complexity
- Identifies dependencies
- Creates execution plan
- Estimates effort per phase
- Generates phase-specific prompts

Uses LLM for intelligent decomposition based on context.
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.llm.litellm_router import LiteLLMRouter


class PhaseType(Enum):
    """Types of phases in a task."""
    SETUP = "setup"
    IMPLEMENTATION = "implementation"
    INTEGRATION = "integration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"


class TaskComplexity(Enum):
    """Complexity levels for tasks."""
    SIMPLE = "simple"      # Single function, < 50 lines
    MODERATE = "moderate"  # Multiple functions, < 200 lines
    COMPLEX = "complex"    # Multiple files, interactions
    SYSTEM = "system"      # Full feature/system


@dataclass
class TaskPhase:
    """Represents a single phase in a task."""
    id: str
    name: str
    type: PhaseType
    description: str
    prompt: str
    dependencies: list[str]  # IDs of dependent phases
    estimated_effort: int  # 1-10 scale
    files_to_create: list[str]
    files_to_modify: list[str]
    success_criteria: list[str]


@dataclass
class TaskPlan:
    """Complete task decomposition plan."""
    task_id: str
    original_request: str
    complexity: TaskComplexity
    phases: list[TaskPhase]
    total_effort: int
    estimated_duration: str  # Human-readable duration
    metadata: dict[str, Any]


class TaskDecomposer:
    """
    Decomposes complex tasks into structured phases.

    Features:
    - LLM-powered intelligent decomposition
    - Dependency tracking
    - Effort estimation
    - Phase-specific prompt generation
    - Template-based common patterns
    """

    def __init__(self):
        self.config = get_settings()
        self.llm_router = LiteLLMRouter()

        # Common task patterns
        self.patterns = {
            "api_endpoint": {
                "phases": [
                    {"type": "setup", "name": "Setup API structure"},
                    {"type": "implementation", "name": "Implement endpoint logic"},
                    {"type": "testing", "name": "Write tests"},
                    {"type": "documentation", "name": "Update API docs"}
                ]
            },
            "database_feature": {
                "phases": [
                    {"type": "setup", "name": "Design database schema"},
                    {"type": "implementation", "name": "Create migration"},
                    {"type": "implementation", "name": "Implement models"},
                    {"type": "implementation", "name": "Create repositories"},
                    {"type": "testing", "name": "Test database operations"}
                ]
            },
            "ui_component": {
                "phases": [
                    {"type": "setup", "name": "Design component structure"},
                    {"type": "implementation", "name": "Create component file"},
                    {"type": "implementation", "name": "Add styling"},
                    {"type": "testing", "name": "Write component tests"},
                    {"type": "integration", "name": "Integrate with app"}
                ]
            },
            "authentication": {
                "phases": [
                    {"type": "setup", "name": "Setup auth configuration"},
                    {"type": "implementation", "name": "Implement auth middleware"},
                    {"type": "implementation", "name": "Create login/logout endpoints"},
                    {"type": "implementation", "name": "Add session management"},
                    {"type": "testing", "name": "Test auth flows"},
                    {"type": "documentation", "name": "Document auth API"}
                ]
            }
        }

    async def decompose(self, request: str, context: dict[str, Any] | None = None) -> TaskPlan:
        """
        Decompose a request into structured phases.

        Args:
            request: The user's request
            context: Project context (tech stack, existing code, etc.)

        Returns:
            TaskPlan with structured phases
        """
        # Detect task type and complexity
        task_type = self._detect_task_type(request)
        complexity = self._estimate_complexity(request, context)

        # Generate plan
        if complexity == TaskComplexity.SIMPLE:
            # Simple tasks don't need decomposition
            phases = [self._create_simple_phase(request)]
        else:
            # Use LLM for complex decomposition
            phases = await self._llm_decompose(request, context, task_type, complexity)

        # Calculate total effort and duration
        total_effort = sum(p.estimated_effort for p in phases)
        estimated_duration = self._estimate_duration(total_effort)

        # Create plan
        plan = TaskPlan(
            task_id=self._generate_task_id(),
            original_request=request,
            complexity=complexity,
            phases=phases,
            total_effort=total_effort,
            estimated_duration=estimated_duration,
            metadata={
                "task_type": task_type,
                "context": context,
                "phase_count": len(phases)
            }
        )

        return plan

    def _detect_task_type(self, request: str) -> str:
        """Detect the type of task from the request."""
        request_lower = request.lower()

        # Check for patterns
        patterns = {
            "api_endpoint": ["api", "endpoint", "route", "controller"],
            "database_feature": ["database", "migration", "model", "schema", "query"],
            "ui_component": ["component", "ui", "view", "page", "interface"],
            "authentication": ["auth", "login", "logout", "session", "token", "oauth"],
            "testing": ["test", "spec", "coverage", "tdd"],
            "deployment": ["deploy", "build", "release", "production"],
            "documentation": ["docs", "readme", "guide", "documentation"]
        }

        for task_type, keywords in patterns.items():
            if any(kw in request_lower for kw in keywords):
                return task_type

        return "general"

    def _estimate_complexity(self, request: str, _context: dict[str, Any] | None) -> TaskComplexity:
        """Estimate task complexity based on request and context."""
        request_lower = request.lower()

        # Complexity indicators
        complexity_score = 0

        # Length of request
        if len(request) > 200:
            complexity_score += 1
        if len(request) > 500:
            complexity_score += 1

        # Multiple requirements
        and_count = request_lower.count(" and ")
        if and_count > 2:
            complexity_score += 1
        if and_count > 4:
            complexity_score += 1

        # System-level indicators
        system_keywords = ["system", "architecture", "infrastructure", "microservice", "full"]
        if any(kw in request_lower for kw in system_keywords):
            complexity_score += 2

        # Integration indicators
        integration_keywords = ["integrate", "connect", "combine", "multiple", "several"]
        if any(kw in request_lower for kw in integration_keywords):
            complexity_score += 1

        # New feature vs modification
        if any(kw in request_lower for kw in ["create", "build", "implement", "design"]):
            complexity_score += 1

        # Map score to complexity
        if complexity_score <= 1:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 3:
            return TaskComplexity.MODERATE
        elif complexity_score <= 5:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.SYSTEM

    def _create_simple_phase(self, request: str) -> TaskPhase:
        """Create a single phase for simple tasks."""
        return TaskPhase(
            id="phase_1",
            name="Implementation",
            type=PhaseType.IMPLEMENTATION,
            description=f"Implement: {request}",
            prompt=f"Please implement the following: {request}",
            dependencies=[],
            estimated_effort=3,
            files_to_create=[],
            files_to_modify=[],
            success_criteria=["Code implements the requested functionality"]
        )

    async def _llm_decompose(self, request: str, context: dict[str, Any] | None,
                           task_type: str, complexity: TaskComplexity) -> list[TaskPhase]:
        """Use LLM to decompose complex tasks."""
        # Build prompt for LLM
        prompt = f"""Please decompose the following task into structured phases:

Task: {request}
Type: {task_type}
Complexity: {complexity.value}
Context: {json.dumps(context or {}, indent=2)}

Requirements:
1. Break into 3-7 logical phases
2. Each phase should be completable independently
3. Identify dependencies between phases
4. Estimate effort (1-10 scale) for each phase
5. Define clear success criteria
6. List files to create/modify

Phase types to use:
- setup: Preparation and configuration
- implementation: Core coding work
- integration: Connecting components
- testing: Writing and running tests
- documentation: Updating docs
- deployment: Preparing for production

Return JSON format:
{{
    "phases": [
        {{
            "id": "phase_1",
            "name": "Phase name",
            "type": "setup|implementation|integration|testing|documentation|deployment",
            "description": "What this phase accomplishes",
            "prompt": "Specific prompt for this phase",
            "dependencies": [],
            "estimated_effort": 3,
            "files_to_create": ["file1.py", "file2.js"],
            "files_to_modify": ["existing.py"],
            "success_criteria": ["Criterion 1", "Criterion 2"]
        }}
    ]
}}"""

        try:
            # Get LLM response
            response = await self.llm_router.generate(
                prompt=prompt,
                model="claude-sonnet",
                max_tokens=2000
            )

            # Parse response
            data = json.loads(response)
            phases = []

            for i, phase_data in enumerate(data.get("phases", [])):
                phase = TaskPhase(
                    id=phase_data.get("id", f"phase_{i+1}"),
                    name=phase_data.get("name", f"Phase {i+1}"),
                    type=PhaseType(phase_data.get("type", "implementation")),
                    description=phase_data.get("description", ""),
                    prompt=phase_data.get("prompt", request),
                    dependencies=phase_data.get("dependencies", []),
                    estimated_effort=phase_data.get("estimated_effort", 3),
                    files_to_create=phase_data.get("files_to_create", []),
                    files_to_modify=phase_data.get("files_to_modify", []),
                    success_criteria=phase_data.get("success_criteria", [])
                )
                phases.append(phase)

            # Validate and fix dependencies
            phases = self._validate_phases(phases)

            return phases

        except Exception as e:
            print(f"LLM decomposition failed: {e}")
            # Fallback to pattern-based decomposition
            return self._pattern_decompose(request, task_type)

    def _pattern_decompose(self, request: str, task_type: str) -> list[TaskPhase]:
        """Fallback pattern-based decomposition."""
        if task_type in self.patterns:
            pattern = self.patterns[task_type]
            phases = []

            for i, phase_data in enumerate(pattern["phases"]):
                phase = TaskPhase(
                    id=f"phase_{i+1}",
                    name=phase_data["name"],
                    type=PhaseType(phase_data["type"]),
                    description=f"{phase_data['name']} for: {request}",
                    prompt=f"Please {phase_data['name'].lower()} for: {request}",
                    dependencies=[f"phase_{i}"] if i > 0 else [],
                    estimated_effort=3,
                    files_to_create=[],
                    files_to_modify=[],
                    success_criteria=[f"Complete {phase_data['name'].lower()}"]
                )
                phases.append(phase)

            return phases

        # Default fallback
        return [self._create_simple_phase(request)]

    def _validate_phases(self, phases: list[TaskPhase]) -> list[TaskPhase]:
        """Validate and fix phase dependencies."""
        phase_ids = {p.id for p in phases}

        for phase in phases:
            # Remove invalid dependencies
            phase.dependencies = [
                dep for dep in phase.dependencies
                if dep in phase_ids
            ]

            # Ensure no circular dependencies (simple check)
            if phase.id in phase.dependencies:
                phase.dependencies.remove(phase.id)

        return phases

    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        import uuid
        return f"task_{uuid.uuid4().hex[:8]}"

    def _estimate_duration(self, total_effort: int) -> str:
        """Estimate duration based on total effort."""
        # Assume each effort point = 30 minutes
        minutes = total_effort * 30

        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 480:  # 8 hours
            hours = minutes // 60
            return f"{hours} hours"
        else:
            days = minutes // 480
            return f"{days} days"

    def get_execution_order(self, phases: list[TaskPhase]) -> list[TaskPhase]:
        """Get phases in execution order based on dependencies."""
        ordered = []
        remaining = phases.copy()

        while remaining:
            # Find phases with no unmet dependencies
            ready = [
                p for p in remaining
                if all(dep in [o.id for o in ordered] for dep in p.dependencies)
            ]

            if not ready:
                # Circular dependency or missing dependency
                # Add the first remaining phase
                ready = [remaining[0]]

            # Add the first ready phase
            phase = ready[0]
            ordered.append(phase)
            remaining.remove(phase)

        return ordered

    def export_plan(self, plan: TaskPlan, output_path: str) -> None:
        """Export task plan to JSON file."""
        export_data = asdict(plan)

        # Convert enums to strings
        export_data["complexity"] = plan.complexity.value
        for phase in export_data["phases"]:
            phase["type"] = PhaseType(phase["type"]).value

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def create_template(self, task_type: str, output_path: str) -> None:
        """Create a task template for common patterns."""
        if task_type not in self.patterns:
            print(f"Unknown task type: {task_type}")
            return

        template = {
            "task_type": task_type,
            "description": f"Template for {task_type} tasks",
            "phases": self.patterns[task_type]
        }

        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        decomposer = TaskDecomposer()

        if len(sys.argv) > 1:
            # Decompose request from file
            request_file = sys.argv[1]
            try:
                with open(request_file) as f:
                    request = f.read().strip()

                context = {
                    "tech_stack": ["Python", "FastAPI"],
                    "project_type": "api"
                }

                plan = await decomposer.decompose(request, context)

                print("=" * 60)
                print("TASK DECOMPOSITION PLAN")
                print("=" * 60)
                print(f"Task: {plan.original_request}")
                print(f"Complexity: {plan.complexity.value}")
                print(f"Total Effort: {plan.total_effort}/10")
                print(f"Estimated Duration: {plan.estimated_duration}")
                print(f"\nPhases ({len(plan.phases)}):")

                ordered = decomposer.get_execution_order(plan.phases)
                for i, phase in enumerate(ordered, 1):
                    print(f"\n{i}. {phase.name} ({phase.type.value})")
                    print(f"   Effort: {phase.estimated_effort}/10")
                    print(f"   Description: {phase.description}")
                    if phase.dependencies:
                        print(f"   Dependencies: {', '.join(phase.dependencies)}")

                # Export plan
                output_file = Path(request_file).with_suffix(".task_plan.json")
                decomposer.export_plan(plan, str(output_file))
                print(f"\nPlan exported to: {output_file}")

            except FileNotFoundError:
                print(f"File not found: {request_file}")
        else:
            # Demo decomposition
            demo_requests = [
                "Create a user authentication API with OAuth and JWT tokens",
                "Add a simple logging function",
                "Build a complete e-commerce system with inventory, payments, and user management"
            ]

            for request in demo_requests:
                print(f"\nDecomposing: {request}")
                plan = await decomposer.decompose(request)
                print(f"  Complexity: {plan.complexity.value}")
                print(f"  Phases: {len(plan.phases)}")

    asyncio.run(main())
