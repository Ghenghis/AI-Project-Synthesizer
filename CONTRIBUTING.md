# Contributing to AI Project Synthesizer

First off, thank you for considering contributing! 🎉

This document provides guidelines for contributing to the AI Project Synthesizer project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Issue Guidelines](#issue-guidelines)

---

## Code of Conduct

We welcome contributions and aim to foster a positive, inclusive community. Please be respectful and constructive in all interactions.

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Git 2.27+**
- **uv** (recommended) or pip
- **Ollama** (for local LLM testing)
- **Docker** (optional, for integration tests)

### Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/AI_Synthesizer.git
cd AI_Synthesizer

# 2. Create virtual environment
uv venv
# OR: python -m venv .venv

# 3. Activate environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# 5. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 6. Run tests
pytest tests/ -v

# 7. Start development server
python -m src.mcp.server --debug
```

---

## Development Setup

### IDE Configuration

**VS Code / Windsurf:**

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Required Tools

```bash
# Install development tools
uv pip install black ruff mypy pytest pytest-asyncio pytest-cov

# Verify installation
black --version
ruff --version
mypy --version
pytest --version
```

### Pre-commit Hooks

```bash
# Install pre-commit
uv pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Project Structure

```
AI_Synthesizer/
├── src/
│   ├── core/           # Core utilities and config
│   ├── discovery/      # Platform API clients
│   ├── analysis/       # Code analysis (AST, deps)
│   ├── resolution/     # Dependency resolution
│   ├── synthesis/      # Code merging
│   ├── generation/     # Doc generation
│   ├── mcp/            # MCP server
│   └── llm/            # LLM orchestration
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
├── docs/               # Documentation
└── config/             # Configuration files
```

### Key Files to Understand

| File | Purpose |
|------|---------|
| `src/mcp/server.py` | MCP server entry point |
| `src/mcp/tools.py` | Tool definitions |
| `src/core/config.py` | Configuration management |
| `src/discovery/unified_search.py` | Multi-platform search |
| `src/analysis/ast_parser.py` | AST parsing with Tree-sitter |
| `src/resolution/python_resolver.py` | Dependency resolution |

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with these specifics:

- **Line length:** 88 characters (Black default)
- **Quotes:** Double quotes for strings
- **Imports:** Sorted with isort (via Ruff)
- **Type hints:** Required for all public functions
- **Docstrings:** Google style

### Example Code

```python
"""Module docstring explaining purpose."""

from typing import List, Optional
from dataclasses import dataclass

from src.core.exceptions import SynthesizerError


@dataclass
class ExampleConfig:
    """Configuration for example component.
    
    Attributes:
        name: Component name.
        enabled: Whether component is active.
        max_items: Maximum items to process.
    """
    name: str
    enabled: bool = True
    max_items: int = 100


async def process_items(
    items: List[str],
    config: Optional[ExampleConfig] = None
) -> dict:
    """Process a list of items.
    
    Args:
        items: Items to process.
        config: Optional configuration override.
        
    Returns:
        Dictionary with processing results.
        
    Raises:
        SynthesizerError: If processing fails.
    """
    config = config or ExampleConfig(name="default")
    
    results = []
    for item in items[:config.max_items]:
        processed = await _process_single(item)
        results.append(processed)
    
    return {
        "processed": len(results),
        "items": results
    }


async def _process_single(item: str) -> str:
    """Internal helper for single item processing."""
    return item.strip().lower()
```

### Linting Commands

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Type checking
mypy src/

# Run all checks
make lint  # If Makefile exists
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── unit/
│   ├── test_discovery/
│   │   ├── test_github_client.py
│   │   └── test_unified_search.py
│   ├── test_analysis/
│   │   └── test_ast_parser.py
│   └── test_resolution/
│       └── test_python_resolver.py
├── integration/
│   ├── test_full_synthesis.py
│   └── test_mcp_server.py
└── e2e/
    └── test_windsurf_integration.py
```

### Writing Tests

```python
"""Tests for GitHub client."""

import pytest
from unittest.mock import AsyncMock, patch

from src.discovery.github_client import GitHubClient


class TestGitHubClient:
    """Test suite for GitHubClient."""
    
    @pytest.fixture
    def client(self):
        """Create test client instance."""
        return GitHubClient(token="test_token")
    
    @pytest.mark.asyncio
    async def test_search_returns_results(self, client):
        """Test that search returns expected results."""
        with patch.object(client, "api") as mock_api:
            mock_api.search.repos.return_value = MockSearchResult()
            
            results = await client.search("test query")
            
            assert len(results) > 0
            assert results[0].platform == "github"
    
    @pytest.mark.asyncio
    async def test_search_handles_rate_limit(self, client):
        """Test graceful handling of rate limits."""
        with patch.object(client, "api") as mock_api:
            mock_api.search.repos.side_effect = RateLimitError()
            
            with pytest.raises(RateLimitError):
                await client.search("test query")


class MockSearchResult:
    """Mock search result for testing."""
    items = [
        MockRepo(id=1, name="test-repo", stargazers_count=100)
    ]
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_discovery/test_github_client.py -v

# Run tests matching pattern
pytest tests/ -k "test_search" -v

# Run only fast tests (no network)
pytest tests/ -m "not slow" -v
```

### Test Coverage Requirements

- **Minimum coverage:** 80%
- **New features:** Must include tests
- **Bug fixes:** Must include regression test

---

## Pull Request Process

### Before Submitting

1. **Create an issue first** for significant changes
2. **Fork the repository**
3. **Create a feature branch:** `git checkout -b feature/your-feature`
4. **Write tests** for new functionality
5. **Ensure all tests pass:** `pytest tests/`
6. **Run linting:** `ruff check src/`
7. **Update documentation** if needed

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue
Fixes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least one approval** required
3. **All conversations resolved**
4. **Squash and merge** preferred

---

## Issue Guidelines

### Bug Reports

Use this template:

```markdown
**Describe the bug**
Clear description of the issue.

**To Reproduce**
1. Step one
2. Step two
3. See error

**Expected behavior**
What should happen.

**Environment**
- OS: Windows 11
- Python: 3.11
- Version: 1.0.0

**Logs**
```
Paste relevant logs here
```
```

### Feature Requests

```markdown
**Is this related to a problem?**
Description of the problem.

**Proposed Solution**
How you'd like it to work.

**Alternatives Considered**
Other solutions you've thought about.

**Additional Context**
Any other information.
```

---

## Getting Help

- **Discord:** [Join our server](#)
- **Discussions:** Use GitHub Discussions
- **Email:** maintainers@example.com

---

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- CHANGELOG.md for their contributions
- Release notes

Thank you for contributing! 🙏
