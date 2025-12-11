"""
AI Project Synthesizer - Python Resolver

Resolves Python dependencies using uv or pip-tools.
Handles version conflicts with SAT solver.
"""

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)


@dataclass
class ResolvedPackage:
    """A resolved package with exact version."""
    name: str
    version: str
    source: str = "pypi"
    extras: List[str] = field(default_factory=list)

    def to_requirement(self) -> str:
        """Convert to requirements.txt line."""
        if self.extras:
            return f"{self.name}[{','.join(self.extras)}]=={self.version}"
        return f"{self.name}=={self.version}"


@dataclass
class ResolutionResult:
    """Result of dependency resolution."""
    success: bool
    packages: List[ResolvedPackage] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    lockfile_content: str = ""
    resolution_time_ms: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "package_count": len(self.packages),
            "packages": [p.to_requirement() for p in self.packages],
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "resolution_time_ms": self.resolution_time_ms,
        }


class PythonResolver:
    """
    Python dependency resolver using uv SAT solver.

    Features:
    - Fast resolution with uv (10-100x faster than pip)
    - Fallback to pip-compile
    - Conflict detection and resolution
    - Lock file generation

    Example:
        resolver = PythonResolver()
        result = await resolver.resolve([
            "fastapi>=0.100.0",
            "pydantic>=2.0",
            "uvicorn",
        ])
        print(result.lockfile_content)
    """

    def __init__(
        self,
        python_version: str = "3.11",
        prefer_uv: bool = True,
    ):
        """
        Initialize the Python resolver.

        Args:
            python_version: Target Python version
            prefer_uv: Try uv first, fallback to pip-tools
        """
        self.python_version = python_version
        self.prefer_uv = prefer_uv
        self._uv_available = self._check_uv()
        self._pip_compile_available = self._check_pip_compile()

    def _check_uv(self) -> bool:
        """Check if uv is available."""
        try:
            # nosec B603 B607 - hardcoded safe command, no user input
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _check_pip_compile(self) -> bool:
        """Check if pip-compile is available."""
        try:
            # nosec B603 B607 - hardcoded safe command, no user input
            result = subprocess.run(
                ["pip-compile", "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def resolve(
        self,
        requirements: List[str],
        python_version: Optional[str] = None,
        constraints: Optional[List[str]] = None,
    ) -> ResolutionResult:
        """
        Resolve dependencies to exact versions.

        Args:
            requirements: List of requirement strings
            python_version: Override Python version
            constraints: Additional version constraints

        Returns:
            ResolutionResult with resolved packages
        """
        import time
        start_time = time.time()

        python_ver = python_version or self.python_version
        all_reqs = requirements.copy()

        if constraints:
            all_reqs.extend(constraints)

        # Try uv first
        if self.prefer_uv and self._uv_available:
            result = await self._resolve_with_uv(all_reqs, python_ver)
        elif self._pip_compile_available:
            result = await self._resolve_with_pip_compile(all_reqs, python_ver)
        else:
            # Fallback to simple parsing
            result = self._simple_resolve(all_reqs)

        result.resolution_time_ms = int((time.time() - start_time) * 1000)
        return result

    async def _resolve_with_uv(
        self,
        requirements: List[str],
        python_version: str,
    ) -> ResolutionResult:
        """Resolve using uv."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write requirements
            req_file = temp_path / "requirements.in"
            req_file.write_text("\n".join(requirements))

            # Run uv pip compile
            output_file = temp_path / "requirements.txt"

            try:
                process = await asyncio.create_subprocess_exec(
                    "uv", "pip", "compile",
                    str(req_file),
                    "--output-file", str(output_file),
                    "--python-version", python_version,
                    "--quiet",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.warning(f"uv resolution failed: {error_msg}")

                    # Parse conflicts from error
                    conflicts = self._parse_conflicts(error_msg)

                    return ResolutionResult(
                        success=False,
                        conflicts=conflicts,
                        warnings=[error_msg],
                    )

                # Parse output
                lockfile_content = output_file.read_text()
                packages = self._parse_lockfile(lockfile_content)

                return ResolutionResult(
                    success=True,
                    packages=packages,
                    lockfile_content=lockfile_content,
                )

            except Exception as e:
                logger.exception("uv resolution error")
                return ResolutionResult(
                    success=False,
                    conflicts=[str(e)],
                )

    async def _resolve_with_pip_compile(
        self,
        requirements: List[str],
        python_version: str,
    ) -> ResolutionResult:
        """Resolve using pip-compile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write requirements
            req_file = temp_path / "requirements.in"
            req_file.write_text("\n".join(requirements))

            output_file = temp_path / "requirements.txt"

            try:
                process = await asyncio.create_subprocess_exec(
                    "pip-compile",
                    str(req_file),
                    "--output-file", str(output_file),
                    "--quiet",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    conflicts = self._parse_conflicts(error_msg)

                    return ResolutionResult(
                        success=False,
                        conflicts=conflicts,
                        warnings=[error_msg],
                    )

                lockfile_content = output_file.read_text()
                packages = self._parse_lockfile(lockfile_content)

                return ResolutionResult(
                    success=True,
                    packages=packages,
                    lockfile_content=lockfile_content,
                )

            except Exception as e:
                logger.exception("pip-compile resolution error")
                return ResolutionResult(
                    success=False,
                    conflicts=[str(e)],
                )

    def _simple_resolve(
        self,
        requirements: List[str],
    ) -> ResolutionResult:
        """Simple resolution without SAT solver."""
        packages = []

        for req in requirements:
            # Parse requirement
            match = re.match(
                r'^([a-zA-Z0-9][-a-zA-Z0-9._]*)(?:\[([^\]]+)\])?(.*)$',
                req.strip()
            )

            if match:
                name, extras, version_spec = match.groups()

                # Extract version if exact
                version = "latest"
                if version_spec:
                    version_match = re.search(r'==([^\s,]+)', version_spec)
                    if version_match:
                        version = version_match.group(1)

                packages.append(ResolvedPackage(
                    name=name,
                    version=version,
                    extras=extras.split(",") if extras else [],
                ))

        # Generate simple lockfile
        lockfile = "# Resolved dependencies (simple mode)\n"
        lockfile += "# Note: Use uv or pip-tools for proper resolution\n\n"
        for pkg in packages:
            lockfile += f"{pkg.to_requirement()}\n"

        return ResolutionResult(
            success=True,
            packages=packages,
            lockfile_content=lockfile,
            warnings=["Used simple resolution - install uv for better results"],
        )

    def _parse_lockfile(self, content: str) -> List[ResolvedPackage]:
        """Parse lockfile content into packages."""
        packages = []

        for line in content.splitlines():
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Parse package==version
            match = re.match(
                r'^([a-zA-Z0-9][-a-zA-Z0-9._]*)(?:\[([^\]]+)\])?==([^\s]+)',
                line
            )

            if match:
                name, extras, version = match.groups()
                packages.append(ResolvedPackage(
                    name=name,
                    version=version,
                    extras=extras.split(",") if extras else [],
                ))

        return packages

    def _parse_conflicts(self, error_message: str) -> List[str]:
        """Parse conflict information from error message."""
        conflicts = []

        # Common conflict patterns
        patterns = [
            r"requires ([a-zA-Z0-9-_]+)[<>=!]+",
            r"incompatible.*?([a-zA-Z0-9-_]+)",
            r"conflict.*?([a-zA-Z0-9-_]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            conflicts.extend(matches)

        return list(set(conflicts))

    async def check_conflicts(
        self,
        requirements: List[str],
    ) -> List[str]:
        """
        Check for potential conflicts without full resolution.

        Args:
            requirements: List of requirements to check

        Returns:
            List of potential conflict descriptions
        """
        # Group by package name
        by_name: Dict[str, List[str]] = {}

        for req in requirements:
            match = re.match(r'^([a-zA-Z0-9][-a-zA-Z0-9._]*)', req)
            if match:
                name = match.group(1).lower().replace("_", "-")
                by_name.setdefault(name, []).append(req)

        conflicts = []

        for name, reqs in by_name.items():
            if len(reqs) > 1:
                # Check if versions are compatible
                exact_versions = set()
                for req in reqs:
                    match = re.search(r'==([^\s,]+)', req)
                    if match:
                        exact_versions.add(match.group(1))

                if len(exact_versions) > 1:
                    conflicts.append(
                        f"{name}: conflicting exact versions {exact_versions}"
                    )

        return conflicts
