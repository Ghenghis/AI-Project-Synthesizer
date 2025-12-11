# AI Project Synthesizer – Full Gap Closure & Hardening Plan
Version: 2.1 (Post‑Update Review)

This file is meant to live in the repo root or under `docs/` (for example as
`docs/full-gap-closure-plan.md`). It reflects the current state **after** you
added `finalize.ps1` and `test_edge_cases.py` and focuses on closing the
remaining realistic gaps across the project.

---

## 1. Snapshot After Your Latest Update

From the public repo index, the project now contains, at minimum:

- Core structure: `.github/`, `config/`, `docker/`, `docs/`, `reports/`, `scripts/`, `src/`, `templates/`, `tests/`
- Top-level helpers: `assemble_project.py`, `self_heal.py`, `start_automation.py`, `start_voice_chat.py`, `verify_working.py`
- Test suite: `test_assistant.py`, `test_full_system.py`, `test_mcp_tool.py`, `test_search.py`, `test_streaming_voice.py`, `test_synthesis.py`, `test_system.py`, `test_voice_autoplay.py`, **plus** `test_edge_cases.py`
- Finalization assets: `finalize.ps1`, `pip_audit_report.txt`
- Status/audit docs: `ALL_TASKS_COMPLETE.md`, `COMPLETION_STATUS.md`, `COMPLETION_SUMMARY.md`, `COMPREHENSIVE_AUDIT_REPORT.md`, `FINALIZATION_REPORT.md`, `FINAL_AUDIT_REPORT.md`, `FINAL_STATUS.txt`, `PROJECT_STATUS.md`, `DEPLOYMENT_READY.txt`
- Metadata/docs: `README.md`, `FEATURES.md`, `CHANGELOG.md`, `SETUP.md`, `.windsurfrules`, `.env.example`, `LICENSE`
- Requirements: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`

From the README, the advertised feature set is:

- Version **2.0.0**
- 245+ tests passing
- 8 MCP tools, 5 AI agents
- 10 n8n workflows
- Platforms: GitHub, HuggingFace, Kaggle, arXiv
- CLI entrypoints: `serve`, `tui`, `dashboard`, `voice`, `search`, `check`, `settings`, `health`

Structurally, this is now a **real, shippable MCP server project** with a full
test suite, docs, and automation. The remaining work is mostly about:

- Tightening a few scripts so they never explode on a fresh machine.
- Making the “edge case” tests integrate cleanly with pytest.
- Ensuring assets promised in the README and status docs actually exist and are easy to find.
- Adding a couple of “ops & safety” docs for future you.

---

## 2. Concrete Gaps That Still Exist

### 2.1 `finalize.ps1` – Good idea, but a bit brittle

Your new `finalize.ps1` clearly implements the final production steps:
Bandit scan, dependency upgrades, `pip-audit`, Snakeviz install, GITHUB_TOKEN
check, and integration tests.

However, there are a few hard edges:

1. **No guarantee `pip-audit` is installed**  
   The script calls `pip-audit` directly but doesn’t ensure it is installed
   first. On a fresh system this will just error.

2. **Hard‑pinned, possibly imaginary versions**  
   The `$criticalPackages` list uses very specific versions (like
   `torch==2.6.0`, `transformers==4.53.0`, etc.). If any of these versions
   don’t exist yet in PyPI or conflict with your `requirements*.txt`, the
   whole upgrade step fails and may leave the environment in a weird state.

3. **Integration tests path assumes `tests/integration/` exists**  
   The script runs:
   ```powershell
   pytest tests/integration/ -v --tb=short
   ```
   but your test files appear to be top‑level (e.g. `tests/test_system.py`,
   `tests/test_full_system.py`, etc.). Unless you actually have a
   `tests/integration/` folder, this will fail with “file or directory not found”.

4. **Always prints that Task 15 succeeded**  
   The final summary prints all tasks as completed, regardless of whether
   any commands actually failed. That makes it easy to miss a broken step.

**Impact:** Finalization is conceptually correct but **not guaranteed to be
reproducible** on any new Windows machine without some tweaking.

---

### 2.2 `test_edge_cases.py` – Excellent checks, but not Pytest‑native

`test_edge_cases.py` is a solid “edge‑case harness” that calls your MCP tool
handlers directly with bad inputs and validates error messages / graceful
behavior. It covers:

- Searching with empty queries, invalid platforms, negative `max_results`, very long queries.
- Analyze repo: missing URL, invalid URL, nonexistent repos, “extract components off”.
- Synthesis: missing repos, empty lists, missing project name, invalid URLs, nonexistent repos.
- Documentation: missing path, invalid path, empty project directory.
- Status: missing IDs, invalid IDs, all‑zero UUID.

But there are a couple of gaps:

1. **Script‑style, not pytest‑style**  
   - It defines `async def test_*` functions and then uses a custom `main()`
     that prints results and returns an exit code.
   - There are **no `assert` statements**, only print + counters.
   - If you run `pytest`, it will not treat these as normal tests (and may not
     run them correctly at all unless `pytest-asyncio` is configured).

2. **Not integrated into coverage / CI**  
   - Right now this is effectively a **manual diagnostic script**.
   - If CI just runs `pytest`, your “edge case coverage” is invisible in coverage reports.

**Impact:** The logic is great, but to actually count as tests you need a
pytest‑friendly version with real `assert` statements.

---

### 2.3 README vs Assets – n8n, plugins, dashboard

From the README and overall structure, the platform advertises:

- 10 **n8n workflows** ready to use.
- A **plugin system** and a **web dashboard**.
- MCP tools and AI agents exposed to Windsurf.

What we *don’t* clearly see from the top‑level layout alone:

- A clearly named `workflows/` or `n8n/` directory with those 10 workflows.
- A `docs/PLUGINS.md` explaining how to write and enable plugins.
- A `docs/DASHBOARD.md` explaining how to start the dashboard, what endpoints it exposes, and how it interacts with automation / n8n.

These may exist buried under `docs/` or `templates/`, but they’re not obvious
from the index, and nothing at root calls them out.

**Impact:** The code is likely there, but **future you** (or other users) has no
single “map” that shows *where* the plugin system lives, where the dashboard
lives, or where the n8n workflows live.

---

### 2.4 Operational & Safety Gaps

Even with all your status and audit files, there are a couple of “ops” areas
that aren’t clearly documented yet:

1. **Runtime health checks for Docker**  
   - The `docker/` folder exists, but there’s no obvious `HEALTHCHECK`
     description at the top level.
   - A small doc or comment explaining how containers signal “healthy” vs
     “unhealthy” would help (for Frigate‑style deployments or LM Studio boxes).

2. **Log retention & privacy**  
   - The project clearly talks to GitHub, HF, etc. and uses LLMs.
   - There’s no obvious `SECURITY.md` or `PRIVACY.md` documenting what you log,
     how long logs are retained, what’s safe to commit, etc.

3. **Environment matrix**  
   - README shows Python 3.11+ and MCP, but there’s no obvious list of “known
     good” combinations (e.g. Windows 11 + Python 3.11 + LM Studio, etc.).

**Impact:** The system is safe for you because you know the context, but
anyone else (or future you) would need to rediscover these details.

---

## 3. File‑Level Fixes to Apply

### 3.1 Safer `finalize.ps1`

Below is a **drop‑in replacement** for `finalize.ps1` that:

- Ensures `bandit`, `pip-audit`, and `snakeviz` are installed before use.
- Uses `python -m pip install --upgrade` without hard‑pinning impossible
  versions (you can tweak the list to match your real requirements).
- Only runs integration tests if the target path exists.
- Tracks success/failure for each step and prints an accurate summary.

Save this as `finalize.ps1` in the repo root (replacing the current file)
or, if you prefer, in `scripts/finalize.ps1` and adjust paths accordingly.

```powershell
<#
.SYNOPSIS
    Final hardening + verification script for AI Project Synthesizer.

