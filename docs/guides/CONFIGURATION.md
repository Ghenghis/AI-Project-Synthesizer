# ⚙️ AI Project Synthesizer - Configuration Guide

> **Complete Configuration Reference**  
> **Version:** 1.0.0  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Overview](#overview)
2. [Environment File](#environment-file)
3. [Platform Credentials](#platform-credentials)
4. [LLM Configuration](#llm-configuration)
5. [Application Settings](#application-settings)
6. [Advanced Configuration](#advanced-configuration)

---

## Overview

The AI Project Synthesizer uses a `.env` file for configuration. All settings are loaded via Pydantic Settings with validation.

### Quick Setup

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

---

## Environment File

Create a `.env` file in the project root with the following structure:

```env
# ===========================================
# AI Project Synthesizer Configuration
# ===========================================

# Application Settings
APP_ENV=development
DEBUG=false
LOG_LEVEL=INFO

# GitHub (Required)
GITHUB_TOKEN=ghp_your_token_here

# Optional Platform Tokens
HUGGINGFACE_TOKEN=hf_your_token_here
GITLAB_TOKEN=glpat_your_token_here
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# LLM Settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_FAST=qwen2.5-coder:7b-instruct-q8_0
```

---

## Platform Credentials

### GitHub (Required)

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | **Yes** | Personal access token |

**Getting a GitHub Token:**

1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`
4. Copy and add to `.env`

### GitLab (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITLAB_TOKEN` | No | - | Personal access token |
| `GITLAB_URL` | No | `https://gitlab.com` | GitLab instance URL |

### HuggingFace (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `HUGGINGFACE_TOKEN` | No | HuggingFace access token |

**Getting a HuggingFace Token:**

1. Go to [HuggingFace Settings → Access Tokens](https://huggingface.co/settings/tokens)
2. Create a new token with read access
3. Copy and add to `.env`

### Kaggle (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `KAGGLE_USERNAME` | No | Your Kaggle username |
| `KAGGLE_KEY` | No | Kaggle API key |

**Getting Kaggle Credentials:**

1. Go to [Kaggle Account Settings](https://www.kaggle.com/account)
2. Scroll to "API" section
3. Click "Create New API Token"
4. Copy username and key to `.env`

### Semantic Scholar (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `SEMANTIC_SCHOLAR_API_KEY` | No | API key for higher rate limits |

---

## LLM Configuration

### Ollama (Local LLM)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL_FAST` | `qwen2.5-coder:7b-instruct-q8_0` | Fast model for simple tasks |
| `OLLAMA_MODEL_BALANCED` | `qwen2.5-coder:14b-instruct-q4_K_M` | Balanced model |
| `OLLAMA_MODEL_POWERFUL` | `qwen2.5-coder:32b-instruct-q4_K_M` | Powerful model for complex tasks |

**Installing Ollama Models:**

```bash
# Install Ollama (if not installed)
# See: https://ollama.ai/download

# Pull recommended models
ollama pull qwen2.5-coder:7b-instruct-q8_0
ollama pull qwen2.5-coder:14b-instruct-q4_K_M

# Start Ollama server
ollama serve
```

### Cloud LLM (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `CLOUD_LLM_ENABLED` | `false` | Enable cloud LLM fallback |
| `CLOUD_ROUTING_THRESHOLD` | `0.7` | Threshold for routing to cloud (0.0-1.0) |

### OpenAI (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | Model to use |

### Anthropic (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Model to use |

---

## Application Settings

### General

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AI Project Synthesizer` | Application name |
| `APP_ENV` | `development` | Environment (development/production) |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_HOST` | `localhost` | Server host |
| `SERVER_PORT` | `8000` | Server port |

### Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_OUTPUT_DIR` | `./output` | Default output directory |
| `TEMP_DIR` | `./temp` | Temporary directory |
| `CACHE_DIR` | `./.cache` | Cache directory |

### Synthesis

| Variable | Default | Range | Description |
|----------|---------|-------|-------------|
| `MAX_REPOS_PER_SYNTHESIS` | `10` | 1-50 | Maximum repositories per synthesis |
| `MAX_CONCURRENT_CLONES` | `3` | 1-10 | Maximum concurrent clone operations |
| `CLONE_DEPTH` | `1` | 1+ | Git clone depth (shallow clone) |

### Network

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUEST_TIMEOUT_SECONDS` | `30` | HTTP request timeout |
| `MAX_RETRIES` | `3` | Maximum retry attempts |

### Cache

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_ENABLED` | `true` | Enable caching |
| `CACHE_TTL_SECONDS` | `3600` | Cache TTL (1 hour) |

---

## Advanced Configuration

### Complete Example `.env`

```env
# ===========================================
# AI Project Synthesizer - Full Configuration
# ===========================================

# Application
APP_NAME=AI Project Synthesizer
APP_ENV=development
DEBUG=false
LOG_LEVEL=INFO

# Server
SERVER_HOST=localhost
SERVER_PORT=8000

# Paths
DEFAULT_OUTPUT_DIR=./output
TEMP_DIR=./temp
CACHE_DIR=./.cache

# Synthesis
MAX_REPOS_PER_SYNTHESIS=10
MAX_CONCURRENT_CLONES=3
CLONE_DEPTH=1

# Network
REQUEST_TIMEOUT_SECONDS=30
MAX_RETRIES=3

# Cache
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# GitHub (Required)
GITHUB_TOKEN=ghp_your_token_here

# GitLab (Optional)
GITLAB_TOKEN=glpat_your_token_here
GITLAB_URL=https://gitlab.com

# HuggingFace (Optional)
HUGGINGFACE_TOKEN=hf_your_token_here

# Kaggle (Optional)
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# Semantic Scholar (Optional)
SEMANTIC_SCHOLAR_API_KEY=your_key_here

# Ollama (Local LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_FAST=qwen2.5-coder:7b-instruct-q8_0
OLLAMA_MODEL_BALANCED=qwen2.5-coder:14b-instruct-q4_K_M
OLLAMA_MODEL_POWERFUL=qwen2.5-coder:32b-instruct-q4_K_M

# Cloud LLM (Optional)
CLOUD_LLM_ENABLED=false
CLOUD_ROUTING_THRESHOLD=0.7

# OpenAI (Optional)
OPENAI_API_KEY=sk-your_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic (Optional)
ANTHROPIC_API_KEY=sk-ant-your_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Production Configuration

For production deployments:

```env
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
CACHE_ENABLED=true
CACHE_TTL_SECONDS=7200
MAX_CONCURRENT_CLONES=5
REQUEST_TIMEOUT_SECONDS=60
```

### Development Configuration

For development:

```env
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
CACHE_ENABLED=false
```

---

## Validation

The configuration is validated on startup using Pydantic. Invalid values will raise errors:

```python
from src.core.config import get_settings

settings = get_settings()
print(f"Environment: {settings.app.app_env}")
print(f"Enabled platforms: {settings.platforms.get_enabled_platforms()}")
```

---

## See Also

- [User Guide](./USER_GUIDE.md) - Complete user documentation
- [CLI Reference](./CLI_REFERENCE.md) - Command line interface
- [API Reference](../API_REFERENCE.md) - MCP tool documentation


