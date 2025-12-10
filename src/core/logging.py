"""
AI Project Synthesizer - Logging Configuration

Structured logging setup using structlog for consistent,
machine-parseable log output across all components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import structlog
from structlog.types import Processor

from src.core.config import get_settings


def setup_logging(
    level: Optional[str] = None,
    json_format: bool = False,
    log_file: Optional[Path] = None
) -> None:
    """
    Configure application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Output logs as JSON (useful for production)
        log_file: Optional file path for log output
    """
    settings = get_settings()
    
    # Determine log level
    log_level = level or settings.app.log_level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # Build processor chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    # Add appropriate renderer based on format
    if json_format or settings.app.app_env == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback
            )
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", repo="owner/repo")
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding temporary context to logs.
    
    Example:
        >>> with LogContext(request_id="abc123", user="john"):
        ...     logger.info("Processing request")
        ...     # Logs will include request_id and user
    """
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self._token = None
    
    def __enter__(self):
        self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.unbind_contextvars(*self.context.keys())
        return False


# Initialize logging on module import
_initialized = False

def _ensure_logging_initialized():
    """Ensure logging is initialized exactly once."""
    global _initialized
    if not _initialized:
        setup_logging()
        _initialized = True

_ensure_logging_initialized()
