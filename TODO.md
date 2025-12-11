# AI Project Synthesizer - Action Plan & Interactive TODO

> **Last Updated:** 2024-12-11 | **Version:** 2.0.0 | **Coverage:** 28% → 80% target

---

## Priority Legend
- 🔴 **CRITICAL** - Blocking issues, must fix immediately
- 🟠 **HIGH** - Important for stability/usability
- 🟡 **MEDIUM** - Quality improvements
- 🟢 **LOW** - Nice to have, future enhancements

---

## Phase 1: Critical Fixes (This Week)

### 🔴 1.1 MCP Server Robustness & Tests

- [ ] **Fix circular import in MCP server**
  - File: `src/mcp_server/server.py`
  - Issue: `from mcp.server import Server` conflicts with local module
  - Fix: Use `from fastmcp import FastMCP` consistently
  - Verify: Import test passes without warnings

- [ ] **Add MCP server test suite**
  - Create: `tests/test_mcp_server.py`
  - Tests needed:
    - [ ] Server startup/shutdown
    - [ ] Each tool registration (8 tools)
    - [ ] Tool execution happy path
    - [ ] Tool execution error handling
    - [ ] Concurrent request handling

- [ ] **Add MCP tools test suite**
  - Create: `tests/test_mcp_tools.py`
  - Tests needed:
    - [ ] `search_repositories` - valid query, empty results, API error
    - [ ] `analyze_repository` - valid repo, invalid URL, timeout
    - [ ] `check_compatibility` - compatible repos, conflicts
    - [ ] `resolve_dependencies` - success, conflicts, circular deps
    - [ ] `synthesize_project` - full flow, partial failure
    - [ ] `generate_documentation` - all doc types
    - [ ] `get_synthesis_status` - valid ID, invalid ID
    - [ ] `get_platforms` - all platforms healthy

- [ ] **Fix synthesis job concurrency**
  - File: `src/mcp_server/tools.py`
  - Issue: `_synthesis_jobs` is global dict without locking
  - Options:
    - [ ] Add `threading.Lock` for simple fix
    - [ ] Move to Redis (matches docker stack)
  - Add test for concurrent job creation

### 🔴 1.2 Version & Metadata Consistency

