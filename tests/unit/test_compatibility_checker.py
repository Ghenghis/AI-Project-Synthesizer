"""
Unit tests for Compatibility Checker edge cases.

Tests conflict detection, version resolution, and edge cases.
"""

from __future__ import annotations

import pytest

from src.analysis.compatibility_checker import (
    CompatibilityChecker,
    RepositoryInfo,
    CompatibilityMatrix,
    CompatibilityIssue,
)
from src.analysis.dependency_analyzer import DependencyGraph, Dependency


class TestCompatibilityCheckerInit:
    """Test CompatibilityChecker initialization."""

    def test_init(self):
        """Test checker initializes correctly."""
        checker = CompatibilityChecker()
        assert checker.dep_analyzer is not None

    def test_python_versions_defined(self):
        """Test Python versions are defined."""
        assert "3.11" in CompatibilityChecker.PYTHON_VERSIONS
        assert "3.12" in CompatibilityChecker.PYTHON_VERSIONS
        assert "3.13" in CompatibilityChecker.PYTHON_VERSIONS

    def test_license_compatibility_defined(self):
        """Test license compatibility matrix is defined."""
        assert "MIT" in CompatibilityChecker.LICENSE_COMPATIBILITY
        assert "Apache-2.0" in CompatibilityChecker.LICENSE_COMPATIBILITY


class TestPythonVersionParsing:
    """Test Python version requirement parsing."""

    def test_parse_simple_version(self):
        """Test parsing simple version requirement."""
        checker = CompatibilityChecker()
        assert checker._parse_python_requirement(">=3.8") == "3.8"
        assert checker._parse_python_requirement(">=3.11") == "3.11"

    def test_parse_caret_version(self):
        """Test parsing caret version requirement."""
        checker = CompatibilityChecker()
        assert checker._parse_python_requirement("^3.9") == "3.9"

    def test_parse_tilde_version(self):
        """Test parsing tilde version requirement."""
        checker = CompatibilityChecker()
        assert checker._parse_python_requirement("~3.10") == "3.10"

    def test_parse_no_version(self):
        """Test parsing string with no version."""
        checker = CompatibilityChecker()
        assert checker._parse_python_requirement("python") is None

    def test_parse_complex_version(self):
        """Test parsing complex version string."""
        checker = CompatibilityChecker()
        assert checker._parse_python_requirement(">=3.8,<3.12") == "3.8"


class TestVersionComparison:
    """Test version comparison logic."""

    def test_version_less_than(self):
        """Test version less than comparison."""
        checker = CompatibilityChecker()
        assert checker._version_less_than("3.8", "3.9") is True
        assert checker._version_less_than("3.11", "3.10") is False
        assert checker._version_less_than("3.10", "3.10") is False

    def test_version_with_patch(self):
        """Test version comparison with patch numbers."""
        checker = CompatibilityChecker()
        assert checker._version_less_than("3.8.1", "3.8.2") is True
        assert checker._version_less_than("3.8.10", "3.8.2") is False

    def test_invalid_version(self):
        """Test handling of invalid version strings."""
        checker = CompatibilityChecker()
        assert checker._version_less_than("invalid", "3.8") is False
        assert checker._version_less_than("3.8", "invalid") is False


class TestVersionOverlap:
    """Test version overlap detection."""

    def test_exact_versions_match(self):
        """Test matching exact versions overlap."""
        checker = CompatibilityChecker()
        assert checker._versions_might_overlap(["==1.0.0", "==1.0.0"]) is True

    def test_exact_versions_conflict(self):
        """Test conflicting exact versions don't overlap."""
        checker = CompatibilityChecker()
        assert checker._versions_might_overlap(["==1.0.0", "==2.0.0"]) is False

    def test_range_versions_assume_overlap(self):
        """Test range versions assume possible overlap."""
        checker = CompatibilityChecker()
        assert checker._versions_might_overlap([">=1.0", ">=2.0"]) is True
        assert checker._versions_might_overlap([">=1.0,<2.0", ">=1.5"]) is True


