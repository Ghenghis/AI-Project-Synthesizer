# AI Project Synthesizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **The Ultimate AI-Powered Vibe Coder** - Transform natural language into production-ready applications with multi-agent AI, voice interaction, and intelligent automation.

## Project Scale

| Metric | Count | Description |
|--------|-------|-------------|
| Source Files | 141+ | Python modules across 27 packages |
| Classes | 461+ | Dataclasses, enums, OOP classes |
| Functions | 1,888+ | Async and sync functions |
| Modules | 27 | Major feature categories |
| Agent Frameworks | 4 | AutoGen, CrewAI, LangGraph, Swarm |
| LLM Providers | 6+ | OpenAI, Anthropic, xAI, Gemini, Ollama, LM Studio |
| Voice Engines | 2 | ElevenLabs TTS, GLM ASR |
| Platforms | 5+ | GitHub, HuggingFace, Kaggle, GitLab, Firecrawl |

## What Is This Project?

AI Project Synthesizer is a comprehensive Vibe Coding platform that:

1. **Understands your intent** - Describe what you want in natural language
2. **Searches multiple platforms** - Finds code from GitHub, HuggingFace, Kaggle
3. **Analyzes codebases** - Parses AST, maps dependencies, scores quality
4. **Resolves conflicts** - Uses SAT solvers to merge dependencies
5. **Synthesizes projects** - Combines components into working projects
6. **Generates documentation** - Creates README, API docs, diagrams
7. **Speaks to you** - Real-time voice conversations
8. **Automates everything** - N8N workflows, scheduled tasks

## System Architecture

`mermaid
flowchart TB
    subgraph USER[User Interfaces]
        CLI[CLI - 23 commands]
        TUI[Terminal UI]
        VOICE[Voice Chat]
        MCP[MCP Server]
    end
    
    subgraph AGENTS[AI Agent Layer]
        CODE[Code Agent]
        RESEARCH[Research Agent]
        SYNTH[Synthesis Agent]
    end
    
    subgraph LLM[LLM Layer]
        ROUTER[LiteLLM Router]
        LOCAL[Ollama/LM Studio]
        CLOUD[OpenAI/Anthropic]
    end
    
    USER --> AGENTS
    AGENTS --> LLM
`

## Module Reference

### Agents (src/agents/) - 12 files, 37 classes, 172 functions

| Module | Description |
|--------|-------------|
| base.py | Foundation for all agents |
| code_agent.py | Code generation, review |
| research_agent.py | Multi-platform discovery |
| voice_agent.py | Voice interaction |
| synthesis_agent.py | Project assembly |
| autogen_integration.py | Multi-agent conversations |
| crewai_integration.py | Role-based teams |
| langgraph_integration.py | Stateful workflows |
| swarm_integration.py | Fast handoffs |
| framework_router.py | Dynamic framework selection |

### Vibe Coder (src/vibe/) - 11 files, 48 classes, 162 functions

| Module | Description |
|--------|-------------|
| prompt_enhancer.py | Enriches prompts with context |
| rules_engine.py | YAML-based coding rules |
| architect_agent.py | Creates architecture plans |
| task_decomposer.py | Breaks tasks into phases |
| context_manager.py | State tracking with Mem0 |
| auto_commit.py | Automated Git commits |
| auto_rollback.py | Checkpoint recovery |
| explain_mode.py | Code decision explanations |
| project_classifier.py | Project type identification |

### Discovery (src/discovery/) - 10 files, 49 classes, 189 functions

| Module | Description |
|--------|-------------|
| github_client.py | GitHub API search, clone |
| huggingface_client.py | HuggingFace models/datasets |
| kaggle_client.py | Kaggle competitions/datasets |
| gitlab_client.py | GitLab projects |
| unified_search.py | Multi-platform search |
| firecrawl_enhanced.py | Web scraping with caching |

### Analysis (src/analysis/) - 6 files, 17 classes, 64 functions

| Module | Description |
|--------|-------------|
| ast_parser.py | Tree-sitter AST parsing |
| dependency_analyzer.py | Dependency graphs |
| compatibility_checker.py | Version compatibility |
| quality_scorer.py | Code quality scoring |
| code_extractor.py | Component extraction |

### Voice (src/voice/) - 8 files, 18 classes, 84 functions

