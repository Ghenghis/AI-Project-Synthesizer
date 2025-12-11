"""
AI Project Synthesizer - Plugin System

Extensible plugin architecture for:
- Custom platform integrations (new search sources)
- Custom synthesis strategies
- Custom analysis tools
- Custom voice providers

Plugins are discovered from:
1. Built-in plugins (src/plugins/)
2. User plugins (~/.synthesizer/plugins/)
3. Project plugins (.synthesizer/plugins/)
"""

import asyncio
import importlib
import importlib.util
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Type, Callable
from enum import Enum

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class PluginType(str, Enum):
    """Types of plugins."""
    PLATFORM = "platform"      # New search platforms
    SYNTHESIS = "synthesis"    # Synthesis strategies
    ANALYSIS = "analysis"      # Code analysis tools
    VOICE = "voice"           # Voice providers
    LLM = "llm"               # LLM providers
    HOOK = "hook"             # Event hooks


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: str = ""
    plugin_type: PluginType = PluginType.PLATFORM
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)


class Plugin(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with config. Override if needed."""
        return True
    
    async def shutdown(self) -> None:
        """Cleanup on shutdown. Override if needed."""
        pass


class PlatformPlugin(Plugin):
    """
    Plugin for adding new search platforms.
    
    Example:
        class GitLabPlugin(PlatformPlugin):
            @property
            def metadata(self):
                return PluginMetadata(
                    name="gitlab",
                    version="1.0.0",
                    description="GitLab repository search",
                    plugin_type=PluginType.PLATFORM,
                )
            
            async def search(self, query, max_results=10):
                # Implement GitLab search
                ...
    """
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search the platform."""
        pass
    
    async def get_details(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific item."""
        return None
    
    async def download(self, identifier: str, destination: Path) -> bool:
        """Download an item."""
        return False


class SynthesisPlugin(Plugin):
    """Plugin for custom synthesis strategies."""
    
    @abstractmethod
    async def synthesize(
        self,
        sources: List[Dict[str, Any]],
        output_path: Path,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synthesize project from sources."""
        pass


class AnalysisPlugin(Plugin):
    """Plugin for custom code analysis."""
    
    @abstractmethod
    async def analyze(self, path: Path) -> Dict[str, Any]:
        """Analyze code at path."""
        pass


class HookPlugin(Plugin):
    """Plugin for event hooks."""
    
    async def on_search_start(self, query: str) -> None:
        """Called before search."""
        pass
    
    async def on_search_complete(self, query: str, results: List[Any]) -> None:
        """Called after search."""
        pass
    
    async def on_synthesis_start(self, project_name: str) -> None:
        """Called before synthesis."""
        pass
    
    async def on_synthesis_complete(self, project_path: Path) -> None:
        """Called after synthesis."""
        pass


class PluginManager:
    """
    Manages plugin discovery, loading, and lifecycle.
    
    Usage:
        manager = PluginManager()
        await manager.discover_plugins()
        
        # Get all platform plugins
        platforms = manager.get_plugins(PluginType.PLATFORM)
        
        # Search across all platforms
        for plugin in platforms:
            results = await plugin.search("machine learning")
    """
    
    def __init__(self):
        """Initialize plugin manager."""
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_paths: List[Path] = [
            Path(__file__).parent.parent / "plugins",  # Built-in
            Path.home() / ".synthesizer" / "plugins",   # User
            Path.cwd() / ".synthesizer" / "plugins",    # Project
        ]
    
    async def discover_plugins(self) -> int:
        """
        Discover and load all plugins.
        
        Returns:
            Number of plugins loaded
        """
        count = 0
        
        for plugin_dir in self._plugin_paths:
            if not plugin_dir.exists():
                continue
            
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                
                try:
                    plugin = await self._load_plugin_file(plugin_file)
                    if plugin:
                        self._plugins[plugin.metadata.name] = plugin
                        count += 1
                        secure_logger.info(f"Loaded plugin: {plugin.metadata.name}")
                except Exception as e:
                    secure_logger.error(f"Failed to load plugin {plugin_file}: {e}")
        
        return count
    
    async def _load_plugin_file(self, path: Path) -> Optional[Plugin]:
        """Load a plugin from file."""
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        
        # Find Plugin subclass
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type) and
                issubclass(obj, Plugin) and
                obj is not Plugin and
                not name.startswith("_")
            ):
                # Check if it's a concrete class (not abstract base)
                if not any(
                    getattr(obj, m, None) is getattr(Plugin, m, None)
                    for m in ['metadata']
                    if hasattr(Plugin, m)
                ):
                    return obj()
        
        return None
    
    def register_plugin(self, plugin: Plugin) -> bool:
        """Register a plugin instance."""
        name = plugin.metadata.name
        if name in self._plugins:
            secure_logger.warning(f"Plugin {name} already registered")
            return False
        
        self._plugins[name] = plugin
        secure_logger.info(f"Registered plugin: {name}")
        return True
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        return self._plugins.get(name)
    
    def get_plugins(self, plugin_type: Optional[PluginType] = None) -> List[Plugin]:
        """Get all plugins, optionally filtered by type."""
        plugins = list(self._plugins.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.metadata.plugin_type == plugin_type]
        
        return plugins
    
    async def initialize_all(self, config: Dict[str, Any] = None) -> int:
        """Initialize all plugins."""
        config = config or {}
        count = 0
        
        for name, plugin in self._plugins.items():
            try:
                plugin_config = config.get(name, {})
                if await plugin.initialize(plugin_config):
                    count += 1
            except Exception as e:
                secure_logger.error(f"Failed to initialize plugin {name}: {e}")
        
        return count
    
    async def shutdown_all(self) -> None:
        """Shutdown all plugins."""
        for name, plugin in self._plugins.items():
            try:
                await plugin.shutdown()
            except Exception as e:
                secure_logger.error(f"Error shutting down plugin {name}: {e}")
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins."""
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "type": p.metadata.plugin_type.value,
                "description": p.metadata.description,
            }
            for p in self._plugins.values()
        ]


# Global plugin manager
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


# Example built-in plugins directory
PLUGINS_DIR = Path(__file__).parent.parent / "plugins"
PLUGINS_DIR.mkdir(exist_ok=True)
