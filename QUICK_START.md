# AI Project Synthesizer - Quick Start Guide

Get up and running in 5 minutes!

## 1. Installation

```bash
# Clone the repository
git clone https://github.com/Ghenghis/AI-Project-Synthesizer.git
cd AI_Synthesizer

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

## 2. Quick Validation

Run smoke tests to verify everything works:

```bash
# Using test runner
python scripts/test_runner.py quick

# Or directly with pytest
pytest tests/test_mcp_smoke.py -v
```

## 3. Development Commands

### Windows (PowerShell)
```powershell
.\scripts\dev.ps1 quick      # Smoke tests
.\scripts\dev.ps1 test       # Unit tests
.\scripts\dev.ps1 lint       # Check code style
.\scripts\dev.ps1 format     # Auto-format code
```

### Linux/Mac (Make)
```bash
make quick      # Smoke tests
make test       # Unit tests
make lint       # Check code style
make format     # Auto-format code
```

### Cross-Platform (Python)
```bash
python scripts/test_runner.py quick   # Smoke tests
python scripts/test_runner.py unit    # Unit tests
python scripts/test_runner.py ci      # CI with coverage
```

## 4. Set Up Pre-commit Hooks (Optional)

Automatically check code quality before each commit:

```bash
pip install pre-commit
pre-commit install
```

## 5. Environment Variables

Create a `.env` file in the project root:

```env
# Required
GITHUB_TOKEN=your_github_token

# Optional - for LLM features
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OLLAMA_HOST=http://localhost:11434
```

## 6. Start the MCP Server

```bash
# Windows
.\scripts\dev.ps1 serve

# Linux/Mac
make serve

# Or directly
python -m src.mcp.server
```

## 7. Use with Windsurf IDE

Add to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "ai-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "C:/Users/Admin/AI_Synthesizer"
    }
  }
}
```

## Common Issues

### Import Errors
Make sure you're in the virtual environment and have installed the package:
```bash
pip install -e ".[dev]"
```

### Tests Failing
Run the quick smoke test first to isolate issues:
```bash
python scripts/test_runner.py quick
```

### Missing Dependencies
Install system dependencies for audio features:
```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev libsndfile1-dev

# macOS
brew install portaudio libsndfile
```

## Next Steps

- 📖 Read the full [README.md](README.md)
- 🐛 Report issues via [GitHub Issues](https://github.com/Ghenghis/AI-Project-Synthesizer/issues)
- 💡 Request features using the feature request template
