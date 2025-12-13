"""
AI Project Synthesizer - Resolution Layer

Dependency resolution using uv/pip-tools for Python and npm for Node.js.
"""

from src.resolution.conflict_detector import ConflictDetector
from src.resolution.python_resolver import PythonResolver, ResolutionResult
from src.resolution.unified_resolver import UnifiedResolver

__all__ = [
    "PythonResolver",
    "ResolutionResult",
    "ConflictDetector",
    "UnifiedResolver",
]
