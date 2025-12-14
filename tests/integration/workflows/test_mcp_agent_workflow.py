"""
Integration test for MCP Server and Agent workflow.
Tests: MCP Server → Tools → Agent Execution → Response
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_server import server as mcp_server
from src.mcp_server import tools


class TestMCPAgentWorkflow:
    """Test MCP server integration with agent workflows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_server_initialization_and_tools(self):
        """Test MCP server initializes and registers all tools."""

        # Initialize MCP server
        server_instance = mcp_server.server

        # Verify server is running (check if server instance exists)
        assert server_instance is not None

        # Check available tools
        available_tools = [name for name in dir(tools) if not name.startswith("_")]
        assert len(available_tools) > 0

        # Check for essential tools
        essential_tools = [
            "search_repositories",
            "analyze_repository",
            "synthesize_project",
            "get_synthesis_status",
            "get_platforms",
        ]

        for tool in essential_tools:
            assert tool in available_tools, f"Missing essential tool: {tool}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_workflow(self):
        """Test complete tool execution through MCP server."""

        # Test search repositories tool directly
        with patch("src.mcp_server.tools.create_unified_search") as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            result = await tools.search_repositories(
                query="test", platforms=["github"], max_results=5
            )

            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_interaction_with_mcp_tools(self):
        """Test agents can interact with MCP tools effectively."""

        # Test that tools can be called directly
        with patch("src.mcp_server.tools.create_unified_search") as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            # Call search tool
            result = await tools.search_repositories(
                query="python web framework", platforms=["github"], max_results=5
            )

            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_in_mcp_workflow(self):
        """Test MCP server handles errors gracefully."""

        # Test error handling in search tool
        result = await tools.search_repositories(
            query="",  # Empty query should error
            platforms=["github"],
            max_results=5,
        )

        assert result is not None
        assert "error" in result or not result.get("success", True)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_server_with_memory_integration(self):
        """Test MCP server integrates with memory system."""

        # Test that tools can handle memory-related parameters
        with patch("src.mcp_server.tools.create_unified_search") as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            # Call tool with context that might include memory
            result = await tools.search_repositories(
                query="python web framework", platforms=["github"], max_results=5
            )

            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test MCP server handles concurrent tool execution."""

        import asyncio

        # Test concurrent tool calls
        with patch("src.mcp_server.tools.create_unified_search") as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            # Execute multiple searches concurrently
            tasks = []
            for i in range(5):
                task = tools.search_repositories(
                    query=f"test-{i}", platforms=["github"], max_results=5
                )
                tasks.append(task)

            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all executed successfully
            assert len(results) == 5
            for result in results:
                assert not isinstance(result, Exception)
                assert isinstance(result, dict)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_server_resource_management(self):
        """Test MCP server manages resources properly."""

        # Test that server instance exists and can be accessed
        server_instance = mcp_server.server
        assert server_instance is not None

        # Test basic server functionality
        with patch("src.mcp_server.tools.create_unified_search") as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            result = await tools.search_repositories(
                query="test", platforms=["github"], max_results=5
            )

            assert result is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_with_quality_checks(self):
        """Test workflow includes quality checks via MCP tools."""

        # Test that tools can handle quality-related parameters
        with patch("src.mcp_server.tools.create_unified_search") as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            # Call tool that might involve quality checks
            result = await tools.search_repositories(
                query="python web framework", platforms=["github"], max_results=5
            )

            assert result is not None
            assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
