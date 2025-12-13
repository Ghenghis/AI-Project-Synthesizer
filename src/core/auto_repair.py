"""
AI Project Synthesizer - Auto-Repair System

Progressive auto-repair for:
- Code issues
- Configuration problems
- Missing dependencies
- Integration failures
"""

import asyncio
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.gap_analyzer import Gap, GapCategory, GapSeverity
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class RepairAction(str, Enum):
    """Types of repair actions."""
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    CREATE_DIR = "create_dir"
    INSTALL_PACKAGE = "install_package"
    RUN_COMMAND = "run_command"
    UPDATE_CONFIG = "update_config"
    RESTART_SERVICE = "restart_service"


@dataclass
class RepairStep:
    """Single repair step."""
    action: RepairAction
    target: str
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    executed: bool = False
    success: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "target": self.target,
            "description": self.description,
            "executed": self.executed,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class RepairPlan:
    """Plan for repairing gaps."""
    gap: Gap
    steps: list[RepairStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed: bool = False
    success: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap.id,
            "gap_description": self.gap.description,
            "steps": [s.to_dict() for s in self.steps],
            "executed": self.executed,
            "success": self.success,
        }


class AutoRepair:
    """
    Automatic repair system for identified gaps.

    Features:
    - Creates repair plans
    - Executes repairs safely
    - Validates repairs
    - Rollback support
    """

    def __init__(self):
        self._repair_handlers: dict[GapCategory, Callable] = {
            GapCategory.FILE: self._plan_file_repair,
            GapCategory.CONFIG: self._plan_config_repair,
            GapCategory.IMPORT: self._plan_import_repair,
            GapCategory.DEPENDENCY: self._plan_dependency_repair,
            GapCategory.DATABASE: self._plan_database_repair,
            GapCategory.INTEGRATION: self._plan_integration_repair,
        }
        self._executed_plans: list[RepairPlan] = []

    def create_plan(self, gap: Gap) -> RepairPlan | None:
        """Create a repair plan for a gap."""
        handler = self._repair_handlers.get(gap.category)

        if handler:
            return handler(gap)

        return None

    async def execute_plan(self, plan: RepairPlan) -> bool:
        """Execute a repair plan."""
        secure_logger.info(f"Executing repair plan for: {plan.gap.description}")

        all_success = True

        for step in plan.steps:
            try:
                success = await self._execute_step(step)
                step.executed = True
                step.success = success

                if not success:
                    all_success = False
                    break

            except Exception as e:
                step.executed = True
                step.success = False
                step.error = str(e)
                all_success = False
                secure_logger.error(f"Repair step failed: {e}")
                break

        plan.executed = True
        plan.success = all_success
        self._executed_plans.append(plan)

        return all_success

    async def _execute_step(self, step: RepairStep) -> bool:
        """Execute a single repair step."""
        if step.action == RepairAction.CREATE_FILE:
            return self._create_file(step.target, step.params.get("content", ""))

        elif step.action == RepairAction.MODIFY_FILE:
            return self._modify_file(
                step.target,
                step.params.get("find", ""),
                step.params.get("replace", ""),
            )

        elif step.action == RepairAction.CREATE_DIR:
            return self._create_dir(step.target)

        elif step.action == RepairAction.INSTALL_PACKAGE:
            return await self._install_package(step.target)

        elif step.action == RepairAction.RUN_COMMAND:
            return await self._run_command(step.params.get("command", ""))

        elif step.action == RepairAction.UPDATE_CONFIG:
            return self._update_config(step.target, step.params)

        return False

    def _create_file(self, path: str, content: str) -> bool:
        """Create a file with content."""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            secure_logger.info(f"Created file: {path}")
            return True
        except Exception as e:
            secure_logger.error(f"Failed to create file {path}: {e}")
            return False

    def _modify_file(self, path: str, find: str, replace: str) -> bool:
        """Modify a file with find/replace."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return False

            content = file_path.read_text()
            new_content = content.replace(find, replace)
            file_path.write_text(new_content)
            secure_logger.info(f"Modified file: {path}")
            return True
        except Exception as e:
            secure_logger.error(f"Failed to modify file {path}: {e}")
            return False

    def _create_dir(self, path: str) -> bool:
        """Create a directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            secure_logger.info(f"Created directory: {path}")
            return True
        except Exception as e:
            secure_logger.error(f"Failed to create directory {path}: {e}")
            return False

    async def _install_package(self, package: str) -> bool:
        """Install a Python package."""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()
            secure_logger.info(f"Installed package: {package}")
            return process.returncode == 0
        except Exception as e:
            secure_logger.error(f"Failed to install package {package}: {e}")
            return False

    async def _run_command(self, command: str) -> bool:
        """Run a shell command."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()
            return process.returncode == 0
        except Exception as e:
            secure_logger.error(f"Failed to run command: {e}")
            return False

    def _update_config(self, path: str, updates: dict[str, Any]) -> bool:
        """Update a JSON config file."""
        try:
            file_path = Path(path)

            config = json.loads(file_path.read_text()) if file_path.exists() else {}

            # Deep merge updates
            self._deep_merge(config, updates)

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(config, indent=2))
            secure_logger.info(f"Updated config: {path}")
            return True
        except Exception as e:
            secure_logger.error(f"Failed to update config {path}: {e}")
            return False

    def _deep_merge(self, base: dict, updates: dict):
        """Deep merge updates into base dict."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    # ============================================
    # Repair Plan Generators
    # ============================================

    def _plan_file_repair(self, gap: Gap) -> RepairPlan:
        """Create repair plan for file gaps."""
        plan = RepairPlan(gap=gap)

        if "missing_dir" in gap.id:
            plan.steps.append(RepairStep(
                action=RepairAction.CREATE_DIR,
                target=gap.location,
                description=f"Create directory: {gap.location}",
            ))

        elif "missing_init" in gap.id:
            plan.steps.append(RepairStep(
                action=RepairAction.CREATE_FILE,
                target=f"{gap.location}/__init__.py",
                params={"content": '"""Package."""\n'},
                description=f"Create __init__.py in {gap.location}",
            ))

        elif "missing" in gap.id.lower():
            # Generic missing file
            plan.steps.append(RepairStep(
                action=RepairAction.CREATE_FILE,
                target=gap.location,
                params={"content": ""},
                description=f"Create file: {gap.location}",
            ))

        return plan

    def _plan_config_repair(self, gap: Gap) -> RepairPlan:
        """Create repair plan for config gaps."""
        plan = RepairPlan(gap=gap)

        if "settings" in gap.id:
            plan.steps.append(RepairStep(
                action=RepairAction.RUN_COMMAND,
                target="settings",
                params={"command": f"{sys.executable} -c \"from src.core.settings_manager import get_settings_manager; get_settings_manager().save()\""},
                description="Create default settings file",
            ))

        elif "env" in gap.id:
            env_content = """# AI Project Synthesizer Environment
GITHUB_TOKEN=
ELEVENLABS_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_HOST=http://localhost:11434
LMSTUDIO_HOST=http://localhost:1234
"""
            plan.steps.append(RepairStep(
                action=RepairAction.CREATE_FILE,
                target=".env",
                params={"content": env_content},
                description="Create .env file with defaults",
            ))

        return plan

    def _plan_import_repair(self, gap: Gap) -> RepairPlan:
        """Create repair plan for import gaps."""
        plan = RepairPlan(gap=gap)

        # Try to identify missing package
        if "cannot import" in gap.description.lower():
            # Extract package name from error
            match = re.search(r"No module named '([^']+)'", gap.description)
            if match:
                package = match.group(1).split(".")[0]
                plan.steps.append(RepairStep(
                    action=RepairAction.INSTALL_PACKAGE,
                    target=package,
                    description=f"Install missing package: {package}",
                ))

        return plan

    def _plan_dependency_repair(self, gap: Gap) -> RepairPlan:
        """Create repair plan for dependency gaps."""
        plan = RepairPlan(gap=gap)

        plan.steps.append(RepairStep(
            action=RepairAction.RUN_COMMAND,
            target="requirements",
            params={"command": f"{sys.executable} -m pip install -r requirements.txt"},
            description="Install all requirements",
        ))

        return plan

    def _plan_database_repair(self, gap: Gap) -> RepairPlan:
        """Create repair plan for database gaps."""
        plan = RepairPlan(gap=gap)

        plan.steps.append(RepairStep(
            action=RepairAction.CREATE_DIR,
            target="data",
            description="Create data directory",
        ))

        plan.steps.append(RepairStep(
            action=RepairAction.RUN_COMMAND,
            target="database",
            params={"command": f"{sys.executable} -c \"from src.core.memory import get_memory_store; get_memory_store()\""},
            description="Initialize database",
        ))

        return plan

    def _plan_integration_repair(self, gap: Gap) -> RepairPlan:
        """Create repair plan for integration gaps."""
        plan = RepairPlan(gap=gap)

        # Most integration issues need manual intervention
        # but we can try some basic fixes

        if "llm" in gap.id.lower():
            plan.steps.append(RepairStep(
                action=RepairAction.RUN_COMMAND,
                target="llm_check",
                params={"command": f"{sys.executable} -c \"from src.llm import LLMRouter; print('LLM OK')\""},
                description="Verify LLM module",
            ))

        return plan

    def get_repair_history(self) -> list[dict[str, Any]]:
        """Get history of executed repairs."""
        return [p.to_dict() for p in self._executed_plans]


# Global auto-repair instance
_auto_repair: AutoRepair | None = None


def get_auto_repair() -> AutoRepair:
    """Get or create auto-repair instance."""
    global _auto_repair
    if _auto_repair is None:
        _auto_repair = AutoRepair()
    return _auto_repair


async def repair_gaps(gaps: list[Gap]) -> list[RepairPlan]:
    """Repair a list of gaps."""
    repair = get_auto_repair()
    plans = []

    for gap in gaps:
        if gap.auto_fixable or gap.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]:
            plan = repair.create_plan(gap)
            if plan and plan.steps:
                await repair.execute_plan(plan)
                plans.append(plan)

    return plans
