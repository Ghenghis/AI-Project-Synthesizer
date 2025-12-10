"""
AI Project Synthesizer - Project Builder Tests

Unit tests for the project synthesis and building functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
from pathlib import Path
import time

from src.synthesis.project_builder import (
    ProjectBuilder,
    SynthesisRequest,
    SynthesisResult,
    SynthesisStatus,
    ExtractionSpec,
    BuildResult,
)


class TestProjectBuilder:
    """Test suite for ProjectBuilder."""
    
    @pytest.fixture
    def builder(self):
        """Create test builder instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ProjectBuilder(work_dir=Path(temp_dir))
    
    @pytest.fixture
    def sample_request(self):
        """Create sample synthesis request."""
        return SynthesisRequest(
            project_name="test-project",
            repositories=[
                ExtractionSpec(
                    repo_url="https://github.com/test/repo1",
                    components=["src"],
                    destination="src",
                    rename_map={},
                ),
                ExtractionSpec(
                    repo_url="https://github.com/test/repo2",
                    components=["lib"],
                    destination="lib",
                    rename_map={"old": "new"},
                ),
            ],
            output_path="/tmp/test-output",
            template="python-default",
            generate_docs=True,
        )
    
    # ========================================
    # Initialization Tests
    # ========================================
    
    def test_initialization(self, builder):
        """Test builder initialization."""
        assert builder.work_dir.exists()
        assert isinstance(builder._active_syntheses, dict)
        assert len(builder._active_syntheses) == 0
    
    # ========================================
    # Synthesis Request Tests
    # ========================================
    
    def test_synthesis_request_creation(self):
        """Test SynthesisRequest dataclass."""
        request = SynthesisRequest(
            project_name="test",
            repositories=[],
            output_path="/tmp/test",
        )
        
        assert request.project_name == "test"
        assert request.repositories == []
        assert request.output_path == "/tmp/test"
        assert request.template == "python-default"  # default value
        assert request.generate_docs is True  # default value
        assert request.id is not None  # auto-generated
    
    def test_extraction_spec_creation(self):
        """Test ExtractionSpec dataclass."""
        spec = ExtractionSpec(
            repo_url="https://github.com/test/repo",
            components=["src", "tests"],
            destination="output",
            rename_map={"old.py": "new.py"},
        )
        
        assert spec.repo_url == "https://github.com/test/repo"
        assert spec.components == ["src", "tests"]
        assert spec.destination == "output"
        assert spec.rename_map == {"old.py": "new.py"}
    
    # ========================================
    # Validation Tests
    # ========================================
    
    def test_validate_request_success(self, builder, sample_request):
        """Test successful request validation."""
        # Should not raise exception
        builder._validate_request(sample_request)
    
    def test_validate_request_missing_name(self, builder):
        """Test validation with missing project name."""
        request = SynthesisRequest(
            project_name="",  # Empty name
            repositories=[],
            output_path="/tmp/test",
        )
        
        with pytest.raises(ValueError, match="Project name is required"):
            builder._validate_request(request)
    
    def test_validate_request_no_repositories(self, builder):
        """Test validation with no repositories."""
        request = SynthesisRequest(
            project_name="test",
            repositories=[],
            output_path="/tmp/test",
        )
        
        with pytest.raises(ValueError, match="At least one repository is required"):
            builder._validate_request(request)
    
    # ========================================
    # Synthesis Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self, builder, sample_request):
        """Test successful synthesis."""
        with patch.object(builder, "_discover_repositories") as mock_discover, \
             patch.object(builder, "_analyze_repositories") as mock_analyze, \
             patch.object(builder, "_resolve_dependencies") as mock_resolve, \
             patch.object(builder, "_synthesize_code") as mock_synthesize, \
             patch.object(builder, "_write_dependencies") as mock_write_deps, \
             patch.object(builder, "_generate_documentation") as mock_generate_docs, \
             patch("pathlib.Path.mkdir"):
            
            # Mock return values
            mock_discover.return_value = []
            mock_analyze.return_value = []
            mock_resolve.return_value = {"lockfile": "fastapi==0.104.1\n"}
            mock_synthesize.return_value = {"files": 5}
            mock_write_deps.return_value = None
            mock_generate_docs.return_value = ["README.md"]
            
            result = await builder.synthesize(sample_request)
            
            assert result.status == SynthesisStatus.COMPLETE
            assert result.request_id == sample_request.id
            assert result.dependencies_resolved > 0
            assert result.files_generated > 0
            assert len(result.documentation_generated) > 0
    
    @pytest.mark.asyncio
    async def test_synthesize_with_error(self, builder, sample_request):
        """Test synthesis with error."""
        with patch.object(builder, "_discover_repositories") as mock_discover:
            mock_discover.side_effect = Exception("Discovery failed")
            
            result = await builder.synthesize(sample_request)
            
            assert result.status == SynthesisStatus.FAILED
            assert len(result.errors) > 0
            assert "Discovery failed" in result.errors[0]
    
    # ========================================
    # Component Method Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_discover_repositories(self, builder):
        """Test repository discovery."""
        with patch("src.discovery.unified_search.UnifiedSearch") as mock_search_class:
            mock_search = AsyncMock()
            mock_search_class.return_value = mock_search
            
            repos = [
                ExtractionSpec(repo_url="https://github.com/test/repo1"),
                ExtractionSpec(repo_url="https://github.com/test/repo2"),
            ]
            
            result = await builder._discover_repositories(repos)
            
            assert len(result) == 2
            mock_search.get_repository.assert_called()
    
    @pytest.mark.asyncio
    async def test_resolve_dependencies(self, builder):
        """Test dependency resolution."""
        with patch("src.resolution.unified_resolver.UnifiedResolver") as mock_resolver_class:
            mock_resolver = AsyncMock()
            mock_resolver.resolve.return_value = {
                "success": True,
                "packages": 5,
                "lockfile": "fastapi==0.104.1\npydantic==2.5.0\n"
            }
            mock_resolver_class.return_value = mock_resolver
            
            repos = [MagicMock(url="https://github.com/test/repo")]
            
            result = await builder._resolve_dependencies(repos, "3.11")
            
            assert result["success"] is True
            assert result["packages"] == 5
    
    @pytest.mark.asyncio
    async def test_synthesize_code(self, builder):
        """Test code synthesis."""
        with patch("src.discovery.unified_search.UnifiedSearch") as mock_search_class, \
             patch("src.analysis.code_extractor.CodeExtractor") as mock_extractor_class, \
             patch("shutil.copytree"), \
             patch("shutil.copy2"), \
             patch("tempfile.TemporaryDirectory") as mock_temp:
            
            # Mock search
            mock_search = AsyncMock()
            mock_search._detect_platform.return_value = "github"
            mock_search._extract_repo_id.return_value = "test/repo"
            mock_search._clients.get.return_value = AsyncMock()
            mock_search_class.return_value = mock_search
            
            # Mock temp directory
            temp_dir = Path("/tmp/test")
            mock_temp.return_value.__enter__.return_value = str(temp_dir)
            
            # Mock extractor
            mock_extractor = AsyncMock()
            mock_extractor_class.return_value = mock_extractor
            
            repos = [
                ExtractionSpec(
                    repo_url="https://github.com/test/repo",
                    components=["src"],
                )
            ]
            output_path = Path("/tmp/output")
            
            result = await builder._synthesize_code(repos, output_path, "python-default")
            
            assert "files" in result
            assert isinstance(result["files"], int)
    
    # ========================================
    # Build Method Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_build_method_with_dicts(self, builder):
        """Test build method with dictionary repository configs."""
        with patch.object(builder, "synthesize") as mock_synthesize:
            mock_result = SynthesisResult(
                request_id="test-id",
                status=SynthesisStatus.COMPLETE,
                repositories_used=["https://github.com/test/repo"],
                dependencies_resolved=3,
                files_generated=5,
                documentation_generated=["README.md"],
            )
            mock_synthesize.return_value = mock_result
            
            repos = [
                {
                    "repo_url": "https://github.com/test/repo",
                    "components": ["src"],
                    "destination": "src",
                    "rename_map": {},
                }
            ]
            output_path = Path("/tmp/test-output")
            
            result = await builder.build(
                repositories=repos,
                project_name="test-project",
                output_path=output_path,
                template="python-default",
            )
            
            assert isinstance(result, BuildResult)
            assert result.project_path == output_path
            assert result.repos_processed == 1
            assert result.files_created == 5
            assert result.deps_merged == 3
            assert len(result.docs_generated) > 0
    
    @pytest.mark.asyncio
    async def test_build_method_with_extraction_specs(self, builder):
        """Test build method with ExtractionSpec objects."""
        with patch.object(builder, "synthesize") as mock_synthesize:
            mock_result = SynthesisResult(
                request_id="test-id",
                status=SynthesisStatus.COMPLETE,
                files_generated=2,
            )
            mock_synthesize.return_value = mock_result
            
            repos = [
                ExtractionSpec(repo_url="https://github.com/test/repo")
            ]
            output_path = Path("/tmp/test-output")
            
            result = await builder.build(
                repositories=repos,
                project_name="test-project",
                output_path=output_path,
            )
            
            assert isinstance(result, BuildResult)
            assert result.repos_processed == 1
    
    # ========================================
    # Status Management Tests
    # ========================================
    
    def test_get_status_existing(self, builder):
        """Test getting status of existing synthesis."""
        # Create a synthesis result
        result = SynthesisResult(
            request_id="test-id",
            status=SynthesisStatus.COMPLETE,
        )
        builder._active_syntheses["test-id"] = result
        
        # Get status
        status = builder.get_status("test-id")
        
        assert status is not None
        assert status.request_id == "test-id"
        assert status.status == SynthesisStatus.COMPLETE
    
    def test_get_status_nonexistent(self, builder):
        """Test getting status of non-existent synthesis."""
        status = builder.get_status("nonexistent-id")
        assert status is None
    
    def test_list_active_empty(self, builder):
        """Test listing active syntheses when none exist."""
        active = builder.list_active()
        assert len(active) == 0
    
    def test_list_active_with_syntheses(self, builder):
        """Test listing active syntheses."""
        # Add some syntheses
        result1 = SynthesisResult(
            request_id="test-1",
            status=SynthesisStatus.SYNTHESIZING,
        )
        result2 = SynthesisResult(
            request_id="test-2",
            status=SynthesisStatus.COMPLETE,
        )
        result3 = SynthesisResult(
            request_id="test-3",
            status=SynthesisStatus.FAILED,
        )
        
        builder._active_syntheses["test-1"] = result1
        builder._active_syntheses["test-2"] = result2
        builder._active_syntheses["test-3"] = result3
        
        # List active (should only include non-complete/failed)
        active = builder.list_active()
        
        assert len(active) == 1
        assert active[0]["request_id"] == "test-1"
    
    # ========================================
    # Documentation Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_generate_documentation(self, builder):
        """Test documentation generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            output_path.mkdir(exist_ok=True)
            
            docs = await builder._generate_documentation(output_path)
            
            assert "README.md" in docs
            assert "docs/ARCHITECTURE.md" in docs
            
            # Check files were created
            assert (output_path / "README.md").exists()
            assert (output_path / "docs" / "ARCHITECTURE.md").exists()
            
            # Check content
            readme = (output_path / "README.md").read_text(encoding='utf-8')
            assert "Generated by AI Project Synthesizer" in readme
            assert "test-project" in readme
    
    def test_generate_readme(self, builder):
        """Test README generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            readme = builder._generate_readme(project_path)
            
            assert "# test-project" in readme
            assert "Generated by AI Project Synthesizer" in readme
            assert "Installation" in readme
            assert "Usage" in readme
            assert "Project Structure" in readme
    
    # ========================================
    # Integration Tests
    # ========================================
    
    @pytest.mark.asyncio
    async def test_full_synthesis_workflow(self, builder):
        """Test complete synthesis workflow with mocked components."""
        with patch.object(builder, "_discover_repositories") as mock_discover, \
             patch.object(builder, "_analyze_repositories") as mock_analyze, \
             patch.object(builder, "_resolve_dependencies") as mock_resolve, \
             patch.object(builder, "_synthesize_code") as mock_synthesize, \
             patch.object(builder, "_write_dependencies") as mock_write_deps, \
             patch.object(builder, "_generate_documentation") as mock_generate_docs, \
             patch("pathlib.Path.mkdir"):
            
            # Setup mocks
            mock_discover.return_value = [MagicMock()]
            mock_analyze.return_value = [MagicMock()]
            mock_resolve.return_value = {
                "success": True,
                "packages": 3,
                "lockfile": "fastapi==0.104.1\npydantic==2.5.0\n"
            }
            mock_synthesize.return_value = {"files": 5}
            mock_write_deps.return_value = None
            mock_generate_docs.return_value = ["README.md", "docs/ARCHITECTURE.md"]
            
            # Run synthesis
            result = await builder.synthesize(sample_request)
            
            # Verify results
            assert result.status == SynthesisStatus.COMPLETE
            assert result.request_id == sample_request.id
            assert len(result.repositories_used) > 0
            assert result.dependencies_resolved == 3
            assert result.files_generated == 5
            assert len(result.documentation_generated) == 2
            assert result.duration_seconds > 0
            
            # Verify all methods were called
            mock_discover.assert_called_once()
            mock_analyze.assert_called_once()
            mock_resolve.assert_called_once()
            mock_synthesize.assert_called_once()
            mock_write_deps.assert_called_once()
            mock_generate_docs.assert_called_once()
