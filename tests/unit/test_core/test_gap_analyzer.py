"""
Unit tests for core.gap_analyzer module.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["APP_ENV"] = "testing"

from src.core.gap_analyzer import (
    AnalysisReport,
    Gap,
    GapAnalyzer,
    GapCategory,
    GapSeverity,
)


class TestGapSeverity:
    """Test GapSeverity enum."""

    def test_gap_severity_values(self):
        """Test all gap severities are defined."""
        assert GapSeverity.CRITICAL.value == "critical"
        assert GapSeverity.HIGH.value == "high"
        assert GapSeverity.MEDIUM.value == "medium"
        assert GapSeverity.LOW.value == "low"
        assert GapSeverity.INFO.value == "info"


class TestGapCategory:
    """Test GapCategory enum."""

    def test_gap_category_values(self):
        """Test all gap categories are defined."""
        assert GapCategory.IMPORT.value == "import"
        assert GapCategory.CONFIG.value == "config"
        assert GapCategory.FILE.value == "file"
        assert GapCategory.DEPENDENCY.value == "dependency"
        assert GapCategory.API.value == "api"
        assert GapCategory.DATABASE.value == "database"
        assert GapCategory.INTEGRATION.value == "integration"
        assert GapCategory.TEST.value == "test"
        assert GapCategory.DOCUMENTATION.value == "documentation"


class TestGap:
    """Test Gap dataclass."""

    def test_gap_creation(self):
        """Test creating a gap."""
        gap = Gap(
            id="gap_001",
            category=GapCategory.IMPORT,
            severity=GapSeverity.HIGH,
            description="Missing authentication module",
            location="src/auth/",
        )

        assert gap.id == "gap_001"
        assert gap.category == GapCategory.IMPORT
        assert gap.severity == GapSeverity.HIGH
        assert gap.description == "Missing authentication module"
        assert gap.location == "src/auth/"
        assert gap.auto_fixable == False
        assert gap.fixed == False


class TestAnalysisReport:
    """Test AnalysisReport dataclass."""

    def test_analysis_report_creation(self):
        """Test creating an analysis report."""
        gaps = [
            Gap(
                id="gap_001",
                category=GapCategory.TEST,
                severity=GapSeverity.MEDIUM,
                description="No unit tests",
                location="src/utils/",
            )
        ]

        report = AnalysisReport(gaps=gaps, fixed_count=0)

        assert report.total_gaps == 1
        assert report.fixed_count == 0
        assert len(report.gaps) == 1

    def test_analysis_report_to_dict(self):
        """Test converting report to dict."""
        report = AnalysisReport()
        result = report.to_dict()

        assert "timestamp" in result
        assert "total_gaps" in result
        assert "gaps" in result

    def test_analysis_report_to_markdown(self):
        """Test generating markdown report."""
        report = AnalysisReport()
        markdown = report.to_markdown()

        assert "# Gap Analysis Report" in markdown
        assert "Summary" in markdown


class TestGapAnalyzer:
    """Test GapAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = GapAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "analyze")
        assert hasattr(analyzer, "add_gap")

    def test_add_gap(self):
        """Test adding a gap."""
        analyzer = GapAnalyzer()

        gap = Gap(
            id="test_gap",
            category=GapCategory.CONFIG,
            severity=GapSeverity.LOW,
            description="Missing config file",
            location="config/",
        )

        analyzer.add_gap(gap)

        assert len(analyzer._gaps) >= 1

    @pytest.mark.asyncio
    async def test_analyze(self):
        """Test running analysis."""
        analyzer = GapAnalyzer()

        # Run analysis (will run all checks)
        report = await analyzer.analyze(auto_fix=False)

        assert isinstance(report, AnalysisReport)
        # Report should have been created
        assert hasattr(report, "total_gaps")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