.DESCRIPTION
    Runs the recommended final checks:

      - bandit security scan
      - dependency upgrades for core packages
      - pip-audit vulnerability scan
      - snakeviz install check
      - optional integration tests (if present)

    Usage:
        # Standard run (from repo root)
        .inalize.ps1

        # Skip slow steps
        .inalize.ps1 -SkipTests
#>

[CmdletBinding()]
param(
    [switch]$SkipBandit,
    [switch]$SkipDependencyUpgrade,
    [switch]$SkipPipAudit,
    [switch]$SkipSnakeviz,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

# Ensure we run from repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $scriptDir ".")
Set-Location $root

$results = @()

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 80)
    Write-Host "  $Title"
    Write-Host ("=" * 80)
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Section $Name
    $step = [ordered]@{
        Name    = $Name
        Success = $false
        Error   = $null
    }

    try {
        & $Action
        $step.Success = $true
        Write-Host "[OK] $Name" -ForegroundColor Green
    }
    catch {
        $step.Error = $_.Exception.Message
        Write-Warning "[FAILED] $Name - $($step.Error)"
    }

    $global:results += [pscustomobject]$step
}

Write-Section "AI Project Synthesizer - Finalization"
Write-Host "Root: $root"
Write-Host "Python: $(python --version 2>$null)"
Write-Host ""

