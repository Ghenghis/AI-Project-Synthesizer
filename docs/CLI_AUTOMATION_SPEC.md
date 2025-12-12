# 🖥️ CLI Automation Specification

## Overview

This document defines how AI agents execute **all CLI commands** on behalf of users. The goal is **100% autonomous operation** where users never need to touch the terminal.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CLI AUTOMATION LAYER                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     COMMAND ROUTER                                   │    │
│  │  Receives command intent from agents, validates, and routes          │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                           │
│          ┌───────────────────────┼───────────────────────┐                  │
│          ▼                       ▼                       ▼                  │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐           │
│  │   SANDBOX     │      │   LOCAL       │      │   REMOTE      │           │
│  │   EXECUTOR    │      │   EXECUTOR    │      │   EXECUTOR    │           │
│  │               │      │               │      │               │           │
│  │ • Docker      │      │ • PowerShell  │      │ • SSH         │           │
│  │ • Isolation   │      │ • WSL2/Bash   │      │ • kubectl     │           │
│  │ • Safe ops    │      │ • System cmds │      │ • Cloud CLIs  │           │
│  └───────────────┘      └───────────────┘      └───────────────┘           │
│          │                       │                       │                  │
│          └───────────────────────┼───────────────────────┘                  │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     OUTPUT PROCESSOR                                 │    │
│  │  • Parse stdout/stderr                                              │    │
│  │  • Detect errors                                                    │    │
│  │  • Extract actionable info                                          │    │
│  │  • Report to agent                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                  │                                           │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     ERROR RECOVERY                                   │    │
│  │  • Auto-retry with fixes                                            │    │
│  │  • Dependency installation                                          │    │
│  │  • Permission escalation (with approval)                            │    │
│  │  • Alternative command suggestion                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Command Categories

### 1. Package Management

| Tool | Platform | Commands |
|------|----------|----------|
| **pip** | Python | `pip install`, `pip freeze`, `pip uninstall` |
| **poetry** | Python | `poetry add`, `poetry install`, `poetry build` |
| **npm** | Node.js | `npm install`, `npm run`, `npm audit` |
| **pnpm** | Node.js | `pnpm add`, `pnpm install`, `pnpm build` |
| **cargo** | Rust | `cargo add`, `cargo build`, `cargo test` |
| **go** | Go | `go get`, `go build`, `go mod` |

### 2. Version Control

| Command | Purpose |
|---------|---------|
| `git init` | Initialize repository |
| `git clone <url>` | Clone repository |
| `git add .` | Stage changes |
| `git commit -m "<msg>"` | Commit changes |
| `git push` | Push to remote |
| `git pull` | Pull from remote |
| `git branch` | Manage branches |
| `git merge` | Merge branches |
| `git stash` | Stash changes |

### 3. Docker Operations

| Command | Purpose |
|---------|---------|
| `docker build` | Build image |
| `docker run` | Run container |
| `docker compose up` | Start services |
| `docker compose down` | Stop services |
| `docker logs` | View logs |
| `docker exec` | Execute in container |
| `docker push` | Push to registry |

### 4. Testing & Quality

| Command | Purpose |
|---------|---------|
| `pytest` | Run Python tests |
| `jest` | Run JS tests |
| `ruff check` | Python linting |
| `eslint` | JS linting |
| `mypy` | Type checking |
| `bandit` | Security scan |

### 5. Build & Deploy

| Command | Purpose |
|---------|---------|
| `python -m build` | Build Python package |
| `npm run build` | Build Node app |
| `docker build` | Build container |
| `kubectl apply` | Deploy to K8s |
| `aws deploy` | Deploy to AWS |

---

## Implementation

**File: `src/cli/executor.py`**

