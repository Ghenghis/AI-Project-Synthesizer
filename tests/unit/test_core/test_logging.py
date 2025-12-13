"""
Unit tests for core logging module.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.core.logging import (
    get_logger,
    setup_logging,
)


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_logger_returns_logger(self):
        """Should return a logger instance."""
        logger = get_logger("test_module")
        assert logger is not None
    
    def test_get_logger_is_callable(self):
        """Logger should have logging methods."""
        logger = get_logger("my_module")
        # structlog loggers have these methods
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')


class TestSetupLogging:
    """Test setup_logging function."""
    
    def test_setup_logging_no_error(self):
        """Should setup logging without error."""
        setup_logging()
    
    def test_setup_logging_with_level(self):
        """Should accept log level parameter."""
        setup_logging(level="DEBUG")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
