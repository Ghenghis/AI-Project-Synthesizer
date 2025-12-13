"""
AI Project Synthesizer - Dependency Analyzer

Analyzes project dependencies across package managers (pip, npm, cargo, etc.).
Builds dependency graphs and detects conflicts.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import toml

logger = logging.getLogger(__name__)


@dataclass
class Dependency:
    """Represents a single dependency."""
    name: str
    version_spec: str  # e.g., ">=1.0.0,<2.0.0"
    extras: list[str] = field(default_factory=list)
    source_file: str = ""
    package_manager: str = "pip"
    is_dev: bool = False
    is_optional: bool = False

    @property
    def normalized_name(self) -> str:
        """Return normalized package name (lowercase, underscores to hyphens)."""
        return self.name.lower().replace("_", "-")


@dataclass
class DependencyConflict:
    """Represents a conflict between dependencies."""
    package_name: str
    dep_a: Dependency
    dep_b: Dependency
    reason: str
    resolvable: bool = True
    suggested_version: str | None = None


@dataclass
class DependencyGraph:
    """Complete dependency graph for a project."""
    direct: list[Dependency] = field(default_factory=list)
    transitive: list[Dependency] = field(default_factory=list)
    conflicts: list[DependencyConflict] = field(default_factory=list)
    dev_dependencies: list[Dependency] = field(default_factory=list)

    @property
    def all_dependencies(self) -> list[Dependency]:
        """Return all dependencies."""
        return self.direct + self.transitive

    @property
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts."""
        return len(self.conflicts) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": {
                "direct_count": len(self.direct),
                "transitive_count": len(self.transitive),
                "dev_count": len(self.dev_dependencies),
                "conflict_count": len(self.conflicts),
                "has_conflicts": self.has_conflicts,
            },
            "direct": [
                {
                    "name": d.name,
                    "version": d.version_spec,
                    "extras": d.extras,
                    "source": d.source_file,
                }
                for d in self.direct
            ],
            "conflicts": [
                {
                    "package": c.package_name,
                    "versions": [c.dep_a.version_spec, c.dep_b.version_spec],
                    "reason": c.reason,
                    "resolvable": c.resolvable,
                    "suggested": c.suggested_version,
                }
                for c in self.conflicts
            ],
        }


