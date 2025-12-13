"""
Test Runner for Vibe MCP

Runs all test suites with proper configuration and reporting.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Test runner for all Vibe MCP tests."""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    async def run_all(self):
        """Run all test suites."""
        print("=" * 80)
        print("VIBE MCP COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Started at: {self.start_time}")
        print()
        
        # Test suites to run
        test_suites = [
            {
                "name": "Pipeline Smoke Tests",
                "file": "tests/integration/vibe_pipeline_smoke_test.py",
                "type": "integration"
            },
            {
                "name": "Component Integration Tests",
                "file": "tests/integration/test_vibe_components.py",
                "type": "integration"
            },
            {
                "name": "Unit Tests",
                "file": "tests/unit/",
                "type": "pytest"
            }
        ]
        
        # Run each test suite
        for suite in test_suites:
            await self.run_test_suite(suite)
        
        # Print summary
        self.print_summary()
    
    async def run_test_suite(self, suite):
        """Run a single test suite."""
        print(f"\n{'-' * 60}")
        print(f"Running: {suite['name']}")
        print(f"{'-' * 60}")
        
        try:
            if suite["type"] == "integration":
                # Run integration tests
                result = await self.run_integration_test(suite["file"])
            elif suite["type"] == "pytest":
                # Run pytest
                result = await self.run_pytest(suite["file"])
            else:
                result = {"passed": False, "output": "Unknown test type"}
            
            self.results.append({
                "name": suite["name"],
                "passed": result["passed"],
                "output": result["output"],
                "duration": result.get("duration", 0)
            })
            
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"\n{status}: {suite['name']}")
            
        except Exception as e:
            self.results.append({
                "name": suite["name"],
                "passed": False,
                "output": str(e),
                "duration": 0
            })
            print(f"\n❌ ERROR: {suite['name']} - {e}")
    
    async def run_integration_test(self, test_file):
        """Run an integration test."""
        start = datetime.now()
        
        try:
            # Run the test file
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            duration = (datetime.now() - start).total_seconds()
            
            return {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "duration": duration
            }
            
        except Exception as e:
            return {
                "passed": False,
                "output": str(e),
                "duration": (datetime.now() - start).total_seconds()
            }
    
    async def run_pytest(self, test_dir):
        """Run pytest on a directory."""
        start = datetime.now()
        
        try:
            # Check if pytest is available
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_dir, "-v"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            duration = (datetime.now() - start).total_seconds()
            
            return {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "duration": duration
            }
            
        except Exception as e:
            return {
                "passed": False,
                "output": str(e),
                "duration": (datetime.now() - start).total_seconds()
            }
    
    def print_summary(self):
        """Print test summary."""
        total_time = datetime.now() - self.start_time
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        
        for result in self.results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['name']} ({result['duration']:.2f}s)")
        
        print(f"\nTotal: {passed}/{total} passed")
        print(f"Total time: {total_time.total_seconds():.2f}s")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️ Some tests failed. Check output above.")
        
        # Print failures
        failures = [r for r in self.results if not r["passed"]]
        if failures:
            print("\nFailed Tests:")
            for failure in failures:
                print(f"\n❌ {failure['name']}:")
                print(failure["output"][:500])
    
    def run_coverage(self):
        """Run tests with coverage report."""
        print("\n" + "=" * 80)
        print("RUNNING WITH COVERAGE")
        print("=" * 80)
        
        try:
            # Install coverage if needed
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "coverage"],
                capture_output=True
            )
            
            # Run coverage
            subprocess.run([
                sys.executable, "-m", "coverage", "run",
                "-m", "pytest", "tests/",
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term"
            ], cwd=project_root)
            
            print("\nCoverage report generated in htmlcov/")
            
        except Exception as e:
            print(f"Coverage failed: {e}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Vibe MCP tests")
    parser.add_argument("--coverage", action="store_true", 
                       help="Run tests with coverage report")
    parser.add_argument("--integration-only", action="store_true",
                       help="Run only integration tests")
    parser.add_argument("--unit-only", action="store_true",
                       help="Run only unit tests")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.coverage:
        runner.run_coverage()
    elif args.integration_only:
        # Run only integration tests
        integration_suites = [
            {
                "name": "Pipeline Smoke Tests",
                "file": "tests/integration/vibe_pipeline_smoke_test.py",
                "type": "integration"
            },
            {
                "name": "Component Integration Tests",
                "file": "tests/integration/test_vibe_components.py",
                "type": "integration"
            }
        ]
        
        for suite in integration_suites:
            await runner.run_test_suite(suite)
        
        runner.print_summary()
    elif args.unit_only:
        # Run only unit tests
        await runner.run_pytest("tests/unit/")
    else:
        # Run all tests
        await runner.run_all()


if __name__ == "__main__":
    asyncio.run(main())
