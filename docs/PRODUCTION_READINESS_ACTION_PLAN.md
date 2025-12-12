# AI Project Synthesizer - Production Readiness Action Plan

## Executive Summary
This document tracks all issues, bugs, and enhancements required to achieve **98-100% test coverage** and **enterprise-grade production readiness**.

**Current Status**: 337 tests passing | 14% coverage | Target: 98-100%

**Last Updated**: 2025-12-12 13:15 UTC

---

## 🔴 Critical Issues (Must Fix)

### 1. Settings Validation Error
**Status**: 🔧 In Progress  
**Location**: `src/core/config.py`, `tests/conftest.py`  
**Error**:
```
ValidationError: 1 validation error for Settings
Input should be an instance of Settings [type=is_instance_of, input_value={}, input_type=dict]
```
**Root Cause**: Pydantic-settings v2 nested model coercion issue during test imports  
**Fix Applied**:
- Added `model_config` with `extra="ignore"` and `env_nested_delimiter="__"` to Settings class
- Removed module-level `settings = get_settings()` from config.py
- Environment variables must be set in conftest.py BEFORE any imports

**Remaining Work**:
- [ ] Fix conftest.py import order
- [ ] Verify all tests pass with new configuration

---

### 2. Resource Manager WeakSet Bug
**Status**: ✅ Fixed  
**Location**: `src/core/resource_manager.py:127-147`  
**Issue**: `_sync_cleanup_type()` was not clearing WeakSet after cleanup  
**Fix**: Added `self._active_resources[resource_type].clear()` after cleanup loop

---

### 3. Template Sanitization Security Gap
**Status**: ✅ Fixed  
**Location**: `src/core/security_utils.py:133-139`  
**Issue**: Missing Jinja2 control block pattern `{% %}` in dangerous patterns  
**Fix**: Added `r'\{%.*%\}'` to dangerous_patterns list

---

### 4. Path Validation Overly Restrictive
**Status**: ✅ Fixed  
**Location**: `src/core/security_utils.py:49-78`  
**Issue**: Blocked legitimate relative paths within base directory  
**Fix**: Only raise error for traversal that actually escapes base directory after resolution

---

## 🟡 Test Coverage Gaps

### Modules at 0% Coverage (Priority: High)

| Module | Lines | Status | Action Required |
|--------|-------|--------|-----------------|
| `src/vibe/` | 2000+ | ❌ 0% | Create comprehensive tests |
| `src/voice/` | 800+ | ❌ 0% | Create voice integration tests |
| `src/quality/` | 1600+ | ❌ 0% | Create quality gate tests |
| `src/discovery/` | 1500+ | ❌ 0-3% | Expand existing tests |
| `src/synthesis/` | 900+ | ❌ 0-7% | Add synthesis workflow tests |
| `src/workflows/` | 500+ | ❌ 0% | Create workflow tests |
| `src/tui/` | 500+ | ❌ 0% | Create TUI tests |
| `src/recipes/` | 170+ | ❌ 0% | Create recipe tests |
| `src/plugins/` | 17+ | ❌ 0% | Create plugin tests |

### Modules with Partial Coverage (Priority: Medium)

| Module | Current | Target | Action Required |
|--------|---------|--------|-----------------|
| `src/platform/` | 30% | 95% | Fill coverage gaps |
| `src/llm/` | 26% | 95% | Add LLM integration tests |
| `src/resolution/` | 18-83% | 95% | Complete resolver tests |
| `src/analysis/` | 15% | 95% | Add AST analysis tests |

---

## 🟢 Completed Fixes

### Security Utils Tests (61 tests passing)
- ✅ Command argument validation
- ✅ Path traversal protection
- ✅ URL validation
- ✅ Template sanitization
- ✅ Safe subprocess execution
- ✅ Secure filename handling

### Safe Formatter Tests (14 tests passing)
- ✅ Placeholder validation
- ✅ HTML escaping
- ✅ MR/Issue formatters

### Resource Manager Tests (17 tests passing)
- ✅ Resource registration/unregistration
- ✅ Cleanup callbacks
- ✅ Leak detection
- ✅ Async context managers

---

## 📋 Action Items

