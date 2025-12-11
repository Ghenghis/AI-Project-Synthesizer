"""
AI Project Synthesizer - GitHub Client Tests

Unit tests for the GitHub API client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.discovery.github_client import GitHubClient
from src.discovery.base_client import (
    RepositoryInfo,
    SearchResult,
    RateLimitError,
    AuthenticationError,
    RepositoryNotFoundError,
)


class TestGitHubClient:
    """Test suite for GitHubClient."""
    
    @pytest.fixture
    def client(self):
        """Create test client instance."""
        with patch("src.discovery.github_client.GitHubClient._init_api"):
            client = GitHubClient(token="test_token")
            client._api = MagicMock()
            return client
    
    # ========================================
    # Initialization Tests
    # ========================================
    
    def test_platform_name(self, client):
        """Test platform name property."""
        assert client.platform_name == "github"
    
    def test_is_authenticated_with_token(self, client):
        """Test authentication status with token."""
        assert client.is_authenticated is True
    
    def test_is_authenticated_without_token(self):
        """Test authentication status without token."""
        with patch("src.discovery.github_client.GitHubClient._init_api"):
            client = GitHubClient(token=None)
            assert client.is_authenticated is False
    
    # ========================================
    # Search Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_search_returns_results(self, client, mock_github_response):
        """Test that search returns properly formatted results."""
        client._api.search.repos.return_value = mock_github_response
        
        result = await client.search("machine learning python")
        
        assert isinstance(result, SearchResult)
        assert result.platform == "github"
        assert len(result.repositories) == 1
        assert result.repositories[0].name == "test-repo"
    
    @pytest.mark.asyncio
    async def test_search_with_language_filter(self, client, mock_github_response):
        """Test search with language filter."""
        client._api.search.repos.return_value = mock_github_response
        
        await client.search("test", language="python")
        
        # Verify query includes language
        call_args = client._api.search.repos.call_args
        assert "language:python" in call_args.kwargs["q"]
    
    @pytest.mark.asyncio
    async def test_search_with_min_stars(self, client, mock_github_response):
        """Test search with minimum stars filter."""
        client._api.search.repos.return_value = mock_github_response
        
        await client.search("test", min_stars=100)
        
        call_args = client._api.search.repos.call_args
        assert "stars:>=100" in call_args.kwargs["q"]
    
    @pytest.mark.asyncio
    async def test_search_handles_rate_limit(self, client):
        """Test that rate limit errors are handled properly."""
        client._api.search.repos.side_effect = Exception("403 rate limit exceeded")
        
        with pytest.raises(RateLimitError):
            await client.search("test")
    
    @pytest.mark.asyncio
    async def test_search_handles_auth_error(self, client):
        """Test that authentication errors are handled properly."""
        client._api.search.repos.side_effect = Exception("401 authentication failed")
        
        with pytest.raises(AuthenticationError):
            await client.search("test")
    
    # ========================================
    # Repository Info Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_get_repository_success(self, client):
        """Test getting repository information."""
        mock_repo = MagicMock()
        mock_repo.id = 123
        mock_repo.name = "test-repo"
        mock_repo.full_name = "owner/test-repo"
        mock_repo.html_url = "https://github.com/owner/test-repo"
        mock_repo.description = "Test"
        mock_repo.stargazers_count = 100
        mock_repo.forks_count = 10
        mock_repo.watchers_count = 50
        mock_repo.open_issues_count = 5
        mock_repo.language = "Python"
        mock_repo.license = MagicMock(spdx_id="MIT")
        mock_repo.created_at = "2024-01-01T00:00:00Z"
        mock_repo.updated_at = "2024-01-01T00:00:00Z"
        mock_repo.pushed_at = "2024-01-01T00:00:00Z"
        mock_repo.topics = ["python"]
        mock_repo.default_branch = "main"
        mock_repo.size = 1000
        mock_repo.owner = MagicMock(login="owner")
        
        client._api.repos.get.return_value = mock_repo
        
        result = await client.get_repository("owner/test-repo")
        
        assert isinstance(result, RepositoryInfo)
        assert result.full_name == "owner/test-repo"
        assert result.stars == 100
    
    @pytest.mark.asyncio
    async def test_get_repository_not_found(self, client):
        """Test handling of non-existent repository."""
        client._api.repos.get.side_effect = Exception("404 Not Found")
        
        with pytest.raises(RepositoryNotFoundError):
            await client.get_repository("owner/nonexistent")
    
    # ========================================
    # Contents Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_get_contents_directory(self, client):
        """Test getting directory contents."""
        mock_src = MagicMock()
        mock_src.name = "src"
        mock_src.path = "src"
        mock_src.sha = "abc"
        mock_src.type = "dir"
        mock_src.size = 0
        
        mock_readme = MagicMock()
        mock_readme.name = "README.md"
        mock_readme.path = "README.md"
        mock_readme.sha = "def"
        mock_readme.type = "file"
        mock_readme.size = 100
        
        mock_contents = [mock_src, mock_readme]
        client._api.repos.get_content.return_value = mock_contents
        
        result = await client.get_contents("owner/repo", "")
        
        assert len(result.directories) == 1
        assert len(result.files) == 1
        assert result.directories[0]["name"] == "src"
        assert result.files[0]["name"] == "README.md"
    
    # ========================================
    # Clone Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_clone_constructs_correct_url(self, client, tmp_path):
        """Test that clone URL is constructed correctly."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            
            await client.clone("owner/repo", tmp_path / "repo")
            
            # Verify git clone was called with correct URL
            call_args = mock_exec.call_args[0]
            assert "git" in call_args
            assert "clone" in call_args
    
    # ========================================
    # Helper Method Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_check_has_tests_true(self, client):
        """Test detection of tests directory."""
        mock_contents = MagicMock()
        mock_contents.directories = [{"name": "tests"}, {"name": "src"}]
        mock_contents.files = []
        
        with patch.object(client, "get_contents", return_value=mock_contents):
            result = await client.check_has_tests("owner/repo")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_has_tests_false(self, client):
        """Test when no tests directory exists."""
        mock_contents = MagicMock()
        mock_contents.directories = [{"name": "src"}]
        mock_contents.files = []
        
        with patch.object(client, "get_contents", return_value=mock_contents):
            result = await client.check_has_tests("owner/repo")
            assert result is False


class TestRepositoryInfoConversion:
    """Test RepositoryInfo data model."""
    
    def test_to_dict(self, mock_repository_info):
        """Test conversion to dictionary."""
        result = mock_repository_info.to_dict()
        
        assert result["platform"] == "github"
        assert result["name"] == "test-repo"
        assert result["stars"] == 1000
        assert "url" in result
    
    def test_default_values(self):
        """Test default values for optional fields."""
        repo = RepositoryInfo(
            platform="github",
            id="1",
            url="https://example.com",
            name="test",
            full_name="owner/test",
        )
        
        assert repo.stars == 0
        assert repo.topics == []
        assert repo.has_tests is False
