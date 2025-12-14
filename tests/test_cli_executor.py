"""
Tests for CLI Executor module.

Tests the core command execution, error detection, and recovery systems.
"""

import asyncio
from pathlib import Path

import pytest

from src.cli_executor import (
    AgentCLI,
    CLIExecutor,
    CommandResult,
    ErrorRecovery,
    ExecutionMode,
    ExecutorConfig,
)
from src.cli_executor.executor import ErrorType


class TestCLIExecutor:
    """Tests for CLIExecutor."""

    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        executor = CLIExecutor()
        assert executor.is_windows is not None
        assert executor.config is not None

    def test_blocked_commands(self):
        """Test dangerous commands are blocked."""
        executor = CLIExecutor()

        # These should be blocked
        assert executor._is_command_blocked("rm -rf /")
        assert executor._is_command_blocked("format c:")
        assert executor._is_command_blocked("del /s /q c:\\")

        # These should be allowed
        assert not executor._is_command_blocked("pip install requests")
        assert not executor._is_command_blocked("git status")

    def test_dangerous_pattern_detection(self):
        """Test dangerous patterns are detected."""
        executor = CLIExecutor()

        assert executor._is_command_dangerous("rm -rf /home/user")
        assert executor._is_command_dangerous("DROP DATABASE users")
        assert not executor._is_command_dangerous("pip install requests")

    def test_error_type_detection(self):
        """Test error type detection from stderr."""
        executor = CLIExecutor()

        # Dependency missing
        assert executor._detect_error_type(
            "ModuleNotFoundError: No module named 'requests'"
        ) == ErrorType.DEPENDENCY_MISSING

        # Permission denied
        assert executor._detect_error_type(
            "Permission denied: /etc/passwd"
        ) == ErrorType.PERMISSION_DENIED

        # File not found
        assert executor._detect_error_type(
            "FileNotFoundError: No such file or directory: 'missing.txt'"
        ) == ErrorType.FILE_NOT_FOUND

        # Git error
        assert executor._detect_error_type(
            "fatal: not a git repository"
        ) == ErrorType.GIT_ERROR

    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """Test executing a simple command."""
        executor = CLIExecutor()

        # Simple echo command
        if executor.is_windows:
            result = await executor.execute("echo 'hello'")
        else:
            result = await executor.execute("echo hello")

        assert result.success
        assert result.exit_code == 0
        assert "hello" in result.stdout.lower()

    @pytest.mark.asyncio
    async def test_execute_blocked_command(self):
        """Test that blocked commands return error."""
        executor = CLIExecutor()

        result = await executor.execute("rm -rf /")

        assert not result.success
        assert result.error_type == ErrorType.BLOCKED

    @pytest.mark.asyncio
    async def test_execute_failing_command(self):
        """Test handling of failing commands."""
        executor = CLIExecutor()

        result = await executor.execute("nonexistent_command_xyz")

        assert not result.success
        assert result.exit_code != 0

    def test_command_history(self):
        """Test command history tracking."""
        executor = CLIExecutor()

        # Run some commands
        asyncio.run(executor.execute("echo test1"))
        asyncio.run(executor.execute("echo test2"))

        history = executor.get_history()
        assert len(history) >= 2

    def test_stats(self):
        """Test statistics collection."""
        executor = CLIExecutor()

        asyncio.run(executor.execute("echo test"))

        stats = executor.get_stats()
        assert "total_commands" in stats
        assert "success_rate" in stats


class TestErrorRecovery:
    """Tests for ErrorRecovery system."""

    def test_pattern_matching(self):
        """Test error pattern matching."""
        executor = CLIExecutor()
        recovery = ErrorRecovery(executor)

        # Test Python module missing
        pattern, extracted = recovery._match_pattern(
            "ModuleNotFoundError: No module named 'requests'"
        )
        assert pattern is not None
        assert pattern.name == "python_module_missing"
        assert extracted == "requests"

    def test_package_name_resolution(self):
        """Test package name mapping."""
        executor = CLIExecutor()
        recovery = ErrorRecovery(executor)

        # Test known mappings
        assert recovery._resolve_package_name("cv2") == "opencv-python"
        assert recovery._resolve_package_name("PIL") == "Pillow"
        assert recovery._resolve_package_name("sklearn") == "scikit-learn"

        # Test unknown (should return as-is)
        assert recovery._resolve_package_name("requests") == "requests"

    def test_fix_command_building(self):
        """Test fix command generation."""
        executor = CLIExecutor()
        recovery = ErrorRecovery(executor)

        pattern, extracted = recovery._match_pattern(
            "ModuleNotFoundError: No module named 'requests'"
        )

        fix_cmd = recovery._build_fix_command(pattern, extracted)
        assert "pip install requests" in fix_cmd


class TestAgentCLI:
    """Tests for AgentCLI interface."""

    def test_initialization(self):
        """Test AgentCLI initializes correctly."""
        cli = AgentCLI()
        assert cli.executor is not None
        assert cli.recovery is not None

    @pytest.mark.asyncio
    async def test_git_status(self):
        """Test git status command."""
        cli = AgentCLI(working_dir=Path.cwd())

        result = await cli.git_status()
        # May fail if not in a git repo, but should execute
        assert result.command == "git status"

    @pytest.mark.asyncio
    async def test_pip_list(self):
        """Test pip list command."""
        cli = AgentCLI()

        result = await cli.pip_list()
        assert result.success
        assert "pip" in result.stdout.lower() or result.exit_code == 0

    @pytest.mark.asyncio
    async def test_ls_command(self):
        """Test directory listing."""
        cli = AgentCLI()

        result = await cli.ls()
        assert result.success

    @pytest.mark.asyncio
    async def test_raw_command(self):
        """Test raw command execution."""
        cli = AgentCLI()

        if cli.executor.is_windows:
            result = await cli.run_raw("echo 'test'")
        else:
            result = await cli.run_raw("echo test")

        assert result.success

    def test_stats(self):
        """Test stats collection."""
        cli = AgentCLI()

        asyncio.run(cli.ls())

        stats = cli.get_stats()
        assert "executor_stats" in stats
        assert "recovery_success_rate" in stats


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_to_dict(self):
        """Test serialization to dict."""
        result = CommandResult(
            command="echo test",
            exit_code=0,
            stdout="test",
            stderr="",
            duration_ms=100.0,
            success=True,
        )

        data = result.to_dict()
        assert data["command"] == "echo test"
        assert data["success"] is True
        assert data["exit_code"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
