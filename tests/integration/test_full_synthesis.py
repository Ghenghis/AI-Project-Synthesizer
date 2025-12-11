"""
Integration Tests for AI Project Synthesizer

These tests verify that all components work together correctly.
They require network access and may take longer to run.

Run with: pytest tests/integration/ -v -m "not slow"
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

# Skip all tests if no GitHub token
pytestmark = pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set"
)


class TestFullSynthesisPipeline:
    """Test the complete synthesis pipeline."""
    
    @pytest.fixture
    def temp_output(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.mark.asyncio
    async def test_search_and_analyze(self):
        """Test searching and analyzing a repository."""
        from src.discovery.github_client import GitHubClient
        from src.analysis.dependency_analyzer import DependencyAnalyzer
        
        # Search for a simple, well-known repo
        client = GitHubClient()
        results = await client.search("requests", max_results=1)
        
        assert len(results.repositories) > 0
        repo = results.repositories[0]
        assert repo.name is not None
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_synthesis_workflow(self, temp_output):
        """Test complete synthesis from search to output."""
        from src.synthesis.project_builder import ProjectBuilder
        
        builder = ProjectBuilder()
        
        # Synthesize a simple project
        result = await builder.synthesize(
            repositories=["https://github.com/psf/requests"],
            project_name="test_synthesis",
            output_path=temp_output,
        )
        
        assert result.success
        assert (temp_output / "test_synthesis").exists()
        assert (temp_output / "test_synthesis" / "README.md").exists()


class TestMCPToolsIntegration:
    """Test MCP tools work correctly."""
    
    @pytest.mark.asyncio
    async def test_search_repositories_tool(self):
        """Test the search_repositories MCP tool."""
        from src.mcp_server.tools import search_repositories
        
        result = await search_repositories(
            query="python http client",
            platforms=["github"],
            max_results=5,
        )
        
        assert "repositories" in result
        assert len(result["repositories"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_repository_tool(self):
        """Test the analyze_repository MCP tool."""
        from src.mcp_server.tools import analyze_repository
        
        result = await analyze_repository(
            repo_url="https://github.com/psf/requests",
        )
        
        assert "languages" in result
        assert "dependencies" in result


class TestDependencyResolution:
    """Test dependency resolution integration."""
    
    @pytest.mark.asyncio
    async def test_resolve_multiple_requirements(self):
        """Test resolving dependencies from multiple sources."""
        from src.resolution.python_resolver import PythonResolver
        
        resolver = PythonResolver()
        
        # Simulate requirements from two repos
        requirements = [
            "requests>=2.28.0",
            "httpx>=0.24.0",
            "pydantic>=2.0.0",
        ]
        
        result = await resolver.resolve(requirements)
        
        assert result.success
        assert len(result.packages) > 0
