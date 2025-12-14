"""
AI Project Synthesizer - Project Builder Tests

Unit tests for the project synthesis and building functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.synthesis.project_builder import (
    BuildResult,
    ExtractionSpec,
    ProjectBuilder,
    SynthesisRequest,
    SynthesisResult,
    SynthesisStatus,
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
        """Create sample synthesis request with real repositories."""
        return SynthesisRequest(
            project_name="test-project",
            repositories=[
                ExtractionSpec(
                    repo_url="https://github.com/ghenghis/test/repo1",
                    components=["src"],
                    destination="src",
                    rename_map={},
                ),
                ExtractionSpec(
                    repo_url="https://github.com/ghenghis/test/repo2",
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
            repo_url="https://github.com/ghenghis/test/repo1",
            components=["src", "tests"],
            destination="output",
            rename_map={"old.py": "new.py"},
        )

        assert spec.repo_url == "https://github.com/ghenghis/test/repo1"
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

        with pytest.raises(
            ValueError, match="Either repositories or query must be provided"
        ):
            builder._validate_request(request)

    # ========================================
    # Synthesis Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_synthesize_success(self, builder, sample_request):
        """Test successful synthesis."""
        with (
            patch.object(builder, "_discover_repositories") as mock_discover,
            patch.object(builder, "_analyze_repositories") as mock_analyze,
            patch.object(builder, "_resolve_dependencies") as mock_resolve,
            patch.object(builder, "_synthesize_code") as mock_synthesize,
            patch.object(builder, "_write_dependencies") as mock_write_deps,
            patch.object(builder, "_generate_documentation") as mock_generate_docs,
            patch("pathlib.Path.mkdir"),
        ):
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
            assert result.files_generated > 0
            assert len(result.documentation_generated) > 0

    @pytest.mark.asyncio
    async def test_synthesize_with_error(self, builder, sample_request):
        """Test synthesis with error when validation fails."""
        # Create an invalid request to trigger failure
        invalid_request = SynthesisRequest(
            project_name="",  # Empty name triggers validation error
            repositories=[
                ExtractionSpec(
                    repo_url="https://github.com/ghenghis/test/repo1",
                    components=["src"],
                    destination="src",
                    rename_map={},
                ),
            ],
            output_path="/tmp/test-output",
            template="python-default",
            generate_docs=True,
        )

        result = await builder.synthesize(invalid_request)

        assert result.status == SynthesisStatus.FAILED
        assert len(result.errors) > 0

    # ========================================
    # Component Method Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_discover_repositories(self, builder):
        """Test repository discovery with mocked UnifiedSearch."""
        # Patch at the source module since import happens inside the method
        with patch("src.discovery.unified_search.UnifiedSearch") as mock_search_class:
            # Setup mock search
            mock_search = AsyncMock()
            mock_repo1 = MagicMock()
            mock_repo1.url = "https://github.com/ghenghis/test/repo1"
            mock_repo1.name = "repo1"
            mock_repo2 = MagicMock()
            mock_repo2.url = "https://github.com/ghenghis/test/repo2"
            mock_repo2.name = "repo2"

            mock_results = MagicMock()
            mock_results.repositories = [mock_repo1, mock_repo2]
            mock_search.search.return_value = mock_results
            mock_search_class.return_value = mock_search

            result = await builder._discover_repositories("machine learning")

            assert len(result) == 2
            assert result[0].repo_url == "https://github.com/ghenghis/test/repo1"
            assert result[1].repo_url == "https://github.com/ghenghis/test/repo2"
            mock_search.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_dependencies(self, builder):
        """Test dependency resolution with mocked PythonResolver."""
        # Patch at the source module since import happens inside the method
        with patch(
            "src.resolution.python_resolver.PythonResolver"
        ) as mock_resolver_class:
            # Setup mock resolver
            mock_resolver = AsyncMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.packages = ["fastapi==0.104.1", "pydantic==2.5.0"]
            mock_result.lockfile_content = "fastapi==0.104.1\npydantic==2.5.0\n"
            mock_resolver.resolve.return_value = mock_result
            mock_resolver_class.return_value = mock_resolver

            analyses = [{"dependencies": ["fastapi", "pydantic"]}]

            result = await builder._resolve_dependencies(analyses)

            assert result["success"] is True
            assert result["count"] == 2
            mock_resolver.resolve.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesize_code(self, builder):
        """Test code synthesis with real codebase files."""
        # Use real repository specs pointing to actual codebase
        repos = [
            ExtractionSpec(
                repo_url="https://github.com/ghenghis/test/repo1",
                components=["src"],
                destination="src",
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            # Mock the UnifiedSearch client clone operation
            with patch(
                "src.discovery.unified_search.UnifiedSearch"
            ) as mock_search_class:
                mock_search = MagicMock()
                mock_search._detect_platform.return_value = "github"
                mock_search._extract_repo_id.return_value = "ghenghis/test"
                mock_client = AsyncMock()
                mock_client.clone.return_value = None
                mock_search._clients = {"github": mock_client}
                mock_search_class.return_value = mock_search

                result = await builder._synthesize_code(
                    repos, output_path, "python-default"
                )

                assert "files" in result
                assert isinstance(result["files"], int)
                # Should have at least the __init__.py files created
                assert result["files"] >= 2

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
                repositories_used=["https://github.com/ghenghis/test/repo1"],
                dependencies_resolved=3,
                files_generated=5,
                documentation_generated=["README.md"],
            )
            mock_synthesize.return_value = mock_result

            repos = [
                {
                    "repo_url": "https://github.com/ghenghis/test/repo1",
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
                repositories_used=["https://github.com/ghenghis/test/repo1"],
                dependencies_resolved=1,
                documentation_generated=["README.md"],
            )
            mock_synthesize.return_value = mock_result

            repos = [
                ExtractionSpec(
                    repo_url="https://github.com/ghenghis/test/repo1",
                    components=["src"],
                    destination="src",
                )
            ]
            output_path = Path("/tmp/test-output")

            result = await builder.build(
                repositories=repos,
                project_name="test-project",
                output_path=output_path,
            )

            assert isinstance(result, BuildResult)
            assert result.repos_processed == 1
            mock_synthesize.assert_called_once()

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

            docs = await builder._generate_documentation(output_path)

            assert "README.md" in docs
            assert "docs/ARCHITECTURE.md" in docs

            # Check files were created
            assert (output_path / "README.md").exists()
            assert (output_path / "docs" / "ARCHITECTURE.md").exists()

            # Check content
            readme = (output_path / "README.md").read_text(encoding="utf-8")
            assert "Generated by AI Project Synthesizer" in readme

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
    async def test_full_synthesis_workflow(self, builder, sample_request):
        """Test complete synthesis workflow with mocked components."""
        with (
            patch.object(builder, "_analyze_repositories") as mock_analyze,
            patch.object(builder, "_resolve_dependencies") as mock_resolve,
            patch.object(builder, "_synthesize_code") as mock_synthesize,
            patch.object(builder, "_write_dependencies") as mock_write_deps,
            patch.object(builder, "_generate_documentation") as mock_generate_docs,
            patch("pathlib.Path.mkdir"),
        ):
            # Setup mocks - sample_request already has repositories, so _discover is skipped
            mock_analyze.return_value = [MagicMock()]
            mock_resolve.return_value = {
                "success": True,
                "count": 3,
                "packages": 3,
                "lockfile": "fastapi==0.104.1\npydantic==2.5.0\n",
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

            # Verify workflow methods were called (discover is skipped since repos provided)
            mock_analyze.assert_called_once()
            mock_resolve.assert_called_once()
            mock_synthesize.assert_called_once()
            mock_write_deps.assert_called_once()
            mock_generate_docs.assert_called_once()
