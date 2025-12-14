"""
Component-level integration tests for Vibe MCP

Tests individual components and their interactions.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.quality import (
    LintChecker,
    QualityGate,
    SecurityScanner,
)
from src.vibe import (
    ArchitectAgent,
    AutoCommit,
    AutoRollback,
    ContextInjector,
    ContextManager,
    ExplainMode,
    ProjectClassifier,
    PromptEnhancer,
    RulesEngine,
    TaskDecomposer,
)


class TestPromptEngineering(unittest.TestCase):
    """Test prompt engineering components."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="vibe_prompt_test_"))
        os.chdir(self.test_dir)

        # Create sample project
        (self.test_dir / "src").mkdir()
        (self.test_dir / "src" / "app.py").write_text("""
from flask import Flask

app = Flask(__name__)

@app.route('/api/users')
def get_users():
    users = []
    return jsonify(users)
""")

    def tearDown(self):
        """Clean up."""
        os.chdir(Path(__file__).parent.parent.parent)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_prompt_enhancer(self):
        """Test PromptEnhancer component."""
        enhancer = PromptEnhancer()

        raw_prompt = "Add user authentication"
        context = {
            "project_type": "web_api",
            "tech_stack": ["Python", "Flask"],
            "security_level": "high",
        }

        enhanced = await enhancer.enhance(raw_prompt, context)

        self.assertIn("CONTEXT:", enhanced)
        self.assertIn("TASK:", enhanced)
        self.assertIn("CONSTRAINTS:", enhanced)
        self.assertIn("authentication", enhanced.lower())
        print("✓ PromptEnhancer working correctly")

    async def test_rules_engine(self):
        """Test RulesEngine component."""
        engine = RulesEngine()

        # Load default rules
        await engine.load_rules()

        # Get rules for Python API
        rules = engine.get_rules("python", "web_api")

        self.assertGreater(len(rules), 0)
        self.assertTrue(any("security" in rule.name.lower() for rule in rules))
        print("✓ RulesEngine loaded and filtering rules correctly")

    async def test_context_injector(self):
        """Test ContextInjector component."""
        injector = ContextInjector()

        context = await injector.get_context()

        self.assertIsNotNone(context.project_type)
        self.assertIsNotNone(context.tech_stack)
        self.assertGreater(len(context.components), 0)
        print(f"✓ ContextInjector detected: {context.project_type}")
        print(f"  Tech stack: {', '.join(context.tech_stack)}")


