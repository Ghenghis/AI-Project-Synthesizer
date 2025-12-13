"""
Unit tests for analysis dependency analyzer module.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.analysis.dependency_analyzer import (
    DependencyAnalyzer,
    Dependency,
    DependencyGraph,
)


class TestDependency:
    """Test Dependency dataclass."""
    
    def test_create_dependency(self):
        """Should create dependency."""
        dep = Dependency(
            name="requests",
            version_spec=">=2.0.0"
        )
        assert dep.name == "requests"
        assert dep.version_spec == ">=2.0.0"


class TestDependencyGraph:
    """Test DependencyGraph class."""
    
    def test_create_graph(self):
        """Should create dependency graph."""
        graph = DependencyGraph()
        assert graph is not None
    
    def test_graph_has_attributes(self):
        """Should have dependency lists."""
        graph = DependencyGraph()
        assert hasattr(graph, 'direct')
        assert hasattr(graph, 'transitive')


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer functionality."""
    
    def test_create_analyzer(self):
        """Should create dependency analyzer instance."""
        analyzer = DependencyAnalyzer()
        assert analyzer is not None
    
    def test_analyzer_has_analyze_method(self):
        """Should have analyze method."""
        analyzer = DependencyAnalyzer()
        assert hasattr(analyzer, 'analyze')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
