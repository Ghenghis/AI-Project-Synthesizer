# AI Project Synthesizer - Setup Guide

## Prerequisites

1. **Python 3.11+** installed
2. **Git** installed and configured
3. **GitHub Personal Access Token** (required for repository cloning)

## Quick Setup

### 1. Clone/Download the Project
```bash
git clone <repository-url>
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
