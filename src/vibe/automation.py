"""
AI Project Synthesizer - Vibe Coding Automation

Automated workflows for "vibe coding" - AI-assisted development that:
- Auto-fixes code issues on save
- Generates tests automatically
- Reviews code in real-time
- Manages CI/CD healing

Integrates with GitHub Actions for seamless automation.
"""

import asyncio
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)
logger = secure_logger.logger


class AutomationMode(str, Enum):
    """Automation modes."""

    PASSIVE = "passive"  # Only report issues
    ASSISTED = "assisted"  # Suggest fixes, user applies
    AGGRESSIVE = "aggressive"  # Auto-fix everything safe
    FULL_AUTO = "full_auto"  # Fix everything including risky


@dataclass
class AutomationConfig:
    """Configuration for vibe automation."""

    mode: AutomationMode = AutomationMode.ASSISTED
    auto_lint: bool = True
    auto_format: bool = True
    auto_test: bool = False
    auto_commit: bool = False
    watch_patterns: list[str] = field(default_factory=lambda: ["*.py"])
    ignore_patterns: list[str] = field(
        default_factory=lambda: ["__pycache__", ".git", "*.pyc"]
    )
    llm_enabled: bool = True
    max_auto_fixes_per_run: int = 10


@dataclass
class AutomationEvent:
    """Event triggered by automation."""

    event_type: str
    file_path: str | None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)
    action_taken: str | None = None
    success: bool = True


