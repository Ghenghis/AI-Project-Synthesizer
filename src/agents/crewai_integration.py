"""
VIBE MCP - CrewAI Integration

Role-based team collaboration system for complex multi-agent tasks.
Implements Phase 3.4 of the VIBE MCP roadmap.

Features:
- Role-based agent teams with specific expertise
- Hierarchical task delegation
- Collaborative problem solving
- Tool sharing between agents
- Integration with VoiceManager for team updates
"""

import asyncio
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from crewai import Agent, Crew, Process, Task
    from crewai.tools import BaseTool
    from langchain.tools import tool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create mock classes for graceful degradation
    class Agent:
        def __init__(self, *args, **kwargs):
            pass
    class Task:
        def __init__(self, *args, **kwargs):
            pass
    class Crew:
        def __init__(self, *args, **kwargs):
            pass
    class Process:
        SEQUENTIAL = "sequential"
        HIERARCHICAL = "hierarchical"

from src.core.security import get_secure_logger
from src.llm.litellm_router import LiteLLMRouter
from src.voice.manager import VoiceManager

secure_logger = get_secure_logger(__name__)


class TeamRole(Enum):
    """ predefined roles for agents in teams."""
    PROJECT_MANAGER = "project_manager"
    SENIOR_DEVELOPER = "senior_developer"
    SECURITY_EXPERT = "security_expert"
    QA_TESTER = "qa_tester"
    DOCUMENTATION_WRITER = "documentation_writer"
    UI_UX_DESIGNER = "ui_ux_designer"
    DATA_SCIENTIST = "data_scientist"
    DEVOPS_ENGINEER = "devops_engineer"


@dataclass
class TeamTask:
    """A task assigned to a CrewAI team."""
    task_id: str
    description: str
    expected_output: str
    agent_role: TeamRole
    context: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    async_execution: bool = False


@dataclass
class TeamResult:
    """Result from a CrewAI team execution."""
    team_name: str
    task_id: str
    success: bool
    final_output: str
    agent_results: dict[str, str]
    execution_time_ms: float
    tokens_used: int
    quality_score: float


