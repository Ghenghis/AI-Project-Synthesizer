"""
Unit tests for core version module.
"""

import pytest
from src.core.version import (
    __version__,
    __version_info__,
    VersionInfo,
)


class TestVersionConstants:
    """Test version constants."""
    
    def test_version_string(self):
        """Should have __version__ constant."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert "." in __version__
    
    def test_version_info_tuple(self):
        """Should have __version_info__ tuple."""
        assert __version_info__ is not None
        assert isinstance(__version_info__, tuple)
        assert len(__version_info__) == 3


class TestVersionInfo:
    """Test VersionInfo dataclass."""
    
    def test_create_version_info(self):
        """Should create version info."""
        info = VersionInfo(major=1, minor=2, patch=3)
        assert info.major == 1
        assert info.minor == 2
        assert info.patch == 3
    
    def test_version_to_string(self):
        """Should convert to string."""
        info = VersionInfo(major=1, minor=2, patch=3)
        assert str(info) == "1.2.3"
    
    def test_version_with_prerelease(self):
        """Should include prerelease in string."""
        info = VersionInfo(major=1, minor=0, patch=0, prerelease="alpha")
        assert str(info) == "1.0.0-alpha"
    
    def test_version_with_build(self):
        """Should include build in string."""
        info = VersionInfo(major=1, minor=0, patch=0, build="20231201")
        assert str(info) == "1.0.0+20231201"
    
    def test_parse_simple_version(self):
        """Should parse simple version string."""
        info = VersionInfo.parse("2.0.0")
        assert info.major == 2
        assert info.minor == 0
        assert info.patch == 0
    
    def test_parse_version_with_prerelease(self):
        """Should parse version with prerelease."""
        info = VersionInfo.parse("1.0.0-beta")
        assert info.prerelease == "beta"
    
    def test_parse_invalid_version(self):
        """Should raise error for invalid version."""
        with pytest.raises(ValueError):
            VersionInfo.parse("invalid")
    
    def test_bump_major(self):
        """Should bump major version."""
        info = VersionInfo(major=1, minor=2, patch=3)
        bumped = info.bump_major()
        assert bumped.major == 2
        assert bumped.minor == 0
        assert bumped.patch == 0
    
    def test_bump_minor(self):
        """Should bump minor version."""
        info = VersionInfo(major=1, minor=2, patch=3)
        bumped = info.bump_minor()
        assert bumped.minor == 3
        assert bumped.patch == 0
    
    def test_bump_patch(self):
        """Should bump patch version."""
        info = VersionInfo(major=1, minor=2, patch=3)
        bumped = info.bump_patch()
        assert bumped.patch == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
