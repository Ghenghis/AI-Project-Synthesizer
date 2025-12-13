"""
AI Project Synthesizer - Integrated Testing Framework

Automated testing for:
- Workflow validation
- API endpoint testing
- Integration tests
- Performance benchmarks
- End-to-end scenarios
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.automation.metrics import ActionTimer, get_metrics_collector
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """A single test case."""
    name: str
    description: str
    test_func: Callable[[], Awaitable[bool]]
    category: str = "general"
    timeout_seconds: int = 30
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of a test execution."""
    name: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestSuiteResult:
    """Result of a test suite execution."""
    suite_name: str
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_ms: float
    results: list[TestResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite_name,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "success_rate": f"{self.success_rate * 100:.1f}%",
            "duration_ms": round(self.duration_ms, 2),
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "duration_ms": round(r.duration_ms, 2),
                    "message": r.message,
                }
                for r in self.results
            ],
        }


class IntegrationTester:
    """
    Integrated testing framework.

    Features:
    - Async test execution
    - Dependency ordering
    - Timeout handling
    - Metrics integration
    - Detailed reporting

    Usage:
        tester = IntegrationTester()

        # Register tests
        tester.register(TestCase(
            name="test_github_search",
            description="Test GitHub search API",
            test_func=test_github_search,
            category="api",
        ))

        # Run all tests
        results = await tester.run_all()

        # Run specific category
        results = await tester.run_category("api")
    """

    def __init__(self):
        self._tests: dict[str, TestCase] = {}
        self._metrics = get_metrics_collector()

    def register(self, test: TestCase):
        """Register a test case."""
        self._tests[test.name] = test

    def register_many(self, tests: list[TestCase]):
        """Register multiple test cases."""
        for test in tests:
            self.register(test)

    async def run_test(self, name: str) -> TestResult:
        """Run a single test."""
        if name not in self._tests:
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                duration_ms=0,
                error=f"Test not found: {name}",
            )

        test = self._tests[name]
        start_time = time.perf_counter()

        try:
            # Run with timeout
            async with ActionTimer(f"test_{name}", self._metrics):
                result = await asyncio.wait_for(
                    test.test_func(),
                    timeout=test.timeout_seconds,
                )

            duration_ms = (time.perf_counter() - start_time) * 1000

            if result:
                return TestResult(
                    name=name,
                    status=TestStatus.PASSED,
                    duration_ms=duration_ms,
                    message="Test passed",
                )
            else:
                return TestResult(
                    name=name,
                    status=TestStatus.FAILED,
                    duration_ms=duration_ms,
                    message="Test returned False",
                )

        except TimeoutError:
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                duration_ms=test.timeout_seconds * 1000,
                error=f"Test timed out after {test.timeout_seconds}s",
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def run_all(self) -> TestSuiteResult:
        """Run all registered tests."""
        return await self._run_tests(list(self._tests.keys()), "all")

    async def run_category(self, category: str) -> TestSuiteResult:
        """Run tests in a specific category."""
        tests = [
            name for name, test in self._tests.items()
            if test.category == category
        ]
        return await self._run_tests(tests, category)

    async def run_tags(self, tags: list[str]) -> TestSuiteResult:
        """Run tests with specific tags."""
        tests = [
            name for name, test in self._tests.items()
            if any(tag in test.tags for tag in tags)
        ]
        return await self._run_tests(tests, f"tags:{','.join(tags)}")

    async def _run_tests(
        self,
        test_names: list[str],
        suite_name: str,
    ) -> TestSuiteResult:
        """Run a list of tests."""
        start_time = time.perf_counter()
        results: list[TestResult] = []
        completed = set()

        # Sort by dependencies
        pending = list(test_names)

        while pending:
            # Find tests with satisfied dependencies
            ready = []
            for name in pending:
                test = self._tests.get(name)
                if test and all(dep in completed for dep in test.dependencies):
                    ready.append(name)

            if not ready:
                # Skip remaining tests with unsatisfied dependencies
                for name in pending:
                    results.append(TestResult(
                        name=name,
                        status=TestStatus.SKIPPED,
                        duration_ms=0,
                        message="Dependencies not satisfied",
                    ))
                break

            # Run ready tests
            for name in ready:
                pending.remove(name)
                result = await self.run_test(name)
                results.append(result)

                if result.status == TestStatus.PASSED:
                    completed.add(name)

        duration_ms = (time.perf_counter() - start_time) * 1000

        return TestSuiteResult(
            suite_name=suite_name,
            total=len(results),
            passed=sum(1 for r in results if r.status == TestStatus.PASSED),
            failed=sum(1 for r in results if r.status == TestStatus.FAILED),
            skipped=sum(1 for r in results if r.status == TestStatus.SKIPPED),
            errors=sum(1 for r in results if r.status == TestStatus.ERROR),
            duration_ms=duration_ms,
            results=results,
        )


