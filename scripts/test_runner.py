#!/usr/bin/env python3
"""
AI Project Synthesizer - Unified Test Runner

One-command test execution with multiple modes:
  - quick: Fast smoke tests only (~30 seconds)
  - unit: All unit tests (~2-5 minutes)
  - full: Complete test suite (~10-15 minutes)
  - ci: CI-style run with coverage

Usage:
    python scripts/test_runner.py quick
    python scripts/test_runner.py unit
    python scripts/test_runner.py full
    python scripts/test_runner.py ci
"""

import subprocess
import sys
import time
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent


def run_cmd(cmd: list[str], check: bool = True) -> int:
    """Run a command and return exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def quick_tests() -> int:
    """Run smoke tests only - fast validation."""
    return run_cmd([
        sys.executable, "-m", "pytest",
        "tests/test_mcp_smoke.py",
        "-v", "--tb=short", "-x"
    ])


def unit_tests() -> int:
    """Run all unit tests."""
    return run_cmd([
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "--ignore=tests/unit/agents/test_crewai_integration.py",
        "--ignore=tests/unit/agents/test_framework_router.py",
        "-v", "--tb=short", "-q"
    ])


def full_tests() -> int:
    """Run complete test suite."""
    return run_cmd([
        sys.executable, "-m", "pytest",
        "tests/",
        "--ignore=tests/generated",
        "--ignore=tests/e2e",
        "-v", "--tb=short"
    ])


def ci_tests() -> int:
    """Run CI-style tests with coverage."""
    return run_cmd([
        sys.executable, "-m", "pytest",
        "tests/",
        "--ignore=tests/generated",
        "--ignore=tests/e2e",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-fail-under=20",
        "-v"
    ])


def lint_check() -> int:
    """Run linting checks."""
    return run_cmd([
        sys.executable, "-m", "ruff", "check", "src/", "tests/"
    ])


def type_check() -> int:
    """Run type checking."""
    return run_cmd([
        sys.executable, "-m", "mypy", "src/", "--ignore-missing-imports"
    ])


def main():
    modes = {
        "quick": ("🚀 Quick smoke tests", quick_tests),
        "unit": ("🧪 Unit tests", unit_tests),
        "full": ("📦 Full test suite", full_tests),
        "ci": ("🔄 CI tests with coverage", ci_tests),
        "lint": ("📝 Lint check", lint_check),
        "type": ("🔍 Type check", type_check),
    }

    if len(sys.argv) < 2 or sys.argv[1] not in modes:
        print("AI Project Synthesizer - Test Runner")
        print("="*40)
        print("\nUsage: python scripts/test_runner.py <mode>\n")
        print("Available modes:")
        for mode, (desc, _) in modes.items():
            print(f"  {mode:8} - {desc}")
        print("\nExamples:")
        print("  python scripts/test_runner.py quick  # Fast validation")
        print("  python scripts/test_runner.py unit   # All unit tests")
        print("  python scripts/test_runner.py ci     # CI with coverage")
        sys.exit(1)

    mode = sys.argv[1]
    desc, func = modes[mode]
    
    print(f"\n{desc}")
    print("="*40)
    
    start = time.time()
    exit_code = func()
    elapsed = time.time() - start
    
    print(f"\n{'='*40}")
    if exit_code == 0:
        print(f"✅ {mode.upper()} PASSED in {elapsed:.1f}s")
    else:
        print(f"❌ {mode.upper()} FAILED in {elapsed:.1f}s")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
