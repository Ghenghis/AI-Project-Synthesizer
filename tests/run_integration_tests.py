"""
Integration Test Runner

Runs all integration tests and generates a comprehensive report.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.integration.test_platform_integrations import (
    TestBrowserClient,
    TestFirecrawlClient,
    TestGitLabClient,
    TestLiteLLMRouter,
    TestMemorySystem,
    run_all_integration_tests,
)


class TestRunner:
    """Integration test runner with reporting."""

    def __init__(self):
        self.results: list[dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    async def run_test_suite(self, test_class, class_name: str) -> dict[str, Any]:
        """Run a test suite and return results."""
        print(f"\n{'=' * 60}")
        print(f"Running {class_name}")
        print(f"{'=' * 60}")

        suite_results = {
            "class_name": class_name,
            "tests": [],
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        # Get all test methods
        test_methods = [
            method
            for method in dir(test_class)
            if method.startswith("test_")
            and asyncio.iscoroutinefunction(getattr(test_class, method))
        ]

        # Create test instance
        test_instance = test_class()

        for test_method in test_methods:
            test_name = f"{class_name}.{test_method}"
            print(f"\n  Running: {test_name}")

            try:
                # Run the test
                method = getattr(test_instance, test_method)
                await method()

                suite_results["tests"].append(
                    {
                        "name": test_name,
                        "status": "PASSED",
                        "duration": 0.1,  # Placeholder
                    }
                )
                suite_results["passed"] += 1
                print("    ✓ PASSED")

            except AssertionError as e:
                suite_results["tests"].append(
                    {
                        "name": test_name,
                        "status": "FAILED",
                        "error": str(e),
                        "duration": 0.1,
                    }
                )
                suite_results["failed"] += 1
                suite_results["errors"].append(f"{test_name}: {str(e)}")
                print(f"    ✗ FAILED: {e}")

            except Exception as e:
                suite_results["tests"].append(
                    {
                        "name": test_name,
                        "status": "ERROR",
                        "error": str(e),
                        "duration": 0.1,
                    }
                )
                suite_results["failed"] += 1
                suite_results["errors"].append(f"{test_name}: {str(e)}")
                print(f"    ✗ ERROR: {e}")

        return suite_results

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all integration test suites."""
        self.start_time = datetime.now()

        print("\n" + "=" * 80)
        print("VIBE MCP - Integration Test Suite")
        print(f"Started at: {self.start_time}")
        print("=" * 80)

        # Define test suites
        test_suites = [
            (TestGitLabClient, "TestGitLabClient"),
            (TestFirecrawlClient, "TestFirecrawlClient"),
            (TestBrowserClient, "TestBrowserClient"),
            (TestMemorySystem, "TestMemorySystem"),
            (TestLiteLLMRouter, "TestLiteLLMRouter"),
        ]

        # Run each suite
        for test_class, class_name in test_suites:
            result = await self.run_test_suite(test_class, class_name)
            self.results.append(result)

        self.end_time = datetime.now()

        # Generate summary
        total_tests = sum(
            r["passed"] + r["failed"] + r["skipped"] for r in self.results
        )
        total_passed = sum(r["passed"] for r in self.results)
        total_failed = sum(r["failed"] for r in self.results)
        total_skipped = sum(r["skipped"] for r in self.results)

        summary = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration": (self.end_time - self.start_time).total_seconds(),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "success_rate": (total_passed / total_tests * 100)
            if total_tests > 0
            else 0,
            "suites": self.results,
        }

        return summary

    def generate_report(self, results: dict[str, Any]) -> str:
        """Generate a test report."""
        report = []
        report.append("\n" + "=" * 80)
        report.append("INTEGRATION TEST REPORT")
        report.append("=" * 80)

        # Summary
        report.append("\nTest Run Summary:")
        report.append(f"  Start Time: {results['start_time']}")
        report.append(f"  End Time: {results['end_time']}")
        report.append(f"  Duration: {results['duration']:.2f} seconds")
        report.append(f"  Total Tests: {results['total_tests']}")
        report.append(f"  Passed: {results['total_passed']}")
        report.append(f"  Failed: {results['total_failed']}")
        report.append(f"  Skipped: {results['total_skipped']}")
        report.append(f"  Success Rate: {results['success_rate']:.1f}%")

        # Suite details
        report.append("\nTest Suite Details:")
        for suite in results["suites"]:
            report.append(f"\n  {suite['class_name']}:")
            report.append(f"    Passed: {suite['passed']}")
            report.append(f"    Failed: {suite['failed']}")
            report.append(f"    Skipped: {suite['skipped']}")

            if suite["errors"]:
                report.append("\n    Errors:")
                for error in suite["errors"]:
                    report.append(f"      - {error}")

        # Recommendations
        report.append("\nRecommendations:")
        if results["total_failed"] == 0:
            report.append("  ✓ All tests passed! System is ready for production.")
        else:
            report.append(
                f"  ⚠ {results['total_failed']} test(s) failed. Review and fix issues."
            )
            report.append("  - Check API keys and credentials for external services")
            report.append("  - Verify network connectivity")
            report.append("  - Review error messages for specific issues")

        return "\n".join(report)

    def save_json_report(self, results: dict[str, Any], file_path: str):
        """Save results as JSON."""
        with open(file_path, "w") as f:
            json.dump(results, f, indent=2, default=str)


async def main():
    """Main test runner."""
    runner = TestRunner()

    # Run tests
    results = await runner.run_all_tests()

    # Generate and print report
    report = runner.generate_report(results)
    print(report)

    # Save JSON report
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = report_dir / f"integration_test_report_{timestamp}.json"
    runner.save_json_report(results, str(json_file))

    print(f"\nDetailed report saved to: {json_file}")

    # Exit with appropriate code
    sys.exit(0 if results["total_failed"] == 0 else 1)


if __name__ == "__main__":
    # Check for specific test suite
    if len(sys.argv) > 1:
        suite_name = sys.argv[1]
        print(f"Running specific test suite: {suite_name}")
        # Implementation for specific suite would go here
    else:
        # Run all tests
        asyncio.run(main())
