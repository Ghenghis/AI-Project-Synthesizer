# MCP Client Support Guide

The AI Project Synthesizer MCP Server is compatible with **any client that implements the Model Context Protocol (MCP)**. This guide covers setup for all major supported clients.

## 📋 Supported MCP Clients Overview

| Client | Type | Status | Platform |
|--------|------|--------|----------|
| **Windsurf** | IDE | ✅ Full Support | Windows, macOS, Linux |
| **Claude Desktop** | App | ✅ Full Support | Windows, macOS |
| **VS Code + Continue** | IDE Extension | ✅ Full Support | Windows, macOS, Linux |
| **VS Code + Cline** | IDE Extension | ✅ Full Support | Windows, macOS, Linux |
| **Cursor** | IDE | ✅ Full Support | Windows, macOS, Linux |
| **LM Studio** | App | ✅ Full Support | Windows, macOS, Linux |
| **JetBrains IDEs** | IDE Plugin | ✅ Full Support | Windows, macOS, Linux |
| **Neovim** | Editor | ✅ Full Support | Windows, macOS, Linux |
| **Vim** | Editor | ⚠️ Via Plugin | Windows, macOS, Linux |
| **Emacs** | Editor | ⚠️ Via Plugin | Windows, macOS, Linux |
| **Zed** | IDE | ✅ Full Support | macOS, Linux |
| **Sourcegraph Cody** | Extension | ✅ Full Support | Web, VS Code |
| **Open Interpreter** | CLI | ✅ Full Support | Windows, macOS, Linux |
| **Custom MCP Clients** | Any | ✅ Full Support | Any |

---

## 🌊 Windsurf IDE

### Configuration
Create or edit `~/.windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "C:\\Users\\Admin\\AI_Synthesizer",
      "env": {
        "PYTHONPATH": "C:\\Users\\Admin\\AI_Synthesizer"
      }
    }
  }
}
```

### Windows Path
```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "C:\\Users\\Admin\\AI_Synthesizer\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "C:\\Users\\Admin\\AI_Synthesizer"
    }
  }
}
```

---

## 🤖 Claude Desktop

### Configuration
Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer",
      "env": {
        "GITHUB_TOKEN": "your_github_token"
      }
    }
  }
}
```

---

## 💻 VS Code + Continue Extension

### Installation
1. Install [Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue) extension
2. Configure MCP in `~/.continue/config.json`:

```json
{
  "models": [...],
  "mcpServers": [
    {
      "name": "ai-project-synthesizer",
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer"
    }
  ]
}
```

---

## 🔧 VS Code + Cline Extension

### Installation
1. Install [Cline](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) extension
2. Open Cline settings and add MCP server:

```json
{
  "cline.mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer"
    }
  }
}
```

---

## 🖱️ Cursor IDE

### Configuration
Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer",
      "env": {
        "PYTHONPATH": "/path/to/AI_Synthesizer"
      }
    }
  }
}
```

---

## 🎨 LM Studio

### MCP Server Integration
LM Studio supports MCP servers natively. Configure in Settings → MCP:

```json
{
  "servers": [
    {
      "name": "ai-project-synthesizer",
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "workingDirectory": "/path/to/AI_Synthesizer"
    }
  ]
}
```

### Alternative: HTTP Mode
Run the server in HTTP mode for LM Studio:

```bash
python -m src.mcp_server.http_server --port 8080
```

---

## 🧠 JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)

### Plugin Installation
1. Install the **AI Assistant** or **MCP Client** plugin from JetBrains Marketplace
2. Go to Settings → Tools → MCP Servers

### Configuration
Add to `~/.config/JetBrains/<IDE>/options/mcp.xml`:

```xml
<application>
  <component name="McpSettings">
    <servers>
      <server>
        <name>ai-project-synthesizer</name>
        <command>python</command>
        <args>-m src.mcp_server.server</args>
        <workingDirectory>/path/to/AI_Synthesizer</workingDirectory>
      </server>
    </servers>
  </component>
</application>
```

### Supported JetBrains IDEs
- **IntelliJ IDEA** (Ultimate/Community)
- **PyCharm** (Professional/Community)
- **WebStorm**
- **PhpStorm**
- **RubyMine**
- **GoLand**
- **CLion**
- **Rider**
- **DataGrip**
- **Android Studio**

---

## 📝 Neovim

### Plugin: nvim-mcp
Install using your preferred plugin manager:

```lua
-- lazy.nvim
{
  "mcp-nvim/nvim-mcp",
  config = function()
    require("mcp").setup({
      servers = {
        ["ai-project-synthesizer"] = {
          command = "python",
          args = { "-m", "src.mcp_server.server" },
          cwd = "/path/to/AI_Synthesizer",
        },
      },
    })
  end,
}
```

