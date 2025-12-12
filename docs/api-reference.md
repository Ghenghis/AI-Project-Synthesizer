# 🔧 API Reference

This document provides detailed API documentation for all modules and components of the AI Project Synthesizer.

## Table of Contents

- [Agents](#agents)
- [LLM Integration](#llm-integration)
- [Voice & Audio](#voice--audio)
- [Discovery & Analysis](#discovery--analysis)
- [Memory & Storage](#memory--storage)
- [Core Infrastructure](#core-infrastructure)
- [Quality & Testing](#quality--testing)

---

## 🤖 Agents

### BaseAgent

The base class for all AI agents.

```python
class BaseAgent:
    """Base agent class with common functionality."""
    
    def __init__(self, llm_router: LiteLLMRouter, **kwargs):
        """Initialize the agent.
        
        Args:
            llm_router: LLM router instance
            **kwargs: Additional configuration
        """
    
    async def process(self, input_data: Any) -> Any:
        """Process input data and return result."""
        pass
```

### CodeAgent

Specialized agent for code generation and analysis.

```python
class CodeAgent(BaseAgent):
    """Agent for code-related tasks."""
    
    async def generate_code(self, prompt: str, language: str = "python") -> str:
        """Generate code from natural language prompt.
        
        Args:
            prompt: Natural language description
            language: Target programming language
            
        Returns:
            Generated code as string
        """
    
    async def review_code(self, code: str) -> dict:
        """Review code and provide feedback.
        
        Args:
            code: Code to review
            
        Returns:
            Dictionary with review results
        """
    
    async def refactor_code(self, code: str, style: str = "clean") -> str:
        """Refactor code according to specified style.
        
        Args:
            code: Code to refactor
            style: Refactoring style
            
        Returns:
            Refactored code
        """
```

### ResearchAgent

Agent for gathering and synthesizing information.

```python
class ResearchAgent(BaseAgent):
    """Agent for research tasks."""
    
    async def search(self, query: str, sources: List[str] = None) -> List[dict]:
        """Search for information across multiple sources.
        
        Args:
            query: Search query
            sources: List of sources to search
            
        Returns:
            List of search results
        """
    
    async def summarize(self, content: str, length: str = "medium") -> str:
        """Summarize content.
        
        Args:
            content: Content to summarize
            length: Summary length (short/medium/long)
            
        Returns:
            Summary as string
        """
```

---

## 🧠 LLM Integration

### LiteLLMRouter

Unified interface for multiple LLM providers.

```python
class LiteLLMRouter:
    """Router for multiple LLM providers."""
    
    def __init__(self, config: dict = None):
        """Initialize the router.
        
        Args:
            config: Configuration dictionary
        """
    
    async def initialize(self):
        """Initialize all configured providers."""
    
    async def chat_completion(
        self,
        messages: List[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> dict:
        """Generate chat completion.
        
        Args:
            messages: List of message dictionaries
            model: Model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Completion response
        """
    
    async def embedding(
        self,
        text: str,
        model: str = None
    ) -> List[float]:
        """Generate text embedding.
        
        Args:
            text: Text to embed
            model: Embedding model
            
        Returns:
            Embedding vector
        """
```

### Provider Classes

#### OpenAIProvider

```python
class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""
    
    async def chat_completion(self, *args, **kwargs) -> dict:
        """OpenAI chat completion."""
    
    async def embedding(self, *args, **kwargs) -> List[float]:
        """OpenAI embedding generation."""
```

#### AnthropicProvider

```python
class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""
    
    async def chat_completion(self, *args, **kwargs) -> dict:
        """Claude chat completion."""
```

---

## 🎤 Voice & Audio

### VoiceManager

Main interface for voice operations.

```python
class VoiceManager:
    """Manager for voice synthesis and recognition."""
    
    def __init__(self, tts_client: ElevenLabsClient, asr_client: ASRClient):
        """Initialize voice manager."""
    
    async def speak(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0
    ) -> bytes:
        """Convert text to speech.
        
        Args:
            text: Text to speak
            voice: Voice to use
            speed: Speech speed
            
        Returns:
            Audio data as bytes
        """
    
    async def listen(
        self,
        language: str = "en",
        duration: float = 5.0
    ) -> str:
        """Listen for speech input.
        
        Args:
            language: Language code
            duration: Maximum duration in seconds
            
        Returns:
            Transcribed text
        """
```

### ElevenLabsClient

Client for ElevenLabs TTS service.

```python
class ElevenLabsClient:
    """ElevenLabs API client."""
    
    async def synthesize(
        self,
        text: str,
        voice_id: str = None,
        model_id: str = None
    ) -> bytes:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_id: Voice ID to use
            model_id: Model ID to use
            
        Returns:
            Audio data
        """
    
    async def get_voices(self) -> List[Voice]:
        """Get available voices."""
    
    async def clone_voice(
        self,
        name: str,
        audio_file: bytes
    ) -> Voice:
        """Clone a voice from audio."""
```

---

## 🔍 Discovery & Analysis

### FirecrawlEnhanced

Enhanced web scraping with AI capabilities.

```python
class FirecrawlEnhanced(FirecrawlClient):
    """Enhanced Firecrawl client with caching and AI features."""
    
    def __init__(
        self,
        api_key: str = None,
        cache_strategy: CacheStrategy = CacheStrategy.HYBRID,
        rate_limit_config: RateLimitConfig = None
    ):
        """Initialize enhanced client."""
    
    async def scrape_url(
        self,
        url: str,
        formats: List[FirecrawlFormat] = None,
        use_browser_fallback: bool = True
    ) -> ScrapedContent:
        """Scrape URL with enhanced features.
        
        Args:
            url: URL to scrape
            formats: Output formats
            use_browser_fallback: Use browser if API fails
            
        Returns:
            Scraped content
        """
    
    async def batch_scrape(
        self,
        urls: List[str],
        **kwargs
    ) -> List[ScrapedContent]:
        """Scrape multiple URLs in parallel."""
```

### ASTParser

Parser for analyzing code structure.

```python
class ASTParser:
    """Python AST parser for code analysis."""
    
    def parse(self, code: str) -> ast.AST:
        """Parse code into AST."""
    
    def extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """Extract function definitions."""
    
    def extract_classes(self, tree: ast.AST) -> List[ClassInfo]:
        """Extract class definitions."""
    
    def analyze_dependencies(self, tree: ast.AST) -> List[str]:
        """Analyze import dependencies."""
```

---

## 💾 Memory & Storage

### MemoryManager

Interface for memory operations.

```python
class MemoryManager:
    """Manager for persistent memory operations."""
    
    async def store(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """Store value in memory.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
    
    async def retrieve(self, key: str) -> Any:
        """Retrieve value from memory."""
    
    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search memory by semantic similarity."""
```

### CacheManager

Multi-level caching system.

```python
class CacheManager:
    """Multi-level cache manager."""
    
    def __init__(
        self,
        memory_size: int = 1000,
        disk_path: str = "./cache",
        ttl: int = 3600
    ):
        """Initialize cache manager."""
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ):
        """Set value in cache."""
    
    async def invalidate(self, pattern: str = None):
        """Invalidate cache entries."""
```

---

## 🔧 Core Infrastructure

### ConfigManager

Centralized configuration management.

```python
class ConfigManager:
    """Configuration manager with validation."""
    
    def __init__(self, config_file: str = "config.yaml"):
        """Initialize config manager."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
    
    def validate(self) -> List[ValidationError]:
        """Validate configuration."""
```

### ResourceManager

System resource management.

```python
class ResourceManager:
    """Manager for system resources."""
    
    async def monitor(self) -> ResourceMetrics:
        """Monitor system resources."""
    
    async def limit_memory(self, limit_mb: int):
        """Limit memory usage."""
    
    async def limit_cpu(self, limit_percent: float):
        """Limit CPU usage."""
```

### HealthChecker

System health monitoring.

```python
class HealthChecker:
    """Health check system."""
    
    async def check_all(self) -> HealthReport:
        """Check all system components."""
    
    async def check_database(self) -> bool:
        """Check database connectivity."""
    
    async def check_apis(self) -> Dict[str, bool]:
        """Check external API status."""
```

---

## 📊 Quality & Testing

### QualityScorer

Code quality assessment.

```python
class QualityScorer:
    """Code quality scoring system."""
    
    def analyze(self, code: str) -> QualityReport:
        """Analyze code quality.
        
        Args:
            code: Code to analyze
            
        Returns:
            Quality report with scores
        """
    
    def calculate_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity."""
    
    def check_style(self, code: str) -> List[StyleViolation]:
        """Check code style violations."""
```

### TestRunner

Automated test execution.

```python
class TestRunner:
    """Test runner with reporting."""
    
    async def run_tests(
        self,
        test_path: str = "tests/",
        coverage: bool = True
    ) -> TestReport:
        """Run test suite.
        
        Args:
            test_path: Path to tests
            coverage: Generate coverage report
            
        Returns:
            Test results
        """
    
    async def generate_report(
        self,
        format: str = "html"
    ) -> str:
        """Generate test report."""
```

---

## 🔄 Error Handling

### Custom Exceptions

```python
class AISynthesizerError(Exception):
    """Base exception for the project."""

class LLMError(AISynthesizerError):
    """LLM-related errors."""

class VoiceError(AISynthesizerError):
    """Voice synthesis/recognition errors."""

class MemoryError(AISynthesizerError):
    """Memory system errors."""

class ConfigurationError(AISynthesizerError):
    """Configuration errors."""
```

---

## 📝 Usage Examples

### Complete Workflow Example

```python
from src.agents import CodeAgent, ResearchAgent
from src.llm import LiteLLMRouter
from src.voice import VoiceManager
from src.memory import MemoryManager

# Initialize components
router = LiteLLMRouter()
await router.initialize()

memory = MemoryManager()
voice = VoiceManager()

# Create agents
coder = CodeAgent(llm_router=router)
researcher = ResearchAgent(llm_router=router)

# Research topic
research = await researcher.search("Python async best practices")
summary = await researcher.summarize(research[0]['content'])

# Generate code based on research
code = await coder.generate_code(
    f"Write async Python code following these practices: {summary}"
)

# Store in memory
await memory.store("async_example", code)

# Speak result
await voice.speak("I've generated the async code example!")
```

---

## 📚 Additional Resources

- [Examples Repository](../examples/)
- [Tutorial Videos](https://youtube.com/playlist)
- [API Playground](https://playground.ai-synthesizer.dev)
- [Community Forum](https://forum.ai-synthesizer.dev)
