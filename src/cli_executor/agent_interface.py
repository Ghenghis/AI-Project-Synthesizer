"""
VIBE MCP - Agent CLI Interface

High-level semantic interface for AI agents to execute CLI commands.
Agents call methods like `git_commit()` instead of raw shell commands.

Features:
- Semantic methods for common operations
- Automatic error recovery
- Git operations (init, commit, push, pull, branch)
- Python operations (pip, venv, pytest, ruff, mypy)
- Node.js operations (npm, yarn, pnpm)
- Docker operations (build, compose, run)
- Cloud operations (aws, gcloud, az)

Usage:
    cli = AgentCLI()

    # Git operations
    await cli.git_init()
    await cli.git_commit("Initial commit")
    await cli.git_push()

    # Python operations
    await cli.pip_install(["requests", "fastapi"])
    await cli.pytest_run()

    # Docker operations
    await cli.docker_build("my-app:latest")
    await cli.docker_compose_up()
"""

import logging
from pathlib import Path

from src.cli_executor.error_recovery import ErrorRecovery
from src.cli_executor.executor import (
    CLIExecutor,
    CommandResult,
    ExecutionMode,
    ExecutorConfig,
)

logger = logging.getLogger(__name__)


class AgentCLI:
    """
    High-level CLI interface for AI agents.

    Provides semantic methods instead of raw commands, making it easier
    for agents to perform common development tasks safely.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        auto_recover: bool = True,
        config: ExecutorConfig | None = None,
    ):
        """
        Initialize AgentCLI.

        Args:
            working_dir: Default working directory for commands
            auto_recover: Whether to automatically attempt error recovery
            config: Custom executor configuration
        """
        self.working_dir = working_dir or Path.cwd()
        self.auto_recover = auto_recover

        # Initialize executor and recovery
        config = config or ExecutorConfig(working_dir=self.working_dir)
        self.executor = CLIExecutor(config)
        self.recovery = ErrorRecovery(self.executor)

        logger.info(f"AgentCLI initialized with working_dir={self.working_dir}")

    async def _run(
        self,
        command: str,
        working_dir: Path | None = None,
        auto_recover: bool | None = None,
        mode: ExecutionMode | None = None,
    ) -> CommandResult:
        """
        Execute a command with optional recovery.

        Args:
            command: Command to execute
            working_dir: Override working directory
            auto_recover: Override auto-recovery setting
            mode: Execution mode (LOCAL, DOCKER, WSL)

        Returns:
            CommandResult
        """
        wd = working_dir or self.working_dir
        recover = auto_recover if auto_recover is not None else self.auto_recover

        if recover:
            return await self.recovery.execute_with_recovery(
                command,
                working_dir=str(wd),
                auto_recover=True,
            )
        else:
            return await self.executor.execute(command, working_dir=wd, mode=mode)

    # ========================================================================
    # GIT OPERATIONS
    # ========================================================================

    async def git_init(self, path: Path | None = None) -> CommandResult:
        """Initialize a new Git repository."""
        return await self._run("git init", working_dir=path)

    async def git_clone(
        self,
        url: str,
        path: Path | None = None,
        branch: str | None = None,
        depth: int | None = None,
    ) -> CommandResult:
        """Clone a Git repository."""
        cmd = f"git clone {url}"
        if branch:
            cmd += f" --branch {branch}"
        if depth:
            cmd += f" --depth {depth}"
        return await self._run(cmd, working_dir=path)

    async def git_add(
        self,
        files: str = ".",
        path: Path | None = None,
    ) -> CommandResult:
        """Stage files for commit."""
        return await self._run(f"git add {files}", working_dir=path)

    async def git_commit(
        self,
        message: str,
        path: Path | None = None,
        add_all: bool = True,
    ) -> CommandResult:
        """Commit staged changes."""
        if add_all:
            await self._run("git add .", working_dir=path)

        # Escape quotes in message
        safe_message = message.replace('"', '\\"')
        return await self._run(f'git commit -m "{safe_message}"', working_dir=path)

    async def git_push(
        self,
        remote: str = "origin",
        branch: str | None = None,
        path: Path | None = None,
        force: bool = False,
        set_upstream: bool = False,
    ) -> CommandResult:
        """Push commits to remote."""
        cmd = f"git push {remote}"
        if branch:
            cmd += f" {branch}"
        if force:
            cmd += " --force"
        if set_upstream:
            cmd += " --set-upstream"
        return await self._run(cmd, working_dir=path)

    async def git_pull(
        self,
        remote: str = "origin",
        branch: str | None = None,
        path: Path | None = None,
        rebase: bool = False,
    ) -> CommandResult:
        """Pull changes from remote."""
        cmd = f"git pull {remote}"
        if branch:
            cmd += f" {branch}"
        if rebase:
            cmd += " --rebase"
        return await self._run(cmd, working_dir=path)

    async def git_checkout(
        self,
        branch: str,
        path: Path | None = None,
        create: bool = False,
    ) -> CommandResult:
        """Checkout a branch."""
        flag = "-b" if create else ""
        return await self._run(
            f"git checkout {flag} {branch}".strip(), working_dir=path
        )

    async def git_branch(
        self,
        name: str | None = None,
        path: Path | None = None,
        delete: bool = False,
        list_all: bool = False,
    ) -> CommandResult:
        """Manage Git branches."""
        if list_all:
            return await self._run("git branch -a", working_dir=path)
        if delete and name:
            return await self._run(f"git branch -d {name}", working_dir=path)
        if name:
            return await self._run(f"git branch {name}", working_dir=path)
        return await self._run("git branch", working_dir=path)

    async def git_status(self, path: Path | None = None) -> CommandResult:
        """Get repository status."""
        return await self._run("git status", working_dir=path)

    async def git_log(
        self,
        path: Path | None = None,
        count: int = 10,
        oneline: bool = True,
    ) -> CommandResult:
        """Get commit history."""
        format_flag = "--oneline" if oneline else ""
        return await self._run(
            f"git log -{count} {format_flag}".strip(), working_dir=path
        )

    async def git_diff(
        self,
        path: Path | None = None,
        staged: bool = False,
    ) -> CommandResult:
        """Show changes."""
        flag = "--staged" if staged else ""
        return await self._run(f"git diff {flag}".strip(), working_dir=path)

    async def git_stash(
        self,
        path: Path | None = None,
        pop: bool = False,
        message: str | None = None,
    ) -> CommandResult:
        """Stash changes."""
        if pop:
            return await self._run("git stash pop", working_dir=path)
        if message:
            return await self._run(f'git stash push -m "{message}"', working_dir=path)
        return await self._run("git stash", working_dir=path)

    async def git_reset(
        self,
        path: Path | None = None,
        hard: bool = False,
        commits: int = 1,
    ) -> CommandResult:
        """Reset to previous state."""
        flag = "--hard" if hard else "--soft"
        return await self._run(f"git reset {flag} HEAD~{commits}", working_dir=path)

    # ========================================================================
    # PYTHON OPERATIONS
    # ========================================================================

    async def pip_install(
        self,
        packages: list[str],
        path: Path | None = None,
        upgrade: bool = False,
        dev: bool = False,
    ) -> CommandResult:
        """Install Python packages."""
        pkg_str = " ".join(packages)
        flags = []
        if upgrade:
            flags.append("--upgrade")
        flag_str = " ".join(flags)
        return await self._run(
            f"pip install {flag_str} {pkg_str}".strip(), working_dir=path
        )

    async def pip_install_requirements(
        self,
        path: Path | None = None,
        requirements_file: str = "requirements.txt",
    ) -> CommandResult:
        """Install from requirements file."""
        return await self._run(f"pip install -r {requirements_file}", working_dir=path)

    async def pip_uninstall(
        self,
        packages: list[str],
        path: Path | None = None,
    ) -> CommandResult:
        """Uninstall Python packages."""
        pkg_str = " ".join(packages)
        return await self._run(f"pip uninstall -y {pkg_str}", working_dir=path)

    async def pip_freeze(self, path: Path | None = None) -> CommandResult:
        """List installed packages."""
        return await self._run("pip freeze", working_dir=path)

    async def pip_list(
        self,
        path: Path | None = None,
        outdated: bool = False,
    ) -> CommandResult:
        """List installed packages."""
        flag = "--outdated" if outdated else ""
        return await self._run(f"pip list {flag}".strip(), working_dir=path)

    async def create_venv(
        self,
        path: Path | None = None,
        venv_name: str = ".venv",
    ) -> CommandResult:
        """Create a virtual environment."""
        return await self._run(f"python -m venv {venv_name}", working_dir=path)

    async def activate_venv(
        self,
        path: Path | None = None,
        venv_name: str = ".venv",
    ) -> CommandResult:
        """Get activation command (returns command, doesn't activate)."""
        if self.executor.is_windows:
            return await self._run(
                f".\\{venv_name}\\Scripts\\activate", working_dir=path
            )
        return await self._run(f"source {venv_name}/bin/activate", working_dir=path)

    async def pytest_run(
        self,
        path: Path | None = None,
        test_path: str = "tests/",
        verbose: bool = True,
        coverage: bool = False,
        markers: str | None = None,
    ) -> CommandResult:
        """Run pytest."""
        cmd = f"pytest {test_path}"
        if verbose:
            cmd += " -v"
        if coverage:
            cmd += " --cov=src --cov-report=term-missing"
        if markers:
            cmd += f" -m {markers}"
        return await self._run(cmd, working_dir=path)

    async def ruff_check(
        self,
        path: Path | None = None,
        target: str = "src/",
        fix: bool = False,
    ) -> CommandResult:
        """Run ruff linter."""
        cmd = f"ruff check {target}"
        if fix:
            cmd += " --fix"
        return await self._run(cmd, working_dir=path)

    async def ruff_format(
        self,
        path: Path | None = None,
        target: str = "src/",
        check: bool = False,
    ) -> CommandResult:
        """Run ruff formatter."""
        cmd = f"ruff format {target}"
        if check:
            cmd += " --check"
        return await self._run(cmd, working_dir=path)

    async def mypy_check(
        self,
        path: Path | None = None,
        target: str = "src/",
    ) -> CommandResult:
        """Run mypy type checker."""
        return await self._run(f"mypy {target}", working_dir=path)

    async def python_run(
        self,
        script: str,
        path: Path | None = None,
        args: list[str] | None = None,
    ) -> CommandResult:
        """Run a Python script."""
        cmd = f"python {script}"
        if args:
            cmd += " " + " ".join(args)
        return await self._run(cmd, working_dir=path)

    # ========================================================================
    # NODE.JS OPERATIONS
    # ========================================================================

    async def npm_install(
        self,
        packages: list[str] | None = None,
        path: Path | None = None,
        dev: bool = False,
        global_install: bool = False,
    ) -> CommandResult:
        """Install npm packages."""
        if packages:
            pkg_str = " ".join(packages)
            flags = []
            if dev:
                flags.append("--save-dev")
            if global_install:
                flags.append("-g")
            flag_str = " ".join(flags)
            return await self._run(
                f"npm install {flag_str} {pkg_str}".strip(), working_dir=path
            )
        return await self._run("npm install", working_dir=path)

    async def npm_run(
        self,
        script: str,
        path: Path | None = None,
    ) -> CommandResult:
        """Run an npm script."""
        return await self._run(f"npm run {script}", working_dir=path)

    async def npm_build(self, path: Path | None = None) -> CommandResult:
        """Run npm build."""
        return await self._run("npm run build", working_dir=path)

    async def npm_test(self, path: Path | None = None) -> CommandResult:
        """Run npm test."""
        return await self._run("npm test", working_dir=path)

    async def npm_start(self, path: Path | None = None) -> CommandResult:
        """Run npm start."""
        return await self._run("npm start", working_dir=path)

    async def npx_run(
        self,
        command: str,
        path: Path | None = None,
    ) -> CommandResult:
        """Run npx command."""
        return await self._run(f"npx {command}", working_dir=path)

    # ========================================================================
    # DOCKER OPERATIONS
    # ========================================================================

    async def docker_build(
        self,
        tag: str,
        path: Path | None = None,
        dockerfile: str = "Dockerfile",
        no_cache: bool = False,
    ) -> CommandResult:
        """Build a Docker image."""
        cmd = f"docker build -t {tag} -f {dockerfile}"
        if no_cache:
            cmd += " --no-cache"
        cmd += " ."
        return await self._run(cmd, working_dir=path)

    async def docker_run(
        self,
        image: str,
        path: Path | None = None,
        name: str | None = None,
        ports: list[str] | None = None,
        volumes: list[str] | None = None,
        env: dict[str, str] | None = None,
        detach: bool = False,
        rm: bool = True,
    ) -> CommandResult:
        """Run a Docker container."""
        cmd = "docker run"
        if rm:
            cmd += " --rm"
        if detach:
            cmd += " -d"
        if name:
            cmd += f" --name {name}"
        if ports:
            for port in ports:
                cmd += f" -p {port}"
        if volumes:
            for vol in volumes:
                cmd += f" -v {vol}"
        if env:
            for key, value in env.items():
                cmd += f" -e {key}={value}"
        cmd += f" {image}"
        return await self._run(cmd, working_dir=path)

    async def docker_compose_up(
        self,
        path: Path | None = None,
        detach: bool = True,
        build: bool = False,
    ) -> CommandResult:
        """Start Docker Compose services."""
        cmd = "docker compose up"
        if detach:
            cmd += " -d"
        if build:
            cmd += " --build"
        return await self._run(cmd, working_dir=path)

    async def docker_compose_down(
        self,
        path: Path | None = None,
        volumes: bool = False,
    ) -> CommandResult:
        """Stop Docker Compose services."""
        cmd = "docker compose down"
        if volumes:
            cmd += " -v"
        return await self._run(cmd, working_dir=path)

    async def docker_ps(
        self,
        path: Path | None = None,
        all_containers: bool = False,
    ) -> CommandResult:
        """List Docker containers."""
        cmd = "docker ps"
        if all_containers:
            cmd += " -a"
        return await self._run(cmd, working_dir=path)

    async def docker_logs(
        self,
        container: str,
        path: Path | None = None,
        follow: bool = False,
        tail: int | None = None,
    ) -> CommandResult:
        """Get container logs."""
        cmd = f"docker logs {container}"
        if follow:
            cmd += " -f"
        if tail:
            cmd += f" --tail {tail}"
        return await self._run(cmd, working_dir=path)

    async def docker_stop(
        self,
        container: str,
        path: Path | None = None,
    ) -> CommandResult:
        """Stop a container."""
        return await self._run(f"docker stop {container}", working_dir=path)

    async def docker_rm(
        self,
        container: str,
        path: Path | None = None,
        force: bool = False,
    ) -> CommandResult:
        """Remove a container."""
        cmd = f"docker rm {container}"
        if force:
            cmd += " -f"
        return await self._run(cmd, working_dir=path)

    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================

    async def mkdir(
        self,
        directory: str,
        path: Path | None = None,
        parents: bool = True,
    ) -> CommandResult:
        """Create a directory."""
        if self.executor.is_windows:
            cmd = f"New-Item -ItemType Directory -Path '{directory}' -Force"
        else:
            flag = "-p" if parents else ""
            cmd = f"mkdir {flag} {directory}"
        return await self._run(cmd, working_dir=path)

    async def rm(
        self,
        target: str,
        path: Path | None = None,
        recursive: bool = False,
        force: bool = False,
    ) -> CommandResult:
        """Remove files or directories."""
        if self.executor.is_windows:
            cmd = f"Remove-Item -Path '{target}'"
            if recursive:
                cmd += " -Recurse"
            if force:
                cmd += " -Force"
        else:
            flags = ""
            if recursive:
                flags += "r"
            if force:
                flags += "f"
            cmd = f"rm -{flags} {target}" if flags else f"rm {target}"
        return await self._run(cmd, working_dir=path)

    async def cp(
        self,
        source: str,
        dest: str,
        path: Path | None = None,
        recursive: bool = False,
    ) -> CommandResult:
        """Copy files or directories."""
        if self.executor.is_windows:
            cmd = f"Copy-Item -Path '{source}' -Destination '{dest}'"
            if recursive:
                cmd += " -Recurse"
        else:
            flag = "-r" if recursive else ""
            cmd = f"cp {flag} {source} {dest}"
        return await self._run(cmd, working_dir=path)

    async def mv(
        self,
        source: str,
        dest: str,
        path: Path | None = None,
    ) -> CommandResult:
        """Move files or directories."""
        if self.executor.is_windows:
            cmd = f"Move-Item -Path '{source}' -Destination '{dest}'"
        else:
            cmd = f"mv {source} {dest}"
        return await self._run(cmd, working_dir=path)

    async def ls(
        self,
        target: str = ".",
        path: Path | None = None,
        all_files: bool = False,
        long_format: bool = False,
    ) -> CommandResult:
        """List directory contents."""
        if self.executor.is_windows:
            cmd = f"Get-ChildItem -Path '{target}'"
            if all_files:
                cmd += " -Force"
        else:
            flags = ""
            if all_files:
                flags += "a"
            if long_format:
                flags += "l"
            cmd = f"ls -{flags} {target}" if flags else f"ls {target}"
        return await self._run(cmd, working_dir=path)

    async def cat(
        self,
        file: str,
        path: Path | None = None,
    ) -> CommandResult:
        """Read file contents."""
        if self.executor.is_windows:
            cmd = f"Get-Content -Path '{file}'"
        else:
            cmd = f"cat {file}"
        return await self._run(cmd, working_dir=path)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def run_raw(
        self,
        command: str,
        path: Path | None = None,
        auto_recover: bool = True,
    ) -> CommandResult:
        """Run a raw command (escape hatch for custom commands)."""
        return await self._run(command, working_dir=path, auto_recover=auto_recover)

    def get_stats(self) -> dict:
        """Get execution statistics."""
        return {
            "executor_stats": self.executor.get_stats(),
            "recovery_success_rate": self.recovery.get_success_rate(),
        }

    def get_history(self, limit: int = 50) -> list[CommandResult]:
        """Get command history."""
        return self.executor.get_history(limit)


# Global instance for convenience
_agent_cli: AgentCLI | None = None


def get_agent_cli() -> AgentCLI:
    """Get or create global AgentCLI instance."""
    global _agent_cli
    if _agent_cli is None:
        _agent_cli = AgentCLI()
    return _agent_cli
