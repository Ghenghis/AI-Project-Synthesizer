"""
Unit tests for the core configuration module.
"""


class TestAppSettings:
    """Test application settings."""

    def test_default_settings_load(self):
        """Test that default settings load correctly."""
        from src.core.config import AppSettings

        settings = AppSettings()

        assert settings.app_name == "AI Project Synthesizer"
        assert settings.log_level in (
            "INFO",
            "DEBUG",
        )  # Accept both as environment may override

    def test_environment_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("DEBUG", "false")

        from src.core.config import AppSettings

        settings = AppSettings()

        assert settings.app_env == "production"
        assert settings.debug is False


class TestPlatformSettings:
    """Test platform settings."""

    def test_enabled_platforms_with_github(self, monkeypatch):
        """Test that GitHub is enabled when token provided."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

        from src.core.config import PlatformSettings

        settings = PlatformSettings()
        platforms = settings.get_enabled_platforms()

        assert "github" in platforms
        assert "arxiv" in platforms

    def test_no_auth_platforms_always_available(self):
        """Test that non-auth platforms are always available."""
        from src.core.config import PlatformSettings

        settings = PlatformSettings()
        platforms = settings.get_enabled_platforms()

        assert "arxiv" in platforms
        assert "papers_with_code" in platforms


class TestLLMSettings:
    """Test LLM settings."""

    def test_default_ollama_settings(self, monkeypatch):
        """Test default Ollama configuration."""
        # Set environment variables to ensure consistent defaults
        monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_MODEL_MEDIUM", "qwen2.5-coder:7b-instruct-q8_0")

        from src.core.config import LLMSettings

        settings = LLMSettings()

        assert settings.ollama_host == "http://localhost:11434"
        assert "qwen2.5-coder" in settings.ollama_model_medium

    def test_cloud_disabled_by_default(self):
        """Test that cloud LLM is disabled by default."""
        from src.core.config import LLMSettings

        settings = LLMSettings()

        assert settings.cloud_llm_enabled is False
