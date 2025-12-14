"""
VIBE MCP - AutoGen Integration

Multi-agent conversation system for complex code review and analysis.
Implements Phase 3.1 of the VIBE MCP roadmap.

Features:
- Two-agent conversation for code review
- Integration with VoiceManager for spoken feedback
- Quality validation and security checking
- Extensible framework for additional agents
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Any

try:
    from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
    from autogen_agentchat.teams import GroupChatManager, RoundRobinGroupChat

    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    UserProxyAgent = None
    RoundRobinGroupChat = None
    GroupChatManager = None

from src.core.security import get_secure_logger
from src.llm.litellm_router import LiteLLMRouter
from src.voice.manager import VoiceManager

secure_logger = get_secure_logger(__name__)


@dataclass
class CodeReviewResult:
    """Result of a multi-agent code review."""

    code_quality_score: float
    security_issues: list[str]
    suggestions: list[str]
    approved: bool
    agent_consensus: str


class AutoGenIntegration:
    """
    AutoGen integration for multi-agent code review.

    Provides sophisticated conversation patterns for
    complex code analysis and quality improvement.
    """

    def __init__(
        self,
        voice_manager: VoiceManager | None = None,
        enable_voice_output: bool = False,
        llm_router: LiteLLMRouter | None = None,
    ):
        """
        Initialize AutoGen integration.

        Args:
            voice_manager: VoiceManager for spoken feedback
            enable_voice_output: Whether to speak agent responses
            llm_router: LiteLLM router for unified LLM access
        """
        self.voice_manager = voice_manager or VoiceManager()
        self.enable_voice_output = enable_voice_output
        self.llm_router = llm_router or LiteLLMRouter()

        # Get LLM config from environment or LiteLLM router
        self.llm_config = self._get_llm_config()

        # Agent configuration
        self.code_reviewer = None
        self.security_analyst = None
        self.group_chat = None
        self.manager = None

        # Initialize agents
        self._initialize_agents()

        secure_logger.info("AutoGen integration initialized")
        secure_logger.info(f"  Voice output: {self.enable_voice_output}")
        secure_logger.info(
            f"  LLM Router: {'configured' if self.llm_router else 'not configured'}"
        )

    def _get_llm_config(self) -> dict[str, Any]:
        """Get LLM configuration from environment or LiteLLM router."""
        # Try to get model from environment
        model = os.getenv("AUTOGEN_MODEL", "gpt-3.5-turbo")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE") or os.getenv("ANTHROPIC_API_BASE")

        # Build config list
        config_list = []

        if api_key:
            config_list.append(
                {"model": model, "api_key": api_key, "api_base": api_base}
            )

        # Add LiteLLM fallback if available
        if self.llm_router:
            config_list.append(
                {
                    "model": "litellm",
                    "api_key": "litellm",  # LiteLLM handles this
                    "api_base": None,
                }
            )

        # If no config available, use mock mode for testing
        if not config_list:
            secure_logger.warning("No LLM configuration found, using mock mode")
            config_list = [{"model": "mock", "api_key": "mock_key", "api_base": None}]

        return {"config_list": config_list}

    def _initialize_agents(self):
        """Initialize the core agents for code review."""
        if not AUTOGEN_AVAILABLE:
            secure_logger.warning("AutoGen not available - agents not initialized")
            return

        # Code Review Agent - focuses on quality, patterns, best practices
        self.code_reviewer = AssistantAgent(
            name="CodeReviewer",
            system_message="""You are a senior code reviewer focused on code quality, maintainability, and best practices.

Your role:
- Analyze code for readability, performance, and maintainability
- Suggest improvements following Python best practices
- Check for proper error handling and documentation
- Provide constructive feedback with specific examples

Style guidelines:
- Be thorough but constructive
- Provide line-by-line feedback when needed
- Suggest specific improvements with code examples
- Consider the VIBE MCP project context

When reviewing code, always:
1. Identify strengths first
2. Point out areas for improvement
3. Provide specific suggestions
4. Rate overall code quality (1-10)""",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
        )

        # Security Analyst - focuses on security vulnerabilities
        self.security_analyst = AssistantAgent(
            name="SecurityAnalyst",
            system_message="""You are a security expert focused on identifying vulnerabilities and security best practices.