class CrewAIIntegration:
    """
    CrewAI integration for role-based team collaboration.

    Provides specialized agent teams that work together
    on complex tasks requiring multiple expertise areas.
    """

    def __init__(
        self,
        voice_manager: VoiceManager | None = None,
        enable_voice_output: bool = False,
        llm_router: LiteLLMRouter | None = None
    ):
        """
        Initialize CrewAI integration.

        Args:
            voice_manager: VoiceManager for spoken feedback
            enable_voice_output: Whether to speak team updates
            llm_router: LiteLLM router for unified LLM access
        """
        self.voice_manager = voice_manager or VoiceManager()
        self.enable_voice_output = enable_voice_output
        self.llm_router = llm_router or LiteLLMRouter()

        # Team configuration
        self.agents: dict[TeamRole, Agent] = {}
        self.crews: dict[str, Crew] = {}
        self.task_history: list[TeamResult] = []

        # LLM configuration
        self.llm_config = self._get_llm_config()

        # Initialize if CrewAI is available
        if CREWAI_AVAILABLE:
            self._create_agents()
            self._create_default_crews()
        else:
            secure_logger.warning("CrewAI not installed. Add to requirements with: crewai>=0.1.0")

        secure_logger.info("CrewAI integration initialized")
        secure_logger.info(f"  Voice output: {self.enable_voice_output}")
        secure_logger.info(f"  CrewAI available: {CREWAI_AVAILABLE}")
        secure_logger.info(f"  Agents created: {len(self.agents)}")
        secure_logger.info(f"  Crews created: {len(self.crews)}")

    def _get_llm_config(self) -> dict[str, Any]:
        """Get LLM configuration from environment or LiteLLM router."""
        # Similar to AutoGen integration
        model = os.getenv("CREWAI_MODEL", "gpt-3.5-turbo")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE") or os.getenv("ANTHROPIC_API_BASE")

        return {
            "model": model,
            "api_key": api_key,
            "api_base": api_base
        }

    def _create_agents(self):
        """Create specialized agents for different roles."""
        # Project Manager - coordinates the team
        self.agents[TeamRole.PROJECT_MANAGER] = Agent(
            role='Project Manager',
            goal='Efficiently coordinate the team to complete tasks on time and with high quality',
            backstory="""You are an experienced project manager with a track record of
            delivering complex software projects. You excel at breaking down tasks,
            delegating work, and ensuring quality standards are met.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm_config
        )

        # Senior Developer - handles complex coding tasks
        self.agents[TeamRole.SENIOR_DEVELOPER] = Agent(
            role='Senior Developer',
            goal='Write clean, efficient, and maintainable code',
            backstory="""You are a senior software engineer with 10+ years of experience
            in multiple programming languages and frameworks. You write production-ready
            code following best practices and design patterns.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )

        # Security Expert - identifies and fixes security issues
        self.agents[TeamRole.SECURITY_EXPERT] = Agent(
            role='Security Expert',
            goal='Ensure the codebase is secure and follows security best practices',
            backstory="""You are a cybersecurity specialist focused on application security.
            You identify vulnerabilities, suggest secure coding practices, and ensure
            compliance with security standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )

        # QA Tester - designs and executes tests
        self.agents[TeamRole.QA_TESTER] = Agent(
            role='QA Tester',
            goal='Ensure software quality through comprehensive testing',
            backstory="""You are a meticulous QA engineer who believes in thorough testing.
            You design test cases, identify edge cases, and ensure the software works
            correctly under all conditions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )

        # Documentation Writer - creates clear documentation
        self.agents[TeamRole.DOCUMENTATION_WRITER] = Agent(
            role='Documentation Writer',
            goal='Create clear, comprehensive, and user-friendly documentation',
            backstory="""You are a technical writer who excels at explaining complex
            concepts in simple terms. You create documentation that helps users
            understand and use the software effectively.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )

        # UI/UX Designer - focuses on user experience
        self.agents[TeamRole.UI_UX_DESIGNER] = Agent(
            role='UI/UX Designer',
            goal='Design intuitive and beautiful user interfaces',
            backstory="""You are a designer with a keen eye for detail and a deep
            understanding of user psychology. You create interfaces that are
            not just functional but delightful to use.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )

        # Data Scientist - handles data analysis and ML
        self.agents[TeamRole.DATA_SCIENTIST] = Agent(
            role='Data Scientist',
            goal='Extract insights from data and build ML models',
            backstory="""You are a data scientist with expertise in statistics,
            machine learning, and data visualization. You turn raw data into
            actionable insights and predictive models.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )

        # DevOps Engineer - handles deployment and infrastructure
        self.agents[TeamRole.DEVOPS_ENGINEER] = Agent(
            role='DevOps Engineer',
            goal='Ensure reliable deployment and infrastructure management',
            backstory="""You are a DevOps engineer who automates everything.
            You design CI/CD pipelines, manage cloud infrastructure, and ensure
            the application runs smoothly in production.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )

        secure_logger.info(f"Created {len(self.agents)} specialized agents")

    def _create_default_crews(self):
        """Create predefined teams for common scenarios."""
        # Development Team - for building new features
        self.crews["development"] = Crew(
            agents=[
                self.agents[TeamRole.PROJECT_MANAGER],
                self.agents[TeamRole.SENIOR_DEVELOPER],
                self.agents[TeamRole.SECURITY_EXPERT],
                self.agents[TeamRole.QA_TESTER]
            ],
            process=Process.HIERARCHICAL,
            manager_agent=self.agents[TeamRole.PROJECT_MANAGER],
            verbose=True
        )

        # Documentation Team - for creating comprehensive docs
        self.crews["documentation"] = Crew(
            agents=[
                self.agents[TeamRole.PROJECT_MANAGER],
                self.agents[TeamRole.DOCUMENTATION_WRITER],
                self.agents[TeamRole.SENIOR_DEVELOPER],
                self.agents[TeamRole.UI_UX_DESIGNER]
            ],
            process=Process.SEQUENTIAL,
            verbose=True
        )

        # Security Audit Team - for thorough security reviews
        self.crews["security_audit"] = Crew(
            agents=[
                self.agents[TeamRole.SECURITY_EXPERT],
                self.agents[TeamRole.SENIOR_DEVELOPER],
                self.agents[TeamRole.QA_TESTER],
                self.agents[TeamRole.DEVOPS_ENGINEER]
            ],
            process=Process.SEQUENTIAL,
            verbose=True
        )

        # Data Science Team - for ML and analytics projects
        self.crews["data_science"] = Crew(
            agents=[
                self.agents[TeamRole.PROJECT_MANAGER],
                self.agents[TeamRole.DATA_SCIENTIST],
                self.agents[TeamRole.SENIOR_DEVELOPER],
                self.agents[TeamRole.DOCUMENTATION_WRITER]
            ],
            process=Process.HIERARCHICAL,
            manager_agent=self.agents[TeamRole.PROJECT_MANAGER],
            verbose=True
        )

        # Full Stack Team - for complete web applications
        self.crews["full_stack"] = Crew(
            agents=[
                self.agents[TeamRole.PROJECT_MANAGER],
                self.agents[TeamRole.UI_UX_DESIGNER],
                self.agents[TeamRole.SENIOR_DEVELOPER],
                self.agents[TeamRole.SECURITY_EXPERT],
                self.agents[TeamRole.QA_TESTER],
                self.agents[TeamRole.DEVOPS_ENGINEER]
            ],
            process=Process.HIERARCHICAL,
            manager_agent=self.agents[TeamRole.PROJECT_MANAGER],
            verbose=True
        )

        secure_logger.info(f"Created {len(self.crews)} default crews")

    async def execute_team_task(
        self,
        team_name: str,
        tasks: list[TeamTask],
        context: dict[str, Any] | None = None
    ) -> TeamResult:
        """
        Execute a task using a specialized team.

        Args:
            team_name: Name of the crew to use
            tasks: List of tasks to complete
            context: Additional context for the tasks

        Returns:
            TeamResult with execution details
        """
        if not CREWAI_AVAILABLE:
            return TeamResult(
                team_name=team_name,
                task_id=tasks[0].task_id if tasks else "",
                success=False,
                final_output="CrewAI not available",
                agent_results={},
                execution_time_ms=0.0,
                tokens_used=0,
                quality_score=0.0
            )

        if team_name not in self.crews:
            raise ValueError(f"Team '{team_name}' not found. Available: {list(self.crews.keys())}")

        start_time = asyncio.get_event_loop().time()

        try:
            # Announce team activation
            if self.enable_voice_output:
                await self._speak_if_enabled(f"Activating {team_name} team")

            # Convert TeamTask objects to CrewAI Task objects
            crewai_tasks = []
            for team_task in tasks:
                agent = self.agents.get(team_task.agent_role)
                if not agent:
                    raise ValueError(f"Agent for role {team_task.agent_role} not found")

                crewai_task = Task(
                    description=team_task.description,
                    expected_output=team_task.expected_output,
                    agent=agent,
                    context=team_task.context,
                    async_execution=team_task.async_execution
                )
                crewai_tasks.append(crewai_task)

            # Execute the crew
            secure_logger.info(f"Executing {len(crewai_tasks)} tasks with {team_name} team")

            # Run in thread pool since CrewAI is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.crews[team_name].kickoff,
                crewai_tasks
            )

            # Calculate metrics
            end_time = asyncio.get_event_loop().time()
            execution_time = (end_time - start_time) * 1000

            # Extract results
            final_output = str(result) if result else "No output"
            agent_results = self._extract_agent_results(result)

            # Calculate quality score (simplified)
            quality_score = self._calculate_quality_score(final_output, agent_results)

            team_result = TeamResult(
                team_name=team_name,
                task_id=tasks[0].task_id if tasks else "",
                success=True,
                final_output=final_output,
                agent_results=agent_results,
                execution_time_ms=execution_time,
                tokens_used=0,  # CrewAI doesn't expose this easily
                quality_score=quality_score
            )

            # Store in history
            self.task_history.append(team_result)

            # Announce completion
            if self.enable_voice_output:
                await self._announce_team_result(team_result)

            secure_logger.info(f"Team {team_name} completed task in {execution_time:.2f}ms")
            return team_result

        except Exception as e:
            secure_logger.error(f"Team execution failed: {e}")
            return TeamResult(
                team_name=team_name,
                task_id=tasks[0].task_id if tasks else "",
                success=False,
                final_output=f"Execution failed: {str(e)}",
                agent_results={},
                execution_time_ms=0.0,
                tokens_used=0,
                quality_score=0.0
            )

    def _extract_agent_results(self, result) -> dict[str, str]:
        """Extract individual agent results from crew execution."""
        # This is a simplified extraction - real implementation would
        # need to parse the CrewAI result object more carefully
        return {
            "summary": str(result) if result else "No results"
        }

    def _calculate_quality_score(self, output: str, agent_results: dict[str, str]) -> float:
        """Calculate a quality score for the team's work."""
        # Simple heuristic-based scoring
        score = 5.0  # Base score

        # Length indicates thoroughness
        if len(output) > 500:
            score += 1.0

        # Check for key quality indicators
        quality_indicators = [
            "test", "security", "documentation", "error handling",
            "optimization", "best practice", "recommendation"
        ]

        for indicator in quality_indicators:
            if indicator.lower() in output.lower():
                score += 0.5

        return min(10.0, score)

    async def create_feature(
        self,
        feature_description: str,
        requirements: list[str]
    ) -> TeamResult:
        """
        Create a new feature using the development team.

        Args:
            feature_description: Description of the feature to build
            requirements: List of requirements for the feature

        Returns:
            TeamResult from the development team
        """
        tasks = [
            TeamTask(
                task_id="plan_feature",
                description=f"Plan the implementation of: {feature_description}",
                expected_output="A detailed implementation plan with tasks and dependencies",
                agent_role=TeamRole.PROJECT_MANAGER
            ),
            TeamTask(
                task_id="implement_feature",
                description="Implement the feature following the plan",
                expected_output="Working code that implements the feature",
                agent_role=TeamRole.SENIOR_DEVELOPER,
                context=["plan_feature"]
            ),
            TeamTask(
                task_id="security_review",
                description="Review the implementation for security issues",
                expected_output="Security assessment and recommendations",
                agent_role=TeamRole.SECURITY_EXPERT,
                context=["implement_feature"]
            ),
            TeamTask(
                task_id="test_feature",
                description="Create and execute tests for the feature",
                expected_output="Comprehensive test suite with results",
                agent_role=TeamRole.QA_TESTER,
                context=["implement_feature"]
            )
        ]

        return await self.execute_team_task(
            team_name="development",
            tasks=tasks,
            context={"requirements": requirements}
        )

    async def audit_security(
        self,
        codebase_description: str,
        focus_areas: list[str]
    ) -> TeamResult:
        """
        Perform a security audit using the security team.

        Args:
            codebase_description: Description of the codebase to audit
            focus_areas: Specific areas to focus on

        Returns:
            TeamResult from the security audit team
        """
        tasks = [
            TeamTask(
                task_id="security_scan",
                description=f"Perform security analysis of: {codebase_description}",
                expected_output="Detailed security report with vulnerabilities and risks",
                agent_role=TeamRole.SECURITY_EXPERT
            ),
            TeamTask(
                task_id="code_review",
                description="Review code for security anti-patterns",
                expected_output="List of security issues in the code",
                agent_role=TeamRole.SENIOR_DEVELOPER,
                context=["security_scan"]
            ),
            TeamTask(
                task_id="penetration_test",
                description="Design security tests based on findings",
                expected_output="Security test cases and procedures",
                agent_role=TeamRole.QA_TESTER,
                context=["security_scan"]
            ),
            TeamTask(
                task_id="infrastructure_review",
                description="Review deployment and infrastructure security",
                expected_output="Infrastructure security assessment",
                agent_role=TeamRole.DEVOPS_ENGINEER,
                context=["security_scan"]
            )
        ]

        return await self.execute_team_task(
            team_name="security_audit",
            tasks=tasks,
            context={"focus_areas": focus_areas}
        )

    async def generate_documentation(
        self,
        project_description: str,
        doc_type: str = "user_guide"
    ) -> TeamResult:
        """
        Generate documentation using the documentation team.

        Args:
            project_description: Description of the project to document
            doc_type: Type of documentation to generate

        Returns:
            TeamResult from the documentation team
        """
        tasks = [
            TeamTask(
                task_id="plan_docs",
                description=f"Plan documentation structure for: {project_description}",
                expected_output="Documentation outline and structure",
                agent_role=TeamRole.PROJECT_MANAGER
            ),
            TeamTask(
                task_id="write_content",
                description=f"Write {doc_type} content",
                expected_output="Complete documentation content",
                agent_role=TeamRole.DOCUMENTATION_WRITER,
                context=["plan_docs"]
            ),
            TeamTask(
                task_id="code_examples",
                description="Create code examples and snippets",
                expected_output="Working code examples",
                agent_role=TeamRole.SENIOR_DEVELOPER,
                context=["write_content"]
            ),
            TeamTask(
                task_id="design_visuals",
                description="Create diagrams and visual aids",
                expected_output="Visual diagrams and illustrations",
                agent_role=TeamRole.UI_UX_DESIGNER,
                context=["plan_docs"]
            )
        ]

        return await self.execute_team_task(
            team_name="documentation",
            tasks=tasks,
            context={"doc_type": doc_type}
        )

    async def get_team_list(self) -> list[dict[str, Any]]:
        """Get list of available teams with their capabilities."""
        return [
            {
                "name": "development",
                "description": "Build new features with coordinated development",
                "agents": ["Project Manager", "Senior Developer", "Security Expert", "QA Tester"],
                "process": "hierarchical"
            },
            {
                "name": "documentation",
                "description": "Create comprehensive documentation",
                "agents": ["Project Manager", "Documentation Writer", "Senior Developer", "UI/UX Designer"],
                "process": "sequential"
            },
            {
                "name": "security_audit",
                "description": "Perform thorough security reviews",
                "agents": ["Security Expert", "Senior Developer", "QA Tester", "DevOps Engineer"],
                "process": "sequential"
            },
            {
                "name": "data_science",
                "description": "Handle ML and analytics projects",
                "agents": ["Project Manager", "Data Scientist", "Senior Developer", "Documentation Writer"],
                "process": "hierarchical"
            },
            {
                "name": "full_stack",
                "description": "Build complete web applications",
                "agents": ["Project Manager", "UI/UX Designer", "Senior Developer", "Security Expert", "QA Tester", "DevOps Engineer"],
                "process": "hierarchical"
            }
        ]

    async def get_task_history(self) -> list[TeamResult]:
        """Get history of all team task executions."""
        return self.task_history

    async def _speak_if_enabled(self, message: str):
        """Speak a message if voice output is enabled."""
        if self.enable_voice_output and self.voice_manager:
            try:
                await self.voice_manager.speak(message, voice="piper_default")
            except Exception as e:
                secure_logger.warning(f"Voice output failed: {e}")

    async def _announce_team_result(self, result: TeamResult):
        """Announce team completion results."""
        if not self.enable_voice_output:
            return

        status = "completed successfully" if result.success else "failed"
        announcement = f"The {result.team_name} team {status}. "
        announcement += f"Quality score: {result.quality_score:.1f} out of 10."

        if result.execution_time_ms > 0:
            announcement += f" Execution time: {result.execution_time_ms:.0f} milliseconds."

        await self._speak_if_enabled(announcement)

    def get_statistics(self) -> dict[str, Any]:
        """Get team execution statistics."""
        if not self.task_history:
            return {
                "total_tasks": 0,
                "success_rate": 0.0,
                "average_quality_score": 0.0,
                "average_execution_time_ms": 0.0,
                "most_used_team": None
            }

        total = len(self.task_history)
        successful = sum(1 for r in self.task_history if r.success)
        total_quality = sum(r.quality_score for r in self.task_history)
        total_time = sum(r.execution_time_ms for r in self.task_history)

        # Find most used team
        team_counts = {}
        for result in self.task_history:
            team_counts[result.team_name] = team_counts.get(result.team_name, 0) + 1
        most_used = max(team_counts.items(), key=lambda x: x[1])[0] if team_counts else None

        return {
            "total_tasks": total,
            "success_rate": (successful / total) * 100,
            "average_quality_score": total_quality / total,
            "average_execution_time_ms": total_time / total,
            "most_used_team": most_used,
            "available_teams": len(self.crews),
            "available_agents": len(self.agents)
        }


