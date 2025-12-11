# 🏛️ AI Project Synthesizer - Architecture Documentation

> **Version:** 2.0.0  
> **Last Updated:** December 2024  
> **Status:** Production Ready  
> **Tests:** 245+ Passing

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [Layer Descriptions](#layer-descriptions)
4. [AI Agents Architecture](#ai-agents-architecture)
5. [Voice System Architecture](#voice-system-architecture)
6. [Real-Time Event System](#real-time-event-system)
7. [Memory & Persistence](#memory--persistence)
8. [Data Flow](#data-flow)
9. [Component Interactions](#component-interactions)
10. [Technology Stack](#technology-stack)
11. [Deployment Architecture](#deployment-architecture)
12. [Security Architecture](#security-architecture)

---

## System Overview

### Purpose

The AI Project Synthesizer is designed to solve the "cold start" problem in software development by automating:

1. **Research** - Finding relevant open-source projects
2. **Analysis** - Understanding code structure and dependencies
3. **Synthesis** - Combining code from multiple sources
4. **Documentation** - Generating comprehensive project docs

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Local-First** | Prioritize local LLM inference for cost efficiency |
| **Modular** | Each component can be replaced or upgraded independently |
| **Extensible** | New platforms and tools can be added via plugins |
| **Observable** | Comprehensive logging and metrics throughout |
| **Resilient** | Graceful degradation when services are unavailable |

---

## Core Architecture

### High-Level System Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              WINDSURF IDE                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           CASCADE AI                                  │  │
│  │                    (Natural Language Interface)                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    │ MCP Protocol (stdio)                   │
│                                    ▼                                        │
├────────────────────────────────────────────────────────────────────────────┤
│                        AI PROJECT SYNTHESIZER                               │
│                           (MCP Server)                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         MCP INTERFACE LAYER                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │  │
│  │  │    Tools    │  │  Resources  │  │   Prompts   │                   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      ORCHESTRATION LAYER                              │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                    Pipeline Coordinator                          │ │  │
│  │  │         (Manages multi-step synthesis workflows)                 │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐                       │
│  │DISCOVERY│ANALYSIS │RESOLUTION│SYNTHESIS│GENERATION│                      │
│  │  Layer  │  Layer  │  Layer  │  Layer  │  Layer  │                       │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘                       │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         LLM ORCHESTRATION                             │  │
│  │  ┌───────────────────────┐  ┌───────────────────────┐                │  │
│  │  │     Local (Ollama)    │  │   Cloud (Fallback)    │                │  │
│  │  │   Qwen2.5-Coder-14B   │  │  OpenAI / Anthropic   │                │  │
│  │  └───────────────────────┘  └───────────────────────┘                │  │
│  │                    ▲                                                  │  │
│  │                    │ RouteLLM (Intelligent Routing)                   │  │
│  │                    ▼                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       INFRASTRUCTURE LAYER                            │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                  │  │
│  │  │  Cache  │  │  Queue  │  │   Logs  │  │ Metrics │                  │  │
│  │  │ (Redis) │  │(BullMQ) │  │(Winston)│  │(Prometheus)│               │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  External APIs  │      │   File System   │      │   Git Repos     │
│  GitHub, HF, etc│      │  Project Output │      │   Cloned Repos  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## Layer Descriptions

### 1. MCP Interface Layer

**Purpose:** Expose synthesizer capabilities to Windsurf via Model Context Protocol

**Components:**

| Component | Description | Implementation |
|-----------|-------------|----------------|
| **Tools** | Callable functions for synthesis operations | FastMCP `@mcp.tool()` |
| **Resources** | Readable data like cached analyses | FastMCP `@mcp.resource()` |
| **Prompts** | Pre-defined prompt templates | FastMCP `@mcp.prompt()` |

**Key Files:**
- `src/mcp_server/server.py` - Server initialization
- `src/mcp_server/tools.py` - Tool definitions (8 tools)
- `src/mcp_server/resources.py` - Resource handlers
- `src/mcp_server/prompts.py` - Prompt templates

### 2. Orchestration Layer

**Purpose:** Coordinate multi-step synthesis workflows

**Responsibilities:**
- Parse user intent into actionable steps
- Manage execution order and dependencies
- Handle errors and retries
- Track progress and status

**State Machine:**

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌───────────┐
│  IDLE   │────▶│DISCOVERING│────▶│ANALYZING │────▶│ RESOLVING │
└─────────┘     └──────────┘     └──────────┘     └───────────┘
                                                        │
┌─────────┐     ┌──────────┐     ┌──────────┐          │
│ COMPLETE│◀────│GENERATING│◀────│SYNTHESIZING│◀───────┘
└─────────┘     └──────────┘     └──────────┘
```

### 3. Discovery Layer

**Purpose:** Find and rank relevant repositories across platforms

**Supported Platforms:**

| Platform | API Library | Rate Limit | Auth Required |
|----------|-------------|------------|---------------|
| GitHub | `ghapi` | 5,000/hr | Yes (token) |
| GitLab | `python-gitlab` | 300/min | Yes (token) |
| HuggingFace | `huggingface_hub` | Generous | Optional |
| Kaggle | `kaggle` | Undocumented | Yes (key) |
| arXiv | `arxiv` | 3s delay | No |
| Papers with Code | `paperswithcode-client` | Undocumented | No |
| Semantic Scholar | `semanticscholar` | 1 RPS | Optional |

**Ranking Algorithm:**

```python
score = (
    stars_normalized * 0.15 +
    recency_score * 0.20 +
    activity_score * 0.15 +
    documentation_score * 0.10 +
    test_coverage_score * 0.10 +
    compatibility_score * 0.30
)
```

### 4. Analysis Layer

**Purpose:** Deep understanding of code structure and dependencies

**Tools Used:**

| Tool | Purpose | Languages |
|------|---------|-----------|
| **Tree-sitter** | AST parsing | 100+ languages |
| **LibCST** | Python concrete syntax | Python |
| **ast-grep** | Structural search | Multi-language |
| **pipdeptree** | Python dep graphs | Python |
| **Knip** | JS/TS unused deps | JavaScript/TypeScript |
| **Semgrep** | Security patterns | Multi-language |

**Analysis Outputs:**

```yaml
analysis_result:
  repository: "owner/repo"
  language_breakdown:
    python: 65%
    javascript: 30%
    other: 5%
  dependencies:
    direct: 24
    transitive: 156
    conflicts: 2
  code_metrics:
    lines_of_code: 15420
    cyclomatic_complexity: 4.2
    test_coverage: 78%
  extractable_components:
    - name: "auth_module"
      files: ["src/auth/*"]
      dependencies: ["bcrypt", "jwt"]
    - name: "api_layer"
      files: ["src/api/*"]
      dependencies: ["fastapi", "pydantic"]
```

### 5. Resolution Layer

**Purpose:** Resolve dependency conflicts between repositories

**Strategy:**

```
┌─────────────────────────────────────────────────────────────┐
│                   DEPENDENCY RESOLUTION                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. COLLECT                                                  │
│     ├── requirements.txt from Repo A                         │
│     ├── requirements.txt from Repo B                         │
│     └── pyproject.toml from Repo C                          │
│                                                              │
│  2. ANALYZE                                                  │
│     ├── Build unified dependency graph                       │
│     ├── Identify version conflicts                           │
│     └── Check transitive dependencies                        │
│                                                              │
│  3. RESOLVE (using uv SAT solver)                           │
│     ├── Find satisfying version set                          │
│     ├── Apply constraints from all sources                   │
│     └── Generate locked requirements                         │
│                                                              │
│  4. VALIDATE                                                 │
│     ├── Verify all imports resolve                           │
│     ├── Check for runtime conflicts                          │
│     └── Generate compatibility report                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6. Synthesis Layer

**Purpose:** Merge code from multiple repositories into unified project

**Process:**

1. **Clone** - Download selected repositories
2. **Extract** - Pull only needed components
3. **Transform** - Rename conflicts, update imports
4. **Merge** - Combine into unified structure
5. **Scaffold** - Apply project template

**Key Tools:**

| Tool | Purpose |
|------|---------|
| `git-filter-repo` | Extract subdirectories with history |
| `Mergiraf` | AST-aware merge conflict resolution |
| `Copier` | Project scaffolding with templates |
| `Repomix` | Package repos for AI analysis |

### 7. Generation Layer

**Purpose:** Create comprehensive documentation automatically

**Generated Artifacts:**

| Artifact | Generator | Format |
|----------|-----------|--------|
| README.md | readme-ai | Markdown |
| ARCHITECTURE.md | LLM + templates | Markdown |
| API_REFERENCE.md | pdoc/TypeDoc | Markdown |
| architecture.mermaid | Kroki | Mermaid |
| dependency_graph.svg | pydeps/madge | SVG |
| data_flow.mermaid | LLM analysis | Mermaid |

---

## Data Flow

### Synthesis Pipeline Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                                  │
│  "Build an AI document analyzer with OCR and vector search"         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INTENT PARSING (LLM)                            │
│  Extract: components needed, constraints, preferences                │
│  Output: StructuredIntent                                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DISCOVERY                                    │
│  Input: StructuredIntent                                             │
│  Process: Query GitHub, HF, Kaggle, Papers                          │
│  Output: CandidateRepositories[]                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          ANALYSIS                                    │
│  Input: CandidateRepositories[]                                      │
│  Process: AST parse, dependency analysis, quality scoring           │
│  Output: AnalyzedRepositories[]                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      COMPATIBILITY CHECK                             │
│  Input: AnalyzedRepositories[]                                       │
│  Process: Cross-reference dependencies, find conflicts              │
│  Output: CompatibilityMatrix, Conflicts[]                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        RESOLUTION                                    │
│  Input: Conflicts[], AllDependencies                                 │
│  Process: SAT solver (uv), version negotiation                      │
│  Output: ResolvedDependencies, UnifiedRequirements                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SYNTHESIS                                    │
│  Input: SelectedRepos[], ExtractionConfig, ResolvedDeps             │
│  Process: Clone, extract, transform, merge, scaffold                │
│  Output: SynthesizedProject/                                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GENERATION                                    │
│  Input: SynthesizedProject/                                          │
│  Process: Generate README, diagrams, API docs                       │
│  Output: DocumentedProject/                                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         OUTPUT                                       │
│  Complete project ready for Windsurf development                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Language** | Python | 3.11+ | Primary implementation |
| **MCP SDK** | FastMCP | 1.0+ | MCP server framework |
| **Package Manager** | uv | 0.9+ | Fast dependency resolution |
| **AST Parsing** | Tree-sitter | 0.25+ | Multi-language parsing |
| **Local LLM** | Ollama | Latest | LLM serving |
| **Code Model** | Qwen2.5-Coder | 14B | Code understanding |

### External Services

| Service | Purpose | Required |
|---------|---------|----------|
| GitHub API | Repository search | Yes |
| Ollama | Local LLM inference | Yes |
| HuggingFace | Model/dataset search | No |
| Kaggle | Dataset search | No |
| OpenAI/Anthropic | Cloud LLM fallback | No |

---

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Windsurf IDE                            │   │
│  │                    │                                 │   │
│  │                    │ MCP (stdio)                     │   │
│  │                    ▼                                 │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │        AI Project Synthesizer               │   │   │
│  │  │            (Python Process)                 │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                    │                                 │   │
│  │         ┌──────────┴──────────┐                     │   │
│  │         ▼                     ▼                     │   │
│  │  ┌─────────────┐      ┌─────────────┐              │   │
│  │  │   Ollama    │      │   Redis     │              │   │
│  │  │  (GPU LLM)  │      │  (Cache)    │              │   │
│  │  └─────────────┘      └─────────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Docker Deployment

```yaml
# docker-compose.yml structure
services:
  synthesizer:
    build: .
    depends_on:
      - redis
      - ollama
    volumes:
      - ./output:/app/output
      
  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
            
  redis:
    image: redis:alpine
```

---

## Security Architecture

### API Key Management

```
┌─────────────────────────────────────────────────────────────┐
│                   SECRETS MANAGEMENT                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  .env (local)           Environment Variables               │
│       │                        │                             │
│       ▼                        ▼                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Config Loader                           │   │
│  │         (src/core/config.py)                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                    │
│         ┌───────────────┼───────────────┐                   │
│         ▼               ▼               ▼                   │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐             │
│  │  GitHub   │   │HuggingFace│   │   Cloud   │             │
│  │   Token   │   │   Token   │   │  API Keys │             │
│  └───────────┘   └───────────┘   └───────────┘             │
│                                                              │
│  NEVER: Hardcoded │ In logs │ In git │ In outputs          │
└─────────────────────────────────────────────────────────────┘
```

### Rate Limiting

All external API calls are rate-limited to prevent abuse:

| Service | Limit | Implementation |
|---------|-------|----------------|
| GitHub | 5000/hr | Token bucket |
| arXiv | 1 req/3s | Fixed delay |
| Local LLM | 10 concurrent | Semaphore |

---

## Next Steps

See the following documentation for more details:

- [API Reference](api/API_REFERENCE.md)
- [Development Guide](guides/DEVELOPMENT.md)
- [Deployment Guide](guides/DEPLOYMENT.md)
- [Contributing](../CONTRIBUTING.md)