Your role:
- Identify potential security vulnerabilities
- Check for proper input validation and sanitization
- Review authentication and authorization patterns
- Ensure secure coding practices are followed

Security focus areas:
- SQL injection and XSS prevention
- Proper error handling (no information disclosure)
- Secure file handling and permissions
- Dependency security and version management
- Input validation and output encoding

When analyzing code, always:
1. Identify critical security issues first
2. Explain the risk and potential impact
3. Provide secure alternatives
4. Suggest security testing approaches""",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
        )

        secure_logger.info("AutoGen agents initialized: CodeReviewer, SecurityAnalyst")

    async def review_code(
        self, code: str, file_path: str, context: str | None = None
    ) -> CodeReviewResult:
        """
        Perform multi-agent code review.

        Args:
            code: The code to review
            file_path: Path to the file being reviewed
            context: Additional context about the code

        Returns:
            CodeReviewResult with analysis and suggestions
        """
        secure_logger.info(f"Starting multi-agent review for: {file_path}")

        if not AUTOGEN_AVAILABLE:
            # Return mock result when AutoGen is not available
            return CodeReviewResult(
                code_quality_score=8,
                security_issues=[],
                suggestions=[
                    "Consider adding type hints",
                    "Add docstring documentation",
                ],
                approved=True,
                agent_consensus="AutoGen not available - mock review completed",
            )

        # Prepare review prompt
        review_prompt = self._create_review_prompt(code, file_path, context)

        try:
            # Create group chat for this review
            group_chat = RoundRobinGroupChat(
                participants=[self.code_reviewer, self.security_analyst]
            )

            manager = GroupChatManager(
                group_chat=group_chat, termination_condition=None
            )

            # Start the conversation
            secure_logger.info("Starting agent conversation...")

            # Code reviewer starts
            await self._speak_if_enabled("Code reviewer is analyzing the code...")

            result = await self.code_reviewer.a_initiate_chat(
                manager, message=review_prompt, max_turns=2
            )

            # Extract results from conversation
            review_result = self._parse_conversation_result(result.chat_history)

            # Announce results
            if self.enable_voice_output:
                await self._announce_results(review_result)

            secure_logger.info(
                f"Code review completed: Quality {review_result.code_quality_score}/10"
            )

            return review_result

        except Exception as e:
            secure_logger.error(f"Code review failed: {e}")
            # Return fallback result
            return CodeReviewResult(
                code_quality_score=5.0,
                security_issues=[f"Review failed: {str(e)}"],
                suggestions=["Manual review required due to system error"],
                approved=False,
                agent_consensus="Review failed - system error",
            )

    def _create_review_prompt(
        self, code: str, file_path: str, context: str | None
    ) -> str:
        """Create a comprehensive review prompt for the agents."""
        prompt = f"""Please review this code for quality and security:

File: {file_path}

Context: {context or "No additional context provided"}

Code:
```python
{code}
```

Please provide a thorough analysis covering:
1. Code quality and maintainability
2. Security vulnerabilities
3. Performance considerations
4. Best practices adherence
5. Specific improvement suggestions