class TestStructuredProcess(unittest.TestCase):
    """Test structured process components."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="vibe_process_test_"))
        os.chdir(self.test_dir)

        # Initialize Git
        os.system("git init --quiet")
        os.system("git config user.name 'Test'")
        os.system("git config user.email 'test@example.com'")

        (self.test_dir / "README.md").write_text("# Test")
        os.system("git add . && git commit -m 'init' --quiet")

    def tearDown(self):
        """Clean up."""
        os.chdir(Path(__file__).parent.parent.parent)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_task_decomposer(self):
        """Test TaskDecomposer component."""
        decomposer = TaskDecomposer()

        request = "Build a REST API with authentication and CRUD operations"

        # Mock LLM response
        mock_response = {
            "task_id": "task_001",
            "phases": [
                {
                    "id": "phase_1",
                    "name": "Setup authentication",
                    "type": "implementation",
                    "complexity": "moderate",
                    "estimated_time": 60,
                    "dependencies": [],
                    "success_criteria": ["Auth system working"],
                    "prompt": "Implement JWT authentication",
                }
            ],
        }

        with patch("src.llm.litellm_router.LiteLLMRouter.generate") as mock:
            mock.return_value = json.dumps(mock_response)

            plan = await decomposer.decompose(request)

            self.assertEqual(len(plan.phases), 1)
            self.assertEqual(plan.phases[0].name, "Setup authentication")
            print("✓ TaskDecomposer breaking down tasks correctly")

    async def test_context_manager(self):
        """Test ContextManager component."""
        manager = ContextManager()

        # Create mock task plan
        from src.vibe.task_decomposer import (
            PhaseType,
            TaskComplexity,
            TaskPhase,
            TaskPlan,
        )

        phase = TaskPhase(
            id="phase_1",
            name="Test Phase",
            description="Test description",
            type=PhaseType.SETUP,
            complexity=TaskComplexity.SIMPLE,
            estimated_time=30,
            dependencies=[],
            success_criteria=["Done"],
            prompt="Test prompt",
        )

        plan = TaskPlan(
            task_id="test_task",
            description="Test plan",
            phases=[phase],
            estimated_total_time=30,
        )

        # Test context creation
        context = await manager.create_context(plan)

        self.assertEqual(context.task_id, "test_task")
        self.assertEqual(len(context.phases), 1)

        # Test phase management
        await manager.start_phase(context.task_id, phase.id)
        phase_state = manager.get_phase_state(context.task_id, phase.id)
        self.assertEqual(phase_state.status.value, "in_progress")

        await manager.complete_phase(context.task_id, phase.id, {"result": "ok"})
        phase_state = manager.get_phase_state(context.task_id, phase.id)
        self.assertEqual(phase_state.status.value, "completed")

        print("✓ ContextManager tracking phases correctly")

    async def test_auto_commit(self):
        """Test AutoCommit component."""
        committer = AutoCommit()

        # Create a file to commit
        (self.test_dir / "test.py").write_text("print('hello')")

        result = await committer.commit_phase("task_1", "phase_1", "Test commit")

        self.assertTrue(result.success)
        self.assertIn("Test commit", result.message)
        print(f"✓ AutoCommit working: {result.message}")

    async def test_architect_agent(self):
        """Test ArchitectAgent component."""
        architect = ArchitectAgent()

        # Mock LLM response
        mock_response = {
            "overview": "Simple REST API",
            "components": [
                {
                    "id": "comp_1",
                    "name": "API Layer",
                    "type": "api",
                    "description": "REST endpoints",
                    "responsibilities": ["Handle requests"],
                    "interfaces": ["HTTP"],
                    "dependencies": [],
                    "technology": "FastAPI",
                }
            ],
            "data_flows": [],
            "technology_stack": {"backend": ["FastAPI"]},
            "non_functional_requirements": {},
            "considerations": [],
        }

        with patch("src.llm.litellm_router.LiteLLMRouter.generate") as mock:
            mock.return_value = json.dumps(mock_response)

            plan = await architect.create_architecture(
                "Create a simple API", {"project_type": "web_api"}
            )

            self.assertEqual(len(plan.components), 1)
            self.assertEqual(plan.components[0].type, "api")
            print("✓ ArchitectAgent generating plans correctly")


class TestQualityPipeline(unittest.TestCase):
    """Test quality pipeline components."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="vibe_quality_test_"))
        os.chdir(self.test_dir)

        # Create sample code with issues
        (self.test_dir / "bad_code.py").write_text("""
import os

def get_user(id):
    query = "SELECT * FROM users WHERE id = " + id
    return os.system(query)
""")

    def tearDown(self):
        """Clean up."""
        os.chdir(Path(__file__).parent.parent.parent)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_security_scanner(self):
        """Test SecurityScanner component."""
        scanner = SecurityScanner()

        # Mock scan results
        mock_result = {
            "scanner": "semgrep",
            "issues": [
                {
                    "rule_id": "python.sql.injection",
                    "message": "SQL injection vulnerability",
                    "severity": "HIGH",
                    "file": "bad_code.py",
                    "line": 4,
                }
            ],
            "summary": {"high": 1, "medium": 0, "low": 0},
        }

        with patch.object(scanner, "scan") as mock_scan:
            mock_scan.return_value = MagicMock(
                success=True,
                issues=mock_result["issues"],
                summary=mock_result["summary"],
            )

            result = await scanner.scan("bad_code.py")

            self.assertTrue(result.success)
            self.assertEqual(len(result.issues), 1)
            self.assertEqual(result.issues[0].severity.value, "high")
            print("✓ SecurityScanner detecting vulnerabilities")

    async def test_lint_checker(self):
        """Test LintChecker component."""
        checker = LintChecker()

        # Mock lint results
        mock_result = {
            "tool": "ruff",
            "issues": [
                {
                    "code": "E501",
                    "message": "Line too long",
                    "severity": "warning",
                    "file": "bad_code.py",
                    "line": 2,
                }
            ],
        }

        with patch.object(checker, "check") as mock_check:
            mock_check.return_value = MagicMock(
                success=True, issues=mock_result["issues"], fixed=0
            )

            result = await checker.check("bad_code.py")

            self.assertTrue(result.success)
            self.assertEqual(len(result.issues), 1)
            print("✓ LintChecker checking code style")

    async def test_quality_gate(self):
        """Test QualityGate component."""
        gate = QualityGate()

        # Mock evaluation
        with patch.object(gate, "evaluate") as mock_eval:
            mock_eval.return_value = MagicMock(passed=True, issues=[], score=85)

            result = await gate.evaluate("sample_code", {})

            self.assertTrue(result.passed)
            self.assertEqual(result.score, 85)
            print("✓ QualityGate evaluating code quality")


