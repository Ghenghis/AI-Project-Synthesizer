# 📖 API Reference

> **AI Project Synthesizer MCP Tools API**  
> **Version:** 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [MCP Tools](#mcp-tools)
4. [Data Types](#data-types)
5. [Error Handling](#error-handling)
6. [Rate Limits](#rate-limits)

---

## Overview

The AI Project Synthesizer exposes its functionality through **MCP (Model Context Protocol) Tools**. These tools are callable from Windsurf's Cascade AI and provide structured inputs/outputs.

### Base Configuration

```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "C:\\Users\\Admin\\AI_Synthesizer"
    }
  }
}
```

---

## Authentication

### Platform API Keys

Configure in `.env` file:

```env
# Required
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# Optional (enables additional platforms)
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key
SEMANTIC_SCHOLAR_API_KEY=xxxxxxxxxxxxx

# Cloud LLM (optional fallback)
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

---

## MCP Tools

### search_repositories

Search for repositories across multiple platforms.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Natural language search query |
| `platforms` | string[] | No | `["github", "huggingface"]` | Platforms to search |
| `max_results` | integer | No | `20` | Maximum results (1-100) |
| `language_filter` | string | No | `null` | Filter by programming language |
| `min_stars` | integer | No | `10` | Minimum star count |
| `updated_within_days` | integer | No | `365` | Max days since last update |

**Returns:** `SearchResult`

**Example:**

```json
// Input
{
  "query": "OCR document extraction Python",
  "platforms": ["github", "huggingface"],
  "max_results": 10,
  "language_filter": "python",
  "min_stars": 100
}

// Output
{
  "query": "OCR document extraction Python",
  "total_found": 10,
  "search_time_ms": 1250,
  "candidates": [
    {
      "platform": "github",
      "url": "https://github.com/PaddlePaddle/PaddleOCR",
      "name": "PaddleOCR",
      "description": "Awesome multilingual OCR toolkits...",
      "stars": 35420,
      "last_updated": "2024-12-09",
      "language": "Python",
      "relevance_score": 0.95,
      "license": "Apache-2.0"
    }
  ]
}
```

---

### analyze_repository

Perform deep analysis of a single repository.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo_url` | string | Yes | Repository URL |
| `include_transitive_deps` | boolean | No | Include transitive dependencies |
| `extract_components` | boolean | No | Identify extractable components |

**Returns:** `AnalysisResult`

**Example:**

```json
// Input
{
  "repo_url": "https://github.com/PaddlePaddle/PaddleOCR",
  "include_transitive_deps": true,
  "extract_components": true
}

// Output
{
  "repo_url": "https://github.com/PaddlePaddle/PaddleOCR",
  "analysis_time_ms": 5420,
  "language_breakdown": {
    "Python": 85.2,
    "C++": 10.5,
    "Shell": 4.3
  },
  "dependencies": {
    "direct_count": 24,
    "transitive_count": 156,
    "conflicts": []
  },
  "code_metrics": {
    "lines_of_code": 125000,
    "files": 450,
    "cyclomatic_complexity_avg": 4.2,
    "test_coverage": 72
  },
  "extractable_components": [
    {
      "name": "text_detection",
      "path": "ppocr/detection",
      "files_count": 25,
      "dependencies": ["paddlepaddle", "opencv-python"]
    },
    {
      "name": "text_recognition",
      "path": "ppocr/recognition",
      "files_count": 30,
      "dependencies": ["paddlepaddle", "numpy"]
    }
  ],
  "quality_score": 0.85
}
```

---

### check_compatibility

Check if multiple repositories can work together.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo_urls` | string[] | Yes | List of repository URLs |
| `target_python_version` | string | No | Target Python version |

**Returns:** `CompatibilityMatrix`

**Example:**

```json
// Input
{
  "repo_urls": [
    "https://github.com/PaddlePaddle/PaddleOCR",
    "https://github.com/chroma-core/chroma",
    "https://github.com/run-llama/llama_index"
  ],
  "target_python_version": "3.11"
}

// Output
{
  "compatible": true,
  "matrix": {
    "PaddleOCR-chroma": {
      "compatible": true,
      "shared_deps": ["numpy", "pillow"],
      "conflicts": []
    },
    "PaddleOCR-llama_index": {
      "compatible": true,
      "shared_deps": ["numpy", "tiktoken"],
      "conflicts": []
    },
    "chroma-llama_index": {
      "compatible": true,
      "shared_deps": ["numpy", "httpx"],
      "conflicts": []
    }
  },
  "unified_python_version": "3.11",
  "warnings": [
    "PaddleOCR recommends Python 3.8-3.10, but should work with 3.11"
  ]
}
```

---

### resolve_dependencies

Resolve and merge dependencies from multiple sources.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repositories` | string[] | Yes | Repository URLs |
| `constraints` | string[] | No | Additional version constraints |
| `python_version` | string | No | Target Python version |
| `generate_lockfile` | boolean | No | Generate lockfile content |

**Returns:** `ResolutionResult`

**Example:**

```json
// Input
{
  "repositories": [
    "https://github.com/PaddlePaddle/PaddleOCR",
    "https://github.com/chroma-core/chroma"
  ],
  "python_version": "3.11",
  "generate_lockfile": true
}

// Output
{
  "success": true,
  "packages_count": 85,
  "resolution_time_ms": 2100,
  "packages": [
    {"name": "numpy", "version": "1.26.2"},
    {"name": "paddlepaddle", "version": "2.6.0"},
    {"name": "chromadb", "version": "0.4.22"}
  ],
  "lockfile_preview": "# Generated by uv\nnumpy==1.26.2 \\\n    --hash=sha256:...",
  "conflicts_resolved": 2,
  "resolution_notes": [
    "Downgraded numpy from 2.0 to 1.26 for PaddlePaddle compatibility"
  ]
}
```

---

### synthesize_project

Create a unified project from multiple repositories.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repositories` | ExtractionSpec[] | Yes | Repositories and extraction config |
| `project_name` | string | Yes | Name for the project |
| `output_path` | string | Yes | Output directory |
| `template` | string | No | Project template to use |
| `generate_docs` | boolean | No | Auto-generate documentation |

**ExtractionSpec:**

```json
{
  "repo_url": "string",
  "components": ["string"],
  "rename_map": {"old": "new"},
  "destination": "string"
}
```

**Returns:** `SynthesisResult`

**Example:**

```json
// Input
{
  "repositories": [
    {
      "repo_url": "https://github.com/PaddlePaddle/PaddleOCR",
      "components": ["ppocr/detection", "ppocr/recognition"],
      "rename_map": {},
      "destination": "src/ocr"
    },
    {
      "repo_url": "https://github.com/chroma-core/chroma",
      "components": ["chromadb/api", "chromadb/db"],
      "rename_map": {},
      "destination": "src/vectorstore"
    }
  ],
  "project_name": "document-analyzer",
  "output_path": "C:/Projects/document-analyzer",
  "template": "python-fastapi",
  "generate_docs": true
}

// Output
{
  "success": true,
  "project_path": "C:/Projects/document-analyzer",
  "files_created": 125,
  "structure": {
    "src/": ["ocr/", "vectorstore/", "api/"],
    "tests/": ["unit/", "integration/"],
    "docs/": ["README.md", "ARCHITECTURE.md"]
  },
  "dependencies_file": "requirements.txt",
  "setup_commands": [
    "cd C:/Projects/document-analyzer",
    "python -m venv .venv",
    ".venv/Scripts/activate",
    "pip install -r requirements.txt"
  ],
  "synthesis_time_seconds": 45.2
}
```

---

### generate_documentation

Generate comprehensive documentation for a project.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | Yes | Path to project |
| `doc_types` | string[] | No | Types to generate |
| `llm_enhanced` | boolean | No | Use LLM for better docs |

**Doc Types:** `readme`, `architecture`, `api`, `diagrams`, `changelog`

**Returns:** `GenerationResult`

---

### get_synthesis_status

Get status of an ongoing synthesis operation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `synthesis_id` | string | Yes | Synthesis operation ID |

**Returns:** `StatusReport`

---

## Data Types

### SearchResult

```typescript
interface SearchResult {
  query: string;
  total_found: number;
  search_time_ms: number;
  candidates: CandidateRepository[];
}
```

### CandidateRepository

```typescript
interface CandidateRepository {
  platform: "github" | "huggingface" | "kaggle" | "gitlab";
  url: string;
  name: string;
  description: string;
  stars: number;
  last_updated: string;  // ISO date
  language: string;
  relevance_score: number;  // 0.0 - 1.0
  license: string | null;
}
```

### AnalysisResult

```typescript
interface AnalysisResult {
  repo_url: string;
  analysis_time_ms: number;
  language_breakdown: Record<string, number>;
  dependencies: {
    direct_count: number;
    transitive_count: number;
    conflicts: Conflict[];
  };
  code_metrics: {
    lines_of_code: number;
    files: number;
    cyclomatic_complexity_avg: number;
    test_coverage: number;
  };
  extractable_components: Component[];
  quality_score: number;
}
```

### SynthesisResult

```typescript
interface SynthesisResult {
  success: boolean;
  project_path: string;
  files_created: number;
  structure: Record<string, string[]>;
  dependencies_file: string;
  setup_commands: string[];
  synthesis_time_seconds: number;
  warnings: string[];
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": true,
  "code": "RESOLUTION_FAILED",
  "message": "Unable to resolve dependencies",
  "details": {
    "conflicts": [
      {
        "package": "numpy",
        "required": [">=2.0", "<1.26"],
        "by": ["package-a", "package-b"]
      }
    ]
  },
  "suggestions": [
    "Try adding constraint: numpy>=1.24,<2.0"
  ]
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `REPO_NOT_FOUND` | Repository URL invalid or inaccessible |
| `AUTH_FAILED` | API authentication failed |
| `RATE_LIMITED` | Platform rate limit exceeded |
| `RESOLUTION_FAILED` | Dependency resolution impossible |
| `SYNTHESIS_FAILED` | Code merge failed |
| `TIMEOUT` | Operation timed out |

---

## Rate Limits

| Platform | Authenticated | Unauthenticated |
|----------|---------------|-----------------|
| GitHub | 5,000/hour | 60/hour |
| HuggingFace | No strict limit | No strict limit |
| Kaggle | Undocumented | N/A |
| arXiv | 1 req/3 sec | 1 req/3 sec |
| Semantic Scholar | 100/sec with key | 1/sec |

The synthesizer implements automatic rate limit handling with exponential backoff.
