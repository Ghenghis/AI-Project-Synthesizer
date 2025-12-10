"""
AI Project Synthesizer - Unified Resolver

Orchestrates dependency resolution across multiple repositories.
Merges requirements and resolves conflicts using appropriate resolvers.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from src.resolution.python_resolver import PythonResolver, ResolutionResult, ResolvedPackage
from src.analysis.dependency_analyzer import DependencyAnalyzer, DependencyGraph

logger = logging.getLogger(__name__)


@dataclass
class UnifiedResolutionResult:
    """Result of unified dependency resolution."""
    
    success: bool
    packages: List[ResolvedPackage] = field(default_factory=list)
    requirements_txt: str = ""
    conflicts_resolved: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    resolution_time_ms: int = 0
    
    # Per-repository breakdown
    repository_deps: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "package_count": len(self.packages),
            "packages": [
                {"name": p.name, "version": p.version, "source": p.source}
                for p in self.packages
            ],
            "requirements_txt": self.requirements_txt,
            "conflicts_resolved": self.conflicts_resolved,
            "warnings": self.warnings,
            "resolution_time_ms": self.resolution_time_ms,
            "repository_breakdown": self.repository_deps,
        }


class UnifiedResolver:
    """
    Unified dependency resolver for multiple repositories.
    
    Workflow:
    1. Clone/access repositories
    2. Extract dependencies from each
    3. Merge and deduplicate
    4. Resolve conflicts with SAT solver
    5. Generate unified requirements
    
    Example:
        resolver = UnifiedResolver()
        result = await resolver.resolve(
            repository_urls=["https://github.com/user/repo1", ...],
            python_version="3.11",
        )
    """
    
    def __init__(self):
        """Initialize the unified resolver."""
        self.dep_analyzer = DependencyAnalyzer()
        self.python_resolver = PythonResolver()
    
    async def resolve(
        self,
        repository_urls: List[str],
        python_version: str = "3.11",
        additional_constraints: Optional[List[str]] = None,
    ) -> UnifiedResolutionResult:
        """
        Resolve dependencies from multiple repositories.
        
        Args:
            repository_urls: List of repository URLs
            python_version: Target Python version
            additional_constraints: Extra version constraints
            
        Returns:
            UnifiedResolutionResult with merged dependencies
        """
        import time
        start_time = time.time()
        
        result = UnifiedResolutionResult(success=False)
        all_requirements: List[str] = []
        seen_packages: Dict[str, List[str]] = {}  # package -> versions
        
        # Analyze each repository
        for repo_url in repository_urls:
            try:
                deps = await self._extract_dependencies(repo_url)
                result.repository_deps[repo_url] = len(deps)
                
                for dep in deps:
                    name = dep.lower().replace("_", "-")
                    # Extract just the package name for tracking
                    pkg_name = name.split("[")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0]
                    
                    if pkg_name not in seen_packages:
                        seen_packages[pkg_name] = []
                        all_requirements.append(dep)
                    else:
                        # Track multiple versions
                        seen_packages[pkg_name].append(dep)
                        
            except Exception as e:
                logger.warning(f"Failed to extract deps from {repo_url}: {e}")
                result.warnings.append(f"Failed to analyze {repo_url}: {e}")
        
        # Add additional constraints
        if additional_constraints:
            all_requirements.extend(additional_constraints)
        
        # Detect potential conflicts before resolution
        conflicts = await self.python_resolver.check_conflicts(all_requirements)
        if conflicts:
            result.warnings.extend(conflicts)
        
        # Resolve dependencies
        if all_requirements:
            resolution = await self.python_resolver.resolve(
                requirements=all_requirements,
                python_version=python_version,
            )
            
            result.success = resolution.success
            result.packages = resolution.packages
            result.requirements_txt = resolution.lockfile_content
            result.conflicts_resolved = resolution.conflicts
            result.warnings.extend(resolution.warnings)
        else:
            result.success = True
            result.requirements_txt = "# No dependencies found\n"
        
        result.resolution_time_ms = int((time.time() - start_time) * 1000)
        return result
    
    async def _extract_dependencies(
        self,
        repo_url: str,
    ) -> List[str]:
        """Extract dependencies from a repository."""
        # For URLs, we need to clone first
        if repo_url.startswith("http"):
            return await self._extract_from_url(repo_url)
        else:
            # Local path
            return await self._extract_from_path(Path(repo_url))
    
    async def _extract_from_url(self, repo_url: str) -> List[str]:
        """Extract dependencies from a remote repository."""
        from src.discovery.unified_search import UnifiedSearch
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "repo"
            
            # Clone repository
            search = UnifiedSearch()
            platform = search._detect_platform(repo_url)
            repo_id = search._extract_repo_id(repo_url, platform)
            
            client = search._clients.get(platform)
            if client:
                await client.clone(repo_id, temp_path, depth=1)
                return await self._extract_from_path(temp_path)
            else:
                logger.warning(f"No client for platform: {platform}")
                return []
    
    async def _extract_from_path(self, repo_path: Path) -> List[str]:
        """Extract dependencies from a local repository path."""
        graph = await self.dep_analyzer.analyze(repo_path)
        
        requirements = []
        for dep in graph.direct:
            if dep.version_spec:
                requirements.append(f"{dep.name}{dep.version_spec}")
            else:
                requirements.append(dep.name)
        
        return requirements
    
    async def resolve_from_graphs(
        self,
        dependency_graphs: List[DependencyGraph],
        python_version: str = "3.11",
    ) -> UnifiedResolutionResult:
        """
        Resolve from pre-analyzed dependency graphs.
        
        Args:
            dependency_graphs: List of analyzed DependencyGraph objects
            python_version: Target Python version
            
        Returns:
            UnifiedResolutionResult
        """
        all_requirements = []
        
        for graph in dependency_graphs:
            for dep in graph.direct:
                if dep.version_spec:
                    all_requirements.append(f"{dep.name}{dep.version_spec}")
                else:
                    all_requirements.append(dep.name)
        
        return await self.resolve(
            repository_urls=[],
            python_version=python_version,
            additional_constraints=all_requirements,
        )
    
    def generate_pyproject_toml(
        self,
        result: UnifiedResolutionResult,
        project_name: str,
        project_version: str = "0.1.0",
    ) -> str:
        """
        Generate pyproject.toml content from resolution.
        
        Args:
            result: Resolution result
            project_name: Project name
            project_version: Project version
            
        Returns:
            pyproject.toml content string
        """
        deps = []
        for pkg in result.packages:
            if pkg.extras:
                deps.append(f'"{pkg.name}[{",".join(pkg.extras)}]=={pkg.version}"')
            else:
                deps.append(f'"{pkg.name}=={pkg.version}"')
        
        deps_str = ",\n    ".join(deps)
        
        return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "{project_version}"
description = "Synthesized project"
readme = "README.md"
requires-python = ">={result.packages[0].version if result.packages else '3.11'}"
dependencies = [
    {deps_str}
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
'''
