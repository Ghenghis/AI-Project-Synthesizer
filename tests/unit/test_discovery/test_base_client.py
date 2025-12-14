"""
Unit tests for discovery base client module.
"""

import pytest

from src.discovery.base_client import (
    AuthenticationError,
    DiscoveryError,
    FileContent,
    Platform,
    RateLimitError,
    RepositoryInfo,
    RepositoryNotFoundError,
    SearchResult,
)


class TestPlatform:
    """Test Platform enum."""

    def test_platform_values(self):
        """Should have all platform values."""
        assert Platform.GITHUB.value == "github"
        assert Platform.GITLAB.value == "gitlab"
        assert Platform.HUGGINGFACE.value == "huggingface"
        assert Platform.KAGGLE.value == "kaggle"
        assert Platform.ARXIV.value == "arxiv"

    def test_platform_is_string(self):
        """Platform should be usable as string."""
        assert str(Platform.GITHUB) == "Platform.GITHUB"


class TestRepositoryInfo:
    """Test RepositoryInfo dataclass."""

    def test_create_basic_repo_info(self):
        """Should create repository info with required fields."""
        info = RepositoryInfo(
            platform="github",
            id="123",
            url="https://github.com/user/test-repo",
            name="test-repo",
            full_name="user/test-repo",
        )
        assert info.name == "test-repo"
        assert info.full_name == "user/test-repo"
        assert info.platform == "github"

    def test_repo_info_with_optional_fields(self):
        """Should create repo info with optional fields."""
        info = RepositoryInfo(
            platform="github",
            id="123",
            url="https://github.com/user/test-repo",
            name="test-repo",
            full_name="user/test-repo",
            description="A test repository",
            stars=100,
            forks=50,
            language="Python",
        )
        assert info.stars == 100
        assert info.forks == 50
        assert info.language == "Python"
        assert info.description == "A test repository"

    def test_repo_info_defaults(self):
        """Should have correct defaults."""
        info = RepositoryInfo(
            platform="github",
            id="123",
            url="https://example.com",
            name="test",
            full_name="user/test",
        )
        assert info.stars == 0
        assert info.forks == 0
        assert info.description is None
        assert info.language is None

    def test_to_dict(self):
        """Should convert to dictionary."""
        info = RepositoryInfo(
            platform="github",
            id="123",
            url="https://example.com",
            name="test",
            full_name="user/test",
            stars=10,
        )
        d = info.to_dict()
        assert d["platform"] == "github"
        assert d["name"] == "test"
        assert d["stars"] == 10


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_create_search_result(self):
        """Should create search result."""
        repo = RepositoryInfo(
            platform="github",
            id="123",
            url="https://example.com",
            name="test",
            full_name="user/test",
        )
        result = SearchResult(
            query="test query",
            platform="github",
            total_count=1,
            repositories=[repo],
            search_time_ms=100,
        )
        assert len(result.repositories) == 1
        assert result.total_count == 1
        assert result.query == "test query"

    def test_empty_search_result(self):
        """Should create empty search result."""
        result = SearchResult(
            query="no results",
            platform="github",
            total_count=0,
            repositories=[],
            search_time_ms=50,
        )
        assert len(result.repositories) == 0
        assert result.total_count == 0

    def test_to_dict(self):
        """Should convert to dictionary."""
        result = SearchResult(
            query="test",
            platform="github",
            total_count=0,
            repositories=[],
            search_time_ms=10,
        )
        d = result.to_dict()
        assert d["query"] == "test"
        assert d["platform"] == "github"


class TestFileContent:
    """Test FileContent dataclass."""

    def test_create_file_content(self):
        """Should create file content."""
        content = FileContent(
            path="src/main.py", name="main.py", content=b"print('hello')", size=14
        )
        assert content.path == "src/main.py"
        assert content.name == "main.py"
        assert content.size == 14

    def test_default_encoding(self):
        """Should have utf-8 default encoding."""
        content = FileContent(path="test.py", name="test.py", content=b"", size=0)
        assert content.encoding == "utf-8"


class TestDiscoveryErrors:
    """Test discovery error classes."""

    def test_discovery_error(self):
        """Should create base discovery error."""
        error = DiscoveryError("Base error")
        assert "Base error" in str(error)

    def test_authentication_error(self):
        """Should create authentication error."""
        error = AuthenticationError("Invalid token")
        assert "Invalid token" in str(error)
        assert isinstance(error, DiscoveryError)

    def test_rate_limit_error(self):
        """Should create rate limit error."""
        error = RateLimitError("Rate limited")
        assert "Rate limited" in str(error)
        assert isinstance(error, DiscoveryError)

    def test_rate_limit_error_with_retry(self):
        """Should create rate limit error with retry_after."""
        error = RateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60

    def test_repository_not_found_error(self):
        """Should create not found error."""
        error = RepositoryNotFoundError("user/repo")
        assert "user/repo" in str(error)
        assert isinstance(error, DiscoveryError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
