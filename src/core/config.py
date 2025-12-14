"""
AI Project Synthesizer - Core Configuration

This module handles all configuration management including:
- Environment variable loading
- Settings validation
- Platform credentials
- LLM configuration
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    """Platform API credentials and settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # GitHub (Required)
    github_token: SecretStr = Field(
        default=SecretStr(""), description="GitHub personal access token"
    )

    # GitLab (Optional)
    gitlab_token: SecretStr = Field(
        default=SecretStr(""), description="GitLab personal access token"
    )
    gitlab_url: str = Field(
        default="https://gitlab.com", description="GitLab instance URL"
    )

    # HuggingFace (Optional)
    huggingface_token: SecretStr = Field(
        default=SecretStr(""), description="HuggingFace access token"
    )

    # Kaggle (Optional)
    kaggle_username: str = Field(default="", description="Kaggle username")
    kaggle_key: SecretStr = Field(default=SecretStr(""), description="Kaggle API key")

    # Semantic Scholar (Optional)
    semantic_scholar_api_key: SecretStr = Field(
        default=SecretStr(""), description="Semantic Scholar API key"
    )

    def get_enabled_platforms(self) -> list[str]:
        """Return list of platforms with valid credentials."""
        platforms = []

        if self.github_token.get_secret_value():
            platforms.append("github")
        if self.gitlab_token.get_secret_value():
            platforms.append("gitlab")
        if self.huggingface_token.get_secret_value():
            platforms.append("huggingface")
        if self.kaggle_username and self.kaggle_key.get_secret_value():
            platforms.append("kaggle")

        # These don't require auth
        platforms.extend(["arxiv", "papers_with_code"])

        if self.semantic_scholar_api_key.get_secret_value():
            platforms.append("semantic_scholar")

        return platforms


