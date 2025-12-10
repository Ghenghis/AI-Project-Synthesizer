# 📊 AI Project Synthesizer - System Diagrams

> **Professional Architecture Visualizations**  
> **Format:** Mermaid, PlantUML Compatible  
> **Last Updated:** December 2024

---

## Table of Contents

1. [System Overview Diagram](#1-system-overview-diagram)
2. [Component Architecture](#2-component-architecture)
3. [Data Flow Diagrams](#3-data-flow-diagrams)
4. [Sequence Diagrams](#4-sequence-diagrams)
5. [State Machine Diagrams](#5-state-machine-diagrams)
6. [Class Diagrams](#6-class-diagrams)
7. [Deployment Diagrams](#7-deployment-diagrams)
8. [Entity Relationship Diagrams](#8-entity-relationship-diagrams)

---

## 1. System Overview Diagram

### High-Level Architecture

```mermaid
flowchart TB
    subgraph IDE["🖥️ WINDSURF IDE"]
        CASCADE["🤖 Cascade AI"]
    end
    
    subgraph MCP["📡 MCP Protocol Layer"]
        direction TB
        TOOLS["🔧 Tools"]
        RESOURCES["📦 Resources"]
        PROMPTS["💬 Prompts"]
    end
    
    subgraph SYNTH["🧬 AI PROJECT SYNTHESIZER"]
        direction TB
        
        subgraph LAYERS["Processing Layers"]
            DISCOVERY["🔍 Discovery"]
            ANALYSIS["🔬 Analysis"]
            RESOLUTION["⚖️ Resolution"]
            SYNTHESIS["🔧 Synthesis"]
            GENERATION["📝 Generation"]
        end
        
        subgraph LLM["🧠 LLM Orchestration"]
            OLLAMA["Ollama\n(Local)"]
            CLOUD["Cloud APIs\n(Fallback)"]
            ROUTER["RouteLLM\nRouter"]
        end
    end
    
    subgraph EXTERNAL["🌐 External Services"]
        GITHUB["GitHub API"]
        HF["HuggingFace"]
        KAGGLE["Kaggle"]
        ARXIV["arXiv"]
    end
    
    subgraph OUTPUT["📁 Output"]
        PROJECT["Synthesized\nProject"]
        DOCS["Generated\nDocumentation"]
    end
    
    CASCADE -->|stdio| MCP
    MCP --> SYNTH
    DISCOVERY --> EXTERNAL
    LLM --> OLLAMA
    LLM --> CLOUD
    ROUTER --> LLM
    SYNTHESIS --> OUTPUT
    GENERATION --> DOCS
```

---

## 2. Component Architecture

### Layered Component View

```mermaid
flowchart TB
    subgraph INTERFACE["Interface Layer"]
        MCP_SERVER["MCP Server\n(FastMCP)"]
    end
    
    subgraph ORCHESTRATION["Orchestration Layer"]
        PIPELINE["Pipeline\nCoordinator"]
        STATE["State\nManager"]
        QUEUE["Task\nQueue"]
    end
    
    subgraph BUSINESS["Business Logic Layer"]
        subgraph DISC["Discovery"]
            GH_CLIENT["GitHub\nClient"]
            HF_CLIENT["HuggingFace\nClient"]
            KG_CLIENT["Kaggle\nClient"]
            UNIFIED["Unified\nSearch"]
        end
        
        subgraph ANAL["Analysis"]
            AST["AST\nParser"]
            DEP["Dependency\nAnalyzer"]
            QUAL["Quality\nScorer"]
            COMPAT["Compatibility\nChecker"]
        end
        
        subgraph RESOL["Resolution"]
            PY_RES["Python\nResolver"]
            NODE_RES["Node\nResolver"]
            CONFLICT["Conflict\nDetector"]
        end
        
        subgraph SYNTH_L["Synthesis"]
            BUILDER["Project\nBuilder"]
            SCAFFOLD["Scaffolder"]
            MERGER["Code\nMerger"]
        end
        
        subgraph GEN["Generation"]
            README_GEN["README\nGenerator"]
            DIAGRAM_GEN["Diagram\nGenerator"]
            API_GEN["API Doc\nGenerator"]
        end
    end
    
    subgraph AI["AI Layer"]
        LLM_CLIENT["LLM\nClient"]
        EMBEDDINGS["Embedding\nService"]
    end
    
    subgraph INFRA["Infrastructure Layer"]
        CONFIG["Config\nManager"]
        CACHE["Cache\n(Redis)"]
        LOGGER["Logging\nService"]
        METRICS["Metrics\nCollector"]
    end
    
    MCP_SERVER --> PIPELINE
    PIPELINE --> DISC
    PIPELINE --> ANAL
    PIPELINE --> RESOL
    PIPELINE --> SYNTH_L
    PIPELINE --> GEN
    
    DISC --> AI
    ANAL --> AI
    GEN --> AI
    
    DISC --> INFRA
    ANAL --> INFRA
    RESOL --> INFRA
    SYNTH_L --> INFRA
    GEN --> INFRA
```

---

## 3. Data Flow Diagrams

### Synthesis Pipeline Flow

```mermaid
flowchart LR
    subgraph INPUT["📥 Input"]
        REQ["User\nRequest"]
    end
    
    subgraph PARSE["🔍 Parse"]
        INTENT["Intent\nExtraction"]
    end
    
    subgraph DISCOVER["🔎 Discover"]
        SEARCH["Multi-Platform\nSearch"]
        RANK["Repository\nRanking"]
    end
    
    subgraph ANALYZE["🔬 Analyze"]
        AST_A["AST\nAnalysis"]
        DEP_A["Dependency\nMapping"]
        QUAL_A["Quality\nScoring"]
    end
    
    subgraph RESOLVE["⚖️ Resolve"]
        CONFLICT_R["Conflict\nDetection"]
        SAT["SAT\nSolver"]
        LOCK["Version\nLocking"]
    end
    
    subgraph SYNTHESIZE["🔧 Synthesize"]
        CLONE["Clone\nRepos"]
        EXTRACT["Extract\nComponents"]
        MERGE["Merge\nCode"]
        SCAFFOLD_S["Apply\nTemplate"]
    end
    
    subgraph GENERATE["📝 Generate"]
        README_G["README"]
        ARCH_G["Architecture"]
        DIAGRAMS_G["Diagrams"]
    end
    
    subgraph OUTPUT["📤 Output"]
        PROJ["Complete\nProject"]
    end
    
    REQ --> INTENT
    INTENT --> SEARCH
    SEARCH --> RANK
    RANK --> AST_A
    AST_A --> DEP_A
    DEP_A --> QUAL_A
    QUAL_A --> CONFLICT_R
    CONFLICT_R --> SAT
    SAT --> LOCK
    LOCK --> CLONE
    CLONE --> EXTRACT
    EXTRACT --> MERGE
    MERGE --> SCAFFOLD_S
    SCAFFOLD_S --> README_G
    README_G --> ARCH_G
    ARCH_G --> DIAGRAMS_G
    DIAGRAMS_G --> PROJ
```

### Repository Analysis Flow

```mermaid
flowchart TD
    REPO["📦 Repository URL"]
    
    subgraph CLONE_PHASE["Clone Phase"]
        SHALLOW["Shallow Clone\n(depth=1)"]
        CACHE_CHECK["Cache\nCheck"]
    end
    
    subgraph STRUCTURE["Structure Analysis"]
        FILE_SCAN["File\nScanning"]
        LANG_DETECT["Language\nDetection"]
        ENTRY_FIND["Entry Point\nDiscovery"]
    end
    
    subgraph DEPENDENCIES["Dependency Analysis"]
        DEP_FILES["Parse Dep\nFiles"]
        TRANSITIVE["Resolve\nTransitive"]
        CONFLICTS_D["Detect\nConflicts"]
    end
    
    subgraph CODE_ANAL["Code Analysis"]
        AST_PARSE["AST\nParsing"]
        METRICS_C["Metrics\nCalculation"]
        PATTERNS["Pattern\nDetection"]
    end
    
    subgraph QUALITY["Quality Assessment"]
        TESTS_Q["Test\nCoverage"]
        DOCS_Q["Documentation\nScore"]
        MAINTAIN["Maintainability\nIndex"]
    end
    
    subgraph OUTPUT_A["Analysis Output"]
        REPORT["Analysis\nReport"]
        COMPONENTS["Extractable\nComponents"]
        SCORE["Quality\nScore"]
    end
    
    REPO --> CACHE_CHECK
    CACHE_CHECK -->|miss| SHALLOW
    CACHE_CHECK -->|hit| STRUCTURE
    SHALLOW --> STRUCTURE
    
    FILE_SCAN --> DEP_FILES
    FILE_SCAN --> AST_PARSE
    LANG_DETECT --> AST_PARSE
    
    DEP_FILES --> TRANSITIVE
    TRANSITIVE --> CONFLICTS_D
    
    AST_PARSE --> METRICS_C
    AST_PARSE --> PATTERNS
    
    METRICS_C --> MAINTAIN
    PATTERNS --> COMPONENTS
    CONFLICTS_D --> REPORT
    MAINTAIN --> SCORE
    TESTS_Q --> SCORE
    DOCS_Q --> SCORE
```

---

## 4. Sequence Diagrams

### Full Synthesis Workflow

```mermaid
sequenceDiagram
    autonumber
    participant U as User (Windsurf)
    participant M as MCP Server
    participant D as Discovery
    participant A as Analysis
    participant R as Resolution
    participant S as Synthesis
    participant G as Generation
    participant L as LLM (Ollama)
    participant E as External APIs
    
    U->>M: synthesize_project(request)
    M->>L: parse_intent(request)
    L-->>M: StructuredIntent
    
    M->>D: search_repositories(intent)
    D->>E: GitHub API search
    D->>E: HuggingFace search
    E-->>D: Raw results
    D->>L: rank_repositories(results)
    L-->>D: Ranked list
    D-->>M: CandidateRepos[]
    
    loop For each candidate
        M->>A: analyze_repository(repo)
        A->>E: Clone repository
        A->>A: Parse AST
        A->>A: Analyze dependencies
        A-->>M: AnalysisResult
    end
    
    M->>R: resolve_dependencies(all_deps)
    R->>R: Detect conflicts
    R->>R: Run SAT solver
    R-->>M: ResolvedDeps
    
    M->>S: build_project(repos, config)
    S->>S: Clone selected repos
    S->>S: Extract components
    S->>S: Merge code
    S->>S: Apply template
    S-->>M: ProjectPath
    
    M->>G: generate_documentation(project)
    G->>L: Generate README
    G->>G: Create diagrams
    G-->>M: DocPaths[]
    
    M-->>U: SynthesisResult
```

### Repository Search Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant U as UnifiedSearch
    participant G as GitHubClient
    participant H as HuggingFaceClient
    participant K as KaggleClient
    participant R as RateLimiter
    participant CA as Cache
    
    C->>U: search(query, platforms)
    
    U->>CA: check_cache(query_hash)
    
    alt Cache Hit
        CA-->>U: cached_results
        U-->>C: SearchResult
    else Cache Miss
        par Parallel Search
            U->>G: search(query)
            G->>R: acquire_token()
            R-->>G: token
            G-->>U: github_results
        and
            U->>H: search(query)
            H->>R: acquire_token()
            R-->>H: token
            H-->>U: hf_results
        and
            U->>K: search(query)
            K->>R: acquire_token()
            R-->>K: token
            K-->>U: kaggle_results
        end
        
        U->>U: merge_and_rank(all_results)
        U->>CA: store(query_hash, results)
        U-->>C: SearchResult
    end
```

---

## 5. State Machine Diagrams

### Synthesis Pipeline States

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> Parsing: receive_request
    Parsing --> Discovering: intent_parsed
    Parsing --> Failed: parse_error
    
    Discovering --> Analyzing: repos_found
    Discovering --> Failed: no_repos_found
    
    Analyzing --> Resolving: analysis_complete
    Analyzing --> Discovering: need_more_repos
    Analyzing --> Failed: analysis_error
    
    Resolving --> Synthesizing: deps_resolved
    Resolving --> Failed: unresolvable_conflicts
    
    Synthesizing --> Generating: synthesis_complete
    Synthesizing --> Failed: synthesis_error
    
    Generating --> Complete: docs_generated
    Generating --> Complete: generation_skipped
    
    Complete --> [*]
    Failed --> Idle: reset
    
    note right of Discovering
        Searches multiple platforms
        in parallel
    end note
    
    note right of Resolving
        Uses SAT solver for
        dependency resolution
    end note
```

### Repository Processing States

```mermaid
stateDiagram-v2
    [*] --> Queued
    
    Queued --> Cloning: start_processing
    
    Cloning --> Analyzing: clone_complete
    Cloning --> Failed: clone_error
    
    state Analyzing {
        [*] --> ScanningFiles
        ScanningFiles --> ParsingAST
        ParsingAST --> AnalyzingDeps
        AnalyzingDeps --> ScoringQuality
        ScoringQuality --> [*]
    }
    
    Analyzing --> Ready: analysis_complete
    Analyzing --> Failed: analysis_error
    
    Ready --> Extracting: select_for_synthesis
    Ready --> Discarded: not_selected
    
    Extracting --> Extracted: extraction_complete
    Extracting --> Failed: extraction_error
    
    Extracted --> [*]
    Discarded --> [*]
    Failed --> [*]
```

---

## 6. Class Diagrams

### Discovery Layer Classes

```mermaid
classDiagram
    class PlatformClient {
        <<abstract>>
        +platform_name: str
        +is_authenticated: bool
        +search(query, **kwargs) SearchResult
        +get_repository(repo_id) RepositoryInfo
        +get_contents(repo_id, path) DirectoryListing
        +get_file(repo_id, path) FileContent
        +clone(repo_id, destination) Path
    }
    
    class GitHubClient {
        -_token: str
        -_api: GhApi
        -_rate_limiter: RateLimiter
        +search(query, language, min_stars) SearchResult
        +get_languages(repo_id) Dict
        +get_topics(repo_id) List
        +check_has_tests(repo_id) bool
        +check_has_ci(repo_id) bool
    }
    
    class HuggingFaceClient {
        -_token: str
        -_api: HfApi
        +search(query, task, library) SearchResult
        +get_model_info(model_id) ModelInfo
        +get_dataset_info(dataset_id) DatasetInfo
    }
    
    class UnifiedSearch {
        -_clients: Dict[str, PlatformClient]
        -_cache: Cache
        +search(query, platforms) SearchResult
        +rank_results(results) List[RepositoryInfo]
        -_merge_results(results) List[RepositoryInfo]
    }
    
    class RepositoryInfo {
        +platform: str
        +id: str
        +url: str
        +name: str
        +full_name: str
        +description: str
        +owner: str
        +stars: int
        +forks: int
        +language: str
        +license: str
        +topics: List[str]
    }
    
    class SearchResult {
        +query: str
        +platform: str
        +total_count: int
        +repositories: List[RepositoryInfo]
        +search_time_ms: int
        +has_more: bool
    }
    
    PlatformClient <|-- GitHubClient
    PlatformClient <|-- HuggingFaceClient
    UnifiedSearch --> PlatformClient
    UnifiedSearch --> SearchResult
    SearchResult --> RepositoryInfo
```

### Analysis Layer Classes

```mermaid
classDiagram
    class DependencyAnalyzer {
        +DEPENDENCY_FILES: Dict
        +analyze(repo_path) DependencyGraph
        -_parse_file(path, pm) Tuple
        -_parse_requirements_txt(path) List
        -_parse_pyproject_toml(path) Tuple
        -_detect_conflicts(deps) List
    }
    
    class Dependency {
        +name: str
        +version_spec: str
        +extras: List[str]
        +source_file: str
        +package_manager: str
        +is_dev: bool
        +normalized_name: str
    }
    
    class DependencyGraph {
        +direct: List[Dependency]
        +transitive: List[Dependency]
        +conflicts: List[DependencyConflict]
        +dev_dependencies: List[Dependency]
        +has_conflicts: bool
        +to_dict() dict
    }
    
    class DependencyConflict {
        +package_name: str
        +dep_a: Dependency
        +dep_b: Dependency
        +reason: str
        +resolvable: bool
        +suggested_version: str
    }
    
    class ASTParser {
        -_parsers: Dict[str, Parser]
        +parse_file(path) ParsedFile
        +extract_imports(parsed) List[Import]
        +extract_functions(parsed) List[Function]
        +extract_classes(parsed) List[Class]
    }
    
    class QualityScorer {
        +calculate_score(repo_path) QualityScore
        -_check_documentation(path) float
        -_check_tests(path) float
        -_check_ci(path) float
        -_calculate_complexity(path) float
    }
    
    DependencyAnalyzer --> Dependency
    DependencyAnalyzer --> DependencyGraph
    DependencyGraph --> DependencyConflict
    DependencyConflict --> Dependency
```

---

## 7. Deployment Diagrams

### Docker Deployment

```mermaid
flowchart TB
    subgraph HOST["Host Machine (Windows 11 + WSL2)"]
        subgraph DOCKER["Docker Environment"]
            subgraph NET["docker-network: synth-net"]
                SYNTH_C["🧬 synthesizer\nPython 3.11\nPort: 8080"]
                REDIS_C["💾 redis\nRedis Alpine\nPort: 6379"]
                OLLAMA_C["🧠 ollama\nOllama + GPU\nPort: 11434"]
            end
            
            subgraph VOLUMES["Volumes"]
                OUTPUT_V["📁 ./output\n→ /app/output"]
                CACHE_V["📁 ./cache\n→ /app/cache"]
                MODELS_V["📁 ./models\n→ /root/.ollama"]
            end
        end
        
        GPU["🎮 NVIDIA GPU\nRTX 3090/4090"]
    end
    
    SYNTH_C <--> REDIS_C
    SYNTH_C <--> OLLAMA_C
    OLLAMA_C --> GPU
    
    SYNTH_C --> OUTPUT_V
    SYNTH_C --> CACHE_V
    OLLAMA_C --> MODELS_V
```

### Local Development Setup

```mermaid
flowchart TB
    subgraph LOCAL["Local Development"]
        subgraph WINDSURF["Windsurf IDE"]
            CASCADE_L["Cascade AI"]
            EDITOR["Code Editor"]
            TERMINAL["Terminal"]
        end
        
        subgraph PYTHON["Python Environment"]
            VENV[".venv\nPython 3.11"]
            SERVER["MCP Server\nFastMCP"]
        end
        
        subgraph SERVICES["Background Services"]
            OLLAMA_L["Ollama Server\nlocalhost:11434"]
            REDIS_L["Redis\nlocalhost:6379"]
        end
        
        subgraph STORAGE["Local Storage"]
            OUTPUT_L["./output/"]
            LOGS_L["./logs/"]
            CACHE_L["./cache/"]
        end
    end
    
    CASCADE_L <-->|MCP stdio| SERVER
    EDITOR --> VENV
    TERMINAL --> VENV
    
    SERVER <--> OLLAMA_L
    SERVER <--> REDIS_L
    SERVER --> OUTPUT_L
    SERVER --> LOGS_L
    SERVER --> CACHE_L
```

---

## 8. Entity Relationship Diagrams

### Data Model

```mermaid
erDiagram
    SYNTHESIS_JOB ||--o{ REPOSITORY : includes
    SYNTHESIS_JOB ||--|| SYNTHESIS_CONFIG : has
    SYNTHESIS_JOB ||--|| SYNTHESIS_RESULT : produces
    
    REPOSITORY ||--o{ COMPONENT : contains
    REPOSITORY ||--|| ANALYSIS_RESULT : has
    REPOSITORY ||--o{ DEPENDENCY : requires
    
    ANALYSIS_RESULT ||--o{ CODE_METRIC : includes
    ANALYSIS_RESULT ||--o{ QUALITY_SCORE : includes
    
    DEPENDENCY ||--o{ CONFLICT : involves
    
    SYNTHESIS_RESULT ||--|| PROJECT : creates
    PROJECT ||--o{ GENERATED_DOC : includes
    
    SYNTHESIS_JOB {
        uuid id PK
        string status
        datetime created_at
        datetime updated_at
        json user_request
    }
    
    REPOSITORY {
        string id PK
        string platform
        string url
        string name
        int stars
        string language
        datetime last_updated
    }
    
    COMPONENT {
        uuid id PK
        string repository_id FK
        string name
        string path
        string type
        json dependencies
    }
    
    DEPENDENCY {
        uuid id PK
        string name
        string version_spec
        string package_manager
        boolean is_dev
    }
    
    CONFLICT {
        uuid id PK
        string package_name
        string reason
        boolean resolvable
        string suggested_version
    }
    
    ANALYSIS_RESULT {
        uuid id PK
        string repository_id FK
        json language_breakdown
        int loc
        float complexity
        datetime analyzed_at
    }
    
    PROJECT {
        uuid id PK
        string name
        string path
        datetime created_at
        json config
    }
    
    GENERATED_DOC {
        uuid id PK
        string project_id FK
        string type
        string path
        datetime generated_at
    }
```

---

## Diagram Rendering

### Tools for Viewing

1. **VS Code** - Install "Markdown Preview Mermaid Support" extension
2. **Windsurf** - Built-in Mermaid rendering in markdown preview
3. **GitHub** - Native Mermaid support in markdown files
4. **Mermaid Live Editor** - https://mermaid.live

### Export Options

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Export to PNG
mmdc -i docs/diagrams/DIAGRAMS.md -o docs/diagrams/output.png

# Export to SVG
mmdc -i docs/diagrams/DIAGRAMS.md -o docs/diagrams/output.svg

# Export to PDF
mmdc -i docs/diagrams/DIAGRAMS.md -o docs/diagrams/output.pdf
```

---

## Quick Reference

| Diagram Type | Use Case |
|--------------|----------|
| Flowchart | System architecture, data flows |
| Sequence | API interactions, workflows |
| State | Process states, transitions |
| Class | Object relationships, inheritance |
| ER | Data models, database design |

