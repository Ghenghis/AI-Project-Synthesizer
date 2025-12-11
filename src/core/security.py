"""
AI Project Synthesizer - Security Utilities

Enterprise-grade security utilities for secret management,
input validation, and secure logging.
"""

import re
import hashlib
import secrets
from typing import Dict, Any
from urllib.parse import urlparse
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Manages secure handling of sensitive data.
    
    Provides utilities for masking secrets in logs,
    validating input, and sanitizing data.
    """

    # Patterns for detecting secrets in logs
    SECRET_PATTERNS = [
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub tokens
        r'gho_[a-zA-Z0-9]{36}',  # GitHub OAuth tokens
        r'ghu_[a-zA-Z0-9]{36}',  # GitHub user tokens
        r'ghs_[a-zA-Z0-9]{36}',  # GitHub server tokens
        r'ghr_[a-zA-Z0-9]{36}',  # GitHub refresh tokens
        r'xoxb-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}',  # Slack bot tokens
        r'xoxp-[0-9]{13}-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}',  # Slack user tokens
        r'sk-[a-zA-Z0-9]{48}',  # Stripe keys
        r'AIza[0-9A-Za-z_-]{35}',  # Google API keys
        r'AKIA[0-9A-Z]{16}',  # AWS access keys
        r'[a-zA-Z0-9_-]{40}\.[a-zA-Z0-9_-]{64}\.[a-zA-Z0-9_-]{25}',  # OpenAI tokens
        r'[a-zA-Z0-9_-]{32}',  # Generic API keys
    ]

    @staticmethod
    def mask_secrets(text: str, mask_char: str = "*") -> str:
        """
        Mask potential secrets in text.
        
        Args:
            text: Text that might contain secrets
            mask_char: Character to use for masking
            
        Returns:
            Text with secrets masked
        """
        if not text:
            return text

        masked_text = text

        for pattern in SecretManager.SECRET_PATTERNS:
            # Replace each match with masked version
            matches = re.finditer(pattern, masked_text, re.IGNORECASE)
            for match in matches:
                secret = match.group()
                # Keep first and last 4 characters, mask the rest
                if len(secret) > 8:
                    masked = secret[:4] + mask_char * (len(secret) - 8) + secret[-4:]
                else:
                    masked = mask_char * len(secret)
                masked_text = masked_text.replace(secret, masked)

        return masked_text

    @staticmethod
    def hash_secret(secret: str) -> str:
        """
        Create a secure hash of a secret for comparison.
        
        Args:
            secret: Secret to hash
            
        Returns:
            SHA-256 hash of the secret
        """
        return hashlib.sha256(secret.encode()).hexdigest()

    @staticmethod
    def generate_secure_id(length: int = 32) -> str:
        """
        Generate a cryptographically secure random ID.
        
        Args:
            length: Length of the ID to generate
            
        Returns:
            Secure random string
        """
        return secrets.token_urlsafe(length)[:length]


class InputValidator:
    """
    Validates and sanitizes user inputs.
    """

    # GitHub repository URL pattern
    GITHUB_URL_PATTERN = re.compile(
        r'^https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+/?$',
        re.IGNORECASE
    )

    # Generic URL pattern
    URL_PATTERN = re.compile(
        r'^https?://(?:[\w\-]+\.)+[\w\-]+(?:/[\w\-./?%&=]*)?$',
        re.IGNORECASE
    )

    # Safe filename pattern
    SAFE_FILENAME_PATTERN = re.compile(r'^[\w\-\.]+$')

    @staticmethod
    def validate_repository_url(url: str) -> bool:
        """
        Validate repository URL format.
        
        Args:
            url: Repository URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False

        # Normalize URL
        url = url.strip().lower()

        # Check GitHub URLs specifically
        if InputValidator.GITHUB_URL_PATTERN.match(url):
            return True

        # Check other valid URLs
        if InputValidator.URL_PATTERN.match(url):
            return True

        return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"

        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\.\.', '_', sanitized)
        sanitized = sanitized.strip('._')

        # Ensure it's not empty
        if not sanitized:
            sanitized = "unnamed"

        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]

        return sanitized

    @staticmethod
    def validate_search_query(query: str) -> bool:
        """
        Validate search query to prevent injection.
        
        Args:
            query: Search query to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not query or not isinstance(query, str):
            return False

        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        if any(char in query for char in dangerous_chars):
            return False

        # Check length
        if len(query.strip()) > 1000:
            return False

        return True

    @staticmethod
    def sanitize_path(path: str) -> str:
        """
        Sanitize file system path to prevent traversal.
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path
        """
        if not path:
            return "."

        # Normalize path separators
        path = path.replace('\\', '/')

        # Remove path traversal attempts
        path = re.sub(r'\.\./', '', path)
        path = re.sub(r'\.\.\/', '', path)

        # Remove leading slashes to prevent absolute paths
        path = path.lstrip('/')

        return path


class SecureLogger:
    """
    Wrapper for secure logging that masks secrets.
    """

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)

    def _sanitize_message(self, message: str, **kwargs) -> tuple[str, Dict[str, Any]]:
        """
        Sanitize message and kwargs for logging.
        
        Args:
            message: Log message
            **kwargs: Additional context
            
        Returns:
            Tuple of sanitized message and context
        """
        # Mask secrets in message
        sanitized_message = SecretManager.mask_secrets(str(message))

        # Sanitize context
        sanitized_context = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_context[key] = SecretManager.mask_secrets(value)
            elif isinstance(value, dict):
                sanitized_context[key] = {
                    k: SecretManager.mask_secrets(str(v)) if isinstance(v, str) else v
                    for k, v in value.items()
                }
            else:
                sanitized_context[key] = value

        return sanitized_message, sanitized_context

    def info(self, message: str, **kwargs):
        """Log info message with secret masking."""
        sanitized_msg, sanitized_ctx = self._sanitize_message(message, **kwargs)
        self.logger.info(sanitized_msg, extra=sanitized_ctx)

    def error(self, message: str, **kwargs):
        """Log error message with secret masking."""
        sanitized_msg, sanitized_ctx = self._sanitize_message(message, **kwargs)
        self.logger.error(sanitized_msg, extra=sanitized_ctx)

    def warning(self, message: str, **kwargs):
        """Log warning message with secret masking."""
        sanitized_msg, sanitized_ctx = self._sanitize_message(message, **kwargs)
        self.logger.warning(sanitized_msg, extra=sanitized_ctx)

    def debug(self, message: str, **kwargs):
        """Log debug message with secret masking."""
        sanitized_msg, sanitized_ctx = self._sanitize_message(message, **kwargs)
        self.logger.debug(sanitized_msg, extra=sanitized_ctx)


def secure_input(validation_func=None):
    """
    Decorator for validating and sanitizing function inputs.
    
    Args:
        validation_func: Optional function to validate inputs
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate common inputs
            if 'repo_url' in kwargs:
                if not InputValidator.validate_repository_url(kwargs['repo_url']):
                    raise ValueError(f"Invalid repository URL: {kwargs['repo_url']}")

            if 'query' in kwargs:
                if not InputValidator.validate_search_query(kwargs['query']):
                    raise ValueError(f"Invalid search query: {kwargs['query']}")

            if 'filename' in kwargs:
                kwargs['filename'] = InputValidator.sanitize_filename(kwargs['filename'])

            if 'path' in kwargs:
                kwargs['path'] = InputValidator.sanitize_path(kwargs['path'])

            # Apply custom validation if provided
            if validation_func:
                validation_func(*args, **kwargs)

            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecurityConfig:
    """
    Security configuration settings.
    """

    # Rate limiting
    DEFAULT_RATE_LIMIT = 1000  # requests per hour
    BURST_SIZE = 100

    # Input validation
    MAX_QUERY_LENGTH = 1000
    MAX_FILENAME_LENGTH = 255
    MAX_PATH_LENGTH = 4096

    # Secret handling
    MASK_SECRETS_IN_LOGS = True
    SECRET_MASK_CHAR = "*"

    # URL validation
    ALLOWED_PROTOCOLS = ['http', 'https']
    ALLOWED_DOMAINS = [
        'github.com',
        'gitlab.com',
        'huggingface.co',
        'kaggle.com',
        'arxiv.org'
    ]

    @classmethod
    def is_domain_allowed(cls, url: str) -> bool:
        """
        Check if URL domain is in allowed list.
        
        Args:
            url: URL to check
            
        Returns:
            True if domain is allowed
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain in cls.ALLOWED_DOMAINS
        except Exception:
            return False


# Create secure logger instances
def get_secure_logger(name: str) -> SecureLogger:
    """Get a secure logger instance."""
    return SecureLogger(name)