# Factory function
async def create_crewai_integration(
    voice_manager: VoiceManager | None = None,
    enable_voice_output: bool = False
) -> CrewAIIntegration | None:
    """
    Create and initialize CrewAI integration.

    Args:
        voice_manager: VoiceManager for spoken feedback
        enable_voice_output: Whether to enable voice output

    Returns:
        Initialized CrewAI integration or None if failed
    """
    try:
        integration = CrewAIIntegration(
            voice_manager=voice_manager,
            enable_voice_output=enable_voice_output
        )

        if CREWAI_AVAILABLE:
            # Test basic functionality
            teams = await integration.get_team_list()

            if teams:
                secure_logger.info("CrewAI integration created successfully")
                return integration
            else:
                secure_logger.error("No teams available")
                return None
        else:
            secure_logger.warning("CrewAI integration created in mock mode")
            return integration

    except Exception as e:
        secure_logger.error(f"Failed to create CrewAI integration: {e}")
        return None


# CLI interface for testing
async def main():
    """Test the CrewAI integration."""
    import argparse

    parser = argparse.ArgumentParser(description="CrewAI Integration Test")
    parser.add_argument("--list-teams", action="store_true", help="List available teams")
    parser.add_argument("--create-feature", help="Feature description to create")
    parser.add_argument("--security-audit", help="Codebase to audit")
    parser.add_argument("--generate-docs", help="Project to document")
    parser.add_argument("--history", action="store_true", help="Show task history")
    parser.add_argument("--voice", action="store_true", help="Enable voice output")

    args = parser.parse_args()

    # Create integration
    integration = await create_crewai_integration(enable_voice_output=args.voice)

    if integration is None:
        print("Failed to create CrewAI integration")
        return

    if args.list_teams:
        teams = await integration.get_team_list()
        print("Available teams:")
        for team in teams:
            print(f"\n  {team['name']}:")
            print(f"    Description: {team['description']}")
            print(f"    Agents: {', '.join(team['agents'])}")
            print(f"    Process: {team['process']}")

    if args.create_feature:
        print(f"Creating feature: {args.create_feature}")
        result = await integration.create_feature(
            feature_description=args.create_feature,
            requirements=["User authentication", "Data persistence"]
        )

        print(f"\nResult: {'Success' if result.success else 'Failed'}")
        print(f"Quality Score: {result.quality_score:.1f}/10")
        print(f"Execution Time: {result.execution_time_ms:.2f}ms")
        print(f"\nOutput:\n{result.final_output[:500]}...")

    if args.security_audit:
        print(f"Performing security audit: {args.security_audit}")
        result = await integration.audit_security(
            codebase_description=args.security_audit,
            focus_areas=["authentication", "data validation"]
        )

        print(f"\nResult: {'Success' if result.success else 'Failed'}")
        print(f"Quality Score: {result.quality_score:.1f}/10")
        print(f"\nOutput:\n{result.final_output[:500]}...")

    if args.generate_docs:
        print(f"Generating documentation: {args.generate_docs}")
        result = await integration.generate_documentation(
            project_description=args.generate_docs,
            doc_type="api_reference"
        )

        print(f"\nResult: {'Success' if result.success else 'Failed'}")
        print(f"Quality Score: {result.quality_score:.1f}/10")
        print(f"\nOutput:\n{result.final_output[:500]}...")

    if args.history:
        history = await integration.get_task_history()
        if history:
            print("\nTask History:")
            for result in history[-5:]:  # Show last 5
                print(f"  {result.team_name}: {result.quality_score:.1f}/10")
        else:
            print("No task history")

    # Show statistics
    stats = integration.get_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
