"""
Unit tests for generation diagram generator module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.generation.diagram_generator import DiagramGenerator


class TestDiagramGenerator:
    """Test DiagramGenerator functionality."""

    def test_create_generator(self):
        """Should create diagram generator instance."""
        generator = DiagramGenerator()
        assert generator is not None

    def test_generator_has_generate_method(self):
        """Should have generate method."""
        generator = DiagramGenerator()
        assert hasattr(generator, "generate")

    def test_generator_is_valid(self):
        """Should be a valid generator instance."""
        generator = DiagramGenerator()
        methods = [m for m in dir(generator) if not m.startswith("_")]
        assert len(methods) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
