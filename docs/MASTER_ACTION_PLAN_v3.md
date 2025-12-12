# 🚀 MASTER ACTION PLAN v3.0: VIBE MCP

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│      ╔═╗ ╦ ╔╗ ╔═╗                                          │
│      ╚╗║ ║ ╠╩╗║╣    MCP                                    │
│      ╚═╝ ╩ ╚═╝╚═╝                                          │
│                                                             │
│      Visual Intelligence Builder Environment                │
│      Model Context Protocol                                 │
│                                                             │
│      "You vibe it. We build it."                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Executive Summary

Transform **AI Project Synthesizer** → **VIBE MCP** - a **100% agent-driven autonomous development platform**:
- **Agents execute ALL CLI commands** - Users never touch the terminal
- **Multi-framework orchestration** - AutoGen, OpenAI Swarm, LangGraph, CrewAI + existing LangChain/n8n
- **Full voice loop** - GLM-ASR (input) + Piper TTS (output)
- **Intelligent memory** - Mem0 for persistent context
- **Unified LLM access** - LiteLLM routing across 100+ providers

---

## 📊 Technology Stack

| Category | Technology | Purpose | Status |
|----------|------------|---------|--------|
| **Voice Input** | GLM-ASR | Speech recognition (1.5B, beats Whisper V3) | 🔲 NEW |
| **Voice Output** | Piper TTS | Local neural TTS (<100ms) | 🔲 NEW |
| **Memory** | Mem0 | Long-term memory (26% better than OpenAI) | 🔲 NEW |
| **LLM Routing** | LiteLLM | Unified API (100+ providers) | 🔲 NEW |
| **CLI Execution** | AgentCLI | Agent-driven commands | 🔲 NEW |
| **Multi-Agent** | AutoGen | Complex conversations, code review | 🔲 NEW |
| **Fast Handoffs** | OpenAI Swarm | Lightweight routing | 🔲 NEW |
| **Stateful Workflows** | LangGraph | Cycles, branches, checkpoints | 🔲 NEW |
| **Team Collaboration** | CrewAI | Role-based agent teams | 🔲 NEW |
| **Web Research** | Firecrawl | LLM-ready web scraping | 🔲 NEW |
| **Browser Control** | Browser-Use | Browser automation | 🔲 NEW |
| **RAG/Tools** | LangChain | Document processing | ✅ EXISTS |
| **Visual Workflows** | n8n | Webhooks, external APIs | ✅ EXISTS |
| **MCP Server** | FastMCP | Tool server | ✅ EXISTS |

---

## 🎯 Implementation Phases

### Phase 1: Core Agent Infrastructure (Week 1-2) ⭐⭐⭐

| Task | Files | Description |
|------|-------|-------------|
| 1.1 CLI Executor | `src/cli/executor.py` | Safe command execution with error detection |
| 1.2 Error Recovery | `src/cli/error_recovery.py` | Auto-fix common errors, retry logic |
| 1.3 AgentCLI | `src/cli/agent_interface.py` | High-level semantic methods for agents |
| 1.4 Command Library | `config/commands/*.yaml` | Git, Python, Docker, Node.js commands |

**Key Features:**
- Execution modes: LOCAL, DOCKER, WSL, REMOTE
- Blocked dangerous commands (rm -rf /, format, etc.)
- Error patterns: DEPENDENCY_MISSING, PERMISSION_DENIED, VERSION_CONFLICT
- Auto-recovery: pip install, sudo, git config

### Phase 2: Voice Integration (Week 2-3) ⭐⭐⭐

| Task | Files | Description |
|------|-------|-------------|
| 2.1 GLM-ASR Engine | `src/voice/asr_engine.py` | Speech-to-text (1.5B params) |
| 2.2 Piper TTS Engine | `src/voice/tts_engine.py` | Text-to-speech (local, <100ms) |
| 2.3 Voice Agent | `src/agents/voice_agent.py` | Integrate ASR/TTS |
| 2.4 Voice Config | `config/voice.yaml` | Templates, settings |

**GLM-ASR Capabilities:**
- Mandarin, Cantonese, English support
- Low-volume speech robustness
- 4.10 avg error rate (SOTA)
- HuggingFace: `zai-org/GLM-ASR-Nano-2512`

**Piper TTS Features:**
- 100+ voices, 25+ languages
- GPU acceleration (CUDA)
- Voice templates: task_start, task_complete, error, question

### Phase 3: Agent Framework Integration (Week 3-4) ⭐⭐⭐

