# 🚀 Getting Started with AI Project Synthesizer

Welcome to the AI Project Synthesizer! This guide will help you set up and start using this powerful AI-powered development ecosystem.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
- **Git** - Download from [git-scm.com](https://git-scm.com/)
- **Docker** (optional) - For containerized deployment
- **API Keys** for AI services you plan to use:
  - OpenAI API Key
  - Anthropic API Key
  - ElevenLabs API Key (for voice features)
  - GitHub Token (for repository access)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-project-synthesizer.git
cd ai-project-synthesizer
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your API keys:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# Local LLM Configuration
OLLAMA_HOST=http://localhost:11434
LM_STUDIO_HOST=http://localhost:1234

# Database Configuration
DATABASE_URL=sqlite:///./ai_synthesizer.db

# Cache Configuration
CACHE_DIR=./cache
```

## 🎯 Quick Start Examples

### Example 1: Code Generation

```python
from src.llm import LiteLLMRouter
from src.agents import CodeAgent

# Initialize the LLM router
router = LiteLLMRouter()
await router.initialize()

# Create a code agent
agent = CodeAgent(llm_router=router)

# Generate code
prompt = "Create a Python function to calculate fibonacci numbers"
code = await agent.generate_code(prompt)
print(code)
```

### Example 2: Voice Interaction

```python
from src.voice import VoiceManager
from src.voice.elevenlabs_client import ElevenLabsClient

# Initialize voice manager
voice_manager = VoiceManager()

# Text to speech
await voice_manager.speak("Hello, welcome to AI Project Synthesizer!")

# Speech to text (if microphone is available)
text = await voice_manager.listen()
print(f"You said: {text}")
```

### Example 3: Web Scraping and Analysis

```python
from src.discovery import FirecrawlEnhanced
from src.analysis import ContentExtractor

# Initialize enhanced scraper
scraper = FirecrawlEnhanced(api_key="your_firecrawl_key")

# Scrape a website
content = await scraper.scrape_url("https://example.com")

# Extract and analyze content
extractor = ContentExtractor()
summary = await extractor.summarize(content)
print(summary)
```

### Example 4: Multi-Agent Collaboration

```python
from src.agents import ResearchAgent, CodeAgent, SynthesisAgent
from src.agents.crewai_integration import CrewAIOrchestrator

# Create agents
researcher = ResearchAgent()
coder = CodeAgent()
synthesizer = SynthesisAgent()

# Set up crew
orchestrator = CrewAIOrchestrator()
orchestrator.add_agent(researcher, role="researcher")
orchestrator.add_agent(coder, role="developer")
orchestrator.add_agent(synthesizer, role="synthesizer")

# Run collaborative task
task = "Research best practices for Python testing and implement a test suite"
result = await orchestrator.execute_task(task)
print(result)
```

## 🔧 Configuration Options

### LLM Provider Configuration

Configure multiple LLM providers in your `.env`:

```env
# Primary provider
PRIMARY_LLM_PROVIDER=openai

# Provider-specific settings
OPENAI_MODEL=gpt-4
ANTHROPIC_MODEL=claude-3-opus-20240229

# Fallback providers
FALLBACK_PROVIDERS=anthropic,ollama,lm_studio
```

### Memory Configuration

```env
# Memory system settings
MEMORY_PROVIDER=mem0
MEMORY_CACHE_SIZE=1000
MEMORY_TTL=3600

# Vector database (for semantic search)
VECTOR_DB_PROVIDER=chroma
VECTOR_DB_PATH=./vector_db
```

### Voice Configuration

```env
# Voice settings
DEFAULT_VOICE=rachel
VOICE_MODEL=eleven_multilingual_v2
VOICE_SAMPLE_RATE=44100

# ASR settings
ASR_PROVIDER=glm
ASR_LANGUAGE=en
```

## 🐳 Docker Setup

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Individual Services

```bash
# Run just the MCP server
docker run -p 8000:8000 ai-synthesizer:server

# Run with local model support
docker run -v ./models:/app/models ai-synthesizer:full
```

## 🧪 Testing Your Setup

Run the test suite to verify everything is working:

```bash
# Run all tests
pytest tests/

# Run specific module tests
pytest tests/unit/agents/

# Run with coverage
pytest --cov=src tests/
```

## 📚 Next Steps

Now that you're set up, explore these resources:

1. **[API Reference](api-reference.md)** - Detailed API documentation
2. **[Tutorials](tutorials.md)** - Step-by-step guides
3. **[Architecture Guide](architecture.md)** - Understand the system design
4. **[Examples](../examples/)** - Practical code examples

## ❓ Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the virtual environment
   which python
   
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

2. **API Key Issues**
   ```bash
   # Verify your .env file
   cat .env
   
   # Test API connectivity
   python -c "from src.llm import LiteLLMRouter; print('API OK')"
   ```

3. **Memory Issues**
   ```bash
   # Clear cache
   rm -rf ./cache
   
   # Reduce memory usage in .env
   echo "MEMORY_CACHE_SIZE=100" >> .env
   ```

4. **Voice Issues**
   ```bash
   # Test audio device
   python -c "import sounddevice as sd; print(sd.query_devices())"
   
   # Install audio dependencies
   pip install sounddevice portaudio
   ```

### Getting Help

- Check the [FAQ](faq.md) for common questions
- Search [GitHub Issues](https://github.com/yourusername/ai-project-synthesizer/issues)
- Join our [Discord Community](https://discord.gg/yourserver)
- Email us at support@ai-synthesizer.dev

## 🎉 Congratulations!

You've successfully set up the AI Project Synthesizer! You're now ready to:
- Generate code with AI assistance
- Build multi-agent systems
- Create voice-enabled applications
- Automate your development workflow
- And much more!

Happy coding! 🚀