```python
"""
CLI Executor - Runs shell commands for agents.

Supports:
- PowerShell (Windows)
- Bash (WSL2, Linux, macOS)
- Docker sandbox for untrusted code
"""

import asyncio
import logging
import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Where to execute commands."""
    LOCAL = "local"           # Direct on host
    DOCKER = "docker"         # In Docker container
    WSL = "wsl"              # In WSL2
    REMOTE = "remote"        # Via SSH


class ShellType(Enum):
    """Shell to use."""
    POWERSHELL = "powershell"
    BASH = "bash"
    CMD = "cmd"
    ZSH = "zsh"


@dataclass
class CommandResult:
    """Result of command execution."""
    
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    success: bool
    error_type: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class ExecutorConfig:
    """Configuration for CLI executor."""
    
    default_mode: ExecutionMode = ExecutionMode.LOCAL
    default_shell: ShellType = ShellType.POWERSHELL
    timeout_seconds: int = 300
    working_dir: Path = Path(".")
    env_vars: dict = field(default_factory=dict)
    docker_image: str = "python:3.11-slim"
    allowed_commands: list = field(default_factory=list)
    blocked_commands: list = field(default_factory=lambda: [
        "rm -rf /",
        "format",
        "del /s /q",
        ":(){:|:&};:",  # Fork bomb
    ])


class CLIExecutor:
    """
    Executes CLI commands for agents.
    
    Features:
    - Multiple execution modes (local, Docker, WSL)
    - Output parsing and error detection
    - Auto-retry with fixes
    - Security safeguards
    """
    
    def __init__(self, config: Optional[ExecutorConfig] = None):
        self.config = config or ExecutorConfig()
        self._detect_environment()
    
    def _detect_environment(self) -> None:
        """Detect available shells and execution modes."""
        self.is_windows = os.name == "nt"
        self.has_wsl = self._check_wsl()
        self.has_docker = self._check_docker()
        
        # Set optimal defaults
        if self.is_windows:
            self.config.default_shell = ShellType.POWERSHELL
        else:
            self.config.default_shell = ShellType.BASH
    
    def _check_wsl(self) -> bool:
        """Check if WSL is available."""
        try:
            result = subprocess.run(
                ["wsl", "--status"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute."""
        command_lower = command.lower()
        
        for blocked in self.config.blocked_commands:
            if blocked.lower() in command_lower:
                logger.warning(f"Blocked dangerous command: {command}")
                return False
        
        return True
    
    async def execute(
        self,
        command: str,
        mode: Optional[ExecutionMode] = None,
        shell: Optional[ShellType] = None,
        working_dir: Optional[Path] = None,
        env_vars: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """
        Execute a CLI command.
        
        Args:
            command: Command to execute
            mode: Execution mode (local, docker, wsl)
            shell: Shell to use
            working_dir: Working directory
            env_vars: Environment variables
            timeout: Timeout in seconds
        
        Returns:
            CommandResult with output and status
        """
        import time
        start_time = time.time()
        
        # Safety check
        if not self._is_safe_command(command):
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr="Command blocked for safety",
                duration_ms=0,
                success=False,
                error_type="BLOCKED",
            )
        
        # Use defaults if not specified
        mode = mode or self.config.default_mode
        shell = shell or self.config.default_shell
        working_dir = working_dir or self.config.working_dir
        timeout = timeout or self.config.timeout_seconds
        
        # Merge environment variables
        env = os.environ.copy()
        env.update(self.config.env_vars)
        if env_vars:
            env.update(env_vars)
        
        try:
            if mode == ExecutionMode.LOCAL:
                result = await self._execute_local(command, shell, working_dir, env, timeout)
            elif mode == ExecutionMode.DOCKER:
                result = await self._execute_docker(command, working_dir, env, timeout)
            elif mode == ExecutionMode.WSL:
                result = await self._execute_wsl(command, working_dir, env, timeout)
            else:
                raise ValueError(f"Unsupported mode: {mode}")
            
            duration_ms = (time.time() - start_time) * 1000
            
            return CommandResult(
                command=command,
                exit_code=result.returncode,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
                duration_ms=duration_ms,
                success=result.returncode == 0,
                error_type=self._detect_error_type(result.stderr.decode()) if result.returncode != 0 else None,
            )
            
        except asyncio.TimeoutError:
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_ms=(time.time() - start_time) * 1000,
                success=False,
                error_type="TIMEOUT",
            )
        except Exception as e:
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=(time.time() - start_time) * 1000,
                success=False,
                error_type="EXCEPTION",
            )
    
    async def _execute_local(
        self,
        command: str,
        shell: ShellType,
        working_dir: Path,
        env: dict,
        timeout: int,
    ) -> subprocess.CompletedProcess:
        """Execute command locally."""
        
        if shell == ShellType.POWERSHELL:
            full_command = ["powershell", "-NoProfile", "-Command", command]
        elif shell == ShellType.CMD:
            full_command = ["cmd", "/c", command]
        else:
            full_command = ["bash", "-c", command]
        
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                full_command,
                cwd=working_dir,
                env=env,
                capture_output=True,
                timeout=timeout,
            )
        )
    
    async def _execute_docker(
        self,
        command: str,
        working_dir: Path,
        env: dict,
        timeout: int,
    ) -> subprocess.CompletedProcess:
        """Execute command in Docker container."""
        
        # Build docker run command
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{working_dir.absolute()}:/workspace",
            "-w", "/workspace",
        ]
        
        # Add environment variables
        for key, value in env.items():
            docker_cmd.extend(["-e", f"{key}={value}"])
        
        docker_cmd.extend([
            self.config.docker_image,
            "bash", "-c", command,
        ])
        
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                docker_cmd,
                capture_output=True,
                timeout=timeout,
            )
        )
    
    async def _execute_wsl(
        self,
        command: str,
        working_dir: Path,
        env: dict,
        timeout: int,
    ) -> subprocess.CompletedProcess:
        """Execute command in WSL2."""
        
        # Convert Windows path to WSL path
        wsl_path = str(working_dir).replace("\\", "/")
        if wsl_path[1] == ":":
            wsl_path = f"/mnt/{wsl_path[0].lower()}{wsl_path[2:]}"
        
        wsl_command = f"cd {wsl_path} && {command}"
        
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["wsl", "bash", "-c", wsl_command],
                env=env,
                capture_output=True,
                timeout=timeout,
            )
        )
    
    def _detect_error_type(self, stderr: str) -> str:
        """Detect type of error from stderr."""
        
        error_patterns = {
            "DEPENDENCY_MISSING": [
                r"ModuleNotFoundError",
                r"ImportError",
                r"Cannot find module",
                r"package .* is not installed",
            ],
            "PERMISSION_DENIED": [
                r"Permission denied",
                r"Access is denied",
                r"EACCES",
            ],
            "FILE_NOT_FOUND": [
                r"FileNotFoundError",
                r"No such file or directory",
                r"ENOENT",
            ],
            "SYNTAX_ERROR": [
                r"SyntaxError",
                r"Unexpected token",
                r"Parse error",
            ],
            "VERSION_CONFLICT": [
                r"version conflict",
                r"incompatible versions",
                r"requires .* but .* is installed",
            ],
            "NETWORK_ERROR": [
                r"ConnectionError",
                r"ETIMEDOUT",
                r"Network is unreachable",
            ],
        }
        
        stderr_lower = stderr.lower()
        for error_type, patterns in error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, stderr, re.IGNORECASE):
                    return error_type
        
        return "UNKNOWN"
```

