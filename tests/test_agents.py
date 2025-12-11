"""
Tests for src/agents/ - AI Agent System

Full coverage tests for:
- BaseAgent
- ResearchAgent
- SynthesisAgent
- VoiceAgent
- AutomationAgent
- CodeAgent
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentResult,
    AgentTool,
    AgentStatus,
)
from src.agents.research_agent import ResearchAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.agents.voice_agent import VoiceAgent, VoiceState, get_voice_agent
from src.agents.automation_agent import AutomationAgent
from src.agents.code_agent import CodeAgent


class TestAgentStatus:
    """Tests for AgentStatus enum."""
    
    def test_all_statuses(self):
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.WAITING.value == "waiting"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.CANCELLED.value == "cancelled"


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""
    
    def test_defaults(self):
        config = AgentConfig(name="test")
        assert config.name == "test"
        assert config.description == ""
        assert config.provider == "lmstudio"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.auto_continue is True
        assert config.max_iterations == 10
        assert config.enable_tools is True
    
    def test_custom_config(self):
        config = AgentConfig(
            name="custom",
            description="Custom agent",
            provider="ollama",
            temperature=0.5,
            max_iterations=20,
            enable_voice=True,
        )
        assert config.provider == "ollama"
        assert config.temperature == 0.5
        assert config.max_iterations == 20
        assert config.enable_voice is True


class TestAgentResult:
    """Tests for AgentResult dataclass."""
    
    def test_success_result(self):
        result = AgentResult(
            success=True,
            output="Test output",
            steps=[{"action": "test"}],
            duration_ms=100,
            iterations=3,
        )
        assert result.success is True
        assert result.output == "Test output"
        assert len(result.steps) == 1
        assert result.duration_ms == 100
        assert result.iterations == 3
        assert result.error is None
    
    def test_failure_result(self):
        result = AgentResult(
            success=False,
            output=None,
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"
    
    def test_to_dict(self):
        result = AgentResult(
            success=True,
            output="output",
            steps=[],
            duration_ms=50,
            iterations=1,
            metadata={"key": "value"},
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["output"] == "output"
        assert d["duration_ms"] == 50
        assert d["metadata"]["key"] == "value"


class TestAgentTool:
    """Tests for AgentTool class."""
    
    def test_create_tool(self):
        def my_func(x):
            return x * 2
        
        tool = AgentTool(
            name="double",
            description="Doubles a number",
            func=my_func,
            parameters={"x": {"type": "integer"}},
        )
        assert tool.name == "double"
        assert tool.description == "Doubles a number"
    
    @pytest.mark.asyncio
    async def test_execute_sync_func(self):
        def sync_func(x):
            return x + 1
        
        tool = AgentTool(name="add", description="", func=sync_func)
        result = await tool.execute(x=5)
        assert result == 6
    
    @pytest.mark.asyncio
    async def test_execute_async_func(self):
        async def async_func(x):
            return x * 3
        
        tool = AgentTool(name="triple", description="", func=async_func)
        result = await tool.execute(x=4)
        assert result == 12
    
    def test_to_schema(self):
        tool = AgentTool(
            name="test",
            description="Test tool",
            func=lambda: None,
            parameters={"param1": {"type": "string"}},
        )
        schema = tool.to_schema()
        assert schema["name"] == "test"
        assert schema["description"] == "Test tool"
        assert "param1" in schema["parameters"]


class TestResearchAgent:
    """Tests for ResearchAgent class."""
    
    @pytest.fixture
    def agent(self):
        return ResearchAgent()
    
    def test_create_agent(self, agent):
        assert agent.config.name == "research_agent"
        assert agent.status == AgentStatus.IDLE
    
    def test_has_tools(self, agent):
        assert "search_github" in agent._tools
        assert "search_huggingface" in agent._tools
        assert "analyze_repo" in agent._tools
        assert "get_trends" in agent._tools
    
    @pytest.mark.asyncio
    async def test_get_trends(self, agent):
        result = await agent._get_trends()
        assert result["success"] is True
        assert "trends" in result
        assert len(result["trends"]) > 0
    
    def test_should_continue_incomplete(self, agent):
        step_result = {"complete": False}
        assert agent._should_continue(step_result) is True
    
    def test_should_continue_complete(self, agent):
        step_result = {"complete": True}
        assert agent._should_continue(step_result) is False


class TestSynthesisAgent:
    """Tests for SynthesisAgent class."""
    
    @pytest.fixture
    def agent(self):
        return SynthesisAgent()
    
    def test_create_agent(self, agent):
        assert agent.config.name == "synthesis_agent"
    
    def test_has_tools(self, agent):
        assert "plan_project" in agent._tools
        assert "generate_file" in agent._tools
        assert "resolve_dependencies" in agent._tools
        assert "create_readme" in agent._tools
        assert "assemble_project" in agent._tools
    
    @pytest.mark.asyncio
    async def test_resolve_dependencies(self, agent):
        result = await agent._resolve_dependencies(
            project_type="python",
            features=["voice", "llm"],
        )
        assert result["success"] is True
        assert "dependencies" in result
        assert "elevenlabs" in result["dependencies"]


class TestVoiceAgent:
    """Tests for VoiceAgent class."""
    
    @pytest.fixture
    def agent(self):
        return VoiceAgent()
    
    def test_create_agent(self, agent):
        assert agent.config.name == "voice_agent"
        assert agent.config.enable_voice is True
        assert agent.config.max_iterations == 100
    
    def test_initial_state(self, agent):
        assert agent._state.is_listening is False
        assert agent._state.is_speaking is False
        assert agent._state.auto_continue is True
    
    def test_has_tools(self, agent):
        assert "speak" in agent._tools
        assert "listen" in agent._tools
        assert "execute_command" in agent._tools
    
    @pytest.mark.asyncio
    async def test_execute_command_stop(self, agent):
        result = await agent._execute_command("stop")
        assert result["action"] == "cancel"
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_command_search(self, agent):
        result = await agent._execute_command("search for python")
        assert result["action"] == "search"
        assert result["query"] == "python"
    
    @pytest.mark.asyncio
    async def test_execute_command_create(self, agent):
        result = await agent._execute_command("create a chatbot")
        assert result["action"] == "synthesize"
        assert "chatbot" in result["idea"]
    
    @pytest.mark.asyncio
    async def test_execute_command_chat(self, agent):
        result = await agent._execute_command("hello there")
        assert result["action"] == "chat"
        assert result["message"] == "hello there"
    
    @pytest.mark.asyncio
    async def test_start_listening(self, agent):
        await agent.start_listening()
        assert agent._state.is_listening is True
        assert agent._state.auto_continue is True
    
    @pytest.mark.asyncio
    async def test_stop_listening(self, agent):
        agent._state.is_listening = True
        await agent.stop_listening()
        assert agent._state.is_listening is False
        assert agent._state.auto_continue is False
    
    def test_get_state(self, agent):
        state = agent.get_state()
        assert "is_listening" in state
        assert "is_speaking" in state
        assert "is_processing" in state
        assert "auto_continue" in state
    
    def test_on_transcription_callback(self, agent):
        callback = Mock()
        agent.on_transcription(callback)
        assert agent._on_transcription is callback
    
    def test_on_response_callback(self, agent):
        callback = Mock()
        agent.on_response(callback)
        assert agent._on_response is callback


class TestVoiceState:
    """Tests for VoiceState dataclass."""
    
    def test_defaults(self):
        state = VoiceState()
        assert state.is_listening is False
        assert state.is_speaking is False
        assert state.is_processing is False
        assert state.current_text == ""
        assert state.last_response == ""
        assert state.auto_continue is True


class TestGetVoiceAgent:
    """Tests for get_voice_agent function."""
    
    def test_singleton(self):
        agent1 = get_voice_agent()
        agent2 = get_voice_agent()
        assert agent1 is agent2


class TestAutomationAgent:
    """Tests for AutomationAgent class."""
    
    @pytest.fixture
    def agent(self):
        return AutomationAgent()
    
    def test_create_agent(self, agent):
        assert agent.config.name == "automation_agent"
    
    def test_has_tools(self, agent):
        assert "run_workflow" in agent._tools
        assert "schedule_task" in agent._tools
        assert "check_health" in agent._tools
        assert "recover_component" in agent._tools
        assert "run_tests" in agent._tools
        assert "get_metrics" in agent._tools
    
    @pytest.mark.asyncio
    async def test_schedule_task(self, agent):
        result = await agent._schedule_task(
            task_id="task_1",
            task_type="research",
            schedule="0 */6 * * *",
            data={"topic": "AI"},
        )
        assert result["success"] is True
        assert result["task_id"] == "task_1"
        assert "task_1" in agent._scheduled_tasks
    
    @pytest.mark.asyncio
    async def test_recover_component(self, agent):
        result = await agent._recover_component("lm_studio")
        assert result["success"] is True
        assert result["component"] == "lm_studio"
        assert "action" in result


class TestCodeAgent:
    """Tests for CodeAgent class."""
    
    @pytest.fixture
    def agent(self):
        return CodeAgent()
    
    def test_create_agent(self, agent):
        assert agent.config.name == "code_agent"
    
    def test_has_tools(self, agent):
        assert "generate_code" in agent._tools
        assert "fix_code" in agent._tools
        assert "review_code" in agent._tools
        assert "refactor_code" in agent._tools
        assert "generate_docs" in agent._tools
        assert "explain_code" in agent._tools
    
    def test_should_continue(self, agent):
        assert agent._should_continue({"complete": False}) is True
        assert agent._should_continue({"complete": True}) is False
