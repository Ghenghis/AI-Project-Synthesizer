"""
AI Project Synthesizer - Compatibility Checker

Checks if multiple repositories can work together by analyzing
dependencies, Python versions, and system requirements.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from src.analysis.dependency_analyzer import DependencyAnalyzer, DependencyGraph

logger = logging.getLogger(__name__)


@dataclass
class RepositoryInfo:
    """Information about a repository for compatibility checking."""
    url: str
    name: str
    path: Optional[Path] = None
    python_version: Optional[str] = None
    languages: Dict[str, float] = field(default_factory=dict)
    dependencies: Optional[DependencyGraph] = None


@dataclass
class CompatibilityIssue:
    """Represents a compatibility issue between repositories."""
    severity: str  # "error", "warning", "info"
    category: str  # "dependency", "python_version", "language", "license"
    repos_involved: List[str]
    description: str
    suggestion: Optional[str] = None


@dataclass
class CompatibilityMatrix:
    """Complete compatibility analysis result."""
    repositories: List[str]
    overall_compatible: bool
    python_version: Optional[str]
    issues: List[CompatibilityIssue] = field(default_factory=list)
    shared_dependencies: List[str] = field(default_factory=list)
    all_dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "compatible": self.overall_compatible,
            "repositories": self.repositories,
            "python_version": self.python_version,
            "issue_count": len(self.issues),
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "repos": i.repos_involved,
                    "description": i.description,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
            "shared_dependencies": self.shared_dependencies,
            "total_dependencies": len(self.all_dependencies),
        }


class CompatibilityChecker:
    """
    Checks compatibility between multiple repositories.
    
    Analyzes:
    - Dependency conflicts
    - Python version requirements
    - Language compatibility
    - License compatibility
    
    Usage:
        checker = CompatibilityChecker()
        matrix = await checker.check([repo_a, repo_b, repo_c])
        if not matrix.overall_compatible:
            print(matrix.issues)
    """
    
    # Python version compatibility
    PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]
    
    # License compatibility matrix (simplified)
    LICENSE_COMPATIBILITY = {
        "MIT": ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Unlicense"],
        "Apache-2.0": ["Apache-2.0", "MIT", "BSD-3-Clause", "BSD-2-Clause", "ISC"],
        "GPL-3.0": ["GPL-3.0", "AGPL-3.0"],
        "LGPL-3.0": ["LGPL-3.0", "GPL-3.0", "MIT", "Apache-2.0"],
        "BSD-3-Clause": ["BSD-3-Clause", "BSD-2-Clause", "MIT", "Apache-2.0", "ISC"],
    }
    
    def __init__(self):
        """Initialize the compatibility checker."""
        self.dep_analyzer = DependencyAnalyzer()
    
    async def check(
        self,
        repositories: List[RepositoryInfo],
        target_python: str = "3.11"
    ) -> CompatibilityMatrix:
        """
        Check compatibility between repositories.
        
        Args:
            repositories: List of repository info objects
            target_python: Target Python version
            
        Returns:
            CompatibilityMatrix with analysis results
        """
        issues: List[CompatibilityIssue] = []
        all_deps: Set[str] = set()
        shared_deps: Set[str] = set()
        
        # Analyze each repository
        for repo in repositories:
            if repo.path and repo.dependencies is None:
                repo.dependencies = await self.dep_analyzer.analyze(repo.path)
        
        # Check Python version compatibility
        python_issues = self._check_python_versions(repositories, target_python)
        issues.extend(python_issues)
        
        # Check dependency conflicts
        dep_issues, all_deps, shared_deps = self._check_dependencies(repositories)
        issues.extend(dep_issues)
        
        # Check language compatibility
        lang_issues = self._check_languages(repositories)
        issues.extend(lang_issues)
        
        # Determine overall compatibility
        has_errors = any(i.severity == "error" for i in issues)
        
        return CompatibilityMatrix(
            repositories=[r.name for r in repositories],
            overall_compatible=not has_errors,
            python_version=target_python,
            issues=issues,
            shared_dependencies=list(shared_deps),
            all_dependencies=list(all_deps),
        )
    
    def _check_python_versions(
        self,
        repositories: List[RepositoryInfo],
        target_python: str
    ) -> List[CompatibilityIssue]:
        """Check Python version compatibility."""
        issues = []
        
        for repo in repositories:
            if repo.python_version:
                # Parse version requirement
                min_version = self._parse_python_requirement(repo.python_version)
                
                if min_version and self._version_less_than(target_python, min_version):
                    issues.append(CompatibilityIssue(
                        severity="warning",
                        category="python_version",
                        repos_involved=[repo.name],
                        description=f"{repo.name} requires Python {repo.python_version}, target is {target_python}",
                        suggestion=f"Consider using Python {min_version} or newer",
                    ))
        
        return issues
    
    def _check_dependencies(
        self,
        repositories: List[RepositoryInfo]
    ) -> tuple[List[CompatibilityIssue], Set[str], Set[str]]:
        """Check for dependency conflicts."""
        issues = []
        all_deps: Dict[str, Dict[str, str]] = {}  # package -> {repo -> version}
        
        # Collect all dependencies
        for repo in repositories:
            if repo.dependencies:
                for dep in repo.dependencies.all_dependencies:
                    name = dep.normalized_name
                    if name not in all_deps:
                        all_deps[name] = {}
                    all_deps[name][repo.name] = dep.version_spec
        
        # Find conflicts
        for pkg_name, repo_versions in all_deps.items():
            if len(repo_versions) > 1:
                versions = list(set(repo_versions.values()))
                if len(versions) > 1 and not self._versions_might_overlap(versions):
                    issues.append(CompatibilityIssue(
                        severity="error",
                        category="dependency",
                        repos_involved=list(repo_versions.keys()),
                        description=f"Conflicting versions of '{pkg_name}': {repo_versions}",
                        suggestion="Use dependency resolution to find compatible version",
                    ))
        
        # Calculate shared and all dependencies
        all_pkg_names = set(all_deps.keys())
        shared_pkg_names = {
            name for name, repos in all_deps.items()
            if len(repos) > 1
        }
        
        return issues, all_pkg_names, shared_pkg_names
    
    def _check_languages(
        self,
        repositories: List[RepositoryInfo]
    ) -> List[CompatibilityIssue]:
        """Check language compatibility."""
        issues = []
        
        primary_languages = {}
        for repo in repositories:
            if repo.languages:
                primary = max(repo.languages, key=repo.languages.get)
                primary_languages[repo.name] = primary
        
        # Check for mixed language projects
        unique_languages = set(primary_languages.values())
        if len(unique_languages) > 1:
            issues.append(CompatibilityIssue(
                severity="info",
                category="language",
                repos_involved=list(primary_languages.keys()),
                description=f"Mixed language project: {primary_languages}",
                suggestion="Ensure proper build tooling for multi-language projects",
            ))
        
        return issues
    
    def _parse_python_requirement(self, spec: str) -> Optional[str]:
        """Parse Python version requirement string."""
        import re
        
        # Match patterns like ">=3.8", "^3.9", "~3.10"
        match = re.search(r"[\d.]+", spec)
        if match:
            return match.group(0)
        return None
    
    def _version_less_than(self, v1: str, v2: str) -> bool:
        """Compare version strings."""
        def to_tuple(v: str) -> tuple:
            return tuple(int(x) for x in v.split("."))
        
        try:
            return to_tuple(v1) < to_tuple(v2)
        except (ValueError, AttributeError):
            return False
    
    def _versions_might_overlap(self, version_specs: List[str]) -> bool:
        """Check if version specs might have overlapping solutions."""
        # Simplified check - real implementation would use packaging library
        exact_versions = []
        for spec in version_specs:
            if spec.startswith("=="):
                exact_versions.append(spec[2:])
        
        # If multiple exact versions required, they must match
        if len(exact_versions) > 1:
            return len(set(exact_versions)) == 1
        
        return True  # Assume possible overlap without exact analysis
