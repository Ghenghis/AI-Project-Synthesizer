"""
AI Project Synthesizer - Python Resolver Tests

Unit tests for the Python dependency resolver using uv/pip-compile.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.resolution.python_resolver import (
    PythonResolver,
    ResolutionResult,
    ResolvedPackage,
)


class TestPythonResolver:
    """Test suite for PythonResolver."""

    @pytest.fixture
    def resolver(self):
        """Create test resolver instance."""
        return PythonResolver(python_version="3.11")

    @pytest.fixture
    def mock_requirements(self):
        """Sample requirements for testing."""
        return [
            "fastapi>=0.100.0",
            "pydantic>=2.0.0",
            "httpx>=0.24.0",
        ]

    # ========================================
    # Initialization Tests
    # ========================================

    def test_initialization(self, resolver):
        """Test resolver initialization."""
        assert resolver.python_version == "3.11"
        assert resolver.prefer_uv is True
        assert isinstance(resolver._uv_available, bool)
        assert isinstance(resolver._pip_compile_available, bool)

    def test_check_uv_available(self):
        """Test uv availability check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            resolver = PythonResolver()
            assert resolver._uv_available is True

            mock_run.return_value.returncode = 1
            resolver = PythonResolver()
            assert resolver._uv_available is False

    def test_check_pip_compile_available(self):
        """Test pip-compile availability check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            resolver = PythonResolver()
            assert resolver._pip_compile_available is True

            mock_run.return_value.returncode = 1
            resolver = PythonResolver()
            assert resolver._pip_compile_available is False

    # ========================================
    # Resolution Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_resolve_with_uv(self, resolver, mock_requirements):
        """Test resolution using uv."""
        with patch.object(resolver, "_uv_available", True), \
             patch.object(resolver, "_resolve_with_uv") as mock_resolve:

            mock_result = ResolutionResult(
                success=True,
                packages=[
                    ResolvedPackage(name="fastapi", version="0.104.1"),
                    ResolvedPackage(name="pydantic", version="2.5.0"),
                ],
                lockfile_content="fastapi==0.104.1\npydantic==2.5.0\n"
            )
            mock_resolve.return_value = mock_result

            result = await resolver.resolve(mock_requirements)

            assert result.success is True
            assert len(result.packages) == 2
            assert "fastapi==0.104.1" in result.lockfile_content

    @pytest.mark.asyncio
    async def test_resolve_fallback_to_pip_compile(self, resolver, mock_requirements):
        """Test fallback to pip-compile when uv unavailable."""
        with patch.object(resolver, "_uv_available", False), \
             patch.object(resolver, "_pip_compile_available", True), \
             patch.object(resolver, "_resolve_with_pip_compile") as mock_resolve:

            mock_result = ResolutionResult(success=True)
            mock_resolve.return_value = mock_result

            result = await resolver.resolve(mock_requirements)

            assert result.success is True
            mock_resolve.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_simple_fallback(self, resolver, mock_requirements):
        """Test simple resolution when neither uv nor pip-compile available."""
        with patch.object(resolver, "_uv_available", False), \
             patch.object(resolver, "_pip_compile_available", False):

            result = await resolver.resolve(mock_requirements)

            assert result.success is True
            assert len(result.packages) == 3
            assert "Used simple resolution" in result.warnings[0]

    # ========================================
    # UV Resolution Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_resolve_with_uv_success(self, resolver):
        """Test successful uv resolution."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess, \
             patch("tempfile.TemporaryDirectory") as mock_temp:

            # Mock subprocess
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Mock temp directory - use Windows path
            temp_dir = Path("C:\\tmp\\test")
            mock_temp.return_value.__enter__.return_value = str(temp_dir)

            # Mock file operations
            with patch.object(Path, "write_text"), \
                 patch.object(Path, "read_text", return_value="fastapi==0.104.1\npydantic==2.5.0\n"):

                result = await resolver._resolve_with_uv(
                    ["fastapi>=0.100.0"],
                    "3.11"
                )

                assert result.success is True
                assert len(result.packages) == 2

    @pytest.mark.asyncio
    async def test_resolve_with_uv_conflict(self, resolver):
        """Test uv resolution with conflicts."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess, \
             patch("tempfile.TemporaryDirectory") as mock_temp:

            # Mock subprocess failure
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"",
                b"error: package fastapi has conflicting requirements"
            )
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            # Mock temp directory - use Windows path
            temp_dir = Path("C:\\tmp\\test")
            mock_temp.return_value.__enter__.return_value = str(temp_dir)

            # Mock Path operations to avoid actual file system
            with patch.object(Path, "write_text"), \
                 patch.object(Path, "read_text", return_value="fastapi==0.104.1\npydantic==2.5.0\n"):

                result = await resolver._resolve_with_uv(
                    ["fastapi>=0.100.0"],
                    "3.11"
                )

            assert result.success is False
            assert len(result.conflicts) > 0

    # ========================================
    # Lockfile Parsing Tests
    # ========================================

    def test_parse_lockfile(self, resolver):
        """Test lockfile parsing."""
        content = """
