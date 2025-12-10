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
from typing import Optional, List, Dict, Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    """Platform API credentials and settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # GitHub (Required)
    github_token: SecretStr = Field(
        default=SecretStr(""),
        description="GitHub personal access token"
    )
    
    # GitLab (Optional)
    gitlab_token: SecretStr = Field(
        default=SecretStr(""),
        description="GitLab personal access token"
    )
    gitlab_url: str = Field(
        default="https://gitlab.com",
        description="GitLab instance URL"
    )
    
    # HuggingFace (Optional)
    huggingface_token: SecretStr = Field(
        default=SecretStr(""),
        description="HuggingFace access token"
    )
    
    # Kaggle (Optional)
    kaggle_username: str = Field(
        default="",
        description="Kaggle username"
    )
    kaggle_key: SecretStr = Field(
        default=SecretStr(""),
        description="Kaggle API key"
    )
    
    # Semantic Scholar (Optional)
    semantic_scholar_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Semantic Scholar API key"
    )
    
    def get_enabled_platforms(self) -> List[str]:
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
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Ollama (Local)
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_model_fast: str = Field(
        default="qwen2.5-coder:7b-instruct-q8_0",
        description="Fast model for simple tasks"
    )
    ollama_model_balanced: str = Field(
        default="qwen2.5-coder:14b-instruct-q4_K_M",
        description="Balanced model for moderate tasks"
    )
    ollama_model_powerful: str = Field(
        default="qwen2.5-coder:32b-instruct-q4_K_M",
        description="Powerful model for complex tasks"
    )
    
    # Cloud LLM
    cloud_llm_enabled: bool = Field(
        default=False,
        description="Enable cloud LLM fallback"
    )
    cloud_routing_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for routing to cloud"
    )
    
    # OpenAI
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model to use"
    )
    
    # Anthropic
    anthropic_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model to use"
    )


class AppSettings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(
        default="AI Project Synthesizer",
        description="Application name"
    )
    app_env: str = Field(
        default="development",
        description="Environment (development/production)"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Server
    server_host: str = Field(
        default="localhost",
        description="Server host"
    )
    server_port: int = Field(
        default=8000,
        description="Server port"
    )
    
    # Paths
    default_output_dir: Path = Field(
        default=Path("./output"),
        description="Default output directory"
    )
    temp_dir: Path = Field(
        default=Path("./temp"),
        description="Temporary directory"
    )
    cache_dir: Path = Field(
        default=Path("./.cache"),
        description="Cache directory"
    )
    
    # Synthesis
    max_repos_per_synthesis: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum repositories per synthesis"
    )
    max_concurrent_clones: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent clone operations"
    )
    clone_depth: int = Field(
        default=1,
        ge=1,
        description="Git clone depth"
    )
    
    # Network
    request_timeout_seconds: int = Field(
        default=30,
        description="HTTP request timeout"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )
    
    # Cache
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    
    @field_validator("default_output_dir", "temp_dir", "cache_dir", mode="after")
    @classmethod
    def ensure_directory_exists(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class Settings(BaseSettings):
    """Combined settings container."""
    
    app: AppSettings = Field(default_factory=AppSettings)
    platforms: PlatformSettings = Field(default_factory=PlatformSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app.app_env == "production"
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.app.debug and not self.is_production


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience function for quick access
settings = get_settings()
