"""
VIBE MCP Quality Pipeline

This module implements the Security & Quality Pipeline:
- Security vulnerability scanning
- Code linting and style checking
- Automated test generation
- Code review automation
- Dependency vulnerability scanning
- Quality gate enforcement

Components:
- SecurityScanner: Static security analysis (Semgrep, Bandit)
- LintChecker: Code style and quality checks (Ruff, ESLint, mypy)
- TestGenerator: Automated test generation (pytest, jest)
- ReviewAgent: Multi-agent code review (AutoGen)
- QualityGate: Unified quality decisions and auto-fix
- DependencyScanner: Package dependency vulnerability scanning
"""

from .dependency_scanner import (
    DependencyReport,
    DependencyScanner,
    PackageManager,
    SeverityLevel,
    Vulnerability,
)
from .lint_checker import LintChecker, LintIssue, LintLevel
from .quality_gate import GateStatus, QualityGate, QualityMetrics
from .review_agent import ReviewAgent, ReviewIssue, ReviewSeverity, ReviewStatus
from .security_scanner import SecurityIssue, SecurityScanner
from .security_scanner import SeverityLevel as SecuritySeverity
from .test_generator import TestGenerator, TestSuite, TestType

__version__ = "1.0.0"
__all__ = [
    # Security Scanning
    "SecurityScanner",
    "SecurityIssue",
    "SecuritySeverity",
    # Lint Checking
    "LintChecker",
    "LintIssue",
    "LintLevel",
    # Test Generation
    "TestGenerator",
    "TestType",
    "TestSuite",
    # Code Review
    "ReviewAgent",
    "ReviewIssue",
    "ReviewSeverity",
    "ReviewStatus",
    # Quality Gate
    "QualityGate",
    "QualityMetrics",
    "GateStatus",
    # Dependency Scanning
    "DependencyScanner",
    "Vulnerability",
    "SeverityLevel",
    "PackageManager",
    "DependencyReport",
]
