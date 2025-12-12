# Windsurf Integration Guide

This project turns **Windsurf** into a guarded, MCP-aware Vibe Coding cockpit wired to local models (via LM Studio or other backends) and MCP tools.

The goal: you open this repo in Windsurf, run one start script, and immediately have:
- MCP tools online
- Local models reachable  
- Guardrails + project rules active for the AI

---

## 1. Prerequisites

- **Windows 11** (primary target; Linux/macOS possible with minor script changes)
- **Windsurf IDE** installed and updated
- **Docker** (for any containerized MCP / backend services)
- **LM Studio** or other local LLM runner (optional but recommended)
- Git + Node/Python as required by your tooling stack

---

## 2. Repo Pieces Windsurf Uses

These are the key parts of the repo that matter for Windsurf:

- `templates/workspace-rules/` 
  - Contains **global** and **project-level** `.windsurfrules` files
  - Teaches Windsurf how to "vibe code" inside this ecosystem:
    - Architecture summary
    - Coding standards and style preferences
    - Safety and quality requirements

- `docs/` (audits, architecture, MCP tools list, etc.)
  - `COMPLETE-MCP-TOOLS-LIST.md` 
  - `HOW-IT-ALL-WORKS-TOGETHER.md` 
  - `DOCUMENTATION-MASTER-PLAN.md` 
  - These give Windsurf (and you) a single source of truth about:
    - Available MCP tools
    - How MCP, LM Studio, and the quality gates fit together

- **Start scripts** (Windows-first)
  - `tools/start_vibe_win.ps1` 
  - `tools/start_mcp_only.ps1` 
  - `tools/start_simple.ps1` 
  - These one-click scripts:
    - Start the MCP server(s)
    - Launch or connect to LM Studio / local models
    - Export env vars and ports so Windsurf can call tools immediately

- **Connectivity tests**
  - `tests/tools/test_lmstudio.py`
  - `tests/tools/test_mcp_connectivity.py`
  - Quick checks to confirm:
    - MCP server is reachable
    - Local models are responding
    - Basic MCP tool calls work

---

## 3. Quick Start in Windsurf

### 1. Clone the repo
```bash
git clone https://github.com/Ghenghis/vibe-mcp
cd vibe-mcp
```

### 2. Open in Windsurf
- File → Open Folder… and select this repo
- Let Windsurf index the project

### 3. Activate workspace rules
Copy the appropriate `.windsurfrules` from:
- `templates/workspace-rules/global.windsurfrules`
- `templates/workspace-rules/project.windsurfrules`

Place them at:
- `~/.windsurfrules` (for global rules, optional)
- `<repo-root>/.windsurfrules` (for this project)

### 4. Start the environment (Windows)
In a PowerShell terminal at the repo root:
```powershell
.\tools\start_vibe_win.ps1
```

This should:
- Start MCP services
- Connect or launch LM Studio / local models
- Print which ports and endpoints Windsurf can use
- Run connectivity tests

### 5. Verify connectivity
From the repo root:
```powershell
python tests/tools/test_lmstudio.py
python tests/tools/test_mcp_connectivity.py
```

You should see successful responses before doing deeper coding sessions.

---

## 4. Using Windsurf with MCP

Once the environment is running:

### In Windsurf, use the agent / chat panel:
Ask it to run structured tasks like:
- "Scan this repo and summarize the architecture using MCP tools."
- "Refactor this module following the project style from .windsurfrules."
- "Generate tests for this module and update the test suite."

The MCP tools list and rules file will nudge it toward the correct flows.

### For bigger changes:
Use commands like:
- "Propose a patch for X, respecting linting and quality gates."
- "Generate tests for this module and update the test suite."
- "Use the CLI executor to run these commands safely."

The workspace rules describe:
- Preferred languages / frameworks
- Testing / linting expectations
- Security assumptions

### If something breaks:
Rerun the connectivity tests:
```powershell
python tests/tools/test_mcp_connectivity.py
```

Check that the start script is still running (no crash, no port conflict).

---

## 5. Recommended Workflow

### Start session
1. Run `.\tools\start_vibe_win.ps1`
2. Confirm MCP + models are up
3. Open repo in Windsurf
4. Ensure `.windsurfrules` is present and loaded

### Let Windsurf scan the repo
Ask for an up-to-date architecture summary.
Confirm MCP tools appear in its tool list (if supported).

### Do focused, rule-driven coding
Always frame tasks with:
- "Respect project architecture and .windsurfrules."
- "Use minimal, well-scoped changes with explanations."
- "Use the CLI executor for any command operations."

### Close session
Stop MCP / Docker services when you're done.

---

## 6. VIBE MCP Specific Features

### CLI Executor Integration
Windsurf can now use the VIBE MCP CLI executor for safe command execution:
- Ask: "Use the CLI executor to install these packages"
- The executor will handle error recovery automatically
- All commands are tracked and logged

### Memory System
Leverage the persistent memory system:
- "Remember that I prefer FastAPI over Flask"
- "What did we learn about the previous error?"
- Context is automatically retrieved for tasks

### Quality Gates
Built-in quality enforcement:
- Automatic linting with ruff/mypy
- Security scanning
- Test generation and validation

---

## 7. Next Steps

- Add per-stack rules to `.windsurfrules` (Python, JS/TS, PowerShell, etc.)
- Hook Windsurf prompts directly into your quality gate (lint + tests + security)
- Gradually replace ad-hoc scripts with consolidated `src/` modules from the MCP architecture plan
- Integrate voice commands through GLM-ASR when Phase 2 is complete