| Task | Files | Description |
|------|-------|-------------|
| 3.1 AutoGen | `src/agents/autogen_integration.py` | Multi-agent conversations |
| 3.2 Swarm | `src/agents/swarm_integration.py` | Lightweight handoffs |
| 3.3 LangGraph | `src/agents/langgraph_integration.py` | Stateful workflows |
| 3.4 CrewAI | `src/agents/crewai_integration.py` | Role-based teams |
| 3.5 Framework Router | `src/agents/framework_router.py` | Dynamic selection |

**Framework Selection Logic:**
```
Simple task → Swarm (fast)
Complex design/review → AutoGen (debate)
Multi-step with state → LangGraph (checkpoints)
Team collaboration → CrewAI (roles)
External integrations → n8n (webhooks)
RAG/Search → LangChain (tools)
```

### Phase 4: Memory & LLM (Week 4-5) ⭐⭐⭐

| Task | Files | Description |
|------|-------|-------------|
| 4.1 Mem0 Integration | `src/memory/mem0_integration.py` | Advanced memory |
| 4.2 LiteLLM Router | `src/llm/litellm_router.py` | Unified LLM access |
| 4.3 Memory MCP | `src/mcp_server/memory_tools.py` | MCP tools for memory |

**Mem0 Memory Categories:**
- User preferences (theme, style, tools)
- Project decisions (tech stack, architecture)
- Code patterns (frameworks, testing)
- Error solutions (what worked)

**LiteLLM Routing:**
```
simple → ollama/llama3.1 (free)
coding → claude-sonnet (quality)
reasoning → claude-opus/o1 (deep)
fast → groq/llama-70b (<100ms)
```

### Phase 5: Platform Integrations (Week 5-6) ⭐⭐

| Task | Files | Description |
|------|-------|-------------|
| 5.1 GitLab Client | `src/discovery/gitlab_client.py` | Full GitLab API |
| 5.2 Firecrawl | `src/research/firecrawl_client.py` | Web scraping |
| 5.3 Browser-Use | `src/automation/browser_agent.py` | Browser automation |

### Phase 6: Testing & Docs (Week 6-7) ⭐⭐

| Task | Files | Description |
|------|-------|-------------|
| 6.1 Integration Tests | `tests/integration/` | All new integrations |
| 6.2 E2E Voice Tests | `tests/e2e/test_voice.py` | Full voice loop |
| 6.3 Documentation | `docs/` | Update all guides |

---

## 🏗️ Architecture Overview

```
USER INPUT (Voice/Chat/Web/MCP/Webhook)
           │
           ▼
┌──────────────────────────────────────┐
│       MASTER COORDINATOR AGENT       │
│  Intent Parser → Task Decomposer →   │
│  Framework Selector → Progress Track │
└──────────────────────────────────────┘
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
┌────────┐ ┌────────┐ ┌────────┐
│  MEM0  │ │LITELLM │ │CHROMA  │
│ Memory │ │ Router │ │Vectors │
└────────┘ └────────┘ └────────┘
           │
           ▼
┌──────────────────────────────────────┐
│    FRAMEWORK ORCHESTRATION LAYER     │
│  AutoGen │ Swarm │ LangGraph │ n8n  │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│      SPECIALIST AGENTS (16+)         │
│  Architect │ Coder │ Tester │ DevOps │
│  Docs │ Debug │ Security │ Research │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│        CLI EXECUTION LAYER           │
│  AgentCLI → CLIExecutor → Recovery   │
│  LOCAL │ DOCKER │ WSL │ REMOTE       │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│        VOICE OUTPUT (Piper TTS)      │
│  "Done! Created 12 files..."         │
└──────────────────────────────────────┘
```

---

## 📦 Dependencies to Add

```txt
# requirements-agents.txt

# Agent Frameworks
pyautogen>=0.2.0
openai-swarm>=0.1.0
langgraph>=0.1.0
crewai>=0.1.0

# Voice
piper-tts>=1.0.0
sounddevice>=0.4.6
torchaudio>=2.0.0

# Memory
mem0ai>=0.1.0

# LLM Routing
litellm>=1.0.0

# Web Research
firecrawl-py>=0.1.0
browser-use>=0.1.0

# GitLab
python-gitlab>=4.0.0
```

---

## ✅ Success Criteria

1. **Voice Loop**: User speaks → GLM-ASR transcribes → Agent executes → Piper speaks result
2. **Zero Terminal**: All CLI commands executed by agents, users never touch terminal
3. **Smart Routing**: Framework router selects optimal framework per task
4. **Memory Persistence**: Mem0 remembers preferences, decisions, solutions
5. **Error Recovery**: Auto-fix 80%+ of common CLI errors
6. **Multi-Framework**: AutoGen, Swarm, LangGraph working together seamlessly

