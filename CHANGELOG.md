# Changelog

All notable changes to the AI Project Synthesizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-11

### Added

- **AI Agents System**
  - `ResearchAgent` - Repository discovery and trend analysis
  - `SynthesisAgent` - Code merging and dependency resolution
  - `VoiceAgent` - Voice interaction and commands
  - `AutomationAgent` - Task scheduling and recovery
  - `CodeAgent` - Code analysis and refactoring

- **Voice System**
  - ElevenLabs TTS integration with streaming
  - Multiple voice profiles (Rachel, Domi, Bella, Josh, Adam, Sam)
  - Push-to-talk and continuous listening modes
  - Voice command processing

- **Terminal UI (TUI)**
  - Rich interactive dashboard
  - Search, assembly, agents, settings views
  - Metrics and workflow management
  - Real-time status updates

- **Memory & Persistence**
  - SQLite-based memory store
  - Conversation history tracking
  - Search history with filtering
  - Bookmark management
  - Workflow state persistence

- **Real-Time Event System**
  - Event bus with pub/sub pattern
  - Server-Sent Events (SSE) streaming
  - Event history and filtering
  - Async event handlers

- **Automation & Workflows**
  - 10 n8n workflow templates
  - Workflow orchestrator
  - Metrics collection
  - Integration testing framework

- **Gap Analyzer & Auto-Repair**
  - Progressive gap detection
  - Automatic issue fixing
  - Repair plans and execution
  - Report generation

- **Webhook Integrations**
  - GitHub webhooks
  - n8n workflow webhooks
  - Slack slash commands
  - Discord bot integration
  - Custom webhook endpoints

- **Settings Manager**
  - 7 configuration tabs (General, Voice, Automation, Hotkeys, AI/ML, Workflows, Advanced)
  - Feature toggles
  - Import/export settings
  - Change callbacks

- **Hotkey Manager**
  - Configurable hotkey bindings
  - Push-to-talk support
  - Action callbacks

- **New CLI Commands**
  - `tui` - Start Terminal UI
  - `voice` - Start voice assistant
  - `dashboard` - Start web dashboard
  - `check` - Run gap analysis
  - `settings` - Manage settings
  - `health` - Check system health

- **Comprehensive Test Suite**
  - 245+ tests passing
  - Core module tests
  - Agent tests
  - Settings/hotkey tests
  - Automation metrics tests
  - Edge case tests (`tests/test_edge_cases.py`)
  - MCP server tests (`tests/test_mcp_server.py`)

- **Recipe System**
  - Pre-configured project templates
  - 3 built-in recipes: MCP Server, RAG Chatbot, Web Scraper
  - Recipe CLI commands: list, show, run, validate
  - YAML-based recipe definitions with JSON schema

- **Wizard Mode**
  - Interactive guided project creation
  - Step-by-step configuration
  - Tech stack recommendations
  - Repository selection

- **Plugin System Documentation**
  - Platform plugins for new code hosts
  - Analysis plugins for custom metrics
  - Synthesis plugins for custom generation
  - Plugin manager and lifecycle

- **Web Dashboard Documentation**
  - API endpoint reference
  - WebSocket real-time updates
  - Authentication and security
  - Deployment guides

- **Finalization Script**
  - `scripts/finalize.ps1` for hardening
  - Security scan with bandit
  - Dependency upgrades
  - pip-audit vulnerability check
  - Integration test runner

- **Thread-Safe Synthesis Jobs**
  - `threading.Lock` for job management
  - `get_synthesis_job()`, `set_synthesis_job()`, `update_synthesis_job()`
  - Concurrent job safety

- **LM Studio Integration**
  - Windows + LM Studio setup docs
  - `scripts/start_with_lmstudio.ps1` helper
  - Auto-detection of local LLM

### Changed

- Version bump to 2.0.0
- Updated all documentation
- Enhanced architecture diagrams
- Improved error handling across agents
- Fixed placeholder URLs in pyproject.toml
- Fixed placeholder email in pyproject.toml
- Updated PROJECT_STATUS.md with metrics table

---

## [1.1.0] - 2024-12-11

### Added

- **Comprehensive Documentation Suite**
  - USER_GUIDE.md - Complete user guide with step-by-step instructions
  - CLI_REFERENCE.md - Full CLI command reference
  - CONFIGURATION.md - Detailed configuration guide
  - TROUBLESHOOTING.md - Common issues and solutions
  - QUICK_START.md - Fast-track getting started guide

- **Edge Case Test Coverage**
  - `tests/unit/test_ast_parser.py` - 19 tests for AST parsing edge cases
  - `tests/unit/test_compatibility_checker.py` - 24 tests for compatibility checking

- **New MCP Tool**
  - `get_platforms` - Returns available platform information

### Changed

- **Module Rename**: Renamed `src/mcp/` to `src/mcp_server/` to avoid collision with installed `mcp` package
- **Updated all imports** across codebase to use new module path
- **README.md** - Updated with accurate MCP tools list, correct paths, and improved quick start
- **API_REFERENCE.md** - Added complete documentation for all 8 tools

### Fixed

- **Import Errors**: Fixed module import paths after rename
- **Test Compatibility**: Updated all tests to use new module paths
- **Windsurf Config**: Fixed MCP server command path in documentation

### Test Coverage

- **162 Total Tests Passing**
  - Unit Tests: 119 passing
  - Integration Tests: 9 passing
  - Edge Case Tests: 43 new tests added

---

## [1.0.0] - 2024-12-10

### Added

- **Complete MCP Server**: 7 fully functional tools for repository synthesis
- **GitHub Integration**: Full repository cloning, analysis, and component extraction
- **Project Synthesis Pipeline**: End-to-end code merging and project generation
- **Dependency Resolution**: SAT solver with uv/pip-compile for conflict detection
- **Documentation Generation**: Professional README and architecture docs
- **Comprehensive Validation**: URL validation and error handling for all tools
- **CI/CD Pipeline**: Automated testing, linting, and Docker builds
- **Quick Start Guide**: 3-step setup process for immediate user value

### Fixed

- **Configuration Bug**: Fixed `create_unified_search()` accessing non-existent attributes
- **Missing URL Validation**: Added regex validation to prevent invalid repository URLs
- **Documentation Inconsistencies**: Updated API Reference to match actual schemas
- **Import Issues**: Moved imports to eliminate IDE warnings

### Features

- **7 MCP Tools**: search_repositories, analyze_repository, check_compatibility, resolve_dependencies, synthesize_project, generate_documentation, get_synthesis_status
- **Cross-Platform Support**: Works on Windows, Linux, macOS
- **Professional Documentation**: Complete API reference with examples
- **Robust Error Handling**: Graceful failures with helpful error messages

### Test Coverage

- **Unit Tests**: 16/16 Python resolver tests pass
- **Integration Tests**: End-to-end synthesis pipeline verified
- **Edge Case Tests**: Comprehensive validation suite created

---

## [Unreleased]

### Planned

- HuggingFace client full implementation
- Kaggle client full implementation
- arXiv/Papers with Code integration
- Additional project templates
- Web UI dashboard
- Plugin system for custom analyzers

---

## Version History Format

### [X.Y.Z] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes in existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security fixes
