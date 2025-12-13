"""
Auto Rollback for VIBE MCP

Automatically rolls back to last successful checkpoint on failures:
- Multiple rollback strategies (Git, file system, state)
- Integration with ContextManager checkpoints
- Configurable rollback modes (auto, interactive, dry-run)
- Rollback pattern tracking for learning
- Failure analysis and prevention

Provides robust error recovery for the Vibe Coding pipeline.
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.memory.mem0_integration import MemorySystem
from src.vibe.context_manager import ContextManager


class RollbackStrategy(Enum):
    """Available rollback strategies."""
    GIT = "git"  # Use Git to rollback commits
    FILE_SYSTEM = "file_system"  # Restore files from backup
    STATE = "state"  # Restore only in-memory state
    HYBRID = "hybrid"  # Combination of strategies


class RollbackMode(Enum):
    """Rollback execution modes."""
    AUTO = "auto"  # Automatically rollback on failure
    INTERACTIVE = "interactive"  # Ask for confirmation
    DRY_RUN = "dry_run"  # Show what would be rolled back
    DISABLED = "disabled"  # No automatic rollback


class RollbackStatus(Enum):
    """Status of a rollback operation."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"


@dataclass
class RollbackPoint:
    """A point in time that can be rolled back to."""
    checkpoint_id: str
    timestamp: datetime
    strategy: RollbackStrategy
    metadata: dict[str, Any]
    artifacts: dict[str, Any]  # Backed up files, commits, etc.


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    status: RollbackStatus
    strategy_used: RollbackStrategy
    files_restored: list[str]
    commits_reverted: list[str]
    errors: list[str]
    metadata: dict[str, Any]


