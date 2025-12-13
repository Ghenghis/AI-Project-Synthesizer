"""
VIBE MCP - Error Recovery System

Automatic error detection and recovery for CLI commands.
Implements the "vibe coding" principle of auto-fixing common issues.

Features:
- Pattern-based error detection
- Automatic fix suggestions
- Retry logic with exponential backoff
- Learning from successful fixes (stores in Mem0)

Usage:
    recovery = ErrorRecovery(executor)
    result = await recovery.attempt_recovery(command, failed_result)
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum

from src.cli_executor.executor import CLIExecutor, CommandResult, ErrorType

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Strategy for recovering from errors."""
    INSTALL_DEPENDENCY = "install_dependency"
    RETRY = "retry"
    CHANGE_PERMISSIONS = "change_permissions"
    CREATE_FILE = "create_file"
    CREATE_DIRECTORY = "create_directory"
    UPGRADE_PACKAGE = "upgrade_package"
    CONFIGURE_GIT = "configure_git"
    START_SERVICE = "start_service"
    FIX_SYNTAX = "fix_syntax"
    MANUAL = "manual"


@dataclass
class ErrorPattern:
    """Pattern for matching and recovering from errors."""
    name: str
    error_type: ErrorType
    patterns: list[str]  # Regex patterns to match
    strategy: RecoveryStrategy
    fix_template: str  # Command template for fix
    extract_info: str | None = None  # Regex to extract info (e.g., package name)
    requires_confirmation: bool = False
    max_retries: int = 3


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    original_error: CommandResult
    recovery_attempted: bool
    recovery_command: str | None = None
    recovery_result: CommandResult | None = None
    final_result: CommandResult | None = None
    success: bool = False
    attempts: int = 0
    strategy_used: RecoveryStrategy | None = None


# Default error patterns with recovery strategies
DEFAULT_ERROR_PATTERNS = [
    # Python dependency missing
    ErrorPattern(
        name="python_module_missing",
        error_type=ErrorType.DEPENDENCY_MISSING,
        patterns=[
            r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]",
            r"ImportError: No module named ['\"]([^'\"]+)['\"]",
            r"No module named ['\"]?([a-zA-Z0-9_-]+)['\"]?",
        ],
        strategy=RecoveryStrategy.INSTALL_DEPENDENCY,
        fix_template="pip install {package}",
        extract_info=r"['\"]?([a-zA-Z0-9_-]+)['\"]?",
    ),

    # npm package missing
    ErrorPattern(
        name="npm_package_missing",
        error_type=ErrorType.DEPENDENCY_MISSING,
        patterns=[
            r"Cannot find module ['\"]([^'\"]+)['\"]",
            r"Module not found: Error: Can't resolve ['\"]([^'\"]+)['\"]",
            r"npm ERR! 404.*['\"]([^'\"]+)['\"]",
        ],
        strategy=RecoveryStrategy.INSTALL_DEPENDENCY,
        fix_template="npm install {package}",
        extract_info=r"['\"]([^'\"]+)['\"]",
    ),

    # Command not found
    ErrorPattern(
        name="command_not_found",
        error_type=ErrorType.DEPENDENCY_MISSING,
        patterns=[
            r"['\"]?([a-zA-Z0-9_-]+)['\"]? is not recognized",
            r"command not found: ([a-zA-Z0-9_-]+)",
            r"'([a-zA-Z0-9_-]+)' is not recognized as an internal or external command",
        ],
        strategy=RecoveryStrategy.MANUAL,
        fix_template="# Install {package} manually",
        extract_info=r"([a-zA-Z0-9_-]+)",
    ),

    # Permission denied
    ErrorPattern(
        name="permission_denied",
        error_type=ErrorType.PERMISSION_DENIED,
        patterns=[
            r"Permission denied",
            r"Access is denied",
            r"EACCES",
            r"Operation not permitted",
        ],
        strategy=RecoveryStrategy.CHANGE_PERMISSIONS,
        fix_template="# Run with elevated permissions or fix file permissions",
        requires_confirmation=True,
    ),

    # File not found
    ErrorPattern(
        name="file_not_found",
        error_type=ErrorType.FILE_NOT_FOUND,
        patterns=[
            r"FileNotFoundError:.*['\"]([^'\"]+)['\"]",
            r"No such file or directory:?\s*['\"]?([^\s'\"]+)['\"]?",
            r"ENOENT.*['\"]([^'\"]+)['\"]",
        ],
        strategy=RecoveryStrategy.CREATE_FILE,
        fix_template="# Create missing file: {path}",
        extract_info=r"['\"]?([^\s'\"]+)['\"]?",
    ),

    # Directory not found
    ErrorPattern(
        name="directory_not_found",
        error_type=ErrorType.FILE_NOT_FOUND,
        patterns=[
            r"The system cannot find the path specified",
            r"directory .* does not exist",
            r"ENOENT.*directory",
        ],
        strategy=RecoveryStrategy.CREATE_DIRECTORY,
        fix_template="mkdir -p {path}",
        extract_info=r"['\"]?([^\s'\"]+)['\"]?",
    ),

    # Version conflict
    ErrorPattern(
        name="version_conflict",
        error_type=ErrorType.VERSION_CONFLICT,
        patterns=[
            r"version conflict",
            r"incompatible versions",
            r"requires ([a-zA-Z0-9_-]+)[<>=]+",
        ],
        strategy=RecoveryStrategy.UPGRADE_PACKAGE,
        fix_template="pip install --upgrade {package}",
        extract_info=r"([a-zA-Z0-9_-]+)",
    ),

    # Git not configured
    ErrorPattern(
        name="git_not_configured",
        error_type=ErrorType.GIT_ERROR,
        patterns=[
            r"Please tell me who you are",
            r"user\.email",
            r"user\.name",
        ],
        strategy=RecoveryStrategy.CONFIGURE_GIT,
        fix_template='git config --global user.email "user@example.com" && git config --global user.name "User"',
    ),

    # Git not a repository
    ErrorPattern(
        name="git_not_repo",
        error_type=ErrorType.GIT_ERROR,
        patterns=[
            r"fatal: not a git repository",
            r"fatal: Not a git repository",
        ],
        strategy=RecoveryStrategy.MANUAL,
        fix_template="git init",
    ),

    # Docker not running
    ErrorPattern(
        name="docker_not_running",
        error_type=ErrorType.DOCKER_ERROR,
        patterns=[
            r"Cannot connect to the Docker daemon",
            r"docker daemon is not running",
            r"Is the docker daemon running",
        ],
        strategy=RecoveryStrategy.START_SERVICE,
        fix_template="Start-Service docker",  # Windows
    ),

    # Network timeout
    ErrorPattern(
        name="network_timeout",
        error_type=ErrorType.NETWORK_ERROR,
        patterns=[
            r"Connection timed out",
            r"ETIMEDOUT",
            r"read ECONNRESET",
        ],
        strategy=RecoveryStrategy.RETRY,
        fix_template="# Retry the command",
        max_retries=3,
    ),

    # SSL certificate error
    ErrorPattern(
        name="ssl_error",
        error_type=ErrorType.NETWORK_ERROR,
        patterns=[
            r"SSL certificate",
            r"CERT_",
            r"certificate verify failed",
        ],
        strategy=RecoveryStrategy.MANUAL,
        fix_template="# Check SSL certificates or use --trusted-host",
    ),
]


