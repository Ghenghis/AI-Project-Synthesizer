"""
VIBE MCP - CLI Execution Module

Agent-driven command execution system that allows AI agents to safely
execute CLI commands on behalf of users.

Components:
- executor: Core command execution with safety checks
- error_recovery: Automatic error detection and recovery
- agent_interface: High-level semantic methods for agents

Usage:
    from src.cli import AgentCLI

    cli = AgentCLI()
    result = await cli.git_commit("Initial commit")
    result = await cli.pip_install(["requests", "fastapi"])
"""

from src.cli_executor.agent_interface import AgentCLI
from src.cli_executor.error_recovery import (
    ErrorPattern,
    ErrorRecovery,
    RecoveryStrategy,
)
from src.cli_executor.executor import (
    CLIExecutor,
    CommandResult,
    ExecutionMode,
    ExecutorConfig,
    ShellType,
)

__all__ = [
    # Executor
    "CLIExecutor",
    "CommandResult",
    "ExecutionMode",
    "ExecutorConfig",
    "ShellType",
    # Error Recovery
    "ErrorRecovery",
    "ErrorPattern",
    "RecoveryStrategy",
    # Agent Interface
    "AgentCLI",
]
