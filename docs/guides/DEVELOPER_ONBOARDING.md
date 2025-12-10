# 🚀 Developer Onboarding Guide

> **AI Project Synthesizer - Getting Started for Contributors**  
> **Version:** 1.0.0  
> **Last Updated:** December 2024

---

## Welcome, Developer! 👋

This guide will get you from zero to contributing in under 30 minutes. Whether you're fixing bugs, adding features, or improving documentation, this is your starting point.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment](#development-environment)
4. [Code Structure Walkthrough](#code-structure-walkthrough)
5. [Key Concepts](#key-concepts)
6. [Development Workflow](#development-workflow)
7. [Testing Guide](#testing-guide)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)
10. [Getting Help](#getting-help)

---

## Quick Start

### Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.11+ | `python --version` |
| Git | 2.27+ | `git --version` |
| Docker | 24+ | `docker --version` |
| Ollama | Latest | `ollama --version` |

### 5-Minute Setup

```powershell
# 1. Clone the repository
git clone https://github.com/your-org/AI_Synthesizer.git
cd AI_Synthesizer

# 2. Run the automated setup script
.\scripts\setup.ps1

# 3. Configure environment
copy .env.example .env
# Edit .env and add your GitHub token

# 4. Verify installation
python test_synthesis.py
# Expected: "🎉 All tests passed!"

# 5. Start the MCP server
python -m src.mcp.server
```

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP INTERFACE                            │
│            (src/mcp/server.py, src/mcp/tools.py)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐ │
│  │ DISCOVERY │  │ ANALYSIS  │  │RESOLUTION │  │SYNTHESIS │ │
│  │   Layer   │  │   Layer   │  │   Layer   │  │  Layer   │ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬─────┘ │
│        │              │              │              │        │
│  ┌─────▼─────────────▼──────────────▼──────────────▼─────┐ │
│  │                    CORE LAYER                          │ │
│  │        (config, logging, exceptions, utils)            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    LLM LAYER                            │ │
│  │            (Ollama local, Cloud fallback)               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Request → MCP Server → Discovery → Analysis → Resolution → Synthesis → Output
                                ↓           ↓           ↓
                            GitHub      AST Parse    SAT Solver
                            HuggingFace Dependencies  uv/pip
```



---

## Development Environment

### IDE Setup (VS Code / Windsurf)

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- Black Formatter
- Ruff
- GitLens
- Mermaid Preview

**Settings (`.vscode/settings.json`):**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.analysis.typeCheckingMode": "basic",
    "editor.formatOnSave": true,
    "python.formatting.provider": "black",
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (WSL/Linux)
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
GITHUB_TOKEN=ghp_your_token_here

# Optional - Local LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:14b

# Optional - Cloud Fallback
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional - Additional Platforms
HF_TOKEN=hf_...
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key

# Development
LOG_LEVEL=DEBUG
DEBUG=true
```

---

## Code Structure Walkthrough

### Directory Map

```
AI_Synthesizer/
│
├── src/                      # Source code
│   ├── core/                 # Foundational modules
│   │   ├── config.py         # Configuration management (YAML + env vars)
│   │   ├── logging.py        # Structured logging setup
│   │   └── exceptions.py     # Custom exception hierarchy
│   │
│   ├── discovery/            # Repository discovery
│   │   ├── base_client.py    # Abstract base class for all clients
│   │   ├── github_client.py  # ✅ Complete - GitHub API wrapper
│   │   ├── huggingface_client.py # ✅ Complete - HF Hub integration
│   │   └── unified_search.py # ✅ Complete - Cross-platform search
│   │
│   ├── analysis/             # Code analysis tools
│   │   ├── ast_parser.py     # 🔄 In Progress - Tree-sitter integration
│   │   ├── dependency_analyzer.py # ✅ Complete
│   │   ├── code_extractor.py # 🔄 In Progress - Component extraction
│   │   ├── quality_scorer.py # 🔄 In Progress
│   │   └── compatibility_checker.py # 🔄 In Progress
│   │
│   ├── resolution/           # Dependency resolution
│   │   ├── python_resolver.py # ✅ Complete - uv/pip SAT solver
│   │   ├── conflict_detector.py # 🔄 In Progress
│   │   └── unified_resolver.py # ✅ Complete
│   │
│   ├── synthesis/            # Project building
│   │   ├── project_builder.py # ✅ Complete - Main synthesis logic
│   │   └── scaffolder.py     # 🔄 In Progress - Template application
│   │
│   ├── generation/           # Documentation generation
│   │   ├── readme_generator.py # 🔄 In Progress
│   │   └── diagram_generator.py # 🔄 In Progress
│   │
│   ├── llm/                  # LLM integration
│   │   ├── ollama_client.py  # ✅ Complete - Local LLM
│   │   └── router.py         # 🔄 In Progress - RouteLLM
│   │
│   └── mcp/                  # MCP server
│       ├── server.py         # ✅ Complete - FastMCP server
│       └── tools.py          # ✅ Complete - 7 MCP tools
│
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
│
├── docs/                     # Documentation
│   ├── architecture/         # Architecture docs
│   ├── blueprints/           # Technical specs
│   ├── diagrams/             # Visual diagrams
│   └── guides/               # Developer guides
│
├── templates/                # Project templates
│   ├── documentation/        # Doc templates
│   └── project/              # Project scaffolds
│
├── config/                   # Configuration files
├── scripts/                  # Utility scripts
└── docker/                   # Docker configuration
```



### Key Files Explained

| File | Purpose | Status |
|------|---------|--------|
| `src/mcp/server.py` | FastMCP server entry point | ✅ Complete |
| `src/mcp/tools.py` | All 7 MCP tool implementations | ✅ Complete |
| `src/discovery/github_client.py` | GitHub API with rate limiting | ✅ Complete |
| `src/resolution/python_resolver.py` | SAT-based dependency solver | ✅ Complete |
| `src/synthesis/project_builder.py` | Core synthesis engine | ✅ Complete |
| `src/analysis/ast_parser.py` | Tree-sitter code parsing | 🔄 Needs Work |
| `src/generation/readme_generator.py` | AI README generation | 🔄 Needs Work |

---

## Key Concepts

### 1. MCP (Model Context Protocol)

The MCP is how Windsurf IDE communicates with our synthesizer:

```python
# Example MCP tool definition (src/mcp/tools.py)
@mcp.tool()
async def search_repositories(
    query: str,
    platforms: list[str] = ["github"],
    max_results: int = 20,
) -> dict:
    """Search for repositories across platforms."""
    search = UnifiedSearch()
    return await search.search(query, platforms=platforms, max_results=max_results)
```

### 2. Platform Clients

All platform clients inherit from `PlatformClient`:

```python
# Abstract base class
class PlatformClient(ABC):
    @abstractmethod
    async def search(self, query: str, **kwargs) -> SearchResult:
        """Search for repositories."""
        pass
    
    @abstractmethod
    async def clone(self, repo_id: str, destination: Path) -> Path:
        """Clone repository to local filesystem."""
        pass
```

### 3. Dependency Resolution

Uses uv's SAT solver for Python:

```python
# src/resolution/python_resolver.py
async def resolve(self, requirements: list[str]) -> ResolvedDeps:
    # 1. Parse all requirements
    # 2. Detect conflicts
    # 3. Run SAT solver
    # 4. Generate locked versions
```

### 4. Project Synthesis

The synthesis pipeline:

```
Discovery → Analysis → Resolution → Extraction → Merging → Scaffolding
```

---

## Development Workflow

### Git Branching Strategy

```
main (production)
  └── develop (integration)
       ├── feature/xxx (new features)
       ├── bugfix/xxx (bug fixes)
       └── docs/xxx (documentation)
```

### Making Changes

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

3. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

4. **Run linters:**
   ```bash
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

5. **Commit with conventional commits:**
   ```bash
   git commit -m "feat(discovery): add gitlab client support"
   ```

6. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Scopes:** `core`, `discovery`, `analysis`, `resolution`, `synthesis`, `mcp`, `llm`, `docs`

---

## Testing Guide

### Running Tests

```powershell
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_github_client.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only fast tests
pytest tests/ -m "not slow"
```

### Test Structure

```python
# tests/unit/test_github_client.py
import pytest
from src.discovery.github_client import GitHubClient

class TestGitHubClient:
    @pytest.fixture
    def client(self):
        return GitHubClient(token="test_token")
    
    def test_search_returns_results(self, client):
        results = client.search("python machine learning")
        assert len(results.repositories) > 0
    
    @pytest.mark.slow
    def test_clone_repository(self, client, tmp_path):
        path = client.clone("octocat/Hello-World", tmp_path)
        assert path.exists()
```

### Writing Tests

**Unit Tests:** Test individual functions/methods in isolation
**Integration Tests:** Test component interactions
**E2E Tests:** Test complete workflows



---

## Common Tasks

### Adding a New Platform Client

1. **Create the client file:**
   ```python
   # src/discovery/gitlab_client.py
   from .base_client import PlatformClient
   
   class GitLabClient(PlatformClient):
       platform_name = "gitlab"
       
       async def search(self, query: str, **kwargs) -> SearchResult:
           # Implementation
           pass
   ```

2. **Register in unified search:**
   ```python
   # src/discovery/unified_search.py
   from .gitlab_client import GitLabClient
   
   # Add to _init_clients()
   if "gitlab" in self.config.enabled_platforms:
       self._clients["gitlab"] = GitLabClient(...)
   ```

3. **Add configuration:**
   ```yaml
   # config/default.yaml
   platforms:
     gitlab:
       enabled: true
       token: ${GITLAB_TOKEN}
   ```

4. **Write tests:**
   ```python
   # tests/unit/test_gitlab_client.py
   def test_gitlab_search():
       # Test implementation
   ```

### Adding a New MCP Tool

1. **Define the tool:**
   ```python
   # src/mcp/tools.py
   @mcp.tool()
   async def my_new_tool(param: str) -> dict:
       """Tool description."""
       # Implementation
       return {"result": "success"}
   ```

2. **Add to documentation:**
   - Update `docs/api/API_REFERENCE.md`
   - Add examples

### Modifying Configuration

1. **Add to YAML schema:**
   ```yaml
   # config/default.yaml
   new_section:
     option1: default_value
   ```

2. **Update config loader:**
   ```python
   # src/core/config.py
   @dataclass
   class NewSectionConfig:
       option1: str = "default_value"
   ```

---

## Troubleshooting

### Common Issues

#### "GitHub rate limit exceeded"

**Problem:** API returns 403 error
**Solution:** 
1. Check your `GITHUB_TOKEN` is set
2. Wait for rate limit reset
3. Use authenticated requests

```python
# Check rate limit status
import os
from ghapi.all import GhApi
api = GhApi(token=os.getenv("GITHUB_TOKEN"))
print(api.rate_limit.get())
```

#### "Ollama connection refused"

**Problem:** LLM requests fail
**Solution:**
1. Ensure Ollama is running: `ollama serve`
2. Check the host: `OLLAMA_HOST=http://localhost:11434`
3. Verify model is pulled: `ollama pull qwen2.5-coder:14b`

#### "Import errors after git pull"

**Problem:** Missing new dependencies
**Solution:**
```bash
pip install -r requirements.txt
```

#### "Tests failing with 'No module named X'"

**Problem:** Test path issues
**Solution:**
```bash
# Run from project root
cd AI_Synthesizer
pytest tests/ -v
```

### Debug Mode

Enable verbose logging:

```python
# In code
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
LOG_LEVEL=DEBUG python -m src.mcp.server
```

---

## Getting Help

### Resources

| Resource | Location |
|----------|----------|
| Architecture Docs | `docs/architecture/ARCHITECTURE.md` |
| API Reference | `docs/api/API_REFERENCE.md` |
| Technical Blueprints | `docs/blueprints/TECHNICAL_BLUEPRINTS.md` |
| System Diagrams | `docs/diagrams/DIAGRAMS.md` |
| Work In Progress | `docs/WORK_IN_PROGRESS.md` |

### Contact

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Code Review:** Pull Requests

---

## Next Steps

Ready to contribute? Here are good first tasks:

1. **Easy:** Add documentation improvements
2. **Medium:** Write tests for uncovered modules
3. **Advanced:** Implement the AST parser improvements
4. **Expert:** Add a new platform client

Check `docs/WORK_IN_PROGRESS.md` for detailed task breakdowns!

---

*Happy Coding! 🚀*
