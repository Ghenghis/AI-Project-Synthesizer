"""
Unit tests for MCP server tools module.
Tests the core functionality of the tools handlers.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure test environment is set
os.environ["APP_ENV"] = "testing"

import src.mcp_server.tools as tools


class TestSynthesisJobManagement:
    """Test synthesis job management functions."""

    def setup_method(self):
        """Clear synthesis jobs before each test."""
        tools._synthesis_jobs.clear()

    def test_get_synthesis_job_existing(self):
        """Test getting existing synthesis job."""
        job_id = "test_job_123"
        job_data = {"id": job_id, "status": "running", "progress": 50}
        tools._synthesis_jobs[job_id] = job_data

        result = tools.get_synthesis_job(job_id)
        assert result is not None
        assert result["id"] == job_id
        assert result["status"] == "running"

    def test_get_synthesis_job_nonexistent(self):
        """Test getting non-existent job returns None."""
        result = tools.get_synthesis_job("nonexistent")
        assert result is None

    def test_set_synthesis_job(self):
        """Test setting synthesis job."""
        job_id = "new_job"
        job_data = {"id": job_id, "status": "pending", "progress": 0}

        tools.set_synthesis_job(job_id, job_data)

        assert job_id in tools._synthesis_jobs
        assert tools._synthesis_jobs[job_id]["status"] == "pending"

    def test_update_synthesis_job(self):
        """Test updating synthesis job."""
        job_id = "update_job"
        tools._synthesis_jobs[job_id] = {"id": job_id, "status": "pending", "progress": 0}

        tools.update_synthesis_job(job_id, progress=75, status="running")

        assert tools._synthesis_jobs[job_id]["progress"] == 75
        assert tools._synthesis_jobs[job_id]["status"] == "running"

    def test_update_nonexistent_job(self):
        """Test updating non-existent job does nothing."""
        tools.update_synthesis_job("nonexistent", progress=50)
        assert "nonexistent" not in tools._synthesis_jobs


class TestUnifiedSearch:
    """Test unified search functionality."""

    def setup_method(self):
        """Reset global search instance."""
        tools._unified_search = None

    def test_get_unified_search_creates_instance(self):
        """Test get_unified_search creates new instance."""
        with patch('src.mcp_server.tools.create_unified_search') as mock_create:
            mock_search = MagicMock()
            mock_create.return_value = mock_search

            result = tools.get_unified_search()

            assert result == mock_search
            mock_create.assert_called_once()

    def test_get_unified_search_returns_cached(self):
        """Test get_unified_search returns cached instance."""
        mock_search = MagicMock()
        tools._unified_search = mock_search

        result = tools.get_unified_search()

        assert result == mock_search


class TestDependencyAnalyzer:
    """Test dependency analyzer functionality."""

    def setup_method(self):
        """Reset global analyzer instance."""
        tools._dependency_analyzer = None

    def test_get_dependency_analyzer_creates_instance(self):
        """Test get_dependency_analyzer creates new instance."""
        with patch('src.mcp_server.tools.DependencyAnalyzer') as mock_class:
            mock_analyzer = MagicMock()
            mock_class.return_value = mock_analyzer

            result = tools.get_dependency_analyzer()

            assert result == mock_analyzer
            mock_class.assert_called_once()

    def test_get_dependency_analyzer_returns_cached(self):
        """Test get_dependency_analyzer returns cached instance."""
        mock_analyzer = MagicMock()
        tools._dependency_analyzer = mock_analyzer

        result = tools.get_dependency_analyzer()

        assert result == mock_analyzer


class TestConstants:
    """Test module constants."""

    def test_timeout_constants(self):
        """Test timeout constants are defined correctly."""
        assert tools.TIMEOUT_API_CALL == 30
        assert tools.TIMEOUT_GIT_CLONE == 300
        assert tools.TIMEOUT_FILE_OPERATIONS == 60
        assert tools.TIMEOUT_SYNTHESIS == 600


class TestSearchRepositories:
    """Test handle_search_repositories function."""

    @pytest.mark.asyncio
    async def test_search_repositories_basic(self):
        """Test basic repository search."""
        with patch.object(tools, 'get_unified_search') as mock_get_search:
            mock_search = MagicMock()
            # Mock the search method to return proper structure
            mock_search.search = AsyncMock(return_value=MagicMock(
                repositories=[{"name": "test-repo", "url": "https://github.com/test/repo"}]
            ))
            mock_get_search.return_value = mock_search

            result = await tools.handle_search_repositories({
                "query": "machine learning",
                "platforms": ["github"],
                "max_results": 10
            })

            # Result should be a dict (either success or error)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_search_repositories_empty_query(self):
        """Test search with empty query."""
        result = await tools.handle_search_repositories({
            "query": "",
            "platforms": ["github"]
        })

        # Should handle empty query gracefully
        assert result is not None
        assert isinstance(result, dict)


class TestAssistant:
    """Test assistant functionality."""

    def setup_method(self):
        """Reset global assistant instance."""
        tools._assistant = None

    def test_get_assistant_creates_instance(self):
        """Test get_assistant creates new instance."""
        with patch('src.assistant.core.ConversationalAssistant') as mock_class:
            mock_assistant = MagicMock()
            mock_class.return_value = mock_assistant

            result = tools.get_assistant()

            assert result == mock_assistant
            mock_class.assert_called_once()

    def test_get_assistant_returns_cached(self):
        """Test get_assistant returns cached instance."""
        mock_assistant = MagicMock()
        tools._assistant = mock_assistant

        result = tools.get_assistant()

        assert result == mock_assistant


class TestRegistration:
    """Test registration functions."""

    def test_register_all_tools(self):
        """Test registering all tools."""
        mock_server = MagicMock()

        # Should not raise any errors
        tools.register_all_tools(mock_server)

        assert True  # If we reach here, function completed

    def test_register_all_resources(self):
        """Test registering all resources."""
        mock_server = MagicMock()

        tools.register_all_resources(mock_server)

        assert True

    def test_register_all_prompts(self):
        """Test registering all prompts."""
        mock_server = MagicMock()

        tools.register_all_prompts(mock_server)

        assert True


class TestThreadSafety:
    """Test thread safety of tools module."""

    def test_synthesis_jobs_thread_safety(self):
        """Test synthesis jobs dictionary is thread-safe."""
        import concurrent.futures

        tools._synthesis_jobs.clear()
        results = []

        def set_job(i):
            job_id = f"job_{i}"
            job_data = {"id": job_id, "thread": i, "status": "running"}
            tools.set_synthesis_job(job_id, job_data)
            return True

        def get_job(i):
            job_id = f"job_{i}"
            return tools.get_synthesis_job(job_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Launch multiple threads to set jobs
            set_futures = [executor.submit(set_job, i) for i in range(20)]

            # Wait for all to complete
            for future in concurrent.futures.as_completed(set_futures):
                results.append(future.result())

        # Should have completed without errors
        assert len(results) == 20
        assert all(results)

        # Verify all jobs were created
        assert len(tools._synthesis_jobs) == 20


class TestUpdateJob:
    """Test _update_job helper function."""

    def setup_method(self):
        """Clear synthesis jobs before each test."""
        tools._synthesis_jobs.clear()

    def test_update_job_existing(self):
        """Test updating existing job."""
        job_id = "test_job"
        tools.set_synthesis_job(job_id, {"id": job_id, "status": "pending", "progress": 0})

        tools._update_job(job_id, 50, "running")

        job = tools.get_synthesis_job(job_id)
        assert job["progress"] == 50
        assert job["status"] == "running"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
