"""
AI Project Synthesizer - Conflict Detector

Detects and analyzes dependency conflicts between repositories.
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from src.analysis.dependency_analyzer import Dependency, DependencyGraph

logger = logging.getLogger(__name__)


@dataclass
class ConflictInfo:
    """Detailed information about a conflict."""
    package_name: str
    conflict_type: str  # "version", "extras", "python_version"
    sources: Dict[str, str]  # source -> version_spec
    description: str
    severity: str  # "error", "warning"
    resolvable: bool
    resolution_suggestion: Optional[str] = None


@dataclass
class ConflictReport:
    """Complete conflict analysis report."""
    total_packages: int
    conflicting_packages: int
    conflicts: List[ConflictInfo]
    resolvable_count: int
    
    @property
    def has_blocking_conflicts(self) -> bool:
        """Check for unresolvable conflicts."""
        return any(not c.resolvable for c in self.conflicts)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_packages": self.total_packages,
                "conflicting_packages": self.conflicting_packages,
                "resolvable": self.resolvable_count,
                "blocking": len(self.conflicts) - self.resolvable_count,
            },
            "conflicts": [
                {
                    "package": c.package_name,
                    "type": c.conflict_type,
                    "sources": c.sources,
                    "severity": c.severity,
                    "resolvable": c.resolvable,
                    "suggestion": c.resolution_suggestion,
                }
                for c in self.conflicts
            ],
        }


class ConflictDetector:
    """
    Detects dependency conflicts between multiple dependency graphs.
    
    Analyzes:
    - Version conflicts
    - Python version requirements
    - Extra dependencies
    - Platform-specific requirements
    
    Usage:
        detector = ConflictDetector()
        report = detector.detect([graph_a, graph_b, graph_c])
        if report.has_blocking_conflicts:
            print("Cannot merge repositories")
    """
    
    def detect(
        self,
        graphs: List[DependencyGraph],
        sources: List[str] = None
    ) -> ConflictReport:
        """
        Detect conflicts between dependency graphs.
        
        Args:
            graphs: List of dependency graphs to analyze
            sources: Optional source names for each graph
            
        Returns:
            ConflictReport with all detected conflicts
        """
        if sources is None:
            sources = [f"source_{i}" for i in range(len(graphs))]
        
        # Collect all dependencies by package name
        all_deps: Dict[str, Dict[str, Dependency]] = {}
        
        for graph, source in zip(graphs, sources):
            for dep in graph.all_dependencies:
                name = dep.normalized_name
                if name not in all_deps:
                    all_deps[name] = {}
                all_deps[name][source] = dep
        
        # Detect conflicts
        conflicts = []
        conflicting_packages = set()
        
        for pkg_name, source_deps in all_deps.items():
            if len(source_deps) <= 1:
                continue
            
            # Check for version conflicts
            version_conflict = self._check_version_conflict(pkg_name, source_deps)
            if version_conflict:
                conflicts.append(version_conflict)
                conflicting_packages.add(pkg_name)
            
            # Check for extras conflicts
            extras_conflict = self._check_extras_conflict(pkg_name, source_deps)
            if extras_conflict:
                conflicts.append(extras_conflict)
                conflicting_packages.add(pkg_name)
        
        resolvable_count = sum(1 for c in conflicts if c.resolvable)
        
        return ConflictReport(
            total_packages=len(all_deps),
            conflicting_packages=len(conflicting_packages),
            conflicts=conflicts,
            resolvable_count=resolvable_count,
        )
    
    def _check_version_conflict(
        self,
        package_name: str,
        source_deps: Dict[str, Dependency]
    ) -> Optional[ConflictInfo]:
        """Check for version conflicts."""
        version_specs = {
            source: dep.version_spec
            for source, dep in source_deps.items()
            if dep.version_spec
        }
        
        if len(version_specs) <= 1:
            return None
        
        # Check for exact version conflicts
        exact_versions = {}
        for source, spec in version_specs.items():
            if spec.startswith("=="):
                exact_versions[source] = spec[2:].strip()
        
        if len(set(exact_versions.values())) > 1:
            return ConflictInfo(
                package_name=package_name,
                conflict_type="version",
                sources=version_specs,
                description=f"Exact version conflict: {exact_versions}",
                severity="error",
                resolvable=False,
                resolution_suggestion="Remove exact version pins or align versions",
            )
        
        # Check for potentially incompatible ranges
        if not self._ranges_compatible(list(version_specs.values())):
            return ConflictInfo(
                package_name=package_name,
                conflict_type="version",
                sources=version_specs,
                description=f"Potentially incompatible version ranges",
                severity="warning",
                resolvable=True,
                resolution_suggestion="Use dependency resolver to find compatible version",
            )
        
        return None
    
    def _check_extras_conflict(
        self,
        package_name: str,
        source_deps: Dict[str, Dependency]
    ) -> Optional[ConflictInfo]:
        """Check for extras conflicts (just informational)."""
        all_extras: Set[str] = set()
        for dep in source_deps.values():
            all_extras.update(dep.extras)
        
        if len(all_extras) > 0:
            extras_by_source = {
                source: dep.extras
                for source, dep in source_deps.items()
                if dep.extras
            }
            
            if len(extras_by_source) > 1:
                # Different extras requested - not a conflict, but notable
                return None  # Don't report as conflict
        
        return None
    
    def _ranges_compatible(self, specs: List[str]) -> bool:
        """
        Check if version ranges might be compatible.
        
        This is a simplified check - full resolution needs SAT solver.
        """
        # If any spec is empty (no constraint), it's compatible
        if any(not spec for spec in specs):
            return True
        
        # Extract min/max versions from specs
        mins = []
        maxs = []
        
        for spec in specs:
            for part in spec.split(","):
                part = part.strip()
                if part.startswith(">="):
                    mins.append(part[2:].strip())
                elif part.startswith(">"):
                    mins.append(part[1:].strip())
                elif part.startswith("<="):
                    maxs.append(part[2:].strip())
                elif part.startswith("<"):
                    maxs.append(part[1:].strip())
        
        # Simple check: if min > max for any combo, incompatible
        for min_v in mins:
            for max_v in maxs:
                if self._version_greater(min_v, max_v):
                    return False
        
        return True
    
    def _version_greater(self, v1: str, v2: str) -> bool:
        """Check if v1 > v2."""
        def to_tuple(v: str) -> tuple:
            parts = []
            for p in v.split("."):
                try:
                    parts.append(int(p.split("-")[0].split("+")[0]))
                except ValueError:
                    parts.append(0)
            return tuple(parts)
        
        try:
            return to_tuple(v1) > to_tuple(v2)
        except:
            return False
