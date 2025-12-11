# 🚀 AI Project Synthesizer - Quick Start Guide

> **Get up and running in 5 minutes!**

---

## Prerequisites

- Python 3.11+
- Git
- GitHub account

---

## Step 1: Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/Ghenghis/AI-Project-Synthesizer.git
cd AI-Project-Synthesizer

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure (1 minute)

```bash
# Create environment file
cp .env.example .env
```

Edit `.env` and add your GitHub token:

```env
GITHUB_TOKEN=ghp_your_token_here
```

**Get a token:** [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)

---

## Step 3: Run (30 seconds)

### Option A: Use CLI

```bash
# Search for repositories
python -m src.cli search "machine learning pytorch"

# Analyze a repository
python -m src.cli analyze https://github.com/pytorch/pytorch

# Show all commands
python -m src.cli --help
```

### Option B: Use with Windsurf IDE

1. Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI-Project-Synthesizer"
    }
  }
}
```

2. Restart Windsurf
3. Use natural language: *"Search for Python web scraping libraries"*

---

## Quick Examples

### Search Repositories

```bash
python -m src.cli search "fastapi authentication" --min-stars 100
```

### Analyze Repository

```bash
python -m src.cli analyze https://github.com/tiangolo/fastapi
```

### Synthesize Project

```bash
python -m src.cli synthesize \
  --repos https://github.com/user/repo1,https://github.com/user/repo2 \
  --name my-project \
  --output ./projects
```

### Generate Documentation

```bash
python -m src.cli docs ./my-project
```

---

## What's Next?

| Want to... | Read... |
|------------|---------|
| Learn all features | [User Guide](./USER_GUIDE.md) |
| See all CLI commands | [CLI Reference](./CLI_REFERENCE.md) |
| Configure settings | [Configuration](./CONFIGURATION.md) |
| Fix issues | [Troubleshooting](./TROUBLESHOOTING.md) |
| Understand the API | [API Reference](../API_REFERENCE.md) |

---

## Common Issues

| Problem | Solution |
|---------|----------|
| `GITHUB_TOKEN not set` | Add token to `.env` file |
| `Module not found: mcp` | Use `src.mcp_server` not `src.mcp` |
| Rate limit exceeded | Wait 1 hour or use authenticated token |

---

## Need Help?

- 📖 [Full Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/Ghenghis/AI-Project-Synthesizer/issues)
- 💬 [Discussions](https://github.com/Ghenghis/AI-Project-Synthesizer/discussions)

---

**Happy Synthesizing! 🧬**

