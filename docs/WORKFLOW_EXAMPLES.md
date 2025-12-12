# 🔄 Complete Workflow Examples

## Overview

This document shows **real end-to-end workflows** demonstrating how agents work together to deliver complete solutions for vibe coders.

---

## Workflow 1: "Build Me a REST API"

### User Request
> "Build me a REST API for managing my dog's health records. I want to track vaccinations, vet visits, and medications."

### Execution Timeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW: Dog Health API                                                     │
│  Total Time: ~5 minutes                                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  00:00 ─► User Request Received                                              │
│           │                                                                  │
│  00:05 ─► Coordinator: Analyze & Plan                                        │
│           │  "Detected: CRUD API for pet health tracking"                    │
│           │  "Tech Stack: FastAPI + SQLite + Docker"                         │
│           │                                                                  │
│  00:15 ─► Architect: Design System                                           │
│           │  • Database schema (dogs, vaccinations, visits, meds)            │
│           │  • API routes design                                             │
│           │  • File structure                                                │
│           │                                                                  │
│  00:45 ─► Database Agent: Create Schema                                      │
│           │  • models.py with SQLAlchemy                                     │
│           │  • Initial migration                                             │
│           │                                                                  │
│  01:15 ─► Coder: Implement API                                               │
│           │  • main.py (FastAPI app)                                         │
│           │  • routes/dogs.py                                                │
│           │  • routes/vaccinations.py                                        │
│           │  • routes/visits.py                                              │
│           │  • routes/medications.py                                         │
│           │  • schemas.py (Pydantic models)                                  │
│           │                                                                  │
│  02:30 ─► Tester: Write & Run Tests                                          │
│           │  • test_dogs.py                                                  │
│           │  • test_vaccinations.py                                          │
│           │  • Run pytest → All pass ✓                                       │
│           │                                                                  │
│  03:15 ─► DevOps: Containerize                                               │
│           │  • Dockerfile (multi-stage)                                      │
│           │  • docker-compose.yml                                            │
│           │  • .env.example                                                  │
│           │                                                                  │
│  03:45 ─► CLI Agent: Build & Test Container                                  │
│           │  • docker compose build                                          │
│           │  • docker compose up -d                                          │
│           │  • Health check → Running ✓                                      │
│           │                                                                  │
│  04:15 ─► Docs: Generate Documentation                                       │
│           │  • README.md                                                     │
│           │  • API_DOCS.md (all routes)                                      │
│           │  • SETUP.md                                                      │
│           │                                                                  │
│  04:45 ─► Coordinator: Final Report                                          │
│           │                                                                  │
│  05:00 ─► USER RECEIVES COMPLETE PROJECT ✓                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Generated Files

```
dog-health-api/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── database.py             # Database connection
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   └── routes/
│       ├── __init__.py
│       ├── dogs.py             # Dog CRUD endpoints
│       ├── vaccinations.py     # Vaccination endpoints
│       ├── visits.py           # Vet visit endpoints
│       └── medications.py      # Medication endpoints
├── tests/
│   ├── conftest.py             # Test fixtures
│   ├── test_dogs.py
│   ├── test_vaccinations.py
│   ├── test_visits.py
│   └── test_medications.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── API_DOCS.md
│   └── SETUP.md
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Agent Messages (Abbreviated)

```json
// Coordinator → Architect
{
  "task": "Design REST API for dog health records",
  "requirements": {
    "entities": ["dogs", "vaccinations", "vet_visits", "medications"],
    "features": ["CRUD for all entities", "relationships between entities"],
    "tech": "FastAPI + SQLite"
  }
}

// Architect → Coordinator (Response)
{
  "architecture": {
    "pattern": "Clean Architecture",
    "database": "SQLite with SQLAlchemy ORM",
    "api": "RESTful with FastAPI",
    "validation": "Pydantic v2"
  },
  "schema": {
    "dogs": ["id", "name", "breed", "birth_date", "weight", "owner_name"],
    "vaccinations": ["id", "dog_id", "vaccine_name", "date", "next_due"],
    "vet_visits": ["id", "dog_id", "date", "reason", "diagnosis", "notes"],
    "medications": ["id", "dog_id", "name", "dosage", "frequency", "start_date", "end_date"]
  },
  "routes": {
    "/dogs": "CRUD",
    "/dogs/{id}/vaccinations": "CRUD",
    "/dogs/{id}/visits": "CRUD",
    "/dogs/{id}/medications": "CRUD"
  }
}

// Coordinator → Coder
{
  "task": "Implement API based on architecture",
  "architecture": "...(from Architect)",
  "deliverables": ["main.py", "models.py", "schemas.py", "routes/*.py"]
}

// Coder → Coordinator (Completion)
{
  "status": "complete",
  "files_created": 12,
  "lines_of_code": 847,
  "summary": "Full REST API with CRUD for dogs and related health records"
}
```

### User Report

```markdown
# ✅ Project Complete: Dog Health API

## Summary
I've built a complete REST API for managing your dog's health records.

