"""
Quality Gate for VIBE MCP Quality Pipeline

Orchestrates all quality checks:
- SecurityScanner: Security vulnerability detection
- LintChecker: Code style and linting
- TestGenerator: Test coverage generation
- ReviewAgent: Multi-agent code review

Provides unified pass/fail decisions with auto-fix capabilities.
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.quality.lint_checker import LintChecker, LintResult
from src.quality.review_agent import ReviewAgent, ReviewReport
from src.quality.security_scanner import (
    ScanResult,
    SecurityIssue,
    SecurityScanner,
)
from src.quality.security_scanner import SeverityLevel as SecuritySeverity
from src.quality.test_generator import TestGenerator, TestSuite


class GateStatus(Enum):
    """Quality gate status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    IN_PROGRESS = "in_progress"


class FixStatus(Enum):
    """Auto-fix status."""

    NOT_APPLICABLE = "not_applicable"
    APPLIED = "applied"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class QualityMetrics:
    """Quality metrics for the gate."""

    security_score: float  # 0-100
    lint_score: float  # 0-100
    test_coverage: float  # 0-100
    review_score: float  # 0-10
    overall_score: float  # 0-100


@dataclass
class GateResult:
    """Result of quality gate evaluation."""

    status: GateStatus
    metrics: QualityMetrics
    security_result: ScanResult | None = None
    lint_result: LintResult | None = None
    test_suite: TestSuite | None = None
    review_report: ReviewReport | None = None
    fixed_code: str | None = None
    applied_fixes: list[str] = None
    blocked_issues: list[dict[str, Any]] = None
    evaluation_time: float = 0.0

    def __post_init__(self):
        if self.applied_fixes is None:
            self.applied_fixes = []
        if self.blocked_issues is None:
            self.blocked_issues = []