# Generated by uv
fastapi==0.104.1
pydantic==2.5.0
pydantic-core==2.14.5
starlette==0.27.0
"""
        packages = resolver._parse_lockfile(content)

        assert len(packages) == 4
        assert packages[0].name == "fastapi"
        assert packages[0].version == "0.104.1"
        assert packages[1].name == "pydantic"
        assert packages[1].version == "2.5.0"

    def test_parse_lockfile_with_extras(self, resolver):
        """Test parsing lockfile with package extras."""
        content = """
fastapi[all]==0.104.1
pydantic[email]==2.5.0
"""
        packages = resolver._parse_lockfile(content)

        assert len(packages) == 2
        assert packages[0].name == "fastapi"
        assert packages[0].extras == ["all"]
        assert packages[1].name == "pydantic"
        assert packages[1].extras == ["email"]

    def test_parse_lockfile_ignores_comments(self, resolver):
        """Test that comments and empty lines are ignored."""
        content = """
# This is a comment
# Another comment
fastapi==0.104.1

pydantic==2.5.0  # Inline comment
"""
        packages = resolver._parse_lockfile(content)

        assert len(packages) == 2
        assert packages[0].name == "fastapi"
        assert packages[1].name == "pydantic"

    # ========================================
    # Conflict Detection Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_check_conflicts_none(self, resolver):
        """Test conflict detection with no conflicts."""
        requirements = [
            "fastapi>=0.100.0",
            "pydantic>=2.0.0",
            "httpx>=0.24.0",
        ]

        conflicts = await resolver.check_conflicts(requirements)

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_check_conflicts_exact_versions(self, resolver):
        """Test conflict detection with exact version conflicts."""
        requirements = [
            "fastapi==0.100.0",
            "fastapi==0.104.1",
            "pydantic>=2.0.0",
        ]

        conflicts = await resolver.check_conflicts(requirements)

        assert len(conflicts) == 1
        assert "fastapi" in conflicts[0]
        assert "0.100.0" in conflicts[0]
        assert "0.104.1" in conflicts[0]

    @pytest.mark.asyncio
    async def test_check_conflicts_case_insensitive(self, resolver):
        """Test conflict detection is case insensitive."""
        requirements = [
            "FastAPI==0.100.0",
            "fastapi==0.104.1",
        ]

        conflicts = await resolver.check_conflicts(requirements)

        assert len(conflicts) == 1
        assert "fastapi" in conflicts[0].lower()

    # ========================================
    # Simple Resolution Tests
    # ========================================

    def test_simple_resolve(self, resolver):
        """Test simple resolution without SAT solver."""
        requirements = [
            "fastapi>=0.100.0",
            "pydantic==2.5.0",
            "httpx[http2]>=0.24.0",
        ]

        result = resolver._simple_resolve(requirements)

        assert result.success is True
        assert len(result.packages) == 3

        # Check exact version preserved
        fastapi_pkg = next(p for p in result.packages if p.name == "fastapi")
        assert fastapi_pkg.version == "latest"

        pydantic_pkg = next(p for p in result.packages if p.name == "pydantic")
        assert pydantic_pkg.version == "2.5.0"

        httpx_pkg = next(p for p in result.packages if p.name == "httpx")
        assert httpx_pkg.extras == ["http2"]

    # ========================================
    # Integration Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_full_resolution_workflow(self, resolver):
        """Test complete resolution workflow."""
        requirements = [
            "fastapi>=0.100.0",
            "pydantic>=2.0.0",
        ]

        with patch.object(resolver, "_uv_available", False), \
             patch.object(resolver, "_pip_compile_available", False):

            result = await resolver.resolve(
                requirements,
                python_version="3.11",
                constraints=["python>=3.11"]
            )

            assert result.success is True
            assert len(result.packages) >= 2  # Simple resolver might include more
            assert result.resolution_time_ms >= 0  # Can be 0 in tests
            assert "simple mode" in result.lockfile_content
