# VIBE MCP User Guide

Welcome to the VIBE MCP (Visual Intelligence Builder Environment) user guide! This comprehensive guide will help you understand and use all the features of the VIBE MCP system.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Voice Interaction](#voice-interaction)
3. [Memory Management](#memory-management)
4. [Agent Frameworks](#agent-frameworks)
5. [Platform Integrations](#platform-integrations)
6. [MCP Tools](#mcp-tools)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Getting Started

### What is VIBE MCP?

VIBE MCP is an intelligent project synthesis system that combines:
- **Voice Interaction** - Natural language communication
- **Memory System** - Context-aware information storage
- **Multi-Agent Framework** - Intelligent task execution
- **Platform Integrations** - Connect to GitLab, web scraping, and browser automation
- **MCP Protocol** - Standardized tool access

### First-Time Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the System**
   ```bash
   python -m src.mcp.server
   ```

4. **Verify Installation**
   ```bash
   python scripts/test_system.py
   ```

## Voice Interaction

### Setting Up Voice

The voice system supports both local and cloud-based TTS/ASR:

#### Local Setup (Recommended)
```python
from src.voice.manager import VoiceManager

# Initialize with local providers
manager = VoiceManager()
await manager.initialize()

# Test voice
await manager.synthesize("Hello, VIBE MCP is ready!")
```

#### Cloud Setup
Add your API keys to `.env`:
```env
ELEVENLABS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Voice Commands

#### Basic Commands
- "Start listening" - Begin voice input
- "Stop listening" - End voice input
- "Repeat that" - Repeat last response
- "Change voice" - Switch TTS voice

#### Task Commands
- "Create a new project called [name]"
- "Search for [query] on GitLab"
- "Scrape the website [url]"
- "Remember that [information]"
- "What do you know about [topic]?"

#### Navigation Commands
- "Go to [section]" - Navigate in documentation
- "Open [file]" - Open specific file
- "Show me [information]" - Display specific data

### Voice Settings

#### Configure Voice
```python
# Change TTS provider
await manager.set_tts_provider("piper")  # or "elevenlabs"

# Change voice characteristics
await manager.configure_voice(
    speed=1.0,
    pitch=1.0,
    voice_id="specific_voice_id"
)
```

#### Voice Profiles
Create custom voice profiles:
```python
await manager.save_voice_profile(
    name="Professional",
    settings={
        "speed": 0.9,
        "pitch": 1.0,
        "voice_id": "professional_voice"
    }
)
```

## Memory Management

### Understanding Memory Types

The memory system organizes information into categories:

1. **Preferences** - User preferences and settings
2. **Decisions** - Project decisions and rationale
3. **Patterns** - Code patterns and solutions
4. **Error Solutions** - Fixes for common issues
5. **Context** - Current project context
6. **Learning** - New knowledge acquired
7. **Components** - Reusable components
8. **Workflows** - Process definitions

### Adding Memories

#### Via Voice
- "Remember that I prefer dark mode"
- "Save this as a pattern: use async/await for I/O"
- "Note this decision: we chose React for the frontend"

#### Via Code
```python
from src.memory.mem0_integration import MemorySystem

memory = MemorySystem()

# Add a memory
await memory.add(
    content="User prefers TypeScript over JavaScript",
    category="PREFERENCE",
    tags=["typescript", "preference"],
    importance=0.8
)
```

### Searching Memories

#### Voice Search
- "What do you know about React?"
- "Show me my project decisions"
- "Find patterns for error handling"

#### Code Search
```python
# Search by query
results = await memory.search(
    query="react components",
    limit=5,
    category="PATTERN"
)

# Get context for task
context = await memory.get_context_for_task(
    "Create a React component with TypeScript"
)
```

### Memory Analytics

View memory insights:
```python
# Get memory statistics
stats = await memory.get_statistics()

# Get insights
insights = await memory.get_memory_insights()

# Export memories
await memory.export_memories(
    format="json",
    file_path="memories_backup.json"
)
```

## Agent Frameworks

### Understanding Frameworks

VIBE MCP supports multiple agent frameworks, each optimized for different tasks:

1. **AutoGen** - Complex multi-agent conversations
2. **Swarm** - Lightweight agent handoffs
3. **LangGraph** - Stateful workflows
4. **CrewAI** - Role-based team collaboration

### Using Agents

#### Automatic Selection
The system automatically selects the best framework:
```python
from src.agents.framework_router import FrameworkRouter

router = FrameworkRouter()
framework = router.select_framework("Create a REST API")
```

#### Manual Selection
```python
# Use specific framework
result = await router.execute_with_framework(
    task="Design database schema",
    framework="autogen"
)
```

### Agent Workflows

#### Code Review Workflow
```python
# Multi-agent code review
agents = [
    {"role": "code_reviewer", "goal": "Review code quality"},
    {"role": "security_expert", "goal": "Check security issues"},
    {"role": "performance_analyst", "goal": "Analyze performance"}
]

result = await router.run_team_workflow(
    task="Review this Python code",
    agents=agents
)
```

#### Learning Workflow
```python
# Learn from documentation
await router.learn_from_docs(
    topic="FastAPI best practices",
    sources=["https://fastapi.tiangolo.com"]
)
```

## Platform Integrations

### GitLab Integration

#### Setup
```env
GITLAB_TOKEN=your_gitlab_token
GITLAB_URL=https://gitlab.com
```

#### Usage
```python
from src.discovery.gitlab_client import GitLabClient

client = GitLabClient()

# Search projects
projects = await client.search_projects(
    query="machine learning",
    limit=10
)

# Get project details
project = await client.get_project("group/project-name")

# Clone repository
await client.clone_repo(
    project_id,
    destination="./cloned_repo"
)
```

#### Voice Commands
- "Search GitLab for [query]"
- "Show me the project [name]"
- "Clone the repository [repo]"
- "Get analytics for [project]"

### Firecrawl Integration

#### Setup
```env
FIRECRAWL_API_KEY=your_firecrawl_key
```

#### Usage
```python
from src.discovery.firecrawl_client import FirecrawlClient

client = FirecrawlClient()

# Scrape a URL
content = await client.scrape_url(
    "https://example.com",
    formats=["markdown", "html"]
)

# Crawl a site
site_map = await client.map_site(
    "https://example.com",
    limit=50
)

# Batch scrape
urls = ["url1", "url2", "url3"]
contents = await client.batch_scrape(urls)
```

#### Voice Commands
- "Scrape the website [url]"
- "Map the site [url]"
- "Extract content from [url]"
- "Crawl all pages on [site]"

### Browser Automation

#### Usage
```python
from src.automation.browser_client import BrowserClient

async with BrowserClient() as browser:
    # Navigate
    await browser.goto("https://example.com")
    
    # Interact
    await browser.click("#submit-button")
    await browser.type_text("#input-field", "Hello World")
    
    # Screenshot
    await browser.screenshot(file_path="screenshot.png")
```

#### Voice Commands
- "Open [url] in browser"
- "Click the [element] button"
- "Type [text] in the [field]"
- "Take a screenshot"
- "Fill the form with [data]"

## MCP Tools

### Available Tools

The MCP server exposes these tools:

1. **Memory Tools**
   - `memory_add` - Add new memory
   - `memory_search` - Search memories
   - `memory_get` - Get specific memory
   - `memory_update` - Update existing memory
   - `memory_delete` - Delete memory
   - `memory_export` - Export memories

2. **Voice Tools**
   - `voice_speak` - Generate speech
   - `voice_listen` - Start listening
   - `voice_configure` - Configure voice settings

3. **Agent Tools**
   - `agent_execute` - Execute task with agent
   - `agent_create_team` - Create agent team
   - `agent_review_code` - Review code with agents

4. **Platform Tools**
   - `gitlab_search` - Search GitLab
   - `firecrawl_scrape` - Scrape website
   - `browser_automate` - Automate browser

### Using MCP Tools

#### Via MCP Client
```python
from mcp import Client

client = Client()

# Add memory
result = await client.call_tool(
    "memory_add",
    {
        "content": "Important information",
        "category": "CONTEXT",
        "tags": ["important"]
    }
)

# Generate speech
await client.call_tool(
    "voice_speak",
    {
        "text": "Hello from VIBE MCP",
        "provider": "piper"
    }
)
```

#### Via Voice
- "Add memory: [content]"
- "Search memories for [query]"
- "Execute task: [task description]"
- "Search GitLab: [query]"

## Advanced Features

### Custom Workflows

Create custom workflows:
```python
from src.workflows import WorkflowBuilder

builder = WorkflowBuilder("Code Review")

# Add steps
builder.add_step("analyze_code", agent="code_analyzer")
builder.add_step("check_security", agent="security_checker")
builder.add_step("optimize", agent="performance_optimizer")

# Execute workflow
result = await builder.run({"code": "..."})
```

### Plugin System

Create custom plugins:
```python
from src.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my_plugin")
    
    async def process(self, data):
        # Custom processing
        return processed_data

# Register plugin
plugin_manager.register(MyPlugin())
```

### Batch Operations

Process multiple items:
```python
# Batch memory operations
memories = [
    {"content": "Item 1", "category": "CONTEXT"},
    {"content": "Item 2", "category": "LEARNING"},
]

await memory.batch_add(memories)

# Batch scraping
urls = ["url1", "url2", "url3"]
contents = await firecrawl.batch_scrape(urls)
```

### Analytics and Reporting

Generate reports:
```python
# System usage report
report = await analytics.generate_usage_report(
    period="7d",
    format="pdf"
)

# Memory insights
insights = await memory.get_memory_insights()
print(f"Total memories: {insights['summary']['total_memories']}")
```

## Configuration

### Environment Variables

Complete list of configuration options:

```env
# Core
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/vibe_mcp

# Voice
VOICE_DEFAULT_PROVIDER=piper
VOICE_CACHE_DIR=./cache/voice
ELEVENLABS_API_KEY=your_key

# LLM
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
OLLAMA_HOST=http://localhost:11434

# Platforms
GITLAB_TOKEN=your_token
FIRECRAWL_API_KEY=your_key

# Performance
MAX_CONCURRENT_REQUESTS=10
CACHE_TTL=3600
```

### Custom Configuration

Create custom config files:
```python
# config/custom.py
CUSTOM_SETTINGS = {
    "voice": {
        "default_speed": 1.0,
        "auto_detect_language": True
    },
    "memory": {
        "auto_consolidate": True,
        "consolidation_interval": 3600
    }
}
```

## Troubleshooting

### Common Issues

#### Voice Not Working
```bash
# Check audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

# Test TTS
python -c "from src.voice.tts.piper_client import PiperTTSClient; asyncio.run(PiperTTSClient().test())"

# Test ASR
python -c "from src.voice.asr.glm_asr_client import GLMASRClient; asyncio.run(GLMASRClient().test())"
```

#### Memory Issues
```bash
# Check database connection
python scripts/test_db.py

# Reset memory system
python scripts/reset_memory.py

# Export/Import memories
python scripts/export_memories.py
python scripts/import_memories.py
```

#### Agent Framework Errors
```bash
# Check framework installation
python -c "import autogen; print('AutoGen installed')"
python -c "import swarm; print('Swarm installed')"

# Test framework router
python scripts/test_frameworks.py
```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m src.mcp.server
```

### Health Checks

Run system health check:
```bash
python scripts/health_check.py
```

## FAQ

### General

**Q: What are the system requirements?**
A: Python 3.11+, 8GB RAM, 10GB disk space. Optional GPU for faster AI processing.

**Q: Can I use VIBE MCP offline?**
A: Yes, with local TTS/ASR and Ollama for LLM, most features work offline.

**Q: How secure is my data?**
A: All data is stored locally by default. Cloud providers are optional and data is encrypted in transit.

### Voice

**Q: Can I use my own voice?**
A: Yes! Use the voice cloning tools to create a custom voice model.

**Q: What languages are supported?**
A: English is primary. Additional languages available through Piper models.

**Q: How accurate is speech recognition?**
A: GLM-ASR achieves 95%+ accuracy on clear speech. Accuracy varies with audio quality.

### Memory

**Q: How much data can I store?**
A: Limited by your database storage. Vector embeddings are ~1KB per memory.

**Q: Is my memory data private?**
A: Yes, all memory data is stored locally and never sent to external services.

**Q: Can I export my memories?**
A: Yes, use the export tool to download in JSON or CSV format.

### Agents

**Q: Which agent framework should I use?**
A: Use AutoGen for complex tasks, Swarm for simple handoffs, LangGraph for workflows, CrewAI for teams.

**Q: Can I create custom agents?**
A: Yes, use the plugin system to create custom agent behaviors.

### Integrations

**Q: Do I need API keys for all platforms?**
A: Only for platforms you want to use. Local alternatives available for most services.

**Q: Can I add new platform integrations?**
A: Yes, follow the integration pattern in `src/discovery/`.

## Tips and Best Practices

### Voice Interaction
- Speak clearly and at a moderate pace
- Use specific commands for better accuracy
- Configure voice settings for your environment

### Memory Management
- Tag memories for easy retrieval
- Regularly review and consolidate old memories
- Use categories to organize information

### Agent Usage
- Start with simple tasks to understand capabilities
- Provide clear, specific instructions
- Review agent outputs before applying

### Performance
- Use caching for frequently accessed data
- Batch operations when possible
- Monitor system resources

## Getting Help

### Resources
- **Documentation**: [docs/](./)
- **Examples**: [examples/](../examples/)
- **API Reference**: [api/](./API_REFERENCE.md)

### Community
- **Discord**: Join our community server
- **GitHub**: Report issues and contribute
- **Forums**: Ask questions and share experiences

### Support
- **Email**: support@vibe-mcp.org
- **Issue Tracker**: GitHub Issues
- **FAQ**: Check this guide first!

---

Thank you for using VIBE MCP! We're constantly improving the system. Your feedback helps us make it better.
