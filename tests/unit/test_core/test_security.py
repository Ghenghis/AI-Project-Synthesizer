"""
Unit tests for core security module.
"""

import pytest

from src.core.security import (
    SecretManager,
    get_secure_logger,
)


class TestSecretManager:
    """Test SecretManager functionality."""

    def test_mask_secrets(self):
        """Should mask secrets in text."""
        result = SecretManager.mask_secrets(
            "token: ghp_abcdefghijklmnopqrstuvwxyz123456789"
        )
        assert "ghp_" not in result or "*" in result

    def test_mask_empty_text(self):
        """Should handle empty text."""
        result = SecretManager.mask_secrets("")
        assert result == ""


class TestSecureLogger:
    """Test secure logger functionality."""

    def test_get_secure_logger(self):
        """Should return a logger instance."""
        logger = get_secure_logger("test_module")
        assert logger is not None

    def test_logger_has_methods(self):
        """Should have standard logging methods."""
        logger = get_secure_logger("test")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