class DependencyAnalyzer:
    """
    Analyzes project dependencies across multiple package managers.

    Supported:
    - Python: requirements.txt, pyproject.toml, setup.py, Pipfile
    - Node.js: package.json
    - Rust: Cargo.toml

    Usage:
        analyzer = DependencyAnalyzer()
        graph = await analyzer.analyze(Path("./my-project"))
        print(graph.to_dict())
    """

    DEPENDENCY_FILES = {
        "python": [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-test.txt",
            "dev-requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "Pipfile",
        ],
        "node": [
            "package.json",
        ],
        "rust": [
            "Cargo.toml",
        ],
    }

    def __init__(self):
        """Initialize the dependency analyzer."""
        self._version_pattern = re.compile(
            r'^([a-zA-Z0-9][-a-zA-Z0-9._]*[a-zA-Z0-9]|[a-zA-Z0-9])'
            r'(\[[-a-zA-Z0-9._,]+\])?'
            r'\s*'
            r'([<>=!~]+\s*[\d.*]+(?:\s*,\s*[<>=!~]+\s*[\d.*]+)*)?'
        )

    async def analyze(self, repo_path: Path) -> DependencyGraph:
        """
        Analyze all dependencies in a repository.

        Args:
            repo_path: Path to repository root

        Returns:
            DependencyGraph with all discovered dependencies
        """
        direct_deps: list[Dependency] = []
        dev_deps: list[Dependency] = []

        # Detect and parse each dependency file
        for pm, files in self.DEPENDENCY_FILES.items():
            for filename in files:
                file_path = repo_path / filename
                if file_path.exists():
                    logger.debug(f"Parsing {file_path}")
                    deps, dev = await self._parse_file(file_path, pm)
                    direct_deps.extend(deps)
                    dev_deps.extend(dev)

        # Also check for requirements in subdirectories
        for req_file in repo_path.glob("**/requirements*.txt"):
            if "venv" not in str(req_file) and "node_modules" not in str(req_file):
                deps, dev = await self._parse_file(req_file, "python")
                if "dev" in req_file.name.lower() or "test" in req_file.name.lower():
                    dev_deps.extend(deps)
                else:
                    direct_deps.extend(deps)

        # Deduplicate
        direct_deps = self._deduplicate(direct_deps)
        dev_deps = self._deduplicate(dev_deps)

        # Detect conflicts
        conflicts = self._detect_conflicts(direct_deps + dev_deps)

        return DependencyGraph(
            direct=direct_deps,
            transitive=[],  # Would require actual resolution
            conflicts=conflicts,
            dev_dependencies=dev_deps,
        )

    async def _parse_file(
        self,
        file_path: Path,
        package_manager: str
    ) -> tuple[list[Dependency], list[Dependency]]:
        """Parse a dependency file and return (regular, dev) dependencies."""
        try:
            if file_path.name == "requirements.txt" or file_path.name.startswith("requirements"):
                deps = self._parse_requirements_txt(file_path)
                is_dev = "dev" in file_path.name.lower() or "test" in file_path.name.lower()
                return ([], deps) if is_dev else (deps, [])

            elif file_path.name == "pyproject.toml":
                return self._parse_pyproject_toml(file_path)

            elif file_path.name == "package.json":
                return self._parse_package_json(file_path)

            elif file_path.name == "Cargo.toml":
                return self._parse_cargo_toml(file_path)

            elif file_path.name == "Pipfile":
                return self._parse_pipfile(file_path)

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

        return [], []

    def _parse_requirements_txt(self, file_path: Path) -> list[Dependency]:
        """Parse requirements.txt format."""
        deps = []
        content = file_path.read_text(encoding="utf-8")

        for line in content.splitlines():
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Handle -r includes (recursive requirements)
            if line.startswith("-r "):
                continue

            # Parse the requirement
            dep = self._parse_requirement_line(line, str(file_path))
            if dep:
                deps.append(dep)

        return deps

    def _parse_requirement_line(
        self,
        line: str,
        source_file: str
    ) -> Dependency | None:
        """Parse a single requirement line."""
        # Remove inline comments
        if "#" in line:
            line = line.split("#")[0].strip()

        # Handle environment markers
        if ";" in line:
            line = line.split(";")[0].strip()

        # Match the pattern
        match = self._version_pattern.match(line)
        if match:
            name = match.group(1)
            extras_str = match.group(2) or ""
            version_spec = match.group(3) or ""

            extras = []
            if extras_str:
                extras = [e.strip() for e in extras_str[1:-1].split(",")]

            return Dependency(
                name=name,
                version_spec=version_spec.strip(),
                extras=extras,
                source_file=source_file,
                package_manager="pip",
            )

        return None

    def _parse_pyproject_toml(
        self,
        file_path: Path
    ) -> tuple[list[Dependency], list[Dependency]]:
        """Parse pyproject.toml for dependencies."""
        deps = []
        dev_deps = []

        content = file_path.read_text(encoding="utf-8")
        data = toml.loads(content)

        source = str(file_path)

        # PEP 621 format (project.dependencies)
        if "project" in data:
            project = data["project"]

            # Regular dependencies
            for req in project.get("dependencies", []):
                dep = self._parse_requirement_line(req, source)
                if dep:
                    deps.append(dep)

            # Optional dependencies (extras)
            for extra, reqs in project.get("optional-dependencies", {}).items():
                is_dev = extra.lower() in ["dev", "test", "testing", "develop"]
                for req in reqs:
                    dep = self._parse_requirement_line(req, source)
                    if dep:
                        dep.is_optional = True
                        if is_dev:
                            dep.is_dev = True
                            dev_deps.append(dep)
                        else:
                            deps.append(dep)

        # Poetry format
        if "tool" in data and "poetry" in data["tool"]:
            poetry = data["tool"]["poetry"]

            for name, spec in poetry.get("dependencies", {}).items():
                if name.lower() == "python":
                    continue
                dep = self._poetry_dep_to_dependency(name, spec, source)
                deps.append(dep)

            for group_name, group in poetry.get("group", {}).items():
                is_dev = group_name.lower() in ["dev", "test"]
                for name, spec in group.get("dependencies", {}).items():
                    dep = self._poetry_dep_to_dependency(name, spec, source)
                    dep.is_dev = is_dev
                    if is_dev:
                        dev_deps.append(dep)
                    else:
                        deps.append(dep)

        return deps, dev_deps

    def _poetry_dep_to_dependency(
        self,
        name: str,
        spec: any,
        source: str
    ) -> Dependency:
        """Convert Poetry dependency spec to Dependency."""
        if isinstance(spec, str):
            version_spec = spec
            extras = []
        elif isinstance(spec, dict):
            version_spec = spec.get("version", "")
            extras = spec.get("extras", [])
        else:
            version_spec = ""
            extras = []

        # Convert Poetry version spec to pip format
        if version_spec.startswith("^"):
            # ^1.2.3 means >=1.2.3,<2.0.0 (approximately)
            version_spec = f">={version_spec[1:]}"
        elif version_spec.startswith("~"):
            # ~1.2.3 means >=1.2.3,<1.3.0
            version_spec = f">={version_spec[1:]}"

        return Dependency(
            name=name,
            version_spec=version_spec,
            extras=extras,
            source_file=source,
            package_manager="pip",
        )

    def _parse_package_json(
        self,
        file_path: Path
    ) -> tuple[list[Dependency], list[Dependency]]:
        """Parse package.json for npm dependencies."""
        import json

        deps = []
        dev_deps = []

        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)
        source = str(file_path)

        # Regular dependencies
        for name, version in data.get("dependencies", {}).items():
            deps.append(Dependency(
                name=name,
                version_spec=version,
                source_file=source,
                package_manager="npm",
            ))

        # Dev dependencies
        for name, version in data.get("devDependencies", {}).items():
            dev_deps.append(Dependency(
                name=name,
                version_spec=version,
                source_file=source,
                package_manager="npm",
                is_dev=True,
            ))

        return deps, dev_deps

    def _parse_cargo_toml(
        self,
        file_path: Path
    ) -> tuple[list[Dependency], list[Dependency]]:
        """Parse Cargo.toml for Rust dependencies."""
        deps = []
        dev_deps = []

        content = file_path.read_text(encoding="utf-8")
        data = toml.loads(content)
        source = str(file_path)

        # Regular dependencies
        for name, spec in data.get("dependencies", {}).items():
            if isinstance(spec, str):
                version = spec
            elif isinstance(spec, dict):
                version = spec.get("version", "")
            else:
                version = ""

            deps.append(Dependency(
                name=name,
                version_spec=version,
                source_file=source,
                package_manager="cargo",
            ))

        # Dev dependencies
        for name, spec in data.get("dev-dependencies", {}).items():
            if isinstance(spec, str):
                version = spec
            elif isinstance(spec, dict):
                version = spec.get("version", "")
            else:
                version = ""

            dev_deps.append(Dependency(
                name=name,
                version_spec=version,
                source_file=source,
                package_manager="cargo",
                is_dev=True,
            ))

        return deps, dev_deps

    def _parse_pipfile(
        self,
        file_path: Path
    ) -> tuple[list[Dependency], list[Dependency]]:
        """Parse Pipfile for dependencies."""
        deps = []
        dev_deps = []

        content = file_path.read_text(encoding="utf-8")
        data = toml.loads(content)
        source = str(file_path)

        # Regular packages
        for name, spec in data.get("packages", {}).items():
            if isinstance(spec, str):
                version = spec if spec != "*" else ""
            elif isinstance(spec, dict):
                version = spec.get("version", "").replace("==", "")
            else:
                version = ""

            deps.append(Dependency(
                name=name,
                version_spec=version,
                source_file=source,
                package_manager="pip",
            ))

        # Dev packages
        for name, spec in data.get("dev-packages", {}).items():
            if isinstance(spec, str):
                version = spec if spec != "*" else ""
            elif isinstance(spec, dict):
                version = spec.get("version", "").replace("==", "")
            else:
                version = ""

            dev_deps.append(Dependency(
                name=name,
                version_spec=version,
                source_file=source,
                package_manager="pip",
                is_dev=True,
            ))

        return deps, dev_deps

    def _deduplicate(self, deps: list[Dependency]) -> list[Dependency]:
        """Remove duplicate dependencies, keeping the most specific version."""
        seen: dict[str, Dependency] = {}

        for dep in deps:
            key = dep.normalized_name
            if key not in seen:
                seen[key] = dep
            else:
                # Keep the one with more specific version constraint
                existing = seen[key]
                if len(dep.version_spec) > len(existing.version_spec):
                    seen[key] = dep

        return list(seen.values())

    def _detect_conflicts(
        self,
        dependencies: list[Dependency]
    ) -> list[DependencyConflict]:
        """Detect version conflicts between dependencies."""
        conflicts = []

        # Group by normalized name
        by_name: dict[str, list[Dependency]] = {}
        for dep in dependencies:
            key = dep.normalized_name
            by_name.setdefault(key, []).append(dep)

        # Check each group
        for name, deps in by_name.items():
            if len(deps) <= 1:
                continue

            # Compare versions pairwise
            for i, dep_a in enumerate(deps):
                for dep_b in deps[i + 1:]:
                    if not self._versions_compatible(
                        dep_a.version_spec,
                        dep_b.version_spec
                    ):
                        conflicts.append(DependencyConflict(
                            package_name=name,
                            dep_a=dep_a,
                            dep_b=dep_b,
                            reason=f"Version specs may conflict: '{dep_a.version_spec}' vs '{dep_b.version_spec}'",
                            resolvable=True,
                        ))

        return conflicts

    def _versions_compatible(self, spec_a: str, spec_b: str) -> bool:
        """Check if two version specs are potentially compatible."""
        # Simple heuristic - proper resolution needs a SAT solver
        if not spec_a or not spec_b:
            return True  # No constraint = compatible

        # If specs are identical, they're compatible
        if spec_a == spec_b:
            return True

        # Check for obvious conflicts (e.g., ==1.0 vs ==2.0)
        if spec_a.startswith("==") and spec_b.startswith("=="):
            return spec_a == spec_b

        # Otherwise assume potentially compatible (needs real resolver)
        return True
