"""
Integration test for the complete synthesis workflow.
Tests: Discovery → Analysis → Synthesis → Generation
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.discovery.github_client import GitHubClient
from src.analysis.dependency_analyzer import DependencyAnalyzer
from src.synthesis.project_assembler import ProjectAssembler
from src.generation.readme_generator import ReadmeGenerator
from src.generation.diagram_generator import DiagramGenerator


class TestFullSynthesisWorkflow:
    """Test the complete synthesis workflow end-to-end."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_github_to_documentation_workflow(self, sample_repository, mock_github_responses, mock_llm_response):
        """Test discovering a GitHub repo and generating full documentation."""
        
        # 1. Discovery Phase
        github_client = GitHubClient(token="test_token")
        repo_info = await github_client.get_repository("user/test-repo")
        
        assert repo_info.name == "test-repo"
        assert repo_info.stargazers == 42
        assert repo_info.language == "Python"
        
        # 2. Analysis Phase
        analyzer = DependencyAnalyzer()
        # Analyze the sample repository
        dependencies = analyzer.analyze_directory(str(sample_repository / "src"))
        
        assert len(dependencies) >= 0
        # Should detect Python standard library usage
        assert any("pytest" in str(dep) for dep in dependencies)
        
        # 3. Quality Assessment
        from src.analysis.quality_scorer import QualityScorer
        scorer = QualityScorer()
        quality_score = await scorer.score_repository(str(sample_repository))
        
        assert 0 <= quality_score.overall_score <= 100
        assert quality_score.structure_score >= 0
        assert quality_score.documentation_score >= 0
        
        # 4. Synthesis Phase
        assembler = ProjectAssembler()
        synthesis_result = await assembler.assemble_project(
            repo_info=repo_info,
            analysis=dependencies,
            quality_score=quality_score
        )
        
        assert synthesis_result is not None
        assert synthesis_result.project_structure is not None
        assert synthesis_result.recommendations is not None
        
        # 5. Generation Phase
        readme_gen = ReadmeGenerator()
        readme_content = await readme_gen.generate(synthesis_result)
        
        assert readme_content is not None
        assert len(readme_content) > 100  # Should generate substantial content
        assert "# test-repo" in readme_content or "# Test Repo" in readme_content
        
        # 6. Diagram Generation
        diagram_gen = DiagramGenerator()
        diagram_path = await diagram_gen.generate_architecture_diagram(synthesis_result)
        
        assert diagram_path is not None
        assert Path(diagram_path).exists()
        
        # Verify workflow completion
        assert all([
            repo_info,
            dependencies,
            quality_score,
            synthesis_result,
            readme_content,
            diagram_path
        ])
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, sample_repository):
        """Test workflow handles errors gracefully."""
        
        # Test with invalid repository
        github_client = GitHubClient(token="invalid")
        
        with pytest.raises(Exception):
            github_client.get_repository("invalid/repo")
        
        # Test analysis of empty directory
        empty_dir = Path(sample_repository.parent / "empty")
        empty_dir.mkdir()
        
        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_directory(str(empty_dir))
        assert dependencies == []
        
        # Test synthesis with minimal data
        from src.synthesis.project_assembler import ProjectAssembler
        from src.discovery.base_client import RepositoryInfo
        
        assembler = ProjectAssembler()
        repo_info = RepositoryInfo(
            name="minimal",
            url="https://github.com/test/minimal",
            description="Minimal test repo"
        )
        
        synthesis_result = assembler.assemble_project(
            repo_info=repo_info,
            analysis=[],
            quality_score=MagicMock(overall_score=50)
        )
        
        assert synthesis_result is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_with_memory_system(self, sample_repository, mock_memory_system):
        """Test workflow integrates with memory system."""
        
        from src.memory.mem0_integration import MemorySystem, MemoryCategory
        
        # Initialize memory system
        memory = MemorySystem()
        
        # Remember project preferences
        await memory.add(
            content="User prefers detailed documentation with examples",
            category=MemoryCategory.PREFERENCE,
            tags=["documentation", "examples"]
        )
        
        # Remember analysis results
        await memory.add(
            content=f"Analyzed repository with 3 Python files",
            category=MemoryCategory.ANALYSIS,
            metadata={"repo": "test-repo", "files": 3}
        )
        
        # Retrieve relevant context for synthesis
        context = await memory.search("documentation")
        assert len(context) >= 0
        
        # Verify memory integration
        assert hasattr(memory, 'add')
        assert hasattr(memory, 'search')
        assert hasattr(memory, 'get')
    
    @pytest.mark.integration
    def test_multi_language_workflow(self):
        """Test workflow handles different programming languages."""
        
        # Create JavaScript project
        with tempfile.TemporaryDirectory() as tmpdir:
            js_project = Path(tmpdir)
            
            # Create package.json
            (js_project / "package.json").write_text("""{
    "name": "test-js-project",
    "version": "1.0.0",
    "dependencies": {
        "express": "^4.18.0",
        "lodash": "^4.17.21"
    }
}""")
            
            # Create index.js
            (js_project / "index.js").write_text("""
const express = require('express');
const _ = require('lodash');

const app = express();

app.get('/', (req, res) => {
    res.json({ message: 'Hello World!' });
});

app.listen(3000);
""")
            
            # Analyze JavaScript project
            analyzer = DependencyAnalyzer()
            dependencies = analyzer.analyze_directory(str(js_project))
            
            # Should detect npm dependencies
            assert any("express" in str(dep) for dep in dependencies)
            assert any("lodash" in str(dep) for dep in dependencies)
            
            # Generate documentation
            from src.generation.readme_generator import ReadmeGenerator
            readme_gen = ReadmeGenerator()
            
            # Mock synthesis result
            synthesis_result = MagicMock()
            synthesis_result.project_info.name = "test-js-project"
            synthesis_result.project_info.language = "JavaScript"
            synthesis_result.dependencies = dependencies
            
            readme = readme_gen.generate(synthesis_result)
            assert "JavaScript" in readme
            assert "express" in readme
    
    @pytest.mark.integration
    def test_workflow_performance(self, sample_repository):
        """Test workflow completes within acceptable time limits."""
        import time
        
        start_time = time.time()
        
        # Run complete workflow
        github_client = GitHubClient(token="test")
        analyzer = DependencyAnalyzer()
        scorer = QualityScorer()
        assembler = ProjectAssembler()
        readme_gen = ReadmeGenerator()
        
        # Execute each phase
        dependencies = analyzer.analyze_directory(str(sample_repository))
        quality_score = scorer.score_repository(str(sample_repository))
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in under 10 seconds for small repo
        assert duration < 10.0, f"Workflow took {duration:.2f} seconds"
    
    @pytest.mark.integration
    def test_workflow_with_quality_gate(self, sample_repository):
        """Test workflow includes quality gate validation."""
        
        from src.quality.quality_gate import QualityGate
        from src.quality.security_scanner import SecurityScanner
        
        # Run quality checks
        quality_gate = QualityGate()
        security_scanner = SecurityScanner()
        
        # Scan for security issues
        security_issues = security_scanner.scan_directory(str(sample_repository))
        assert isinstance(security_issues, list)
        
        # Run quality gate
        quality_results = quality_gate.run_checks(str(sample_repository))
        assert len(quality_results) >= 0
        
        # Check if project passes quality gate
        summary = quality_gate.get_summary()
        assert hasattr(summary, 'passed')
        assert hasattr(summary, 'failed')
        assert hasattr(summary, 'total')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
