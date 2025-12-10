"""
AI Project Synthesizer

Intelligent multi-repository code synthesis platform for Windsurf IDE.

This package provides:
- Multi-platform repository discovery
- Code analysis and dependency resolution
- Intelligent code synthesis
- Automated documentation generation

Example:
    from src.mcp.server import main
    import asyncio
    asyncio.run(main())
"""

__version__ = "1.0.0"
__author__ = "AI Synthesizer Team"

from src.core.config import get_settings, Settings
from src.core.exceptions import SynthesizerError

__all__ = [
    "__version__",
    "get_settings",
    "Settings",
    "SynthesizerError",
]
