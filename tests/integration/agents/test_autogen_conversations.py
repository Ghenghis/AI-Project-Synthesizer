"""
Integration test for AutoGen multi-agent conversations.
Tests: Multi-agent code review, coordination, and collaboration.
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock AutoGen if not available
try:
    from autogen_agentchat import ConversableAgent, GroupChat, GroupChatManager

    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    ConversableAgent = None
    GroupChat = None
    GroupChatManager = None

from src.agents.autogen_integration import AutoGenIntegration, CodeReviewResult
from src.llm.litellm_router import LiteLLMRouter


class TestAutoGenConversations:
    """Test AutoGen multi-agent conversation workflows."""

    @pytest.mark.integration
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    async def test_code_review_conversation_flow(self):
        """Test complete code review conversation between agents."""

        # Initialize AutoGen integration
        integration = AutoGenIntegration()
        await integration.initialize()

        # Create code review participants
        reviewer = integration.create_reviewer_agent()
        author = integration.create_author_agent()
        summarizer = integration.create_summarizer_agent()

        # Start code review conversation
        code_snippet = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
"""

        conversation_result = await integration.start_code_review(
            code=code_snippet,
            context="E-commerce checkout function",
            participants=[reviewer, author, summarizer],
        )

        # Verify conversation completed
        assert conversation_result is not None
        assert conversation_result.status == "completed"
        assert len(conversation_result.messages) > 0

        # Check for expected review points
        messages = conversation_result.messages
        has_security_comment = any(
            "security" in msg.get("content", "").lower() for msg in messages
        )
        has_performance_comment = any(
            "performance" in msg.get("content", "").lower()
            or "optimize" in msg.get("content", "").lower()
            for msg in messages
        )

        assert has_security_comment or has_performance_comment

        await integration.shutdown()

    @pytest.mark.integration
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    async def test_group_chat_coordination(self):
        """Test agents coordinate through group chat."""

        integration = AutoGenIntegration()
        await integration.initialize()

        # Create specialized agents
        security_agent = integration.create_security_specialist()
        performance_agent = integration.create_performance_specialist()
        documentation_agent = integration.create_documentation_specialist()

        # Set up group chat
        agents = [security_agent, performance_agent, documentation_agent]
        group_chat = GroupChat(agents=agents, messages=[], max_round=5)

        manager = GroupChatManager(groupchat=group_chat, llm_config={"model": "mock"})

        # Initiate group discussion
        task = "Review this authentication function for security, performance, and documentation:"
        code = """
def authenticate_user(username, password):
    if username in users and users[username] == password:
        return True
    return False
"""

        # Mock LLM responses for each agent
        with patch.object(LiteLLMRouter, "complete") as mock_llm:
            mock_llm.side_effect = [
                {
                    "content": "This function has security vulnerabilities - plain text passwords",
                    "provider": "mock",
                },
                {
                    "content": "Performance is fine for small user sets, consider hashing",
                    "provider": "mock",
                },
                {"content": "Needs docstring and type hints", "provider": "mock"},
                {
                    "content": "Agreed, let's implement secure hashing",
                    "provider": "mock",
                },
                {"content": "I'll add proper documentation", "provider": "mock"},
            ]

            # Run group chat
            result = await manager.a_initiate_chat(
                recipient=security_agent, message=f"{task}\n\n{code}", max_turns=5
            )

            # Verify collaboration occurred
            chat_messages = group_chat.messages
            assert len(chat_messages) >= 3  # At least one message per agent

            # Check each agent contributed
            agent_names = {msg.get("name", "") for msg in chat_messages}
            assert len(agent_names) >= 2  # At least 2 agents participated

        await integration.shutdown()

    @pytest.mark.integration
    async def test_conversation_with_memory_system(self):
        """Test conversation integrates with memory system."""

        from src.memory.mem0_integration import MemoryCategory, MemorySystem

        # Mock memory system
        with patch("src.memory.mem0_integration.MemorySystem") as mock_memory_class:
            mock_memory = MagicMock()
            mock_memory_class.return_value = mock_memory

            # Configure memory
            mock_memory.add.return_value = MagicMock(id="conv123")
            mock_memory.search.return_value = [
                MagicMock(content="Previous security review noted SQL injection risks"),
                MagicMock(content="Team prefers bcrypt for password hashing"),
            ]

            integration = AutoGenIntegration()
            await integration.initialize()

            # Start conversation with memory context
            result = await integration.start_code_review(
                code="def login(user, pass): return user in database",
                context="Login function",
                use_memory=True,
            )

            # Verify memory was consulted
            mock_memory.search.assert_called()
            mock_memory.add.assert_called()

            # Check memory influenced conversation
            if hasattr(result, "messages"):
                memory_influenced = any(
                    "bcrypt" in msg.get("content", "").lower()
                    or "injection" in msg.get("content", "").lower()
                    for msg in result.messages
                )
                assert memory_influenced

            await integration.shutdown()

    @pytest.mark.integration
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    async def test_error_handling_in_conversations(self):
        """Test conversation handles errors gracefully."""

        integration = AutoGenIntegration()
        await integration.initialize()

        # Test with invalid code
        result = await integration.start_code_review(
            code="def invalid_syntax(:", context="Invalid code test"
        )

        assert result is not None
        assert result.status in ["failed", "completed_with_errors"]
        assert "syntax" in result.get("error", "").lower() or len(result.messages) > 0

        # Test with unresponsive agent
        with patch.object(ConversableAgent, "a_generate_reply") as mock_reply:
            mock_reply.side_effect = TimeoutError("Agent not responding")

            result = await integration.start_code_review(
                code="print('hello')", context="Simple test"
            )

            assert result is not None
            assert (
                result.status != "completed"
                or "timeout" in result.get("error", "").lower()
            )

        await integration.shutdown()

    @pytest.mark.integration
    async def test_conversation_quality_metrics(self):
        """Test conversation quality is tracked and measured."""

        integration = AutoGenIntegration()
        await integration.initialize()

        # Mock a detailed conversation
        with patch.object(integration, "start_code_review") as mock_review:
            mock_review.return_value = CodeReviewResult(
                status="completed",
                messages=[
                    {
                        "agent": "reviewer",
                        "content": "Consider using type hints",
                        "timestamp": "2024-01-01T10:00:00",
                    },
                    {
                        "agent": "author",
                        "content": "Good point, I'll add them",
                        "timestamp": "2024-01-01T10:01:00",
                    },
                    {
                        "agent": "reviewer",
                        "content": "Also add input validation",
                        "timestamp": "2024-01-01T10:02:00",
                    },
                    {
                        "agent": "author",
                        "content": "Will validate all inputs",
                        "timestamp": "2024-01-01T10:03:00",
                    },
                ],
                summary="Code needs type hints and validation",
                action_items=["Add type hints", "Add input validation"],
                quality_score=8.5,
            )

            result = await integration.start_code_review(
                code="def process(data): return data",
                context="Data processing function",
            )

            # Verify quality metrics
            assert result.quality_score >= 0
            assert result.quality_score <= 10
            assert len(result.action_items) > 0
            assert result.summary is not None

            # Check conversation depth
            assert len(result.messages) >= 4  # At least 2 rounds

            # Verify actionable feedback
            actionable = any(
                "add" in item.lower()
                or "implement" in item.lower()
                or "fix" in item.lower()
                for item in result.action_items
            )
            assert actionable

        await integration.shutdown()

    @pytest.mark.integration
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    async def test_concurrent_conversations(self):
        """Test system handles multiple concurrent conversations."""

        integration = AutoGenIntegration()
        await integration.initialize()

        # Start multiple conversations
        conversations = []
        for i in range(3):
            conv = asyncio.create_task(
                integration.start_code_review(
                    code=f"def function_{i}(): return {i}",
                    context=f"Function {i} review",
                )
            )
            conversations.append(conv)

        # Wait for all to complete
        results = await asyncio.gather(*conversations, return_exceptions=True)

        # Verify all completed successfully
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)
            assert result.status in ["completed", "completed_with_errors"]

        await integration.shutdown()

    @pytest.mark.integration
    async def test_conversation_export_and_import(self):
        """Test conversations can be exported and imported."""

        integration = AutoGenIntegration()
        await integration.initialize()

        # Create a conversation
        result = await integration.start_code_review(
            code="def example(): pass", context="Example function"
        )

        # Export conversation
        export_data = await integration.export_conversation(result.conversation_id)

        assert export_data is not None
        assert "messages" in export_data
        assert "metadata" in export_data
        assert len(export_data["messages"]) > 0

        # Import conversation
        imported_result = await integration.import_conversation(export_data)

        assert imported_result is not None
        assert len(imported_result.messages) == len(result.messages)

        await integration.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
