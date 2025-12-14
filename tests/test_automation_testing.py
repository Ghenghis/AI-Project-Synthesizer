"""
Tests for src/automation/testing.py - Integration Testing Framework

Full coverage tests for:
- TestCase
- TestResult
- IntegrationTester
"""

import asyncio

import pytest

from src.automation.testing import (
    IntegrationTester,
    TestCase,
    TestResult,
    TestStatus,
    get_default_tests,
)


class TestStatusEnum:
    """Tests for TestStatus enum."""

    def test_all_statuses(self):
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"


class TestCaseDataclass:
    """Tests for TestCase dataclass."""

    def test_create_test_case(self):
        async def test_func():
            return True

        case = TestCase(
            name="Test One",
            description="A test case",
            test_func=test_func,
            category="unit",
        )
        assert case.name == "Test One"
        assert case.description == "A test case"
        assert case.category == "unit"
        assert case.timeout_seconds == 30
        assert case.dependencies == []

    def test_with_dependencies(self):
        async def test_func():
            return True

        case = TestCase(
            name="Dependent Test",
            description="Test with dependencies",
            test_func=test_func,
            category="integration",
            dependencies=["test_1", "test_2"],
        )
        assert case.dependencies == ["test_1", "test_2"]

    def test_custom_timeout(self):
        async def test_func():
            return True

        case = TestCase(
            name="Long Test",
            description="Test with custom timeout",
            test_func=test_func,
            category="e2e",
            timeout_seconds=120,
        )
        assert case.timeout_seconds == 120


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_passed_result(self):
        result = TestResult(
            name="test_1",
            status=TestStatus.PASSED,
            duration_ms=50.0,
        )
        assert result.name == "test_1"
        assert result.status == TestStatus.PASSED
        assert result.duration_ms == 50.0
        assert result.error is None

    def test_failed_result(self):
        result = TestResult(
            name="test_2",
            status=TestStatus.FAILED,
            duration_ms=100.0,
            error="Assertion failed",
        )
        assert result.status == TestStatus.FAILED
        assert result.error == "Assertion failed"

    def test_with_details(self):
        result = TestResult(
            name="test_3",
            status=TestStatus.PASSED,
            duration_ms=25.0,
            details={"data": "value"},
        )
        assert result.details["data"] == "value"

    def test_with_message(self):
        result = TestResult(
            name="test_msg",
            status=TestStatus.PASSED,
            duration_ms=75.0,
            message="Test completed successfully",
        )
        assert result.name == "test_msg"
        assert result.status == TestStatus.PASSED
        assert result.duration_ms == 75.0
        assert result.message == "Test completed successfully"


