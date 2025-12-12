# Migration Plan: windsurf-vibe-setup → VIBE MCP

This document maps components from the original `windsurf-vibe-setup` repository to their new locations in the VIBE MCP architecture.

## Overview

The migration preserves all valuable historical work while integrating it into the structured Phase 1-10 implementation plan of VIBE MCP.

---

## 1. Startup Scripts & Test Harness

### From: `windsurf-vibe-setup/`
```
START-MCP-ONLY.bat
START-SIMPLE.bat
START-VIBE.bat
START-VIBE-FIXED.bat
test-lmstudio.js
test-local-llms.js
test-mcp-simple.js
```

### To: `VIBE MCP/`
```
tools/
├── start_vibe_win.ps1      (replaces START-VIBE.bat)
├── start_mcp_only.ps1      (replaces START-MCP-ONLY.bat)
├── start_simple.ps1        (replaces START-SIMPLE.bat)
└── start_vibe_fixed.ps1    (replaces START-VIBE-FIXED.bat)

tests/tools/
├── test_lmstudio.py        (replaces test-lmstudio.js)
├── test_local_llms.py      (replaces test-local-llms.js)
└── test_mcp_connectivity.py (replaces test-mcp-simple.js)
```

### Migration Notes:
- Convert from `.bat` to PowerShell (`.ps1`) for better Windows integration
- Python tests provide better integration with pytest and existing test infrastructure
- Scripts will use the new CLI executor for safety

### Status: ⏳ In Progress

---

## 2. Windsurf Editor Integration

### From: `windsurf-vibe-setup/`
```
Windsurf-IDE-configuration-guide.md
templates/workspace-rules/
├── global.windsurfrules
└── project.windsurfrules
```

### To: `VIBE MCP/`
```
docs/windsurf-integration.md
templates/workspace-rules/
├── global.windsurfrules
└── project.windsurfrules
```

### Migration Notes:
- Updated integration guide to reference VIBE MCP architecture
- Enhanced .windsurfrules with CLI executor and memory system references

### Status: ✅ Complete

---

## 3. Audit Reports & Metrics

### From: `windsurf-vibe-setup/`
```
AUDIT_REPORT.md
AUDIT-REPORT-DETAILED.md
FAST-API-FIXES-AUDIT.md
FASTAPI_AUDIT_2025-12-09.md
security-reports/
├── security-scan-results.json
└── vulnerability-report.md
metrics-reports/
├── performance-metrics.json
└── code-quality-metrics.md
benchmark-results/
├── llm-benchmark.json
└── speed-tests.json
COMPLETE-FILE-STRUCTURE-DEEP-DIVE.md
COMPLETE-MCP-TOOLS-LIST.md
COMPLETE-PROJECT-AUDIT-PLAN.md
DOCUMENTATION-MASTER-PLAN.md
ENV_CONFIG_GUIDE.md
```

### To: `VIBE MCP/`
```
docs/audits/
├── AUDIT_REPORT.md
├── AUDIT-REPORT-DETAILED.md
├── FAST-API-FIXES-AUDIT.md
├── FASTAPI_AUDIT_2025-12-09.md
└── historical/
    └── [older audits organized by date]

docs/metrics/
├── performance/
│   └── performance-metrics.json
├── quality/
│   └── code-quality-metrics.md
└── benchmarks/
    ├── llm-benchmark.json
    └── speed-tests.json

docs/reference/
├── COMPLETE-FILE-STRUCTURE-DEEP-DIVE.md
├── COMPLETE-MCP-TOOLS-LIST.md
├── COMPLETE-PROJECT-AUDIT-PLAN.md
├── DOCUMENTATION-MASTER-PLAN.md
└── ENV_CONFIG_GUIDE.md
```

### Migration Notes:
- Organize by type (audits, metrics, reference)
- Keep as historical baseline for VIBE MCP quality gates
- Reference from new security and quality documentation

### Status: ⏳ Pending

---