---

## Error Recovery System

**File: `src/cli/error_recovery.py`**

```python
"""
CLI Error Recovery - Auto-fixes common errors.

When a command fails, this module:
1. Detects the error type
2. Applies known fixes
3. Retries the command
4. Learns from new errors
"""

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from src.cli.executor import CLIExecutor, CommandResult

logger = logging.getLogger(__name__)


@dataclass
class RecoveryAction:
    """Action to recover from an error."""
    
    error_type: str
    pattern: str
    fix_command: str
    description: str
    requires_approval: bool = False


class ErrorRecovery:
    """
    Auto-recovers from CLI errors.
    """
    
    def __init__(self, executor: CLIExecutor):
        self.executor = executor
        self._register_recovery_actions()
    
    def _register_recovery_actions(self) -> None:
        """Register known error recovery patterns."""
        
        self.recovery_actions = {
            # Python dependency errors
            "DEPENDENCY_MISSING": [
                RecoveryAction(
                    error_type="DEPENDENCY_MISSING",
                    pattern=r"No module named '(\w+)'",
                    fix_command="pip install {package}",
                    description="Install missing Python package",
                ),
                RecoveryAction(
                    error_type="DEPENDENCY_MISSING",
                    pattern=r"ModuleNotFoundError: No module named '(\w+)'",
                    fix_command="pip install {package}",
                    description="Install missing Python package",
                ),
            ],
            
            # Node.js dependency errors
            "DEPENDENCY_MISSING_NODE": [
                RecoveryAction(
                    error_type="DEPENDENCY_MISSING",
                    pattern=r"Cannot find module '(@?\w+(?:/\w+)?)'",
                    fix_command="npm install {package}",
                    description="Install missing Node package",
                ),
            ],
            
            # Permission errors
            "PERMISSION_DENIED": [
                RecoveryAction(
                    error_type="PERMISSION_DENIED",
                    pattern=r"Permission denied",
                    fix_command="sudo {original_command}",
                    description="Retry with elevated permissions",
                    requires_approval=True,
                ),
            ],
            
            # Docker errors
            "DOCKER_NOT_RUNNING": [
                RecoveryAction(
                    error_type="DOCKER_NOT_RUNNING",
                    pattern=r"Cannot connect to the Docker daemon",
                    fix_command="Start-Service docker",  # Windows
                    description="Start Docker service",
                ),
            ],
            
            # Git errors
            "GIT_NOT_CONFIGURED": [
                RecoveryAction(
                    error_type="GIT_NOT_CONFIGURED",
                    pattern=r"Please tell me who you are",
                    fix_command='git config --global user.email "agent@synthesizer.ai" && git config --global user.name "AI Agent"',
                    description="Configure git identity",
                ),
            ],
            
            # Version conflicts
            "VERSION_CONFLICT": [
                RecoveryAction(
                    error_type="VERSION_CONFLICT",
                    pattern=r"requires .* but .* is installed",
                    fix_command="pip install --upgrade {package}",
                    description="Upgrade conflicting package",
                ),
            ],
        }
    
    async def attempt_recovery(
        self,
        original_command: str,
        result: CommandResult,
        max_retries: int = 3,
        approval_callback: Optional[Callable] = None,
    ) -> CommandResult:
        """
        Attempt to recover from a failed command.
        
        Args:
            original_command: The command that failed
            result: The failure result
            max_retries: Max recovery attempts
            approval_callback: Function to call for user approval
        
        Returns:
            New CommandResult after recovery attempt
        """
        if result.success:
            return result
        
        for attempt in range(max_retries):
            recovery = self._find_recovery_action(result)
            
            if not recovery:
                logger.warning(f"No recovery action found for: {result.error_type}")
                return result
            
            # Check if approval needed
            if recovery.requires_approval:
                if approval_callback:
                    approved = await approval_callback(
                        f"Recovery requires: {recovery.description}\n"
                        f"Command: {recovery.fix_command}\n"
                        "Approve? (yes/no)"
                    )
                    if not approved:
                        return result
                else:
                    logger.warning(f"Approval required but no callback: {recovery.description}")
                    return result
            
            # Execute recovery command
            logger.info(f"Attempting recovery: {recovery.description}")
            
            fix_command = self._format_fix_command(
                recovery.fix_command,
                original_command,
                result.stderr,
            )
            
            fix_result = await self.executor.execute(fix_command)
            
            if not fix_result.success:
                logger.warning(f"Recovery command failed: {fix_result.stderr}")
                continue
            
            # Retry original command
            logger.info("Retrying original command after recovery")
            retry_result = await self.executor.execute(original_command)
            
            if retry_result.success:
                retry_result.suggested_fix = f"Auto-fixed with: {fix_command}"
                return retry_result
        
        return result
    
    def _find_recovery_action(self, result: CommandResult) -> Optional[RecoveryAction]:
        """Find matching recovery action."""
        import re
        
        for error_type, actions in self.recovery_actions.items():
            for action in actions:
                if re.search(action.pattern, result.stderr, re.IGNORECASE):
                    return action
        
        return None
    
    def _format_fix_command(
        self,
        fix_template: str,
        original_command: str,
        stderr: str,
    ) -> str:
        """Format fix command with extracted values."""
        import re
        
        # Extract package name if present
        package_match = re.search(r"No module named ['\"]?(\w+)['\"]?", stderr)
        package_match = package_match or re.search(r"Cannot find module ['\"]?(@?\w+(?:/\w+)?)['\"]?", stderr)
        
        package = package_match.group(1) if package_match else ""
        
        return fix_template.format(
            package=package,
            original_command=original_command,
        )
```