- [ ] **Create single source of truth for version**
  - Create: `src/core/version.py` (already exists, verify it's used)
  - Update all files to import from this:
    - [ ] `pyproject.toml` - use dynamic versioning or sync script
    - [ ] `README.md` - Project Stats section
    - [ ] `PROJECT_STATUS.md` - metrics table (shows 1.1.0, should be 2.0.0)
    - [ ] `CHANGELOG.md` - latest entry

- [ ] **Fix placeholder URLs in pyproject.toml**
  ```toml
  # Current (wrong):
  Homepage = "https://github.com/yourusername/AI_Synthesizer"
  
  # Should be:
  Homepage = "https://github.com/Ghenghis/AI-Project-Synthesizer"
  ```

- [ ] **Create release checklist script**
  - Create: `scripts/release.py`
  - Automates:
    - [ ] Bump version in all files
    - [ ] Update CHANGELOG
    - [ ] Verify all URLs
    - [ ] Run tests
    - [ ] Create git tag

---

## Phase 2: Test Coverage (Next 2 Weeks)

### 🟠 2.1 Coverage Infrastructure

- [ ] **Add coverage badge to README**
  - Use: codecov.io or coveralls
  - Add badge after Tests badge

- [ ] **Update GitHub Actions workflow**
  - File: `.github/workflows/ci.yml`
  - Add:
    ```yaml
    - name: Run tests with coverage
      run: pytest --cov=src --cov-report=xml --cov-fail-under=80
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
    ```

- [ ] **Document current vs target coverage**
  - Update `PROJECT_STATUS.md`:
    ```markdown
    | Metric | Current | Target |
    |--------|---------|--------|
    | Test Coverage | 28% | 80% |
    ```

### 🟠 2.2 Priority Test Files (0% coverage currently)

- [ ] **src/mcp_server/server.py** - See 1.1 above
- [ ] **src/mcp_server/tools.py** - See 1.1 above
- [ ] **src/generation/readme_generator.py**
  - Create: `tests/test_readme_generator.py`
- [ ] **src/generation/diagram_generator.py**
  - Create: `tests/test_diagram_generator.py`
- [ ] **src/llm/ollama_client.py**
  - Create: `tests/test_ollama_client.py`
- [ ] **src/llm/lmstudio_client.py**
  - Create: `tests/test_lmstudio_client.py`

---

## Phase 3: Documentation Cleanup (This Month)

### 🟡 3.1 Verify All Doc Links

- [ ] **Audit README links**
  - [ ] `docs/API_REFERENCE.md` - exists and has content
  - [ ] `docs/architecture/ARCHITECTURE.md` - exists and has content
  - [ ] `docs/diagrams/DIAGRAMS.md` - exists and has content
  - [ ] `docs/guides/QUICK_START.md` - exists and has content
  - [ ] `docs/guides/USER_GUIDE.md` - exists and has content
  - [ ] `docs/guides/CONFIGURATION.md` - exists and has content
  - [ ] `docs/guides/CLI_REFERENCE.md` - exists and has content
  - [ ] `docs/guides/TROUBLESHOOTING.md` - exists and has content
  - [ ] `docs/MCP_SETUP_GUIDE.md` - exists and has content
  - [ ] `docs/MCP_CLIENT_SUPPORT.md` - exists and has content
  - [ ] `docs/ENTERPRISE_DEPLOYMENT.md` - exists and has content

- [ ] **Fix external doc URL**
  - `pyproject.toml` says: `Documentation = "https://ai-synthesizer.readthedocs.io"`
  - Options:
    - [ ] Deploy to ReadTheDocs, OR
    - [ ] Change to: `Documentation = "https://github.com/Ghenghis/AI-Project-Synthesizer/tree/master/docs"`

### 🟡 3.2 LM Studio vs Docker Story

- [ ] **Add Windows + LM Studio setup section to README**
  ```markdown
  ## Windows Setup (LM Studio)
  
  If you're on Windows with LM Studio (no Docker needed):
  
  1. Start LM Studio and load a model
  2. Enable the local server (default: http://localhost:1234)
  3. Run: `python -m src.cli serve`
  
  The synthesizer will auto-detect LM Studio.
  ```

- [ ] **Create LM Studio helper script**
  - Create: `scripts/start_with_lmstudio.ps1`
  - Features:
    - [ ] Check if LM Studio is running
    - [ ] Ping LM Studio API
    - [ ] Start MCP server with LM Studio as default
    - [ ] Show status

---

## Phase 4: UX Enhancements (Future)

### 🟢 4.1 Recipe System

- [ ] **Create recipes folder structure**
  ```
  recipes/
  ├── README.md
  ├── schema.json
  ├── story-mcp.yaml
  ├── ai-camera-stack.yaml
  ├── bar-map-toolkit.yaml
  └── web-scraper.yaml
  ```

- [ ] **Define recipe schema**
  ```yaml
  # recipes/story-mcp.yaml
  name: Story MCP Server
  description: Build a story-focused MCP server
  version: 1.0.0
  
  sources:
    - repo: https://github.com/example/story-engine
      extract: [src/story/, src/characters/]
    - repo: https://github.com/example/mcp-template
      extract: [src/mcp/]
  
  synthesis:
    strategy: selective
    output_name: story-mcp-server
    template: mcp-server
  
  post_synthesis:
    - generate_readme
    - generate_api_docs
  ```

- [ ] **Add CLI commands**
  - [ ] `synth recipe list` - List available recipes
  - [ ] `synth recipe show <name>` - Show recipe details
  - [ ] `synth recipe run <name>` - Execute recipe
  - [ ] `synth recipe create` - Interactive recipe creator

### 🟢 4.2 Wizard Mode

- [ ] **Create wizard TUI command**
  - Add: `python -m src.cli wizard`
  - Steps:
    1. Project type selection (API, Desktop, MCP, CLI)
    2. Tech stack selection (Python, Node, React, etc.)
    3. Example repo suggestions
    4. Customization options
    5. Synthesis execution

- [ ] **Implement with Textual**
  - Create: `src/tui/wizard.py`
  - Use forms, selections, progress bars

### 🟢 4.3 Plugin System

- [ ] **Create plugin architecture**
  ```
  plugins/
  ├── __init__.py
  ├── base.py          # Plugin base class
  ├── registry.py      # Plugin discovery/loading
  ├── hooks.py         # Hook definitions
  └── examples/
      ├── custom_ranker.py
      └── story_specializer.py
  ```

- [ ] **Define hook points**
  - `before_discovery` - Modify search queries
  - `after_discovery` - Filter/rank results
  - `before_synthesis` - Pre-process repos
  - `after_synthesis` - Post-process output
  - `on_repo_selected` - Custom repo handling

- [ ] **Add plugin config**
  ```json
  // config/plugins.json
  {
    "enabled": ["custom_ranker", "story_specializer"],
    "settings": {
      "custom_ranker": {"weight_stars": 0.3}
    }
  }
  ```

### 🟢 4.4 Windows Packaging

- [ ] **Create build script**
  - Create: `scripts/build_windows.ps1`
  - Steps:
    - [ ] Create clean venv
    - [ ] Install dependencies
    - [ ] Run tests
    - [ ] Build with PyInstaller
    - [ ] Create zip package
    - [ ] Generate installer (optional)

- [ ] **PyInstaller spec file**
  - Create: `ai_synthesizer.spec`
  - Include all data files, configs

### 🟢 4.5 Observability Dashboard

- [ ] **Create minimal web dashboard**
  - Extend: `src/dashboard/app.py`
  - New routes:
    - [ ] `/dashboard/jobs` - Synthesis job history
    - [ ] `/dashboard/platforms` - Platform health
    - [ ] `/dashboard/llm` - LLM provider status
    - [ ] `/dashboard/metrics` - Timing/performance

- [ ] **Simple HTML templates**
  - Create: `src/dashboard/templates/`
  - Use: Jinja2 + minimal CSS

---

## Quick Reference: File Locations

| Task | Primary File(s) |
|------|-----------------|
| MCP Server | `src/mcp_server/server.py`, `src/mcp_server/tools.py` |
| Version | `src/core/version.py`, `pyproject.toml` |
| Tests | `tests/test_*.py` |
| CI/CD | `.github/workflows/ci.yml` |
| Docs | `docs/**/*.md`, `README.md` |
| Recipes | `recipes/*.yaml` |
| Plugins | `plugins/*.py` |
| TUI | `src/tui/*.py` |
| Dashboard | `src/dashboard/*.py` |

---

## Progress Tracking

### Phase 1: Critical Fixes
```
[░░░░░░░░░░] 0% - Not started
```

### Phase 2: Test Coverage  
```
[██░░░░░░░░] 28% - Current baseline
```

### Phase 3: Documentation
```
[████████░░] 80% - Most docs exist, need verification
```

### Phase 4: UX Enhancements
```
[░░░░░░░░░░] 0% - Future work
```

---

## Commands to Run

```bash
# Check current coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_mcp_server.py -v

# Verify all imports work
python -c "from src.mcp_server.server import mcp"

# Check version consistency
python -c "from src.core.version import __version__; print(__version__)"

# Validate all doc links exist
python scripts/validate_docs.py
```

---

## Next Actions (Pick One)

1. **Start with MCP server tests** → Create `tests/test_mcp_server.py`
2. **Fix version consistency** → Update `PROJECT_STATUS.md` to 2.0.0
3. **Add LM Studio docs** → Update README with Windows setup
4. **Create recipe system** → Design `recipes/schema.json`

---

*This TODO is interactive - check off items as you complete them!*
