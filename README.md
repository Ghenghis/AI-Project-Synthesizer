# 🧬 AI Project Synthesizer

> **Intelligent Multi-Repository Code Synthesis Platform for Windsurf IDE**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)
[![Windsurf Compatible](https://img.shields.io/badge/Windsurf-Compatible-orange.svg)](https://windsurf.ai/)
[![CI](https://github.com/Ghenghis/AI-Project-Synthesizer/workflows/CI/badge.svg)](https://github.com/Ghenghis/AI-Project-Synthesizer/actions)
[![Status: Complete](https://img.shields.io/badge/Status-Core%20Functionality%20Complete-brightgreen.svg)](docs/COMPLETION_SUMMARY.md)

---

## 🎯 What Is This?

The **AI Project Synthesizer** is a complete, production-ready MCP (Model Context Protocol) server that transforms how developers start new projects. It automatically discovers, analyzes, and synthesizes code from multiple repositories into unified projects.

### ✅ **PROJECT STATUS: 100% COMPLETE**

All core features implemented and tested:
- ✅ GitHub repository cloning and analysis
- ✅ Intelligent code component extraction
- ✅ Dependency conflict resolution with SAT solver
- ✅ Professional documentation generation
- ✅ 7 fully functional MCP tools
- ✅ Comprehensive error handling and validation

**Turn hours of research into minutes of intelligent synthesis.**

---

## 🚀 Quick Start

Get the AI Project Synthesizer running in 3 simple steps:

### 1. Clone & Install
```bash
git clone https://github.com/Ghenghis/AI-Project-Synthesizer.git
cd AI-Project-Synthesizer
pip install -r requirements.txt
```

### 2. Configure GitHub Token
```bash
# Create .env file from template
cp .env.example .env

# Add your GitHub token (create at github.com/settings/tokens)
# GITHUB_TOKEN=ghp_your_token_here
```

### 3. Start the MCP Server
```bash
python -m src.mcp.server
```

That's it! The server is now running and ready to synthesize projects from GitHub repositories.

---

## 📚 Documentation

- **[📖 API Reference](docs/API_REFERENCE.md)** - Complete MCP tool documentation with examples
- **[📊 Project Status](docs/PROJECT_STATUS.md)** - Detailed implementation status
- **[🎯 Completion Summary](docs/COMPLETION_SUMMARY.md)** - Final project completion report
- **[⚙️ Setup Guide](SETUP.md)** - Installation and configuration instructions

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI PROJECT SYNTHESIZER                        │
│                    MCP Server for Windsurf                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  DISCOVERY  │  │  ANALYSIS   │  │  SYNTHESIS  │             │
│  │    Layer    │─▶│    Layer    │─▶│    Layer    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ GitHub API  │  │ Tree-sitter │  │ git-filter  │             │
│  │ HuggingFace │  │   AST-grep  │  │   Copier    │             │
│  │   Kaggle    │  │   LibCST    │  │  Mergiraf   │             │
│  │   arXiv     │  │  pipdeptree │  │    uv       │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LLM ORCHESTRATION                     │   │
│  │  Local: Ollama (Qwen2.5-Coder) │ Cloud: OpenAI/Anthropic │   │
│  │         RouteLLM Hybrid Routing for Cost Optimization    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🔍 Multi-Platform Discovery
- **GitHub** - 330M+ repositories with advanced search
- **GitLab** - Public and self-hosted instances
- **HuggingFace** - ML models, datasets, and Spaces
- **Kaggle** - Notebooks and datasets
- **Papers with Code** - Academic implementations
- **arXiv/Semantic Scholar** - Research papers

### 🧠 Intelligent Analysis
- **AST Parsing** - Tree-sitter for 100+ languages
- **Dependency Graphs** - Visualize all relationships
- **Conflict Detection** - Find version incompatibilities
- **Code Quality Scoring** - Assess maintainability
- **License Compatibility** - Legal compliance checking

### 🔧 Smart Synthesis
- **Selective Extraction** - Pull only what you need
- **Automatic Refactoring** - Rename conflicts
- **Dependency Resolution** - SAT solver via `uv`
- **History Preservation** - git-filter-repo
- **Syntax-Aware Merging** - Mergiraf

### 📚 Documentation Generation
- **README.md** - AI-powered with readme-ai
- **Architecture Diagrams** - Mermaid/Kroki
- **API Documentation** - Auto-extracted
- **Dependency Visualizations** - pydeps/madge

### 🖥️ Local-First LLM
- **Primary**: Ollama with Qwen2.5-Coder (14B)
- **Fallback**: Cloud APIs (toggled)
- **Routing**: RouteLLM for intelligent switching
- **Hardware**: Optimized for RTX 3090/4090

---

## 📁 Project Structure

```
AI_Synthesizer/
├── src/
│   ├── core/                 # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration management
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── logging.py        # Logging setup
│   │
│   ├── discovery/            # Repository discovery
│   │   ├── __init__.py
│   │   ├── github_client.py  # GitHub API integration
│   │   ├── huggingface_client.py
│   │   ├── kaggle_client.py
│   │   ├── arxiv_client.py
│   │   ├── papers_with_code.py
│   │   └── unified_search.py # Cross-platform search
│   │
│   ├── analysis/             # Code analysis
│   │   ├── __init__.py
│   │   ├── ast_parser.py     # Tree-sitter integration
│   │   ├── dependency_analyzer.py
│   │   ├── compatibility_checker.py
│   │   ├── code_extractor.py
│   │   └── quality_scorer.py
│   │
│   ├── resolution/           # Dependency resolution
│   │   ├── __init__.py
│   │   ├── python_resolver.py  # uv/pip-tools
│   │   ├── node_resolver.py    # npm/pnpm
│   │   ├── conflict_detector.py
│   │   └── unified_resolver.py
│   │
│   ├── synthesis/            # Project synthesis
│   │   ├── __init__.py
│   │   ├── repo_merger.py    # git-filter-repo
│   │   ├── code_merger.py    # Mergiraf integration
│   │   ├── scaffolder.py     # Copier templates
│   │   └── project_builder.py
│   │
│   ├── generation/           # Documentation generation
│   │   ├── __init__.py
│   │   ├── readme_generator.py
│   │   ├── diagram_generator.py  # Mermaid/Kroki
│   │   ├── api_doc_generator.py
│   │   └── architecture_generator.py
│   │
│   ├── mcp/                  # MCP Server
│   │   ├── __init__.py
│   │   ├── server.py         # FastMCP server
│   │   ├── tools.py          # MCP tool definitions
│   │   ├── resources.py      # MCP resources
│   │   └── prompts.py        # MCP prompts
│   │
│   ├── llm/                  # LLM orchestration
│   │   ├── __init__.py
│   │   ├── ollama_client.py
│   │   ├── cloud_client.py
│   │   ├── router.py         # RouteLLM integration
│   │   └── prompts.py        # System prompts
│   │
│   └── utils/                # Utilities
│       ├── __init__.py
│       ├── git_utils.py
│       ├── file_utils.py
│       ├── rate_limiter.py
│       └── cache.py
│
├── tests/                    # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                     # Documentation
│   ├── architecture/         # System design docs
│   ├── api/                  # API reference
│   ├── guides/               # User guides
│   ├── diagrams/             # Visual diagrams
│   └── blueprints/           # Technical blueprints
│
├── config/                   # Configuration files
│   ├── default.yaml
│   ├── ai_providers.yaml
│   └── platforms.yaml
│
├── templates/                # Project templates
│   ├── project/
│   └── documentation/
│
├── scripts/                  # Automation scripts
│   ├── setup.ps1
│   ├── setup.sh
│   └── download_models.py
│
├── docker/                   # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── .github/                  # GitHub configuration
│   ├── workflows/
│   └── ISSUE_TEMPLATE/
│
├── pyproject.toml            # Python project config
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
├── .gitignore
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
└── CODE_OF_CONDUCT.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Git 2.27+**
- **Docker & Docker Compose** (optional)
- **Ollama** (for local LLM)
- **NVIDIA GPU** with CUDA 12.1+ (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AI_Synthesizer.git
cd AI_Synthesizer

# Option 1: Using uv (recommended - 10-100x faster)
pip install uv
uv venv
uv pip install -r requirements.txt

# Option 2: Traditional pip
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Download local LLM models
python scripts/download_models.py

# Start the MCP server
python -m src.mcp.server
```

### Windsurf Integration

Add to your `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "C:\\Users\\Admin\\AI_Synthesizer",
      "env": {
        "OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

---

## 🛠️ MCP Tools Reference

| Tool | Description |
|------|-------------|
| `search_repositories` | Search across all platforms |
| `analyze_compatibility` | Check if repos work together |
| `extract_components` | Pull specific code from repos |
| `resolve_dependencies` | Merge and resolve dependencies |
| `synthesize_project` | Create unified project |
| `generate_documentation` | Auto-generate docs |
| `get_synthesis_status` | Check progress |

---

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32+ GB |
| GPU VRAM | 8 GB | 24 GB (RTX 3090/4090) |
| Storage | 50 GB | 100+ GB SSD |
| OS | Windows 10/11, Linux | Windows 11 + WSL2 |

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install dev dependencies
uv pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run linting
ruff check src/
mypy src/

# Format code
black src/ tests/
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with these amazing open-source projects:
- [Tree-sitter](https://tree-sitter.github.io/) - Universal AST parsing
- [uv](https://github.com/astral-sh/uv) - Fast Python package management
- [Qwen2.5-Coder](https://github.com/QwenLM/Qwen2.5-Coder) - Code LLM
- [FastMCP](https://github.com/anthropics/anthropic-cookbook) - MCP SDK
- [Ollama](https://ollama.ai/) - Local LLM serving

---

**Made with ❤️ for the Windsurf community**
