# 🖥️ AI Project Synthesizer - CLI Reference

> **Complete Command Line Interface Documentation**  
> **Version:** 1.0.0  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Installation](#installation)
2. [Global Options](#global-options)
3. [Commands](#commands)
   - [search](#search)
   - [analyze](#analyze)
   - [synthesize](#synthesize)
   - [resolve](#resolve)
   - [docs](#docs)
   - [config](#config)
   - [serve](#serve)
   - [version](#version)
   - [info](#info)

---

## Installation

The CLI is available after installing the package:

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python -m src.cli --help
```

---

## Global Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version number |

---

## Commands

### search

Search for repositories across multiple platforms.

```bash
python -m src.cli search <query> [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `query` | Yes | Natural language search query |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--platforms` | `-p` | `github,huggingface` | Comma-separated platforms |
| `--max-results` | `-n` | `20` | Maximum results per platform |
| `--language` | `-l` | None | Filter by programming language |
| `--min-stars` | `-s` | `10` | Minimum star count |
| `--format` | `-f` | `table` | Output format: table, json, simple |

**Examples:**

```bash
# Basic search
python -m src.cli search "machine learning transformers"

# Search GitHub only with filters
python -m src.cli search "web scraping" -p github -s 100 -l python

# Output as JSON
python -m src.cli search "llm agents" --format json

# Search multiple platforms
python -m src.cli search "data visualization" -p github,kaggle -n 50
```

---

### analyze

Perform deep analysis of a repository.

```bash
python -m src.cli analyze <repo_url> [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `repo_url` | Yes | Repository URL to analyze |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--include-deps/--no-deps` | | `--include-deps` | Include dependency analysis |
| `--include-quality/--no-quality` | | `--include-quality` | Include quality scoring |
| `--extract-components` | `-e` | False | Identify extractable components |
| `--format` | `-f` | `rich` | Output format: rich, json, summary |

**Examples:**

```bash
# Basic analysis
python -m src.cli analyze https://github.com/pytorch/pytorch

# With component extraction
python -m src.cli analyze https://github.com/user/repo -e

# JSON output for scripting
python -m src.cli analyze https://github.com/user/repo -f json

# Quick summary
python -m src.cli analyze https://github.com/user/repo -f summary
```

---

### synthesize

Create a unified project from multiple repositories.

```bash
python -m src.cli synthesize [OPTIONS]
```

**Options:**

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--repos` | `-r` | Yes | - | Comma-separated repository URLs |
| `--name` | `-n` | Yes | - | Name for synthesized project |
| `--output` | `-o` | No | `./output` | Output directory path |
| `--template` | `-t` | No | `python-default` | Project template |

**Available Templates:**

- `python-default` - Standard Python project
- `python-ml` - Machine learning project
- `python-web` - Web application
- `minimal` - Bare bones structure

**Examples:**

```bash
# Basic synthesis
python -m src.cli synthesize \
  --repos https://github.com/user/repo1,https://github.com/user/repo2 \
  --name my-project

# With specific template and output
python -m src.cli synthesize \
  -r url1,url2 \
  -n ml-toolkit \
  -o ./projects \
  -t python-ml
```

---

### resolve

Resolve and merge dependencies from multiple repositories.

```bash
python -m src.cli resolve [OPTIONS]
```

**Options:**

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--repos` | `-r` | Yes | - | Comma-separated repository URLs |
| `--python` | `-p` | No | `3.11` | Target Python version |
| `--output` | `-o` | No | None | Output file for requirements |

**Examples:**

```bash
# Basic resolution
python -m src.cli resolve --repos url1,url2

# With specific Python version
python -m src.cli resolve -r url1,url2 --python 3.12

# Save to requirements file
python -m src.cli resolve -r url1,url2 -o requirements.txt
```

---

### docs

Generate comprehensive documentation for a project.

```bash
python -m src.cli docs <project_path> [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `project_path` | Yes | Path to the project to document |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--types` | `-t` | `readme,architecture,api` | Comma-separated doc types |
| `--llm/--no-llm` | | `--llm` | Use LLM for enhanced quality |

**Available Documentation Types:**

- `readme` - README.md file
- `architecture` - Architecture documentation
- `api` - API reference documentation
- `diagrams` - Mermaid diagrams

**Examples:**

```bash
# Generate all documentation
python -m src.cli docs ./my-project

# Specific documentation types
python -m src.cli docs ./my-project -t readme,api

# Without LLM enhancement (faster)
python -m src.cli docs ./my-project --no-llm
```

---

### config

Show current configuration settings.

```bash
python -m src.cli config [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--all` | `-a` | False | Show all config including sensitive values |

**Examples:**

```bash
# Show basic configuration
python -m src.cli config

# Show all configuration (including token status)
python -m src.cli config --all
```

**Output includes:**

- Environment (development/production)
- Debug mode status
- Log level
- Enabled platforms
- LLM settings
- Cache settings

---

### serve

Start the MCP server for Windsurf IDE integration.

```bash
python -m src.cli serve
```

This command starts the Model Context Protocol server that allows Windsurf IDE to interact with the AI Project Synthesizer.

**Example:**

```bash
python -m src.cli serve
```

The server runs on stdio and communicates with Windsurf via the MCP protocol.

---

### version

Show version information.

```bash
python -m src.cli version
```

**Output:**

```
AI Project Synthesizer v1.0.0
```

---

### info

Show detailed information about the tool.

```bash
python -m src.cli info
```

Displays:
- Application banner
- Key features
- Usage examples
- Documentation links
- Support information

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error occurred |

---

## Environment Variables

The CLI respects the following environment variables:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub API token (required) |
| `HUGGINGFACE_TOKEN` | HuggingFace API token (optional) |
| `KAGGLE_USERNAME` | Kaggle username (optional) |
| `KAGGLE_KEY` | Kaggle API key (optional) |
| `OLLAMA_HOST` | Ollama server URL (default: http://localhost:11434) |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## See Also

- [User Guide](./USER_GUIDE.md) - Complete user documentation
- [API Reference](../API_REFERENCE.md) - MCP tool documentation
- [Configuration](./CONFIGURATION.md) - Configuration options


