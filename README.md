# AI Project Synthesizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

AI Project Synthesizer is an AI-powered **Vibe Coder** system that discovers, analyzes, merges, and generates projects from multiple sources (GitHub, HuggingFace, Kaggle, web scraping), with a multi-agent architecture, quality gates, memory, and voice interaction.

## Project Scale

- **Source files:** 141+
- **Classes:** 461+
- **Functions:** 1,888+
- **Major module groups:** 27

For a full auto-generated inventory, see:
- `scripts/feature_inventory.md`

## High-Level Architecture

```mermaid
flowchart TB
  subgraph UI[Entry Points]
    CLI[CLI]
    MCP[MCP Server (Windsurf IDE)]
    TUI[Terminal UI]
    VOICE[Voice Chat]
  end

  subgraph VIBE[Vibe Coding Pipeline]
    PE[Prompt Enhancer]
    ARCH[Architect Agent]
    TD[Task Decomposer]
    CTX[Context Manager]
    QG[Quality Gate]
    AC[Auto Commit]
    AR[Auto Rollback]
  end

  subgraph DISC[Discovery]
    GH[GitHub]
    HF[HuggingFace]
    KG[Kaggle]
    GL[GitLab]
    FC[Firecrawl]
  end

  subgraph ANA[Analysis]
    AST[AST Parser]
    DEP[Dependency Analyzer]
    QUAL[Quality Scorer]
    COMPAT[Compatibility Checker]
  end

  subgraph LLM[LLM Orchestration]
    ROUTER[Router]
    LOCAL[Local Models]
    CLOUD[Cloud Providers]
  end

  UI --> VIBE
  VIBE --> DISC
  DISC --> ANA
  VIBE --> LLM
  ANA --> VIBE
  ROUTER --> LOCAL
  ROUTER --> CLOUD
```

## What It Does (End-to-End)

- **Discovery**
  - Searches across platforms and scrapes documentation pages
  - Caches results and rate limits requests
- **Analysis**
  - Parses code using AST tooling
  - Builds dependency graphs and detects conflicts
  - Scores quality (tests/docs/maintenance)
- **Resolution + Synthesis**
  - Resolves dependency conflicts (including SAT-style strategies)
  - Assembles a synthesized output project
- **Generation**
  - Generates documentation and diagrams
- **Quality + Auto-Repair**
  - Runs lint/security checks and can attempt auto-fixes
  - Uses automated repair logic (see `src/core/auto_repair.py`)
- **Event Handling + Debugging**
  - Centralized lifecycle/health/telemetry utilities in `src/core/`

## Module Map (Top-Level)

The authoritative code is under `src/`.

- `src/agents/` - agent implementations (code/research/synthesis/voice)
- `src/vibe/` - the Vibe Coding pipeline components
- `src/discovery/` - GitHub/HF/Kaggle/GitLab/Firecrawl clients + unified search
- `src/analysis/` - AST parsing, dependency/compatibility/quality scoring
- `src/resolution/` - dependency conflict detection/resolution
- `src/synthesis/` - project assembly/scaffolding
- `src/generation/` - README/diagram generation
- `src/quality/` - lint/security/test generation + quality gate
- `src/memory/` - persistent memory store/integration
- `src/voice/` - ElevenLabs + realtime voice components
- `src/mcp/` and/or `src/mcp_server/` - MCP server + tools for IDE integration
- `src/dashboard/` - web dashboard routes/app
- `src/tui/` - terminal UI
- `src/core/` - configuration, security, caching, health, lifecycle, observability

## Quick Start

```bash
git clone https://github.com/Ghenghis/AI-Project-Synthesizer.git
cd AI-Project-Synthesizer

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

# Copy env template and fill in keys
copy .env.example .env

python -m src.cli --help
```

## Key Commands

```bash
# Multi-platform search
python -m src.cli search "fastapi auth" --limit 5

# Analyze a repo
python -m src.cli analyze https://github.com/user/repo --deep

# Synthesize a project
python -m src.cli synthesize --repos repo1,repo2 --output .\out

# Run MCP server
python -m src.mcp.server
```

## Documentation

- `docs/USER_GUIDE.md`
- `docs/VIBE_CODING_AUTOMATION.md`
- `docs/architecture.md`
- `docs/diagrams/DIAGRAMS.md`

## Contributing

See `CONTRIBUTING.md`.

## License

MIT