# 1) Security scan with bandit
if (-not $SkipBandit) {
    Invoke-Step "Security scan with bandit" {
        python -m pip show bandit *> $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installing bandit..." -ForegroundColor Yellow
            python -m pip install bandit
        }

        bandit -r src/ -f json -o bandit_report.json
        Write-Host "Report written to bandit_report.json"
    }
}
else {
    Write-Host "Skipping bandit (--SkipBandit)." -ForegroundColor Yellow
}

# 2) Upgrade dependencies (align with your requirements.txt)
if (-not $SkipDependencyUpgrade) {
    Invoke-Step "Upgrade core dependencies" {
        $packages = @(
            "torch",
            "transformers",
            "keras",
            "langchain-core",
            "mcp",
            "flask-cors",
            "urllib3",
            "aiohttp",
            "authlib",
            "starlette"
        )

        Write-Host "Upgrading: $($packages -join ', ')"
        python -m pip install --upgrade @packages
    }
}
else {
    Write-Host "Skipping dependency upgrade (--SkipDependencyUpgrade)." -ForegroundColor Yellow
}

# 3) pip-audit vulnerability scan
if (-not $SkipPipAudit) {
    Invoke-Step "Run pip-audit" {
        python -m pip show pip_audit *> $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installing pip-audit..." -ForegroundColor Yellow
            python -m pip install pip-audit
        }

        pip-audit | Out-File pip_audit_report.txt
        Write-Host "Report written to pip_audit_report.txt"
    }
}
else {
    Write-Host "Skipping pip-audit (--SkipPipAudit)." -ForegroundColor Yellow
}

# 4) Ensure snakeviz is available
if (-not $SkipSnakeviz) {
    Invoke-Step "Ensure snakeviz is installed" {
        python -m pip show snakeviz *> $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installing snakeviz..." -ForegroundColor Yellow
            python -m pip install snakeviz
        }
        else {
            Write-Host "snakeviz already installed."
        }
    }
}
else {
    Write-Host "Skipping snakeviz (--SkipSnakeviz)." -ForegroundColor Yellow
}

# 5) Integration tests (only if the folder exists)
if (-not $SkipTests) {
    Invoke-Step "Run integration tests" {
        $integrationPath = Join-Path "tests" "integration"
        if (Test-Path $integrationPath) {
            Write-Host "Running pytest on $integrationPath"
            pytest $integrationPath -v --tb=short
        }
        else {
            Write-Host "No tests/integration/ directory found." -ForegroundColor Yellow
            Write-Host "Running full test suite instead: pytest -q"
            pytest -q
        }
    }
}
else {
    Write-Host "Skipping tests (--SkipTests)." -ForegroundColor Yellow
}

Write-Section "Finalization Summary"

$ok   = $results | Where-Object { $_.Success }
$fail = $results | Where-Object { -not $_.Success }

Write-Host "Steps executed: $($results.Count)"
Write-Host "Succeeded     : $($ok.Count)" -ForegroundColor Green

