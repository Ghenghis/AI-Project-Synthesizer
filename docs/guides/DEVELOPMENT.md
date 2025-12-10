# 🛠️ Development Guide

> Complete guide for developing and contributing to AI Project Synthesizer

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Adding New Features](#adding-new-features)
5. [Testing Guidelines](#testing-guidelines)
6. [Debugging Tips](#debugging-tips)
7. [Common Tasks](#common-tasks)

---

## Environment Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| Git | 2.27+ | Version control |
| uv | Latest | Package management |
| Ollama | Latest | Local LLM |
| Docker | 24+ | Containerization (optional) |

### Quick Setup

```bash
# Clone repository
git clone https://github.com/yourusername/AI_Synthesizer.git
cd AI_Synthesizer

# Run setup script
# Windows:
.\scripts\setup.ps1 -Dev

# Linux/WSL:
chmod +x scripts/setup.sh
./scripts/setup.sh --dev
```

### Manual Setup

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # Linux
.\.venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Create directories
mkdir -p logs output temp .cache
```

### IDE Configuration

**VS Code / Windsurf settings.json:**

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  },
  "ruff.lint.args": ["--config=pyproject.toml"],
  "editor.rulers": [88]
}
```

---

## Project Structure

```
AI_Synthesizer/
├── src/                      # Source code
│   ├── core/                 # Core utilities
│   │   ├── config.py         # Configuration management
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── logging.py        # Logging setup
│   │
│   ├── discovery/            # Repository discovery
│   │   ├── base_client.py    # Abstract client interface
│   │   ├── github_client.py  # GitHub implementation
│   │   ├── huggingface_client.py
│   │   └── unified_search.py # Multi-platform search
│   │
│   ├── analysis/             # Code analysis
│   │   ├── ast_parser.py     # Tree-sitter parsing
│   │   ├── dependency_analyzer.py
│   │   └── quality_scorer.py
│   │
│   ├── resolution/           # Dependency resolution
│   │   ├── python_resolver.py
│   │   └── unified_resolver.py
│   │
│   ├── synthesis/            # Code synthesis
│   │   ├── project_builder.py
│   │   └── scaffolder.py
│   │
│   ├── generation/           # Doc generation
│   │   └── readme_generator.py
│   │
│   ├── mcp/                  # MCP server
│   │   ├── server.py         # Main entry point
│   │   └── tools.py          # Tool definitions
│   │
│   └── llm/                  # LLM orchestration
│       ├── ollama_client.py
│       └── router.py
│
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── conftest.py           # Pytest fixtures
│
├── docs/                     # Documentation
├── config/                   # Configuration files
├── scripts/                  # Automation scripts
└── docker/                   # Docker files
```

---

## Development Workflow

### Branch Strategy

```
main          # Production-ready code
  └── develop # Integration branch
        ├── feature/xyz    # New features
        ├── fix/xyz        # Bug fixes
        └── docs/xyz       # Documentation
```

### Creating a Feature

```bash
# Create feature branch
git checkout develop
git pull
git checkout -b feature/my-feature

# Make changes...

# Run tests
pytest tests/ -v

# Run linting
ruff check src/ --fix
ruff format src/

# Commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push -u origin feature/my-feature
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new platform client for GitLab
fix: resolve rate limiting issue in GitHub client
docs: update API reference with new tools
test: add tests for dependency resolver
refactor: simplify unified search logic
chore: update dependencies
```

---

## Adding New Features

### Adding a New Platform Client

1. **Create client file:**

```python
# src/discovery/gitlab_client.py

from src.discovery.base_client import PlatformClient, RepositoryInfo

class GitLabClient(PlatformClient):
    @property
    def platform_name(self) -> str:
        return "gitlab"
    
    async def search(self, query: str, ...) -> SearchResult:
        # Implementation
        pass
```

2. **Register in unified search:**

```python
# src/discovery/unified_search.py

def _init_clients(self):
    # ...existing code...
    
    # Add GitLab
    gitlab_token = self.settings.platforms.gitlab_token.get_secret_value()
    if gitlab_token:
        from src.discovery.gitlab_client import GitLabClient
        self.clients["gitlab"] = GitLabClient(token=gitlab_token)
```

3. **Add configuration:**

```python
# src/core/config.py

class PlatformSettings(BaseSettings):
    gitlab_token: SecretStr = Field(default=SecretStr(""))
    gitlab_url: str = Field(default="https://gitlab.com")
```

4. **Write tests:**

```python
# tests/unit/test_discovery/test_gitlab_client.py

class TestGitLabClient:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        # Test implementation
        pass
```

### Adding a New MCP Tool

1. **Define tool in server:**

```python
# src/mcp/server.py

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ...existing tools...
        Tool(
            name="my_new_tool",
            description="Description of tool",
            inputSchema={...}
        )
    ]
```

2. **Implement handler:**

```python
async def handle_my_new_tool(args: dict) -> dict:
    # Implementation
    return {"result": "..."}
```

3. **Add to dispatcher:**

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # ...
    elif name == "my_new_tool":
        result = await handle_my_new_tool(arguments)
```

---

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_discovery/test_github_client.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Only unit tests
pytest tests/unit/ -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

### Writing Tests

```python
# tests/unit/test_discovery/test_github_client.py

import pytest
from unittest.mock import AsyncMock, patch

class TestGitHubClient:
    """Test suite for GitHubClient."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return GitHubClient(token="test_token")
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock API response."""
        return {
            "items": [{"id": 1, "name": "test"}],
            "total_count": 1
        }
    
    @pytest.mark.asyncio
    async def test_search_success(self, client, mock_api_response):
        """Test successful search."""
        with patch.object(client, "_api") as mock:
            mock.search.repos.return_value = mock_api_response
            
            result = await client.search("test query")
            
            assert len(result.repositories) == 1
            assert result.platform == "github"
    
    @pytest.mark.asyncio
    async def test_search_rate_limited(self, client):
        """Test rate limit handling."""
        with patch.object(client, "_api") as mock:
            mock.search.repos.side_effect = Exception("403 rate limit")
            
            with pytest.raises(RateLimitError):
                await client.search("test")
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In .env
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.getLogger("src").setLevel(logging.DEBUG)
```

### Debug MCP Server

```bash
# Run with debug flag
python -m src.mcp.server --debug

# Or set environment variable
DEBUG=true python -m src.mcp.server
```

### Test LLM Connection

```python
# Quick test script
import asyncio
from src.llm.ollama_client import OllamaClient

async def test():
    client = OllamaClient()
    response = await client.complete("Hello, world!")
    print(response)

asyncio.run(test())
```

---

## Common Tasks

### Update Dependencies

```bash
# Update requirements
uv pip compile requirements.in -o requirements.txt

# Upgrade all
uv pip install -U -r requirements.txt
```

### Generate Documentation

```bash
# Build docs
mkdocs build

# Serve locally
mkdocs serve
```

### Run Security Scan

```bash
# Bandit security scan
bandit -r src/ -c pyproject.toml

# Check dependencies
pip-audit
```

### Clean Up

```bash
# Remove caches
rm -rf .cache __pycache__ .pytest_cache .mypy_cache .ruff_cache

# Remove build artifacts
rm -rf dist build *.egg-info
```

---

## Getting Help

- **GitHub Issues:** Report bugs and request features
- **Discussions:** Ask questions and share ideas
- **Documentation:** Check `/docs` folder

Happy coding! 🚀
