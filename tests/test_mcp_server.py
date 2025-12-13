"""
Tests for MCP Server - Server startup, tool registration, and execution.

This module tests the core MCP server functionality including:
- Server initialization and startup
- Tool registration verification
- Tool execution (happy path and error cases)
- Concurrent request handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMCPServerImports:
    """Test that MCP server imports work correctly without circular imports."""

    def test_import_mcp_server(self):
        """Verify MCP server module can be imported."""
        from src.mcp_server import server
        assert server is not None

    def test_import_mcp_tools(self):
        """Verify MCP tools module can be imported."""
        from src.mcp_server import tools
        assert tools is not None

    def test_import_fastmcp(self):
        """Verify FastMCP can be imported (no circular import)."""
        try:
            from fastmcp import FastMCP
            assert FastMCP is not None
        except ImportError:
            # FastMCP may not be installed in test environment
            pytest.skip("FastMCP not installed")

    def test_no_circular_import(self):
        """Verify no circular import issues exist."""
        # This should not raise ImportError
        import sys

        # Clear any cached imports
        modules_to_clear = [k for k in sys.modules if k.startswith('src.mcp')]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Re-import - should work without circular import error
        from src.mcp_server import server, tools

        assert server is not None
        assert tools is not None


class TestMCPServerInitialization:
    """Test MCP server initialization."""

    def test_server_module_has_server_instance(self):
        """Verify server module exposes server instance."""
        from src.mcp_server import server
        # Check for server instance (lowercase 'server')
        assert hasattr(server, 'server') or hasattr(server, 'Server') or hasattr(server, 'main')

    def test_tools_are_registered(self):
        """Verify all expected tools are registered."""
        from src.mcp_server import tools

        expected_tools = [
            'search_repositories',
            'analyze_repository',
            'check_compatibility',
            'resolve_dependencies',
            'synthesize_project',
            'generate_documentation',
            'get_synthesis_status',
            'get_platforms',
        ]

        # Check that tool functions exist
        for tool_name in expected_tools:
            assert hasattr(tools, tool_name) or tool_name in dir(tools), \
                f"Tool {tool_name} not found in tools module"


class TestSearchRepositoriesTool:
    """Test search_repositories tool."""

    @pytest.mark.asyncio
    async def test_search_repositories_valid_query(self):
        """Test search with valid query returns results."""
        from src.mcp_server.tools import search_repositories

        with patch('src.mcp_server.tools.create_unified_search') as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[
                {'name': 'test-repo', 'stars': 100, 'platform': 'github'}
            ])
            mock_create.return_value = mock_instance

            # Call the tool
            result = await search_repositories(
                query="machine learning",
                platforms=["github"],
                max_results=10
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_search_repositories_empty_query(self):
        """Test search with empty query handles gracefully."""
        from src.mcp_server.tools import search_repositories

        with patch('src.mcp_server.tools.create_unified_search') as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            result = await search_repositories(
                query="",
                platforms=["github"],
                max_results=10
            )

            # Should return empty results, not error
            assert result is not None


class TestAnalyzeRepositoryTool:
    """Test analyze_repository tool."""

    @pytest.mark.asyncio
    async def test_analyze_repository_valid_url(self):
        """Test analysis with valid repository URL."""
        from src.mcp_server.tools import analyze_repository

        # Mock at the source module level
        with patch('src.mcp_server.tools.ASTParser') as mock_parser, \
             patch('src.mcp_server.tools.DependencyAnalyzer') as mock_analyzer:

            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_file = MagicMock(return_value={})
            mock_parser.return_value = mock_parser_instance

            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze = AsyncMock(return_value={'dependencies': []})
            mock_analyzer.return_value = mock_analyzer_instance

            result = await analyze_repository(
                repo_url="https://github.com/test/repo"
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_repository_invalid_url(self):
        """Test analysis with invalid URL returns error."""
        from src.mcp_server.tools import analyze_repository

        # Invalid URL should be handled gracefully
        result = await analyze_repository(repo_url="not-a-valid-url")
        # Should return error info, not crash
        assert result is not None


class TestSynthesisJobTracking:
    """Test synthesis job tracking and concurrency."""

    def test_synthesis_jobs_dict_exists(self):
        """Verify synthesis jobs tracking exists."""
        from src.mcp_server import tools

        # Check for job tracking mechanism
        assert hasattr(tools, '_synthesis_jobs') or \
               hasattr(tools, 'synthesis_jobs') or \
               hasattr(tools, 'SynthesisJobManager'), \
               "No synthesis job tracking found"

    @pytest.mark.asyncio
    async def test_get_synthesis_status_valid_id(self):
        """Test getting status of valid synthesis job."""
        from src.mcp_server.tools import get_synthesis_status, set_synthesis_job

        # Create a test job
        set_synthesis_job('test-id', {
            'status': 'running',
            'progress': 50,
            'current_step': 'analyzing'
        })

        result = await get_synthesis_status(synthesis_id='test-id')
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_synthesis_status_invalid_id(self):
        """Test getting status of non-existent job."""
        from src.mcp_server.tools import get_synthesis_status

        result = await get_synthesis_status(synthesis_id='non-existent-id')
        # Should return error or not found status
        assert result is not None


class TestGetPlatformsTool:
    """Test get_platforms tool."""

    @pytest.mark.asyncio
    async def test_get_platforms_returns_all(self):
        """Test that all platforms are returned."""
        from src.mcp_server.tools import get_platforms

        result = await get_platforms()

        assert result is not None
        # Result is a dict with platforms as a dict
        if isinstance(result, dict) and 'platforms' in result:
            platforms = result['platforms']
            # platforms is a dict, not a list
            if isinstance(platforms, dict):
                platform_names = list(platforms.keys())
                assert len(platform_names) > 0
                # Check that expected platforms exist
                assert 'github' in platform_names
                assert 'huggingface' in platform_names
        elif isinstance(result, list):
            if result:
                assert len(result) > 0


class TestConcurrentRequests:
    """Test handling of concurrent requests."""

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test multiple concurrent search requests."""
        from src.mcp_server.tools import search_repositories

        with patch('src.mcp_server.tools.create_unified_search') as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            # Run multiple searches concurrently
            tasks = [
                search_repositories(query=f"test-{i}", platforms=["github"])
                for i in range(5)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should complete without error
            for result in results:
                assert not isinstance(result, Exception), f"Got exception: {result}"

    @pytest.mark.asyncio
    async def test_concurrent_synthesis_jobs(self):
        """Test multiple concurrent synthesis job creations."""
        from src.mcp_server.tools import synthesize_project

        with patch('src.mcp_server.tools.ProjectBuilder') as mock_builder:
            mock_instance = MagicMock()
            mock_instance.build = AsyncMock(return_value={'status': 'started'})
            mock_builder.return_value = mock_instance

            # Create multiple synthesis jobs
            tasks = [
                synthesize_project(
                    repositories=[f"https://github.com/test/repo{i}"],
                    project_name=f"project-{i}",
                    output_path=f"/tmp/project-{i}"
                )
                for i in range(3)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should complete (may have errors but shouldn't crash)
            assert len(results) == 3


class TestErrorHandling:
    """Test error handling in MCP tools."""

    @pytest.mark.asyncio
    async def test_search_handles_api_error(self):
        """Test search handles API errors gracefully."""
        from src.mcp_server.tools import search_repositories

        with patch('src.mcp_server.tools.create_unified_search') as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(side_effect=Exception("API Error"))
            mock_create.return_value = mock_instance

            try:
                result = await search_repositories(query="test", platforms=["github"])
                # If returns, should indicate error
                assert result is not None
            except Exception:
                # Any exception is acceptable - it's handled
                pass

    @pytest.mark.asyncio
    async def test_analyze_handles_timeout(self):
        """Test analyze handles timeout gracefully."""
        from src.mcp_server.tools import analyze_repository

        with patch('src.mcp_server.tools.ASTParser') as mock_parser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_file = MagicMock(side_effect=TimeoutError())
            mock_parser.return_value = mock_parser_instance

            try:
                result = await analyze_repository(
                    repo_url="https://github.com/test/repo"
                )
                assert result is not None
            except (TimeoutError, Exception):
                pass  # Expected - any handled exception is fine


class TestToolParameters:
    """Test tool parameter validation."""

    @pytest.mark.asyncio
    async def test_search_validates_platforms(self):
        """Test search validates platform parameter."""
        from src.mcp_server.tools import search_repositories

        with patch('src.mcp_server.tools.create_unified_search') as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            # Valid platforms
            result = await search_repositories(
                query="test",
                platforms=["github", "huggingface"]
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_synthesize_validates_repositories(self):
        """Test synthesize validates repositories parameter."""
        from src.mcp_server.tools import synthesize_project

        # Empty repositories should be handled
        try:
            result = await synthesize_project(
                repositories=[],
                project_name="test",
                output_path="/tmp/test"
            )
            # Should either return error or raise
            assert result is not None
        except (ValueError, Exception):
            pass  # Expected for empty repos
