"""
Tests for Swarm Integration

Tests the lightweight agent handoff system for fast routing.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Check if Swarm is available
try:
    import swarm
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False
    swarm = None

from src.agents.swarm_integration import (
    HandoffResult,
    SwarmIntegration,
    create_swarm_integration,
)
from src.llm.litellm_router import LiteLLMRouter
from src.voice.manager import VoiceManager


class TestSwarmIntegration:
    """Test suite for Swarm integration."""

    @pytest.fixture
    def mock_voice_manager(self):
        """Create a mock VoiceManager."""
        manager = MagicMock(spec=VoiceManager)
        manager.speak = AsyncMock()
        return manager

    @pytest.fixture
    def mock_llm_router(self):
        """Create a mock LiteLLM router."""
        router = MagicMock(spec=LiteLLMRouter)
        return router

    @pytest.fixture
    def swarm_integration(self, mock_voice_manager, mock_llm_router):
        """Create a Swarm integration instance for testing."""
        if not SWARM_AVAILABLE:
            pytest.skip("Swarm not installed")
        with patch('src.agents.swarm_integration.SWARM_AVAILABLE', True):
            with patch('src.agents.swarm_integration.Swarm') as mock_swarm:
                with patch('src.agents.swarm_integration.Agent') as mock_agent:
                    # Create instance
                    integration = SwarmIntegration(
                        voice_manager=mock_voice_manager,
                        enable_voice_output=False,
                        llm_router=mock_llm_router
                    )

                    # Mock the client and agents
                    integration.client = MagicMock()
                    integration.agents = {
                        "code_helper": mock_agent(),
                        "doc_generator": mock_agent(),
                        "task_decomposer": mock_agent(),
                        "quick_fixer": mock_agent(),
                        "complex_reviewer": mock_agent()
                    }

                    return integration

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    def test_init_without_swarm(self, mock_voice_manager, mock_llm_router):
        """Test initialization when Swarm is not available."""
        with patch('src.agents.swarm_integration.SWARM_AVAILABLE', False):
            integration = SwarmIntegration(
                voice_manager=mock_voice_manager,
                enable_voice_output=True,
                llm_router=mock_llm_router
            )

            assert integration.enable_voice_output is True
            assert integration.client is None
            assert len(integration.agents) == 0

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    def test_init_with_swarm(self, mock_voice_manager, mock_llm_router):
        """Test initialization when Swarm is available."""
        with patch('src.agents.swarm_integration.SWARM_AVAILABLE', True):
            with patch('src.agents.swarm_integration.Swarm') as mock_swarm:
                integration = SwarmIntegration(
                    voice_manager=mock_voice_manager,
                    enable_voice_output=False,
                    llm_router=mock_llm_router
                )

                assert integration.client is not None
                assert len(integration.agents) == 5  # 5 default agents

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_quick_handoff_success(self, swarm_integration):
        """Test successful agent handoff."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.messages = [{"content": "Here's your answer!"}]
        mock_response.context_variables = {}

        swarm_integration.client.run.return_value = mock_response

        result = await swarm_integration.quick_handoff(
            agent_name="code_helper",
            message="What is Python?",
            context_variables={"user": "test"}
        )

        assert result.success is True
        assert result.agent_name == "code_helper"
        assert result.response == "Here's your answer!"
        assert result.context_variables == {}
        assert result.latency_ms > 0

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_quick_handoff_streaming(self, swarm_integration):
        """Test agent handoff with streaming."""
        # Create async generator for streaming
        async def mock_stream():
            chunks = ["Here's", " your", " streaming", " answer!"]
            for chunk in chunks:
                mock_chunk = MagicMock()
                mock_chunk.content = chunk
                yield mock_chunk

        swarm_integration.client.run_stream.return_value = mock_stream()

        result = await swarm_integration.quick_handoff(
            agent_name="code_helper",
            message="Stream me an answer",
            stream=True
        )

        assert result.success is True
        assert result.response == "Here's your streaming answer!"

    @pytest.mark.asyncio
    async def test_quick_handoff_no_swarm(self, mock_voice_manager, mock_llm_router):
        """Test handoff when Swarm is not available."""
        with patch('src.agents.swarm_integration.SWARM_AVAILABLE', False):
            integration = SwarmIntegration(
                voice_manager=mock_voice_manager,
                enable_voice_output=False,
                llm_router=mock_llm_router
            )

            result = await integration.quick_handoff(
                agent_name="code_helper",
                message="Test message"
            )

            assert result.success is False
            assert "Swarm not available" in result.response
            assert result.latency_ms == 0.0

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_quick_handoff_invalid_agent(self, swarm_integration):
        """Test handoff to non-existent agent."""
        result = await swarm_integration.quick_handoff(
            agent_name="nonexistent_agent",
            message="Test message"
        )

        assert result.success is False
        assert "not found" in result.response
        assert "code_helper" in result.response  # Should list available agents

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_quick_handoff_with_voice(self, swarm_integration):
        """Test handoff with voice output enabled."""
        swarm_integration.enable_voice_output = True

        # Mock response
        mock_response = MagicMock()
        mock_response.messages = [{"content": "Voice enabled response"}]
        mock_response.context_variables = {}

        swarm_integration.client.run.return_value = mock_response

        await swarm_integration.quick_handoff(
            agent_name="code_helper",
            message="Test with voice"
        )

        # Check voice was called for handoff announcement
        swarm_integration.voice_manager.speak.assert_called()

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_decompose_task(self, swarm_integration):
        """Test task decomposition."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.messages = [{
            "content": """1. Write the function signature (code_helper)
