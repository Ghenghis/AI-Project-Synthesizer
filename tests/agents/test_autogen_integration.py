"""
Tests for AutoGen Integration

Tests the multi-agent conversation system for code review.
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Check if AutoGen is available
try:
    from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    UserProxyAgent = None

from src.agents.autogen_integration import (
    AutoGenIntegration,
    CodeReviewResult,
    create_autogen_integration
)
from src.voice.manager import VoiceManager
from src.llm.litellm_router import LiteLLMRouter


class TestAutoGenIntegration:
    """Test suite for AutoGen integration."""
    
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
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    def autogen_integration(self, mock_voice_manager, mock_llm_router):
        """Create an AutoGen integration instance for testing."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'AUTOGEN_MODEL': 'gpt-3.5-turbo'
        }):
            return AutoGenIntegration(
                voice_manager=mock_voice_manager,
                enable_voice_output=False,
                llm_router=mock_llm_router
            )
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    def test_init_with_env_vars(self, mock_voice_manager, mock_llm_router):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'AUTOGEN_MODEL': 'gpt-4'
        }):
            integration = AutoGenIntegration(
                voice_manager=mock_voice_manager,
                enable_voice_output=True,
                llm_router=mock_llm_router
            )
            
            assert integration.enable_voice_output is True
            assert integration.voice_manager == mock_voice_manager
            assert integration.llm_router == mock_llm_router
            assert integration.llm_config is not None
            assert len(integration.llm_config['config_list']) > 0
            assert integration.llm_config['config_list'][0]['model'] == 'gpt-4'
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    def test_init_without_api_key(self, mock_voice_manager, mock_llm_router):
        """Test initialization without API key falls back to mock mode."""
        with patch.dict(os.environ, {}, clear=True):
            integration = AutoGenIntegration(
                voice_manager=mock_voice_manager,
                enable_voice_output=False,
                llm_router=mock_llm_router
            )
            
            assert integration.llm_config['config_list'][0]['model'] == 'mock'
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    def test_get_llm_config_with_multiple_keys(self, mock_voice_manager):
        """Test LLM config building with multiple API keys available."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'openai-key',
            'ANTHROPIC_API_KEY': 'anthropic-key',
            'OPENAI_API_BASE': 'https://api.openai.com/v1'
        }):
            integration = AutoGenIntegration(
                voice_manager=mock_voice_manager,
                enable_voice_output=False
            )
            
            config_list = integration.llm_config['config_list']
            # Should have OpenAI config
            openai_config = next(c for c in config_list if c['model'] == 'gpt-3.5-turbo')
            assert openai_config['api_key'] == 'openai-key'
            assert openai_config['api_base'] == 'https://api.openai.com/v1'
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_review_code_success(self, autogen_integration):
        """Test successful code review."""
        # Mock the agent conversation
        with patch.object(autogen_integration.code_reviewer, 'a_initiate_chat') as mock_chat:
            # Create mock chat history
            mock_result = MagicMock()
            mock_result.chat_history = [
                {"content": "I've reviewed the code. It looks good with a quality score of 8."}
            ]
            mock_chat.return_value = mock_result
            
            code = """
def hello_world():
    print("Hello, World!")
    return True
