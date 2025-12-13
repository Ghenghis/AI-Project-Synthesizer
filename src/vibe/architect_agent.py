"""
Architect Agent for VIBE MCP

Creates high-level architectural plans before coding:
- Analyzes requirements for architectural patterns
- Generates component diagrams
- Defines data flows and interfaces
- Identifies technology choices
- Provides structured plans for TaskDecomposer

Runs before TaskDecomposer to provide architectural context.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.agents.autogen_integration import AutoGenIntegration
from src.core.config import get_settings
from src.llm.litellm_router import LiteLLMRouter


class ArchitecturePattern(Enum):
    """Common architectural patterns."""
    MVC = "mvc"
    MICROSERVICES = "microservices"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    MONOLITH = "monolith"
    SPA = "spa"  # Single Page Application
    REST_API = "rest_api"
    WEBSOCKET_API = "websocket_api"


@dataclass
class Component:
    """Represents a system component."""
    id: str
    name: str
    type: str  # service, module, component, database, etc.
    description: str
    responsibilities: list[str]
    interfaces: list[str]
    dependencies: list[str]
    technology: str | None = None


@dataclass
class DataFlow:
    """Represents data flow between components."""
    from_component: str
    to_component: str
    data_type: str
    protocol: str
    description: str


@dataclass
class ArchitecturePlan:
    """Complete architectural plan."""
    pattern: ArchitecturePattern
    overview: str
    components: list[Component]
    data_flows: list[DataFlow]
    technology_stack: dict[str, list[str]]
    non_functional_requirements: dict[str, str]
    diagram: str  # ASCII/Mermaid diagram
    considerations: list[str]


class ArchitectAgent:
    """
    Creates architectural plans for development tasks.

    Features:
    - Pattern detection and recommendation
    - Component identification
    - Data flow modeling
    - Technology stack suggestions
    - Diagram generation
    """

    def __init__(self):
        self.config = get_settings()
        self.autogen = AutoGenIntegration()
        self.llm_router = LiteLLMRouter()

        # Pattern detection rules
        self.pattern_keywords = {
            ArchitecturePattern.MVC: ["mvc", "model view controller", "web app", "crud"],
            ArchitecturePattern.MICROSERVICES: ["microservice", "service", "api", "distributed"],
            ArchitecturePattern.SERVERLESS: ["serverless", "lambda", "function", "faas"],
            ArchitecturePattern.EVENT_DRIVEN: ["event", "message", "queue", "pub/sub"],
            ArchitecturePattern.LAYERED: ["layer", "tier", "n-tier"],
            ArchitecturePattern.HEXAGONAL: ["hexagonal", "ports", "adapters"],
            ArchitecturePattern.MONOLITH: ["monolith", "single", "all-in-one"],
            ArchitecturePattern.SPA: ["spa", "single page", "react", "vue", "angular"],
            ArchitecturePattern.REST_API: ["rest", "api", "endpoint", "http"],
            ArchitecturePattern.WEBSOCKET_API: ["websocket", "real-time", "socket", "live"]
        }

        # Component type templates
        self.component_types = {
            "database": ["database", "db", "storage", "persistence"],
            "api": ["api", "endpoint", "service", "controller"],
            "ui": ["ui", "interface", "view", "component"],
            "business": ["logic", "service", "handler", "processor"],
            "integration": ["integration", "adapter", "gateway", "proxy"]
        }

    async def create_architecture(self, requirements: str, context: dict[str, Any] | None = None) -> ArchitecturePlan:
        """
        Create an architectural plan based on requirements.

        Args:
            requirements: The system requirements
            context: Project context (tech stack, existing components, etc.)

        Returns:
            ArchitecturePlan with detailed design
        """
        # Detect architectural pattern
        pattern = self._detect_pattern(requirements, context)

        # Generate plan using LLM
        plan = await self._generate_architectural_plan(requirements, context, pattern)

        # Generate diagram
        plan.diagram = self._generate_diagram(plan)

        return plan

    def _detect_pattern(self, requirements: str, context: dict[str, Any] | None) -> ArchitecturePattern:
        """Detect the most suitable architectural pattern."""
        req_lower = requirements.lower()

        # Score each pattern
        pattern_scores = {}

        for pattern, keywords in self.pattern_keywords.items():
            score = 0
            for keyword in keywords:
                score += req_lower.count(keyword)
            pattern_scores[pattern] = score

        # Consider context
        if context:
            tech_stack = context.get("tech_stack", [])
            if "microservice" in " ".join(tech_stack).lower():
                pattern_scores[ArchitecturePattern.MICROSERVICES] += 2
            if "serverless" in " ".join(tech_stack).lower():
                pattern_scores[ArchitecturePattern.SERVERLESS] += 2

        # Return pattern with highest score
        if not pattern_scores or max(pattern_scores.values()) == 0:
            # Default based on requirements complexity
            if "api" in req_lower:
                return ArchitecturePattern.REST_API
            elif "web" in req_lower:
                return ArchitecturePattern.MVC
            else:
                return ArchitecturePattern.LAYERED

        return max(pattern_scores, key=pattern_scores.get)

    async def _generate_architectural_plan(self, requirements: str, context: dict[str, Any] | None,
                                         pattern: ArchitecturePattern) -> ArchitecturePlan:
        """Generate detailed architectural plan using LLM."""
        # Build prompt
        prompt = f"""You are a software architect. Create an architectural plan for the following requirements:

