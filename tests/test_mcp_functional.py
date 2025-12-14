"""
Functional test for MCP server tool responses.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_mcp_search_repositories_tool():
    """Test that search_repositories tool handler works."""
    from src.mcp_server.tools import handle_search_repositories

    # Mock dependencies
    with patch("src.mcp_server.tools.create_unified_search") as mock_search:
        mock_search_instance = AsyncMock()
        mock_search.return_value = mock_search_instance

        # Mock search results with proper objects
        mock_repo = MagicMock()
        mock_repo.name = "test-repo"
        mock_repo.full_name = "test/test-repo"
        mock_repo.url = "https://github.com/test/test-repo"
        mock_repo.description = "Test repository"
        mock_repo.stars = 100
        mock_repo.language = "Python"
        mock_repo.platform = "github"
        mock_repo.updated_at = "2024-01-01"

        mock_search_instance.search.return_value = MagicMock(
            repositories=[mock_repo], total_count=1, search_time_ms=100
        )

        # Call the handler
        result = await handle_search_repositories(
            {"query": "test repository", "platforms": ["github"], "max_results": 10}
        )

        # Verify response
        assert "repositories" in result
        assert result["success"] is True
        assert len(result["repositories"]) > 0
        assert result["repositories"][0]["name"] == "test-repo"


@pytest.mark.asyncio
async def test_mcp_analyze_repository_tool():
    """Test that analyze_repository tool handler works."""
    from src.mcp_server.tools import handle_analyze_repository

    # Mock dependencies
    with (
        patch("src.mcp_server.tools.DependencyAnalyzer") as mock_dep_analyzer,
        patch("src.mcp_server.tools.ASTParser") as mock_ast_parser,
        patch("src.mcp_server.tools.QualityScorer") as mock_quality_scorer,
    ):
        # Setup mocks
        mock_dep_analyzer.return_value.analyze.return_value = {
            "dependencies": {"requests": "2.28.0"},
            "issues": [],
        }

        mock_ast_parser.return_value.parse.return_value = {
            "functions": ["test_func"],
            "classes": ["TestClass"],
        }

        mock_quality_scorer.return_value.score.return_value = {
            "score": 85,
            "metrics": {},
        }

        # Call the handler
        result = await handle_analyze_repository(
            {
                "repo_url": "https://github.com/test/test-repo",
                "include_transitive_deps": True,
                "extract_components": True,
            }
        )

        # Verify response
        assert "summary" in result
        assert "dependencies" in result
        assert "structure" in result
        assert "quality" in result


@pytest.mark.asyncio
async def test_mcp_check_compatibility_tool():
    """Test that check_compatibility tool handler works."""
    from src.mcp_server.tools import handle_check_compatibility

    # Mock dependencies
    with patch("src.mcp_server.tools.CompatibilityChecker") as mock_checker:
        mock_checker_instance = MagicMock()
        mock_checker.return_value = mock_checker_instance

        # Mock compatibility results
        mock_checker_instance.check_compatibility.return_value = {
            "compatible": True,
            "conflicts": [],
            "warnings": [],
        }

        # Call the handler
        result = await handle_check_compatibility(
            {
                "repo_urls": [
                    "https://github.com/test/repo1",
                    "https://github.com/test/repo2",
                ],
                "target_python_version": "3.11",
            }
        )

        # Verify response
        assert "compatible" in result
        assert "conflicts" in result
        assert result["compatible"] is True


@pytest.mark.asyncio
async def test_mcp_server_can_start():
    """Test that MCP server can start without errors."""
    import sys
    from unittest.mock import AsyncMock, patch

    # Mock the stdio_server to avoid actually starting it
    with (
        patch("src.mcp_server.server.stdio_server") as mock_stdio,
        patch("src.mcp_server.server.server.run") as mock_run,
    ):
        mock_stdio.return_value.__aenter__.return_value = (None, None)
        mock_run = AsyncMock()

        # Import and try to run main (should not crash)
        from src.mcp_server.server import main

        # Run main with timeout to avoid hanging
        try:
            await asyncio.wait_for(main(), timeout=1.0)
        except TimeoutError:
            # Expected - we're mocking the server run
            pass
        except Exception as e:
            pytest.fail(f"Server failed to start: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