| Module | Description |
|--------|-------------|
| manager.py | Unified TTS/ASR interface |
| elevenlabs_client.py | 9+ voices, cloning |
| realtime_conversation.py | Continuous voice chat |
| streaming_player.py | Low-latency audio |

**Voices:** Rachel, Domi, Bella, Antoni, Josh, Adam, Sam, Elli, Arnold


### LLM (src/llm/) - 11 files, 32 classes, 89 functions

| Provider | Models | Type |
|----------|--------|------|
| Ollama | qwen2.5-coder, llama3, mistral | Local |
| LM Studio | Any GGUF model | Local |
| OpenAI | gpt-4o, o1-preview | Cloud |
| Anthropic | claude-sonnet-4 | Cloud |
| xAI | grok-3 | Cloud |
| Google | gemini-2.0-flash | Cloud |

### Memory (src/memory/) - 2 files, 5 classes, 42 functions

**Categories:** PREFERENCE, DECISION, PATTERN, ERROR_SOLUTION, CONTEXT, LEARNING, COMPONENT, WORKFLOW

### Quality (src/quality/) - 7 files, 28 classes, 90 functions

| Module | Description |
|--------|-------------|
| security_scanner.py | Semgrep + Bandit |
| lint_checker.py | Ruff, ESLint, MyPy |
| test_generator.py | Auto pytest/Jest |
| review_agent.py | Multi-agent review |
| quality_gate.py | Pass/fail with auto-fix |

### Automation (src/automation/) - 6 files, 19 classes, 97 functions

| Module | Description |
|--------|-------------|
| coordinator.py | Event-driven hub |
| n8n_client.py | N8N workflows |
| browser_client.py | Playwright automation |
| scheduler.py | Cron scheduling |

### Core (src/core/) - 22 files, 110 classes, 391 functions

| Module | Description |
|--------|-------------|
| config.py | Pydantic settings |
| resource_manager.py | Memory optimization |
| health.py | Health checks |
| circuit_breaker.py | Fault tolerance |
| security_utils.py | Input validation |
| exceptions.py | Error hierarchy |
| cache.py | Multi-level caching |

### Additional Modules

| Module | Files | Classes | Functions |
|--------|-------|---------|-----------|
| assistant/ | 3 | 10 | 42 |
| synthesis/ | 4 | 12 | 42 |
| resolution/ | 4 | 8 | 28 |
| generation/ | 3 | 4 | 29 |
| workflows/ | 4 | 14 | 40 |
| recipes/ | 3 | 6 | 9 |
| tui/ | 3 | 2 | 28 |
| dashboard/ | 6 | 15 | 83 |
| mcp_server/ | 3 | 0 | 35 |


### CLI Commands

`ash
ai-synthesizer search query --platforms github,huggingface
ai-synthesizer analyze https://github.com/user/repo
ai-synthesizer synthesize --repos repo1,repo2 --output ./project
ai-synthesizer docs ./project
ai-synthesizer tui
ai-synthesizer mcp-server
ai-synthesizer wizard
`

### MCP Server Tools

| Tool | Description |
|------|-------------|
| search_repositories | Multi-platform search |
| analyze_repository | Deep code analysis |
| synthesize_project | Combine repos |
| generate_documentation | Create docs |
| memory_add/search | Memory operations |
| voice_speak | Text-to-speech |

## Quick Start

`ash
git clone https://github.com/Ghenghis/AI-Project-Synthesizer.git
cd AI-Project-Synthesizer
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
python -m src.cli --help
`

## Environment Variables

`
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_HOST=http://localhost:11434
ELEVENLABS_API_KEY=...
GITHUB_TOKEN=ghp_...
`

## Voice Chat

`ash
python start_voice_chat.py --voice rachel
`

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation guide |
| [API Reference](docs/api-reference.md) | Complete API docs |
| [Tutorials](docs/tutorials.md) | Step-by-step guides |
| [Architecture](docs/architecture.md) | System design |
| [User Guide](docs/USER_GUIDE.md) | Full manual |
| [Vibe Coding](docs/VIBE_CODING_AUTOMATION.md) | Pipeline details |

## Testing

`ash
pytest tests/ -v
`

**Status:** 281+ tests passing

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE)

---

[Report Bug](https://github.com/Ghenghis/AI-Project-Synthesizer/issues) | [Request Feature](https://github.com/Ghenghis/AI-Project-Synthesizer/issues)
