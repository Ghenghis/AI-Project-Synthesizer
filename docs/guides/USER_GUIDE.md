# 📖 AI Project Synthesizer - User Guide

> **Complete Guide for Using the AI Project Synthesizer**  
> **Version:** 1.0.0  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Using MCP Tools in Windsurf](#using-mcp-tools-in-windsurf)
4. [Using the CLI](#using-the-cli)
5. [Common Workflows](#common-workflows)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Introduction

The AI Project Synthesizer helps you:

- **Discover** relevant repositories across GitHub, HuggingFace, Kaggle, and arXiv
- **Analyze** code structure, dependencies, and quality
- **Synthesize** unified projects from multiple sources
- **Generate** professional documentation automatically

### Who Is This For?

- Developers starting new projects who want to leverage existing open-source code
- Teams evaluating multiple repositories for compatibility
- Anyone who wants to automate the tedious parts of project setup

---

## Getting Started

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime environment |
| Git | 2.27+ | Repository operations |
| GitHub Token | - | API access (required) |
| Ollama | Latest | Local LLM (optional) |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Ghenghis/AI-Project-Synthesizer.git
cd AI-Project-Synthesizer

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
```

### Getting a GitHub Token

1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`
4. Copy the token and add to your `.env` file:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

---

## Using MCP Tools in Windsurf

### Configuring Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI-Project-Synthesizer",
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

### Available MCP Tools

#### 1. search_repositories

Search for repositories across multiple platforms.

**Example prompt in Windsurf:**
> "Search for Python machine learning libraries with at least 1000 stars"

**Parameters:**
- `query` (required): Natural language search query
- `platforms`: Platforms to search (default: `["github", "huggingface"]`)
- `max_results`: Maximum results per platform (default: 20)
- `language_filter`: Filter by programming language
- `min_stars`: Minimum star count (default: 10)

#### 2. analyze_repository

Perform deep analysis of a repository.

**Example prompt:**
> "Analyze the repository at https://github.com/pytorch/pytorch"

**Parameters:**
- `repo_url` (required): Repository URL to analyze
- `include_transitive_deps`: Include transitive dependencies (default: true)
- `extract_components`: Identify extractable components (default: true)

#### 3. check_compatibility

Check if multiple repositories can work together.

**Example prompt:**
> "Check if pytorch and transformers are compatible"

**Parameters:**
- `repo_urls` (required): List of repository URLs
- `target_python_version`: Target Python version (default: "3.11")

#### 4. resolve_dependencies

Resolve and merge dependencies from multiple repositories.

**Example prompt:**
> "Resolve dependencies for pytorch and transformers for Python 3.11"

**Parameters:**
- `repositories` (required): Repository URLs
- `constraints`: Additional version constraints
- `python_version`: Target Python version (default: "3.11")

#### 5. synthesize_project

Create a unified project from multiple repositories.

**Example prompt:**
> "Create a new project called 'ml-toolkit' from pytorch and transformers"

**Parameters:**
- `repositories` (required): Repository configurations
- `project_name` (required): Name for synthesized project
- `output_path` (required): Output directory path
- `template`: Project template (default: "python-default")

#### 6. generate_documentation

Generate comprehensive documentation for a project.

**Example prompt:**
> "Generate documentation for my project at ./my-project"

**Parameters:**
- `project_path` (required): Path to the project
- `doc_types`: Types to generate (default: `["readme", "architecture", "api"]`)
- `llm_enhanced`: Use LLM for enhanced quality (default: true)

#### 7. get_synthesis_status

Check the status of a synthesis job.

**Parameters:**
- `synthesis_id` (required): The synthesis job ID

---

## Using the CLI

The CLI provides direct access to all synthesizer features.

### Basic Commands

```bash
# Show help
python -m src.cli --help

# Show version
python -m src.cli version

# Show detailed info
python -m src.cli info

# Show configuration
python -m src.cli config
```

### Search Repositories

```bash
# Basic search
python -m src.cli search "machine learning transformers"

# Search with filters
python -m src.cli search "web scraping" \
  --platforms github,kaggle \
  --min-stars 100 \
  --language python

# Output as JSON
python -m src.cli search "llm agents" --format json
```

### Analyze Repository

```bash
# Basic analysis
python -m src.cli analyze https://github.com/user/repo

# With component extraction
python -m src.cli analyze https://github.com/user/repo --extract-components

# Output as JSON
python -m src.cli analyze https://github.com/user/repo --format json
```

### Synthesize Project

```bash
# Create project from multiple repos
python -m src.cli synthesize \
  --repos https://github.com/user/repo1,https://github.com/user/repo2 \
  --name my-project \
  --output ./projects

# With specific template
python -m src.cli synthesize \
  --repos url1,url2 \
  --name ml-toolkit \
  --template python-ml
```

### Resolve Dependencies

```bash
# Resolve dependencies
python -m src.cli resolve --repos url1,url2

# With specific Python version
python -m src.cli resolve --repos url1,url2 --python 3.12

# Save to file
python -m src.cli resolve --repos url1,url2 --output requirements.txt
```

### Generate Documentation

```bash
# Generate all documentation
python -m src.cli docs ./my-project

# Specific documentation types
python -m src.cli docs ./my-project --types readme,api

# Without LLM enhancement
python -m src.cli docs ./my-project --no-llm
```

### Start MCP Server

```bash
# Start the MCP server for Windsurf
python -m src.cli serve
```

---

## Common Workflows

### Workflow 1: Starting a New ML Project

1. **Search for relevant repositories:**
   ```bash
   python -m src.cli search "pytorch image classification" --min-stars 500
   ```

2. **Analyze top candidates:**
   ```bash
   python -m src.cli analyze https://github.com/user/repo1 --extract-components
   python -m src.cli analyze https://github.com/user/repo2 --extract-components
   ```

3. **Check compatibility:**
   Use the `check_compatibility` MCP tool in Windsurf

4. **Synthesize the project:**
   ```bash
   python -m src.cli synthesize \
     --repos url1,url2 \
     --name image-classifier \
     --output ./projects \
     --template python-ml
   ```

5. **Generate documentation:**
   ```bash
   python -m src.cli docs ./projects/image-classifier
   ```

### Workflow 2: Evaluating Repository Quality

1. **Search for repositories:**
   ```bash
   python -m src.cli search "fastapi authentication" --format json > results.json
   ```

2. **Analyze each repository:**
   ```bash
   python -m src.cli analyze https://github.com/user/repo --format json
   ```

3. **Review the quality scores and dependency analysis**

---

## Best Practices

### 1. Use Specific Search Queries

❌ Bad: `"python library"`
✅ Good: `"python async http client with retry support"`

### 2. Check Compatibility Before Synthesis

Always use `check_compatibility` before synthesizing to avoid dependency conflicts.

### 3. Start with Fewer Repositories

Begin with 2-3 repositories and add more as needed. Too many sources can create complex dependency conflicts.

### 4. Review Generated Documentation

LLM-generated documentation is a starting point. Always review and customize for your specific needs.

### 5. Use Templates Appropriately

| Template | Use Case |
|----------|----------|
| `python-default` | General Python projects |
| `python-ml` | Machine learning projects |
| `python-web` | Web applications |
| `minimal` | Minimal structure |

---

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

### Quick Fixes

| Issue | Solution |
|-------|----------|
| "GitHub API rate limit exceeded" | Wait 1 hour or use authenticated token |
| "Module not found: mcp" | Ensure you're using `src.mcp_server` not `src.mcp` |
| "GITHUB_TOKEN not set" | Add token to `.env` file |
| "Connection refused to Ollama" | Start Ollama: `ollama serve` |

---

## Next Steps

- 📖 [API Reference](../API_REFERENCE.md) - Detailed API documentation
- 🏗️ [Architecture](../architecture/ARCHITECTURE.md) - System design
- ⚙️ [Configuration](./CONFIGURATION.md) - Configuration options
- 🔧 [CLI Reference](./CLI_REFERENCE.md) - Complete CLI documentation


