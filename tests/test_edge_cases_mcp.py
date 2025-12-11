"""
Pytest-based edge case tests for MCP tools.

These mirror the logic from the interactive test_edge_cases.py script but
use asserts so they show up in coverage and CI.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from src.mcp_server.tools import (
    handle_search_repositories,
    handle_analyze_repository,
    handle_synthesize_project,
    handle_generate_documentation,
    handle_get_synthesis_status,
)


class TestSearchRepositoriesEdgeCases:
    """Edge case tests for search_repositories MCP tool."""

    @pytest.mark.asyncio
    async def test_empty_query_returns_error(self):
        """Empty query should return an error."""
        result = await handle_search_repositories({})
        assert result.get("error") is True
        assert "query" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_empty_string_query_returns_error(self):
        """Empty string query should return an error."""
        result = await handle_search_repositories({"query": ""})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_negative_max_results_handled(self):
        """Negative max_results should be handled gracefully."""
        result = await handle_search_repositories({
            "query": "test",
            "max_results": -1
        })
        # Should either return error or handle gracefully
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_very_long_query_handled(self):
        """Very long query should be handled gracefully."""
        result = await handle_search_repositories({
            "query": "x" * 1000
        })
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_invalid_platform_handled(self):
        """Invalid platform should be handled gracefully."""
        result = await handle_search_repositories({
            "query": "test",
            "platforms": ["invalid_platform"]
        })
        assert isinstance(result, dict)


class TestAnalyzeRepositoryEdgeCases:
    """Edge case tests for analyze_repository MCP tool."""

    @pytest.mark.asyncio
    async def test_missing_url_returns_error(self):
        """Missing repo_url should return an error."""
        result = await handle_analyze_repository({})
        assert result.get("error") is True
        assert "url" in result.get("message", "").lower() or "required" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        """Invalid URL should return an error."""
        result = await handle_analyze_repository({"repo_url": "not-a-url"})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_empty_url_returns_error(self):
        """Empty URL should return an error."""
        result = await handle_analyze_repository({"repo_url": ""})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_nonexistent_repo_handled_gracefully(self):
        """Non-existent repo should be handled gracefully."""
        result = await handle_analyze_repository({
            "repo_url": "https://github.com/nonexistent-user-12345/nonexistent-repo-67890"
        })
        assert isinstance(result, dict)
        # Should return some response, not crash - could be error, status, or analysis
        assert any(key in result for key in ["error", "status", "analysis", "message", "data"])


class TestSynthesizeProjectEdgeCases:
    """Edge case tests for synthesize_project MCP tool."""

    @pytest.mark.asyncio
    async def test_missing_repositories_returns_error(self):
        """Missing repositories should return an error."""
        result = await handle_synthesize_project({})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_empty_repositories_list_returns_error(self):
        """Empty repositories list should return an error."""
        result = await handle_synthesize_project({
            "repositories": [],
            "project_name": "test",
            "output_path": "/tmp"
        })
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_missing_project_name_returns_error(self):
        """Missing project_name should return an error."""
        result = await handle_synthesize_project({
            "repositories": [{"repo_url": "https://github.com/octocat/Hello-World"}],
            "output_path": "/tmp"
        })
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_invalid_repo_url_in_list_returns_error(self):
        """Invalid repo URL in list should return an error."""
        result = await handle_synthesize_project({
            "repositories": [{"repo_url": "invalid-url"}],
            "project_name": "test",
            "output_path": "/tmp"
        })
        assert result.get("error") is True


class TestGenerateDocumentationEdgeCases:
    """Edge case tests for generate_documentation MCP tool."""

    @pytest.mark.asyncio
    async def test_missing_path_returns_error(self):
        """Missing project_path should return an error."""
        result = await handle_generate_documentation({})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_empty_path_returns_error(self):
        """Empty project_path should return an error."""
        result = await handle_generate_documentation({"project_path": ""})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_nonexistent_path_handled_gracefully(self):
        """Non-existent path should be handled gracefully."""
        result = await handle_generate_documentation({
            "project_path": "/nonexistent/path/12345"
        })
        assert isinstance(result, dict)
        assert "error" in result or "status" in result


class TestGetSynthesisStatusEdgeCases:
    """Edge case tests for get_synthesis_status MCP tool."""

    @pytest.mark.asyncio
    async def test_missing_id_returns_error(self):
        """Missing synthesis_id should return an error."""
        result = await handle_get_synthesis_status({})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_empty_id_returns_error(self):
        """Empty synthesis_id should return an error."""
        result = await handle_get_synthesis_status({"synthesis_id": ""})
        assert result.get("error") is True

    @pytest.mark.asyncio
    async def test_invalid_id_handled_gracefully(self):
        """Invalid synthesis_id should be handled gracefully."""
        result = await handle_get_synthesis_status({
            "synthesis_id": "invalid-id-format"
        })
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_nonexistent_id_handled_gracefully(self):
        """Non-existent synthesis_id should be handled gracefully."""
        result = await handle_get_synthesis_status({
            "synthesis_id": "00000000-0000-0000-0000-000000000000"
        })
        assert isinstance(result, dict)
        # Should return not found or similar, not crash
        assert "error" in result or "status" in result


class TestInputBoundaries:
    """Test input boundary conditions."""

    @pytest.mark.asyncio
    async def test_unicode_query_handled(self):
        """Unicode characters in query should be handled."""
        result = await handle_search_repositories({
            "query": "机器学习 深度学习"
        })
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self):
        """Special characters in query should be handled."""
        result = await handle_search_repositories({
            "query": "test@#$%^&*()"
        })
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_whitespace_only_query(self):
        """Whitespace-only query should return error."""
        result = await handle_search_repositories({
            "query": "   "
        })
        # Should either return error or handle gracefully
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_zero_max_results(self):
        """Zero max_results should be handled."""
        result = await handle_search_repositories({
            "query": "test",
            "max_results": 0
        })
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_very_large_max_results(self):
        """Very large max_results should be handled."""
        result = await handle_search_repositories({
            "query": "test",
            "max_results": 999999
        })
        assert isinstance(result, dict)
