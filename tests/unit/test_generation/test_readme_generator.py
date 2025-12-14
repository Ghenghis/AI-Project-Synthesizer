"""
Unit tests for generation readme generator module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.generation.readme_generator import ReadmeGenerator


class TestReadmeGenerator:
    """Test ReadmeGenerator functionality."""

    def test_create_generator(self):
        """Should create readme generator instance."""
        generator = ReadmeGenerator()
        assert generator is not None

    def test_generator_has_generate_method(self):
        """Should have generate method."""
        generator = ReadmeGenerator()
        assert hasattr(generator, 'generate')

    def test_generator_is_valid(self):
        """Should be a valid generator instance."""
        generator = ReadmeGenerator()
        methods = [m for m in dir(generator) if not m.startswith('_')]
        assert len(methods) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
