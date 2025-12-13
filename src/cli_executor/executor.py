"""
VIBE MCP - CLI Executor

Core command execution engine with safety checks, multiple execution modes,
and comprehensive error detection.

Features:
- Multiple execution modes: LOCAL, DOCKER, WSL, REMOTE
- Blocked dangerous commands
- Timeout handling
- Error type detection
- Async execution support

Usage:
    executor = CLIExecutor()
    result = await executor.execute("pip install requests")

    if result.success:
        print(result.stdout)
    else:
        print(f"Error: {result.error_type}")
"""

import asyncio
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Command execution environment."""
    LOCAL = "local"      # Direct execution on host
    DOCKER = "docker"    # Sandboxed Docker container
    WSL = "wsl"          # Windows Subsystem for Linux
    REMOTE = "remote"    # Remote SSH execution


class ShellType(Enum):
    """Shell type for command execution."""
    POWERSHELL = "powershell"
    BASH = "bash"
    CMD = "cmd"
    ZSH = "zsh"


class ErrorType(Enum):
    """Categorized error types for recovery."""
    DEPENDENCY_MISSING = "dependency_missing"
    PERMISSION_DENIED = "permission_denied"
    FILE_NOT_FOUND = "file_not_found"
    SYNTAX_ERROR = "syntax_error"
    VERSION_CONFLICT = "version_conflict"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    DOCKER_ERROR = "docker_error"
    GIT_ERROR = "git_error"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    success: bool
    error_type: ErrorType | None = None
    suggested_fix: str | None = None
    execution_mode: ExecutionMode = ExecutionMode.LOCAL
    working_dir: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_type": self.error_type.value if self.error_type else None,
            "suggested_fix": self.suggested_fix,
            "execution_mode": self.execution_mode.value,
            "working_dir": self.working_dir,
        }


@dataclass
class ExecutorConfig:
    """Configuration for CLI executor."""
    default_mode: ExecutionMode = ExecutionMode.LOCAL
    default_shell: ShellType = ShellType.POWERSHELL
    timeout_seconds: int = 300
    working_dir: Path = field(default_factory=Path.cwd)

    # Safety settings
    blocked_commands: list = field(default_factory=lambda: [
        # Destructive file operations
        "rm -rf /",
        "rm -rf /*",
        "del /s /q c:\\",
        "format c:",
        "format d:",
        "rd /s /q c:\\",
        # Fork bombs
        ":(){:|:&};:",
        ":(){ :|:& };:",
        # System damage
        "dd if=/dev/zero",
        "mkfs.",
        "> /dev/sda",
        # Registry damage (Windows)
        "reg delete HKLM",
        "reg delete HKCU",
        # Shutdown/reboot
        "shutdown /s",
        "shutdown -h",
        "reboot",
        "init 0",
        "init 6",
    ])

    # Patterns that require confirmation
    dangerous_patterns: list = field(default_factory=lambda: [
        r"rm\s+-rf",
        r"del\s+/[sq]",
        r"rmdir\s+/s",
        r"DROP\s+DATABASE",
        r"DROP\s+TABLE",
        r"TRUNCATE\s+TABLE",
        r"sudo\s+rm",
        r"chmod\s+777",
        r"chmod\s+-R\s+777",
    ])

    # Docker settings
    docker_image: str = "python:3.11-slim"
    docker_timeout: int = 600

    # WSL settings
    wsl_distro: str | None = None


class CLIExecutor:
    """
    Executes CLI commands for agents with safety and error recovery.

    This is the core execution engine that agents use to run commands.
    It provides:
    - Safety checks to block dangerous commands
    - Multiple execution modes (local, Docker, WSL)
    - Automatic error type detection
    - Timeout handling
    - Async execution support
    """

    def __init__(self, config: ExecutorConfig | None = None):
        """Initialize the CLI executor."""
        self.config = config or ExecutorConfig()
        self._detect_environment()
        self._command_history: list[CommandResult] = []

    def _detect_environment(self) -> None:
        """Detect available execution environments."""
        self.is_windows = os.name == "nt"
        self.has_wsl = self._check_wsl()
        self.has_docker = self._check_docker()

        # Set default shell based on OS
        if self.is_windows:
            self.config.default_shell = ShellType.POWERSHELL
        else:
            self.config.default_shell = ShellType.BASH

        logger.info(
            f"Environment detected: Windows={self.is_windows}, "
            f"WSL={self.has_wsl}, Docker={self.has_docker}"
        )

    def _check_wsl(self) -> bool:
        """Check if WSL is available."""
        if not self.is_windows:
            return False
        try:
            result = subprocess.run(
                ["wsl", "--status"],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _check_docker(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _is_command_blocked(self, command: str) -> bool:
        """Check if command is in the blocked list."""
        command_lower = command.lower().strip()
        for blocked in self.config.blocked_commands:
            if blocked.lower() in command_lower:
                logger.warning(f"Blocked dangerous command: {command}")
                return True
        return False

    def _is_command_dangerous(self, command: str) -> bool:
        """Check if command matches dangerous patterns."""
        for pattern in self.config.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def _detect_error_type(self, stderr: str, stdout: str = "") -> ErrorType:
        """Detect the type of error from stderr/stdout."""
        combined = f"{stderr} {stdout}".lower()

        patterns = {
            ErrorType.DEPENDENCY_MISSING: [
                r"modulenotfounderror",
                r"importerror",
                r"cannot find module",
                r"no module named",
                r"package .* is not installed",
                r"command not found",
                r"'.*' is not recognized",
                r"npm err! 404",
                r"could not find a version",
            ],
            ErrorType.PERMISSION_DENIED: [
                r"permission denied",
                r"access is denied",
                r"eacces",
                r"operation not permitted",
                r"requires elevation",
                r"run as administrator",
            ],
            ErrorType.FILE_NOT_FOUND: [
                r"filenotfounderror",
                r"no such file or directory",
                r"cannot find path",
                r"the system cannot find",
                r"enoent",
            ],
            ErrorType.SYNTAX_ERROR: [
                r"syntaxerror",
                r"unexpected token",
                r"parsing error",
                r"invalid syntax",
            ],
            ErrorType.VERSION_CONFLICT: [
                r"version conflict",
                r"incompatible versions",
                r"version .* not found",
                r"requires python",
                r"unsupported python",
            ],
            ErrorType.NETWORK_ERROR: [
                r"connection refused",
                r"network unreachable",
                r"timeout",
                r"could not resolve host",
                r"ssl certificate",
                r"connection reset",
            ],
            ErrorType.DOCKER_ERROR: [
                r"docker daemon",
                r"cannot connect to docker",
                r"docker: error",
                r"no such container",
                r"image not found",
            ],
            ErrorType.GIT_ERROR: [
                r"fatal: not a git repository",
                r"git: command not found",
                r"failed to push",
                r"merge conflict",
                r"authentication failed",
            ],
        }

        for error_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, combined, re.IGNORECASE):
                    return error_type

        return ErrorType.UNKNOWN

    async def execute(
        self,
        command: str,
        mode: ExecutionMode | None = None,
        working_dir: Path | None = None,
        timeout: int | None = None,
        env: dict | None = None,
    ) -> CommandResult:
        """
        Execute a CLI command.

        Args:
            command: The command to execute
            mode: Execution mode (LOCAL, DOCKER, WSL, REMOTE)
            working_dir: Working directory for the command
            timeout: Timeout in seconds
            env: Additional environment variables

        Returns:
            CommandResult with execution details
        """
        start_time = time.time()
        mode = mode or self.config.default_mode
        working_dir = working_dir or self.config.working_dir
        timeout = timeout or self.config.timeout_seconds

        # Safety check - blocked commands
        if self._is_command_blocked(command):
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr="Command blocked for safety reasons",
                duration_ms=0,
                success=False,
                error_type=ErrorType.BLOCKED,
                execution_mode=mode,
                working_dir=str(working_dir),
            )
            self._command_history.append(result)
            return result

        # Log dangerous commands (but allow them)
        if self._is_command_dangerous(command):
            logger.warning(f"Executing potentially dangerous command: {command}")

        try:
            if mode == ExecutionMode.LOCAL:
                result = await self._execute_local(command, working_dir, timeout, env)
            elif mode == ExecutionMode.DOCKER:
                result = await self._execute_docker(command, working_dir, timeout, env)
            elif mode == ExecutionMode.WSL:
                result = await self._execute_wsl(command, working_dir, timeout, env)
            elif mode == ExecutionMode.REMOTE:
                raise NotImplementedError("Remote execution not yet implemented")
            else:
                raise ValueError(f"Unsupported execution mode: {mode}")

            duration_ms = (time.time() - start_time) * 1000

            # Detect error type if command failed
            error_type = None
            if result.returncode != 0:
                stderr_text = result.stderr.decode("utf-8", errors="replace")
                stdout_text = result.stdout.decode("utf-8", errors="replace")
                error_type = self._detect_error_type(stderr_text, stdout_text)

            cmd_result = CommandResult(
                command=command,
                exit_code=result.returncode,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
                duration_ms=duration_ms,
                success=result.returncode == 0,
                error_type=error_type,
                execution_mode=mode,
                working_dir=str(working_dir),
            )

            self._command_history.append(cmd_result)

            # Log result
            if cmd_result.success:
                logger.debug(f"Command succeeded: {command[:50]}...")
            else:
                logger.warning(
                    f"Command failed: {command[:50]}... "
                    f"(exit={result.returncode}, error={error_type})"
                )

            return cmd_result

        except TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_ms=duration_ms,
                success=False,
                error_type=ErrorType.TIMEOUT,
                execution_mode=mode,
                working_dir=str(working_dir),
            )
            self._command_history.append(result)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(f"Command execution error: {e}")
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                success=False,
                error_type=ErrorType.UNKNOWN,
                execution_mode=mode,
                working_dir=str(working_dir),
            )
            self._command_history.append(result)
            return result

    async def _execute_local(
        self,
        command: str,
        working_dir: Path,
        timeout: int,
        env: dict | None = None,
    ) -> subprocess.CompletedProcess:
        """Execute command locally."""
        # Build environment
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        # Build command based on shell
        if self.is_windows:
            full_command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
        else:
            full_command = ["bash", "-c", command]

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                full_command,
                cwd=working_dir,
                capture_output=True,
                timeout=timeout,
                env=cmd_env,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )
        )

    async def _execute_docker(
        self,
        command: str,
        working_dir: Path,
        timeout: int,
        env: dict | None = None,
    ) -> subprocess.CompletedProcess:
        """Execute command in Docker container."""
        if not self.has_docker:
            raise RuntimeError("Docker is not available")

        # Build docker command
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{working_dir.absolute()}:/workspace",
            "-w", "/workspace",
        ]

        # Add environment variables
        if env:
            for key, value in env.items():
                docker_cmd.extend(["-e", f"{key}={value}"])

        docker_cmd.extend([
            self.config.docker_image,
            "bash", "-c", command
        ])

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                docker_cmd,
                capture_output=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )
        )

    async def _execute_wsl(
        self,
        command: str,
        working_dir: Path,
        timeout: int,
        env: dict | None = None,
    ) -> subprocess.CompletedProcess:
        """Execute command in WSL."""
        if not self.has_wsl:
            raise RuntimeError("WSL is not available")

        # Convert Windows path to WSL path
        wsl_path = str(working_dir).replace("\\", "/")
        if len(wsl_path) > 1 and wsl_path[1] == ":":
            wsl_path = f"/mnt/{wsl_path[0].lower()}{wsl_path[2:]}"

        # Build WSL command
        wsl_command = f"cd {wsl_path} && {command}"

        wsl_cmd = ["wsl"]
        if self.config.wsl_distro:
            wsl_cmd.extend(["-d", self.config.wsl_distro])
        wsl_cmd.extend(["bash", "-c", wsl_command])

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                wsl_cmd,
                capture_output=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        )

    def get_history(self, limit: int = 100) -> list[CommandResult]:
        """Get command execution history."""
        return self._command_history[-limit:]

    def clear_history(self) -> None:
        """Clear command history."""
        self._command_history.clear()

    def get_stats(self) -> dict:
        """Get execution statistics."""
        if not self._command_history:
            return {
                "total_commands": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
            }

        successful = sum(1 for r in self._command_history if r.success)
        total = len(self._command_history)
        avg_duration = sum(r.duration_ms for r in self._command_history) / total

        return {
            "total_commands": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total * 100,
            "avg_duration_ms": avg_duration,
        }


# Convenience function for quick execution
async def run_command(
    command: str,
    working_dir: Path | None = None,
    timeout: int = 300,
) -> CommandResult:
    """
    Quick command execution helper.

    Usage:
        result = await run_command("pip install requests")
    """
    executor = CLIExecutor()
    return await executor.execute(command, working_dir=working_dir, timeout=timeout)