class TestIntegrationTester:
    """Tests for IntegrationTester class."""

    @pytest.fixture
    def tester(self):
        return IntegrationTester()

    def test_create_tester(self, tester):
        assert tester is not None
        assert len(tester._tests) == 0

    def test_register_test(self, tester):
        async def my_test():
            return True

        case = TestCase(
            name="my_test",
            description="My Test",
            test_func=my_test,
            category="unit",
        )
        tester.register(case)

        assert "my_test" in tester._tests

    def test_register_duplicate(self, tester):
        async def test_func():
            return True

        case = TestCase(
            name="dup_test",
            description="Duplicate",
            test_func=test_func,
            category="unit",
        )
        tester.register(case)
        tester.register(case)  # Should overwrite

        assert len([t for t in tester._tests.values() if t.name == "dup_test"]) == 1

    def test_list_tests(self, tester):
        async def test_func():
            return True

        for i in range(3):
            tester.register(
                TestCase(
                    name=f"list_test_{i}",
                    description=f"List Test {i}",
                    test_func=test_func,
                    category="unit",
                )
            )

        tests = tester.list_tests()
        assert len(tests) == 3

    def test_list_tests_by_category(self, tester):
        async def test_func():
            return True

        tester.register(
            TestCase(
                name="unit_1",
                description="Unit 1",
                test_func=test_func,
                category="unit",
            )
        )
        tester.register(
            TestCase(
                name="integration_1",
                description="Integration 1",
                test_func=test_func,
                category="integration",
            )
        )

        unit_tests = tester.list_tests(category="unit")
        assert len(unit_tests) == 1
        assert unit_tests[0].category == "unit"

    @pytest.mark.asyncio
    async def test_run_single_passing(self, tester):
        async def passing_test():
            return True

        tester.register(
            TestCase(
                name="pass_test",
                description="Passing Test",
                test_func=passing_test,
                category="unit",
            )
        )

        result = await tester.run_test("pass_test")
        assert result.status == TestStatus.PASSED

    @pytest.mark.asyncio
    async def test_run_single_failing(self, tester):
        async def failing_test():
            raise AssertionError("Test failed")

        tester.register(
            TestCase(
                name="fail_test",
                description="Failing Test",
                test_func=failing_test,
                category="unit",
            )
        )

        result = await tester.run_test("fail_test")
        assert result.status == TestStatus.ERROR
        assert "Test failed" in result.error

    @pytest.mark.asyncio
    async def test_run_nonexistent(self, tester):
        result = await tester.run_test("nonexistent")
        assert result.status == TestStatus.ERROR

    @pytest.mark.asyncio
    async def test_run_with_timeout(self, tester):
        async def slow_test():
            await asyncio.sleep(10)
            return True

        tester.register(
            TestCase(
                name="slow_test",
                description="Slow Test",
                test_func=slow_test,
                category="unit",
                timeout_seconds=1,  # Short timeout
            )
        )

        result = await tester.run_test("slow_test")
        assert result.status == TestStatus.ERROR
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_all(self, tester):
        async def test1():
            return True

        async def test2():
            return True

        tester.register(
            TestCase(
                name="all_1",
                description="All 1",
                test_func=test1,
                category="unit",
            )
        )
        tester.register(
            TestCase(
                name="all_2",
                description="All 2",
                test_func=test2,
                category="unit",
            )
        )

        summary = await tester.run_all()
        assert summary.total == 2
        assert summary.passed == 2
        assert summary.failed == 0

    @pytest.mark.asyncio
    async def test_run_all_by_category(self, tester):
        async def test_func():
            return True

        tester.register(
            TestCase(
                name="cat_unit",
                description="Unit",
                test_func=test_func,
                category="unit",
            )
        )
        tester.register(
            TestCase(
                name="cat_int",
                description="Integration",
                test_func=test_func,
                category="integration",
            )
        )

        summary = await tester.run_category("unit")
        assert summary.total == 1

    @pytest.mark.asyncio
    async def test_run_with_dependencies(self, tester):
        results = []

        async def dep_test():
            results.append("dep")
            return True

        async def main_test():
            results.append("main")
            return True

        tester.register(
            TestCase(
                name="dep_test",
                description="Dependency",
                test_func=dep_test,
                category="unit",
            )
        )
        tester.register(
            TestCase(
                name="main_test",
                description="Main",
                test_func=main_test,
                category="unit",
                dependencies=["dep_test"],
            )
        )

        await tester.run_all()

        # Dependency should run first
        assert results.index("dep") < results.index("main")


class TestGetDefaultTests:
    """Tests for get_default_tests function."""

    def test_returns_list(self):
        tests = get_default_tests()
        assert isinstance(tests, list)

    def test_has_tests(self):
        tests = get_default_tests()
        assert len(tests) > 0

    def test_test_structure(self):
        tests = get_default_tests()
        for test in tests:
            # Verify TestCase dataclass fields
            assert hasattr(test, "name")
            assert hasattr(test, "description")
            assert hasattr(test, "test_func")
            assert hasattr(test, "category")
            assert hasattr(test, "timeout_seconds")
            assert hasattr(test, "dependencies")
            assert hasattr(test, "tags")