class AutoRollback:
    """
    Automatic rollback system for phase failures.

    Features:
    - Multiple rollback strategies
    - Checkpoint integration
    - Pattern learning
    - Failure analysis
    - Configurable modes
    """

    def __init__(self, mode: RollbackMode = RollbackMode.INTERACTIVE):
        self.config = get_settings()
        self.mode = mode
        self.context_manager = ContextManager()
        self.memory = MemorySystem()

        # Rollback history
        self._rollback_history: list[RollbackResult] = []

        # Configuration
        self.max_backup_files = 100
        self.backup_dir = Path.cwd() / ".vibe" / "rollbacks"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Git detection
        self._is_git_repo = self._detect_git_repo()

    def _detect_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def create_rollback_point(self, task_id: str, phase_id: str,
                                  strategy: RollbackStrategy = RollbackStrategy.HYBRID,
                                  files: list[str] | None = None) -> RollbackPoint:
        """
        Create a rollback point before executing a phase.

        Args:
            task_id: The task ID
            phase_id: The phase ID
            strategy: Rollback strategy to use
            files: Specific files to backup

        Returns:
            RollbackPoint with backup information
        """
        timestamp = datetime.now()
        artifacts = {}

        # Create checkpoint in ContextManager
        checkpoint_id = await self.context_manager.create_checkpoint(
            task_id, phase_id, f"pre_phase_{phase_id}"
        )

        # Strategy-specific backups
        if strategy in [RollbackStrategy.GIT, RollbackStrategy.HYBRID] and self._is_git_repo:
            artifacts["git"] = await self._backup_git_state()

        if strategy in [RollbackStrategy.FILE_SYSTEM, RollbackStrategy.HYBRID]:
            artifacts["files"] = await self._backup_files(files or self._get_tracked_files())

        # Create rollback point
        rollback_point = RollbackPoint(
            checkpoint_id=checkpoint_id,
            timestamp=timestamp,
            strategy=strategy,
            metadata={
                "task_id": task_id,
                "phase_id": phase_id,
                "mode": self.mode.value,
                "git_repo": self._is_git_repo
            },
            artifacts=artifacts
        )

        # Save rollback point
        await self._save_rollback_point(rollback_point)

        return rollback_point

    async def rollback_on_failure(self, task_id: str, phase_id: str,
                                failure_reason: str,
                                rollback_point: RollbackPoint | None = None) -> RollbackResult:
        """
        Perform rollback when a phase fails.

        Args:
            task_id: The task ID
            phase_id: The phase ID that failed
            failure_reason: Description of the failure
            rollback_point: Specific rollback point to use

        Returns:
            RollbackResult with operation details
        """
        # Get latest rollback point if not specified
        if not rollback_point:
            rollback_point = await self._get_latest_rollback_point(task_id, phase_id)
            if not rollback_point:
                return RollbackResult(
                    status=RollbackStatus.FAILED,
                    strategy_used=RollbackStrategy.STATE,
                    files_restored=[],
                    commits_reverted=[],
                    errors=["No rollback point found"],
                    metadata={}
                )

        # Check if rollback is enabled
        if self.mode == RollbackMode.DISABLED:
            return RollbackResult(
                status=RollbackStatus.SKIPPED,
                strategy_used=rollback_point.strategy,
                files_restored=[],
                commits_reverted=[],
                errors=["Rollback is disabled"],
                metadata={}
            )

        # Dry run mode
        if self.mode == RollbackMode.DRY_RUN:
            return await self._dry_run_rollback(rollback_point)

        # Interactive mode
        if self.mode == RollbackMode.INTERACTIVE:
            if not await self._confirm_rollback(rollback_point, failure_reason):
                return RollbackResult(
                    status=RollbackStatus.SKIPPED,
                    strategy_used=rollback_point.strategy,
                    files_restored=[],
                    commits_reverted=[],
                    errors=["User cancelled rollback"],
                    metadata={}
                )

        # Perform rollback
        result = await self._execute_rollback(rollback_point)

        # Track failure pattern
        await self._track_failure_pattern(task_id, phase_id, failure_reason, result)

        # Store rollback history
        self._rollback_history.append(result)

        return result

    async def _execute_rollback(self, rollback_point: RollbackPoint) -> RollbackResult:
        """Execute the actual rollback."""
        files_restored = []
        commits_reverted = []
        errors = []

        try:
            # Restore ContextManager state
            success = await self.context_manager.restore_checkpoint(
                rollback_point.metadata["task_id"],
                rollback_point.checkpoint_id
            )
            if not success:
                errors.append("Failed to restore context state")

            # Strategy-specific rollback
            if rollback_point.strategy in [RollbackStrategy.GIT, RollbackStrategy.HYBRID]:
                if "git" in rollback_point.artifacts:
                    git_result = await self._rollback_git(rollback_point.artifacts["git"])
                    commits_reverted = git_result.get("commits", [])
                    if git_result.get("errors"):
                        errors.extend(git_result["errors"])

            if rollback_point.strategy in [RollbackStrategy.FILE_SYSTEM, RollbackStrategy.HYBRID]:
                if "files" in rollback_point.artifacts:
                    file_result = await self._rollback_files(rollback_point.artifacts["files"])
                    files_restored = file_result.get("files", [])
                    if file_result.get("errors"):
                        errors.extend(file_result["errors"])

            # Determine status
            status = RollbackStatus.SUCCESS if not errors else RollbackStatus.PARTIAL

            return RollbackResult(
                status=status,
                strategy_used=rollback_point.strategy,
                files_restored=files_restored,
                commits_reverted=commits_reverted,
                errors=errors,
                metadata={
                    "rollback_point_id": rollback_point.checkpoint_id,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            return RollbackResult(
                status=RollbackStatus.FAILED,
                strategy_used=rollback_point.strategy,
                files_restored=files_restored,
                commits_reverted=commits_reverted,
                errors=[str(e)],
                metadata={}
            )

    async def _backup_git_state(self) -> dict[str, Any]:
        """Backup current Git state."""
        if not self._is_git_repo:
            return {}

        import subprocess

        try:
            # Get current commit
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True
            )
            current_commit = result.stdout.strip() if result.returncode == 0 else None

            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True
            )
            staged_files = result.stdout.strip().split('\n') if result.stdout else []

            # Get modified files
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True
            )
            modified_files = result.stdout.strip().split('\n') if result.stdout else []

            return {
                "commit": current_commit,
                "staged_files": [f for f in staged_files if f],
                "modified_files": [f for f in modified_files if f],
                "branch": self._get_current_branch()
            }
        except Exception as e:
            return {"error": str(e)}

    async def _rollback_git(self, git_state: dict[str, Any]) -> dict[str, Any]:
        """Rollback Git state."""
        if not self._is_git_repo or not git_state.get("commit"):
            return {"errors": ["No Git state to rollback to"]}

        import subprocess

        commits = []
        errors = []

        try:
            # Reset to commit
            result = subprocess.run(
                ["git", "reset", "--hard", git_state["commit"]],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                commits.append(git_state["commit"])
            else:
                errors.append(f"Git reset failed: {result.stderr}")

            # Clear staging area
            subprocess.run(["git", "reset", "HEAD"], capture_output=True)

            return {
                "commits": commits,
                "errors": errors
            }
        except Exception as e:
            return {"errors": [str(e)]}

    async def _backup_files(self, files: list[str]) -> dict[str, Any]:
        """Backup files to rollback directory."""
        backup_info = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        for file_path in files:
            try:
                source = Path(file_path)
                if source.exists():
                    # Calculate relative path
                    rel_path = source.relative_to(Path.cwd())
                    dest = backup_path / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(source, dest)
                    backup_info[str(rel_path)] = str(dest)
            except Exception as e:
                backup_info[file_path] = {"error": str(e)}

        return {
            "backup_path": str(backup_path),
            "files": backup_info,
            "timestamp": timestamp
        }

    async def _rollback_files(self, file_backup: dict[str, Any]) -> dict[str, Any]:
        """Restore files from backup."""
        files = []
        errors = []

        Path(file_backup["backup_path"])

        for rel_path, backup_file in file_backup["files"].items():
            if isinstance(backup_file, dict) and "error" in backup_file:
                errors.append(f"Failed to backup {rel_path}: {backup_file['error']}")
                continue

            try:
                source = Path(backup_file)
                dest = Path.cwd() / rel_path

                if source.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    files.append(str(dest))
            except Exception as e:
                errors.append(f"Failed to restore {rel_path}: {str(e)}")

        return {
            "files": files,
            "errors": errors
        }

    def _get_tracked_files(self) -> list[str]:
        """Get list of tracked files in the project."""
        files = []

        # Git tracked files
        if self._is_git_repo:
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "ls-files"],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    files = result.stdout.strip().split('\n')
            except:
                pass

        # If not git or error, get common project files
        if not files:
            patterns = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.md", "*.json", "*.yaml", "*.yml"]
            for pattern in patterns:
                files.extend(str(f) for f in Path.cwd().rglob(pattern))

        return [f for f in files if f and not any(skip in f for skip in [".git", "__pycache__", "node_modules"])]

    def _get_current_branch(self) -> str:
        """Get current Git branch."""
        if not self._is_git_repo:
            return "unknown"

        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    async def _dry_run_rollback(self, rollback_point: RollbackPoint) -> RollbackResult:
        """Perform a dry run rollback showing what would be done."""
        actions = []

        actions.append(f"Would restore context to checkpoint: {rollback_point.checkpoint_id}")

        if rollback_point.strategy in [RollbackStrategy.GIT, RollbackStrategy.HYBRID]:
            if "git" in rollback_point.artifacts:
                git_state = rollback_point.artifacts["git"]
                actions.append(f"Would reset Git to commit: {git_state.get('commit', 'unknown')}")
                if git_state.get("staged_files"):
                    actions.append(f"Would unstage {len(git_state['staged_files'])} files")

        if rollback_point.strategy in [RollbackStrategy.FILE_SYSTEM, RollbackStrategy.HYBRID]:
            if "files" in rollback_point.artifacts:
                file_count = len([f for f in rollback_point.artifacts["files"].values()
                                if not isinstance(f, dict)])
                actions.append(f"Would restore {file_count} files")

        return RollbackResult(
            status=RollbackStatus.DRY_RUN,
            strategy_used=rollback_point.strategy,
            files_restored=[],
            commits_reverted=[],
            errors=[],
            metadata={
                "actions": actions,
                "message": "Dry run - no changes made"
            }
        )

    async def _confirm_rollback(self, rollback_point: RollbackPoint, failure_reason: str) -> bool:
        """Ask user to confirm rollback."""
        print(f"\n⚠️ Phase failed: {failure_reason}")
        print(f"📅 Rollback point created: {rollback_point.timestamp}")
        print(f"🔄 Strategy: {rollback_point.strategy.value}")

        if rollback_point.strategy in [RollbackStrategy.GIT, RollbackStrategy.HYBRID]:
            if "git" in rollback_point.artifacts:
                git_state = rollback_point.artifacts["git"]
                print(f"📦 Git commit: {git_state.get('commit', 'unknown')[:8]}")

        if rollback_point.strategy in [RollbackStrategy.FILE_SYSTEM, RollbackStrategy.HYBRID]:
            if "files" in rollback_point.artifacts:
                file_count = len([f for f in rollback_point.artifacts["files"].values()
                                if not isinstance(f, dict)])
                print(f"📁 Files to restore: {file_count}")

        while True:
            response = input("\nRollback to this point? [y/N/skip] ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            elif response in ['skip', 'disable']:
                self.mode = RollbackMode.DISABLED
                return False
            else:
                print("Please enter 'y', 'n', or 'skip'")

    async def _save_rollback_point(self, rollback_point: RollbackPoint) -> None:
        """Save rollback point to disk and memory."""
        # Save to disk
        rollback_file = self.backup_dir / f"rollback_{rollback_point.checkpoint_id}.json"

        data = {
            "checkpoint_id": rollback_point.checkpoint_id,
            "timestamp": rollback_point.timestamp.isoformat(),
            "strategy": rollback_point.strategy.value,
            "metadata": rollback_point.metadata,
            "artifacts": rollback_point.artifacts
        }

        with open(rollback_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Save to memory
        await self.memory.add(
            content=json.dumps(data),
            category="ROLLBACK",
            tags=["rollback", rollback_point.metadata["task_id"], rollback_point.metadata["phase_id"]],
            importance=0.8
        )

    async def _get_latest_rollback_point(self, task_id: str, phase_id: str) -> RollbackPoint | None:
        """Get the latest rollback point for a task/phase."""
        # Search memory
        results = await self.memory.search(
            query=f"{task_id} {phase_id}",
            category="ROLLBACK",
            limit=10
        )

        if not results:
            return None

        # Get latest
        latest = None
        latest_time = None

        for result in results:
            try:
                data = json.loads(result["content"])
                timestamp = datetime.fromisoformat(data["timestamp"])

                if not latest_time or timestamp > latest_time:
                    latest = data
                    latest_time = timestamp
            except:
                continue

        if latest:
            return RollbackPoint(
                checkpoint_id=latest["checkpoint_id"],
                timestamp=datetime.fromisoformat(latest["timestamp"]),
                strategy=RollbackStrategy(latest["strategy"]),
                metadata=latest["metadata"],
                artifacts=latest["artifacts"]
            )

        return None

    async def _track_failure_pattern(self, task_id: str, phase_id: str,
                                    failure_reason: str, result: RollbackResult) -> None:
        """Track failure patterns for learning."""
        pattern = {
            "task_id": task_id,
            "phase_id": phase_id,
            "failure_reason": failure_reason,
            "rollback_successful": result.status == RollbackStatus.SUCCESS,
            "strategy_used": result.strategy_used.value,
            "timestamp": datetime.now().isoformat(),
            "error_count": len(result.errors)
        }

        await self.memory.add(
            content=json.dumps(pattern),
            category="FAILURE_PATTERN",
            tags=["failure", task_id, phase_id],
            importance=0.7
        )

    def get_rollback_history(self, task_id: str | None = None) -> list[RollbackResult]:
        """Get rollback history."""
        if task_id:
            return [r for r in self._rollback_history
                   if r.metadata.get("rollback_point_id", "").startswith(task_id)]
        return self._rollback_history.copy()

    def set_mode(self, mode: RollbackMode) -> None:
        """Change rollback mode."""
        self.mode = mode
        print(f"Rollback mode set to: {mode.value}")

    def cleanup_old_backups(self, days: int = 7) -> int:
        """Clean up old backup files."""
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        cleaned = 0

        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                try:
                    if backup_dir.stat().st_mtime < cutoff:
                        shutil.rmtree(backup_dir)
                        cleaned += 1
                except:
                    pass

        # Clean up rollback point files
        for rollback_file in self.backup_dir.glob("rollback_*.json"):
            try:
                if rollback_file.stat().st_mtime < cutoff:
                    rollback_file.unlink()
                    cleaned += 1
            except:
                pass

        return cleaned


# CLI interface for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        # Create auto rollback with interactive mode
        auto_rollback = AutoRollback(mode=RollbackMode.INTERACTIVE)

        # Test creating rollback point
        print("Creating rollback point...")
        rollback_point = await auto_rollback.create_rollback_point(
            task_id="test_task",
            phase_id="test_phase",
            strategy=RollbackStrategy.HYBRID
        )

        print(f"Created rollback point: {rollback_point.checkpoint_id}")
        print(f"Strategy: {rollback_point.strategy.value}")
        print(f"Artifacts: {list(rollback_point.artifacts.keys())}")

        # Test dry run rollback
        print("\nPerforming dry run rollback...")
        result = await auto_rollback.rollback_on_failure(
            task_id="test_task",
            phase_id="test_phase",
            failure_reason="Test failure - syntax error",
            rollback_point=rollback_point
        )

        print(f"Status: {result.status.value}")
        if result.metadata.get("actions"):
            print("Actions that would be taken:")
            for action in result.metadata["actions"]:
                print(f"  - {action}")

        # Clean up
        cleaned = auto_rollback.cleanup_old_backups(0)
        print(f"\nCleaned up {cleaned} backup files")

    asyncio.run(main())
