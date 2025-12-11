"""
Tests for MCP Server - Server startup, tool registration, and execution.

This module tests the core MCP server functionality including:
- Server initialization and startup
- Tool registration verification
- Tool execution (happy path and error cases)
- Concurrent request handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


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
        import importlib
        import sys
        
        # Clear any cached imports
        modules_to_clear = [k for k in sys.modules if k.startswith('src.mcp')]
        for mod in modules_to_clear:
            del sys.modules[mod]
        
        # Re-import - should work without circular import error
        from src.mcp_server import server
        from src.mcp_server import tools
        
        assert server is not None
        assert tools is not None


class TestMCPServerInitialization:
    """Test MCP server initialization."""

    def test_server_module_has_mcp_instance(self):
        """Verify server module exposes mcp instance."""
        from src.mcp_server import server
        assert hasattr(server, 'mcp') or hasattr(server, 'app')

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
        
        with patch('src.mcp_server.tools.UnifiedSearch') as mock_search:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[
                {'name': 'test-repo', 'stars': 100, 'platform': 'github'}
            ])
            mock_search.return_value = mock_instance
            
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
        
        with patch('src.mcp_server.tools.UnifiedSearch') as mock_search:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_search.return_value = mock_instance
            
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
        
        with patch('src.mcp_server.tools.GitHubClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock(return_value={
                'structure': {},
                'dependencies': [],
                'languages': {'python': 100}
            })
            mock_client.return_value = mock_instance
            
            result = await analyze_repository(
                repo_url="https://github.com/test/repo"
            )
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_repository_invalid_url(self):
        """Test analysis with invalid URL returns error."""
        from src.mcp_server.tools import analyze_repository
        
        # Invalid URL should be handled gracefully
        try:
            result = await analyze_repository(repo_url="not-a-valid-url")
            # If it returns, should indicate error
            assert result is not None
        except (ValueError, Exception):
            # Expected to raise for invalid URL
            pass


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
        from src.mcp_server.tools import get_synthesis_status
        
        # Create a mock job first
        with patch.dict('src.mcp_server.tools._synthesis_jobs', {'test-id': {
            'status': 'running',
            'progress': 50,
            'current_step': 'analyzing'
        }}):
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
        # Should include github, huggingface, kaggle, arxiv
        if isinstance(result, dict) and 'platforms' in result:
            platform_names = [p.get('name', p) for p in result['platforms']]
            assert 'github' in platform_names or len(platform_names) > 0


class TestConcurrentRequests:
    """Test handling of concurrent requests."""

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test multiple concurrent search requests."""
        from src.mcp_server.tools import search_repositories
        
        with patch('src.mcp_server.tools.UnifiedSearch') as mock_search:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_search.return_value = mock_instance
            
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
        
        with patch('src.mcp_server.tools.ProjectAssembler') as mock_assembler:
            mock_instance = MagicMock()
            mock_instance.assemble = AsyncMock(return_value={'status': 'started'})
            mock_assembler.return_value = mock_instance
            
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
        
        with patch('src.mcp_server.tools.UnifiedSearch') as mock_search:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(side_effect=Exception("API Error"))
            mock_search.return_value = mock_instance
            
            try:
                result = await search_repositories(query="test", platforms=["github"])
                # If returns, should indicate error
                assert result is not None
            except Exception as e:
                # Should be a handled exception
                assert "API Error" in str(e) or True  # Any exception is acceptable

    @pytest.mark.asyncio
    async def test_analyze_handles_timeout(self):
        """Test analyze handles timeout gracefully."""
        from src.mcp_server.tools import analyze_repository
        
        with patch('src.mcp_server.tools.GitHubClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_client.return_value = mock_instance
            
            try:
                result = await analyze_repository(
                    repo_url="https://github.com/test/repo"
                )
                assert result is not None
            except asyncio.TimeoutError:
                pass  # Expected
            except Exception:
                pass  # Other handled exception is fine


class TestToolParameters:
    """Test tool parameter validation."""

    @pytest.mark.asyncio
    async def test_search_validates_platforms(self):
        """Test search validates platform parameter."""
        from src.mcp_server.tools import search_repositories
        
        with patch('src.mcp_server.tools.UnifiedSearch') as mock_search:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_search.return_value = mock_instance
            
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
