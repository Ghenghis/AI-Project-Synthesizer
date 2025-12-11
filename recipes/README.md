# AI Synthesizer Recipes

Pre-configured project templates that combine multiple repositories into ready-to-use projects.

## What are Recipes?

Recipes are YAML files that define:
- **Source repositories** to pull code from
- **Components** to extract from each repo
- **Synthesis strategy** (merge, copy, selective)
- **Post-processing** steps (documentation, tests)

## Usage

```bash
# List available recipes
python -m src.cli recipe list

# Show recipe details
python -m src.cli recipe show story-mcp

# Run a recipe
python -m src.cli recipe run story-mcp --output G:/my-project

# Create a new recipe interactively
python -m src.cli recipe create
```

## Available Recipes

| Recipe | Description | Sources |
|--------|-------------|---------|
| `mcp-server-starter` | Basic MCP server template | FastMCP, example tools |
| `rag-chatbot` | RAG chatbot with local LLM | LangChain, ChromaDB, Ollama |
| `ai-camera-stack` | AI camera with object detection | Frigate, YOLO, MQTT |
| `web-scraper` | Async web scraper with proxy support | Playwright, aiohttp |

## Recipe Schema

```yaml
name: recipe-name
version: 1.0.0
description: What this recipe creates

# Source repositories
sources:
  - repo: https://github.com/owner/repo
    branch: main  # optional
    extract:
      - src/core/
      - src/utils/
    rename:
      src/core/: core/
      
  - repo: https://github.com/owner/repo2
    components:
      - name: auth
        path: src/auth/
      - name: api
        path: src/api/

# Synthesis configuration
synthesis:
  strategy: selective  # merge, copy, selective
  output_name: my-project
  template: python-default
  
  # Dependency handling
  dependencies:
    merge: true
    python_version: "3.11"
    
  # Conflict resolution
  conflicts:
    strategy: prefer_first  # prefer_first, prefer_last, manual

# Post-synthesis steps
post_synthesis:
  - generate_readme
  - generate_api_docs
  - run_tests
  - create_github_repo

# Variables (user-provided)
variables:
  project_name:
    description: Name for the project
    default: my-project
  github_org:
    description: GitHub organization
    required: false
```

## Creating Custom Recipes

1. Create a new YAML file in `recipes/`
2. Follow the schema above
3. Test with `python -m src.cli recipe validate my-recipe.yaml`
4. Run with `python -m src.cli recipe run my-recipe`

## Examples

See the `examples/` folder for complete recipe examples.
