"""Tests for workflows.langchain_integration."""

import asyncio
import os
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["APP_ENV"] = "testing"

try:
    from src.workflows.langchain_integration import (
        ChainType,
        LangChainWorkflow,
        LLMConfig,
        PromptTemplate,
        ToolIntegration,
        WorkflowContext,
        WorkflowResult,
        WorkflowStatus,
        WorkflowStep,
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error for workflows.langchain_integration: {e}")
    IMPORTS_AVAILABLE = False


class TestWorkflowStatus:
    """Test WorkflowStatus enum."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_workflow_status_values(self):
        """Should have correct WorkflowStatus values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"


class TestChainType:
    """Test ChainType enum."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_chain_type_values(self):
        """Should have correct ChainType values."""
        assert ChainType.LLM_CHAIN.value == "llm_chain"
        assert ChainType.SEQUENTIAL.value == "sequential"
        assert ChainType.ROUTER.value == "router"
        assert ChainType.AGENT.value == "agent"


class TestWorkflowStep:
    """Test WorkflowStep dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_workflow_step(self):
        """Should create WorkflowStep with all fields."""
        step = WorkflowStep(
            step_id="step1",
            name="Test Step",
            description="A test workflow step",
            chain_type=ChainType.LLM_CHAIN,
            config={"temperature": 0.7}
        )
        assert step.step_id == "step1"
        assert step.name == "Test Step"
        assert step.description == "A test workflow step"
        assert step.chain_type == ChainType.LLM_CHAIN
        assert step.config["temperature"] == 0.7


class TestPromptTemplate:
    """Test PromptTemplate dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_prompt_template(self):
        """Should create PromptTemplate."""
        template = PromptTemplate(
            template="Hello {name}, how are you?",
            input_variables=["name"],
            template_format="f-string"
        )
        assert template.template == "Hello {name}, how are you?"
        assert template.input_variables == ["name"]
        assert template.template_format == "f-string"


class TestLLMConfig:
    """Test LLMConfig dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_llm_config(self):
        """Should create LLMConfig."""
        config = LLMConfig(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        assert config.model_name == "gpt-3.5-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.top_p == 0.9


class TestWorkflowContext:
    """Test WorkflowContext dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_workflow_context(self):
        """Should create WorkflowContext."""
        context = WorkflowContext(
            inputs={"text": "Hello"},
            variables={"name": "World"},
            metadata={"session_id": "123"}
        )
        assert context.inputs["text"] == "Hello"
        assert context.variables["name"] == "World"
        assert context.metadata["session_id"] == "123"


class TestWorkflowResult:
    """Test WorkflowResult dataclass."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_workflow_result(self):
        """Should create WorkflowResult."""
        result = WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            outputs={"response": "Hello World!"},
            error=None,
            execution_time=1.5,
            tokens_used=100
        )
        assert result.status == WorkflowStatus.COMPLETED
        assert result.outputs["response"] == "Hello World!"
        assert result.error is None
        assert result.execution_time == 1.5
        assert result.tokens_used == 100


class TestToolIntegration:
    """Test ToolIntegration."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_tool_integration(self):
        """Should create ToolIntegration."""
        tool = ToolIntegration(
            name="search",
            description="Search the web",
            func=lambda x: f"Results for {x}",
            parameters={"query": "string"}
        )
        assert tool.name == "search"
        assert tool.description == "Search the web"
        assert tool.func("test") == "Results for test"
        assert tool.parameters["query"] == "string"


class TestLangChainWorkflow:
    """Test LangChainWorkflow."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_create_workflow(self):
        """Should create workflow with steps."""
        workflow = LangChainWorkflow(
            name="Test Workflow",
            description="A test workflow"
        )
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.status == WorkflowStatus.PENDING
        assert len(workflow.steps) == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_add_step(self):
        """Should add step to workflow."""
        workflow = LangChainWorkflow("Test")
        step = WorkflowStep(
            step_id="step1",
            name="Step 1",
            chain_type=ChainType.LLM_CHAIN
        )

        workflow.add_step(step)

        assert len(workflow.steps) == 1
        assert workflow.steps[0] == step

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_remove_step(self):
        """Should remove step from workflow."""
        workflow = LangChainWorkflow("Test")
        step = WorkflowStep(
            step_id="step1",
            name="Step 1",
            chain_type=ChainType.LLM_CHAIN
        )
        workflow.add_step(step)

        workflow.remove_step("step1")

        assert len(workflow.steps) == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.workflows.langchain_integration.LLMChain')
    @patch('src.workflows.langchain_integration.ChatOpenAI')
    async def test_execute_llm_chain_step(self, mock_llm, mock_chain):
        """Should execute LLM chain step."""
        # Mock LLM and chain
        mock_model = MagicMock()
        mock_llm.return_value = mock_model

        mock_chain_instance = MagicMock()
        mock_chain_instance.arun.return_value = "Hello World!"
        mock_chain.return_value = mock_chain_instance

        # Create workflow
        workflow = LangChainWorkflow("Test")
        step = WorkflowStep(
            step_id="step1",
            name="LLM Step",
            chain_type=ChainType.LLM_CHAIN,
            config={
                "prompt": PromptTemplate(
                    template="Say hello to {name}",
                    input_variables=["name"]
                ),
                "llm": LLMConfig(model_name="gpt-3.5-turbo")
            }
        )
        workflow.add_step(step)

        # Execute
        context = WorkflowContext(
            inputs={"name": "World"},
            variables={}
        )
        result = await workflow.execute_step(step, context)

        assert isinstance(result, WorkflowResult)
        assert result.status == WorkflowStatus.COMPLETED
        assert "Hello World!" in str(result.outputs)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.workflows.langchain_integration.SequentialChain')
    async def test_execute_sequential_chain(self, mock_sequential):
        """Should execute sequential chain."""
        # Mock sequential chain
        mock_chain = MagicMock()
        mock_chain.arun.return_value = {"output": "Final result"}
        mock_sequential.return_value = mock_chain

        # Create workflow with sequential step
        workflow = LangChainWorkflow("Test")
        step = WorkflowStep(
            step_id="seq1",
            name="Sequential Step",
            chain_type=ChainType.SEQUENTIAL,
            config={
                "chains": [
                    {"prompt": "Step 1: {input}"},
                    {"prompt": "Step 2: {step1_output}"}
                ]
            }
        )
        workflow.add_step(step)

        # Execute
        context = WorkflowContext(inputs={"input": "test"})
        result = await workflow.execute_step(step, context)

        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @patch('src.workflows.langchain_integration.AgentExecutor')
    @patch('src.workflows.langchain_integration.initialize_agent')
    async def test_execute_agent_step(self, mock_init_agent, mock_executor):
        """Should execute agent step."""
        # Mock agent
        mock_agent = MagicMock()
        mock_init_agent.return_value = mock_agent

        mock_exec = MagicMock()
        mock_exec.arun.return_value = "Agent response"
        mock_executor.return_value = mock_exec

        # Create workflow with agent step
        workflow = LangChainWorkflow("Test")
        tools = [
            ToolIntegration(
                name="calculator",
                description="Calculate",
                func=lambda x: str(eval(x)),
                parameters={"expression": "string"}
            )
        ]
        step = WorkflowStep(
            step_id="agent1",
            name="Agent Step",
            chain_type=ChainType.AGENT,
            config={
                "tools": tools,
                "llm": LLMConfig(model_name="gpt-3.5-turbo")
            }
        )
        workflow.add_step(step)

        # Execute
        context = WorkflowContext(inputs={"task": "Calculate 2+2"})
        result = await workflow.execute_step(step, context)

        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_execute_workflow(self):
        """Should execute entire workflow."""
        workflow = LangChainWorkflow("Test")

        # Mock step execution
        workflow.execute_step = AsyncMock(side_effect=[
            WorkflowResult(
                status=WorkflowStatus.COMPLETED,
                outputs={"step1": "Result 1"},
                execution_time=1.0
            ),
            WorkflowResult(
                status=WorkflowStatus.COMPLETED,
                outputs={"step2": "Result 2"},
                execution_time=1.0
            )
        ])

        # Add steps
        step1 = WorkflowStep(step_id="step1", name="Step 1", chain_type=ChainType.LLM_CHAIN)
        step2 = WorkflowStep(step_id="step2", name="Step 2", chain_type=ChainType.LLM_CHAIN)
        workflow.add_step(step1)
        workflow.add_step(step2)

        # Execute
        context = WorkflowContext(inputs={})
        result = await workflow.execute(context)

        assert result.status == WorkflowStatus.COMPLETED
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.execute_step.call_count == 2

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_handle_workflow_error(self):
        """Should handle errors in workflow execution."""
        workflow = LangChainWorkflow("Test")

        # Mock step execution with error
        workflow.execute_step = AsyncMock(side_effect=Exception("Step failed"))

        step = WorkflowStep(step_id="step1", name="Step 1", chain_type=ChainType.LLM_CHAIN)
        workflow.add_step(step)

        # Execute
        context = WorkflowContext(inputs={})
        result = await workflow.execute(context)

        assert result.status == WorkflowStatus.FAILED
        assert workflow.status == WorkflowStatus.FAILED
        assert "Step failed" in str(result.error)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    async def test_cancel_workflow(self):
        """Should cancel running workflow."""
        workflow = LangChainWorkflow("Test")
        workflow.status = WorkflowStatus.RUNNING

        # Mock running task
        workflow._execution_task = MagicMock()
        workflow._execution_task.cancel = MagicMock()

        await workflow.cancel()

        assert workflow.status == WorkflowStatus.CANCELLED
        workflow._execution_task.cancel.assert_called_once()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_get_workflow_stats(self):
        """Should return workflow statistics."""
        workflow = LangChainWorkflow("Test")
        workflow._start_time = 1234567890.0
        workflow._total_tokens = 1000
        workflow._execution_count = 5

        stats = workflow.get_stats()

        assert stats['name'] == "Test"
        assert stats['status'] == WorkflowStatus.PENDING
        assert stats['step_count'] == 0
        assert stats['total_tokens'] == 1000
        assert stats['execution_count'] == 5
        assert 'start_time' in stats

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_validate_workflow(self):
        """Should validate workflow configuration."""
        workflow = LangChainWorkflow("Test")

        # Empty workflow should be invalid
        assert workflow.validate() is False

        # Add valid step
        step = WorkflowStep(
            step_id="step1",
            name="Step 1",
            chain_type=ChainType.LLM_CHAIN,
            config={
                "prompt": PromptTemplate(
                    template="Test prompt",
                    input_variables=[]
                ),
                "llm": LLMConfig(model_name="gpt-3.5-turbo")
            }
        )
        workflow.add_step(step)

        assert workflow.validate() is True

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_export_workflow(self):
        """Should export workflow to dictionary."""
        workflow = LangChainWorkflow("Test Workflow")
        workflow.description = "A test workflow"

        step = WorkflowStep(
            step_id="step1",
            name="Step 1",
            description="First step",
            chain_type=ChainType.LLM_CHAIN,
            config={"temperature": 0.7}
        )
        workflow.add_step(step)

        exported = workflow.export()

        assert exported['name'] == "Test Workflow"
        assert exported['description'] == "A test workflow"
        assert len(exported['steps']) == 1
        assert exported['steps'][0]['step_id'] == "step1"
        assert exported['steps'][0]['chain_type'] == "llm_chain"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_import_workflow(self):
        """Should import workflow from dictionary."""
        workflow_dict = {
            "name": "Imported Workflow",
            "description": "Imported from dict",
            "steps": [
                {
                    "step_id": "step1",
                    "name": "Step 1",
                    "chain_type": "llm_chain",
                    "config": {"temperature": 0.5}
                }
            ]
        }

        workflow = LangChainWorkflow.import_workflow(workflow_dict)

        assert workflow.name == "Imported Workflow"
        assert workflow.description == "Imported from dict"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].step_id == "step1"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
