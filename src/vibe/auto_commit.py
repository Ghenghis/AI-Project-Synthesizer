"""
Auto Commit for VIBE MCP

Automatically commits changes after each phase:
- Git integration for version control
- Configurable commit strategies
- Phase-based commit messages
- Change detection and staging
- Integration with ContextManager

Provides reliable version control for structured processes.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings


class CommitStrategy(Enum):
    """Strategies for automatic commits."""
    AFTER_EACH_PHASE = "after_each_phase"
    ON_COMPLETION = "on_completion"
    ON_FAILURE = "on_failure"
    MANUAL = "manual"


class CommitStatus(Enum):
    """Status of a commit operation."""
    SUCCESS = "success"
    NO_CHANGES = "no_changes"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CommitInfo:
    """Information about a commit."""
    commit_hash: str
    phase_id: str
    timestamp: datetime
    message: str
    files_changed: list[str]
    additions: int
    deletions: int
    status: CommitStatus


@dataclass
class CommitConfig:
    """Configuration for auto-commit behavior."""
    strategy: CommitStrategy
    auto_push: bool = False
    create_branch: bool = False
    branch_prefix: str = "feature/vibe"
    include_artifacts: bool = True
    ignore_patterns: list[str] = None

    def __post_init__(self):
        if self.ignore_patterns is None:
            self.ignore_patterns = [
                "*.pyc",
                "__pycache__/",
                ".pytest_cache/",
                ".coverage",
                "htmlcov/",
                ".DS_Store",
                "*.log",
                ".env.local",
                "node_modules/",
                ".venv/",
                "venv/"
            ]


class AutoCommit:
    """
    Handles automatic Git commits for task phases.

    Features:
    - Multiple commit strategies
    - Intelligent change detection
    - Structured commit messages
    - Branch management
    - Conflict detection
    """

    def __init__(self, config: CommitConfig | None = None):
        self.config = config or CommitConfig(strategy=CommitStrategy.AFTER_EACH_PHASE)
        self.app_config = get_settings()

        # Git repository detection
        self.repo_root = self._find_repo_root()
        self.is_git_repo = self.repo_root is not None

        # Commit history
        self._commits: list[CommitInfo] = []

        # Phase tracking
        self._committed_phases: set[str] = set()

    def _find_repo_root(self) -> Path | None:
        """Find the Git repository root."""
        current = Path.cwd()

        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        return None

    def _run_git_command(self, args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
        """Run a Git command."""
        work_dir = cwd or self.repo_root

        if not work_dir:
            raise ValueError("Not in a Git repository")

        return subprocess.run(
            ["git"] + args,
            cwd=work_dir,
            capture_output=True,
            text=True
        )

    def _get_changed_files(self, _phase_id: str) -> list[str]:
        """Get list of files changed since last phase commit."""
        if not self.is_git_repo:
            return []

        # Get staged and unstaged changes
        files = set()

        # Staged files
        result = self._run_git_command(["diff", "--cached", "--name-only"])
        if result.stdout:
            files.update(result.stdout.strip().split('\n'))

        # Unstaged files
        result = self._run_git_command(["diff", "--name-only"])
        if result.stdout:
            files.update(result.stdout.strip().split('\n'))

        # Untracked files
        result = self._run_git_command(["ls-files", "--others", "--exclude-standard"])
        if result.stdout:
            files.update(result.stdout.strip().split('\n'))

        # Filter out ignored patterns
        filtered_files = []
        for file in files:
            if not file:
                continue

            # Check ignore patterns
            ignored = False
            for pattern in self.config.ignore_patterns:
                if self._match_pattern(file, pattern):
                    ignored = True
                    break

            if not ignored:
                filtered_files.append(file)

        return filtered_files

    def _match_pattern(self, file: str, pattern: str) -> bool:
        """Check if file matches ignore pattern."""
        import fnmatch

        # Handle directory patterns
        if pattern.endswith('/'):
            return file.startswith(pattern) or '/' in file and file.split('/')[0] == pattern.rstrip('/')

        # Handle file patterns
        return fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(file.split('/')[-1], pattern)

    def _stage_changes(self, files: list[str]) -> bool:
        """Stage specific files for commit."""
        if not files:
            return True

        for file in files:
            result = self._run_git_command(["add", file])
            if result.returncode != 0:
                print(f"Failed to stage {file}: {result.stderr}")
                return False

        return True

    def _get_diff_stats(self) -> tuple[int, int]:
        """Get addition and deletion counts for staged changes."""
        result = self._run_git_command(["diff", "--cached", "--numstat"])

        additions = 0
        deletions = 0

        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        additions += int(parts[0]) if parts[0] != '-' else 0
                        deletions += int(parts[1]) if parts[1] != '-' else 0

        return additions, deletions

    def _create_commit_message(self, phase_id: str, phase_name: str,
                             artifacts: dict[str, Any] | None = None) -> str:
        """Create a structured commit message for a phase."""
        message = [f"feat: Complete phase {phase_id} - {phase_name}"]
        message.append("")
        message.append(f"Phase: {phase_id}")
        message.append(f"Completed at: {datetime.now().isoformat()}")

        if artifacts and self.config.include_artifacts:
            message.append("")
            message.append("Artifacts:")
            for key, value in artifacts.items():
                if isinstance(value, list) and value:
                    message.append(f"  - {key}: {', '.join(map(str, value[:3]))}")
                    if len(value) > 3:
                        message.append(f"    and {len(value) - 3} more")
                elif value:
                    message.append(f"  - {key}: {str(value)[:100]}")

        message.append("")
        message.append("Committed automatically by VIBE MCP")

        return '\n'.join(message)

    async def commit_phase(self, task_id: str, _phase_id: str, phase_name: str,
                          artifacts: dict[str, Any] | None = None,
                          force: bool = False) -> CommitInfo:
        """
        Commit changes for a completed phase.

        Args:
            task_id: The task ID
            phase_id: The phase ID
            phase_name: Human-readable phase name
            artifacts: Artifacts created in this phase
            force: Force commit even if no changes

        Returns:
            CommitInfo with commit details
        """
        if not self.is_git_repo:
            return CommitInfo(
                commit_hash="",
                phase_id=_phase_id,
                timestamp=datetime.now(),
                message="Not in a Git repository",
                files_changed=[],
                additions=0,
                deletions=0,
                status=CommitStatus.FAILED
            )

        # Check if already committed
        if _phase_id in self._committed_phases and not force:
            return CommitInfo(
                commit_hash="",
                phase_id=_phase_id,
                timestamp=datetime.now(),
                message="Phase already committed",
                files_changed=[],
                additions=0,
                deletions=0,
                status=CommitStatus.SKIPPED
            )

        # Get changed files
        changed_files = self._get_changed_files(_phase_id)

        if not changed_files and not force:
            return CommitInfo(
                commit_hash="",
                phase_id=_phase_id,
                timestamp=datetime.now(),
                message="No changes to commit",
                files_changed=[],
                additions=0,
                deletions=0,
                status=CommitStatus.NO_CHANGES
            )

        # Stage changes
        if not self._stage_changes(changed_files):
            return CommitInfo(
                commit_hash="",
                phase_id=_phase_id,
                timestamp=datetime.now(),
                message="Failed to stage changes",
                files_changed=[],
                additions=0,
                deletions=0,
                status=CommitStatus.FAILED
            )

        # Get diff stats
        additions, deletions = self._get_diff_stats()

        # Create commit message
        commit_message = self._create_commit_message(_phase_id, phase_name, artifacts)

        # Create commit
        result = self._run_git_command(["commit", "-m", commit_message])

        if result.returncode != 0:
            return CommitInfo(
                commit_hash="",
                phase_id=_phase_id,
                timestamp=datetime.now(),
                message=f"Commit failed: {result.stderr}",
                files_changed=changed_files,
                additions=additions,
                deletions=deletions,
                status=CommitStatus.FAILED
            )

        # Get commit hash
        hash_result = self._run_git_command(["rev-parse", "HEAD"])
        commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else ""

        # Create commit info
        commit_info = CommitInfo(
            commit_hash=commit_hash,
            phase_id=_phase_id,
            timestamp=datetime.now(),
            message=commit_message,
            files_changed=changed_files,
            additions=additions,
            deletions=deletions,
            status=CommitStatus.SUCCESS
        )

        # Track commit
        self._commits.append(commit_info)
        self._committed_phases.add(_phase_id)

        # Auto push if configured
        if self.config.auto_push:
            await self._push_changes()

        return commit_info

    async def _push_changes(self) -> bool:
        """Push changes to remote repository."""
        if not self.is_git_repo:
            return False

        # Check if remote exists
        result = self._run_git_command(["remote", "get-url", "origin"])
        if result.returncode != 0:
            print("No remote 'origin' configured")
            return False

        # Push changes
        result = self._run_git_command(["push", "origin", "HEAD"])

        return result.returncode == 0

    async def create_feature_branch(self, task_id: str, task_name: str) -> bool:
        """
        Create a feature branch for the task.

        Args:
            task_id: The task ID
            task_name: Human-readable task name

        Returns:
            True if branch created successfully
        """
        if not self.is_git_repo or not self.config.create_branch:
            return False

        # Sanitize branch name
        branch_name = f"{self.config.branch_prefix}/{task_id}"
        branch_name = branch_name.replace(' ', '-').replace('_', '-').lower()

        # Create and checkout branch
        result = self._run_git_command(["checkout", "-b", branch_name])

        if result.returncode != 0:
            print(f"Failed to create branch: {result.stderr}")
            return False

        return True

    def get_commit_history(self, task_id: str | None = None) -> list[CommitInfo]:
        """
        Get commit history.

        Args:
            task_id: Filter by task ID if provided

        Returns:
            List of commits
        """
        if task_id:
            # Filter by task ID (phase IDs contain task_id)
            return [c for c in self._commits if task_id in c.phase_id]
        return self._commits.copy()

    def rollback_to_commit(self, commit_hash: str) -> bool:
        """
        Rollback to a specific commit.

        Args:
            commit_hash: The commit hash to rollback to

        Returns:
            True if rollback successful
        """
        if not self.is_git_repo:
            return False

        # Soft reset (keeps changes)
        result = self._run_git_command(["reset", "--soft", commit_hash])

        return result.returncode == 0

    def get_status(self) -> dict[str, Any]:
        """Get current repository status."""
        if not self.is_git_repo:
            return {"status": "not_a_repo"}

        # Get current branch
        branch_result = self._run_git_command(["branch", "--show-current"])
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Get status
        status_result = self._run_git_command(["status", "--porcelain"])

        staged = 0
        modified = 0
        untracked = 0

        if status_result.stdout:
            for line in status_result.stdout.strip().split('\n'):
                if line:
                    if line.startswith(' '):
                        untracked += 1
                    elif line[0] in ['M', 'A', 'D', 'R', 'C']:
                        if line[1] != ' ':
                            staged += 1
                        else:
                            modified += 1

        return {
            "status": "ok",
            "branch": current_branch,
            "staged": staged,
            "modified": modified,
            "untracked": untracked,
            "total_commits": len(self._commits),
            "committed_phases": len(self._committed_phases)
        }

    def save_config(self, config_path: str) -> None:
        """Save configuration to file."""
        config_data = {
            "strategy": self.config.strategy.value,
            "auto_push": self.config.auto_push,
            "create_branch": self.config.create_branch,
            "branch_prefix": self.config.branch_prefix,
            "include_artifacts": self.config.include_artifacts,
            "ignore_patterns": self.config.ignore_patterns
        }

        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

    def load_config(self, config_path: str) -> bool:
        """Load configuration from file."""
        try:
            with open(config_path) as f:
                config_data = json.load(f)

            self.config = CommitConfig(
                strategy=CommitStrategy(config_data["strategy"]),
                auto_push=config_data.get("auto_push", False),
                create_branch=config_data.get("create_branch", False),
                branch_prefix=config_data.get("branch_prefix", "feature/vibe"),
                include_artifacts=config_data.get("include_artifacts", True),
                ignore_patterns=config_data.get("ignore_patterns", [])
            )

            return True
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False


# CLI interface for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        # Create auto commit with default config
        auto_commit = AutoCommit()

        # Check status
        status = auto_commit.get_status()
        print(f"Git Status: {status}")

        if status["status"] == "ok":
            # Simulate phase completion
            artifacts = {
                "files_created": ["main.py", "utils.py"],
                "functions_added": 5,
                "tests_written": 3
            }

            commit_info = await auto_commit.commit_phase(
                task_id="demo_task",
                phase_id="phase_1",
                phase_name="Setup project structure",
                artifacts=artifacts
            )

            print(f"\nCommit Status: {commit_info.status.value}")
            print(f"Commit Hash: {commit_info.commit_hash}")
            print(f"Files Changed: {len(commit_info.files_changed)}")
            print(f"Additions: {commit_info.additions}")
            print(f"Deletions: {commit_info.deletions}")
        else:
            print("Not in a Git repository")

    asyncio.run(main())
