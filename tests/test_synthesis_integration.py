"""
Integration test for project synthesis functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_synthesize_project_from_idea():
    """Test synthesizing a project from an idea."""
    # Import inside the test to handle ImportError gracefully
    try:
        from src.mcp_server.tools import handle_synthesize_from_idea
    except ImportError:
        # Skip test if handler doesn't exist yet
        pytest.skip("handle_synthesize_from_idea not implemented yet")
    
    # Mock the ProjectAssembler
    with patch('src.synthesis.project_assembler.ProjectAssembler') as mock_assembler_class:
        mock_assembler = AsyncMock()
        mock_assembler_class.return_value = mock_assembler
        
        # Mock the assembled project
        mock_project = MagicMock()
        mock_project.name = "test-web-scraper"
        mock_project.slug = "test-web-scraper"
        mock_project.description = "A web scraping project"
        mock_project.base_path = Path("/tmp/test-project")
        mock_project.github_repo_url = "https://github.com/test/test-web-scraper"
        mock_project.github_repo_created = True
        mock_project.ready_for_windsurf = True
        
        mock_assembler.assemble.return_value = mock_project
        
        # Call the handler
        result = await handle_synthesize_from_idea({
            "idea": "Create a web scraper using BeautifulSoup and requests",
            "name": "Test Web Scraper",
            "output_dir": "/tmp",
            "create_github": False
        })
        
        # Verify response
        assert result["success"] is True
        assert result["project"]["name"] == "test-web-scraper"
        assert result["project"]["ready_for_windsurf"] is True
        
        # Verify assembler was called correctly
        mock_assembler.assemble.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_specific_repos():
    """Test synthesizing a project from specific repositories."""
    # Skip this test as specific repo synthesis is not yet implemented
    pytest.skip("Specific repository synthesis not yet implemented")


@pytest.mark.asyncio
async def test_project_assembler_integration():
    """Test the actual ProjectAssembler with mocked downloads."""
    from src.synthesis.project_assembler import ProjectAssembler, AssemblerConfig
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config = AssemblerConfig(
            base_output_dir=Path(temp_dir),
            create_github_repo=False,  # Skip GitHub for testing
            download_code=False,  # Skip actual downloads
        )
        
        assembler = ProjectAssembler(config)
        
        # Mock the search to avoid real API calls
        with patch.object(assembler, '_search_resources') as mock_search:
            # Mock search results
            mock_search.return_value = None
            
            # Assemble a project
            project = await assembler.assemble(
                idea="Test project for integration testing",
                name="Test Project"
            )
            
            # Verify project was created
            assert project.name == "Test Project"
            assert project.slug == "test-project"
            assert project.base_path.exists()
            assert (project.base_path / "README.md").exists()
            assert (project.base_path / ".gitignore").exists()


@pytest.mark.asyncio
async def test_requirements_merging():
    """Test merging requirements from multiple sources."""
    from src.synthesis.project_assembler import ProjectAssembler, AssemblerConfig
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = AssemblerConfig(
            base_output_dir=Path(temp_dir),
            create_github_repo=False,
            download_code=False,
        )
        
        assembler = ProjectAssembler(config)
        
        # Create mock project with repos
        from src.synthesis.project_assembler import AssembledProject, ProjectResource
        
        repo1 = ProjectResource(
            name="repo1",
            source="github",
            url="https://github.com/example/repo1",
            resource_type="code",
            download_path=Path(temp_dir) / "repo1"
        )
        
        repo2 = ProjectResource(
            name="repo2", 
            source="github",
            url="https://github.com/example/repo2",
            resource_type="code",
            download_path=Path(temp_dir) / "repo2"
        )
        
        project = AssembledProject(
            name="Test",
            slug="test",
            description="Test project",
            base_path=Path(temp_dir),
            code_repos=[repo1, repo2]
        )
        
        # Collect requirements
        requirements = await assembler._collect_requirements(project)
        
        # Verify common requirements are included
        assert "torch>=2.0.0" in requirements
        assert "datasets>=2.0.0" in requirements
        assert "numpy>=1.24.0" in requirements
        assert len(requirements) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
