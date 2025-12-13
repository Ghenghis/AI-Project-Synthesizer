# AI Project Synthesizer - Quick Setup Guide

## Overview
AI Project Synthesizer is an MCP (Model Context Protocol) server that helps you discover, analyze, and synthesize code from multiple repositories. It works with Windsurf IDE, Claude Desktop, VS Code, and other MCP-compatible clients.

## Prerequisites

- Python 3.11 or higher
- Git
- GitHub Personal Access Token (required for repository cloning)
- Optional: Ollama for local LLM support

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Ghenghis/AI-Project-Synthesizer.git
cd AI_Synthesizer
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create `.env` file in the root directory:
```env
# Required
GITHUB_TOKEN=your_github_token_here

# Optional - for local LLM
OLLAMA_HOST=http://localhost:11434

# Optional - for cloud LLMs
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Running the MCP Server

### Option 1: Standalone (for testing)
```bash
python -m src.mcp_server.server
```

### Option 2: With Windsurf IDE
Add to `~/.windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer"
    }
  }
}
```

### Option 3: With Claude Desktop
Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer"
    }
  }
}
```

## Available Tools

- **search_repositories**: Find repositories across GitHub, HuggingFace, Kaggle
- **analyze_repository**: Deep analysis of code structure, dependencies, quality
- **check_compatibility**: Verify if multiple repositories can work together
- **resolve_dependencies**: Merge dependencies without conflicts
- **synthesize_project**: Create a new project from multiple sources

## Example Usage

In Windsurf/Claude, try:
```
Search for Python web scraping repositories on GitHub with at least 100 stars.
```

```
Analyze https://github.com/example/scrapy-project and extract the main components.
```

```
Check if https://github.com/a/fastapi and https://github.com/b/sqlalchemy are compatible.
```

## Troubleshooting

### Voice/Audio Issues on Linux
If you get portaudio errors:
```bash
sudo apt-get install portaudio19-dev libsndfile1-dev
```

### Permission Errors
Make sure your GitHub token has the appropriate scopes:
- `public_repo` (for public repositories)
- `repo` (for private repositories)

### LLM Not Responding
- Check Ollama is running: `ollama list`
- Verify OLLAMA_HOST in `.env`
- Try a cloud provider as fallback

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
ruff check src/ --fix
ruff format src/
```

## Need Help?

- Check the [Issues](https://github.com/Ghenghis/AI-Project-Synthesizer/issues) page
- Read the [Documentation](docs/)
- Join our Discord community

## License
MIT License - see LICENSE file for details.

### 4. Configure Environment

Create a `.env` file in the project root:

```env
# Required: GitHub Token
GITHUB_TOKEN=ghp_your_actual_github_token_here

# Optional: HuggingFace Token (for model repositories)
HUGGINGFACE_TOKEN=hf_your_huggingface_token_here

# Optional: Ollama for local LLM
OLLAMA_HOST=http://localhost:11434

# App Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
CACHE_ENABLED=true
```

#### Getting a GitHub Token:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (for private repos) or `public_repo` (for public repos only)
4. Copy the token (it starts with `ghp_`)
5. Paste it in your `.env` file

### 5. Verify Installation

Run the end-to-end test:
```bash
python test_synthesis.py
```

Expected output:
```
🎉 All tests passed! The AI Project Synthesizer is working.
```

## Optional Dependencies

For enhanced functionality, install:

### Tree-sitter (for better AST parsing)
```bash
# Python binding
pip install tree-sitter
# Language parsers
pip install tree-sitter-python tree-sitter-javascript tree-sitter-typescript
```

### ghapi (for enhanced GitHub API)
```bash
pip install ghapi
```

### uv (for faster dependency resolution)
```bash
# Windows
pip install uv
# Or follow instructions at https://github.com/astral-sh/uv
```

## Running the MCP Server

Once configured, start the MCP server:

```bash
python -m src.mcp.server
```

The server will expose 7 tools:
- `search_repositories` - Search across platforms
- `analyze_repository` - Analyze a repository
- `check_compatibility` - Check for conflicts
- `resolve_dependencies` - Resolve Python dependencies
- `synthesize_project` - Create unified project
- `generate_documentation` - Generate docs
- `get_synthesis_status` - Check synthesis status

## Troubleshooting

### "No client for platform: github"
- **Cause**: Missing or invalid GitHub token
- **Fix**: Set a valid `GITHUB_TOKEN` in `.env`

### "tree-sitter not available, using fallback parsing"
- **Cause**: tree-sitter not installed
- **Fix**: Install tree-sitter (optional, fallback works)

### "ghapi not installed, using fallback"
- **Cause**: ghapi not installed
- **Fix**: Install ghapi (optional, fallback works)

### UnicodeEncodeError on Windows
- **Cause**: Windows default encoding
- **Fix**: Fixed in code - files now use UTF-8 encoding

## Current Limitations

1. **GitHub Only**: Only GitHub repositories are fully supported
2. **Python Projects**: Dependency resolution works for Python projects
3. **Public Repos**: Easier with public repositories (no token scopes needed)
4. **Basic Merging**: Code merging is simple file copying (no AST-aware merging yet)

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run specific test suites:
```bash
pytest tests/unit/test_python_resolver.py -v
pytest tests/unit/test_github_client.py -v
```

## Next Steps

To contribute or extend:
1. Add more platform clients (Kaggle, arXiv)
2. Implement tree-sitter AST parsing
3. Add conflict detection improvements
4. Create more sophisticated code merging

## Support

If you encounter issues:
1. Check your `.env` file has correct tokens
2. Verify Python 3.11+ is installed
3. Run with `DEBUG=true` to see detailed logs
4. Check the test output for specific error messages
