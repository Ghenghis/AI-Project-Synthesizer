"""
AI Project Synthesizer - Quality Scorer

Scores repository quality based on documentation, tests,
code organization, activity, and maintenance.
"""

import logging
import re
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Repository quality score breakdown."""

    overall: float = 0.0  # 0.0-1.0 composite score
    documentation: float = 0.0  # README, docstrings, comments
    test_coverage: float = 0.0  # Test presence and coverage
    code_quality: float = 0.0  # Linting, type hints, structure
    ci_cd: float = 0.0  # CI/CD configuration
    maintenance: float = 0.0  # Recent activity, issue handling
    community: float = 0.0  # Stars, forks, contributors

    # Detailed metrics
    has_readme: bool = False
    has_contributing: bool = False
    has_license: bool = False
    has_tests: bool = False
    has_ci: bool = False
    has_type_hints: bool = False
    test_file_count: int = 0
    doc_file_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "overall": round(self.overall, 2),
            "breakdown": {
                "documentation": round(self.documentation, 2),
                "test_coverage": round(self.test_coverage, 2),
                "code_quality": round(self.code_quality, 2),
                "ci_cd": round(self.ci_cd, 2),
                "maintenance": round(self.maintenance, 2),
                "community": round(self.community, 2),
            },
            "indicators": {
                "has_readme": self.has_readme,
                "has_contributing": self.has_contributing,
                "has_license": self.has_license,
                "has_tests": self.has_tests,
                "has_ci": self.has_ci,
                "has_type_hints": self.has_type_hints,
            },
            "counts": {
                "test_files": self.test_file_count,
                "doc_files": self.doc_file_count,
            },
        }

    @property
    def grade(self) -> str:
        """Get letter grade for overall score."""
        if self.overall >= 0.9:
            return "A"
        elif self.overall >= 0.8:
            return "B"
        elif self.overall >= 0.7:
            return "C"
        elif self.overall >= 0.6:
            return "D"
        else:
            return "F"


class QualityScorer:
    """
    Scores repository quality across multiple dimensions.

    Scoring criteria:
    - Documentation (25%): README, docstrings, guides
    - Tests (25%): Test files, coverage indicators
    - Code Quality (20%): Type hints, linting, structure
    - CI/CD (15%): Automation, workflows
    - Maintenance (10%): Activity, responsiveness
    - Community (5%): Adoption metrics

    Example:
        scorer = QualityScorer()
        score = await scorer.score(Path("./repo"), repo_info)
        print(f"Quality: {score.grade} ({score.overall:.0%})")
    """

    # Weights for composite score
    WEIGHTS = {
        "documentation": 0.25,
        "test_coverage": 0.25,
        "code_quality": 0.20,
        "ci_cd": 0.15,
        "maintenance": 0.10,
        "community": 0.05,
    }

    def __init__(self):
        """Initialize the quality scorer."""
        pass

    async def score(
        self,
        repo_path: Path,
        repo_info: Any | None = None,
    ) -> QualityScore:
        """
        Calculate quality score for a repository.

        Args:
            repo_path: Path to repository
            repo_info: Optional RepositoryInfo with metadata

        Returns:
            QualityScore with breakdown
        """
        score = QualityScore()

        # Documentation score
        score.documentation, doc_details = await self._score_documentation(repo_path)
        score.has_readme = doc_details.get("has_readme", False)
        score.has_contributing = doc_details.get("has_contributing", False)
        score.has_license = doc_details.get("has_license", False)
        score.doc_file_count = doc_details.get("doc_count", 0)

        # Test coverage score
        score.test_coverage, test_details = await self._score_tests(repo_path)
        score.has_tests = test_details.get("has_tests", False)
        score.test_file_count = test_details.get("test_count", 0)

        # Code quality score
        score.code_quality, quality_details = await self._score_code_quality(repo_path)
        score.has_type_hints = quality_details.get("has_type_hints", False)

        # CI/CD score
        score.ci_cd, ci_details = await self._score_ci_cd(repo_path)
        score.has_ci = ci_details.get("has_ci", False)

        # Maintenance score (from repo_info)
        if repo_info:
            score.maintenance = self._score_maintenance(repo_info)
            score.community = self._score_community(repo_info)
        else:
            score.maintenance = 0.5  # Default
            score.community = 0.5

        # Calculate overall score
        score.overall = (
            score.documentation * self.WEIGHTS["documentation"]
            + score.test_coverage * self.WEIGHTS["test_coverage"]
            + score.code_quality * self.WEIGHTS["code_quality"]
            + score.ci_cd * self.WEIGHTS["ci_cd"]
            + score.maintenance * self.WEIGHTS["maintenance"]
            + score.community * self.WEIGHTS["community"]
        )

        return score

    async def _score_documentation(
        self,
        repo_path: Path,
    ) -> tuple[float, dict]:
        """Score documentation quality."""
        details = {
            "has_readme": False,
            "has_contributing": False,
            "has_license": False,
            "doc_count": 0,
            "readme_length": 0,
        }

        score_points = 0.0
        max_points = 10.0

        # Check for README
        readme_files = ["README.md", "README.rst", "README.txt", "README"]
        for readme in readme_files:
            readme_path = repo_path / readme
            if readme_path.exists():
                details["has_readme"] = True
                content = readme_path.read_text(encoding="utf-8", errors="replace")
                details["readme_length"] = len(content)

                # Score based on README quality
                if len(content) > 2000:
                    score_points += 3.0  # Comprehensive README
                elif len(content) > 500:
                    score_points += 2.0  # Basic README
                else:
                    score_points += 1.0  # Minimal README
                break

        # Check for CONTRIBUTING
        contributing_files = ["CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING"]
        for contrib in contributing_files:
            if (repo_path / contrib).exists():
                details["has_contributing"] = True
                score_points += 1.0
                break

        # Check for LICENSE
        license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
        for lic in license_files:
            if (repo_path / lic).exists():
                details["has_license"] = True
                score_points += 1.0
                break

        # Check for docs directory
        docs_dirs = ["docs", "doc", "documentation"]
        for docs_dir in docs_dirs:
            docs_path = repo_path / docs_dir
            if docs_path.exists() and docs_path.is_dir():
                doc_files = list(docs_path.rglob("*.md")) + list(
                    docs_path.rglob("*.rst")
                )
                details["doc_count"] = len(doc_files)
                score_points += min(2.0, len(doc_files) * 0.5)
                break

        # Check for docstrings in Python files
        docstring_score = await self._check_docstrings(repo_path)
        score_points += docstring_score * 3.0

        return score_points / max_points, details

    async def _score_tests(
        self,
        repo_path: Path,
    ) -> tuple[float, dict]:
        """Score test coverage."""
        details = {
            "has_tests": False,
            "test_count": 0,
            "has_pytest": False,
            "has_coverage": False,
        }

        score_points = 0.0
        max_points = 10.0

        # Check for test directories
        test_dirs = ["tests", "test", "spec", "__tests__"]
        test_files = []

        for test_dir in test_dirs:
            test_path = repo_path / test_dir
            if test_path.exists() and test_path.is_dir():
                details["has_tests"] = True

                # Count test files
                for pattern in ["test_*.py", "*_test.py", "*.spec.js", "*.test.js"]:
                    test_files.extend(test_path.rglob(pattern))
                break

        # Also check root for test files
        test_files.extend(repo_path.glob("test_*.py"))
        details["test_count"] = len(test_files)

        if details["has_tests"]:
            score_points += 3.0

            # Score based on test count
            if details["test_count"] >= 20:
                score_points += 3.0
            elif details["test_count"] >= 10:
                score_points += 2.0
            elif details["test_count"] >= 5:
                score_points += 1.0

        # Check for pytest configuration
        pytest_configs = ["pytest.ini", "pyproject.toml", "setup.cfg"]
        for config in pytest_configs:
            config_path = repo_path / config
            if config_path.exists():
                content = config_path.read_text(encoding="utf-8", errors="replace")
                if "pytest" in content or "[tool.pytest" in content:
                    details["has_pytest"] = True
                    score_points += 1.0
                    break

        # Check for coverage configuration
        coverage_indicators = [".coveragerc", "codecov.yml", ".codecov.yml"]
        for indicator in coverage_indicators:
            if (repo_path / indicator).exists():
                details["has_coverage"] = True
                score_points += 2.0
                break

        # Check pyproject.toml for coverage
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8", errors="replace")
            if "coverage" in content:
                details["has_coverage"] = True
                score_points += 1.0

        return score_points / max_points, details

    async def _score_code_quality(
        self,
        repo_path: Path,
    ) -> tuple[float, dict]:
        """Score code quality indicators."""
        details = {
            "has_type_hints": False,
            "has_linting": False,
            "has_formatting": False,
            "proper_structure": False,
        }

        score_points = 0.0
        max_points = 10.0

        # Check for type hints in Python files
        py_files = list(repo_path.rglob("*.py"))[:20]  # Sample files
        type_hint_count = 0

        for py_file in py_files:
            if self._should_skip(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                # Simple check for type hints
                if re.search(r"def \w+\([^)]*:\s*\w+", content):
                    type_hint_count += 1
                if re.search(r"->\s*\w+", content):
                    type_hint_count += 1
            except Exception as e:
                logger.debug(f"Failed to analyze type hints in {py_file}: {e}")

        if type_hint_count > len(py_files) * 0.5:
            details["has_type_hints"] = True
            score_points += 2.0

        # Check for linting configuration
        linting_configs = [
            ".flake8",
            ".pylintrc",
            "pylintrc",
            ".ruff.toml",
            "ruff.toml",
            ".eslintrc",
            ".eslintrc.js",
            ".eslintrc.json",
        ]
        for config in linting_configs:
            if (repo_path / config).exists():
                details["has_linting"] = True
                score_points += 2.0
                break

        # Check pyproject.toml for linting
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8", errors="replace")
            if any(tool in content for tool in ["ruff", "flake8", "pylint", "mypy"]):
                details["has_linting"] = True
                score_points += 2.0

        # Check for formatting configuration
        format_configs = [".prettierrc", ".black.toml", "pyproject.toml"]
        for config in format_configs:
            config_path = repo_path / config
            if config_path.exists():
                if config == "pyproject.toml":
                    content = config_path.read_text(encoding="utf-8", errors="replace")
                    if "black" in content or "isort" in content:
                        details["has_formatting"] = True
                        score_points += 2.0
                        break
                else:
                    details["has_formatting"] = True
                    score_points += 2.0
                    break

        # Check for proper project structure
        expected_dirs = ["src", "tests", "docs"]
        existing = sum(1 for d in expected_dirs if (repo_path / d).exists())
        if existing >= 2:
            details["proper_structure"] = True
            score_points += 2.0

        return score_points / max_points, details

    async def _score_ci_cd(
        self,
        repo_path: Path,
    ) -> tuple[float, dict]:
        """Score CI/CD configuration."""
        details = {
            "has_ci": False,
            "ci_provider": None,
            "has_pre_commit": False,
        }

        score_points = 0.0
        max_points = 10.0

        # Check for CI configurations
        ci_configs = {
            ".github/workflows": "github_actions",
            ".gitlab-ci.yml": "gitlab",
            ".travis.yml": "travis",
            "Jenkinsfile": "jenkins",
            ".circleci": "circleci",
            "azure-pipelines.yml": "azure",
            ".drone.yml": "drone",
        }

        for ci_path, provider in ci_configs.items():
            full_path = repo_path / ci_path
            if full_path.exists():
                details["has_ci"] = True
                details["ci_provider"] = provider
                score_points += 5.0

                # Check workflow complexity for GitHub Actions
                if provider == "github_actions" and full_path.is_dir():
                    workflow_files = list(full_path.glob("*.yml")) + list(
                        full_path.glob("*.yaml")
                    )
                    if len(workflow_files) >= 2:
                        score_points += 2.0  # Multiple workflows
                break

        # Check for pre-commit hooks
        if (repo_path / ".pre-commit-config.yaml").exists():
            details["has_pre_commit"] = True
            score_points += 2.0

        # Check for Makefile or task automation
        if (repo_path / "Makefile").exists() or (repo_path / "justfile").exists():
            score_points += 1.0

        return score_points / max_points, details

    def _score_maintenance(self, repo_info: Any) -> float:
        """Score maintenance based on repository metadata."""
        score = 0.5  # Base score

        if hasattr(repo_info, "updated_at") and repo_info.updated_at:
            import math
            from datetime import datetime

            try:
                if isinstance(repo_info.updated_at, str):
                    updated = datetime.fromisoformat(
                        repo_info.updated_at.replace("Z", "+00:00")
                    )
                else:
                    updated = repo_info.updated_at

                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=UTC)

                now = datetime.now(UTC)
                days_ago = (now - updated).days

                # Exponential decay - recent updates score higher
                score = math.exp(-days_ago / 90)  # 3-month half-life

            except Exception as e:
                logger.debug("Failed to calculate recency score: %s", e)

        return min(1.0, score)

    def _score_community(self, repo_info: Any) -> float:
        """Score community adoption."""
        import math

        stars = getattr(repo_info, "stars", 0)
        forks = getattr(repo_info, "forks", 0)

        # Log-scaled scoring
        star_score = min(1.0, math.log10(stars + 1) / 5) if stars > 0 else 0
        fork_score = min(1.0, math.log10(forks + 1) / 4) if forks > 0 else 0

        return star_score * 0.7 + fork_score * 0.3

    async def _check_docstrings(self, repo_path: Path) -> float:
        """Check docstring coverage in Python files."""
        py_files = list(repo_path.rglob("*.py"))[:10]  # Sample
        has_docstring = 0
        total = 0

        for py_file in py_files:
            if self._should_skip(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")

                # Check for module docstring
                if content.strip().startswith('"""') or content.strip().startswith(
                    "'''"
                ):
                    has_docstring += 1

                # Check for function/class docstrings
                func_count = len(re.findall(r"\ndef \w+", content))
                doc_count = len(re.findall(r'"""[^"]+"""', content))

                if func_count > 0 and doc_count >= func_count * 0.5:
                    has_docstring += 1

                total += 1
            except Exception as e:
                logger.debug("Failed to analyze docstrings: %s", e)

        return has_docstring / max(total, 1)

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        skip_patterns = {
            "__pycache__",
            "node_modules",
            "venv",
            ".venv",
            ".git",
            "dist",
            "build",
            ".tox",
            ".eggs",
        }
        return any(p in path.parts for p in skip_patterns)


# Alias for backwards compatibility
QualityMetrics = QualityScore
