"""
AI Project Synthesizer - Core Package

Core utilities, configuration, and shared components.
"""

from src.core.config import get_settings
from src.core.exceptions import (
    AnalysisError,
    AuthenticationError,
    DiscoveryError,
    GenerationError,
    RateLimitError,
    ResolutionError,
    SynthesisError,
    SynthesizerError,
)
from src.core.logging import get_logger, setup_logging

__all__ = [
    "get_settings",
    "get_logger",
    "setup_logging",
    "SynthesizerError",
    "DiscoveryError",
    "AnalysisError",
    "ResolutionError",
    "SynthesisError",
    "GenerationError",
    "RateLimitError",
    "AuthenticationError",
]