### Alternative: mcp.nvim
```lua
-- packer.nvim
use {
  'someone/mcp.nvim',
  config = function()
    require('mcp').setup({
      servers = {
        {
          name = "ai-project-synthesizer",
          cmd = { "python", "-m", "src.mcp_server.server" },
          root_dir = "/path/to/AI_Synthesizer",
        }
      }
    })
  end
}
```

---

## 🖥️ Vim

### Via vim-mcp Plugin
Add to your `.vimrc`:

```vim
" Using vim-plug
Plug 'mcp-vim/vim-mcp'

" Configuration
let g:mcp_servers = {
  \ 'ai-project-synthesizer': {
  \   'command': 'python',
  \   'args': ['-m', 'src.mcp_server.server'],
  \   'cwd': '/path/to/AI_Synthesizer'
  \ }
  \}
```

---

## 🦬 Emacs

### Via mcp.el Package
Add to your Emacs config:

```elisp
(use-package mcp
  :config
  (setq mcp-servers
        '(("ai-project-synthesizer"
           :command "python"
           :args ("-m" "src.mcp_server.server")
           :cwd "/path/to/AI_Synthesizer"))))
```

---

## ⚡ Zed Editor

### Configuration
Edit `~/.config/zed/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "ai-project-synthesizer": {
        "command": "python",
        "args": ["-m", "src.mcp_server.server"],
        "cwd": "/path/to/AI_Synthesizer"
      }
    }
  }
}
```

---

## 🔍 Sourcegraph Cody

### VS Code Extension
Configure in Cody settings:

```json
{
  "cody.experimental.mcp.servers": [
    {
      "name": "ai-project-synthesizer",
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer"
    }
  ]
}
```

---

## 🖥️ Open Interpreter

### Configuration
```python
from interpreter import interpreter

interpreter.mcp_servers = [
    {
        "name": "ai-project-synthesizer",
        "command": "python",
        "args": ["-m", "src.mcp_server.server"],
        "cwd": "/path/to/AI_Synthesizer"
    }
]
```

### CLI Mode
```bash
interpreter --mcp-server "python -m src.mcp_server.server"
```

---

## 🔧 Custom MCP Client Integration

### Python Client
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_server.server"],
        cwd="/path/to/AI_Synthesizer"
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            
            # Call a tool
            result = await session.call_tool(
                "search_repositories",
                {"query": "machine learning", "max_results": 5}
            )
            print(result)

asyncio.run(main())
```

### Node.js Client
```javascript
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

async function main() {
  const transport = new StdioClientTransport({
    command: "python",
    args: ["-m", "src.mcp_server.server"],
    cwd: "/path/to/AI_Synthesizer"
  });
  
  const client = new Client({ name: "my-client", version: "1.0.0" });
  await client.connect(transport);
  
  // List tools
  const tools = await client.listTools();
  console.log("Tools:", tools);
  
  // Call tool
  const result = await client.callTool("search_repositories", {
    query: "web framework",
    max_results: 10
  });
  console.log(result);
}

main();
```

---

## 🌐 HTTP/SSE Transport (Universal)

For clients that don't support stdio, run the server in HTTP mode:

### Start HTTP Server
```bash
python -m src.mcp_server.http_server --host 0.0.0.0 --port 8080
```

### Connect via HTTP
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

---

## 📊 Available MCP Tools

All clients have access to these tools:

| Tool | Description |
|------|-------------|
| `search_repositories` | Search GitHub, HuggingFace, Kaggle, ArXiv |
| `analyze_repository` | Analyze code structure and quality |
| `check_compatibility` | Check dependency compatibility |
| `resolve_dependencies` | Resolve and merge dependencies |
| `synthesize_project` | Generate new project from sources |
| `generate_documentation` | Generate README and docs |
| `get_synthesis_status` | Check synthesis job status |

---

## 🔒 Security Considerations

### API Keys
Never commit API keys. Use environment variables:

```bash
export GITHUB_TOKEN=your_token
export HUGGINGFACE_TOKEN=your_token
```

### Network Security
- Use localhost for local development
- Enable TLS for remote connections
- Implement authentication for production

---

## 🐛 Troubleshooting

### Common Issues

**Server not starting:**
```bash
# Check Python path
which python
python --version

# Test server directly
python -m src.mcp_server.server
```

**Connection refused:**
```bash
# Check if server is running
ps aux | grep mcp_server

# Check port availability
netstat -an | grep 8080
```

**Tools not appearing:**
```bash
# Verify MCP protocol
python -c "from mcp.server import Server; print('MCP OK')"
```

### Debug Mode
Enable debug logging:
```bash
DEBUG=true LOG_LEVEL=DEBUG python -m src.mcp_server.server
```

---

## 📚 Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/sdk)
- [AI Project Synthesizer Docs](./ENTERPRISE_DEPLOYMENT.md)