## What's Included
- **Dogs Management**: Add, view, update, delete dog profiles
- **Vaccinations**: Track all vaccinations with due date reminders
- **Vet Visits**: Log vet visits with diagnosis and notes
- **Medications**: Track current and past medications

## Quick Start
```bash
# Start the API
docker compose up -d

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /dogs | List all dogs |
| POST | /dogs | Add a new dog |
| GET | /dogs/{id} | Get dog details |
| PUT | /dogs/{id} | Update dog |
| DELETE | /dogs/{id} | Delete dog |
| GET | /dogs/{id}/vaccinations | List vaccinations |
| POST | /dogs/{id}/vaccinations | Add vaccination |
| ... | ... | ... |

## Files Created
12 source files, 5 test files, 4 config files

## Tests
✅ All 24 tests passing
📊 87% code coverage

Would you like me to add any additional features?
```

---

## Workflow 2: "Fix This Bug"

### User Request
> "My app crashes when I try to upload large files. Here's the error: [pastes traceback]"

### Execution Timeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW: Bug Fix - Large File Upload                                        │
│  Total Time: ~3 minutes                                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  00:00 ─► User Submits Bug Report + Traceback                                │
│           │                                                                  │
│  00:05 ─► Coordinator: Analyze Error                                         │
│           │  "Detected: MemoryError during file upload"                      │
│           │  "Root cause likely: Loading entire file into memory"            │
│           │                                                                  │
│  00:15 ─► Debug Agent: Deep Analysis                                         │
│           │  • Parse traceback                                               │
│           │  • Identify problematic code location                            │
│           │  • Analyze memory usage pattern                                  │
│           │                                                                  │
│  00:45 ─► Debug → Coder: Fix Request                                         │
│           │  "Change file handling to streaming/chunked"                     │
│           │                                                                  │
│  01:00 ─► Coder: Implement Fix                                               │
│           │  • Modify upload handler to use chunks                           │
│           │  • Add configurable chunk size                                   │
│           │  • Add progress tracking                                         │
│           │                                                                  │
│  01:45 ─► Tester: Create Regression Test                                     │
│           │  • test_large_file_upload.py                                     │
│           │  • Test with 100MB, 500MB, 1GB files                            │
│           │  • All pass ✓                                                    │
│           │                                                                  │
│  02:30 ─► CLI: Run Full Test Suite                                           │
│           │  • pytest tests/ → All pass                                      │
│           │  • No regressions                                                │
│           │                                                                  │
│  03:00 ─► Coordinator: Report to User                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Debug Agent Analysis

```python
# Debug Agent's Analysis Output
{
    "error_type": "MemoryError",
    "location": "src/upload/handler.py:45",
    "problematic_code": """
        # OLD CODE - Loads entire file into memory
        def handle_upload(file):
            content = file.read()  # ← Memory explosion for large files
            process_content(content)
    """,
    "root_cause": "file.read() loads entire file into RAM",
    "impact": "Files > available RAM cause crash",
    "recommended_fix": "Use chunked reading with streaming",
    "fix_pattern": "chunked_file_processing"
}
```

### Coder's Fix

```python
# NEW CODE - Chunked processing
async def handle_upload(file: UploadFile, chunk_size: int = 1024 * 1024):  # 1MB chunks
    """Handle file upload with chunked processing to avoid memory issues."""
    
    total_size = 0
    chunks_processed = 0
    
    async with aiofiles.open(f"uploads/{file.filename}", "wb") as out_file:
        while chunk := await file.read(chunk_size):
            await out_file.write(chunk)
            total_size += len(chunk)
            chunks_processed += 1
            
            # Optional: Report progress
            logger.debug(f"Processed chunk {chunks_processed}, total: {total_size} bytes")
    
    return {
        "filename": file.filename,
        "size": total_size,
        "chunks": chunks_processed,
    }
```

### User Report

```markdown
# 🐛 Bug Fixed: Large File Upload Crash

## Problem
Your app was loading entire files into memory, causing crashes for large files.

## Solution
Changed file handling to use chunked streaming:
- Files are now processed in 1MB chunks
- Memory usage stays constant regardless of file size
- Added progress logging

## Changes Made
- Modified: `src/upload/handler.py`
- Added: `tests/test_large_file_upload.py`

## Testing
✅ Tested with files up to 2GB - no issues
✅ All existing tests still pass

## Code Diff
```diff
- content = file.read()
+ while chunk := await file.read(chunk_size):
+     await out_file.write(chunk)
```
```

---

## Workflow 3: "Deploy to Production"

### User Request
> "My app is ready. Deploy it to production with proper monitoring."