"""
            
            result = await autogen_integration.review_code(
                code=code,
                file_path="test.py",
                context="Simple test function"
            )
            
            assert isinstance(result, CodeReviewResult)
            assert result.code_quality_score == 8.0
            assert result.approved is True
            assert len(result.suggestions) > 0
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_review_code_with_security_issues(self, autogen_integration):
        """Test code review that identifies security issues."""
        with patch.object(autogen_integration.code_reviewer, 'a_initiate_chat') as mock_chat:
            mock_result = MagicMock()
            mock_result.chat_history = [
                {"content": "Critical security vulnerability found: SQL injection risk. Quality score: 4. Rejected."}
            ]
            mock_chat.return_value = mock_result
            
            code = "query = f'SELECT * FROM users WHERE id = {user_id}'"
            
            result = await autogen_integration.review_code(
                code=code,
                file_path="database.py",
                context="Database query"
            )
            
            assert result.approved is False
            assert result.code_quality_score == 4.0
            assert len(result.security_issues) > 0
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_review_code_with_voice_output(self, autogen_integration):
        """Test code review with voice output enabled."""
        autogen_integration.enable_voice_output = True
        
        with patch.object(autogen_integration.code_reviewer, 'a_initiate_chat') as mock_chat:
            mock_result = MagicMock()
            mock_result.chat_history = [
                {"content": "Code reviewed. Quality score: 9. Approved."}
            ]
            mock_chat.return_value = mock_result
            
            await autogen_integration.review_code(
                code="print('test')",
                file_path="test.py"
            )
            
            # Check that voice was used
            autogen_integration.voice_manager.speak.assert_called()
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_review_code_error_handling(self, autogen_integration):
        """Test error handling during code review."""
        with patch.object(autogen_integration.code_reviewer, 'a_initiate_chat') as mock_chat:
            mock_chat.side_effect = Exception("API error")
            
            result = await autogen_integration.review_code(
                code="print('test')",
                file_path="test.py"
            )
            
            assert result.approved is False
            assert "Review failed" in result.security_issues[0]
            assert result.agent_consensus == "Review failed - system error"
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_simple_conversation_test(self, autogen_integration):
        """Test basic conversation between agents."""
        with patch.object(autogen_integration.code_reviewer, 'a_initiate_chat') as mock_chat:
            mock_chat.return_value = MagicMock()
            
            result = await autogen_integration.simple_conversation_test()
            
            assert result is True
            mock_chat.assert_called_once()
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_create_autogen_integration_success(self):
        """Test factory function creates integration successfully."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            integration = await create_autogen_integration(
                enable_voice_output=False
            )
            
            assert integration is not None
            assert isinstance(integration, AutoGenIntegration)
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_create_autogen_integration_failure(self):
        """Test factory function handles initialization failure."""
        with patch('src.agents.autogen_integration.AutoGenIntegration') as mock_class:
            mock_instance = MagicMock()
            mock_instance.simple_conversation_test = AsyncMock(return_value=False)
            mock_class.return_value = mock_instance
            
            integration = await create_autogen_integration()
            
            assert integration is None
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    def test_parse_conversation_result_empty(self, autogen_integration):
        """Test parsing empty conversation history."""
        result = autogen_integration._parse_conversation_result([])
        
        assert result.code_quality_score == 5.0
        assert "No conversation history" in result.security_issues[0]
        assert result.approved is False
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    def test_parse_conversation_result_with_scores(self, autogen_integration):
        """Test parsing conversation with quality scores."""
        history = [
            {"content": "short"},
            {"content": "The code has a quality score of 9 out of 10. It's approved."}
        ]
        
        result = autogen_integration._parse_conversation_result(history)
        
        assert result.code_quality_score == 9.0
        assert result.approved is True
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    def test_parse_conversation_result_rejected(self, autogen_integration):
        """Test parsing conversation with rejection."""
        history = [
            {"content": "This code is rejected due to security issues. Quality score: 3."}
        ]
        
        result = autogen_integration._parse_conversation_result(history)
        
        assert result.code_quality_score == 3.0
        assert result.approved is False
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_speak_if_enabled(self, autogen_integration):
        """Test speaking only when enabled."""
        autogen_integration.enable_voice_output = True
        
        await autogen_integration._speak_if_enabled("Test message")
        
        autogen_integration.voice_manager.speak.assert_called_with(
            "Test message", 
            voice="piper_default"
        )
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_speak_if_disabled(self, autogen_integration):
        """Test not speaking when disabled."""
        autogen_integration.enable_voice_output = False
        
        await autogen_integration._speak_if_enabled("Test message")
        
        autogen_integration.voice_manager.speak.assert_not_called()
    
    @pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
    @pytest.mark.asyncio
    async def test_announce_results(self, autogen_integration):
        """Test result announcements."""
        autogen_integration.enable_voice_output = True
        
        # Test approved result
        result = CodeReviewResult(
            code_quality_score=8.0,
            security_issues=[],
            suggestions=[],
            approved=True,
            agent_consensus="Good code"
        )
        
        await autogen_integration._announce_results(result)
        
        autogen_integration.voice_manager.speak.assert_called()
        call_args = autogen_integration.voice_manager.speak.call_args[0][0]
        assert "8 out of 10" in call_args
        assert "approved" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