## 4. Harness & Subscription Enforcement

### From: `windsurf-vibe-setup/`
```
ANTHROPIC_HARNESS_INTEGRATION.md
HARNESS_COMPLETE_INTEGRATION.md
HARNESS_INTEGRATION_COMPLETE.md
SETUP_CLAUDE_SUBSCRIPTION.md
SUBSCRIPTION_ONLY_ENFORCEMENT.md
```

### To: `VIBE MCP/`
```
docs/integrations/
├── anthropic_harness.md
├── claude_subscription_setup.md
└── subscription_enforcement.md

docs/policies/
└── subscription_management.md
```

### Migration Notes:
- Update to reference VIBE MCP's LiteLLM router
- Integrate with new quality gate and security systems
- Link from Phase 4 cloud integration documentation

### Status: ⏳ Pending

---

## 5. Docker & Environment Setup

### From: `windsurf-vibe-setup/`
```
docker-compose.yml
.env.example
```

### To: `VIBE MCP/`
```
docker-compose.yml (updated for new architecture)
.env.example (enhanced with VIBE MCP variables)
```

### Migration Notes:
- Update docker-compose.yml to include:
  - Mem0 service (when installed)
  - Enhanced MCP server configuration
  - Voice system services (Phase 2)
- Add new environment variables for VIBE MCP features

### Status: ⏳ Pending

---

## 6. Documentation Consolidation

### From: `windsurf-vibe-setup/`
```
HOW-IT-ALL-WORKS-TOGETHER.md
README.md
```

### To: `VIBE MCP/`
```
docs/architecture/HOW-IT-ALL-WORKS-TOGETHER.md
README.md (updated for VIBE MCP)
```

### Migration Notes:
- Update architecture documentation to include Phase 1-10 plan
- Reference new CLI executor, memory system, and LiteLLM router

### Status: ⏳ Pending

---

## Migration Checklist

### Phase 1: Documentation & Rules ✅
- [x] Create `docs/windsurf-integration.md`
- [x] Create `.windsurfrules` template
- [x] Set up `templates/workspace-rules/` structure

### Phase 2: Test Harness ⏳
- [ ] Create `tests/tools/test_mcp_connectivity.py`
- [ ] Create `tests/tools/test_lmstudio.py`
- [ ] Create `tests/tools/test_local_llms.py`
- [ ] Update pytest configuration

### Phase 3: Startup Scripts ⏳
- [ ] Convert `.bat` to `.ps1` scripts
- [ ] Update scripts to use CLI executor
- [ ] Add error handling and logging

### Phase 4: Documentation Migration ⏳
- [ ] Move audit reports to `docs/audits/`
- [ ] Move metrics to `docs/metrics/`
- [ ] Move reference docs to `docs/reference/`
- [ ] Update internal links

### Phase 5: Integration Docs ⏳
- [ ] Move Harness docs to `docs/integrations/`
- [ ] Create subscription policies
- [ ] Link from Phase 4 documentation

### Phase 6: Docker & Environment ⏳
- [ ] Update `docker-compose.yml`
- [ ] Enhance `.env.example`
- [ ] Add VIBE MCP specific services

---

## Next Steps

1. **Immediate**: Create Python test equivalents in `tests/tools/`
2. **This Week**: Migrate all documentation to new structure
3. **Next Week**: Update Docker and startup scripts
4. **Ongoing**: Reference historical audits in new quality gate system

---

## Benefits of Migration

- **Preserved History**: All audits and metrics retained as baseline
- **Better Organization**: Structured docs/ hierarchy for scalability
- **Enhanced Testing**: Python tests integrate with pytest infrastructure
- **Improved Safety**: PowerShell scripts with proper error handling
- **Future-Ready**: Structure supports Phase 2-10 implementation

---

## Notes for Developers

- When referencing historical audits, use relative paths from new locations
- Test scripts should use the CLI executor for all command operations
- PowerShell scripts should include proper error handling and logging
- Update all internal documentation links after migration
