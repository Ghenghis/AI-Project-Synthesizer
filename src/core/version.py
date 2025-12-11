"""
AI Project Synthesizer - Version Management

Semantic versioning with automatic version bumping.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import re
import json
from datetime import datetime

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)


@dataclass
class VersionInfo:
    """Semantic version information."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None  # alpha, beta, rc
    build: Optional[str] = None
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    @classmethod
    def parse(cls, version_string: str) -> "VersionInfo":
        """Parse version string."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$"
        match = re.match(pattern, version_string)
        
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
            build=match.group(5),
        )
    
    def bump_major(self) -> "VersionInfo":
        """Bump major version."""
        return VersionInfo(self.major + 1, 0, 0)
    
    def bump_minor(self) -> "VersionInfo":
        """Bump minor version."""
        return VersionInfo(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> "VersionInfo":
        """Bump patch version."""
        return VersionInfo(self.major, self.minor, self.patch + 1)


def get_version() -> str:
    """Get current version."""
    return __version__


def get_version_info() -> VersionInfo:
    """Get version info object."""
    return VersionInfo.parse(__version__)


def get_build_info() -> dict:
    """Get build information."""
    return {
        "version": __version__,
        "python_version": "3.11+",
        "build_date": datetime.now().isoformat(),
        "components": {
            "mcp_server": True,
            "discovery": True,
            "synthesis": True,
            "voice": True,
            "assistant": True,
        }
    }
