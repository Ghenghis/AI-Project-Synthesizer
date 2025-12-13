"""
AI Synthesizer Recipe System

Pre-configured project templates for common use cases.
"""

from .loader import Recipe, RecipeLoader
from .runner import RecipeRunner

__all__ = ["RecipeLoader", "Recipe", "RecipeRunner"]