Requirements:
{requirements}

Architectural Pattern: {pattern.value}

Context:
{json.dumps(context or {}, indent=2)}

Create a detailed architectural plan including:

1. Overview: Brief description of the architecture
2. Components: List all major components with:
   - ID (component_1, component_2, etc.)
   - Name
   - Type (database, api, ui, business, integration)
   - Description
   - 3-5 key responsibilities
   - Interfaces it provides
   - Dependencies on other components
   - Technology stack for this component

3. Data Flows: How data moves between components:
   - From component
   - To component
   - Data type
   - Protocol (HTTP, WebSocket, etc.)
   - Description

4. Technology Stack: Group by layer (frontend, backend, database, etc.)

5. Non-functional Requirements:
   - Performance considerations
   - Security requirements
   - Scalability approach
   - Monitoring needs

6. Considerations: Key architectural decisions and trade-offs

Return as JSON:
{{
    "overview": "Architecture overview",
    "components": [...],
    "data_flows": [...],
    "technology_stack": {{
        "frontend": [],
        "backend": [],
        "database": [],
        "infrastructure": []
    }},
    "non_functional_requirements": {{
        "performance": "...",
        "security": "...",
        "scalability": "...",
        "monitoring": "..."
    }},
    "considerations": ["...", "..."]
}}"""

        try:
            # Get LLM response
            response = await self.llm_router.generate(
                prompt=prompt,
                model="claude-sonnet",
                max_tokens=3000
            )

            # Parse response
            data = json.loads(response)

            # Parse components
            components = []
            for comp_data in data.get("components", []):
                component = Component(
                    id=comp_data.get("id", ""),
                    name=comp_data.get("name", ""),
                    type=comp_data.get("type", ""),
                    description=comp_data.get("description", ""),
                    responsibilities=comp_data.get("responsibilities", []),
                    interfaces=comp_data.get("interfaces", []),
                    dependencies=comp_data.get("dependencies", []),
                    technology=comp_data.get("technology")
                )
                components.append(component)

            # Parse data flows
            data_flows = []
            for flow_data in data.get("data_flows", []):
                flow = DataFlow(
                    from_component=flow_data.get("from_component", ""),
                    to_component=flow_data.get("to_component", ""),
                    data_type=flow_data.get("data_type", ""),
                    protocol=flow_data.get("protocol", ""),
                    description=flow_data.get("description", "")
                )
                data_flows.append(flow)

            return ArchitecturePlan(
                pattern=pattern,
                overview=data.get("overview", ""),
                components=components,
                data_flows=data_flows,
                technology_stack=data.get("technology_stack", {}),
                non_functional_requirements=data.get("non_functional_requirements", {}),
                diagram="",  # Will be generated separately
                considerations=data.get("considerations", [])
            )

        except Exception as e:
            print(f"Failed to generate architectural plan: {e}")
            # Return basic plan
            return self._create_basic_plan(requirements, pattern)

    def _create_basic_plan(self, requirements: str, pattern: ArchitecturePattern) -> ArchitecturePlan:
        """Create a basic fallback plan."""
        # Basic components based on pattern
        components = []

        if pattern == ArchitecturePattern.REST_API:
            components = [
                Component(
                    id="component_1",
                    name="API Layer",
                    type="api",
                    description="REST API endpoints",
                    responsibilities=["Handle HTTP requests", "Validate input", "Return responses"],
                    interfaces=["REST API"],
                    dependencies=["component_2"],
                    technology="FastAPI/Flask"
                ),
                Component(
                    id="component_2",
                    name="Business Logic",
                    type="business",
                    description="Core business logic",
                    responsibilities=["Process data", "Apply rules", "Coordinate operations"],
                    interfaces=["Internal API"],
                    dependencies=["component_3"],
                    technology="Python"
                ),
                Component(
                    id="component_3",
                    name="Database",
                    type="database",
                    description="Data persistence",
                    responsibilities=["Store data", "Query data", "Maintain integrity"],
                    interfaces=["SQL/NoSQL API"],
                    dependencies=[],
                    technology="PostgreSQL"
                )
            ]
        else:
            # Generic layered architecture
            components = [
                Component(
                    id="component_1",
                    name="Presentation Layer",
                    type="ui",
                    description="User interface",
                    responsibilities=["Display data", "Handle user input"],
                    interfaces=["UI"],
                    dependencies=["component_2"],
                    technology="Web/CLI"
                ),
                Component(
                    id="component_2",
                    name="Business Layer",
                    type="business",
                    description="Business logic",
                    responsibilities=["Process logic", "Validate rules"],
                    interfaces=["API"],
                    dependencies=["component_3"],
                    technology="Python"
                ),
                Component(
                    id="component_3",
                    name="Data Layer",
                    type="database",
                    description="Data access",
                    responsibilities=["CRUD operations", "Data mapping"],
                    interfaces=["DAO"],
                    dependencies=[],
                    technology="Database"
                )
            ]

        return ArchitecturePlan(
            pattern=pattern,
            overview=f"Basic {pattern.value} architecture for the requirements",
            components=components,
            data_flows=[],
            technology_stack={"backend": ["Python"], "database": ["PostgreSQL"]},
            non_functional_requirements={},
            diagram="",
            considerations=["This is a basic plan that should be refined"]
        )

    def _generate_diagram(self, plan: ArchitecturePlan) -> str:
        """Generate an ASCII/Mermaid diagram of the architecture."""
        if plan.pattern == ArchitecturePattern.REST_API:
            return self._generate_rest_diagram(plan)
        elif plan.pattern == ArchitecturePattern.MICROSERVICES:
            return self._generate_microservices_diagram(plan)
        elif plan.pattern == ArchitecturePattern.MVC:
            return self._generate_mvc_diagram(plan)
        else:
            return self._generate_generic_diagram(plan)

    def _generate_rest_diagram(self, plan: ArchitecturePlan) -> str:
        """Generate REST API architecture diagram."""
        diagram = ["graph LR"]

        # Add components
        for comp in plan.components:
            safe_name = comp.name.replace(" ", "_").replace("-", "_")
            diagram.append(f"    {safe_name}[{comp.name}]")

        # Add flows
        for flow in plan.data_flows:
            from_name = flow.from_component.replace(" ", "_").replace("-", "_")
            to_name = flow.to_component.replace(" ", "_").replace("-", "_")
            diagram.append(f"    {from_name} -->|{flow.protocol}| {to_name}")

        return "\n".join(diagram)

    def _generate_microservices_diagram(self, plan: ArchitecturePlan) -> str:
        """Generate microservices architecture diagram."""
        diagram = ["graph TB"]
        diagram.append("    subgraph \"System\"")

        # Group components by type
        for comp in plan.components:
            safe_name = comp.name.replace(" ", "_").replace("-", "_")
            diagram.append(f"        {safe_name}[{comp.name}<br/>{comp.type}]")

        diagram.append("    end")

        # Add flows
        for flow in plan.data_flows:
            from_name = flow.from_component.replace(" ", "_").replace("-", "_")
            to_name = flow.to_component.replace(" ", "_").replace("-", "_")
            diagram.append(f"    {from_name} -->|{flow.data_type}| {to_name}")

        return "\n".join(diagram)

    def _generate_mvc_diagram(self, plan: ArchitecturePlan) -> str:
        """Generate MVC architecture diagram."""
        diagram = ["graph LR"]
        diagram.append("    subgraph \"MVC Pattern\"")

        # Find MVC components
        model = next((c for c in plan.components if "model" in c.name.lower() or c.type == "database"), None)
        view = next((c for c in plan.components if "view" in c.name.lower() or c.type == "ui"), None)
        controller = next((c for c in plan.components if "controller" in c.name.lower() or c.type == "api"), None)

        if model:
            diagram.append(f"        Model[{model.name}]")
        if view:
            diagram.append(f"        View[{view.name}]")
        if controller:
            diagram.append(f"        Controller[{controller.name}]")

        diagram.append("    end")

        # MVC connections
        if controller and model:
            diagram.append("    Controller --> Model")
        if controller and view:
            diagram.append("    Controller --> View")
        if view and model:
            diagram.append("    View --> Model")

        return "\n".join(diagram)

    def _generate_generic_diagram(self, plan: ArchitecturePlan) -> str:
        """Generate generic architecture diagram."""
        diagram = ["graph TD"]

        # Add components
        for comp in plan.components:
            safe_name = comp.name.replace(" ", "_").replace("-", "_")
            diagram.append(f"    {safe_name}[{comp.name}]")

        # Add flows
        for flow in plan.data_flows:
            from_name = flow.from_component.replace(" ", "_").replace("-", "_")
            to_name = flow.to_component.replace(" ", "_").replace("-", "_")
            diagram.append(f"    {from_name} --> {to_name}")

        return "\n".join(diagram)

    def get_component_by_id(self, plan: ArchitecturePlan, component_id: str) -> Component | None:
        """Get a component by its ID."""
        for component in plan.components:
            if component.id == component_id:
                return component
        return None

    def get_components_by_type(self, plan: ArchitecturePlan, component_type: str) -> list[Component]:
        """Get all components of a specific type."""
        return [c for c in plan.components if c.type == component_type]

    def validate_plan(self, plan: ArchitecturePlan) -> list[str]:
        """Validate an architectural plan and return issues."""
        issues = []

        # Check for required components based on pattern
        if plan.pattern == ArchitecturePattern.MVC:
            types = {c.type for c in plan.components}
            if "ui" not in types and "view" not in types:
                issues.append("MVC pattern requires a View/UI component")
            if "business" not in types and "controller" not in types:
                issues.append("MVC pattern requires a Controller component")
            if "database" not in types and "model" not in types:
                issues.append("MVC pattern requires a Model/Database component")

        # Check for orphaned components
        all_deps = set()
        for comp in plan.components:
            all_deps.update(comp.dependencies)

        all_ids = {c.id for c in plan.components}
        orphaned = all_deps - all_ids
        if orphaned:
            issues.append(f"Dependencies reference non-existent components: {orphaned}")

        # Check for circular dependencies
        for comp in plan.components:
            if self._has_circular_dependency(plan, comp.id, set()):
                issues.append(f"Circular dependency detected involving {comp.id}")

        return issues

    def _has_circular_dependency(self, plan: ArchitecturePlan, component_id: str, visited: set) -> bool:
        """Check if a component has circular dependencies."""
        if component_id in visited:
            return True

        visited.add(component_id)
        component = self.get_component_by_id(plan, component_id)

        if component:
            for dep in component.dependencies:
                if self._has_circular_dependency(plan, dep, visited.copy()):
                    return True

        return False

    def export_plan(self, plan: ArchitecturePlan, output_path: str) -> None:
        """Export architectural plan to file."""
        export_data = {
            "pattern": plan.pattern.value,
            "overview": plan.overview,
            "components": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.type,
                    "description": c.description,
                    "responsibilities": c.responsibilities,
                    "interfaces": c.interfaces,
                    "dependencies": c.dependencies,
                    "technology": c.technology
                }
                for c in plan.components
            ],
            "data_flows": [
                {
                    "from_component": f.from_component,
                    "to_component": f.to_component,
                    "data_type": f.data_type,
                    "protocol": f.protocol,
                    "description": f.description
                }
                for f in plan.data_flows
            ],
            "technology_stack": plan.technology_stack,
            "non_functional_requirements": plan.non_functional_requirements,
            "diagram": plan.diagram,
            "considerations": plan.considerations
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def create_markdown_report(self, plan: ArchitecturePlan) -> str:
        """Create a markdown report of the architectural plan."""
        report = []
        report.append(f"# Architecture Plan: {plan.pattern.value.title()}")
        report.append("")
        report.append("## Overview")
        report.append(plan.overview)
        report.append("")

        # Components
        report.append("## Components")
        for comp in plan.components:
            report.append(f"### {comp.name}")
            report.append(f"**Type:** {comp.type}")
            report.append(f"**Description:** {comp.description}")
            report.append("")
            report.append("**Responsibilities:**")
            for resp in comp.responsibilities:
                report.append(f"- {resp}")
            report.append("")
            if comp.interfaces:
                report.append("**Interfaces:**")
                for iface in comp.interfaces:
                    report.append(f"- {iface}")
                report.append("")
            if comp.dependencies:
                report.append("**Dependencies:**")
                for dep in comp.dependencies:
                    report.append(f"- {dep}")
                report.append("")
            if comp.technology:
                report.append(f"**Technology:** {comp.technology}")
                report.append("")

        # Data Flows
        if plan.data_flows:
            report.append("## Data Flows")
            for flow in plan.data_flows:
                report.append(f"- {flow.from_component} → {flow.to_component}")
                report.append(f"  - Data: {flow.data_type}")
                report.append(f"  - Protocol: {flow.protocol}")
                report.append(f"  - Description: {flow.description}")
                report.append("")

        # Technology Stack
        report.append("## Technology Stack")
        for layer, techs in plan.technology_stack.items():
            report.append(f"**{layer.title()}:** {', '.join(techs)}")
        report.append("")

        # Diagram
        if plan.diagram:
            report.append("## Architecture Diagram")
            report.append("```mermaid")
            report.append(plan.diagram)
            report.append("```")
            report.append("")

        # Non-functional Requirements
        if plan.non_functional_requirements:
            report.append("## Non-Functional Requirements")
            for req_type, desc in plan.non_functional_requirements.items():
                report.append(f"**{req_type.title()}:** {desc}")
            report.append("")

        # Considerations
        if plan.considerations:
            report.append("## Architectural Considerations")
            for consideration in plan.considerations:
                report.append(f"- {consideration}")

        return "\n".join(report)


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        architect = ArchitectAgent()

        if len(sys.argv) > 1:
            # Create architecture from file
            req_file = sys.argv[1]
            try:
                with open(req_file) as f:
                    requirements = f.read().strip()

                context = {
                    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                    "project_type": "web_api"
                }

                plan = await architect.create_architecture(requirements, context)

                # Print summary
                print("=" * 60)
                print("ARCHITECTURAL PLAN")
                print("=" * 60)
                print(f"Pattern: {plan.pattern.value}")
                print(f"Components: {len(plan.components)}")
                print(f"Data Flows: {len(plan.data_flows)}")
                print("\nOverview:")
                print(plan.overview)

                # Validate plan
                issues = architect.validate_plan(plan)
                if issues:
                    print("\nValidation Issues:")
                    for issue in issues:
                        print(f"- {issue}")

                # Export plan
                output_file = Path(req_file).with_suffix(".architecture.json")
                architect.export_plan(plan, str(output_file))
                print(f"\nPlan exported to: {output_file}")

                # Export markdown
                md_file = Path(req_file).with_suffix(".architecture.md")
                with open(md_file, 'w') as f:
                    f.write(architect.create_markdown_report(plan))
                print(f"Markdown report exported to: {md_file}")

            except FileNotFoundError:
                print(f"File not found: {req_file}")
        else:
            # Demo architecture
            demo_requirements = """
            Create a REST API for a todo application with the following features:
            - User authentication
            - CRUD operations for todos
            - Categories and tags
            - Due dates and reminders
            - Search and filtering
            """

            context = {
                "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                "project_type": "web_api"
            }

            plan = await architect.create_architecture(demo_requirements, context)
            print(f"Created {plan.pattern.value} architecture with {len(plan.components)} components")

    asyncio.run(main())
