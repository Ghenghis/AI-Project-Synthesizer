"""
AI Project Synthesizer - Core Package

Core utilities, configuration, and shared components.
"""

from src.core.config import get_settings, settings
from src.core.exceptions import (
    SynthesizerError,
    DiscoveryError,
    AnalysisError,
    ResolutionError,
    SynthesisError,
    GenerationError,
    RateLimitError,
    AuthenticationError,
)
from src.core.logging import get_logger, setup_logging

__all__ = [
    "get_settings",
    "settings",
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
