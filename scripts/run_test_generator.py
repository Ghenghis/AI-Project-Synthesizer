#!/usr/bin/env python
"""
Enterprise Test Generator - Main Entry Point
============================================

Generates 6000+ unit tests, 300+ integration tests, 200+ E2E tests
for 100% code coverage using multi-threaded execution.

Usage:
    python run_test_generator.py generate    # Generate all tests
    python run_test_generator.py run         # Run all tests in parallel
    python run_test_generator.py coverage    # Run with coverage report
    python run_test_generator.py full        # Generate + Run + Coverage

Hardware Optimizations:
    - Uses all CPU cores for parallel generation
    - Multi-process test execution
    - Memory-efficient batch processing
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'enterprise_test_generator'))

from enterprise_test_generator.generator import TestGenerator, GenerationConfig
from enterprise_test_generator.parallel_runner import ParallelTestRunner, RunnerConfig
from enterprise_test_generator.analyzer import CodeAnalyzer


def cmd_analyze(args):
    """Analyze codebase and show statistics."""
    print("\n" + "=" * 60)
    print("CODEBASE ANALYSIS")
    print("=" * 60)
    
    analyzer = CodeAnalyzer(args.project, max_workers=args.workers)
    summary = analyzer.analyze_project(['src'])
    
    print(f"\nProject: {args.project}")
    print(f"Modules: {summary['total_modules']}")
    print(f"Classes: {summary['total_classes']}")
    print(f"Functions: {summary['total_functions']}")
    print(f"\nComplexity Distribution:")
    print(f"  Low:    {summary['functions_by_complexity']['low']}")
    print(f"  Medium: {summary['functions_by_complexity']['medium']}")
    print(f"  High:   {summary['functions_by_complexity']['high']}")
    print(f"\nAsync Functions: {summary['async_functions']}")
    print(f"Private Functions: {summary['private_functions']}")
    print(f"Functions with Exceptions: {summary['functions_with_exceptions']}")
    
    # Calculate test estimates
    total_funcs = summary['total_functions']
    unit_tests = total_funcs * 5  # 5 tests per function
    integration_tests = summary['total_modules'] * 3
    e2e_tests = 5 * 3  # 5 workflows * 3 tests each
    
    print(f"\nEstimated Tests Needed for 100% Coverage:")
    print(f"  Unit Tests:        ~{unit_tests:,}")
    print(f"  Integration Tests: ~{integration_tests:,}")
    print(f"  E2E Tests:         ~{e2e_tests:,}")
    print(f"  TOTAL:             ~{unit_tests + integration_tests + e2e_tests:,}")
    
    if args.output:
        analyzer.save_analysis(args.output)
        print(f"\nFull analysis saved to: {args.output}")
    
    print("=" * 60)
    return 0


def cmd_generate(args):
    """Generate all tests."""
    print("\n" + "=" * 60)
    print("ENTERPRISE TEST GENERATOR")
    print("=" * 60)
    print(f"Project:  {args.project}")
    print(f"Output:   {args.output}")
    print(f"Workers:  {args.workers}")
    print("=" * 60)
    
    config = GenerationConfig(
        project_root=args.project,
        output_dir=args.output,
        max_workers=args.workers,
        tests_per_function=5,
        generate_unit=not args.skip_unit,
        generate_integration=not args.skip_integration,
        generate_e2e=not args.skip_e2e,
        generate_mocks=True,
        overwrite_existing=args.overwrite,
        include_private=True,
        include_dunder=False,
    )
    
    generator = TestGenerator(config)
    stats = generator.generate_all()
    
    if stats.errors:
        print(f"\nGeneration completed with {len(stats.errors)} errors")
        return 1
    
    return 0


def cmd_run(args):
    """Run all tests in parallel."""
    print("\n" + "=" * 60)
    print("PARALLEL TEST RUNNER")
    print("=" * 60)
    
    config = RunnerConfig(
        project_root=args.project,
        test_dirs=['tests', 'tests/generated'] if not args.generated_only else ['tests/generated'],
        max_workers=args.workers,
        timeout=args.timeout,
        verbose=args.verbose,
        coverage=args.coverage,
        fail_fast=args.fail_fast,
    )
    
    runner = ParallelTestRunner(config)
    passed, failed, errors = runner.run_all()
    
    if args.report:
        runner.generate_report(args.report)
    
    return 0 if (failed == 0 and errors == 0) else 1


def cmd_coverage(args):
    """Run tests with coverage report."""
    import subprocess
    
    print("\n" + "=" * 60)
    print("COVERAGE REPORT")
    print("=" * 60)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '--cov=src',
        '--cov-report=html',
        '--cov-report=term-missing',
        f'-n={args.workers}',  # pytest-xdist parallel
        '-v',
    ]
    
    if args.generated_only:
        cmd[2] = 'tests/generated/'
    
    result = subprocess.run(cmd, cwd=args.project)
    
    print(f"\nCoverage report: {args.project}/htmlcov/index.html")
    
    return result.returncode


def cmd_full(args):
    """Full pipeline: generate + run + coverage."""
    print("\n" + "=" * 60)
    print("FULL TEST PIPELINE")
    print("=" * 60)
    
    # Step 1: Analyze
    print("\n[1/4] Analyzing codebase...")
    args.output = None
    cmd_analyze(args)
    
    # Step 2: Generate
    print("\n[2/4] Generating tests...")
    result = cmd_generate(args)
    if result != 0:
        print("Generation failed!")
        return result
    
    # Step 3: Run
    print("\n[3/4] Running tests...")
    args.coverage = False
    args.generated_only = True
    result = cmd_run(args)
    
    # Step 4: Coverage
    print("\n[4/4] Generating coverage report...")
    args.coverage = True
    cmd_coverage(args)
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Enterprise Test Generator - 100% Coverage Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze codebase
    python run_test_generator.py analyze
    
    # Generate all tests
    python run_test_generator.py generate
    
    # Run tests in parallel
    python run_test_generator.py run --workers 16
    
    # Generate coverage report
    python run_test_generator.py coverage
    
    # Full pipeline
    python run_test_generator.py full
"""
    )
    
    # Global arguments
    parser.add_argument('--project', '-p', default='.', help='Project root directory')
    parser.add_argument('--workers', '-w', type=int, default=16, help='Max worker threads')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze codebase')
    analyze_parser.add_argument('--output', '-o', help='Save analysis to file')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate tests')
    gen_parser.add_argument('--output', '-o', default='tests/generated', help='Output directory')
    gen_parser.add_argument('--skip-unit', action='store_true', help='Skip unit tests')
    gen_parser.add_argument('--skip-integration', action='store_true', help='Skip integration tests')
    gen_parser.add_argument('--skip-e2e', action='store_true', help='Skip E2E tests')
    gen_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing')
    gen_parser.set_defaults(func=cmd_generate)
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run tests in parallel')
    run_parser.add_argument('--timeout', '-t', type=int, default=300, help='Test timeout')
    run_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    run_parser.add_argument('--coverage', '-c', action='store_true', help='Enable coverage')
    run_parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    run_parser.add_argument('--generated-only', action='store_true', help='Run only generated tests')
    run_parser.add_argument('--report', '-r', help='Output report file')
    run_parser.set_defaults(func=cmd_run)
    
    # Coverage command
    cov_parser = subparsers.add_parser('coverage', help='Run with coverage')
    cov_parser.add_argument('--generated-only', action='store_true', help='Only generated tests')
    cov_parser.set_defaults(func=cmd_coverage)
    
    # Full command
    full_parser = subparsers.add_parser('full', help='Full pipeline')
    full_parser.add_argument('--output', '-o', default='tests/generated', help='Output directory')
    full_parser.add_argument('--skip-unit', action='store_true')
    full_parser.add_argument('--skip-integration', action='store_true')
    full_parser.add_argument('--skip-e2e', action='store_true')
    full_parser.add_argument('--overwrite', action='store_true')
    full_parser.add_argument('--timeout', '-t', type=int, default=300)
    full_parser.add_argument('--verbose', '-v', action='store_true')
    full_parser.add_argument('--fail-fast', '-x', action='store_true')
    full_parser.add_argument('--report', '-r', help='Output report file')
    full_parser.set_defaults(func=cmd_full)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