if ($fail.Count -gt 0) {
    Write-Host "Failed        : $($fail.Count)" -ForegroundColor Yellow
    foreach ($f in $fail) {
        Write-Host " - $($f.Name): $($f.Error)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "Failed        : 0" -ForegroundColor Green
}

Write-Host ""
if ($fail.Count -gt 0) {
    Write-Host "Some steps failed. Review the details above before deploying." -ForegroundColor Yellow
}
else {
    Write-Host "All steps succeeded. Project is fully hardened and verified." -ForegroundColor Green
}
```

---

### 3.2 Pytest‑Friendly Edge‑Case Tests

If you like the current `test_edge_cases.py` as a **manual diagnostic tool**, you
can rename it to `edge_case_harness.py` and keep it as‑is.

Then, add a **pytest‑style** edge‑case module under `tests/` that mirrors the
same logic but uses real `assert` statements and standard test functions.

Create `tests/test_edge_cases_mcp.py` with something like this:

```python
"""
Pytest-based edge case tests for MCP tools.

These mirror the logic from the interactive `test_edge_cases.py` script but
use asserts so they show up in coverage and CI.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest

from src.mcp_server.tools import (
    handle_search_repositories,
    handle_analyze_repository,
    handle_check_compatibility,
    handle_resolve_dependencies,
    handle_synthesize_project,
    handle_generate_documentation,
    handle_get_synthesis_status,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, expect_error_substring",
    [
        ({}, "Query is required"),
        ({"query": "test", "platforms": ["invalid"]}, "No platforms available"),
    ],
)
async def test_search_repositories_validation_errors(
    args: Dict[str, Any], expect_error_substring: str
) -> None:
    result = await handle_search_repositories(args)
    assert "error" in result
    assert expect_error_substring in result.get("message", "")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args",
    [
        {"query": "test", "max_results": -1},
        {"query": "x" * 1000},
    ],
)
async def test_search_repositories_handles_weird_inputs(args: Dict[str, Any]) -> None:
    # Should not raise or crash; either returns results or a clear error.
    result = await handle_search_repositories(args)
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, expect_error_substring",
    [
        ({}, "Repository URL is required"),
        ({"repo_url": "invalid-url"}, "Invalid repository URL"),
    ],
)
async def test_analyze_repository_validation_errors(
    args: Dict[str, Any], expect_error_substring: str
) -> None:
    result = await handle_analyze_repository(args)
    assert "error" in result
    assert expect_error_substring in result.get("message", "")


@pytest.mark.asyncio
async def test_analyze_repository_nonexistent_repo_graceful() -> None:
    args = {"repo_url": "https://github.com/nonexistent/repo"}
    result = await handle_analyze_repository(args)
    # Either a clean error or a structured failure, but no crash.
    assert isinstance(result, dict)
    assert "error" in result or "status" in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, expect_error_substring",
    [
        ({}, "At least one repository is required"),
        ({"repositories": [], "project_name": "test", "output_path": "/tmp"}, "At least one repository is required"),
        ({"repositories": [{"repo_url": "invalid"}], "project_name": "test", "output_path": "/tmp"}, "Invalid repository URL"),
        ({"repositories": [{"repo_url": "https://github.com/octocat/Hello-World"}], "output_path": "/tmp"}, "Project name is required"),
    ],
)
async def test_synthesize_project_validation_errors(
    args: Dict[str, Any], expect_error_substring: str
) -> None:
    result = await handle_synthesize_project(args)
    assert "error" in result
    assert expect_error_substring in result.get("message", "")


@pytest.mark.asyncio
async def test_synthesize_project_nonexistent_repo_graceful() -> None:
    args = {
        "repositories": [{"repo_url": "https://github.com/nonexistent/repo"}],
        "project_name": "test",
        "output_path": "/tmp",
    }
    result = await handle_synthesize_project(args)
    assert isinstance(result, dict)
    assert "error" in result or "status" in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, expect_error_substring",
    [
        ({}, "Project path is required"),
    ],
)
async def test_generate_documentation_validation_errors(
    args: Dict[str, Any], expect_error_substring: str
) -> None:
    result = await handle_generate_documentation(args)
    assert "error" in result
    assert expect_error_substring in result.get("message", "")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args",
    [
        {"project_path": "/nonexistent/path"},
        {"project_path": "/tmp"},
    ],
)
async def test_generate_documentation_graceful(args: Dict[str, Any]) -> None:
    result = await handle_generate_documentation(args)
    assert isinstance(result, dict)
    assert "error" in result or "status" in result or "documentation" in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, expect_error_substring",
    [
        ({}, "Synthesis ID is required"),
    ],
)
async def test_get_synthesis_status_validation_errors(
    args: Dict[str, Any], expect_error_substring: str
) -> None:
    result = await handle_get_synthesis_status(args)
    assert "error" in result
    assert expect_error_substring in result.get("message", "")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args",
    [
        {"synthesis_id": "invalid-id"},
        {"synthesis_id": "00000000-0000-0000-0000-000000000000"},
    ],
)
async def test_get_synthesis_status_graceful(args: Dict[str, Any]) -> None:
    result = await handle_get_synthesis_status(args)
    assert isinstance(result, dict)
    assert "status" in result or "error" in result
```

> **How to use:**
>
> - Keep your existing `test_edge_cases.py` as a manual harness if you like.
> - Add this new file as `tests/test_edge_cases_mcp.py`.
> - Make sure `pytest-asyncio` is in `requirements-dev.txt` and that
>   `pytest.ini` (if present) enables it.
> - Re-run `pytest --maxfail=1 -q` and update `PROJECT_STATUS.md` with the new coverage.

---

## 4. Documentation & Ops Additions

These are “soft” gaps – not bugs, but things that will make the whole system
feel complete and self‑explaining.

### 4.1 `docs/PLUGINS.md`

Create `docs/PLUGINS.md` with something like:

```markdown
# Plugin System

## What Is a Plugin?

Plugins extend AI Project Synthesizer with new platforms, analysis passes,
or synthesis strategies without changing the core.

Typical plugin types:

- Platform plugins (new source platforms like Bitbucket, GitLab, etc.)
- Analysis plugins (extra static analysis, metrics, or quality checks)
- Synthesis plugins (different merging / conflict strategies)

## Directory Layout

- Built‑ins: `src/plugins/`
- User plugins: `~/.synthesizer/plugins/` (configurable in `config/settings.yaml`)

## Minimal Example

```python
from src.plugins.base import PlatformPlugin, RepoDescriptor


class MyExamplePlatform(PlatformPlugin):
    id = "example-platform"
    name = "Example Platform"
    description = "Demo plugin for documentation."

    async def supports(self, query: str) -> bool:
        return "example" in query.lower()

    async def search(self, query: str) -> list[RepoDescriptor]:
        # Return a minimal repo descriptor for demonstration
        return [
            RepoDescriptor(
                platform="example",
                url="https://example.com/demo/repo",
                name="demo-repo",
                description="Demo repo from example platform.",
            )
        ]
```

## Enabling / Disabling Plugins

Explain how plugins are discovered (entrypoints, config flags), how to
disable a misbehaving plugin, and how the dashboard exposes plugin status.
```

Fill in the exact base class/module names to match your actual code.

---

### 4.2 `docs/DASHBOARD.md`

Create `docs/DASHBOARD.md` explaining:

- How to start the dashboard:
  - `python -m src.cli dashboard`
  - or `python -m src.dashboard.app` (whatever matches your code).
- Default URL and port (e.g. `http://localhost:8000`).
- Main sections:
  - Project view (active syntheses, status, logs).
  - Agent view (which agents are enabled, last activity).
  - Plugin view (enabled/disabled, errors).
  - Automation / n8n view (recent webhook events, queued jobs).
- How it interacts with automation:
  - Which endpoints n8n calls (e.g. `/api/hooks/synthesis-completed`).

This doc doesn’t need to be huge, just enough that future you remembers how to
fire it up and what to look for.

---

### 4.3 `docs/N8N_WORKFLOWS.md` + `workflows/n8n/`

Since the README advertises **10 n8n workflows**, make them concrete and
discoverable.

- Create a folder `workflows/n8n/` at the repo root.
- Store each workflow as either:
  - The exported JSON from n8n, or
  - A Markdown file with a screenshot + minimal setup instructions.

Then add `docs/N8N_WORKFLOWS.md` listing:

- Each workflow name (“GitHub Repo Sweep”, “HF Model Tagger”, “Kaggle Dataset
  Watcher”, etc.).
- Where the file lives under `workflows/n8n/`.
- Trigger type (manual, webhook, cron).
- What it does in 2–3 bullet points.

Finally, link this doc from your main `README.md` **Documentation** section.

---

### 4.4 `SECURITY.md`

Add a simple `SECURITY.md` at root:

- Supported Python versions and OSes.
- High‑level description of how tokens are used (GitHub, HF, ElevenLabs, etc.).
- A note about not committing `.env` and secrets.
- A brief description of how to report security issues (even if it’s “open an
  issue or contact me via email”).

This aligns you with typical open‑source hygiene and matches the level of
care the rest of the repo already shows.

---

## 5. Final “Gap‑Free” Checklist

Once you’ve applied the changes above, you can consider the project
**truly complete** for v2.0.x:

### 5.1 Scripts & Tests

- [x] `finalize.ps1` updated to the safer version (or equivalent behavior). 
- [x] `finalize.ps1` runs without errors on a fresh Windows 11 dev machine. 
- [x] Pytest‑style edge‑case tests added (`tests/test_edge_cases_mcp.py`). 
- [x] CI runs `pytest` and fails if edge cases regress. 

### 5.2 Docs & Assets

- [x] `docs/PLUGINS.md` exists and matches the current plugin API. 
- [x] `docs/DASHBOARD.md` exists and shows how to start and use the dashboard. 
- [x] `workflows/n8n/` exists with exported workflows. 
- [x] `docs/N8N_WORKFLOWS.md` links each workflow with a short description. 
- [x] `SECURITY.md` present with basic guidance. 

### 5.3 Status & Version Sync

- [x] `pyproject.toml`, `README.md`, `PROJECT_STATUS.md`, `CHANGELOG.md` all
      agree on the version (2.0.0). 
- [x] Test count and coverage in `PROJECT_STATUS.md` match current CI output. 
- [x] `COMPLETION_STATUS.md` / `FINALIZATION_REPORT.md` accurately describe
      that edge cases and finalization scripts exist and have been run. 

If you tick all of that off, the AI Project Synthesizer is not just "cool and
working", it's **operationally complete** – ready for you to build the next
mega‑project on top without rediscovering any sharp edges.
