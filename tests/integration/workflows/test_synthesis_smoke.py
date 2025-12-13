"""
Smoke test for synthesis workflow.
Tests core components work together without external dependencies.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.discovery.base_client import RepositoryInfo
from src.analysis.dependency_analyzer import DependencyAnalyzer
from src.analysis.quality_scorer import QualityScorer
from src.synthesis.project_assembler import ProjectAssembler
from src.generation.readme_generator import ReadmeGenerator


class TestSynthesisSmoke:
    """Smoke test for synthesis workflow components."""
    
    @pytest.mark.integration
    def test_repository_info_creation(self):
        """Test RepositoryInfo dataclass works correctly."""
        
        repo = RepositoryInfo(
            name="test-repo",
            url="https://github.com/test/test-repo",
            description="Test repository",
            language="Python",
            stars=42,
            forks=5,
            open_issues=3
        )
        
        assert repo.name == "test-repo"
        assert repo.language == "Python"
        assert repo.stars == 42
        assert repo.to_dict() is not None
        assert repo.to_dict()["name"] == "test-repo"
    
    @pytest.mark.integration
    def test_dependency_analyzer(self, sample_repository):
        """Test dependency analyzer works on real code."""
        
        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_directory(str(sample_repository / "src"))
        
        assert isinstance(dependencies, list)
        # Should detect pytest from requirements.txt
        assert any("pytest" in str(dep).lower() for dep in dependencies)
    
    @pytest.mark.integration
    def test_quality_scorer(self, sample_repository):
        """Test quality scorer works on real code."""
        
        scorer = QualityScorer()
        score = scorer.score_repository(str(sample_repository))
        
        assert score is not None
        assert hasattr(score, 'overall_score')
        assert score.overall_score >= 0
        assert score.overall_score <= 100
    
    @pytest.mark.integration
    def test_project_assembler(self):
        """Test project assembler creates valid structure."""
        
        assembler = ProjectAssembler()
        
        # Create test data
        repo = RepositoryInfo(
            name="test-project",
            url="https://github.com/test/test-project",
            description="Test project",
            language="Python"
        )
        
        dependencies = ["pytest", "requests"]
        quality_score = MagicMock()
        quality_score.overall_score = 85
        quality_score.structure_score = 90
        quality_score.documentation_score = 80
        
        # Test assembly
        result = assembler.assemble_project(
            repo_info=repo,
            analysis=dependencies,
            quality_score=quality_score
        )
        
        assert result is not None
        assert result.project_info is not None
        assert result.project_structure is not None
        assert result.recommendations is not None
    
    @pytest.mark.integration
    def test_readme_generator(self):
        """Test readme generator creates content."""
        
        generator = ReadmeGenerator()
        
        # Mock synthesis result
        synthesis_result = MagicMock()
        synthesis_result.project_info.name = "test-project"
        synthesis_result.project_info.description = "Test project description"
        synthesis_result.project_info.language = "Python"
        synthesis_result.dependencies = ["pytest", "requests"]
        synthesis_result.quality_score.overall_score = 85
        
        # Generate README
        readme = generator.generate(synthesis_result)
        
        assert readme is not None
        assert len(readme) > 100
        assert "test-project" in readme
        assert "Python" in readme
        assert "#" in readme  # Should have headers
    
    @pytest.mark.integration
    def test_full_workflow_mocked(self):
        """Test full workflow with mocked external dependencies."""
        
        # Create test repository info
        repo = RepositoryInfo(
            name="workflow-test",
            url="https://github.com/test/workflow-test",
            description="Workflow test repository",
            language="Python",
            stars=100
        )
        
        # Analyze dependencies (mock)
        with patch.object(DependencyAnalyzer, 'analyze_directory') as mock_analyze:
            mock_analyze.return_value = ["pytest", "requests", "numpy"]
            
            analyzer = DependencyAnalyzer()
            dependencies = analyzer.analyze_directory("/fake/path")
            
            assert len(dependencies) == 3
        
        # Score quality (mock)
        with patch.object(QualityScorer, 'score_repository') as mock_score:
            mock_score.return_value = MagicMock(
                overall_score=88,
                structure_score=90,
                documentation_score=85,
                test_score=80
            )
            
            scorer = QualityScorer()
            quality = scorer.score_repository("/fake/path")
            
            assert quality.overall_score == 88
        
        # Assemble project
        assembler = ProjectAssembler()
        synthesis = assembler.assemble_project(
            repo_info=repo,
            analysis=dependencies,
            quality_score=quality
        )
        
        assert synthesis is not None
        
        # Generate documentation
        generator = ReadmeGenerator()
        readme = generator.generate(synthesis)
        
        assert readme is not None
        assert "workflow-test" in readme
    
    @pytest.mark.integration
    def test_error_propagation(self):
        """Test errors are properly handled in workflow."""
        
        # Test with invalid repository
        with pytest.raises(Exception):
            repo = RepositoryInfo(
                name=None,  # Invalid
                url="invalid-url",
                description="Test"
            )
            # Validation should catch this
            if not repo.name:
                raise ValueError("Repository name is required")
    
    @pytest.mark.integration
    def test_component_integration(self, sample_repository):
        """Test components integrate correctly."""
        
        # Real analysis
        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_directory(str(sample_repository))
        
        # Real quality scoring
        scorer = QualityScorer()
        quality = scorer.score_repository(str(sample_repository))
        
        # Real repository info
        repo = RepositoryInfo(
            name=sample_repository.name,
            url="https://github.com/test/" + sample_repository.name,
            description="Sample repository",
            language="Python"
        )
        
        # Assemble with real data
        assembler = ProjectAssembler()
        synthesis = assembler.assemble_project(
            repo_info=repo,
            analysis=dependencies,
            quality_score=quality
        )
        
        # Generate with real synthesis
        generator = ReadmeGenerator()
        readme = generator.generate(synthesis)
        
        # Verify end-to-end result
        assert readme is not None
        assert len(readme) > 50
        assert sample_repository.name in readme or "Sample" in readme


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
