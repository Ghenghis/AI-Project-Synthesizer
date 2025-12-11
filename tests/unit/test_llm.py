"""
AI Project Synthesizer - LLM Module Tests

Tests for LLM client implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


class TestOllamaClient:
    """Test Ollama client."""
    
    def test_client_initialization(self):
        """Test client initializes with defaults."""
        from src.llm.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        assert client is not None
        assert client.host == "http://localhost:11434"
    
    def test_client_with_custom_host(self):
        """Test client with custom host."""
        from src.llm.ollama_client import OllamaClient
        
        client = OllamaClient(host="http://custom:11434")
        
        assert client.host == "http://custom:11434"
    
    def test_default_models_defined(self):
        """Test default models are defined."""
        from src.llm.ollama_client import OllamaClient
        
        assert hasattr(OllamaClient, 'DEFAULT_MODELS')
        assert 'fast' in OllamaClient.DEFAULT_MODELS
        assert 'balanced' in OllamaClient.DEFAULT_MODELS
    
    def test_default_model_set(self):
        """Test default model is set."""
        from src.llm.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        assert client.default_model is not None
        assert "qwen" in client.default_model.lower()
    
    def test_custom_model(self):
        """Test custom model can be set."""
        from src.llm.ollama_client import OllamaClient
        
        client = OllamaClient(default_model="custom-model:latest")
        
        assert client.default_model == "custom-model:latest"


class TestLMStudioClient:
    """Test LM Studio client."""
    
    def test_client_initialization(self):
        """Test client initializes correctly."""
        from src.llm.lmstudio_client import LMStudioClient
        
        client = LMStudioClient()
        
        assert client is not None
        assert "1234" in client.host  # Default LM Studio port
    
    def test_client_with_custom_host(self):
        """Test client with custom host."""
        from src.llm.lmstudio_client import LMStudioClient
        
        client = LMStudioClient(host="http://localhost:8080")
        
        assert client.host == "http://localhost:8080"
    
    def test_openai_compatible(self):
        """Test that client is OpenAI-compatible."""
        from src.llm.lmstudio_client import LMStudioClient
        
        client = LMStudioClient()
        
        # Should have complete method like OpenAI
        assert hasattr(client, 'complete') or hasattr(client, 'chat_complete')


class TestLLMRouter:
    """Test LLM router."""
    
    def test_router_initialization(self):
        """Test router initializes."""
        from src.llm.router import LLMRouter
        
        router = LLMRouter()
        
        assert router is not None
    
    def test_router_has_clients(self):
        """Test router has client instances."""
        from src.llm.router import LLMRouter
        
        router = LLMRouter()
        
        # Should have client instances
        assert hasattr(router, 'ollama_client')
        assert hasattr(router, 'lmstudio_client')
    
    def test_router_preferred_provider(self):
        """Test router preferred provider setting."""
        from src.llm.router import LLMRouter, ProviderType
        
        router = LLMRouter(preferred_provider="ollama")
        
        assert router.preferred_provider == ProviderType.OLLAMA
    
    def test_router_local_models(self):
        """Test router has local model configurations."""
        from src.llm.router import LLMRouter
        
        router = LLMRouter()
        
        assert hasattr(router, 'local_models')
        assert "ollama" in router.local_models
        assert "lmstudio" in router.local_models


class TestModelSizing:
    """Test model size selection."""
    
    def test_size_categories(self):
        """Test model size categories."""
        from src.core.config import LLMSettings
        
        settings = LLMSettings()
        
        # Should have different size models
        assert hasattr(settings, 'ollama_model_tiny')
        assert hasattr(settings, 'ollama_model_small')
        assert hasattr(settings, 'ollama_model_medium')
    
    def test_size_preference(self):
        """Test size preference setting."""
        from src.core.config import LLMSettings
        
        settings = LLMSettings()
        
        assert settings.ollama_model_size_preference in ['tiny', 'small', 'medium', 'large']
    
    def test_lmstudio_settings(self):
        """Test LM Studio settings."""
        from src.core.config import LLMSettings
        
        settings = LLMSettings()
        
        assert hasattr(settings, 'lmstudio_host')
        assert hasattr(settings, 'lmstudio_enabled')