class TestCompatibilityCheck:
    """Test full compatibility checking."""

    @pytest.mark.asyncio
    async def test_empty_repositories(self):
        """Test checking empty repository list."""
        checker = CompatibilityChecker()
        result = await checker.check([], target_python="3.11")

        assert isinstance(result, CompatibilityMatrix)
        assert result.overall_compatible is True
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_single_repository(self):
        """Test checking single repository."""
        checker = CompatibilityChecker()
        repo = RepositoryInfo(
            url="https://github.com/test/repo",
            name="test-repo",
            python_version=">=3.9",
        )

        result = await checker.check([repo], target_python="3.11")

        assert result.overall_compatible is True
        assert "test-repo" in result.repositories

    @pytest.mark.asyncio
    async def test_python_version_warning(self):
        """Test Python version incompatibility warning."""
        checker = CompatibilityChecker()
        repo = RepositoryInfo(
            url="https://github.com/test/repo",
            name="test-repo",
            python_version=">=3.12",
        )

        result = await checker.check([repo], target_python="3.11")

        # Should have a warning about Python version
        python_issues = [i for i in result.issues if i.category == "python_version"]
        assert len(python_issues) >= 1

    @pytest.mark.asyncio
    async def test_mixed_languages_info(self):
        """Test mixed language projects generate info."""
        checker = CompatibilityChecker()
        repos = [
            RepositoryInfo(
                url="https://github.com/test/py-repo",
                name="py-repo",
                languages={"python": 90.0, "shell": 10.0},
            ),
            RepositoryInfo(
                url="https://github.com/test/js-repo",
                name="js-repo",
                languages={"javascript": 95.0, "css": 5.0},
            ),
        ]

        result = await checker.check(repos, target_python="3.11")

        # Should have an info about mixed languages
        lang_issues = [i for i in result.issues if i.category == "language"]
        assert len(lang_issues) >= 1
        assert lang_issues[0].severity == "info"


class TestDependencyConflictDetection:
    """Test dependency conflict detection."""

    def _create_dependency(self, name: str, version: str) -> Dependency:
        """Create a test dependency."""
        return Dependency(
            name=name,
            version_spec=version,
            is_dev=False,
            source_file="pyproject.toml",
        )

    def _create_repo_with_deps(
        self, name: str, deps: list[tuple[str, str]]
    ) -> RepositoryInfo:
        """Create a repository with dependencies."""
        dep_list = [self._create_dependency(n, v) for n, v in deps]
        dep_graph = DependencyGraph(
            direct=dep_list,
        )
        return RepositoryInfo(
            url=f"https://github.com/test/{name}",
            name=name,
            dependencies=dep_graph,
        )

    @pytest.mark.asyncio
    async def test_no_dependency_conflicts(self):
        """Test repositories with no conflicts."""
        checker = CompatibilityChecker()
        repos = [
            self._create_repo_with_deps("repo1", [("requests", ">=2.28")]),
            self._create_repo_with_deps("repo2", [("flask", ">=2.0")]),
        ]

        result = await checker.check(repos, target_python="3.11")

        dep_issues = [i for i in result.issues if i.category == "dependency"]
        assert len(dep_issues) == 0

    @pytest.mark.asyncio
    async def test_shared_dependencies_detected(self):
        """Test shared dependencies are detected."""
        checker = CompatibilityChecker()
        repos = [
            self._create_repo_with_deps("repo1", [("requests", ">=2.28")]),
            self._create_repo_with_deps("repo2", [("requests", ">=2.25")]),
        ]

        result = await checker.check(repos, target_python="3.11")

        # requests should be in shared dependencies
        assert "requests" in result.shared_dependencies

    @pytest.mark.asyncio
    async def test_conflicting_exact_versions(self):
        """Test conflicting exact versions are detected."""
        checker = CompatibilityChecker()
        repos = [
            self._create_repo_with_deps("repo1", [("numpy", "==1.24.0")]),
            self._create_repo_with_deps("repo2", [("numpy", "==1.25.0")]),
        ]

        result = await checker.check(repos, target_python="3.11")

        # Should have a dependency conflict error
        dep_issues = [i for i in result.issues if i.category == "dependency"]
        assert len(dep_issues) >= 1
        assert dep_issues[0].severity == "error"
        assert not result.overall_compatible


class TestCompatibilityMatrixSerialization:
    """Test CompatibilityMatrix to_dict serialization."""

    def test_to_dict_basic(self):
        """Test basic to_dict serialization."""
        matrix = CompatibilityMatrix(
            repositories=["repo1", "repo2"],
            overall_compatible=True,
            python_version="3.11",
            issues=[],
            shared_dependencies=["requests"],
            all_dependencies=["requests", "flask", "numpy"],
        )

        result = matrix.to_dict()

        assert result["compatible"] is True
        assert result["repositories"] == ["repo1", "repo2"]
        assert result["python_version"] == "3.11"
        assert result["issue_count"] == 0
        assert result["shared_dependencies"] == ["requests"]
        assert result["total_dependencies"] == 3

    def test_to_dict_with_issues(self):
        """Test to_dict with issues included."""
        issue = CompatibilityIssue(
            severity="error",
            category="dependency",
            repos_involved=["repo1", "repo2"],
            description="Conflicting versions",
            suggestion="Use version resolution",
        )
        matrix = CompatibilityMatrix(
            repositories=["repo1", "repo2"],
            overall_compatible=False,
            python_version="3.11",
            issues=[issue],
        )

        result = matrix.to_dict()

        assert result["compatible"] is False
        assert result["issue_count"] == 1
        assert len(result["issues"]) == 1
        assert result["issues"][0]["severity"] == "error"
        assert result["issues"][0]["suggestion"] == "Use version resolution"