### Execution Timeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW: Production Deployment                                              │
│  Total Time: ~10 minutes                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  00:00 ─► User Request: Deploy to Production                                 │
│           │                                                                  │
│  00:10 ─► Coordinator: Pre-deployment Checklist                              │
│           │  • Check tests pass                                              │
│           │  • Check security scan                                           │
│           │  • Check environment config                                      │
│           │                                                                  │
│  00:30 ─► Security Agent: Full Audit                                         │
│           │  • Run bandit (Python security)                                  │
│           │  • Check dependencies for CVEs                                   │
│           │  • Verify secrets not in code                                    │
│           │  • Result: 2 medium issues → Auto-fixed                         │
│           │                                                                  │
│  01:30 ─► Tester: Full Test Suite                                            │
│           │  • Unit tests ✓                                                  │
│           │  • Integration tests ✓                                           │
│           │  • E2E tests ✓                                                   │
│           │                                                                  │
│  02:30 ─► DevOps: Production Configuration                                   │
│           │  • Optimize Dockerfile for production                            │
│           │  • Create production docker-compose                              │
│           │  • Set up nginx reverse proxy                                    │
│           │  • Configure SSL/TLS                                             │
│           │                                                                  │
│  04:00 ─► DevOps: Monitoring Setup                                           │
│           │  • Add Prometheus metrics endpoint                               │
│           │  • Configure Grafana dashboard                                   │
│           │  • Set up alerting rules                                         │
│           │  • Configure log aggregation                                     │
│           │                                                                  │
│  06:00 ─► DevOps: CI/CD Pipeline                                             │
│           │  • Create GitHub Actions workflow                                │
│           │  • Build → Test → Security → Deploy                             │
│           │  • Auto-rollback on failure                                      │
│           │                                                                  │
│  07:30 ─► CLI Agent: Deploy                                                  │
│           │  • docker compose -f docker-compose.prod.yml up -d              │
│           │  • Health checks pass ✓                                          │
│           │  • Smoke tests pass ✓                                            │
│           │                                                                  │
│  09:00 ─► Docs Agent: Deployment Docs                                        │
│           │  • DEPLOYMENT.md                                                 │
│           │  • RUNBOOK.md (operations guide)                                 │
│           │                                                                  │
│  10:00 ─► Coordinator: Deployment Complete                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Generated Production Files

```
production/
├── docker-compose.prod.yml      # Production compose
├── nginx/
│   ├── nginx.conf               # Reverse proxy config
│   └── ssl/                     # SSL certificates
├── monitoring/
│   ├── prometheus.yml           # Metrics collection
│   ├── grafana/
│   │   └── dashboard.json       # Pre-built dashboard
│   └── alertmanager.yml         # Alert rules
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline
└── docs/
    ├── DEPLOYMENT.md            # How to deploy
    └── RUNBOOK.md               # Operations guide
```

---

## Workflow 4: "Create a Dashboard"

### User Request
> "I need a dashboard to visualize my sales data from this CSV file."

### Execution Timeline (Abbreviated)

```
1. Coordinator: Analyze CSV structure
2. Architect: Design dashboard layout
3. Coder: Create React dashboard with charts
4. CLI: Install dependencies, build
5. DevOps: Dockerize
6. Docs: Usage guide
7. → Complete Dashboard delivered
```

### Generated Dashboard

```
sales-dashboard/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── SalesChart.tsx       # Line chart
│   │   ├── RevenueCard.tsx      # KPI card
│   │   ├── TopProducts.tsx      # Bar chart
│   │   └── SalesTable.tsx       # Data table
│   ├── hooks/
│   │   └── useCSVData.ts        # CSV parsing
│   └── styles/
│       └── dashboard.css
├── public/
│   └── index.html
├── Dockerfile
└── README.md
```

---

## Workflow 5: Error Recovery Example

### Scenario
During code generation, an import error occurs.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ERROR RECOVERY FLOW                                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Coder Agent: Generate code                                                  │
│       │                                                                      │
│       ▼                                                                      │
│  CLI Agent: pip install -r requirements.txt                                  │
│       │                                                                      │
│       ▼                                                                      │
│  ❌ ERROR: "No module named 'pydantic_settings'"                             │
│       │                                                                      │
│       ▼                                                                      │
│  Error Recovery System: Detect missing package                               │
│       │                                                                      │
│       ▼                                                                      │
│  CLI Agent: pip install pydantic-settings                                    │
│       │                                                                      │
│       ▼                                                                      │
│  ✅ Package installed                                                        │
│       │                                                                      │
│       ▼                                                                      │
│  CLI Agent: Retry original command                                           │
│       │                                                                      │
│       ▼                                                                      │
│  ✅ Success - Continue workflow                                              │
│                                                                              │
│  (User never sees the error - handled automatically)                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Patterns Across Workflows

### 1. Always Deliver Complete Solutions
- No partial implementations
- All files needed to run
- Documentation included

### 2. Automatic Error Handling
- Errors caught and fixed
- User only notified if critical
- Automatic retries

### 3. Quality Assurance Built-in
- Tests generated automatically
- Security scans before deploy
- Code review by agents

### 4. Clear User Communication
- Progress updates at milestones
- Final report with summary
- Next steps suggestions

---

## Next Document

See **[N8N_AUTOGEN_BRIDGE.md](./N8N_AUTOGEN_BRIDGE.md)** for workflow automation integration.
