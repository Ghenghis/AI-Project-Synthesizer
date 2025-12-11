# MCP Setup Guide for LM Studio, Windsurf & Claude Desktop

Quick setup guide to connect AI Project Synthesizer with your favorite AI tools.

## 🚀 Quick Setup (Automated)

Run the setup script to automatically configure all clients:

```powershell
cd C:\Users\Admin\AI_Synthesizer
.\scripts\setup_mcp_clients.ps1
```

---

## 📋 Manual Setup

### 1️⃣ LM Studio Setup

#### Step 1: Start LM Studio
1. Open LM Studio
2. Load a model (recommended: 7B model like Qwen2.5-Coder-7B)
3. Start the local server (default: `http://localhost:1234`)

#### Step 2: Configure MCP Server
LM Studio supports MCP servers. Add this configuration:

**Option A: Via LM Studio UI**
1. Go to Settings → MCP Servers
2. Click "Add Server"
3. Configure:
   - Name: `ai-project-synthesizer`
   - Command: `python`
   - Args: `-m src.mcp_server.server`
   - Working Directory: `C:\Users\Admin\AI_Synthesizer`

**Option B: Via Config File**
Copy `config/lmstudio_mcp_config.json` to:
```
%USERPROFILE%\.lmstudio\mcp-servers\ai-project-synthesizer.json
```

#### Step 3: Use LM Studio as LLM Provider
The AI Synthesizer can use LM Studio for completions:
```env
LLM_PREFERRED_PROVIDER=lmstudio
LMSTUDIO_HOST=http://localhost:1234
```

---

### 2️⃣ Windsurf Setup

#### Step 1: Create Config Directory
```powershell
mkdir "$env:USERPROFILE\.windsurf" -Force
```

#### Step 2: Create MCP Config
Create `%USERPROFILE%\.windsurf\mcp_config.json`:

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "C:\\Users\\Admin\\AI_Synthesizer\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "C:\\Users\\Admin\\AI_Synthesizer",
      "env": {
        "PYTHONPATH": "C:\\Users\\Admin\\AI_Synthesizer",
        "LLM_PREFERRED_PROVIDER": "lmstudio",
        "LMSTUDIO_HOST": "http://localhost:1234"
      }
    },
    "lmstudio": {
      "command": "npx",
      "args": ["-y", "@lmstudio/mcp-server"]
    }
  }
}
```

#### Step 3: Restart Windsurf
Close and reopen Windsurf to load the MCP servers.

#### Step 4: Verify
In Windsurf, you should see the MCP tools available:
- `search_repositories`
- `analyze_repository`
- `synthesize_project`
- etc.

---

### 3️⃣ Claude Desktop Setup

#### Step 1: Create Config Directory
```powershell
mkdir "$env:APPDATA\Claude" -Force
```

#### Step 2: Create MCP Config
Create `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "C:\\Users\\Admin\\AI_Synthesizer\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "C:\\Users\\Admin\\AI_Synthesizer",
      "env": {
        "PYTHONPATH": "C:\\Users\\Admin\\AI_Synthesizer",
        "GITHUB_TOKEN": "your_github_token_here",
        "LLM_PREFERRED_PROVIDER": "lmstudio",
        "LMSTUDIO_HOST": "http://localhost:1234"
      }
    },
    "lmstudio": {
      "command": "npx",
      "args": ["-y", "@lmstudio/mcp-server"]
    }
  }
}
```

#### Step 3: Restart Claude Desktop
Close and reopen Claude Desktop to load the MCP servers.

#### Step 4: Verify
Ask Claude: "What MCP tools are available?"

---

## 🔧 Configuration Files Location

| Client | Config File Path |
|--------|-----------------|
| **Windsurf** | `%USERPROFILE%\.windsurf\mcp_config.json` |
| **Claude Desktop** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **LM Studio** | `%USERPROFILE%\.lmstudio\mcp-servers\*.json` |

---

## 🎯 Using Both MCP Servers Together

With this setup, you get TWO MCP servers:

### 1. AI Project Synthesizer
Tools for repository search, code analysis, and project synthesis:
- `search_repositories` - Search GitHub, HuggingFace, Kaggle
- `analyze_repository` - Analyze code structure
- `check_compatibility` - Check dependency compatibility
- `synthesize_project` - Generate new projects
- `generate_documentation` - Create docs

### 2. LM Studio MCP Server
Direct access to your local LLM:
- Chat completions
- Code generation
- Text analysis

---

## 🔄 Workflow Example

1. **Start LM Studio** with a 7B model loaded
2. **Open Windsurf** or **Claude Desktop**
3. **Use AI Synthesizer tools**:
   ```
   Search for machine learning repositories on GitHub
   ```
4. **AI Synthesizer** searches using the MCP tool
5. **LM Studio** provides local LLM completions for analysis

---

## 🐛 Troubleshooting

### MCP Server Not Starting

```powershell
# Test the server directly
cd C:\Users\Admin\AI_Synthesizer
.\.venv\Scripts\python.exe -m src.mcp_server.server
```

### LM Studio Not Connected

```powershell
# Check if LM Studio server is running
curl http://localhost:1234/v1/models
```

### Tools Not Appearing

1. Check config file syntax (valid JSON)
2. Restart the client application
3. Check logs for errors

### Permission Issues

Run PowerShell as Administrator if needed:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📊 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PREFERRED_PROVIDER` | LLM provider to use | `ollama` |
| `LMSTUDIO_HOST` | LM Studio server URL | `http://localhost:1234` |
| `LLM_MODEL_SIZE_PREFERENCE` | Model size tier | `medium` |
| `GITHUB_TOKEN` | GitHub API token | Required |
| `PYTHONPATH` | Python module path | Project root |

---

## 🎉 Success Checklist

- [ ] LM Studio running with model loaded
- [ ] Windsurf config file created
- [ ] Claude Desktop config file created
- [ ] Applications restarted
- [ ] MCP tools visible in client
- [ ] Test search works

---

## 📚 Related Documentation

- [MCP Client Support](./MCP_CLIENT_SUPPORT.md) - All supported clients
- [Model Quick Start](./MODEL_QUICK_START.md) - Model configuration
- [Enterprise Deployment](./ENTERPRISE_DEPLOYMENT.md) - Production setup