class VibeAutomation:
    """
    Main automation orchestrator for vibe coding.

    Coordinates:
    - File watching
    - Auto-fixing
    - Test generation
    - CI/CD integration
    """

    def __init__(
        self, project_root: Path | None = None, config: AutomationConfig | None = None
    ):
        self.project_root = project_root or Path.cwd()
        self.config = config or AutomationConfig()
        self.settings = get_settings()
        self._event_log: list[AutomationEvent] = []
        self._running = False

    def log_event(self, event: AutomationEvent):
        """Log an automation event."""
        self._event_log.append(event)
        logger.info(f"[{event.event_type}] {event.file_path}: {event.action_taken}")

    def run_lint_fix(self, file_path: Path | None = None) -> tuple[bool, str]:
        """Run ruff lint fix on file or project."""
        target = str(file_path) if file_path else "src/ tests/"
        try:
            result = subprocess.run(
                f"ruff check {target} --fix",
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def run_format(self, file_path: Path | None = None) -> tuple[bool, str]:
        """Run ruff format on file or project."""
        target = str(file_path) if file_path else "src/ tests/"
        try:
            result = subprocess.run(
                f"ruff format {target}",
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def run_tests(self, file_path: Path | None = None) -> tuple[bool, str]:
        """Run pytest on file or project."""
        if file_path:
            # Find corresponding test file
            test_file = self._find_test_file(file_path)
            target = str(test_file) if test_file else "tests/"
        else:
            target = "tests/"

        try:
            result = subprocess.run(
                f"pytest {target} -x -q",
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def _find_test_file(self, source_file: Path) -> Path | None:
        """Find test file corresponding to source file."""
        # Convert src/module/file.py -> tests/test_module/test_file.py
        rel_path = source_file.relative_to(self.project_root)
        parts = list(rel_path.parts)

        if parts[0] == "src":
            parts[0] = "tests"
            parts[-1] = f"test_{parts[-1]}"
            test_path = self.project_root / Path(*parts)
            if test_path.exists():
                return test_path

        return None

    async def on_file_change(self, file_path: Path) -> list[AutomationEvent]:
        """Handle file change event."""
        events = []

        if file_path.suffix != ".py":
            return events

        # Auto-lint
        if self.config.auto_lint and self.config.mode in [
            AutomationMode.AGGRESSIVE,
            AutomationMode.FULL_AUTO,
        ]:
            success, output = self.run_lint_fix(file_path)
            events.append(
                AutomationEvent(
                    event_type="lint_fix",
                    file_path=str(file_path),
                    action_taken="Applied ruff --fix" if success else "Lint fix failed",
                    success=success,
                    details={"output": output[:500]},
                )
            )

        # Auto-format
        if self.config.auto_format and self.config.mode in [
            AutomationMode.AGGRESSIVE,
            AutomationMode.FULL_AUTO,
        ]:
            success, output = self.run_format(file_path)
            events.append(
                AutomationEvent(
                    event_type="format",
                    file_path=str(file_path),
                    action_taken="Formatted with ruff" if success else "Format failed",
                    success=success,
                )
            )

        # Auto-test
        if self.config.auto_test:
            success, output = self.run_tests(file_path)
            events.append(
                AutomationEvent(
                    event_type="test",
                    file_path=str(file_path),
                    action_taken="Tests passed" if success else "Tests failed",
                    success=success,
                    details={"output": output[:1000]},
                )
            )

        for event in events:
            self.log_event(event)

        return events

    def get_project_health(self) -> dict[str, Any]:
        """Get overall project health status."""
        health = {
            "lint": {"status": "unknown", "issues": 0},
            "tests": {"status": "unknown", "passed": 0, "failed": 0},
            "coverage": {"status": "unknown", "percent": 0},
            "last_check": datetime.now().isoformat(),
        }

        # Check lint
        try:
            result = subprocess.run(
                "ruff check src/ tests/ --output-format=json",
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.stdout:
                issues = json.loads(result.stdout)
                health["lint"]["issues"] = len(issues)
                health["lint"]["status"] = "ok" if len(issues) == 0 else "warning"
        except Exception:
            health["lint"]["status"] = "error"

        # Check tests
        try:
            result = subprocess.run(
                "pytest tests/ --tb=no -q",
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            health["tests"]["status"] = "ok" if result.returncode == 0 else "failing"
        except Exception:
            health["tests"]["status"] = "error"

        return health

    def generate_health_report(self) -> str:
        """Generate markdown health report."""
        health = self.get_project_health()

        status_emoji = {
            "ok": "✅",
            "warning": "⚠️",
            "failing": "❌",
            "error": "🔴",
            "unknown": "❓",
        }

        report = f"""# Project Health Report

Generated: {health["last_check"]}

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Linting | {status_emoji.get(health["lint"]["status"], "❓")} | {health["lint"]["issues"]} issues |
| Tests | {status_emoji.get(health["tests"]["status"], "❓")} | - |
| Coverage | {status_emoji.get(health["coverage"]["status"], "❓")} | {health["coverage"]["percent"]}% |

## Recent Events

"""
        for event in self._event_log[-10:]:
            emoji = "✅" if event.success else "❌"
            report += f"- {emoji} [{event.event_type}] {event.file_path}: {event.action_taken}\n"

        return report


class GitHubActionsIntegration:
    """
    Integration with GitHub Actions for CI/CD automation.
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.workflows_dir = self.project_root / ".github" / "workflows"

    def list_workflows(self) -> list[dict[str, Any]]:
        """List all workflow files."""
        workflows = []
        if self.workflows_dir.exists():
            for f in self.workflows_dir.glob("*.yml"):
                workflows.append(
                    {
                        "name": f.stem,
                        "path": str(f.relative_to(self.project_root)),
                        "size": f.stat().st_size,
                    }
                )
        return workflows

    def check_workflow_syntax(self, workflow_path: Path) -> tuple[bool, str]:
        """Check workflow YAML syntax."""
        try:
            import yaml

            content = workflow_path.read_text()
            yaml.safe_load(content)
            return True, "Valid YAML"
        except Exception as e:
            return False, str(e)

    def get_workflow_status(self) -> dict[str, str]:
        """Get status of all workflows (requires gh CLI)."""
        status = {}
        try:
            result = subprocess.run(
                "gh run list --limit 10 --json name,status,conclusion",
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                runs = json.loads(result.stdout)
                for run in runs:
                    name = run.get("name", "unknown")
                    conclusion = run.get("conclusion") or run.get("status", "unknown")
                    status[name] = conclusion
        except Exception as e:
            logger.error(f"Could not get workflow status: {e}")

        return status

    def trigger_workflow(self, workflow_name: str) -> tuple[bool, str]:
        """Trigger a workflow dispatch event."""
        try:
            result = subprocess.run(
                f"gh workflow run {workflow_name}.yml",
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)


# CLI interface
async def main():
    """CLI for vibe automation."""
    import argparse

    parser = argparse.ArgumentParser(description="Vibe Coding Automation")
    parser.add_argument(
        "command", choices=["health", "fix", "test", "watch", "workflows"]
    )
    parser.add_argument("--file", help="Specific file to process")
    parser.add_argument(
        "--mode", choices=["passive", "assisted", "aggressive"], default="assisted"
    )
    args = parser.parse_args()

    automation = VibeAutomation(config=AutomationConfig(mode=AutomationMode(args.mode)))

    if args.command == "health":
        print(automation.generate_health_report())

    elif args.command == "fix":
        file_path = Path(args.file) if args.file else None
        success, output = automation.run_lint_fix(file_path)
        print(f"Lint fix: {'✅' if success else '❌'}")
        success, output = automation.run_format(file_path)
        print(f"Format: {'✅' if success else '❌'}")

    elif args.command == "test":
        file_path = Path(args.file) if args.file else None
        success, output = automation.run_tests(file_path)
        print(output)

    elif args.command == "workflows":
        gh = GitHubActionsIntegration()
        workflows = gh.list_workflows()
        print(f"Found {len(workflows)} workflows:")
        for w in workflows:
            print(f"  - {w['name']}")

        status = gh.get_workflow_status()
        if status:
            print("\nRecent run status:")
            for name, result in status.items():
                emoji = (
                    "✅"
                    if result == "success"
                    else "❌"
                    if result == "failure"
                    else "🔄"
                )
                print(f"  {emoji} {name}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
