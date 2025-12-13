"""
Integration test for MCP Server and Agent workflow.
Tests: MCP Server → Tools → Agent Execution → Response
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from src.mcp_server.server import MCPServer
from src.mcp_server.tools import ToolRegistry


class TestMCPAgentWorkflow:
    """Test MCP server integration with agent workflows."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_server_initialization_and_tools(self):
        """Test MCP server initializes and registers all tools."""
        
        # Initialize MCP server
        server = MCPServer()
        await server.initialize()
        
        # Verify server is running
        assert server.is_running()
        
        # Check tool registry
        registry = server.get_tool_registry()
        assert isinstance(registry, ToolRegistry)
        
        # Verify core tools are registered
        tools = registry.list_tools()
        assert len(tools) > 0
        
        # Check for essential tools
        tool_names = [tool.name for tool in tools]
        essential_tools = [
            "get_synthesis_job",
            "set_synthesis_job",
            "get_unified_search",
            "get_dependency_analyzer",
            "get_assistant"
        ]
        
        for tool in essential_tools:
            assert tool in tool_names, f"Missing essential tool: {tool}"
        
        await server.shutdown()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_workflow(self):
        """Test complete tool execution through MCP server."""
        
        server = MCPServer()
        await server.initialize()
        
        # Test synthesis job tool
        registry = server.get_tool_registry()
        
        # Execute get_synthesis_job
        result = await registry.execute_tool(
            "get_synthesis_job",
            {"job_id": "test_job_123"}
        )
        
        assert result is not None
        assert "status" in result or "error" in result
        
        # Execute set_synthesis_job
        result = await registry.execute_tool(
            "set_synthesis_job",
            {
                "job_id": "new_job_456",
                "status": "in_progress",
                "result": {"files": ["main.py", "README.md"]}
            }
        )
        
        assert result is not None
        
        # Execute unified search
        with patch('src.discovery.unified_search.UnifiedSearch.search') as mock_search:
            mock_search.return_value = [
                {
                    "name": "test-repo",
                    "url": "https://github.com/test/test-repo",
                    "stars": 100,
                    "language": "Python"
                }
            ]
            
            result = await registry.execute_tool(
                "get_unified_search",
                {"query": "python web framework", "limit": 10}
            )
            
            assert result is not None
            assert len(result) > 0
            assert result[0]["name"] == "test-repo"
        
        await server.shutdown()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_interaction_with_mcp_tools(self):
        """Test agents can interact with MCP tools effectively."""
        
        from src.agents.code_agent import CodeAgent
        from src.llm.litellm_router import LiteLLMRouter
        
        # Mock LLM responses
        with patch.object(LiteLLMRouter, 'complete') as mock_llm:
            mock_llm.return_value = {
                "content": "I'll help you analyze this codebase. Let me search for relevant repositories first.",
                "provider": "mock",
                "tokens_used": 50
            }
            
            # Initialize agent
            agent = CodeAgent()
            await agent.initialize()
            
            # Connect to MCP server
            server = MCPServer()
            await server.initialize()
            
            # Agent uses MCP tools
            task = "Find and analyze a Python web framework repository"
            
            # Simulate agent workflow
            # 1. Search for repositories
            search_result = await agent.execute_tool(
                "get_unified_search",
                {"query": "python web framework", "limit": 5}
            )
            
            assert search_result is not None
            
            # 2. Get synthesis job details
            if search_result:
                job_result = await agent.execute_tool(
                    "get_synthesis_job",
                    {"job_id": "analysis_job"}
                )
                
                assert job_result is not None
            
            await server.shutdown()
            await agent.shutdown()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_in_mcp_workflow(self):
        """Test MCP server handles errors gracefully."""
        
        server = MCPServer()
        await server.initialize()
        
        registry = server.get_tool_registry()
        
        # Test with invalid tool name
        result = await registry.execute_tool(
            "nonexistent_tool",
            {"param": "value"}
        )
        
        assert result is not None
        assert "error" in result
        
        # Test with invalid parameters
        result = await registry.execute_tool(
            "get_synthesis_job",
            {}  # Missing required job_id
        )
        
        assert result is not None
        assert "error" in result
        
        # Test tool timeout
        with patch('src.mcp_server.tools.execute_with_timeout') as mock_timeout:
            mock_timeout.side_effect = TimeoutError("Tool execution timed out")
            
            result = await registry.execute_tool(
                "get_synthesis_job",
                {"job_id": "test"}
            )
            
            assert result is not None
            assert "timeout" in result.get("error", "").lower()
        
        await server.shutdown()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_server_with_memory_integration(self):
        """Test MCP server integrates with memory system."""
        
        from src.memory.mem0_integration import MemorySystem, MemoryCategory
        
        # Mock memory system
        with patch('src.memory.mem0_integration.MemorySystem') as mock_memory_class:
            mock_memory = MagicMock()
            mock_memory_class.return_value = mock_memory
            
            # Configure memory mock
            mock_memory.add.return_value = MagicMock(
                id="mem123",
                content="User prefers Python projects",
                category=MemoryCategory.PREFERENCE
            )
            mock_memory.search.return_value = [
                MagicMock(content="Previous analysis of FastAPI"),
                MagicMock(content="Django project preferences")
            ]
            
            server = MCPServer()
            await server.initialize()
            
            # Test assistant tool with memory
            registry = server.get_tool_registry()
            
            result = await registry.execute_tool(
                "get_assistant",
                {
                    "message": "Find me a Python web framework",
                    "context": {"use_memory": True}
                }
            )
            
            assert result is not None
            assert "response" in result
            
            # Verify memory was accessed
            mock_memory.search.assert_called()
            
            await server.shutdown()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test MCP server handles concurrent tool execution."""
        
        import asyncio
        
        server = MCPServer()
        await server.initialize()
        
        registry = server.get_tool_registry()
        
        # Mock tool execution
        with patch.object(registry, '_execute_tool_internal') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            # Execute multiple tools concurrently
            tasks = []
            for i in range(10):
                task = registry.execute_tool(
                    "get_synthesis_job",
                    {"job_id": f"job_{i}"}
                )
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all executed successfully
            assert len(results) == 10
            for result in results:
                assert not isinstance(result, Exception)
                assert result["status"] == "success"
            
            # Verify concurrent execution
            assert mock_execute.call_count == 10
        
        await server.shutdown()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_server_resource_management(self):
        """Test MCP server manages resources properly."""
        
        server = MCPServer()
        await server.initialize()
        
        # Test resource registration
        await server.register_resource(
            name="test_resource",
            uri="file:///test/path",
            description="Test resource for workflow"
        )
        
        # List resources
        resources = await server.list_resources()
        assert len(resources) > 0
        
        # Get specific resource
        resource = await server.get_resource("test_resource")
        assert resource is not None
        assert resource["uri"] == "file:///test/path"
        
        # Test resource cleanup
        await server.unregister_resource("test_resource")
        resources_after = await server.list_resources()
        assert "test_resource" not in [r["name"] for r in resources_after]
        
        await server.shutdown()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_with_quality_checks(self):
        """Test workflow includes quality checks via MCP tools."""
        
        server = MCPServer()
        await server.initialize()
        
        registry = server.get_tool_registry()
        
        # Mock quality gate tool
        with patch('src.quality.quality_gate.QualityGate.run_checks') as mock_quality:
            mock_quality.return_value = [
                {"check": "security", "status": "pass"},
                {"check": "linting", "status": "fail", "issues": 3},
                {"check": "coverage", "status": "pass"}
            ]
            
            # Execute quality check through MCP
            result = await registry.execute_tool(
                "run_quality_gate",
                {"project_path": "/test/project"}
            )
            
            assert result is not None
            assert len(result) == 3
            assert result[1]["status"] == "fail"
            assert result[1]["issues"] == 3
        
        await server.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