---

## Command Library

All commands agents can execute, organized by category:

### Git Commands

```yaml
git_commands:
  initialize:
    - cmd: "git init"
      desc: "Initialize new repository"
    - cmd: "git clone {url}"
      desc: "Clone repository"
      params: [url]
  
  staging:
    - cmd: "git add ."
      desc: "Stage all changes"
    - cmd: "git add {file}"
      desc: "Stage specific file"
      params: [file]
    - cmd: "git reset HEAD {file}"
      desc: "Unstage file"
      params: [file]
  
  commits:
    - cmd: "git commit -m \"{message}\""
      desc: "Commit with message"
      params: [message]
    - cmd: "git commit --amend"
      desc: "Amend last commit"
  
  branches:
    - cmd: "git branch {name}"
      desc: "Create branch"
      params: [name]
    - cmd: "git checkout {branch}"
      desc: "Switch branch"
      params: [branch]
    - cmd: "git merge {branch}"
      desc: "Merge branch"
      params: [branch]
  
  remote:
    - cmd: "git push origin {branch}"
      desc: "Push to remote"
      params: [branch]
    - cmd: "git pull origin {branch}"
      desc: "Pull from remote"
      params: [branch]
    - cmd: "git fetch --all"
      desc: "Fetch all remotes"
```

