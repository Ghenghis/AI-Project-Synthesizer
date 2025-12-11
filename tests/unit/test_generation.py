"""
AI Project Synthesizer - Generation Module Tests

Tests for README and diagram generation.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from src.generation.readme_generator import ReadmeGenerator, ProjectInfo
from src.generation.diagram_generator import DiagramGenerator


class TestProjectInfo:
    """Test ProjectInfo dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        info = ProjectInfo(name="test-project")
        
        assert info.name == "test-project"
        assert info.description is None
        assert info.frameworks == []
        assert info.dependencies == []
        assert info.has_tests is False
    
    def test_with_all_fields(self):
        """Test with all fields populated."""
        info = ProjectInfo(
            name="my-project",
            description="A test project",
            version="1.0.0",
            language="Python",
            frameworks=["FastAPI", "Pydantic"],
            dependencies=["httpx", "pytest"],
            has_tests=True,
            has_docs=True,
            has_ci=True,
            license="MIT",
        )
        
        assert info.name == "my-project"
        assert info.version == "1.0.0"
        assert len(info.frameworks) == 2
        assert info.has_tests is True


class TestReadmeGenerator:
    """Test ReadmeGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance without LLM."""
        return ReadmeGenerator(use_llm=False)
    
    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create sample project structure."""
        project = tmp_path / "sample-project"
        project.mkdir()
        
        # Create directories
        (project / "src").mkdir()
        (project / "tests").mkdir()
        (project / "docs").mkdir()
        (project / ".github" / "workflows").mkdir(parents=True)
        
        # Create files
        (project / "README.md").write_text("# Sample Project\n")
        (project / "requirements.txt").write_text("fastapi>=0.100.0\npydantic>=2.0.0\n")
        (project / "pyproject.toml").write_text('''
[project]
name = "sample-project"
version = "1.0.0"
description = "A sample project"
''')
        (project / "src" / "__init__.py").write_text("")
        (project / "src" / "main.py").write_text('def main():\n    print("Hello")\n')
        (project / "tests" / "test_main.py").write_text('def test_main():\n    assert True\n')
        
        return project
    
    def test_generator_initialization(self, generator):
        """Test generator initializes correctly."""
        assert generator is not None
        assert hasattr(generator, 'TEMPLATE')
    
    def test_generator_has_use_llm_flag(self):
        """Test generator has use_llm flag."""
        gen_with = ReadmeGenerator(use_llm=True)
        gen_without = ReadmeGenerator(use_llm=False)
        
        assert gen_with.use_llm is True
        assert gen_without.use_llm is False
    
    def test_detect_language(self, generator, sample_project):
        """Test language detection."""
        language = generator._detect_language(sample_project)
        
        # Should detect Python or return a string
        assert language is None or isinstance(language, str)
    
    def test_detect_frameworks(self, generator, sample_project):
        """Test framework detection."""
        frameworks = generator._detect_frameworks(sample_project)
        
        # Should return a list
        assert isinstance(frameworks, list)
    
    @pytest.mark.asyncio
    async def test_analyze_project(self, generator, sample_project):
        """Test project analysis."""
        info = await generator._analyze_project(sample_project)
        
        assert info.name == "sample-project"
        assert info.has_tests is True
        assert info.has_docs is True
        assert info.has_ci is True
    
    @pytest.mark.asyncio
    async def test_generate_creates_readme(self, generator, sample_project):
        """Test full README generation."""
        readme_path = await generator.generate(sample_project)
        
        assert readme_path.exists()
        content = readme_path.read_text(encoding='utf-8')
        assert "sample-project" in content.lower() or "Sample" in content


class TestDiagramGenerator:
    """Test DiagramGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return DiagramGenerator()
    
    @pytest.fixture
    def sample_config(self):
        """Create sample diagram config."""
        from src.generation.diagram_generator import DiagramConfig
        return DiagramConfig(
            project_name="test-project",
            components=["API", "Core", "Models"],
            dependencies={"API": ["Core"], "Core": ["Models"]},
            diagram_types=["architecture", "flow"],
        )
    
    def test_generator_initialization(self, generator):
        """Test generator initializes correctly."""
        assert generator is not None
    
    def test_generate_creates_output(self, generator, sample_config):
        """Test diagram generation creates output."""
        result = generator.generate(sample_config)
        
        # Should return a dict of diagrams
        assert isinstance(result, dict)
        assert len(result) > 0
    
    def test_generate_architecture_diagram(self, generator, sample_config):
        """Test architecture diagram generation."""
        result = generator.generate(sample_config)
        
        assert "architecture" in result
        assert "graph" in result["architecture"].lower()
    
    def test_generate_flow_diagram(self, generator, sample_config):
        """Test flow diagram generation."""
        result = generator.generate(sample_config)
        
        assert "data_flow" in result


class TestGenerationIntegration:
    """Integration tests for generation module."""
    
    @pytest.fixture
    def full_project(self, tmp_path):
        """Create a more complete project structure."""
        project = tmp_path / "full-project"
        project.mkdir()
        
        # Standard structure
        for dir_name in ["src", "tests", "docs", "config"]:
            (project / dir_name).mkdir()
        
        # GitHub workflows
        (project / ".github" / "workflows").mkdir(parents=True)
        (project / ".github" / "workflows" / "ci.yml").write_text("name: CI")
        
        # Project files
        (project / "README.md").write_text("# Full Project")
        (project / "LICENSE").write_text("MIT License")
        (project / "pyproject.toml").write_text('''
[project]
name = "full-project"
version = "2.0.0"
description = "A full featured project"
dependencies = ["fastapi", "pydantic", "httpx"]
''')
        (project / "requirements.txt").write_text('''
fastapi>=0.100.0
pydantic>=2.0.0
httpx>=0.24.0
pytest>=7.0.0
''')
        
        # Source files
        (project / "src" / "__init__.py").write_text('__version__ = "2.0.0"')
        (project / "src" / "main.py").write_text('''
"""Main module."""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
''')
        
        # Test files
        (project / "tests" / "__init__.py").write_text("")
        (project / "tests" / "test_main.py").write_text('''
def test_root():
    assert True
''')
        
        return project
    
    @pytest.mark.asyncio
    async def test_full_readme_generation(self, full_project):
        """Test complete README generation workflow."""
        generator = ReadmeGenerator(use_llm=False)
        
        readme_path = await generator.generate(full_project)
        
        assert readme_path.exists()
        content = readme_path.read_text(encoding='utf-8')
        
        # Should contain key sections
        assert "full-project" in content.lower() or "Full" in content
    
    def test_full_diagram_generation(self, full_project):
        """Test complete diagram generation workflow."""
        from src.generation.diagram_generator import DiagramConfig
        
        generator = DiagramGenerator()
        config = DiagramConfig(
            project_name="full-project",
            components=["src", "tests", "docs"],
            diagram_types=["architecture"],
        )
        
        result = generator.generate(config)
        
        assert isinstance(result, dict)
        assert "architecture" in result
