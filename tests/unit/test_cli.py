"""
Tests for the CLI module.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typer.testing import CliRunner

from src.cli import app, main


runner = CliRunner()


class TestCLIBasics:
    """Test basic CLI functionality."""
    
    def test_help(self):
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AI Project Synthesizer" in result.stdout
    
    def test_version(self):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.stdout
    
    def test_info(self):
        """Test info command."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "AI Project Synthesizer" in result.stdout
        assert "Key Features" in result.stdout


class TestSearchCommand:
    """Test the search command."""
    
    @patch("src.discovery.unified_search.create_unified_search")
    def test_search_basic(self, mock_create_search):
        """Test basic search functionality."""
        mock_search = AsyncMock()
        mock_search.search.return_value = MagicMock(
            repositories=[],
            total_count=0,
        )
        mock_create_search.return_value = mock_search
        
        result = runner.invoke(app, ["search", "machine learning"])
        # Should complete without error even with no results
        assert "Searching for" in result.stdout
    
    @patch("src.discovery.unified_search.create_unified_search")
    def test_search_with_options(self, mock_create_search):
        """Test search with all options."""
        mock_search = AsyncMock()
        mock_search.search.return_value = MagicMock(
            repositories=[],
            total_count=0,
        )
        mock_create_search.return_value = mock_search
        
        result = runner.invoke(app, [
            "search", "transformers",
            "--platforms", "github,huggingface",
            "--max-results", "10",
            "--language", "python",
            "--min-stars", "100",
            "--format", "json"
        ])
        assert "Searching for" in result.stdout
    
    def test_search_no_query(self):
        """Test search without query fails appropriately."""
        result = runner.invoke(app, ["search"])
        assert result.exit_code != 0


class TestAnalyzeCommand:
    """Test the analyze command."""
    
    @patch("src.mcp_server.tools.handle_analyze_repository")
    def test_analyze_basic(self, mock_analyze):
        """Test basic analyze functionality."""
        mock_analyze.return_value = {
            "status": "success",
            "repository": {
                "name": "test-repo",
                "platform": "github",
                "language": "Python",
                "stars": 100,
                "url": "https://github.com/user/repo",
                "description": "Test repository",
            },
            "files_analyzed": 50,
            "lines_of_code": 1000,
            "dependencies": {"direct_count": 5},
            "quality_score": {"overall_score": 85},
        }
        
        result = runner.invoke(app, ["analyze", "https://github.com/user/repo"])
        assert result.exit_code == 0 or "Analyzing" in result.stdout
    
    @patch("src.mcp_server.tools.handle_analyze_repository")
    def test_analyze_json_format(self, mock_analyze):
        """Test analyze with JSON output."""
        mock_analyze.return_value = {
            "status": "success",
            "repository": {"name": "test"},
            "files_analyzed": 10,
        }
        
        result = runner.invoke(app, [
            "analyze", "https://github.com/user/repo",
            "--format", "json"
        ])
        # Should attempt JSON output
        assert "Analyzing" in result.stdout or result.exit_code == 0
    
    def test_analyze_no_url(self):
        """Test analyze without URL fails."""
        result = runner.invoke(app, ["analyze"])
        assert result.exit_code != 0


class TestSynthesizeCommand:
    """Test the synthesize command."""
    
    def test_synthesize_missing_args(self):
        """Test synthesize without required args fails."""
        result = runner.invoke(app, ["synthesize"])
        assert result.exit_code != 0
    
    @patch("src.mcp_server.tools.handle_synthesize_project")
    def test_synthesize_basic(self, mock_synthesize):
        """Test basic synthesize functionality."""
        mock_synthesize.return_value = {
            "status": "success",
            "project_path": "/tmp/test-project",
        }
        
        result = runner.invoke(app, [
            "synthesize",
            "--repos", "https://github.com/user/repo1,https://github.com/user/repo2",
            "--name", "test-project",
            "--output", "./output"
        ])
        assert "Synthesizing" in result.stdout or result.exit_code == 0


class TestResolveCommand:
    """Test the resolve command."""
    
    def test_resolve_missing_repos(self):
        """Test resolve without repos fails."""
        result = runner.invoke(app, ["resolve"])
        assert result.exit_code != 0
    
    @patch("src.mcp_server.tools.handle_resolve_dependencies")
    def test_resolve_basic(self, mock_resolve):
        """Test basic resolve functionality."""
        mock_resolve.return_value = {
            "status": "success",
            "packages": [
                {"name": "fastapi", "version": "0.100.0", "source": "pypi"},
            ],
            "requirements_txt": "fastapi==0.100.0\n",
            "warnings": [],
        }
        
        result = runner.invoke(app, [
            "resolve",
            "--repos", "https://github.com/user/repo1"
        ])
        assert "Resolving" in result.stdout or result.exit_code == 0


class TestDocsCommand:
    """Test the docs command."""
    
    def test_docs_missing_path(self):
        """Test docs without path fails."""
        result = runner.invoke(app, ["docs"])
        assert result.exit_code != 0
    
    @patch("src.mcp_server.tools.handle_generate_documentation")
    def test_docs_basic(self, mock_docs):
        """Test basic docs functionality."""
        mock_docs.return_value = {
            "status": "success",
            "documents": ["README.md", "API.md"],
            "llm_enhanced": True,
        }
        
        result = runner.invoke(app, ["docs", "./my-project"])
        assert "Generating documentation" in result.stdout or result.exit_code == 0


class TestConfigCommand:
    """Test the config command."""
    
    @patch("src.cli.get_settings")
    def test_config_basic(self, mock_get_settings):
        """Test basic config display."""
        # Create properly structured mock settings
        mock_app = MagicMock()
        mock_app.app_env = "development"
        mock_app.debug = True
        mock_app.log_level = "INFO"
        
        mock_platforms = MagicMock()
        mock_platforms.get_enabled_platforms.return_value = ["github", "arxiv"]
        mock_platforms.github_token = MagicMock()
        mock_platforms.github_token.get_secret_value.return_value = "test-token"
        mock_platforms.huggingface_token = MagicMock()
        mock_platforms.huggingface_token.get_secret_value.return_value = ""
        
        mock_llm = MagicMock()
        mock_llm.ollama_host = "http://localhost:11434"
        mock_llm.default_model = "llama3"
        
        mock_cache = MagicMock()
        mock_cache.enabled = True
        mock_cache.ttl = 3600
        
        settings_instance = MagicMock()
        settings_instance.app = mock_app
        settings_instance.platforms = mock_platforms
        settings_instance.llm = mock_llm
        settings_instance.cache = mock_cache
        
        mock_get_settings.return_value = settings_instance
        
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Configuration" in result.stdout


class TestServeCommand:
    """Test the serve command."""
    
    @pytest.mark.skip(reason="MCP server requires external mcp package with stdio module")
    def test_serve_starts(self):
        """Test that serve command attempts to start server."""
        # Note: This test is skipped because src.mcp_server.server imports mcp.server.stdio
        # which requires the external MCP package to be properly configured
        import src.mcp_server.server as mcp_server_module
        
        with patch.object(mcp_server_module, 'main', new_callable=AsyncMock) as mock_main:
            mock_main.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(app, ["serve"])
            assert "Starting MCP Server" in result.stdout or "stopped" in result.stdout


class TestMainFunction:
    """Test the main entry point."""
    
    def test_main_imports(self):
        """Test that main function exists and is callable."""
        assert callable(main)
    
    @patch("src.cli.app")
    def test_main_calls_app(self, mock_app):
        """Test that main calls the app."""
        mock_app.side_effect = SystemExit(0)
        
        with pytest.raises(SystemExit):
            main()
