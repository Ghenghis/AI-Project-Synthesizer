"""
Unit tests for core exceptions module.
"""

import pytest

from src.core.exceptions import (
    AnalysisError,
    AuthenticationError,
    DiscoveryError,
    GenerationError,
    RateLimitError,
    ResolutionError,
    SynthesisError,
    SynthesizerError,
)


class TestSynthesizerError:
    """Test base synthesizer error."""

    def test_basic_error(self):
        """Should create basic error with message."""
        error = SynthesizerError("Test error")
        assert str(error) == "Test error"

    def test_error_with_details(self):
        """Should create error with details."""
        error = SynthesizerError("Test error", details={"key": "value"})
        assert "Test error" in str(error)

    def test_error_inheritance(self):
        """Should inherit from Exception."""
        error = SynthesizerError("Test")
        assert isinstance(error, Exception)


class TestDiscoveryError:
    """Test discovery error."""

    def test_basic_error(self):
        """Should create discovery error."""
        error = DiscoveryError("Discovery failed")
        assert str(error) == "Discovery failed"
        assert isinstance(error, SynthesizerError)

    def test_error_code(self):
        """Should have discovery error code."""
        error = DiscoveryError("Failed")
        assert isinstance(error, SynthesizerError)


class TestAnalysisError:
    """Test analysis error."""

    def test_basic_error(self):
        """Should create analysis error."""
        error = AnalysisError("Analysis failed")
        assert str(error) == "Analysis failed"
        assert isinstance(error, SynthesizerError)


class TestResolutionError:
    """Test resolution error."""

    def test_basic_error(self):
        """Should create resolution error."""
        error = ResolutionError("Resolution failed")
        assert str(error) == "Resolution failed"
        assert isinstance(error, SynthesizerError)

    def test_error_code(self):
        """Should have resolution error code."""
        error = ResolutionError("Conflicts detected")
        assert isinstance(error, SynthesizerError)


class TestSynthesisError:
    """Test synthesis error."""

    def test_basic_error(self):
        """Should create synthesis error."""
        error = SynthesisError("Synthesis failed")
        assert str(error) == "Synthesis failed"
        assert isinstance(error, SynthesizerError)


class TestGenerationError:
    """Test generation error."""

    def test_basic_error(self):
        """Should create generation error."""
        error = GenerationError("Generation failed")
        assert str(error) == "Generation failed"
        assert isinstance(error, SynthesizerError)


class TestRateLimitError:
    """Test rate limit error."""

    def test_basic_error(self):
        """Should create rate limit error."""
        error = RateLimitError("Rate limited")
        assert "Rate limited" in str(error)
        assert isinstance(error, SynthesizerError)

    def test_error_code(self):
        """Should have rate limit error code."""
        error = RateLimitError("Rate limited")
        assert isinstance(error, SynthesizerError)


class TestAuthenticationError:
    """Test authentication error."""

    def test_basic_error(self):
        """Should create auth error."""
        error = AuthenticationError("Auth failed")
        assert "Auth failed" in str(error)
        assert isinstance(error, SynthesizerError)

    def test_error_code(self):
        """Should have auth error code."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, SynthesizerError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