class QualityGate:
    """
    Unified quality gate for VIBE MCP.

    Features:
    - Orchestrates all quality checks
    - Auto-fix capabilities
    - Configurable thresholds
    - Detailed reporting
    - Block on critical issues
    """

    def __init__(self):
        self.config = get_settings()

        # Initialize quality tools
        self.security_scanner = SecurityScanner()
        self.lint_checker = LintChecker()
        self.test_generator = TestGenerator()
        self.review_agent = ReviewAgent()

        # Quality thresholds (configurable)
        self.thresholds = {
            "security": {
                "block_on_critical": True,
                "block_on_high": True,
                "max_high_issues": 0,
                "max_medium_issues": 5,
            },
            "lint": {
                "block_on_errors": True,
                "max_warnings": 10,
                "require_fixable": False,
            },
            "test": {
                "min_coverage": 80.0,
                "require_tests": True,
                "block_on_no_tests": True,
            },
            "review": {"min_score": 6.0, "block_on_rejected": True},
        }

        # Auto-fix configuration
        self.auto_fix_enabled = {
            "security": False,  # Security fixes need human review
            "lint": True,  # Lint fixes are generally safe
            "test": False,  # Test generation is not a fix
            "review": False,  # Review suggestions need review
        }

    async def evaluate(
        self, code: str, context: dict[str, Any], auto_fix: bool = True
    ) -> GateResult:
        """
        Evaluate code against all quality checks.

        Args:
            code: Code to evaluate
            context: Additional context (file path, language, etc.)
            auto_fix: Whether to apply automatic fixes

        Returns:
            GateResult with detailed findings
        """
        start_time = time.time()
        file_path = context.get("file_path", ".")
        language = context.get("language", "python")

        # Run all checks
        results = await self._run_all_checks(code, file_path, language)

        # Run dependency scan separately (project-level)
        if self.config.get("dependencies", {}).get("enabled", True):
            from .dependency_scanner import DependencyScanner

            dep_scanner = DependencyScanner()
            dependency_reports = await dep_scanner.scan(
                context.get("project_path", ".")
            )

            # Convert dependency vulnerabilities to security issues
            dep_issues = []
            for report in dependency_reports:
                for vuln in report.vulnerabilities:
                    severity_map = {
                        "critical": SecuritySeverity.CRITICAL,
                        "high": SecuritySeverity.HIGH,
                        "medium": SecuritySeverity.MEDIUM,
                        "low": SecuritySeverity.LOW,
                        "none": SecuritySeverity.LOW,
                    }

                    dep_issues.append(
                        SecurityIssue(
                            rule_id=f"DEP-{vuln.package}",
                            message=f"Dependency vulnerability in {vuln.package}@{vuln.installed_version}: {vuln.description}",
                            severity=severity_map.get(
                                vuln.severity.value, SecuritySeverity.MEDIUM
                            ),
                            file_path=f"dependencies/{report.package_manager.value}",
                            line_number=0,
                            category="dependency",
                            cwe_id=vuln.cve_id,
                            tool="dependency_scanner",
                        )
                    )

            # Add dependency issues to security result
            if results.get("security"):
                results["security"].issues.extend(dep_issues)
            else:
                # Create a mock security result for dependency issues
                results["security"] = ScanResult(
                    success=len(dep_issues) == 0,
                    issues=dep_issues,
                    summary={"total": len(dep_issues)},
                    scan_time=0,
                )

        # Calculate metrics
        metrics = self._calculate_metrics(results)

        # Apply auto-fixes if enabled
        current_code = code
        applied_fixes = []
        if auto_fix:
            current_code, applied_fixes = await self._apply_auto_fixes(
                code, file_path, language, results
            )

        # Check pass criteria
        self._check_pass_criteria(results, metrics)

        # Get blocked issues
        blocked_issues = self._get_blocked_issues(results)

        # Determine status
        if any(i.get("severity") in ["critical", "high"] for i in blocked_issues):
            status = GateStatus.FAILED
        elif blocked_issues:
            status = GateStatus.WARNING
        else:
            status = GateStatus.PASSED

        return GateResult(
            status=status,
            metrics=metrics,
            security_result=results.get("security"),
            lint_result=results.get("lint"),
            test_suite=results.get("test"),
            review_report=results.get("review"),
            fixed_code=current_code if applied_fixes else None,
            applied_fixes=applied_fixes,
            blocked_issues=blocked_issues,
            evaluation_time=time.time() - start_time,
        )

    async def _run_all_checks(
        self, code: str, file_path: str, _language: str
    ) -> dict[str, Any]:
        """Run all quality checks in parallel."""
        tasks = {
            "security": self.security_scanner.scan_code(code, file_path),
            "lint": self.lint_checker.check_code(code, file_path, _language),
            "test": self.test_generator.generate_tests(code, file_path, _language),
            "review": self.review_agent.review_code(code, file_path),
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        return {
            "security": results[0] if not isinstance(results[0], Exception) else None,
            "lint": results[1] if not isinstance(results[1], Exception) else None,
            "test": results[2] if not isinstance(results[2], Exception) else None,
            "review": results[3] if not isinstance(results[3], Exception) else None,
        }

    def _calculate_metrics(self, results: dict[str, Any]) -> QualityMetrics:
        """Calculate quality metrics from results."""
        # Security score (100 - critical*20 - high*10 - medium*5)
        security_score = 100
        if results.get("security"):
            for issue in results["security"].issues:
                if issue.severity.value == "critical":
                    security_score -= 20
                elif issue.severity.value == "high":
                    security_score -= 10
                elif issue.severity.value == "medium":
                    security_score -= 5
        security_score = max(0, security_score)

        # Lint score (100 - errors*10 - warnings*2)
        lint_score = 100
        if results.get("lint"):
            for issue in results["lint"].issues:
                if issue.level.value == "error":
                    lint_score -= 10
                elif issue.level.value == "warning":
                    lint_score -= 2
        lint_score = max(0, lint_score)

        # Test coverage
        test_coverage = results["test"].coverage_estimate if results.get("test") else 0

        # Review score (already 0-10)
        review_score = results["review"].overall_score if results.get("review") else 0

        # Overall score (weighted average)
        overall_score = (
            security_score * 0.3
            + lint_score * 0.2
            + test_coverage * 0.3
            + (review_score * 10) * 0.2
        )

        return QualityMetrics(
            security_score=security_score,
            lint_score=lint_score,
            test_coverage=test_coverage,
            review_score=review_score,
            overall_score=overall_score,
        )

    def _check_pass_criteria(
        self, results: dict[str, Any], metrics: QualityMetrics
    ) -> bool:
        """Check if code passes all quality criteria."""
        # Security checks
        if results.get("security"):
            sec_result = results["security"]
            if not sec_result.passed:
                return False

        # Lint checks
        if results.get("lint"):
            lint_result = results["lint"]
            if not lint_result.passed:
                return False

        # Test checks
        if results.get("test"):
            if metrics.test_coverage < self.thresholds["test"]["min_coverage"]:
                return False

        # Review checks
        if results.get("review"):
            if results["review"].overall_score < self.thresholds["review"]["min_score"]:
                return False

        return True

    async def _apply_auto_fixes(
        self, code: str, file_path: str, _language: str, results: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Apply automatic fixes where possible."""
        fixed_code = code
        applied_fixes = []

        # Apply lint fixes
        if self.auto_fix_enabled["lint"] and results.get("lint"):
            try:
                lint_fixed, lint_fixes = await self.lint_checker.fix_code(
                    fixed_code, file_path, _language
                )
                if lint_fixed != fixed_code:
                    fixed_code = lint_fixed
                    applied_fixes.extend(lint_fixes)
            except Exception as e:
                print(f"Lint fix failed: {e}")

        # Note: Security and review fixes require human oversight
        # Test generation is not a fix but a supplement

        return fixed_code, applied_fixes

    def _get_blocked_issues(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """Get issues that block deployment."""
        blocked = []

        # Security issues
        if results.get("security"):
            for issue in results["security"].issues:
                if issue.severity.value in ["critical", "high"]:
                    blocked.append(
                        {
                            "type": "security",
                            "severity": issue.severity.value,
                            "message": issue.message,
                            "file": issue.file_path,
                            "line": issue.line_number,
                        }
                    )

        # Lint errors
        if results.get("lint"):
            for issue in results["lint"].issues:
                if issue.level.value == "error":
                    blocked.append(
                        {
                            "type": "lint",
                            "severity": "error",
                            "message": issue.message,
                            "file": issue.file_path,
                            "line": issue.line_number,
                        }
                    )

        # Test coverage
        if results.get("test"):
            if (
                results["test"].coverage_estimate
                < self.thresholds["test"]["min_coverage"]
            ):
                blocked.append(
                    {
                        "type": "test",
                        "severity": "medium",
                        "message": f"Test coverage {results['test'].coverage_estimate:.1f}% below threshold {self.thresholds['test']['min_coverage']}%",
                        "file": results["test"].file_path,
                    }
                )

        # Review rejection
        if results.get("review"):
            if results["review"].overall_score < self.thresholds["review"]["min_score"]:
                blocked.append(
                    {
                        "type": "review",
                        "severity": "high",
                        "message": f"Review score {results['review'].overall_score:.1f} below threshold {self.thresholds['review']['min_score']}",
                        "file": "review",
                    }
                )

        return blocked

    async def evaluate_directory(
        self, directory: Path, patterns: list[str] = None
    ) -> dict[str, GateResult]:
        """
        Evaluate all files in a directory.

        Args:
            directory: Directory to evaluate
            patterns: File patterns to include

        Returns:
            Dict mapping file paths to GateResults
        """
        if patterns is None:
            patterns = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]

        results = {}

        # Find all matching files
        files = []
        for pattern in patterns:
            files.extend(directory.rglob(pattern))

        # Limit to reasonable number
        if len(files) > 50:
            print(
                f"Warning: Limiting evaluation to first 50 files (found {len(files)})"
            )
            files = files[:50]

        # Evaluate files in parallel batches
        batch_size = 5
        for i in range(0, len(files), batch_size):
            batch = files[i : i + batch_size]

            tasks = []
            for file_path in batch:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        code = f.read()
                    language = "python" if file_path.suffix == ".py" else "javascript"
                    task = self.evaluate(code, str(file_path), language, auto_fix=False)
                    tasks.append((str(file_path), task))
                except Exception as e:
                    print(f"Could not read {file_path}: {e}")
                    continue

            batch_results = await asyncio.gather(
                *[task for _, task in tasks], return_exceptions=True
            )

            for (file_path, _), result in zip(tasks, batch_results, strict=False):
                if isinstance(result, GateResult):
                    results[file_path] = result
                else:
                    print(f"Evaluation failed for {file_path}: {result}")

        return results

    def generate_report(self, result: GateResult) -> str:
        """Generate a comprehensive quality gate report."""
        report = []
        report.append("=" * 70)
        report.append("VIBE MCP QUALITY GATE REPORT")
        report.append("=" * 70)
        report.append(
            f"Status: {self._get_status_emoji(result.status)} {result.status.value.upper()}"
        )
        report.append(f"Overall Score: {result.metrics.overall_score:.1f}/100")
        report.append(f"Evaluation Time: {result.evaluation_time:.2f}s")
        report.append("")

        # Metrics breakdown
        report.append("QUALITY METRICS:")
        report.append(f"  Security:     {result.metrics.security_score:.1f}/100")
        report.append(f"  Lint:         {result.metrics.lint_score:.1f}/100")
        report.append(f"  Test Coverage:{result.metrics.test_coverage:.1f}%")
        report.append(f"  Review Score: {result.metrics.review_score:.1f}/10")
        report.append("")

        # Individual tool results
        if result.security_result:
            report.append("SECURITY SCAN:")
            report.append(f"  Issues found: {len(result.security_result.issues)}")
            critical = sum(
                1
                for i in result.security_result.issues
                if i.severity.value == "critical"
            )
            high = sum(
                1 for i in result.security_result.issues if i.severity.value == "high"
            )
            if critical > 0 or high > 0:
                report.append(f"  ⚠️  {critical} critical, {high} high severity issues")
            report.append("")

        if result.lint_result:
            report.append("LINT CHECK:")
            report.append(f"  Issues found: {len(result.lint_result.issues)}")
            errors = sum(
                1 for i in result.lint_result.issues if i.level.value == "error"
            )
            warnings = sum(
                1 for i in result.lint_result.issues if i.level.value == "warning"
            )
            report.append(f"  {errors} errors, {warnings} warnings")
            if result.lint_result.fixable_issues > 0:
                report.append(
                    f"  ✨ {result.lint_result.fixable_issues} issues auto-fixable"
                )
            report.append("")

        if result.test_suite:
            report.append("TEST GENERATION:")
            report.append(f"  Tests generated: {len(result.test_suite.test_functions)}")
            report.append(
                f"  Estimated coverage: {result.test_suite.coverage_estimate:.1f}%"
            )
            report.append("")

        if result.review_report:
            report.append("CODE REVIEW:")
            report.append(f"  Status: {result.review_report.status.value}")
            report.append(f"  Score: {result.review_report.overall_score:.1f}/10")
            report.append(f"  Issues: {len(result.review_report.issues)}")
            report.append("")

        # Applied fixes
        if result.applied_fixes:
            report.append("AUTO-FIXES APPLIED:")
            for fix in result.applied_fixes:
                report.append(f"  ✅ {fix}")
            report.append("")

        # Blocked issues
        if result.blocked_issues:
            report.append("BLOCKING ISSUES:")
            for issue in result.blocked_issues:
                report.append(f"  ❌ [{issue['type'].upper()}] {issue['message']}")
                if issue.get("line"):
                    report.append(f"     Line {issue['line']} in {issue['file']}")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        if result.status == GateStatus.PASSED:
            report.append(
                "  ✅ Code meets all quality standards and is ready for deployment"
            )
        elif result.status == GateStatus.WARNING:
            report.append("  ⚠️  Code has minor issues that should be addressed soon")
            report.append(
                "  - Consider fixing the identified issues for better code quality"
            )
        else:
            report.append(
                "  ❌ Code has critical issues that must be fixed before deployment"
            )
            report.append("  - Address all blocking issues listed above")
            report.append("  - Re-run the quality gate after fixes")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def _get_status_emoji(self, status: GateStatus) -> str:
        """Get emoji for status."""
        emojis = {
            GateStatus.PASSED: "✅",
            GateStatus.FAILED: "❌",
            GateStatus.WARNING: "⚠️",
            GateStatus.IN_PROGRESS: "🔄",
        }
        return emojis.get(status, "❓")

    def save_report(self, result: GateResult, output_path: str):
        """Save detailed report to JSON file."""
        report_data = {
            "timestamp": time.time(),
            "status": result.status.value,
            "metrics": asdict(result.metrics),
            "applied_fixes": result.applied_fixes,
            "blocked_issues": result.blocked_issues,
            "evaluation_time": result.evaluation_time,
        }

        # Add detailed results
        if result.security_result:
            report_data["security"] = {
                "passed": result.security_result.passed,
                "issues_count": len(result.security_result.issues),
                "scan_time": result.security_result.scan_time,
            }

        if result.lint_result:
            report_data["lint"] = {
                "passed": result.lint_result.passed,
                "issues_count": len(result.lint_result.issues),
                "check_time": result.lint_result.check_time,
                "fixable": result.lint_result.fixable_issues,
            }

        if result.test_suite:
            report_data["test"] = {
                "tests_generated": len(result.test_suite.test_functions),
                "coverage_estimate": result.test_suite.coverage_estimate,
            }

        if result.review_report:
            report_data["review"] = {
                "status": result.review_report.status.value,
                "score": result.review_report.overall_score,
                "issues_count": len(result.review_report.issues),
            }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

    async def install_tools(self) -> bool:
        """Install all required quality tools."""
        print("Installing quality gate tools...")

        tools_installed = await asyncio.gather(
            self.security_scanner.install_tools(),
            self.lint_checker.install_tools(),
            return_exceptions=True,
        )

        return all(isinstance(t, bool) and t for t in tools_installed)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    async def main():
        gate = QualityGate()

        # Install tools if needed
        await gate.install_tools()

        if len(sys.argv) > 1:
            # Evaluate file
            file_path = sys.argv[1]
            if Path(file_path).exists():
                with open(file_path) as f:
                    code = f.read()

                language = "python" if Path(file_path).suffix == ".py" else "javascript"
                result = await gate.evaluate(code, file_path, language)

                print(gate.generate_report(result))

                # Save detailed report
                report_file = Path(file_path).with_suffix(".quality_report.json")
                gate.save_report(result, str(report_file))
                print(f"\nDetailed report saved to: {report_file}")

                # Save fixed code if applicable
                if result.fixed_code and result.fixed_code != code:
                    fixed_file = Path(file_path).with_name(
                        f"{Path(file_path).stem}_fixed{Path(file_path).suffix}"
                    )
                    with open(fixed_file, "w") as f:
                        f.write(result.fixed_code)
                    print(f"Fixed code saved to: {fixed_file}")
            else:
                print(f"File not found: {file_path}")
        else:
            # Demo evaluation
            demo_code = """
import os
import subprocess

def process_user_input(user_data):
    # Security issue: eval usage
    result = eval(user_data)

    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE data = '{user_data}'"

    # Hardcoded secret
    password = "secret123"

    # Print in production
    print(f"Processing: {result}")

    return result

# No type annotations
def calculate(a, b):
    return a + b
"""
            result = await gate.evaluate(demo_code, "demo.py", "python")
            print(gate.generate_report(result))

    asyncio.run(main())