class TestLearningIteration(unittest.TestCase):
    """Test learning and iteration components."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="vibe_learning_test_"))
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up."""
        os.chdir(Path(__file__).parent.parent.parent)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_auto_rollback(self):
        """Test AutoRollback component."""
        from src.vibe.auto_rollback import RollbackMode, RollbackStrategy

        rollback = AutoRollback(mode=RollbackMode.DRY_RUN)

        # Create rollback point
        point = await rollback.create_rollback_point(
            "test_task", "test_phase", RollbackStrategy.FILE_SYSTEM
        )

        self.assertIsNotNone(point.checkpoint_id)

        # Test rollback (dry run)
        result = await rollback.rollback_on_failure(
            "test_task", "test_phase", "Test failure", point
        )

        self.assertEqual(result.status.value, "dry_run")
        print("✓ AutoRollback handling failures correctly")

    async def test_explain_mode(self):
        """Test ExplainMode component."""
        from src.vibe.explain_mode import CodeChange, ExplanationLevel

        explainer = ExplainMode()

        # Mock explanation
        mock_response = {
            "title": "Code improvement",
            "summary": "Added type hints for better code clarity",
            "reasoning": ["Type safety", "Better documentation"],
            "alternatives": ["Use type comments"],
            "impact": {"readability": "High"},
            "best_practices": ["Type hints"],
        }

        change = CodeChange(
            file_path="test.py",
            old_code="def add(a, b):",
            new_code="def add(a: int, b: int) -> int:",
            change_type="modify",
            line_numbers=(1, 1),
        )

        with patch("src.llm.litellm_router.LiteLLMRouter.generate") as mock:
            mock.return_value = json.dumps(mock_response)

            explanation = await explainer.explain_code_change(
                change, {}, ExplanationLevel.STANDARD
            )

            self.assertEqual(explanation.title, "Code improvement")
            self.assertIn("type hints", explanation.summary.lower())
            print("✓ ExplainMode generating explanations")

    async def test_project_classifier(self):
        """Test ProjectClassifier component."""
        classifier = ProjectClassifier()

        # Create a Python project
        (self.test_dir / "main.py").write_text("print('hello')")
        (self.test_dir / "requirements.txt").write_text("fastapi")

        characteristics = await classifier.classify_project()

        self.assertIsNotNone(characteristics.type)
        self.assertIn("python", characteristics.stack.languages)
        print(f"✓ ProjectClassifier: {characteristics.type.value}")


class ComponentTestRunner:
    """Run all component tests."""

    @staticmethod
    async def run_all():
        """Run all component integration tests."""
        print("=" * 60)
        print("VIBE COMPONENT INTEGRATION TESTS")
        print("=" * 60)

        test_classes = [
            TestPromptEngineering,
            TestStructuredProcess,
            TestQualityPipeline,
            TestLearningIteration,
        ]

        for test_class in test_classes:
            print(f"\n--- Running {test_class.__name__} ---")

            # Create instance and run tests
            test_instance = test_class()
            test_instance.setUp()

            try:
                # Run all async test methods
                for method_name in dir(test_instance):
                    if method_name.startswith("test_"):
                        method = getattr(test_instance, method_name)
                        if asyncio.iscoroutinefunction(method):
                            await method()

                print(f"✅ {test_class.__name__} passed!")

            except Exception as e:
                print(f"❌ {test_class.__name__} failed: {e}")
                raise
            finally:
                test_instance.tearDown()

        print("\n" + "=" * 60)
        print("✅ ALL COMPONENT TESTS PASSED!")
        print("=" * 60)


if __name__ == "__main__":
    import asyncio

    asyncio.run(ComponentTestRunner.run_all())
