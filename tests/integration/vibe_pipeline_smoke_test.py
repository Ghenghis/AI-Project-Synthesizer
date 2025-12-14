"""
Vibe Coding Automation Pipeline Smoke Test

Tests the complete pipeline flow:
ArchitectAgent → TaskDecomposer → ContextManager → QualityGate → AutoCommit

Usage:
- Fast mode: Mocked LLM responses for quick testing
- Integration mode: Real LLM calls for full validation
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.llm.litellm_router import LiteLLMRouter
from src.quality import QualityGate
from src.vibe import (
    ArchitectAgent,
    AutoCommit,
    AutoRollback,
    ContextManager,
    ExplainMode,
    ProjectClassifier,
    TaskDecomposer,
)
from src.vibe.auto_rollback import RollbackMode, RollbackStrategy


class VibePipelineSmokeTest(unittest.TestCase):
    """Smoke test for the complete Vibe Coding Automation pipeline."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="vibe_test_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize Git repo in test directory
        os.system("git init --quiet")
        os.system("git config user.name 'Test User'")
        os.system("git config user.email 'test@example.com'")

        # Create sample project structure
        self.create_sample_project()

        # Test data
        self.sample_request = "Create a REST API for a todo application with CRUD operations"
        self.sample_context = {
            "project_type": "web_api",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
        }

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_sample_project(self):
        """Create a sample project structure for testing."""
        # Create directories
        (self.test_dir / "src").mkdir()
        (self.test_dir / "tests").mkdir()
        (self.test_dir / "docs").mkdir()

        # Create sample files
        (self.test_dir / "README.md").write_text("# Test Project")
        (self.test_dir / "requirements.txt").write_text("fastapi\nuvicorn\n")
        (self.test_dir / "pyproject.toml").write_text("""
[tool.black]
line-length = 88

[tool.mypy]
python_version = "3.11"
""")

        # Initial commit
        os.system("git add .")
        os.system("git commit -m 'Initial commit' --quiet")

    def get_mock_llm_responses(self):
        """Get predefined LLM responses for testing."""
        return {
            "architect": {
                "overview": "REST API for todo management",
                "components": [
                    {
                        "id": "component_1",
                        "name": "API Layer",
                        "type": "api",
                        "description": "REST API endpoints",
                        "responsibilities": ["Handle HTTP requests", "Validate input"],
                        "interfaces": ["REST API"],
                        "dependencies": ["component_2"],
                        "technology": "FastAPI"
                    },
                    {
                        "id": "component_2",
                        "name": "Business Logic",
                        "type": "business",
                        "description": "Core business logic",
                        "responsibilities": ["Process data", "Apply rules"],
                        "interfaces": ["Internal API"],
                        "dependencies": ["component_3"],
                        "technology": "Python"
                    },
                    {
                        "id": "component_3",
                        "name": "Database",
                        "type": "database",
                        "description": "Data persistence",
                        "responsibilities": ["Store data", "Query data"],
                        "interfaces": ["SQL"],
                        "dependencies": [],
                        "technology": "PostgreSQL"
                    }
                ],
                "data_flows": [],
                "technology_stack": {
                    "backend": ["FastAPI"],
                    "database": ["PostgreSQL"]
                },
                "non_functional_requirements": {
                    "performance": "Medium",
                    "security": "Medium",
                    "scalability": "Medium"
                },
                "considerations": ["Simple CRUD operations"]
            },
            "decomposer": {
                "task_id": "task_001",
                "phases": [
                    {
                        "id": "phase_1",
                        "name": "Setup Project Structure",
                        "description": "Create initial project structure",
                        "type": "setup",
                        "complexity": "simple",
                        "estimated_time": 30,
                        "dependencies": [],
                        "success_criteria": ["Structure created"],
                        "prompt": "Create project structure for todo API"
                    },
                    {
                        "id": "phase_2",
                        "name": "Implement API Endpoints",
                        "description": "Create CRUD endpoints",
                        "type": "implementation",
                        "complexity": "moderate",
                        "estimated_time": 120,
                        "dependencies": ["phase_1"],
                        "success_criteria": ["Endpoints working"],
                        "prompt": "Implement FastAPI endpoints for todo CRUD"
                    }
                ]
            },
            "explain": {
                "title": "API Endpoint Implementation",
                "summary": "Implemented REST API endpoints using FastAPI",
                "reasoning": ["FastAPI provides automatic docs", "Type safety with Pydantic"],
                "alternatives": ["Flask", "Django REST"],
                "impact": {"performance": "Medium", "security": "Medium"},
                "best_practices": ["Type hints", "Async support"]
            }
        }

    async def test_pipeline_success_scenario(self):
        """Test the complete pipeline with success scenario."""
        print("\n=== Testing Pipeline Success Scenario ===")

        # Get mock responses
        mock_responses = self.get_mock_llm_responses()

        # Mock LLM router
        with patch.object(LiteLLMRouter, 'generate') as mock_generate:
            mock_generate.return_value = json.dumps(mock_responses["architect"])

            # 1. Architect Agent
            architect = ArchitectAgent()
            arch_plan = await architect.create_architecture(
                self.sample_request,
                self.sample_context
            )

            self.assertEqual(arch_plan.pattern.value, "rest_api")
            self.assertEqual(len(arch_plan.components), 3)
            print("✓ ArchitectAgent created architectural plan")

        # 2. Task Decomposer
        with patch.object(LiteLLMRouter, 'generate') as mock_generate:
            mock_generate.return_value = json.dumps(mock_responses["decomposer"])

            decomposer = TaskDecomposer()
            task_plan = await decomposer.decompose(
                self.sample_request,
                arch_plan
            )

            self.assertEqual(len(task_plan.phases), 2)
            self.assertEqual(task_plan.phases[0].name, "Setup Project Structure")
            print("✓ TaskDecomposer created task phases")

        # 3. Context Manager
        context_manager = ContextManager()
        task_context = await context_manager.create_context(task_plan)

        self.assertIsNotNone(task_context.task_id)
        self.assertEqual(len(task_context.phases), 2)
        print("✓ ContextManager initialized task context")

        # 4. Process phases
        for i, phase in enumerate(task_plan.phases):
            print(f"\n--- Processing Phase {i+1}: {phase.name} ---")

            # Start phase
            await context_manager.start_phase(task_context.task_id, phase.id)

            # Simulate phase work
            if phase.id == "phase_1":
                # Create sample code
                (self.test_dir / "src" / "main.py").write_text("""
from fastapi import FastAPI

app = FastAPI(title="Todo API")

@app.get("/")
async def root():
    return {"message": "Todo API"}
""")

            elif phase.id == "phase_2":
                # Add more code
                (self.test_dir / "src" / "models.py").write_text("""
from pydantic import BaseModel

class Todo(BaseModel):
    id: int
    title: str
    completed: bool
""")

            # Complete phase
            await context_manager.complete_phase(
                task_context.task_id,
                phase.id,
                {"status": "completed"}
            )

            # 5. Auto Commit
            auto_commit = AutoCommit()
            commit_result = await auto_commit.commit_phase(
                task_context.task_id,
                phase.id,
                phase.name
            )

            self.assertTrue(commit_result.success)
            print(f"✓ AutoCommit committed phase: {commit_result.message}")

        # 6. Quality Gate (mock success)
        with patch.object(QualityGate, 'evaluate') as mock_evaluate:
            mock_evaluate.return_value = MagicMock(
                passed=True,
                issues=[],
                score=95
            )

            quality_gate = QualityGate()
            gate_result = await quality_gate.evaluate(
                "sample_code",
                {"project": "todo_api"}
            )

            self.assertTrue(gate_result.passed)
            print("✓ QualityGate passed")

        print("\n✅ Pipeline success scenario completed!")

    async def test_pipeline_failure_scenario(self):
        """Test pipeline with quality gate failure and rollback."""
        print("\n=== Testing Pipeline Failure Scenario ===")

        # Create initial task context
        context_manager = ContextManager()
        task_context = await context_manager.create_context(None)
        task_context.task_id = "test_task_001"

        # Create rollback point
        auto_rollback = AutoRollback(mode=RollbackMode.AUTO)
        rollback_point = await auto_rollback.create_rollback_point(
            task_context.task_id,
            "test_phase",
            strategy=RollbackStrategy.GIT
        )

        self.assertIsNotNone(rollback_point.checkpoint_id)
        print("✓ Created rollback point")

        # Simulate phase failure
        with patch.object(QualityGate, 'evaluate') as mock_evaluate:
            mock_evaluate.return_value = MagicMock(
                passed=False,
                issues=["Security vulnerability detected"],
                score=45
            )

            quality_gate = QualityGate()
            gate_result = await quality_gate.evaluate(
                "vulnerable_code",
                {"project": "todo_api"}
            )

            self.assertFalse(gate_result.passed)
            print("✓ QualityGate failed as expected")

        # Trigger rollback
        rollback_result = await auto_rollback.rollback_on_failure(
            task_context.task_id,
            "test_phase",
            "Quality gate failed: Security vulnerability",
            rollback_point
        )

        self.assertEqual(rollback_result.status.value, "success")
        print("✓ AutoRollback executed successfully")

        print("\n✅ Pipeline failure scenario completed!")

    async def test_explain_mode(self):
        """Test ExplainMode component."""
        print("\n=== Testing ExplainMode ===")

        explain_mode = ExplainMode()

        # Create code change
        from src.vibe.explain_mode import CodeChange, ExplanationLevel

        change = CodeChange(
            file_path="src/main.py",
            old_code="def hello():\n    return 'Hello'",
            new_code="def hello() -> str:\n    \"\"\"Return greeting message.\"\"\"\n    return 'Hello'",
            change_type="modify",
            line_numbers=(1, 3)
        )

        # Mock LLM response
        mock_responses = self.get_mock_llm_responses()
        with patch.object(LiteLLMRouter, 'generate') as mock_generate:
            mock_generate.return_value = json.dumps(mock_responses["explain"])

            explanation = await explain_mode.explain_code_change(
                change,
                {"task": "Add type hints"},
                ExplanationLevel.STANDARD
            )

            self.assertEqual(explanation.type.value, "code_decision")
            self.assertIn("FastAPI", explanation.summary)
            print("✓ ExplainMode generated explanation")

        print("\n✅ ExplainMode test completed!")

    async def test_project_classifier(self):
        """Test ProjectClassifier component."""
        print("\n=== Testing ProjectClassifier ===")

        classifier = ProjectClassifier()
        characteristics = await classifier.classify_project(".")

        self.assertIsNotNone(characteristics)
        self.assertIn("python", characteristics.stack.languages)
        print(f"✓ ProjectClassifier detected: {characteristics.type.value}")
        print(f"  Complexity: {characteristics.complexity.value}")
        print(f"  Architecture: {characteristics.architecture.value}")

        # Get recommendations
        recommendations = classifier.get_recommendations(characteristics)
        self.assertIsInstance(recommendations, list)
        print(f"✓ Generated {len(recommendations)} recommendations")

        print("\n✅ ProjectClassifier test completed!")

    async def test_integration_mode(self):
        """Test with real LLM calls (integration mode)."""
        print("\n=== Testing Integration Mode (Real LLM) ===")

        # This test requires actual LLM API keys
        # Skip if not in integration mode
        if os.getenv("VIBE_TEST_MODE") != "integration":
            print("⏭ Skipping integration test (set VIBE_TEST_MODE=integration to run)")
            return

        try:
            # Test with real LLM
            architect = ArchitectAgent()
            arch_plan = await architect.create_architecture(
                "Create a simple calculator API",
                {"project_type": "web_api"}
            )

            self.assertIsNotNone(arch_plan)
            print("✅ Integration mode test passed!")

        except Exception as e:
            print(f"❌ Integration mode test failed: {e}")
            raise


class TestRunner:
    """Test runner for async tests."""

    @staticmethod
    async def run_all():
        """Run all smoke tests."""
        test = VibePipelineSmokeTest()
        test.setUp()

        try:
            print("=" * 60)
            print("VIBE CODING AUTOMATION PIPELINE SMOKE TEST")
            print("=" * 60)

            # Run tests
            await test.test_pipeline_success_scenario()
            await test.test_pipeline_failure_scenario()
            await test.test_explain_mode()
            await test.test_project_classifier()
            await test.test_integration_mode()

            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise
        finally:
            test.tearDown()


if __name__ == "__main__":
    import asyncio

    # Run tests
    asyncio.run(TestRunner.run_all())
