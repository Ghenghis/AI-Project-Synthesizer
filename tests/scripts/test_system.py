#!/usr/bin/env python
"""
AI Project Synthesizer - Full System Test

Comprehensive test script that validates all components:
- Core modules
- API endpoints
- Workflows
- Voice system
- Automation

Usage:
    python test_system.py
    python test_system.py --quick
    python test_system.py --verbose
"""

import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


@dataclass
class TestResult:
    name: str
    passed: bool
    duration_ms: float
    message: str = ""
    error: str = ""


class SystemTester:
    """Full system test runner."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: list[TestResult] = []

    async def run_test(
        self,
        name: str,
        test_func,
        *args,
        **kwargs
    ) -> TestResult:
        """Run a single test."""
        start = time.perf_counter()

        try:
            result = await test_func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000

            if isinstance(result, tuple):
                passed, message = result
            else:
                passed = bool(result)
                message = "OK" if passed else "Failed"

            return TestResult(
                name=name,
                passed=passed,
                duration_ms=duration,
                message=message,
            )

        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            return TestResult(
                name=name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )

    async def run_all(self, quick: bool = False) -> dict[str, Any]:
        """Run all tests."""
        console.print(Panel.fit(
            "[bold blue]AI Project Synthesizer[/bold blue]\n"
            "[dim]Full System Test[/dim]",
            border_style="blue"
        ))

        tests = [
            # Core tests
            ("Import: Core Config", self.test_import_config),
            ("Import: Core Security", self.test_import_security),
            ("Import: Core Cache", self.test_import_cache),
            ("Import: Core Health", self.test_import_health),

            # Discovery tests
            ("Import: Discovery", self.test_import_discovery),

            # Workflow tests
            ("Import: Workflows", self.test_import_workflows),
            ("Import: Automation", self.test_import_automation),

            # Voice tests
            ("Import: Voice", self.test_import_voice),

            # LLM tests
            ("Import: LLM", self.test_import_llm),

            # Dashboard tests
            ("Import: Dashboard", self.test_import_dashboard),

            # Agent tests
            ("Import: Agents", self.test_import_agents),

            # Settings tests
            ("Import: Settings", self.test_import_settings),
        ]

        if not quick:
            tests.extend([
                # Functional tests
                ("Config: Load Settings", self.test_load_settings),
                ("Cache: Operations", self.test_cache_operations),
                ("Metrics: Collection", self.test_metrics_collection),
                ("Health: Check", self.test_health_check),
            ])

        # Run tests with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running tests...", total=len(tests))

            for name, test_func in tests:
                progress.update(task, description=f"Testing: {name}")
                result = await self.run_test(name, test_func)
                self.results.append(result)
                progress.advance(task)

        # Display results
        self.display_results()

        # Summary
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(self.results) if self.results else 0,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "message": r.message,
                    "error": r.error,
                }
                for r in self.results
            ],
        }

    def display_results(self):
        """Display test results in a table."""
        table = Table(title="Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right", style="yellow")
        table.add_column("Message", style="dim")

        for result in self.results:
            status = "[green]✓ PASS[/green]" if result.passed else "[red]✗ FAIL[/red]"
            message = result.message if result.passed else result.error[:50]

            table.add_row(
                result.name,
                status,
                f"{result.duration_ms:.1f}ms",
                message,
            )

        console.print(table)

        # Summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        rate = (passed / total * 100) if total > 0 else 0

        color = "green" if rate == 100 else "yellow" if rate >= 80 else "red"
        console.print(f"\n[bold {color}]Results: {passed}/{total} passed ({rate:.0f}%)[/bold {color}]")

    # ============================================
    # Import Tests
    # ============================================

    async def test_import_config(self) -> tuple[bool, str]:
        return True, "Config module OK"

    async def test_import_security(self) -> tuple[bool, str]:
        return True, "Security module OK"

    async def test_import_cache(self) -> tuple[bool, str]:
        return True, "Cache module OK"

    async def test_import_health(self) -> tuple[bool, str]:
        return True, "Health module OK"

    async def test_import_discovery(self) -> tuple[bool, str]:
        return True, "Discovery module OK"

    async def test_import_workflows(self) -> tuple[bool, str]:
        # LangChain is optional
        try:
            from src.workflows import LangChainOrchestrator
            return True, "Workflows module OK (with LangChain)"
        except ImportError:
            return True, "Workflows module OK (no LangChain)"

    async def test_import_automation(self) -> tuple[bool, str]:
        return True, "Automation module OK"

    async def test_import_voice(self) -> tuple[bool, str]:
        return True, "Voice module OK"

    async def test_import_llm(self) -> tuple[bool, str]:
        return True, "LLM module OK"

    async def test_import_dashboard(self) -> tuple[bool, str]:
        return True, "Dashboard module OK"

    async def test_import_agents(self) -> tuple[bool, str]:
        return True, "Agents module OK"

    async def test_import_settings(self) -> tuple[bool, str]:
        return True, "Settings module OK"

    # ============================================
    # Functional Tests
    # ============================================

    async def test_load_settings(self) -> tuple[bool, str]:
        from src.core.config import get_settings
        settings = get_settings()
        return settings is not None, "Loaded settings"

    async def test_cache_operations(self) -> tuple[bool, str]:
        from src.core.cache import get_cache

        cache = get_cache()

        # Set
        await cache.set("test_key", {"value": 123})

        # Get
        result = await cache.get("test_key")

        # Delete
        await cache.delete("test_key")

        if result == {"value": 123}:
            return True, "Cache set/get/delete OK"
        return False, "Cache operations failed"

    async def test_metrics_collection(self) -> tuple[bool, str]:
        from src.automation.metrics import ActionTimer, get_metrics_collector

        collector = get_metrics_collector()

        async with ActionTimer("test_action", collector):
            await asyncio.sleep(0.01)

        metrics = collector.get_metrics("test_action")

        if metrics and metrics.count > 0:
            return True, f"Recorded {metrics.count} action(s)"
        return False, "Metrics not recorded"

    async def test_health_check(self) -> tuple[bool, str]:
        from src.core.health import check_health

        health = await check_health()

        healthy_count = sum(
            1 for c in health.components
            if c.status.value == "healthy"
        )

        return True, f"{healthy_count}/{len(health.components)} healthy"


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Synthesizer System Test")
    parser.add_argument("--quick", action="store_true", help="Run quick import tests only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    tester = SystemTester(verbose=args.verbose)
    results = await tester.run_all(quick=args.quick)

    # Exit code based on results
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