### Phase 1: Fix Test Infrastructure (Priority: Critical)
- [ ] Fix conftest.py to set env vars before any imports
- [ ] Ensure Settings() can be instantiated in test environment
- [ ] Run full test suite to verify fixes

### Phase 2: Core Module Coverage (Priority: High)
- [ ] src/core/exceptions.py - 100% coverage
- [ ] src/core/logging.py - 100% coverage
- [ ] src/core/config.py - 100% coverage
- [ ] src/core/security_utils.py - 100% coverage ✅
- [ ] src/core/safe_formatter.py - 100% coverage ✅
- [ ] src/core/resource_manager.py - 100% coverage ✅

### Phase 3: Discovery Module Coverage (Priority: High)
- [ ] src/discovery/github_client.py - 95% coverage
- [ ] src/discovery/gitlab_client.py - 95% coverage
- [ ] src/discovery/huggingface_client.py - 95% coverage
- [ ] src/discovery/unified_search.py - 95% coverage
- [ ] src/discovery/base_client.py - 95% coverage

### Phase 4: LLM Module Coverage (Priority: High)
- [ ] src/llm/ollama_client.py - 95% coverage
- [ ] src/llm/lmstudio_client.py - 95% coverage
- [ ] src/llm/cloud_client.py - 95% coverage
- [ ] src/llm/orchestrator.py - 95% coverage

### Phase 5: Synthesis & Analysis Coverage (Priority: Medium)
- [ ] src/synthesis/project_builder.py - 95% coverage
- [ ] src/synthesis/project_assembler.py - 95% coverage
- [ ] src/analysis/ast_parser.py - 95% coverage
- [ ] src/analysis/dependency_analyzer.py - 95% coverage

### Phase 6: Quality & Vibe Coverage (Priority: Medium)
- [ ] src/quality/quality_gate.py - 80% coverage
- [ ] src/quality/security_scanner.py - 80% coverage
- [ ] src/vibe/architect_agent.py - 80% coverage
- [ ] src/vibe/context_manager.py - 80% coverage

### Phase 7: Voice & TUI Coverage (Priority: Low)
- [ ] src/voice/manager.py - 70% coverage
- [ ] src/tui/app.py - 70% coverage
- [ ] src/tui/wizard.py - 70% coverage

---

## 🏗️ Architecture Improvements

### Performance Enhancements
- [ ] Add caching layer for API responses
- [ ] Implement connection pooling for HTTP clients
- [ ] Add async batch processing for repository analysis
- [ ] Optimize memory usage in large codebase synthesis

### Error Handling
- [ ] Standardize exception hierarchy
- [ ] Add retry logic with exponential backoff
- [ ] Implement circuit breaker patterns (partially done)
- [ ] Add comprehensive error logging

### Security Hardening
- [ ] Input validation on all external inputs ✅
- [ ] Template injection protection ✅
- [ ] Path traversal protection ✅
- [ ] Rate limiting on API endpoints
- [ ] Secrets management audit

---

## 📊 Metrics & Monitoring

### Test Coverage Targets
| Category | Current | Target | Status |
|----------|---------|--------|--------|
| Unit Tests | 13% | 95% | 🔴 |
| Integration Tests | 5% | 80% | 🔴 |
| E2E Tests | 0% | 70% | 🔴 |
| Overall | 13% | 98% | 🔴 |

### Code Quality Targets
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Pylint Score | Unknown | 9.5/10 | 🟡 |
| Type Coverage | Unknown | 95% | 🟡 |
| Doc Coverage | Unknown | 90% | 🟡 |
| Complexity | Unknown | <10 | 🟡 |

---

## 🔄 Next Steps

1. **Immediate**: Fix conftest.py import order issue
2. **Today**: Run full test suite, document failures
3. **This Week**: Achieve 50% coverage on core modules
4. **Next Week**: Achieve 80% coverage overall
5. **Final**: Achieve 98% coverage, production deployment

---

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-12 | Initial action plan created | Cascade |
| 2025-12-12 | Fixed resource_manager.py WeakSet bug | Cascade |
| 2025-12-12 | Fixed security_utils.py template pattern | Cascade |
| 2025-12-12 | Fixed security_utils.py path validation | Cascade |
| 2025-12-12 | Added model_config to Settings class | Cascade |

---

*This document is automatically updated as issues are discovered and fixed.*
