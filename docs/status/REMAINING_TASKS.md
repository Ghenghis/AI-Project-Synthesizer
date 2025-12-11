# 📋 AI Project Synthesizer - Remaining Tasks

**Last Updated**: December 11, 2025  
**Project Status**: 95% Complete  
**Estimated Time to 100%**: 2-4 hours

---

## 🔴 Critical Tasks (Must Fix)

### Task 1: Fix Failing Unit Tests (~30 minutes)

#### 1.1 Fix GitHub Client Tests
**File**: `tests/unit/test_github_client.py`

Add mocking to avoid hitting real GitHub API:

```python
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses."""
    with patch('src.discovery.github_client.GhApi') as mock:
        mock_instance = MagicMock()
        mock_instance.search.repos.return_value = {
            'total_count': 1,
            'items': [{
                'id': 12345,
                'html_url': 'https://github.com/test/repo',
                'name': 'repo',
                'full_name': 'test/repo',
                'description': 'Test repository',
                'owner': {'login': 'test'},
                'stargazers_count': 100,
                'forks_count': 10,
                'watchers_count': 50,
                'open_issues_count': 5,
                'language': 'Python',
                'license': {'spdx_id': 'MIT'},
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-12-01T00:00:00Z',
                'pushed_at': '2024-12-01T00:00:00Z',
                'topics': ['python', 'test'],
                'default_branch': 'main',
                'size': 1000,
            }]
        }
        mock.return_value = mock_instance
        yield mock_instance
```

#### 1.2 Fix SQLite Cache Test
**File**: `tests/unit/test_new_features.py`

```python
@pytest.fixture
def temp_cache_dir(tmp_path):
    """Provide temp directory for cache tests."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir

def test_sqlite_cache(temp_cache_dir):
    """Test SQLite cache with proper temp directory."""
    cache = SQLiteCache(cache_dir=temp_cache_dir)
    # ... rest of test
```

#### 1.3 Fix Telemetry Tests
Add proper fixture/mock setup for telemetry service.

#### 1.4 Fix Config Test
Update test expectations to match actual default values.

---

### Task 2: Implement HTTP Fallback (~45 minutes)
**File**: `src/discovery/github_client.py`

Replace `NotImplementedError` with working httpx:

```python
async def _search_fallback(
    self, query: str, language: Optional[str],
    min_stars: int, max_results: int,
    sort_by: str, order: str,
) -> SearchResult:
    """Fallback search using httpx."""
    import httpx
    
    search_query = query
    if language:
        search_query += f" language:{language}"
    if min_stars > 0:
        search_query += f" stars:>={min_stars}"
    
    headers = {}
    if self._token:
        headers["Authorization"] = f"token {self._token}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": search_query, "per_page": max_results},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    
    # Convert to RepositoryInfo objects
    repositories = [self._convert_repo_dict(item) 
                   for item in data.get("items", [])[:max_results]]
    
    return SearchResult(
        query=query,
        platform="github",
        total_count=data.get("total_count", 0),
        repositories=repositories,
        search_time_ms=0,
    )
```

---

## 🟡 Medium Priority Tasks

### Task 3: Clean Up Root Directory (~10 minutes)

```bash
# Remove artifact files
rm "compass_artifact_wf-*.md"
rm COMPLETION_STATUS.md  # if duplicate

# Move test artifacts
mv test_output.mp3 tests/fixtures/
mv assistant_voice.mp3 tests/fixtures/

# Consolidate reports
mkdir -p docs/reports
mv reports/*.md docs/reports/
```

### Task 4: Increase Test Coverage (~2 hours)

Add tests for:
1. `src/generation/readme_generator.py` (0% → 70%)
2. `src/generation/diagram_generator.py` (0% → 60%)
3. `src/llm/ollama_client.py` (0% → 50%)

---

## 🟢 Low Priority (Optional)

- Add more LLM providers (Groq, Together AI)
- Complete GitLab client
- Add monitoring dashboard

---

## Validation Commands

```bash
# Run all unit tests
pytest tests/unit/ -v --tb=short

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing

# Run linting
ruff check src/ tests/

# Full CI simulation
pytest tests/ -v && ruff check src/ && mypy src/
```

---

## Completion Criteria

Project is **100% complete** when:
1. [ ] All 143+ unit tests pass
2. [ ] Test coverage ≥ 80%
3. [ ] Root directory is clean
4. [ ] HTTP fallback implemented
5. [ ] All linting checks pass