### Python Commands

```yaml
python_commands:
  environment:
    - cmd: "python -m venv .venv"
      desc: "Create virtual environment"
    - cmd: ".venv\\Scripts\\activate"  # Windows
      desc: "Activate venv (Windows)"
    - cmd: "source .venv/bin/activate"  # Unix
      desc: "Activate venv (Unix)"
  
  packages:
    - cmd: "pip install -r requirements.txt"
      desc: "Install from requirements"
    - cmd: "pip install {package}"
      desc: "Install package"
      params: [package]
    - cmd: "pip freeze > requirements.txt"
      desc: "Export requirements"
    - cmd: "pip install --upgrade {package}"
      desc: "Upgrade package"
      params: [package]
  
  testing:
    - cmd: "pytest tests/"
      desc: "Run all tests"
    - cmd: "pytest tests/ -v"
      desc: "Run tests verbose"
    - cmd: "pytest tests/ --cov=src"
      desc: "Run tests with coverage"
    - cmd: "pytest tests/ -k {pattern}"
      desc: "Run tests matching pattern"
      params: [pattern]
  
  linting:
    - cmd: "ruff check src/ tests/"
      desc: "Run Ruff linter"
    - cmd: "ruff check src/ tests/ --fix"
      desc: "Run Ruff with auto-fix"
    - cmd: "mypy src/"
      desc: "Run type checker"
    - cmd: "bandit -r src/"
      desc: "Run security scan"
  
  building:
    - cmd: "python -m build"
      desc: "Build package"
    - cmd: "python setup.py sdist bdist_wheel"
      desc: "Build distributions"
```

### Docker Commands

```yaml
docker_commands:
  images:
    - cmd: "docker build -t {name} ."
      desc: "Build image"
      params: [name]
    - cmd: "docker images"
      desc: "List images"
    - cmd: "docker rmi {image}"
      desc: "Remove image"
      params: [image]
  
  containers:
    - cmd: "docker run -d {image}"
      desc: "Run container detached"
      params: [image]
    - cmd: "docker ps"
      desc: "List running containers"
    - cmd: "docker stop {container}"
      desc: "Stop container"
      params: [container]
    - cmd: "docker rm {container}"
      desc: "Remove container"
      params: [container]
    - cmd: "docker logs {container}"
      desc: "View container logs"
      params: [container]
  
  compose:
    - cmd: "docker compose up -d"
      desc: "Start services detached"
    - cmd: "docker compose down"
      desc: "Stop services"
    - cmd: "docker compose logs -f"
      desc: "Follow logs"
    - cmd: "docker compose build"
      desc: "Build services"
    - cmd: "docker compose ps"
      desc: "List services"
```

### Node.js Commands

```yaml
node_commands:
  packages:
    - cmd: "npm init -y"
      desc: "Initialize package.json"
    - cmd: "npm install"
      desc: "Install dependencies"
    - cmd: "npm install {package}"
      desc: "Install package"
      params: [package]
    - cmd: "npm install -D {package}"
      desc: "Install dev dependency"
      params: [package]
    - cmd: "npm update"
      desc: "Update packages"
    - cmd: "npm audit"
      desc: "Security audit"
    - cmd: "npm audit fix"
      desc: "Fix vulnerabilities"
  
  scripts:
    - cmd: "npm run {script}"
      desc: "Run npm script"
      params: [script]
    - cmd: "npm run build"
      desc: "Build project"
    - cmd: "npm run test"
      desc: "Run tests"
    - cmd: "npm run lint"
      desc: "Run linter"
    - cmd: "npm start"
      desc: "Start application"
```

---

## Agent CLI Interface

**File: `src/cli/agent_interface.py`**

