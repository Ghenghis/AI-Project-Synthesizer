"""
Tests for src/automation/testing.py - Integration Testing Framework

Full coverage tests for:
- TestCase
- TestResult
- IntegrationTester
"""

import pytest
import asyncio
from datetime import datetime

from src.automation.testing import (
    TestCase,
    TestResult,
    TestStatus,
    IntegrationTester,
    get_default_tests,
)


class TestTestStatus:
    """Tests for TestStatus enum."""
    
    def test_all_statuses(self):
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"


class TestTestCase:
    """Tests for TestCase dataclass."""
    
    def test_create_test_case(self):
        async def test_func():
            return True
        
        case = TestCase(
            id="test_1",
            name="Test One",
            description="A test case",
            func=test_func,
            category="unit",
        )
        assert case.id == "test_1"
        assert case.name == "Test One"
        assert case.category == "unit"
        assert case.timeout_seconds == 30
        assert case.dependencies == []
    
    def test_with_dependencies(self):
        case = TestCase(
            id="test_dep",
            name="Dependent Test",
            description="",
            func=lambda: True,
            category="integration",
            dependencies=["test_1", "test_2"],
        )
        assert case.dependencies == ["test_1", "test_2"]
    
    def test_custom_timeout(self):
        case = TestCase(
            id="test_timeout",
            name="Long Test",
            description="",
            func=lambda: True,
            category="e2e",
            timeout_seconds=120,
        )
        assert case.timeout_seconds == 120


class TestTestResult:
    """Tests for TestResult dataclass."""
    
    def test_passed_result(self):
        result = TestResult(
            test_id="test_1",
            status=TestStatus.PASSED,
            duration_ms=50.0,
        )
        assert result.test_id == "test_1"
        assert result.status == TestStatus.PASSED
        assert result.duration_ms == 50.0
        assert result.error is None
    
    def test_failed_result(self):
        result = TestResult(
            test_id="test_2",
            status=TestStatus.FAILED,
            duration_ms=100.0,
            error="Assertion failed",
        )
        assert result.status == TestStatus.FAILED
        assert result.error == "Assertion failed"
    
    def test_with_output(self):
        result = TestResult(
            test_id="test_3",
            status=TestStatus.PASSED,
            duration_ms=25.0,
            output={"data": "value"},
        )
        assert result.output["data"] == "value"
    
    def test_to_dict(self):
        result = TestResult(
            test_id="test_dict",
            status=TestStatus.PASSED,
            duration_ms=75.0,
            output={"key": "val"},
        )
        d = result.to_dict()
        assert d["test_id"] == "test_dict"
        assert d["status"] == "passed"
        assert d["duration_ms"] == 75.0


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
            id="my_test",
            name="My Test",
            description="",
            func=my_test,
            category="unit",
        )
        tester.register(case)
        
        assert "my_test" in tester._tests
    
    def test_register_duplicate(self, tester):
        case = TestCase(
            id="dup_test",
            name="Duplicate",
            description="",
            func=lambda: True,
            category="unit",
        )
        tester.register(case)
        tester.register(case)  # Should overwrite
        
        assert len([t for t in tester._tests.values() if t.id == "dup_test"]) == 1
    
    def test_get_test(self, tester):
        case = TestCase(
            id="get_test",
            name="Get Test",
            description="",
            func=lambda: True,
            category="unit",
        )
        tester.register(case)
        
        retrieved = tester.get_test("get_test")
        assert retrieved is not None
        assert retrieved.name == "Get Test"
    
    def test_get_nonexistent_test(self, tester):
        result = tester.get_test("nonexistent")
        assert result is None
    
    def test_list_tests(self, tester):
        for i in range(3):
            tester.register(TestCase(
                id=f"list_test_{i}",
                name=f"List Test {i}",
                description="",
                func=lambda: True,
                category="unit",
            ))
        
        tests = tester.list_tests()
        assert len(tests) == 3
    
    def test_list_tests_by_category(self, tester):
        tester.register(TestCase(
            id="unit_1", name="Unit 1", description="",
            func=lambda: True, category="unit",
        ))
        tester.register(TestCase(
            id="integration_1", name="Integration 1", description="",
            func=lambda: True, category="integration",
        ))
        
        unit_tests = tester.list_tests(category="unit")
        assert len(unit_tests) == 1
        assert unit_tests[0]["category"] == "unit"
    
    @pytest.mark.asyncio
    async def test_run_single_passing(self, tester):
        async def passing_test():
            return True
        
        tester.register(TestCase(
            id="pass_test",
            name="Passing Test",
            description="",
            func=passing_test,
            category="unit",
        ))
        
        result = await tester.run_test("pass_test")
        assert result.status == TestStatus.PASSED
    
    @pytest.mark.asyncio
    async def test_run_single_failing(self, tester):
        async def failing_test():
            raise AssertionError("Test failed")
        
        tester.register(TestCase(
            id="fail_test",
            name="Failing Test",
            description="",
            func=failing_test,
            category="unit",
        ))
        
        result = await tester.run_test("fail_test")
        assert result.status == TestStatus.FAILED
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
        
        tester.register(TestCase(
            id="slow_test",
            name="Slow Test",
            description="",
            func=slow_test,
            category="unit",
            timeout_seconds=0.1,
        ))
        
        result = await tester.run_test("slow_test")
        assert result.status == TestStatus.ERROR
        assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_run_all(self, tester):
        async def test1():
            return True
        
        async def test2():
            return True
        
        tester.register(TestCase(
            id="all_1", name="All 1", description="",
            func=test1, category="unit",
        ))
        tester.register(TestCase(
            id="all_2", name="All 2", description="",
            func=test2, category="unit",
        ))
        
        summary = await tester.run_all()
        assert summary.total == 2
        assert summary.passed == 2
        assert summary.failed == 0
    
    @pytest.mark.asyncio
    async def test_run_all_by_category(self, tester):
        tester.register(TestCase(
            id="cat_unit", name="Unit", description="",
            func=lambda: True, category="unit",
        ))
        tester.register(TestCase(
            id="cat_int", name="Integration", description="",
            func=lambda: True, category="integration",
        ))
        
        summary = await tester.run_all(category="unit")
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
        
        tester.register(TestCase(
            id="dep_test", name="Dependency", description="",
            func=dep_test, category="unit",
        ))
        tester.register(TestCase(
            id="main_test", name="Main", description="",
            func=main_test, category="unit",
            dependencies=["dep_test"],
        ))
        
        await tester.run_all()
        
        # Dependency should run first
        assert results.index("dep") < results.index("main")
    
    def test_get_results(self, tester):
        results = tester.get_results()
        assert isinstance(results, list)
    
    def test_clear_results(self, tester):
        tester._results.append(TestResult(
            test_id="test",
            status=TestStatus.PASSED,
            duration_ms=10,
        ))
        
        tester.clear_results()
        assert len(tester._results) == 0


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
            assert hasattr(test, "id")
            assert hasattr(test, "name")
            assert hasattr(test, "func")
            assert hasattr(test, "category")
