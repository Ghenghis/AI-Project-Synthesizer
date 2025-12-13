"""
Unit tests for resolution conflict detector module.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.resolution.conflict_detector import (
    ConflictInfo,
    ConflictReport,
)


class TestConflictInfo:
    """Test ConflictInfo dataclass."""
    
    def test_create_conflict_info(self):
        """Should create conflict info."""
        conflict = ConflictInfo(
            package_name="requests",
            conflict_type="version",
            sources={"repo1": ">=2.0", "repo2": "<2.0"},
            description="Version mismatch",
            severity="error",
            resolvable=False
        )
        assert conflict.package_name == "requests"
        assert conflict.conflict_type == "version"
    
    def test_conflict_with_suggestion(self):
        """Should accept resolution suggestion."""
        conflict = ConflictInfo(
            package_name="numpy",
            conflict_type="version",
            sources={"a": "1.0", "b": "2.0"},
            description="Version conflict",
            severity="warning",
            resolvable=True,
            resolution_suggestion="Use numpy>=1.0,<3.0"
        )
        assert conflict.resolution_suggestion is not None


class TestConflictReport:
    """Test ConflictReport dataclass."""
    
    def test_create_report(self):
        """Should create conflict report."""
        report = ConflictReport(
            total_packages=10,
            conflicting_packages=2,
            conflicts=[],
            resolvable_count=0
        )
        assert report.total_packages == 10
    
    def test_has_blocking_conflicts_empty(self):
        """Should return False when no conflicts."""
        report = ConflictReport(
            total_packages=5,
            conflicting_packages=0,
            conflicts=[],
            resolvable_count=0
        )
        assert report.has_blocking_conflicts is False
    
    def test_to_dict(self):
        """Should convert to dictionary."""
        report = ConflictReport(
            total_packages=5,
            conflicting_packages=0,
            conflicts=[],
            resolvable_count=0
        )
        result = report.to_dict()
        assert "summary" in result
        assert "conflicts" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