---

## 🚀 Quick Start (After Implementation)

```python
from src.agents.framework_router import get_framework_router
from src.voice.asr_engine import GLMASREngine
from src.voice.tts_engine import agent_speak

# Voice input
asr = GLMASREngine()
user_request = asr.transcribe("recording.wav")

# Route and execute
router = get_framework_router()
result = await router.route_and_execute(user_request)

# Voice output
agent_speak(template="task_complete", summary=result["summary"])
```

---

## 📋 Checklist

- [ ] Phase 1: CLI Executor, Error Recovery, AgentCLI
- [ ] Phase 2: GLM-ASR, Piper TTS, Voice Agent
- [ ] Phase 3: AutoGen, Swarm, LangGraph, Framework Router
- [ ] Phase 4: Mem0, LiteLLM Router
- [ ] Phase 5: GitLab, Firecrawl, Browser-Use
- [ ] Phase 6: Tests, Documentation
- [ ] **Phase 7: REBRAND → VIBE MCP** 🎉

---

## 🎨 Phase 7: Rebrand to VIBE MCP (Final Phase)

### Brand Identity

**VIBE MCP** = **V**isual **I**ntelligence **B**uilder **E**nvironment + **M**odel **C**ontext **P**rotocol

| Aspect | Value |
|--------|-------|
| **Identity** | "Vibe coder" brand - this IS you |
| **Memorable** | One word everyone knows + MCP |
| **Backronym** | Actually meaningful, not forced |
| **Ecosystem** | Ties directly to Model Context Protocol |
| **Searchable** | "VIBE MCP" is unique, won't get lost |
| **Verb-able** | "Just VIBE it" / "Let VIBE handle it" |

### The Backronym Breakdown

```
V isual      → Dashboard, TUI, voice feedback, diagrams
I ntelligence → 14 AI agents, 6 frameworks, Mem0 memory
B uilder     → Creates complete applications autonomously  
E nvironment → Full dev platform (CLI, Docker, testing, deploy)

MCP          → Model Context Protocol (the standard we build on)
```

### Taglines

- **"You vibe it. We build it."** (Primary)
- "From vibes to production."
- "Speak your vision. Ship your code."

### Rebranding Tasks

| Task | Description | Status |
|------|-------------|--------|
| 7.1 | Rename repo to `vibe-mcp` | 🔲 |
| 7.2 | Update all imports from `ai_synthesizer` → `vibe_mcp` | 🔲 |
| 7.3 | Update `pyproject.toml` with new name | 🔲 |
| 7.4 | Update README.md with new branding | 🔲 |
| 7.5 | Update MCP server name | 🔲 |
| 7.6 | Create logo assets | 🔲 |
| 7.7 | Update all documentation | 🔲 |
| 7.8 | Push to https://github.com/Ghenghis/vibe-mcp | 🔲 |

### File Renames

```
AI_Synthesizer/           →  vibe-mcp/
├── src/                  →  src/vibe_mcp/
├── ai-project-synthesizer (MCP name) → vibe-mcp
└── pyproject.toml [name] →  "vibe-mcp"
```

### Package Updates

```toml
# pyproject.toml
[project]
name = "vibe-mcp"
description = "Visual Intelligence Builder Environment - Model Context Protocol"

[project.scripts]
vibe = "vibe_mcp.cli:main"
vibe-mcp = "vibe_mcp.mcp.server:main"
```

### New CLI Commands

```bash
# After rebrand
vibe init           # Initialize new project
vibe build          # Build with agents
vibe deploy         # Deploy to cloud
vibe-mcp serve      # Start MCP server
```

---

## 🏆 Final Vision

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   USER: "Hey VIBE, build me a FastAPI app with auth"       │
│                                                             │
│   🎤 GLM-ASR transcribes voice                             │
│   🧠 Master Coordinator analyzes intent                     │
│   🔀 Framework Router selects AutoGen (complex task)        │
│   👥 Agent team: Architect → Coder → Tester → DevOps       │
│   ⚡ AgentCLI executes: git, pip, docker, pytest           │
│   💾 Mem0 remembers preferences for next time              │
│   🔊 Piper TTS: "Done! Your FastAPI app is ready."         │
│                                                             │
│   Total time: 3 minutes. Zero terminal interaction.         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Last Updated: December 2025*
*Version: 3.0*
*Future Name: VIBE MCP*
*Repo: https://github.com/Ghenghis/vibe-mcp*
