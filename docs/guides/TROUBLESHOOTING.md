# 🔧 AI Project Synthesizer - Troubleshooting Guide

> **Solutions for Common Issues**  
> **Version:** 1.0.0  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Authentication Issues](#authentication-issues)
3. [MCP Server Issues](#mcp-server-issues)
4. [CLI Issues](#cli-issues)
5. [Synthesis Issues](#synthesis-issues)
6. [LLM Issues](#llm-issues)
7. [Performance Issues](#performance-issues)
8. [Getting Help](#getting-help)

---

## Installation Issues

### Python Version Error

**Error:**
```
Python 3.11+ is required
```

**Solution:**
```bash
# Check your Python version
python --version

# Install Python 3.11+ from python.org or use pyenv
pyenv install 3.11.0
pyenv local 3.11.0
```

### Missing Dependencies

**Error:**
```
ModuleNotFoundError: No module named 'pydantic'
```

**Solution:**
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Tree-sitter Build Errors

**Error:**
```
Failed to build tree-sitter-python
```

**Solution:**
```bash
# Install build tools
# Windows: Install Visual Studio Build Tools
# Linux: sudo apt install build-essential
# macOS: xcode-select --install

# Reinstall tree-sitter
pip uninstall tree-sitter tree-sitter-python
pip install tree-sitter tree-sitter-python
```

---

## Authentication Issues

### GitHub Token Not Set

**Error:**
```
GITHUB_TOKEN environment variable not set
```

**Solution:**
1. Create a GitHub token at https://github.com/settings/tokens
2. Add to `.env` file:
   ```env
   GITHUB_TOKEN=ghp_your_token_here
   ```
3. Restart the application

### GitHub API Rate Limit

**Error:**
```
GitHub API rate limit exceeded
```

**Solution:**
- Wait for rate limit reset (usually 1 hour)
- Use an authenticated token (5000 requests/hour vs 60)
- Check remaining rate limit:
  ```bash
  curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
  ```

### Invalid Token

**Error:**
```
401 Unauthorized: Bad credentials
```

**Solution:**
1. Verify token is correct in `.env`
2. Check token hasn't expired
3. Ensure token has required scopes: `repo`, `read:org`
4. Generate a new token if needed

---

## MCP Server Issues

### Module Not Found: mcp

**Error:**
```
ModuleNotFoundError: No module named 'mcp'
```

**Solution:**
The module was renamed. Use the correct import:
```bash
# Correct command
python -m src.mcp_server.server

# NOT this (old path)
python -m src.mcp.server
```

### Server Won't Start

**Error:**
```
Address already in use
```

**Solution:**
```bash
# Find and kill the process using the port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :8000
kill -9 <PID>
```

### Windsurf Not Connecting

**Symptoms:**
- MCP tools not appearing in Windsurf
- Connection timeout errors

**Solution:**
1. Verify `mcp_config.json` is correct:
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
3. Check server logs for errors

---

## CLI Issues

### Command Not Found

**Error:**
```
No such command 'search'
```

**Solution:**
```bash
# Use the correct module path
python -m src.cli search "query"

# NOT
python src/cli.py search "query"
```

### Output Encoding Errors

**Error:**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solution:**
```bash
# Set UTF-8 encoding
# Windows PowerShell:
$env:PYTHONIOENCODING = "utf-8"

# Windows CMD:
set PYTHONIOENCODING=utf-8

# Linux/macOS:
export PYTHONIOENCODING=utf-8
```

---

## Synthesis Issues

### Repository Clone Failed

**Error:**
```
Failed to clone repository: Permission denied
```

**Solution:**
1. Check repository exists and is accessible
2. Verify GitHub token has `repo` scope
3. For private repos, ensure you have access

### Dependency Conflict

**Error:**
```
Dependency conflict: package-a requires X>=2.0, package-b requires X<2.0
```

**Solution:**
1. Use `resolve` command to see conflicts:
   ```bash
   python -m src.cli resolve --repos url1,url2
   ```
2. Add constraints to resolve:
   ```bash
   python -m src.cli synthesize --repos url1,url2 --constraints "X>=1.5,<2.0"
   ```
3. Consider using fewer repositories

### Synthesis Timeout

**Error:**
```
Synthesis operation timed out
```

**Solution:**
1. Reduce number of repositories
2. Use shallow clones (default)
3. Increase timeout in config:
   ```env
   REQUEST_TIMEOUT_SECONDS=120
   ```

---

## LLM Issues

### Ollama Connection Refused

**Error:**
```
Connection refused: http://localhost:11434
```

**Solution:**
```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### Model Not Found

**Error:**
```
Model 'qwen2.5-coder:7b-instruct-q8_0' not found
```

**Solution:**
```bash
# Pull the model
ollama pull qwen2.5-coder:7b-instruct-q8_0

# List available models
ollama list
```

### LLM Response Timeout

**Error:**
```
LLM request timed out
```

**Solution:**
1. Use a smaller/faster model:
   ```env
   OLLAMA_MODEL_FAST=qwen2.5-coder:3b
   ```
2. Increase timeout
3. Check system resources (RAM, GPU)

### Out of Memory

**Error:**
```
CUDA out of memory
```

**Solution:**
1. Use a smaller quantized model:
   ```env
   OLLAMA_MODEL_FAST=qwen2.5-coder:7b-instruct-q4_K_M
   ```
2. Close other GPU-intensive applications
3. Use CPU-only mode (slower)

---

## Performance Issues

### Slow Repository Analysis

**Symptoms:**
- Analysis takes several minutes
- High CPU usage

**Solution:**
1. Enable caching:
   ```env
   CACHE_ENABLED=true
   CACHE_TTL_SECONDS=7200
   ```
2. Use shallow clones (default)
3. Limit analysis scope

### High Memory Usage

**Symptoms:**
- Memory usage grows over time
- Application becomes slow

**Solution:**
1. Reduce concurrent operations:
   ```env
   MAX_CONCURRENT_CLONES=2
   ```
2. Clear cache periodically:
   ```bash
   rm -rf .cache/*
   ```
3. Restart the application

### Slow Search Results

**Symptoms:**
- Search takes >30 seconds

**Solution:**
1. Reduce platforms searched:
   ```bash
   python -m src.cli search "query" -p github
   ```
2. Reduce max results:
   ```bash
   python -m src.cli search "query" -n 10
   ```

---

## Getting Help

### Debug Mode

Enable debug mode for detailed logs:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Log Files

Check logs for detailed error information:

```bash
# View recent logs
tail -f logs/app.log
```

### Reporting Issues

When reporting issues, include:

1. **Error message** - Full error text
2. **Steps to reproduce** - What you did
3. **Environment** - OS, Python version
4. **Configuration** - Relevant `.env` settings (redact tokens!)
5. **Logs** - Debug output if available

**Report issues at:** https://github.com/Ghenghis/AI-Project-Synthesizer/issues

---

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Module not found: mcp | Use `src.mcp_server` not `src.mcp` |
| GitHub rate limit | Wait 1 hour or use authenticated token |
| Ollama not connecting | Run `ollama serve` |
| Model not found | Run `ollama pull <model>` |
| Dependency conflict | Use `resolve` command first |
| Slow performance | Enable caching, reduce concurrency |

---

## See Also

- [User Guide](./USER_GUIDE.md) - Complete user documentation
- [Configuration](./CONFIGURATION.md) - Configuration options
- [CLI Reference](./CLI_REFERENCE.md) - Command line interface


