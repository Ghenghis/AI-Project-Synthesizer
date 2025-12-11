# AI Project Synthesizer - Plugin System

> **Version:** 2.0.0 | **Status:** Production Ready

The plugin system allows extending the AI Project Synthesizer with custom functionality without modifying core code.

---

## Overview

Plugins can extend:
- **Platform Discovery** - Add new code hosting platforms
- **Analysis** - Custom code analysis and metrics
- **Synthesis** - Custom project generation strategies
- **Post-Processing** - Custom documentation, testing, deployment

---

## Plugin Types

### 1. Platform Plugins

Add support for new code hosting platforms.

```python
from src.core.plugins import PlatformPlugin, PluginMetadata

class GitLabPlugin(PlatformPlugin):
    """Plugin for GitLab repository discovery."""
    
    metadata = PluginMetadata(
        id="gitlab",
        name="GitLab Platform",
        version="1.0.0",
        description="Search and analyze GitLab repositories",
        author="Your Name",
    )
    
    def supports(self, url: str) -> bool:
        """Check if this plugin handles the given URL."""
        return "gitlab.com" in url or "gitlab" in url
    
    async def search(self, query: str, **kwargs) -> list:
        """Search for repositories."""
        # Implementation here
        pass
    
    async def analyze(self, repo_url: str) -> dict:
        """Analyze a repository."""
        # Implementation here
        pass
```

### 2. Analysis Plugins

Add custom code analysis capabilities.

```python
from src.core.plugins import AnalysisPlugin, PluginMetadata

class SecurityScanPlugin(AnalysisPlugin):
    """Plugin for security vulnerability scanning."""
    
    metadata = PluginMetadata(
        id="security-scan",
        name="Security Scanner",
        version="1.0.0",
        description="Scan code for security vulnerabilities",
    )
    
    async def analyze(self, project_path: str) -> dict:
        """Run security analysis on a project."""
        return {
            "vulnerabilities": [],
            "score": 100,
            "recommendations": [],
        }
```

### 3. Synthesis Plugins

Customize project generation.

```python
from src.core.plugins import SynthesisPlugin, PluginMetadata

class MonorepoPlugin(SynthesisPlugin):
    """Plugin for monorepo project structure."""
    
    metadata = PluginMetadata(
        id="monorepo",
        name="Monorepo Generator",
        version="1.0.0",
        description="Generate monorepo project structures",
    )
    
    async def synthesize(self, config: dict) -> dict:
        """Generate a monorepo structure."""
        # Implementation here
        pass
```

---

## Plugin Locations

Plugins are discovered from these locations:

| Location | Description |
|----------|-------------|
| `src/plugins/` | Built-in plugins (shipped with the project) |
| `~/.synthesizer/plugins/` | User-installed plugins |
| `./plugins/` | Project-local plugins |

---

## Installing Plugins

### From PyPI

```bash
pip install ai-synthesizer-plugin-gitlab
```

### From Git

```bash
pip install git+https://github.com/user/synthesizer-plugin.git
```

### Manual Installation

1. Create a Python file in `~/.synthesizer/plugins/`
2. Implement the plugin class
3. Restart the synthesizer

---

## Plugin Configuration

### Enable/Disable Plugins

In your `.env` or config:

```bash
# Enable specific plugins
ENABLED_PLUGINS=gitlab,security-scan,monorepo

# Disable specific plugins
DISABLED_PLUGINS=legacy-analyzer
```

### Plugin Settings

Plugins can have their own configuration:

```bash
# GitLab plugin settings
GITLAB_URL=https://gitlab.company.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxx
```

---

## Plugin API Reference

### PluginMetadata

```python
@dataclass
class PluginMetadata:
    id: str              # Unique identifier
    name: str            # Display name
    version: str         # Semantic version
    description: str     # Short description
    author: str = ""     # Author name
    homepage: str = ""   # Project URL
    requires: list = []  # Dependencies
```

### Base Plugin Class

```python
class BasePlugin:
    metadata: PluginMetadata
    
    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass
    
    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass
    
    def get_config(self) -> dict:
        """Get plugin configuration."""
        return {}
```

---

## Plugin Manager

The `PluginManager` handles plugin lifecycle:

```python
from src.core.plugins import PluginManager

manager = PluginManager()

# List all plugins
plugins = manager.list_plugins()

# Get a specific plugin
gitlab = manager.get_plugin("gitlab")

# Enable/disable plugins
manager.enable_plugin("gitlab")
manager.disable_plugin("legacy-analyzer")

# Reload plugins
manager.reload_plugins()
```

---

## Dashboard Integration

The web dashboard shows plugin status at `/api/plugins`:

```json
{
  "plugins": [
    {
      "id": "gitlab",
      "name": "GitLab Platform",
      "version": "1.0.0",
      "enabled": true,
      "status": "active"
    }
  ]
}
```

---

## Creating a Plugin Package

For distributable plugins:

```
my-plugin/
├── pyproject.toml
├── README.md
├── src/
│   └── my_plugin/
│       ├── __init__.py
│       └── plugin.py
└── tests/
    └── test_plugin.py
```

**pyproject.toml:**

```toml
[project]
name = "ai-synthesizer-plugin-myplugin"
version = "1.0.0"

[project.entry-points."ai_synthesizer.plugins"]
myplugin = "my_plugin.plugin:MyPlugin"
```

---

## Best Practices

1. **Keep plugins focused** - One plugin, one responsibility
2. **Handle errors gracefully** - Don't crash the main application
3. **Use async where possible** - For I/O operations
4. **Document your plugin** - Include usage examples
5. **Test thoroughly** - Include unit tests
6. **Version properly** - Use semantic versioning

---

## Example: Complete Plugin

```python
"""
Example: Bitbucket Platform Plugin
"""

from typing import List, Dict, Any
from src.core.plugins import PlatformPlugin, PluginMetadata
import aiohttp


class BitbucketPlugin(PlatformPlugin):
    """Plugin for Bitbucket repository discovery."""
    
    metadata = PluginMetadata(
        id="bitbucket",
        name="Bitbucket Platform",
        version="1.0.0",
        description="Search and analyze Bitbucket repositories",
        author="AI Synthesizer Team",
        homepage="https://github.com/Ghenghis/AI-Project-Synthesizer",
    )
    
    def __init__(self):
        self.base_url = "https://api.bitbucket.org/2.0"
        self.session = None
    
    def on_load(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()
    
    def on_unload(self) -> None:
        """Cleanup HTTP session."""
        if self.session:
            # Note: Should be awaited in async context
            pass
    
    def supports(self, url: str) -> bool:
        """Check if URL is a Bitbucket repository."""
        return "bitbucket.org" in url
    
    async def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search Bitbucket repositories."""
        async with self.session.get(
            f"{self.base_url}/repositories",
            params={"q": f'name~"{query}"', "pagelen": max_results}
        ) as response:
            data = await response.json()
            return data.get("values", [])
    
    async def analyze(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a Bitbucket repository."""
        # Parse owner/repo from URL
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        
        async with self.session.get(
            f"{self.base_url}/repositories/{owner}/{repo}"
        ) as response:
            return await response.json()
```

---

## Troubleshooting

### Plugin Not Loading

1. Check plugin location is correct
2. Verify plugin class inherits from correct base
3. Check for import errors in plugin code
4. Review logs for error messages

### Plugin Conflicts

1. Check for duplicate plugin IDs
2. Verify dependency versions
3. Disable conflicting plugins

### Performance Issues

1. Use async operations for I/O
2. Implement caching where appropriate
3. Profile plugin code for bottlenecks
