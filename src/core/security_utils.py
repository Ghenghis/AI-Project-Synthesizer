"""
Security utilities for input validation and secure operations.
"""

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def validate_command_args(args: list[str]) -> list[str]:
    """
    Validate and sanitize command arguments.

    Args:
        args: List of command arguments

    Returns:
        Sanitized arguments

    Raises:
        ValueError: If arguments contain dangerous characters
    """
    sanitized = []

    for arg in args:
        # Check for dangerous patterns
        dangerous_patterns = [
            r'[;&|`$()]',  # Shell metacharacters
            r'\.\./',      # Directory traversal
            r'--\s*exec',  # Dangerous exec flags
            r'--\s*system', # Dangerous system flags
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, arg):
                raise ValueError(f"Argument contains dangerous pattern: {arg}")

        # Limit argument length
        if len(arg) > 1000:
            raise ValueError(f"Argument too long: {len(arg)} characters")

        sanitized.append(arg)

    return sanitized


def validate_path(path: Path, base: Path | None = None) -> Path:
    """
    Validate file path to prevent directory traversal.

    Args:
        path: Path to validate
        base: Base directory for relative paths

    Returns:
        Absolute, resolved path

    Raises:
        ValueError: If path contains dangerous patterns
    """
    if base is None:
        base = Path.cwd()

    # Normalize and resolve the path
    resolved = path.resolve()

    # Check for obvious traversal patterns first
    path_str = str(path)
    if "../" in path_str or "..\\" in path_str:
        # Check if it actually goes outside base after resolution
        try:
            resolved.relative_to(base)
        except ValueError:
            raise ValueError(f"Path contains directory traversal: {path}")

    return resolved


def validate_url(url: str) -> str:
    """
    Validate URL to prevent malicious URLs.

    Args:
        url: URL to validate

    Returns:
        Normalized URL

    Raises:
        ValueError: If URL is invalid or dangerous
    """
    try:
        parsed = urlparse(url)

        # Require http or https
        if parsed.scheme not in ['http', 'https']:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

        # Check for localhost/private IPs if needed
        if parsed.hostname in ['localhost', '127.0.0.1']:
            raise ValueError("Localhost URLs not allowed")

        # Limit URL length
        if len(url) > 2048:
            raise ValueError("URL too long")

        return url
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")


def sanitize_template_string(template: str, max_length: int = 10000) -> str:
    """
    Sanitize template strings to prevent injection.

    Args:
        template: Template string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized template

    Raises:
        ValueError: If template contains dangerous patterns
    """
    # Check length
    if len(template) > max_length:
        raise ValueError(f"Template too long: {len(template)} characters")

    # Check for dangerous patterns
    dangerous_patterns = [
        r'\{\{.*\}\}',        # Jinja2 template injection
        r'\{%.*%\}',          # Jinja2 control blocks
        r'<\?.*\?>',          # PHP tags
        r'<%.*%>',            # ERB tags
        r'\$\{.*\}',          # Shell variable expansion
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, template, re.DOTALL):
            raise ValueError("Template contains potentially dangerous pattern")

    return template


def safe_subprocess_run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 30,
    **kwargs
) -> Any:
    """
    Safely run subprocess with validation.

    Args:
        cmd: Command and arguments
        cwd: Working directory
        timeout: Timeout in seconds
        **kwargs: Additional arguments for subprocess.run

    Returns:
        Subprocess result

    Raises:
        ValueError: If command is invalid
    """
    import subprocess

    # Validate command
    if not cmd:
        raise ValueError("Empty command")

    # Validate arguments
    sanitized_cmd = validate_command_args(cmd)

    # Validate working directory
    validated_cwd = validate_path(cwd) if cwd else None

    # Ensure shell=False (default)
    kwargs['shell'] = False

    # Run with timeout
    return subprocess.run(
        sanitized_cmd,
        cwd=validated_cwd,
        timeout=timeout,
        **kwargs
    )


def secure_filename(filename: str) -> str:
    """
    Sanitize filename for secure storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Strip whitespace first
    filename = filename.strip()

    # Replace path separators first
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove path components
    filename = Path(filename).name

    # Replace dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)

    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]

    return filename or 'unnamed'