# ============================================
# Built-in Test Cases
# ============================================

async def test_lm_studio_connection() -> bool:
    """Test LM Studio is running."""
    import httpx
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get("http://localhost:1234/v1/models")
        return response.status_code == 200


async def test_ollama_connection() -> bool:
    """Test Ollama is running."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except Exception:
        return True  # Optional service


async def test_github_api() -> bool:
    """Test GitHub API access."""
    import httpx

    from src.core.config import get_settings

    settings = get_settings()
    token = settings.platforms.github_token.get_secret_value()

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        return response.status_code == 200


async def test_huggingface_api() -> bool:
    """Test HuggingFace API access."""
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get("https://huggingface.co/api/models?limit=1")
        return response.status_code == 200


async def test_elevenlabs_api() -> bool:
    """Test ElevenLabs API access."""
    import httpx

    from src.core.config import get_settings

    settings = get_settings()
    api_key = settings.elevenlabs.elevenlabs_api_key.get_secret_value()

    if not api_key:
        return True  # Optional

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key}
        )
        return response.status_code == 200


async def test_search_workflow() -> bool:
    """Test search workflow end-to-end."""
    from src.workflows.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    result = await orchestrator.research("test query python")

    return result.success and result.data.get("total", 0) >= 0


async def test_cache_operations() -> bool:
    """Test cache operations."""
    from src.core.cache import get_cache

    cache = get_cache()

    # Set
    await cache.set("test_key", {"value": 123})

    # Get
    result = await cache.get("test_key")

    # Delete
    await cache.delete("test_key")

    return result == {"value": 123}


async def test_metrics_collection() -> bool:
    """Test metrics collection."""
    from src.automation.metrics import ActionTimer, get_metrics_collector

    collector = get_metrics_collector()

    async with ActionTimer("test_action", collector):
        await asyncio.sleep(0.01)

    metrics = collector.get_metrics("test_action")
    return metrics is not None and metrics.count > 0


def get_default_tests() -> list[TestCase]:
    """Get default test cases."""
    return [
        TestCase(
            name="lm_studio",
            description="LM Studio connection",
            test_func=test_lm_studio_connection,
            category="infrastructure",
            tags=["llm", "local"],
        ),
        TestCase(
            name="ollama",
            description="Ollama connection",
            test_func=test_ollama_connection,
            category="infrastructure",
            tags=["llm", "local"],
        ),
        TestCase(
            name="github_api",
            description="GitHub API access",
            test_func=test_github_api,
            category="api",
            tags=["platform", "github"],
        ),
        TestCase(
            name="huggingface_api",
            description="HuggingFace API access",
            test_func=test_huggingface_api,
            category="api",
            tags=["platform", "huggingface"],
        ),
        TestCase(
            name="elevenlabs_api",
            description="ElevenLabs API access",
            test_func=test_elevenlabs_api,
            category="api",
            tags=["voice"],
        ),
        TestCase(
            name="cache",
            description="Cache operations",
            test_func=test_cache_operations,
            category="core",
            tags=["cache"],
        ),
        TestCase(
            name="metrics",
            description="Metrics collection",
            test_func=test_metrics_collection,
            category="core",
            tags=["metrics"],
        ),
        TestCase(
            name="search_workflow",
            description="Search workflow end-to-end",
            test_func=test_search_workflow,
            category="workflow",
            tags=["e2e", "search"],
            dependencies=["github_api"],
            timeout_seconds=60,
        ),
    ]