class LLMSettings(BaseSettings):
    """LLM configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Ollama - Optimized for 7B and smaller models
    ollama_host: str = Field(
        default="http://localhost:11434", description="Ollama server URL"
    )
    ollama_model_tiny: str = Field(
        default="qwen2.5-coder:1.5b-instruct",
        description="Tiny model (< 2B) for quick tasks",
    )
    ollama_model_small: str = Field(
        default="qwen2.5-coder:3b-instruct",
        description="Small model (2-4B) for simple tasks",
    )
    ollama_model_medium: str = Field(
        default="qwen2.5-coder:7b-instruct-q8_0",
        description="Medium model (4-7B) for balanced tasks - DEFAULT",
    )
    ollama_model_size_preference: str = Field(
        default="medium",
        description="Model size preference: tiny, small, medium, large",
    )

    # LM Studio - Size-based model selection
    lmstudio_host: str = Field(
        default="http://localhost:1234", description="LM Studio server URL"
    )
    lmstudio_model_tiny: str = Field(
        default="local-model-tiny", description="Tiny model (< 2B) for quick tasks"
    )
    lmstudio_model_small: str = Field(
        default="local-model-small", description="Small model (2-4B) for simple tasks"
    )
    lmstudio_model_medium: str = Field(
        default="local-model-medium",
        description="Medium model (4-7B) for balanced tasks - DEFAULT",
    )
    lmstudio_model_size_preference: str = Field(
        default="medium",
        description="Model size preference: tiny, small, medium, large",
    )
    lmstudio_api_key: str = Field(
        default="lm-studio", description="LM Studio API key (any string works)"
    )
    lmstudio_enabled: bool = Field(
        default=True, description="Enable LM Studio integration"
    )

    # Cloud LLM
    cloud_llm_enabled: bool = Field(
        default=False, description="Enable cloud LLM fallback"
    )
    cloud_routing_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Threshold for routing to cloud"
    )

    # OpenAI
    openai_api_key: SecretStr = Field(
        default=SecretStr(""), description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview", description="OpenAI model to use"
    )

    # Anthropic
    anthropic_api_key: SecretStr = Field(
        default=SecretStr(""), description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514", description="Anthropic model to use"
    )

    # xAI / Grok
    xai_api_key: SecretStr = Field(
        default=SecretStr(""), description="xAI API key for Grok models"
    )
    xai_model: str = Field(default="grok-3", description="xAI Grok model to use")
    xai_base_url: str = Field(
        default="https://api.x.ai/v1", description="xAI API base URL"
    )

    # Google Gemini
    google_api_key: SecretStr = Field(
        default=SecretStr(""),
        alias="google_generative_ai_api_key",
        description="Google Generative AI API key",
    )
    google_model: str = Field(
        default="gemini-2.0-flash", description="Google Gemini model to use"
    )

    # Brave Search
    brave_search_api_key: SecretStr = Field(
        default=SecretStr(""), description="Brave Search API key"
    )


class ElevenLabsSettings(BaseSettings):
    """ElevenLabs voice AI configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # API Configuration
    elevenlabs_api_key: SecretStr = Field(
        default=SecretStr(""), description="ElevenLabs API key"
    )

    # Voice Selection
    default_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",  # Rachel - default voice
        description="Default voice ID for TTS",
    )

    # Available voices (popular ones)
    # Rachel: 21m00Tcm4TlvDq8ikWAM - Calm, professional
    # Domi: AZnzlk1XvdvUeBnXmlld - Strong, confident
    # Bella: EXAVITQu4vr4xnSDxMaL - Soft, gentle
    # Antoni: ErXwobaYiN019PkySvjV - Well-rounded, warm
    # Elli: MF3mGyEYCl7XYWbV9V6O - Young, expressive
    # Josh: TxGEqnHWrfWFTfGW9XjX - Deep, narrative
    # Arnold: VR6AewLTigWG4xSOukaG - Crisp, authoritative
    # Adam: pNInz6obpgDQGcFmaJgB - Deep, warm
    # Sam: yoZ06aMxZJJ28mfd3POQ - Dynamic, expressive

    # Model Selection
    tts_model: str = Field(
        default="eleven_multilingual_v2",
        description="TTS model: eleven_multilingual_v2, eleven_turbo_v2_5, eleven_turbo_v2",
    )

    # Real-time Voice Settings
    realtime_enabled: bool = Field(
        default=True, description="Enable real-time voice streaming"
    )
    realtime_model: str = Field(
        default="eleven_turbo_v2_5",
        description="Model for real-time voice (lower latency)",
    )

    # Voice Settings
    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0=variable, 1=stable)",
    )
    similarity_boost: float = Field(
        default=0.75, ge=0.0, le=1.0, description="Voice similarity boost"
    )
    style: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Style exaggeration (v2 models only)"
    )
    use_speaker_boost: bool = Field(default=True, description="Enhance speaker clarity")

    # Output Settings
    output_format: str = Field(
        default="mp3_44100_128",
        description="Output format: mp3_44100_128, pcm_16000, pcm_22050, pcm_24000, pcm_44100",
    )


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    app_name: str = Field(
        default="AI Project Synthesizer", description="Application name"
    )
    app_env: str = Field(
        default="development", description="Environment (development/production)"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server
    server_host: str = Field(default="localhost", description="Server host")
    server_port: int = Field(default=8000, description="Server port")

    # Paths
    default_output_dir: Path = Field(
        default=Path("./output"), description="Default output directory"
    )
    temp_dir: Path = Field(default=Path("./temp"), description="Temporary directory")
    cache_dir: Path = Field(default=Path("./.cache"), description="Cache directory")

    # Synthesis
    max_repos_per_synthesis: int = Field(
        default=10, ge=1, le=50, description="Maximum repositories per synthesis"
    )
    max_concurrent_clones: int = Field(
        default=3, ge=1, le=10, description="Maximum concurrent clone operations"
    )
    clone_depth: int = Field(default=1, ge=1, description="Git clone depth")

    # Network
    request_timeout_seconds: int = Field(default=30, description="HTTP request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    # Cache
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")

    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = Field(
        default=5, ge=1, le=20, description="Failures before circuit breaker opens"
    )
    circuit_breaker_recovery_timeout: float = Field(
        default=60.0,
        ge=10.0,
        le=600.0,
        description="Seconds to wait before retry (circuit breaker)",
    )
    circuit_breaker_success_threshold: int = Field(
        default=2, ge=1, le=10, description="Successes needed to close circuit breaker"
    )
    circuit_breaker_timeout: float = Field(
        default=30.0, ge=5.0, le=300.0, description="Call timeout for circuit breaker"
    )

    # Observability Settings
    metrics_retention_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # 1 week
        description="Metrics retention period in hours",
    )
    correlation_id_in_logs: bool = Field(
        default=True, description="Include correlation IDs in log output"
    )
    health_check_interval: int = Field(
        default=60, ge=10, le=300, description="Health check interval in seconds"
    )

    # Security Settings
    mask_secrets_in_logs: bool = Field(
        default=True, description="Mask secrets in log output"
    )
    validate_input_urls: bool = Field(
        default=True, description="Validate repository URLs"
    )
    max_query_length: int = Field(
        default=1000, ge=100, le=10000, description="Maximum search query length"
    )

    # Lifecycle Settings
    graceful_shutdown_timeout: float = Field(
        default=60.0,
        ge=10.0,
        le=300.0,
        description="Graceful shutdown timeout in seconds",
    )
    shutdown_cleanup_timeout: float = Field(
        default=30.0, ge=5.0, le=120.0, description="Cleanup timeout during shutdown"
    )

    @field_validator("default_output_dir", "temp_dir", "cache_dir", mode="after")
    @classmethod
    def ensure_directory_exists(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class Settings(BaseSettings):
    """Combined settings container."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    platforms: PlatformSettings = Field(default_factory=PlatformSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    elevenlabs: ElevenLabsSettings = Field(default_factory=ElevenLabsSettings)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app.app_env == "production"

    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.app.debug and not self.is_production

    def get_available_llm_providers(self) -> list[str]:
        """Get list of LLM providers with valid API keys."""
        providers = []

        # Local providers (always available if running)
        providers.extend(["lmstudio", "ollama"])

        # Cloud providers
        if self.llm.openai_api_key.get_secret_value():
            providers.append("openai")
        if self.llm.anthropic_api_key.get_secret_value():
            providers.append("anthropic")
        if self.llm.xai_api_key.get_secret_value():
            providers.append("xai")
        if self.llm.google_api_key.get_secret_value():
            providers.append("google")

        return providers


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
