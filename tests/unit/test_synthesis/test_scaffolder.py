"""
Unit tests for synthesis scaffolder module.
"""

import pytest

from src.synthesis.scaffolder import (
    Scaffolder,
    ScaffoldResult,
)


class TestScaffoldResult:
    """Test ScaffoldResult dataclass."""

    def test_create_scaffold_result(self):
        """Should create scaffold result."""
        result = ScaffoldResult(success=True, files_created=5)
        assert result.success is True
        assert result.files_created == 5

    def test_result_defaults(self):
        """Should have correct defaults."""
        result = ScaffoldResult(success=False)
        assert result.files_created == 0
        assert result.warnings == []


class TestScaffolder:
    """Test Scaffolder functionality."""

    def test_create_scaffolder(self):
        """Should create scaffolder instance."""
        scaffolder = Scaffolder()
        assert scaffolder is not None

    def test_scaffolder_has_scaffold_method(self):
        """Should have scaffold method."""
        scaffolder = Scaffolder()
        assert hasattr(scaffolder, "scaffold")

    def test_templates_exist(self):
        """Should have template definitions."""
        assert hasattr(Scaffolder, "TEMPLATES")
        assert "python-default" in Scaffolder.TEMPLATES
        assert "python-fastapi" in Scaffolder.TEMPLATES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
