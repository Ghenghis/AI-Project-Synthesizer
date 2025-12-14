"""
MCP Server Integration Tests

Tests that the MCP server starts correctly and responds to tool calls.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set"
)


class TestMCPServerStartup:
    """Test MCP server initialization."""

    def test_server_imports(self):
        """Test that server module imports correctly."""
        from src.mcp_server.tools import (
            handle_analyze_repository,
            handle_search_repositories,
            handle_synthesize_project,
        )

        assert handle_search_repositories is not None
        assert handle_analyze_repository is not None
        assert handle_synthesize_project is not None

    def test_tools_registered(self):
        """Test that all 7 tool handlers are available."""
        from src.mcp_server.tools import (
            handle_analyze_repository,
            handle_check_compatibility,
            handle_generate_documentation,
            handle_get_synthesis_status,
            handle_resolve_dependencies,
            handle_search_repositories,
            handle_synthesize_project,
        )

        # Verify all 7 handlers exist
        handlers = [
            handle_search_repositories,
            handle_analyze_repository,
            handle_check_compatibility,
            handle_resolve_dependencies,
            handle_synthesize_project,
            handle_generate_documentation,
            handle_get_synthesis_status,
        ]
        assert len(handlers) == 7
        assert all(callable(h) for h in handlers)


class TestMCPToolSchemas:
    """Test MCP tool input/output schemas."""

    def test_search_repositories_schema(self):
        """Verify search_repositories has correct schema."""
        # Check function signature
        import inspect

        from src.mcp_server.tools import search_repositories

        sig = inspect.signature(search_repositories)
        params = list(sig.parameters.keys())

        assert "query" in params
        assert "platforms" in params
        assert "max_results" in params

    def test_analyze_repository_schema(self):
        """Verify analyze_repository has correct schema."""
        import inspect

        from src.mcp_server.tools import analyze_repository

        sig = inspect.signature(analyze_repository)
        params = list(sig.parameters.keys())

        assert "repo_url" in params

    def test_synthesize_project_schema(self):
        """Verify synthesize_project has correct schema."""
        import inspect

        from src.mcp_server.tools import synthesize_project

        sig = inspect.signature(synthesize_project)
        params = list(sig.parameters.keys())

        assert "repositories" in params
        assert "project_name" in params


class TestMCPToolExecution:
    """Test actual tool execution."""

    @pytest.mark.asyncio
    async def test_search_returns_dict(self):
        """Test search returns properly structured dict."""
        from src.mcp_server.tools import search_repositories

        result = await search_repositories(
            query="fastapi",
            platforms=["github"],
            max_results=3,
        )

        assert isinstance(result, dict)
        # Result has "status" and "data" keys on success
        assert "status" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_platforms_tool(self):
        """Test get_platforms returns available platforms."""
        from src.mcp_server.tools import get_platforms

        result = await get_platforms()

        assert isinstance(result, dict)
        assert "platforms" in result
        assert "github" in result["platforms"]


class TestMCPErrorHandling:
    """Test error handling in MCP tools."""

    @pytest.mark.asyncio
    async def test_invalid_repo_url(self):
        """Test handling of invalid repository URL."""
        from src.mcp_server.tools import analyze_repository

        result = await analyze_repository(
            repo_url="not-a-valid-url",
        )

        # Should return error structure, not raise
        assert "error" in result or not result.get("success", True)

    @pytest.mark.asyncio
    async def test_empty_search_query(self):
        """Test handling of empty search query."""
        from src.mcp_server.tools import search_repositories

        result = await search_repositories(
            query="",
            platforms=["github"],
            max_results=5,
        )

        # Should handle gracefully
        assert isinstance(result, dict)
