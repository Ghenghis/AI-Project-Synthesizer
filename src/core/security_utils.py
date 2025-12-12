"""
Security utilities for input validation and secure operations.
"""

import shlex
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse


def validate_command_args(args: List[str]) -> List[str]:
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


def validate_path(path: Path, base_path: Optional[Path] = None) -> Path:
    """
    Validate file path to prevent directory traversal.
    
    Args:
        path: Path to validate
        base_path: Base directory to restrict to
        
    Returns:
        Absolute, validated path
        
    Raises:
        ValueError: If path is outside base_path or contains dangerous patterns
    """
    # Resolve to absolute path
    abs_path = path.resolve()
    
    # Check for dangerous patterns
    if '..' in path.parts:
        raise ValueError(f"Path contains directory traversal: {path}")
    
    # Restrict to base path if provided
    if base_path:
        base_abs = base_path.resolve()
        try:
            abs_path.relative_to(base_abs)
        except ValueError:
            raise ValueError(f"Path {abs_path} is outside base directory {base_abs}")
    
    return abs_path


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
        r'<\?.*\?>',          # PHP tags
        r'<%.*%>',            # ERB tags
        r'\$\{.*\}',          # Shell variable expansion
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, template, re.DOTALL):
            raise ValueError(f"Template contains potentially dangerous pattern")
    
    return template


def safe_subprocess_run(
    cmd: List[str],
    cwd: Optional[Path] = None,
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
    if cwd:
        validated_cwd = validate_path(cwd)
    else:
        validated_cwd = None
    
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
