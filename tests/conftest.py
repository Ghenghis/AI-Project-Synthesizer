"""
AI Project Synthesizer - Test Configuration

Pytest fixtures and configuration for all test suites.
"""

import os
import sys
from pathlib import Path

# Set environment variables BEFORE any other imports
# This must happen before any src modules are imported
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("GITHUB_TOKEN", "test_github_token")
os.environ.setdefault("CACHE_ENABLED", "false")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Now import other modules
import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest


# ============================================
# Async Configuration
# ============================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================
# Environment Fixtures
# ============================================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GITHUB_TOKEN", "test_github_token")
    monkeypatch.setenv("CACHE_ENABLED", "false")


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide temporary directory for tests."""
    return tmp_path


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Provide output directory for tests."""
    output = tmp_path / "output"
    output.mkdir()
    return output


# ============================================
# Mock Fixtures - Discovery
# ============================================

@pytest.fixture
def mock_github_response():
    """Mock GitHub API search response that supports both dict and attribute access."""
    class MockRepo:
        def __init__(self):
            self.id = 123456
            self.name = "test-repo"
            self.full_name = "owner/test-repo"
            self.html_url = "https://github.com/owner/test-repo"
            self.description = "A test repository"
            self.stargazers_count = 1000
            self.forks_count = 100
            self.watchers_count = 50
            self.open_issues_count = 10
            self.language = "Python"
            self.license = MagicMock(spdx_id="MIT")
            self.created_at = "2023-01-01T00:00:00Z"
            self.updated_at = "2024-01-01T00:00:00Z"
            self.pushed_at = "2024-01-01T00:00:00Z"
            self.topics = ["python", "ml", "ai"]
            self.default_branch = "main"
            self.size = 5000
            self.owner = MagicMock(login="owner")

        def __getitem__(self, key):
            return getattr(self, key)

        def get(self, key, default=None):
            return getattr(self, key, default)

    class MockSearchResult:
        """Mock that supports both dict-style and attribute access like ghapi."""
        def __init__(self):
            self.items = [MockRepo()]
            self.total_count = 1

        def __getitem__(self, key):
            return getattr(self, key)

        def get(self, key, default=None):
            return getattr(self, key, default)

    return MockSearchResult()


@pytest.fixture
def mock_github_client(mock_github_response):
    """Mock GitHub client."""
    from src.discovery.github_client import GitHubClient

    client = GitHubClient(token="test_token")
    client._api = MagicMock()
    client._api.search.repos.return_value = mock_github_response
    return client


@pytest.fixture
def mock_repository_info():
    """Mock RepositoryInfo object."""
    from src.discovery.base_client import RepositoryInfo

    return RepositoryInfo(
        platform="github",
        id="123456",
        url="https://github.com/owner/test-repo",
        name="test-repo",
        full_name="owner/test-repo",
        description="A test repository for unit testing",
        owner="owner",
        stars=1000,
        forks=100,
        watchers=50,
        open_issues=10,
        language="Python",
        license="MIT",
        created_at="2023-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        pushed_at="2024-01-01T00:00:00Z",
        topics=["python", "testing"],
        default_branch="main",
        has_readme=True,
        has_tests=True,
    )


# ============================================
# Mock Fixtures - Analysis
# ============================================

@pytest.fixture
def sample_python_code():
    """Sample Python code for AST testing."""
    return '''
"""Sample module docstring."""

import os
from typing import List, Optional

class SampleClass:
    """A sample class."""

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"


def sample_function(items: List[str]) -> int:
    """Count items."""
    return len(items)


async def async_function() -> None:
    """Async function example."""
    pass
'''


@pytest.fixture
def sample_requirements():
    """Sample requirements.txt content."""
    return """
# Core dependencies
fastapi>=0.100.0
pydantic>=2.0.0
httpx>=0.24.0

# Development
pytest>=7.0.0
black>=23.0.0
"""


@pytest.fixture
def sample_pyproject():
    """Sample pyproject.toml content."""
    return """
[project]
name = "sample-project"
version = "1.0.0"
dependencies = [
    "fastapi>=0.100.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
]
"""


# ============================================
# Mock Fixtures - LLM
# ============================================

@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client."""
    client = AsyncMock()
    client.generate.return_value = {
        "response": "This is a mock LLM response.",
        "done": True,
    }
    return client


@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response."""
    return "This is a mock response from the language model."


# ============================================
# Integration Test Fixtures
# ============================================

@pytest.fixture
def sample_repo_structure(tmp_path: Path) -> Path:
    """Create sample repository structure for testing."""
    repo = tmp_path / "sample-repo"
    repo.mkdir()

    # Create directories
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "docs").mkdir()

    # Create files
    (repo / "README.md").write_text("# Sample Repository\n\nA test repository.")
    (repo / "requirements.txt").write_text("fastapi>=0.100.0\npydantic>=2.0.0\n")
    (repo / "pyproject.toml").write_text('[project]\nname = "sample"\nversion = "1.0.0"\n')
    (repo / "src" / "__init__.py").write_text("")
    (repo / "src" / "main.py").write_text('def main():\n    print("Hello")\n')
    (repo / "tests" / "__init__.py").write_text("")
    (repo / "tests" / "test_main.py").write_text('def test_main():\n    assert True\n')

    return repo


# ============================================
# Markers
# ============================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "e2e: marks end-to-end tests")
    config.addinivalue_line("markers", "requires_gpu: requires GPU")
    config.addinivalue_line("markers", "requires_ollama: requires Ollama")
