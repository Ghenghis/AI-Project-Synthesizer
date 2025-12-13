"""
Parallel Test Runner - Multi-threaded test execution for maximum speed.
Leverages all CPU cores and RAM for fast test execution.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a test run."""
    test_file: str
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration: float = 0.0
    output: str = ""
    success: bool = True


@dataclass
class RunnerConfig:
    """Configuration for parallel test runner."""
    project_root: str
    test_dirs: List[str] = field(default_factory=lambda: ['tests'])
    max_workers: int = 0  # 0 = auto-detect
    timeout: int = 300
    verbose: bool = False
    coverage: bool = False
    fail_fast: bool = False
    markers: List[str] = field(default_factory=list)
    ignore_patterns: List[str] = field(default_factory=lambda: ['__pycache__', '.pytest_cache'])


class ParallelTestRunner:
    """Multi-process test runner for maximum throughput."""
    
    def __init__(self, config: RunnerConfig):
        self.config = config
        self.project_root = Path(config.project_root)
        self.max_workers = config.max_workers or max(cpu_count() - 2, 4)
        self.results: List[TestResult] = []
        
    def discover_tests(self) -> List[Path]:
        """Discover all test files."""
        test_files = []
        
        for test_dir in self.config.test_dirs:
            test_path = self.project_root / test_dir
            if test_path.exists():
                for f in test_path.rglob('test_*.py'):
                    # Skip ignored patterns
                    skip = False
                    for pattern in self.config.ignore_patterns:
                        if pattern in str(f):
                            skip = True
                            break
                    if not skip:
                        test_files.append(f)
        
        logger.info(f"Discovered {len(test_files)} test files")
        return test_files
    
    def run_all(self) -> Tuple[int, int, int]:
        """Run all tests in parallel."""
        test_files = self.discover_tests()
        
        if not test_files:
            logger.warning("No test files found!")
            return 0, 0, 0
        
        logger.info(f"Running tests with {self.max_workers} workers...")
        start_time = time.time()
        
        # Group tests into batches for better load balancing
        batches = self._create_batches(test_files)
        
        # Run tests in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._run_test_batch, batch): i
                for i, batch in enumerate(batches)
            }
            
            completed = 0
            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    results = future.result()
                    self.results.extend(results)
                    completed += 1
                    
                    # Progress update
                    if completed % 5 == 0 or completed == len(batches):
                        passed = sum(r.passed for r in self.results)
                        failed = sum(r.failed for r in self.results)
                        logger.info(f"Progress: {completed}/{len(batches)} batches | Passed: {passed} | Failed: {failed}")
                        
                except Exception as e:
                    logger.error(f"Batch {batch_idx} failed: {e}")
        
        duration = time.time() - start_time
        
        # Summary
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        
        logger.info("\n" + "=" * 60)
        logger.info("TEST RUN COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Passed:  {total_passed}")
        logger.info(f"Failed:  {total_failed}")
        logger.info(f"Errors:  {total_errors}")
        logger.info(f"Skipped: {total_skipped}")
        logger.info(f"Total:   {total_passed + total_failed + total_errors + total_skipped}")
        
        if total_failed > 0 or total_errors > 0:
            logger.info("\nFailed tests:")
            for r in self.results:
                if r.failed > 0 or r.errors > 0:
                    logger.info(f"  - {r.test_file}")
        
        logger.info("=" * 60)
        
        return total_passed, total_failed, total_errors
    
    def _create_batches(self, test_files: List[Path], batch_size: int = 5) -> List[List[Path]]:
        """Create batches of test files."""
        batches = []
        for i in range(0, len(test_files), batch_size):
            batches.append(test_files[i:i + batch_size])
        return batches
    
    def _run_test_batch(self, test_files: List[Path]) -> List[TestResult]:
        """Run a batch of test files."""
        results = []
        
        for test_file in test_files:
            result = self._run_single_test(test_file)
            results.append(result)
            
            if self.config.fail_fast and not result.success:
                break
        
        return results
    
    def _run_single_test(self, test_file: Path) -> TestResult:
        """Run a single test file."""
        start_time = time.time()
        
        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_file),
            '--tb=short',
            '-q',
            '--no-header',
        ]
        
        if self.config.coverage:
            cmd.extend(['--cov=src', '--cov-append'])
        
        if self.config.markers:
            for marker in self.config.markers:
                cmd.extend(['-m', marker])
        
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )
            
            output = proc.stdout + proc.stderr
            duration = time.time() - start_time
            
            # Parse results from output
            passed, failed, errors, skipped = self._parse_pytest_output(output)
            
            return TestResult(
                test_file=str(test_file.relative_to(self.project_root)),
                passed=passed,
                failed=failed,
                errors=errors,
                skipped=skipped,
                duration=duration,
                output=output if self.config.verbose else "",
                success=(failed == 0 and errors == 0),
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                test_file=str(test_file.relative_to(self.project_root)),
                errors=1,
                duration=self.config.timeout,
                output=f"Test timed out after {self.config.timeout}s",
                success=False,
            )
        except Exception as e:
            return TestResult(
                test_file=str(test_file.relative_to(self.project_root)),
                errors=1,
                output=str(e),
                success=False,
            )
    
    def _parse_pytest_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse pytest output for results."""
        import re
        
        passed = failed = errors = skipped = 0
        
        # Look for summary line like "5 passed, 2 failed, 1 error in 0.5s"
        summary_pattern = r'(\d+)\s+(passed|failed|error|skipped)'
        matches = re.findall(summary_pattern, output.lower())
        
        for count, status in matches:
            count = int(count)
            if status == 'passed':
                passed = count
            elif status == 'failed':
                failed = count
            elif status == 'error':
                errors = count
            elif status == 'skipped':
                skipped = count
        
        # Also check for collection errors
        if 'error' in output.lower() and errors == 0:
            if 'collection' in output.lower() or 'import' in output.lower():
                errors = 1
        
        return passed, failed, errors, skipped
    
    def generate_report(self, output_file: str = 'test_report.json'):
        """Generate JSON report of test results."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_files': len(self.results),
                'passed': sum(r.passed for r in self.results),
                'failed': sum(r.failed for r in self.results),
                'errors': sum(r.errors for r in self.results),
                'skipped': sum(r.skipped for r in self.results),
            },
            'results': [
                {
                    'file': r.test_file,
                    'passed': r.passed,
                    'failed': r.failed,
                    'errors': r.errors,
                    'skipped': r.skipped,
                    'duration': r.duration,
                    'success': r.success,
                }
                for r in self.results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Parallel Test Runner')
    parser.add_argument('--project', '-p', default='.', help='Project root')
    parser.add_argument('--workers', '-w', type=int, default=0, help='Max workers (0=auto)')
    parser.add_argument('--timeout', '-t', type=int, default=300, help='Test timeout')
    parser.add_argument('--coverage', '-c', action='store_true', help='Enable coverage')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    parser.add_argument('--marker', '-m', action='append', help='Test markers')
    parser.add_argument('--report', '-r', default='', help='Report output file')
    
    args = parser.parse_args()
    
    config = RunnerConfig(
        project_root=args.project,
        max_workers=args.workers,
        timeout=args.timeout,
        coverage=args.coverage,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        markers=args.marker or [],
    )
    
    runner = ParallelTestRunner(config)
    passed, failed, errors = runner.run_all()
    
    if args.report:
        runner.generate_report(args.report)
    
    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