class ErrorRecovery:
    """
    Automatic error recovery system for CLI commands.

    Analyzes failed commands, matches error patterns, and attempts
    automatic recovery using predefined strategies.
    """

    def __init__(
        self,
        executor: CLIExecutor,
        patterns: list[ErrorPattern] | None = None,
        max_retries: int = 3,
    ):
        """Initialize error recovery system."""
        self.executor = executor
        self.patterns = patterns or DEFAULT_ERROR_PATTERNS
        self.max_retries = max_retries
        self._recovery_history: list[RecoveryResult] = []

        # Package name mappings (import name -> pip package)
        self._package_mappings = {
            "cv2": "opencv-python",
            "PIL": "Pillow",
            "sklearn": "scikit-learn",
            "yaml": "pyyaml",
            "bs4": "beautifulsoup4",
            "dotenv": "python-dotenv",
            "jwt": "pyjwt",
            "magic": "python-magic",
            "dateutil": "python-dateutil",
        }

    def _match_pattern(self, error_text: str) -> tuple[ErrorPattern | None, str | None]:
        """Match error text against patterns and extract info."""
        for pattern in self.patterns:
            for regex in pattern.patterns:
                match = re.search(regex, error_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Extract captured group if available
                    extracted = match.group(1) if match.lastindex else None
                    return pattern, extracted
        return None, None

    def _resolve_package_name(self, import_name: str) -> str:
        """Resolve import name to actual package name."""
        # Check mappings first
        if import_name in self._package_mappings:
            return self._package_mappings[import_name]

        # Handle submodule imports (e.g., "foo.bar" -> "foo")
        base_name = import_name.split(".")[0]
        if base_name in self._package_mappings:
            return self._package_mappings[base_name]

        # Return as-is (most packages match their import name)
        return base_name

    def _build_fix_command(self, pattern: ErrorPattern, extracted: str | None) -> str:
        """Build the fix command from template."""
        if not extracted:
            return pattern.fix_template

        # Resolve package name if it's a dependency install
        if pattern.strategy == RecoveryStrategy.INSTALL_DEPENDENCY:
            extracted = self._resolve_package_name(extracted)

        return pattern.fix_template.format(
            package=extracted,
            path=extracted,
            module=extracted,
        )

    async def attempt_recovery(
        self,
        original_command: str,
        failed_result: CommandResult,
        context: dict | None = None,
    ) -> RecoveryResult:
        """
        Attempt to recover from a failed command.

        Args:
            original_command: The command that failed
            failed_result: The failed CommandResult
            context: Optional context for recovery

        Returns:
            RecoveryResult with recovery details
        """
        error_text = f"{failed_result.stderr} {failed_result.stdout}"

        # Match error pattern
        pattern, extracted = self._match_pattern(error_text)

        if not pattern:
            logger.info(f"No recovery pattern matched for error: {error_text[:100]}...")
            return RecoveryResult(
                original_error=failed_result,
                recovery_attempted=False,
                success=False,
            )

        logger.info(f"Matched error pattern: {pattern.name}, strategy: {pattern.strategy}")

        # Build fix command
        fix_command = self._build_fix_command(pattern, extracted)

        # Skip if requires confirmation or is manual
        if pattern.requires_confirmation or pattern.strategy == RecoveryStrategy.MANUAL:
            logger.info(f"Recovery requires manual intervention: {fix_command}")
            result = RecoveryResult(
                original_error=failed_result,
                recovery_attempted=False,
                recovery_command=fix_command,
                success=False,
                strategy_used=pattern.strategy,
            )
            result.final_result = failed_result
            result.final_result.suggested_fix = fix_command
            self._recovery_history.append(result)
            return result

        # Attempt recovery
        attempts = 0
        max_attempts = min(pattern.max_retries, self.max_retries)

        while attempts < max_attempts:
            attempts += 1
            logger.info(f"Recovery attempt {attempts}/{max_attempts}: {fix_command}")

            # Execute fix command
            fix_result = await self.executor.execute(
                fix_command,
                working_dir=failed_result.working_dir,
            )

            if not fix_result.success:
                logger.warning(f"Fix command failed: {fix_result.stderr[:100]}...")
                if pattern.strategy != RecoveryStrategy.RETRY:
                    break
                await asyncio.sleep(2 ** attempts)  # Exponential backoff
                continue

            # Retry original command
            logger.info(f"Retrying original command: {original_command}")
            retry_result = await self.executor.execute(
                original_command,
                working_dir=failed_result.working_dir,
            )

            if retry_result.success:
                logger.info(f"Recovery successful after {attempts} attempts")
                result = RecoveryResult(
                    original_error=failed_result,
                    recovery_attempted=True,
                    recovery_command=fix_command,
                    recovery_result=fix_result,
                    final_result=retry_result,
                    success=True,
                    attempts=attempts,
                    strategy_used=pattern.strategy,
                )
                self._recovery_history.append(result)
                return result

            # If retry strategy, wait and try again
            if pattern.strategy == RecoveryStrategy.RETRY:
                await asyncio.sleep(2 ** attempts)

        # Recovery failed
        logger.warning(f"Recovery failed after {attempts} attempts")
        result = RecoveryResult(
            original_error=failed_result,
            recovery_attempted=True,
            recovery_command=fix_command,
            final_result=failed_result,
            success=False,
            attempts=attempts,
            strategy_used=pattern.strategy,
        )
        result.final_result.suggested_fix = fix_command
        self._recovery_history.append(result)
        return result

    async def execute_with_recovery(
        self,
        command: str,
        working_dir: str | None = None,
        auto_recover: bool = True,
    ) -> CommandResult:
        """
        Execute command with automatic recovery on failure.

        Args:
            command: Command to execute
            working_dir: Working directory
            auto_recover: Whether to attempt auto-recovery

        Returns:
            Final CommandResult (either original success or recovered)
        """
        result = await self.executor.execute(command, working_dir=working_dir)

        if result.success or not auto_recover:
            return result

        # Attempt recovery
        recovery = await self.attempt_recovery(command, result)

        if recovery.success and recovery.final_result:
            return recovery.final_result

        # Return original result with suggested fix
        if recovery.recovery_command:
            result.suggested_fix = recovery.recovery_command

        return result

    def get_recovery_history(self, limit: int = 50) -> list[RecoveryResult]:
        """Get recovery attempt history."""
        return self._recovery_history[-limit:]

    def get_success_rate(self) -> float:
        """Get recovery success rate."""
        if not self._recovery_history:
            return 0.0

        attempted = [r for r in self._recovery_history if r.recovery_attempted]
        if not attempted:
            return 0.0

        successful = sum(1 for r in attempted if r.success)
        return successful / len(attempted) * 100

    def add_pattern(self, pattern: ErrorPattern) -> None:
        """Add a custom error pattern."""
        self.patterns.append(pattern)
        logger.info(f"Added error pattern: {pattern.name}")

    def add_package_mapping(self, import_name: str, package_name: str) -> None:
        """Add a custom package name mapping."""
        self._package_mappings[import_name] = package_name
        logger.info(f"Added package mapping: {import_name} -> {package_name}")
