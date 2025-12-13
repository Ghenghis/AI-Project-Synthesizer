"""
VIBE MCP - Swarm Integration

Lightweight agent handoff system for fast routing and simple task delegation.
Implements Phase 3.2 of the VIBE MCP roadmap.

Features:
- Fast agent handoffs (<100ms)
- Simple function-based delegation
- Context variable passing
- Streaming support
- Integration with VoiceManager for spoken updates
"""

import asyncio
from dataclasses import dataclass
from typing import Any

try:
    from swarm import Agent, Swarm
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False
    # Create mock classes for graceful degradation
    class Swarm:
        def __init__(self, *args, **kwargs):
            pass
    class Agent:
        def __init__(self, *args, **kwargs):
            pass

from src.core.security import get_secure_logger
from src.llm.litellm_router import LiteLLMRouter
from src.voice.manager import VoiceManager

secure_logger = get_secure_logger(__name__)


@dataclass
class HandoffResult:
    """Result of an agent handoff."""
    success: bool
    agent_name: str
    response: str
    context_variables: dict[str, Any]
    handoff_count: int
    latency_ms: float


class SwarmIntegration:
    """
    Swarm integration for lightweight agent handoffs.

    Provides fast, efficient agent routing for simple tasks
    that don't require complex multi-agent conversations.
    """

    def __init__(
        self,
        voice_manager: VoiceManager | None = None,
        enable_voice_output: bool = False,
        llm_router: LiteLLMRouter | None = None
    ):
        """
        Initialize Swarm integration.

        Args:
            voice_manager: VoiceManager for spoken feedback
            enable_voice_output: Whether to speak agent responses
            llm_router: LiteLLM router for unified LLM access
        """
        self.voice_manager = voice_manager or VoiceManager()
        self.enable_voice_output = enable_voice_output
        self.llm_router = llm_router or LiteLLMRouter()

        # Swarm client (if available)
        self.client = None
        self.agents: dict[str, Agent] = {}

        # Statistics
        self.handoff_count = 0
        self.total_latency = 0.0

        # Initialize if Swarm is available
        if SWARM_AVAILABLE:
            self._initialize_swarm()
        else:
            secure_logger.warning("Swarm not installed. Run: pip install git+https://github.com/openai/swarm.git")

        secure_logger.info("Swarm integration initialized")
        secure_logger.info(f"  Voice output: {self.enable_voice_output}")
        secure_logger.info(f"  Swarm available: {SWARM_AVAILABLE}")

    def _initialize_swarm(self):
        """Initialize Swarm client and default agents."""
        # Create Swarm client
        self.client = Swarm()

        # Create default agents
        self._create_default_agents()

        secure_logger.info(f"Created {len(self.agents)} default agents")

    def _create_default_agents(self):
        """Create default agent set for common tasks."""
        # Quick Code Helper - for simple code questions
        self.agents["code_helper"] = Agent(
            name="Code Helper",
            instructions="""You are a quick code helper that provides concise, accurate answers to coding questions.

            Guidelines:
            - Keep responses brief and to the point
            - Provide code examples when helpful
            - Focus on practical solutions
            - Hand off to complex_reviewer for detailed analysis""",
            functions=[self._handoff_to_complex_reviewer]
        )

        # Documentation Generator - for docs and comments
        self.agents["doc_generator"] = Agent(
            name="Documentation Generator",
            instructions="""You generate clear, concise documentation for code and functions.

            Guidelines:
            - Write docstrings in Google style
            - Keep documentation simple and readable
            - Include parameter types and return values
            - Add usage examples when helpful""",
            functions=[self._handoff_to_code_helper]
        )

        # Task Decomposer - breaks down tasks
        self.agents["task_decomposer"] = Agent(
            name="Task Decomposer",
            instructions="""You break down complex tasks into simple, actionable steps.

            Guidelines:
            - Number each step clearly
            - Keep steps small and focused
            - Estimate complexity (simple/medium/complex)
            - Suggest which agent should handle each step""",
            functions=[self._handoff_to_code_helper, self._handoff_to_doc_generator]
        )

        # Quick Fixer - handles simple bug fixes
        self.agents["quick_fixer"] = Agent(
            name="Quick Fixer",
            instructions="""You quickly identify and fix simple bugs in code.

            Guidelines:
            - Focus on syntax errors, typos, simple logic errors
            - Provide the corrected code
            - Explain what was fixed in one sentence
            - Hand off to complex_reviewer for architectural issues""",
            functions=[self._handoff_to_complex_reviewer]
        )

        # Complex Reviewer - handles what others can't
        self.agents["complex_reviewer"] = Agent(
            name="Complex Reviewer",
            instructions="""You handle complex code analysis, architecture, and security issues.

            Guidelines:
            - Provide thorough analysis for complex problems
            - Consider performance, security, and maintainability
            - Suggest refactoring approaches
            - This is the last resort agent""",
            functions=[]
        )

    def _handoff_to_complex_reviewer(self) -> Agent:
        """Handoff to complex reviewer agent."""
        self.handoff_count += 1
        return self.agents["complex_reviewer"]

    def _handoff_to_code_helper(self) -> Agent:
        """Handoff to code helper agent."""
        self.handoff_count += 1
        return self.agents["code_helper"]

    def _handoff_to_doc_generator(self) -> Agent:
        """Handoff to documentation generator agent."""
        self.handoff_count += 1
        return self.agents["doc_generator"]

    async def quick_handoff(
        self,
        agent_name: str,
        message: str,
        context_variables: dict[str, Any] | None = None,
        stream: bool = False
    ) -> HandoffResult:
        """
        Perform a quick agent handoff.

        Args:
            agent_name: Name of the agent to handoff to
            message: Message to send to the agent
            context_variables: Context variables to pass
            stream: Whether to stream the response

        Returns:
            HandoffResult with the agent's response
        """
        if not SWARM_AVAILABLE or not self.client:
            return HandoffResult(
                success=False,
                agent_name=agent_name,
                response="Swarm not available. Install with: pip install git+https://github.com/openai/swarm.git",
                context_variables=context_variables or {},
                handoff_count=0,
                latency_ms=0.0
            )

        if agent_name not in self.agents:
            return HandoffResult(
                success=False,
                agent_name=agent_name,
                response=f"Agent '{agent_name}' not found. Available: {list(self.agents.keys())}",
                context_variables=context_variables or {},
                handoff_count=0,
                latency_ms=0.0
            )

        start_time = asyncio.get_event_loop().time()
        initial_handoffs = self.handoff_count

        try:
            # Announce handoff if voice enabled
            if self.enable_voice_output:
                await self._speak_if_enabled(f"Handing off to {agent_name}")

            # Prepare messages
            messages = [{"role": "user", "content": message}]

            # Run the agent
            secure_logger.info(f"Running agent: {agent_name}")

            if stream:
                response = self.client.run_stream(
                    agent=self.agents[agent_name],
                    messages=messages,
                    context_variables=context_variables or {}
                )
                # Handle streaming response
                result_text = ""
                async for chunk in response:
                    if hasattr(chunk, 'content'):
                        result_text += chunk.content
            else:
                response = self.client.run(
                    agent=self.agents[agent_name],
                    messages=messages,
                    context_variables=context_variables or {}
                )
                result_text = response.messages[-1]["content"] if response.messages else ""

            # Calculate metrics
            end_time = asyncio.get_event_loop().time()
            latency = (end_time - start_time) * 1000
            handoffs_made = self.handoff_count - initial_handoffs

            # Speak result if enabled
            if self.enable_voice_output and result_text:
                # Speak a summary of the response
                summary = result_text[:100] + "..." if len(result_text) > 100 else result_text
                await self._speak_if_enabled(summary)

            # Update statistics
            self.total_latency += latency

            return HandoffResult(
                success=True,
                agent_name=agent_name,
                response=result_text,
                context_variables=response.context_variables if hasattr(response, 'context_variables') else {},
                handoff_count=handoffs_made,
                latency_ms=latency
            )

        except Exception as e:
            secure_logger.error(f"Handoff failed: {e}")
            return HandoffResult(
                success=False,
                agent_name=agent_name,
                response=f"Handoff failed: {str(e)}",
                context_variables=context_variables or {},
                handoff_count=0,
                latency_ms=0.0
            )

    async def decompose_task(
        self,
        task_description: str
    ) -> list[dict[str, str]]:
        """
        Decompose a complex task into simple steps.

        Args:
            task_description: Description of the task to decompose

        Returns:
            List of steps with agent assignments
        """
        result = await self.quick_handoff(
            agent_name="task_decomposer",
            message=f"Decompose this task: {task_description}"
        )

        if not result.success:
            return []

        # Parse the response into steps
        steps = []
        lines = result.response.split('\n')

        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Extract step and suggested agent
                step = line
                agent = "code_helper"  # default

                if "doc_generator" in line.lower():
                    agent = "doc_generator"
                elif "quick_fixer" in line.lower():
                    agent = "quick_fixer"
                elif "complex_reviewer" in line.lower():
                    agent = "complex_reviewer"

                steps.append({
                    "step": step,
                    "agent": agent
                })

        return steps

    async def generate_docs(
        self,
        code: str,
        doc_type: str = "docstring"
    ) -> str:
        """
        Generate documentation for code.

        Args:
            code: The code to document
            doc_type: Type of documentation (docstring, comments, readme)

        Returns:
            Generated documentation
        """
        message = f"Generate {doc_type} for this code:\n\n{code}"

        result = await self.quick_handoff(
            agent_name="doc_generator",
            message=message
        )

        return result.response if result.success else ""

    async def quick_fix(
        self,
        code: str,
        error_message: str | None = None
    ) -> str:
        """
        Quickly fix simple bugs in code.

        Args:
            code: The code with bugs
            error_message: Optional error message

        Returns:
            Fixed code
        """
        message = "Fix this code"
        if error_message:
            message += f". Error: {error_message}"
        message += f":\n\n{code}"

        result = await self.quick_handoff(
            agent_name="quick_fixer",
            message=message
        )

        return result.response if result.success else code

    async def get_agent_list(self) -> list[dict[str, str]]:
        """Get list of available agents with descriptions."""
        return [
            {"name": "code_helper", "description": "Quick coding questions and answers"},
            {"name": "doc_generator", "description": "Generate documentation and docstrings"},
            {"name": "task_decomposer", "description": "Break down tasks into steps"},
            {"name": "quick_fixer", "description": "Fix simple bugs and errors"},
            {"name": "complex_reviewer", "description": "Handle complex analysis and architecture"}
        ]

    async def _speak_if_enabled(self, message: str):
        """Speak a message if voice output is enabled."""
        if self.enable_voice_output and self.voice_manager:
            try:
                await self.voice_manager.speak(message, voice="piper_default")
            except Exception as e:
                secure_logger.warning(f"Voice output failed: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """Get usage statistics."""
        avg_latency = self.total_latency / max(1, self.handoff_count)

        return {
            "total_handoffs": self.handoff_count,
            "average_latency_ms": avg_latency,
            "total_latency_ms": self.total_latency,
            "agents_available": len(self.agents),
            "swarm_available": SWARM_AVAILABLE
        }


# Factory function
async def create_swarm_integration(
    voice_manager: VoiceManager | None = None,
    enable_voice_output: bool = False
) -> SwarmIntegration | None:
    """
    Create and initialize Swarm integration.

    Args:
        voice_manager: VoiceManager for spoken feedback
        enable_voice_output: Whether to enable voice output

    Returns:
        Initialized Swarm integration or None if failed
    """
    try:
        integration = SwarmIntegration(
            voice_manager=voice_manager,
            enable_voice_output=enable_voice_output
        )

        # Test basic functionality
        if SWARM_AVAILABLE:
            test_result = await integration.quick_handoff(
                agent_name="code_helper",
                message="Say 'test successful' if you receive this."
            )

            if test_result.success:
                secure_logger.info("Swarm integration created and tested successfully")
                return integration
            else:
                secure_logger.error("Swarm integration failed basic test")
                return None
        else:
            secure_logger.warning("Swarm integration created in mock mode")
            return integration

    except Exception as e:
        secure_logger.error(f"Failed to create Swarm integration: {e}")
        return None


# CLI interface for testing
async def main():
    """Test the Swarm integration."""
    import argparse

    parser = argparse.ArgumentParser(description="Swarm Integration Test")
    parser.add_argument("--list-agents", action="store_true", help="List available agents")
    parser.add_argument("--handoff", help="Agent name to handoff to")
    parser.add_argument("--message", help="Message to send")
    parser.add_argument("--decompose", help="Task to decompose")
    parser.add_argument("--voice", action="store_true", help="Enable voice output")

    args = parser.parse_args()

    # Create integration
    integration = await create_swarm_integration(enable_voice_output=args.voice)

    if integration is None:
        print("Failed to create Swarm integration")
        return

    if args.list_agents:
        agents = await integration.get_agent_list()
        print("Available agents:")
        for agent in agents:
            print(f"  - {agent['name']}: {agent['description']}")

    if args.handoff and args.message:
        print(f"Handing off to {args.handoff}...")
        result = await integration.quick_handoff(args.handoff, args.message)

        if result.success:
            print(f"Response from {result.agent_name}:")
            print(result.response)
            print(f"\nHandoffs: {result.handoff_count}, Latency: {result.latency_ms:.2f}ms")
        else:
            print(f"Error: {result.response}")

    if args.decompose:
        print(f"Decomposing task: {args.decompose}")
        steps = await integration.decompose_task(args.decompose)

        if steps:
            print("\nDecomposed steps:")
            for i, step in enumerate(steps, 1):
                print(f"{i}. {step['step']} (Agent: {step['agent']})")
        else:
            print("Failed to decompose task")

    # Show statistics
    stats = integration.get_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