```python
"""
Agent CLI Interface - High-level CLI operations for agents.

Provides semantic operations that map to CLI commands.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from src.cli.executor import CLIExecutor, CommandResult, ExecutionMode
from src.cli.error_recovery import ErrorRecovery

logger = logging.getLogger(__name__)


class AgentCLI:
    """
    High-level CLI interface for agents.
    
    Provides semantic methods instead of raw commands.
    Handles error recovery automatically.
    """
    
    def __init__(self):
        self.executor = CLIExecutor()
        self.recovery = ErrorRecovery(self.executor)
    
    # ========== Git Operations ==========
    
    async def git_init(self, path: Optional[Path] = None) -> CommandResult:
        """Initialize git repository."""
        return await self._run("git init", working_dir=path)
    
    async def git_clone(self, url: str, path: Optional[Path] = None) -> CommandResult:
        """Clone a repository."""
        return await self._run(f"git clone {url}", working_dir=path)
    
    async def git_commit(self, message: str) -> CommandResult:
        """Stage all changes and commit."""
        await self._run("git add .")
        return await self._run(f'git commit -m "{message}"')
    
    async def git_push(self, branch: str = "main") -> CommandResult:
        """Push to remote."""
        return await self._run(f"git push origin {branch}")
    
    async def git_pull(self, branch: str = "main") -> CommandResult:
        """Pull from remote."""
        return await self._run(f"git pull origin {branch}")
    
    # ========== Python Operations ==========
    
    async def python_create_venv(self, path: Path = Path(".venv")) -> CommandResult:
        """Create Python virtual environment."""
        return await self._run(f"python -m venv {path}")
    
    async def pip_install(self, *packages: str) -> CommandResult:
        """Install Python packages."""
        pkg_list = " ".join(packages)
        return await self._run(f"pip install {pkg_list}")
    
    async def pip_install_requirements(self, file: str = "requirements.txt") -> CommandResult:
        """Install from requirements file."""
        return await self._run(f"pip install -r {file}")
    
    async def pytest_run(self, path: str = "tests/", coverage: bool = False) -> CommandResult:
        """Run pytest."""
        cmd = f"pytest {path}"
        if coverage:
            cmd += " --cov=src"
        return await self._run(cmd)
    
    async def ruff_check(self, fix: bool = False) -> CommandResult:
        """Run Ruff linter."""
        cmd = "ruff check src/ tests/"
        if fix:
            cmd += " --fix"
        return await self._run(cmd)
    
    # ========== Docker Operations ==========
    
    async def docker_build(self, tag: str, dockerfile: str = "Dockerfile") -> CommandResult:
        """Build Docker image."""
        return await self._run(f"docker build -t {tag} -f {dockerfile} .")
    
    async def docker_compose_up(self, detach: bool = True) -> CommandResult:
        """Start Docker Compose services."""
        cmd = "docker compose up"
        if detach:
            cmd += " -d"
        return await self._run(cmd)
    
    async def docker_compose_down(self) -> CommandResult:
        """Stop Docker Compose services."""
        return await self._run("docker compose down")
    
    # ========== Node.js Operations ==========
    
    async def npm_install(self, *packages: str, dev: bool = False) -> CommandResult:
        """Install npm packages."""
        if packages:
            pkg_list = " ".join(packages)
            cmd = f"npm install {'-D ' if dev else ''}{pkg_list}"
        else:
            cmd = "npm install"
        return await self._run(cmd)
    
    async def npm_run(self, script: str) -> CommandResult:
        """Run npm script."""
        return await self._run(f"npm run {script}")
    
    # ========== File Operations ==========
    
    async def create_file(self, path: Path, content: str) -> CommandResult:
        """Create file with content."""
        # Use Python for cross-platform compatibility
        escaped = content.replace('"', '\\"').replace("\n", "\\n")
        cmd = f'python -c "from pathlib import Path; Path(\'{path}\').write_text(\'{escaped}\')"'
        return await self._run(cmd)
    
    async def read_file(self, path: Path) -> CommandResult:
        """Read file content."""
        return await self._run(f"cat {path}")
    
    # ========== Helper Methods ==========
    
    async def _run(
        self,
        command: str,
        working_dir: Optional[Path] = None,
        auto_recover: bool = True,
    ) -> CommandResult:
        """Execute command with optional recovery."""
        result = await self.executor.execute(command, working_dir=working_dir)
        
        if not result.success and auto_recover:
            result = await self.recovery.attempt_recovery(command, result)
        
        return result
```

---

## Next Document

See **[MEMORY_LEARNING_SYSTEM.md](./MEMORY_LEARNING_SYSTEM.md)** for the brain architecture.