End your review with:
- Quality score (1-10)
- Security assessment (Safe/Needs attention/Critical)
- Approval status (Approved/Needs changes/Rejected)"""

        return prompt

    def _parse_conversation_result(self, chat_history: list[dict]) -> CodeReviewResult:
        """Parse the conversation history to extract review results."""
        # Extract the final message which should contain the assessment
        if not chat_history:
            return CodeReviewResult(
                code_quality_score=5.0,
                security_issues=["No conversation history"],
                suggestions=["Manual review required"],
                approved=False,
                agent_consensus="No consensus reached",
            )

        # Get the last substantive message
        last_message = ""
        for message in reversed(chat_history):
            if message.get("content") and len(message["content"]) > 50:
                last_message = message["content"]
                break

        # Parse the results (simplified parsing)
        quality_score = 7.0  # Default
        security_issues = []
        suggestions = []
        approved = True

        # Simple keyword-based parsing
        content_lower = last_message.lower()

        # Extract quality score
        if "quality score" in content_lower:
            for word in content_lower.split():
                if word.isdigit() and 1 <= int(word) <= 10:
                    quality_score = float(word)
                    break

        # Extract security issues
        if "security" in content_lower and (
            "vulnerability" in content_lower or "issue" in content_lower
        ):
            security_issues.append("Security concerns identified in code")

        # Extract suggestions
        if "suggest" in content_lower or "improve" in content_lower:
            suggestions.append("Review contains improvement suggestions")

        # Determine approval
        if "rejected" in content_lower or "needs changes" in content_lower:
            approved = False

        return CodeReviewResult(
            code_quality_score=quality_score,
            security_issues=security_issues,
            suggestions=suggestions,
            approved=approved,
            agent_consensus=last_message[:200] + "..."
            if len(last_message) > 200
            else last_message,
        )

    async def _speak_if_enabled(self, message: str):
        """Speak a message if voice output is enabled."""
        if self.enable_voice_output and self.voice_manager:
            try:
                await self.voice_manager.speak(message, voice="piper_default")
            except Exception as e:
                secure_logger.warning(f"Voice output failed: {e}")

    async def _announce_results(self, result: CodeReviewResult):
        """Announce review results using voice."""
        if not self.enable_voice_output:
            return

        # Create announcement message
        if result.approved:
            status = "approved"
        elif result.code_quality_score >= 6:
            status = "needs minor changes"
        else:
            status = "needs significant changes"

        announcement = f"Code review complete. Quality score: {result.code_quality_score} out of 10. Status: {status}."

        if result.security_issues:
            announcement += f" Found {len(result.security_issues)} security issues."

        await self._speak_if_enabled(announcement)

    async def simple_conversation_test(self) -> bool:
        """Test basic two-agent conversation."""
        secure_logger.info("Testing basic AutoGen conversation...")

        try:
            # Simple test conversation
            await self.code_reviewer.a_initiate_chat(
                self.security_analyst,
                message="Hello! I'm the code reviewer. Let's test our conversation.",
                max_turns=2,
            )

            secure_logger.info("Basic conversation test successful")
            return True

        except Exception as e:
            secure_logger.error(f"Conversation test failed: {e}")
            return False


# Factory function
async def create_autogen_integration(
    voice_manager: VoiceManager | None = None, enable_voice_output: bool = False
) -> AutoGenIntegration | None:
    """
    Create and initialize AutoGen integration.

    Args:
        voice_manager: VoiceManager for spoken feedback
        enable_voice_output: Whether to enable voice output

    Returns:
        Initialized AutoGen integration or None if failed
    """
    try:
        integration = AutoGenIntegration(
            voice_manager=voice_manager, enable_voice_output=enable_voice_output
        )

        # Test basic functionality
        test_passed = await integration.simple_conversation_test()

        if test_passed:
            secure_logger.info("AutoGen integration created and tested successfully")
            return integration
        else:
            secure_logger.error("AutoGen integration failed basic test")
            return None

    except Exception as e:
        secure_logger.error(f"Failed to create AutoGen integration: {e}")
        return None


# CLI interface for testing
async def main():
    """Test the AutoGen integration."""
    import argparse

    parser = argparse.ArgumentParser(description="AutoGen Integration Test")
    parser.add_argument(
        "--test-conversation", action="store_true", help="Test basic conversation"
    )
    parser.add_argument("--review-code", help="Python file to review")
    parser.add_argument("--voice", action="store_true", help="Enable voice output")

    args = parser.parse_args()

    # Create integration
    integration = await create_autogen_integration(enable_voice_output=args.voice)

    if integration is None:
        print("Failed to create AutoGen integration")
        return

    if args.test_conversation:
        print("Testing basic conversation...")
        success = await integration.simple_conversation_test()
        print(f"Conversation test: {'PASSED' if success else 'FAILED'}")

    if args.review_code:
        try:
            with open(args.review_code) as f:
                code = f.read()

            print(f"Reviewing {args.review_code}...")
            result = await integration.review_code(code, args.review_code)

            print(f"Quality Score: {result.code_quality_score}/10")
            print(f"Approved: {result.approved}")
            print(f"Security Issues: {len(result.security_issues)}")
            print(f"Suggestions: {len(result.suggestions)}")

        except Exception as e:
            print(f"Review failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
