# 📚 AI Project Synthesizer - API Reference

## MCP Tools Documentation

### 1. search_repositories
Search for repositories across multiple platforms.

**Parameters:**
- `query` (string, required): Natural language search query
- `platforms` (array, optional): Platforms to search (github, huggingface, kaggle, arxiv) - default: ["github", "huggingface"]
- `max_results` (integer, optional): Maximum results per platform (1-100) - default: 20
- `language_filter` (string, optional): Filter by programming language
- `min_stars` (integer, optional): Minimum star count - default: 10

**Example:**
```python
result = await handle_search_repositories({
    "query": "machine learning pytorch",
    "platforms": ["github"],
    "max_results": 10,
    "language_filter": "python",
    "min_stars": 50
})
```

### 2. analyze_repository
Perform deep analysis of a repository.

**Parameters:**
- `repo_url` (string, required): Repository URL to analyze
- `include_transitive_deps` (boolean, optional): Include transitive dependencies
- `extract_components` (boolean, optional): Identify extractable components

**Example:**
```python
result = await handle_analyze_repository({
    "repo_url": "https://github.com/pytorch/pytorch",
    "include_transitive_deps": True,
    "extract_components": True
})
```

### 3. check_compatibility
Check if multiple repositories can work together.

**Parameters:**
- `repo_urls` (array, required): List of repository URLs
- `target_python_version` (string, optional): Target Python version (default: "3.11")

**Example:**
```python
result = await handle_check_compatibility({
    "repo_urls": [
        "https://github.com/pytorch/pytorch",
        "https://github.com/huggingface/transformers"
    ],
    "target_python_version": "3.11"
})
```

### 4. resolve_dependencies
Resolve and merge dependencies from multiple repositories.

**Parameters:**
- `repositories` (array, required): Repository URLs
- `constraints` (array, optional): Additional version constraints
- `python_version` (string, optional): Target Python version (default: "3.11")

**Example:**
```python
result = await handle_resolve_dependencies({
    "repositories": [
        "https://github.com/pytorch/pytorch",
        "https://github.com/huggingface/transformers"
    ],
    "constraints": ["numpy>=1.20"],
    "python_version": "3.11"
})
```

### 5. synthesize_project
Create a unified project from multiple repositories.

**Parameters:**
- `repositories` (array, required): Repository configurations
  - `repo_url` (string, required): Repository URL
  - `components` (array, optional): Components to extract
  - `destination` (string, optional): Target directory
- `project_name` (string, required): Name for synthesized project
- `output_path` (string, required): Output directory path
- `template` (string, optional): Project template (default: "python-default")

**Example:**
```python
result = await handle_synthesize_project({
    "repositories": [
        {
            "repo_url": "https://github.com/octocat/Hello-World",
            "components": ["src", "tests"],
            "destination": "src"
        }
    ],
    "project_name": "my-project",
    "output_path": "/tmp/my-project",
    "template": "python-default"
})
```

### 6. generate_documentation
Generate comprehensive documentation for a project.

**Parameters:**
- `project_path` (string, required): Path to the project
- `doc_types` (array, optional): Types of docs to generate - default: ["readme", "architecture", "api"]
- `llm_enhanced` (boolean, optional): Use LLM for enhancement - default: true

**Example:**
```python
result = await handle_generate_documentation({
    "project_path": "/tmp/my-project",
    "doc_types": ["readme", "architecture", "api"],
    "llm_enhanced": True
})
```

### 7. get_synthesis_status
Get the status of an ongoing synthesis operation.

**Parameters:**
- `synthesis_id` (string, required): Synthesis operation ID

**Example:**
```python
result = await handle_get_synthesis_status({
    "synthesis_id": "12345678-1234-1234-1234-123456789012"
})
```

## Response Format

All tools return a JSON object with the following structure:

**Success Response:**
```json
{
    "status": "success",
    "data": { ... },
    "message": "Operation completed successfully"
}
```

**Error Response:**
```json
{
    "error": true,
    "message": "Error description",
    "details": { ... }
}
```

## Error Handling

The system handles the following error cases:
- Invalid input parameters
- Network connectivity issues
- Repository not found
- Permission denied
- Dependency conflicts
- File system errors

## Rate Limits

- GitHub API: 60 requests/hour (unauthenticated)
- Search operations: 100 requests/minute
- Synthesis operations: 10 concurrent jobs

## Authentication

Configure tokens in `.env` file:
```env
GITHUB_TOKEN=ghp_your_token_here
HUGGINGFACE_TOKEN=hf_your_token_here
```

## Templates

Available project templates:
- `python-default`: Standard Python project
- `python-ml`: Machine learning project with ML dependencies
- `python-web`: Web application with Flask/FastAPI
- `minimal`: Bare bones project structure
