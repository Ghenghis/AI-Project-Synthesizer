# VIBE MCP Developer Guide

Welcome to the VIBE MCP (Visual Intelligence Builder Environment) project! This guide will help you get set up for development and contribute to the project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Setup Instructions](#setup-instructions)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Code Style](#code-style)
8. [Contributing](#contributing)
9. [Troubleshooting](#troubleshooting)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/vibe-mcp.git
cd vibe-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize voice models
python scripts/download_voice_models.py

# Run tests
pytest tests/ -v

# Start development server
python -m src.mcp.server
```

## Prerequisites

### Required Software

- **Python 3.11+** - The project requires Python 3.11 or higher
- **Git** - For version control
- **Docker & Docker Compose** - For containerized development (optional but recommended)
- **Node.js 18+** - For certain integrations and tools

### System Dependencies

#### Linux/Ubuntu
```bash
sudo apt-get update
sudo apt-get install python3-dev python3-pip
sudo apt-get install espeak-ng  # For voice synthesis
```

#### macOS
```bash
brew install python@3.11 espeak
```

#### Windows
- Install Python 3.11+ from python.org
- Install Microsoft Visual C++ Build Tools
- Install Windows Subsystem for Linux (WSL) for best compatibility

### Voice System Requirements

The voice system requires additional models:

1. **Piper TTS Models** - Downloaded automatically on first run
2. **GLM-ASR Model** - 1.5B parameter model for speech recognition
3. **Optional: ElevenLabs API Key** - For cloud TTS fallback

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/vibe-mcp.git
cd vibe-mcp

# Create and activate virtual environment
python -m venv .venv

# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the template
cp .env.example .env

# Edit with your configuration
nano .env
```

Required environment variables:

```env
# Core Configuration
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/vibe_mcp

# API Keys (Optional)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
ELEVENLABS_API_KEY=your_elevenlabs_key
GITLAB_TOKEN=your_gitlab_token
FIRECRAWL_API_KEY=your_firecrawl_key

# Voice Configuration
VOICE_DEFAULT_PROVIDER=piper
VOICE_CACHE_DIR=./cache/voice
```

### 4. Database Setup

#### Option A: Local PostgreSQL
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb vibe_mcp

# Run migrations
python scripts/migrate_db.py
```

#### Option B: Docker (Recommended)
```bash
# Start PostgreSQL container
docker-compose -f docker/docker-compose.dev.yml up -d postgres

# Run migrations
python scripts/migrate_db.py
```

### 5. Voice Model Setup

```bash
# Download required voice models
python scripts/download_voice_models.py

# Verify installation
python -c "from src.voice.manager import VoiceManager; asyncio.run(VoiceManager().test_connection())"
```

## Project Structure

```
vibe-mcp/
├── src/                          # Source code
│   ├── agents/                   # Agent framework integrations
│   │   ├── autogen_integration.py
│   │   ├── swarm_integration.py
│   │   ├── langgraph_integration.py
│   │   ├── crewai_integration.py
│   │   └── framework_router.py
│   ├── automation/               # Browser automation
│   │   └── browser_client.py
│   ├── discovery/                # Platform discovery clients
│   │   ├── gitlab_client.py
│   │   └── firecrawl_client.py
│   ├── llm/                      # LLM integration
│   │   └── litellm_router.py
│   ├── memory/                   # Memory system
│   │   └── mem0_integration.py
│   ├── mcp/                      # MCP server and tools
│   │   ├── server.py
│   │   └── memory_tools.py
│   ├── voice/                    # Voice system
│   │   ├── manager.py
│   │   ├── tts/
│   │   │   └── piper_client.py
│   │   └── asr/
│   │       └── glm_asr_client.py
│   └── core/                     # Core utilities
│       ├── config.py
│       ├── security.py
│       └── exceptions.py
├── tests/                        # Test suite
│   ├── integration/
│   ├── e2e/
│   └── unit/
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── docker/                       # Docker configurations
├── models/                       # Model files
├── cache/                        # Cache directory
└── config/                       # Configuration files
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Create and checkout a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### 2. Make Changes

- Follow the code style guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/integration/test_memory.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### 4. Code Quality Checks

```bash
# Lint code
ruff check src/ --fix

# Format code
ruff format src/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

### 5. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add new feature description"

# Push to remote
git push origin feature/your-feature-name
```

## Testing

### Test Categories

1. **Unit Tests** - Test individual components
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test complete workflows

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance tests
pytest tests/performance/ -v
```

### Writing Tests

Example test structure:

```python
import pytest
from src.memory.mem0_integration import MemorySystem

class TestMemorySystem:
    @pytest.fixture
    async def memory_system(self):
        system = MemorySystem()
        yield system
        await system.cleanup()
    
    @pytest.mark.asyncio
    async def test_add_memory(self, memory_system):
        memory_id = await memory_system.add("Test content")
        assert memory_id is not None
```

## Code Style

### Python Style Guide

We use the following tools for code quality:

- **Ruff** - Linting and formatting
- **MyPy** - Type checking
- **Black** - Code formatting (via Ruff)

### Style Rules

1. **Line Length**: 88 characters
2. **Indentation**: 4 spaces
3. **Quotes**: Double quotes for strings
4. **Imports**: Grouped and sorted
5. **Type Hints**: Required on all functions

### Example

```python
"""Module docstring explaining purpose."""

from typing import Dict, List, Optional
import asyncio

from src.core.config import get_config

class ExampleClass:
    """Class docstring."""
    
    def __init__(self, param: str) -> None:
        """Initialize with parameter."""
        self.param = param
    
    async def process_data(
        self,
        data: List[Dict[str, Any]],
        option: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process data with optional configuration.
        
        Args:
            data: List of data items to process
            option: Optional processing option
            
        Returns:
            Processed results
        """
        # Implementation here
        return {"processed": len(data)}
```

## Contributing

### Types of Contributions

1. **Bug Fixes** - Report and fix issues
2. **Features** - Add new functionality
3. **Documentation** - Improve docs
4. **Performance** - Optimize existing code
5. **Tests** - Improve test coverage

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Add** tests
5. **Run** all tests and quality checks
6. **Submit** a pull request

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Code Review Guidelines

1. **Review** all changes carefully
2. **Test** the changes if possible
3. **Provide** constructive feedback
4. **Approve** only when satisfied

## Architecture Overview

### Core Components

1. **MCP Server** - Main server exposing tools via MCP protocol
2. **Agent Frameworks** - Multi-agent system with dynamic routing
3. **Voice System** - TTS/ASR with multi-provider support
4. **Memory System** - Advanced memory with Mem0 integration
5. **Platform Clients** - GitLab, Firecrawl, Browser automation
6. **LLM Router** - Unified LLM access with intelligent routing

### Design Patterns

- **Async/Await** - All I/O operations are asynchronous
- **Factory Pattern** - For creating clients and integrations
- **Strategy Pattern** - For provider selection
- **Observer Pattern** - For event handling

### Configuration

Configuration is managed through:

1. **Environment Variables** - For secrets and deployment config
2. **Config Files** - For structured configuration
3. **Runtime Config** - For dynamic updates

## Performance Considerations

### Optimization Guidelines

1. **Async Operations** - Use async for all I/O
2. **Caching** - Implement caching for expensive operations
3. **Batching** - Batch API calls when possible
4. **Connection Pooling** - Reuse connections
5. **Memory Management** - Clean up resources properly

### Monitoring

Use the built-in monitoring tools:

```python
# Enable performance monitoring
from src.core.monitoring import PerformanceMonitor

monitor = PerformanceMonitor()
with monitor.measure("operation_name"):
    # Your code here
    pass
```

## Troubleshooting

### Common Issues

#### Voice System Not Working

```bash
# Check voice models
ls models/voice/

# Test voice system
python -c "from src.voice.manager import VoiceManager; asyncio.run(VoiceManager().test())"

# Reinstall models
python scripts/download_voice_models.py --force
```

#### Database Connection Issues

```bash
# Check database URL
echo $DATABASE_URL

# Test connection
python scripts/test_db.py

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### Import Errors

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall in development mode
pip install -e .

# Check dependencies
pip check
```

### Getting Help

1. **Check** the documentation
2. **Search** existing issues
3. **Create** a new issue with details
4. **Join** our Discord community

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export LOG_LEVEL=DEBUG
```

## Development Tips

### Productivity Tools

1. **Pre-commit Hooks** - Auto-format and lint on commit
2. **IDE Configuration** - Use provided settings
3. **Docker Dev Environment** - Consistent development setup

### Hot Reload

For rapid development:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Enable hot reload
python -m src.mcp.server --reload
```

### Debugging

Use the built-in debugger:

```python
from src.core.debug import debug_breakpoint

debug_breakpoint()  # Pauses execution
```

## Release Process

### Version Management

We use semantic versioning:

- **MAJOR** - Breaking changes
- **MINOR** - New features
- **PATCH** - Bug fixes

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Create release tag
5. Build and publish packages

## Security

### Security Guidelines

1. **Never** commit secrets or API keys
2. **Use** environment variables for sensitive data
3. **Validate** all inputs
4. **Follow** OWASP guidelines
5. **Run** security scans regularly

### Reporting Security Issues

Email security@yourorg.com with details.

## License

This project is licensed under the MIT License. See LICENSE.md for details.

## Acknowledgments

Thanks to all contributors who make this project possible!

---

For more information, visit our [GitHub repository](https://github.com/your-org/vibe-mcp) or [documentation site](https://vibe-mcp.readthedocs.io).
