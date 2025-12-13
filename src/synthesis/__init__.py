"""
AI Project Synthesizer - Synthesis Layer

Code merging, project scaffolding, and synthesis operations.
"""

from src.synthesis.project_builder import (
    BuildResult,
    ProjectBuilder,
    SynthesisRequest,
    SynthesisResult,
)
from src.synthesis.scaffolder import Scaffolder

__all__ = [
    "ProjectBuilder",
    "SynthesisRequest",
    "SynthesisResult",
    "BuildResult",
    "Scaffolder",
]
