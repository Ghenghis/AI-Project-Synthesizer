"""
AI Project Synthesizer - Custom Exceptions

Hierarchical exception classes for error handling throughout the application.
"""

from typing import Any


class SynthesizerError(Exception):
    """
    Base exception for all AI Synthesizer errors.

    All custom exceptions inherit from this class, allowing
    for catch-all error handling when needed.

    Attributes:
        message: Human-readable error description
        code: Machine-readable error code
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code or "SYNTHESIZER_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ============================================
# Discovery Layer Exceptions
# ============================================


class DiscoveryError(SynthesizerError):
    """Base exception for discovery layer errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="DISCOVERY_ERROR", **kwargs)


class RepositoryNotFoundError(DiscoveryError):
    """Repository could not be found or accessed."""

    def __init__(self, repo_url: str, platform: str = "unknown"):
        super().__init__(
            message=f"Repository not found: {repo_url}",
            details={"repo_url": repo_url, "platform": platform},
        )
        self.code = "REPO_NOT_FOUND"


class PlatformUnavailableError(DiscoveryError):
    """Platform API is unavailable or unreachable."""

    def __init__(self, platform: str, reason: str = ""):
        super().__init__(
            message=f"Platform unavailable: {platform}. {reason}",
            details={"platform": platform, "reason": reason},
        )
        self.code = "PLATFORM_UNAVAILABLE"


class SearchError(DiscoveryError):
    """Error during repository search."""

    def __init__(self, query: str, platform: str, reason: str):
        super().__init__(
            message=f"Search failed on {platform}: {reason}",
            details={"query": query, "platform": platform, "reason": reason},
        )
        self.code = "SEARCH_ERROR"


# ============================================
# Analysis Layer Exceptions
# ============================================


class AnalysisError(SynthesizerError):
    """Base exception for analysis layer errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="ANALYSIS_ERROR", **kwargs)


class ParseError(AnalysisError):
    """Error parsing source code."""

    def __init__(self, file_path: str, language: str, reason: str):
        super().__init__(
            message=f"Failed to parse {file_path}: {reason}",
            details={"file_path": file_path, "language": language, "reason": reason},
        )
        self.code = "PARSE_ERROR"


class UnsupportedLanguageError(AnalysisError):
    """Language is not supported for analysis."""

    def __init__(self, language: str, supported: list):
        super().__init__(
            message=f"Unsupported language: {language}",
            details={"language": language, "supported": supported},
        )
        self.code = "UNSUPPORTED_LANGUAGE"


# ============================================
# Resolution Layer Exceptions
# ============================================


class ResolutionError(SynthesizerError):
    """Base exception for dependency resolution errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="RESOLUTION_ERROR", **kwargs)


class DependencyConflictError(ResolutionError):
    """Unresolvable dependency conflict detected."""

    def __init__(self, package: str, conflicts: list):
        conflict_str = ", ".join(f"{c['source']}: {c['version']}" for c in conflicts)
        super().__init__(
            message=f"Dependency conflict for {package}: {conflict_str}",
            details={"package": package, "conflicts": conflicts},
        )
        self.code = "DEPENDENCY_CONFLICT"


class ResolutionTimeoutError(ResolutionError):
    """Dependency resolution timed out."""

    def __init__(self, timeout_seconds: int):
        super().__init__(
            message=f"Dependency resolution timed out after {timeout_seconds}s",
            details={"timeout_seconds": timeout_seconds},
        )
        self.code = "RESOLUTION_TIMEOUT"


# ============================================
# Synthesis Layer Exceptions
# ============================================


class SynthesisError(SynthesizerError):
    """Base exception for synthesis layer errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="SYNTHESIS_ERROR", **kwargs)


class MergeConflictError(SynthesisError):
    """Code merge conflict that couldn't be resolved."""

    def __init__(self, file_path: str, conflict_type: str):
        super().__init__(
            message=f"Merge conflict in {file_path}: {conflict_type}",
            details={"file_path": file_path, "conflict_type": conflict_type},
        )
        self.code = "MERGE_CONFLICT"


class ExtractionError(SynthesisError):
    """Error extracting code from repository."""

    def __init__(self, repo_url: str, component: str, reason: str):
        super().__init__(
            message=f"Failed to extract {component} from {repo_url}: {reason}",
            details={"repo_url": repo_url, "component": component, "reason": reason},
        )
        self.code = "EXTRACTION_ERROR"


class TemplateError(SynthesisError):
    """Error applying project template."""

    def __init__(self, template: str, reason: str):
        super().__init__(
            message=f"Template error ({template}): {reason}",
            details={"template": template, "reason": reason},
        )
        self.code = "TEMPLATE_ERROR"


# ============================================
# Generation Layer Exceptions
# ============================================


class GenerationError(SynthesizerError):
    """Base exception for documentation generation errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="GENERATION_ERROR", **kwargs)


class DiagramGenerationError(GenerationError):
    """Error generating diagrams."""

    def __init__(self, diagram_type: str, reason: str):
        super().__init__(
            message=f"Failed to generate {diagram_type} diagram: {reason}",
            details={"diagram_type": diagram_type, "reason": reason},
        )
        self.code = "DIAGRAM_ERROR"


# ============================================
# Infrastructure Exceptions
# ============================================


class RateLimitError(SynthesizerError):
    """API rate limit exceeded."""

    def __init__(self, platform: str, reset_time: int | None = None):
        message = f"Rate limit exceeded for {platform}"
        if reset_time:
            message += f". Resets in {reset_time} seconds"

        super().__init__(
            message=message, details={"platform": platform, "reset_time": reset_time}
        )
        self.code = "RATE_LIMITED"


class AuthenticationError(SynthesizerError):
    """Authentication failed for platform."""

    def __init__(self, platform: str, reason: str = "Invalid or expired token"):
        super().__init__(
            message=f"Authentication failed for {platform}: {reason}",
            details={"platform": platform, "reason": reason},
        )
        self.code = "AUTH_FAILED"


class ConfigurationError(SynthesizerError):
    """Configuration error."""

    def __init__(self, setting: str, reason: str):
        super().__init__(
            message=f"Configuration error for {setting}: {reason}",
            details={"setting": setting, "reason": reason},
        )
        self.code = "CONFIG_ERROR"


class LLMError(SynthesizerError):
    """Error from LLM service."""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"LLM error ({provider}): {reason}",
            details={"provider": provider, "reason": reason},
        )
        self.code = "LLM_ERROR"


class TimeoutError(SynthesizerError):
    """Operation timed out."""

    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout_seconds}s",
            details={"operation": operation, "timeout_seconds": timeout_seconds},
        )
        self.code = "TIMEOUT"


class SecurityScanError(SynthesizerError):
    """Security scan failed or found issues."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="SECURITY_SCAN_ERROR", **kwargs)
