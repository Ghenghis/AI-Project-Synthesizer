# AI Project Synthesizer - Ops Quickstart

> **Version:** 2.0.0 | **Tag:** v2.0.0

Quick reference for running the AI Project Synthesizer in production.

---

## 1. Run MCP Server

```bash
# Activate environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Start MCP server (default mode)
python -m src.mcp_server.server

# Or via CLI
ai-synthesizer serve

# With specific LLM provider
ai-synthesizer serve --llm-provider ollama
ai-synthesizer serve --llm-provider lmstudio
```

### Environment Variables

```bash
# Required
GITHUB_TOKEN=ghp_your_token_here

# Optional LLM providers
OLLAMA_HOST=http://localhost:11434
LMSTUDIO_HOST=http://localhost:1234
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 2. Run Dashboard

```bash
# Start web dashboard
ai-synthesizer dashboard

# Or directly
python -m src.dashboard.app

# Custom port
ai-synthesizer dashboard --port 8080
```

**Default URL:** http://localhost:8000

### Dashboard Views

- `/` - Home (system status)
- `/projects` - Synthesized projects
- `/search` - Repository search
- `/synthesis` - Active synthesis jobs
- `/plugins` - Plugin management
- `/settings` - Configuration
- `/metrics` - Performance metrics

---

## 3. Import n8n Workflows

### Quick Import

1. Open n8n → **Workflows** → **Import from File**
2. Select from `workflows/n8n/`:
   - `github-repo-sweep.json` - Daily GitHub scanning
   - `synthesis-complete.json` - Completion notifications
   - `health-check.json` - System monitoring

### Configure Webhooks

In your `.env`:

```bash
N8N_WEBHOOK_URL=http://your-n8n:5678/webhook
```

The Synthesizer calls these n8n endpoints:
- `/webhook/synthesis-complete`
- `/webhook/error`
- `/webhook/health`

### n8n Credentials Needed

- **Synthesizer API**: `http://localhost:8000`
- **GitHub Token**: Your `GITHUB_TOKEN`
- **Slack Webhook**: For notifications (optional)

---

## 4. Windsurf IDE Integration

### MCP Configuration

Add to your Windsurf MCP config (`~/.windsurf/mcp.json` or IDE settings):

```json
{
  "mcpServers": {
    "ai-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "C:/Users/Admin/AI_Synthesizer",
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}",
        "OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `search_repositories` | Search GitHub/HuggingFace/Kaggle |
| `analyze_repository` | Analyze repo structure and dependencies |
| `check_compatibility` | Check if repos can be merged |
| `resolve_dependencies` | Resolve Python dependencies |
| `synthesize_project` | Merge multiple repos into one |
| `generate_documentation` | Generate docs for a project |
| `get_synthesis_status` | Check synthesis job status |
| `list_templates` | List available project templates |

---

## 5. Health Checks

### API Health

```bash
curl http://localhost:8000/api/health
```

### CLI Health

```bash
ai-synthesizer health
ai-synthesizer check
```

### Expected Response

```json
{
  "status": "healthy",
  "components": {
    "database": "ok",
    "cache": "ok",
    "llm": "ok"
  },
  "version": "2.0.0"
}
```

---

## 6. Common Commands

```bash
# Search repositories
ai-synthesizer search "fastapi mcp server" --platform github

# Analyze a repo
ai-synthesizer analyze https://github.com/owner/repo

# Synthesize project
ai-synthesizer synthesize \
  --repos https://github.com/a/repo1 https://github.com/b/repo2 \
  --name my-project \
  --output ./output

# Interactive wizard
ai-synthesizer wizard

# Use a recipe
ai-synthesizer recipe run mcp-server-starter --name my-mcp

# Check settings
ai-synthesizer settings show
```

---

## 7. Docker Deployment

```bash
# Build and run
cd docker
docker-compose up -d

# Check logs
docker-compose logs -f synthesizer

# Stop
docker-compose down
```

---

## Quick Links

- [Full Documentation](https://github.com/Ghenghis/AI-Project-Synthesizer/tree/master/docs)
- [CHANGELOG](https://github.com/Ghenghis/AI-Project-Synthesizer/blob/master/CHANGELOG.md)
- [API Reference](./API_REFERENCE.md)
- [Dashboard Guide](./DASHBOARD.md)
- [n8n Workflows](./N8N_WORKFLOWS.md)
- [Security Policy](../SECURITY.md)

---

*Last updated: 2025-12-11 | Tag: v2.0.0*
