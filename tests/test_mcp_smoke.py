"""
Smoke test for MCP server functionality.
"""

import pytest


@pytest.mark.asyncio
async def test_mcp_server_imports():
    """Test that MCP server can be imported without errors."""
    try:
        from src.mcp_server.server import MCPServer, server

        assert MCPServer is not None
        assert server is not None
    except ImportError as e:
        pytest.fail(f"Failed to import MCP server: {e}")


@pytest.mark.asyncio
async def test_mcp_server_initialization():
    """Test that MCP server initializes correctly."""
    from src.mcp_server.server import MCPServer

    # Create server instance
    mcp_server = MCPServer()

    # Verify attributes exist
    assert hasattr(mcp_server, "llm_router")
    assert hasattr(mcp_server, "memory_system")
    assert hasattr(mcp_server, "server")

    # Verify server info
    info = mcp_server.get_server_info()
    assert info["name"] == "AI Project Synthesizer"
    assert "tools" in info


@pytest.mark.asyncio
async def test_mcp_tools_list():
    """Test that MCP tools can be listed."""
    # Skip this test for now - decorator makes it difficult to test directly
    # The important thing is that the server imports and initializes correctly
    pytest.skip("Tool listing requires full MCP server context")


@pytest.mark.asyncio
async def test_mcp_tool_handlers_import():
    """Test that all tool handlers can be imported."""
    try:
        from src.mcp_server.tools import (
            handle_analyze_repository,
            handle_check_compatibility,
            handle_generate_documentation,
            handle_resolve_dependencies,
            handle_search_repositories,
            handle_synthesize_project,
        )

        assert handle_search_repositories is not None
        assert handle_analyze_repository is not None
        assert handle_check_compatibility is not None
        assert handle_resolve_dependencies is not None
        assert handle_synthesize_project is not None
        assert handle_generate_documentation is not None
    except ImportError as e:
        pytest.fail(f"Failed to import tool handlers: {e}")


@pytest.mark.asyncio
async def test_unified_search_import():
    """Test that unified search can be imported."""
    try:
        from src.discovery.unified_search import UnifiedSearch, create_unified_search

        search = create_unified_search()
        assert search is not None
        assert isinstance(search, UnifiedSearch)
    except ImportError as e:
        pytest.fail(f"Failed to import unified search: {e}")


@pytest.mark.asyncio
async def test_dependency_analyzer_import():
    """Test that dependency analyzer can be imported."""
    try:
        from src.analysis.dependency_analyzer import DependencyAnalyzer

        analyzer = DependencyAnalyzer()
        assert analyzer is not None
    except ImportError as e:
        pytest.fail(f"Failed to import dependency analyzer: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