2. Add docstring (doc_generator)
3. Implement logic (code_helper)
4. Add error handling (quick_fixer)"""
        }]
        mock_response.context_variables = {}

        swarm_integration.client.run.return_value = mock_response

        steps = await swarm_integration.decompose_task(
            "Create a Python function to validate email"
        )

        assert len(steps) == 4
        assert steps[0]["agent"] == "code_helper"
        assert steps[1]["agent"] == "doc_generator"
        assert "function signature" in steps[0]["step"]

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_generate_docs(self, swarm_integration):
        """Test documentation generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.messages = [{
            "content": '"""This is a generated docstring."""'
        }]
        mock_response.context_variables = {}

        swarm_integration.client.run.return_value = mock_response

        docs = await swarm_integration.generate_docs(
            "def test(): pass",
            "docstring"
        )

        assert "docstring" in docs
        assert docs == '"""This is a generated docstring."""'

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_quick_fix(self, swarm_integration):
        """Test quick bug fixing."""
        # Mock response
        mock_response = MagicMock()
        mock_response.messages = [{
            "content": "def test():\n    return 'fixed'"
        }]
        mock_response.context_variables = {}

        swarm_integration.client.run.return_value = mock_response

        fixed_code = await swarm_integration.quick_fix(
            "def test():\n    retrn 'broken'",
            "SyntaxError: invalid syntax"
        )

        assert "return 'fixed'" in fixed_code

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_get_agent_list(self, swarm_integration):
        """Test getting list of available agents."""
        agents = await swarm_integration.get_agent_list()

        assert len(agents) == 5
        agent_names = [a["name"] for a in agents]
        assert "code_helper" in agent_names
        assert "doc_generator" in agent_names
        assert "task_decomposer" in agent_names
        assert "quick_fixer" in agent_names
        assert "complex_reviewer" in agent_names

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    def test_handoff_methods(self, swarm_integration):
        """Test agent handoff methods."""
        initial_count = swarm_integration.handoff_count

        # Test handoff to complex reviewer
        agent = swarm_integration._handoff_to_complex_reviewer()
        assert swarm_integration.handoff_count == initial_count + 1
        assert agent == swarm_integration.agents["complex_reviewer"]

        # Test handoff to code helper
        agent = swarm_integration._handoff_to_code_helper()
        assert swarm_integration.handoff_count == initial_count + 2
        assert agent == swarm_integration.agents["code_helper"]

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    def test_get_statistics(self, swarm_integration):
        """Test statistics tracking."""
        # Add some mock data
        swarm_integration.handoff_count = 10
        swarm_integration.total_latency = 500.0

        stats = swarm_integration.get_statistics()

        assert stats["total_handoffs"] == 10
        assert stats["average_latency_ms"] == 50.0
        assert stats["total_latency_ms"] == 500.0
        assert stats["agents_available"] == 5
        assert stats["swarm_available"] is True

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_create_swarm_integration_success(self):
        """Test factory function creates integration successfully."""
        with patch('src.agents.swarm_integration.SWARM_AVAILABLE', True):
            with patch('src.agents.swarm_integration.SwarmIntegration') as mock_class:
                mock_instance = MagicMock()
                mock_instance.quick_handoff = AsyncMock(return_value=MagicMock(success=True))
                mock_class.return_value = mock_instance

                integration = await create_swarm_integration(
                    enable_voice_output=False
                )

                assert integration is not None
                mock_instance.quick_handoff.assert_called_once()

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_create_swarm_integration_failure(self):
        """Test factory function handles initialization failure."""
        with patch('src.agents.swarm_integration.SwarmIntegration') as mock_class:
            mock_instance = MagicMock()
            mock_instance.quick_handoff = AsyncMock(return_value=MagicMock(success=False))
            mock_class.return_value = mock_instance

            integration = await create_swarm_integration()

            assert integration is None

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_create_swarm_integration_no_swarm(self):
        """Test factory function when Swarm is not available."""
        with patch('src.agents.swarm_integration.SWARM_AVAILABLE', False):
            with patch('src.agents.swarm_integration.SwarmIntegration') as mock_class:
                mock_instance = MagicMock()
                mock_class.return_value = mock_instance

                integration = await create_swarm_integration()

                assert integration is not None

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_speak_if_enabled(self, swarm_integration):
        """Test speaking only when enabled."""
        swarm_integration.enable_voice_output = True

        await swarm_integration._speak_if_enabled("Test message")

        swarm_integration.voice_manager.speak.assert_called_with(
            "Test message",
            voice="piper_default"
        )

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_speak_if_disabled(self, swarm_integration):
        """Test not speaking when disabled."""
        swarm_integration.enable_voice_output = False

        await swarm_integration._speak_if_enabled("Test message")

        swarm_integration.voice_manager.speak.assert_not_called()

    @pytest.mark.skipif(not SWARM_AVAILABLE, reason="Swarm not installed")
    @pytest.mark.asyncio
    async def test_handoff_error_handling(self, swarm_integration):
        """Test error handling during handoff."""
        swarm_integration.client.run.side_effect = Exception("API error")

        result = await swarm_integration.quick_handoff(
            agent_name="code_helper",
            message="Test message"
        )

        assert result.success is False
        assert "Handoff failed: API error" in result.response
        assert result.latency_ms == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
