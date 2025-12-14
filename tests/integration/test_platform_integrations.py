"""
Integration Tests for Platform Components

Tests for GitLab, Firecrawl, and Browser-Use clients.
Implements Phase 6.1 of the VIBE MCP roadmap.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest

from src.automation.browser_client import BrowserClient, BrowserType, ViewportSize
from src.discovery.firecrawl_client import (
    FirecrawlClient,
    FirecrawlFormat,
    ScrapedContent,
)
from src.discovery.gitlab_client import GitLabClient, GitLabProject, GitLabVisibility
from src.llm.litellm_router import LiteLLMRouter, TaskType
from src.memory.mem0_integration import MemoryCategory, MemorySystem


class TestGitLabClient:
    """Test GitLab client functionality."""

    @pytest.fixture
    async def client(self):
        """Create GitLab client for testing."""
        client = GitLabClient(
            token=os.getenv("GITLAB_TOKEN"),
            url="https://gitlab.com"
        )
        yield client
        if client._session:
            await client._session.close()

    @pytest.mark.asyncio
    async def test_gitlab_connection(self, client):
        """Test GitLab API connection."""
        if not client.token:
            pytest.skip("No GitLab token provided")

        result = await client.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_search_projects(self, client):
        """Test project search functionality."""
        projects = await client.search_projects(
            query="python",
            limit=5,
            min_stars=10
        )

        assert len(projects) <= 5
        for project in projects:
            assert isinstance(project, GitLabProject)
            assert project.star_count >= 10
            assert "python" in project.name.lower() or "python" in project.description.lower()

    @pytest.mark.asyncio
    async def test_get_project(self, client):
        """Test getting a specific project."""
        # Use a known public project
        project = await client.get_project("gitlab-org/gitlab")

        assert isinstance(project, GitLabProject)
        assert project.name == "GitLab"
        assert project.path == "gitlab"
        assert project.visibility == GitLabVisibility.PUBLIC
        assert project.star_count > 0

    @pytest.mark.asyncio
    async def test_get_project_analytics(self, client):
        """Test project analytics."""
        analytics = await client.get_project_analytics("gitlab-org/gitlab")

        assert "project" in analytics
        assert "languages" in analytics
        assert "issues" in analytics
        assert "merge_requests" in analytics
        assert "pipelines" in analytics

        # Verify analytics structure
        assert analytics["project"]["id"] > 0
        assert analytics["issues"]["total"] >= 0
        assert analytics["merge_requests"]["total"] >= 0

    @pytest.mark.asyncio
    async def test_rate_limit_status(self, client):
        """Test rate limit status."""
        status = await client.get_rate_limit_status()

        assert "remaining" in status
        assert "reset_at" in status
        assert "reset_in_seconds" in status
        assert isinstance(status["remaining"], int)


class TestFirecrawlClient:
    """Test Firecrawl client functionality."""

    @pytest.fixture
    async def client(self):
        """Create Firecrawl client for testing."""
        client = FirecrawlClient(
            api_key=os.getenv("FIRECRAWL_API_KEY")
        )
        yield client
        if client._session:
            await client._session.close()

    @pytest.mark.asyncio
    async def test_firecrawl_connection(self, client):
        """Test Firecrawl API connection."""
        result = await client.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_scrape_url(self, client):
        """Test URL scraping."""
        content = await client.scrape_url(
            "https://example.com",
            formats=[FirecrawlFormat.MARKDOWN]
        )

        assert isinstance(content, ScrapedContent)
        assert content.url == "https://example.com"
        assert content.format == FirecrawlFormat.MARKDOWN
        assert len(content.content) > 0
        assert content.word_count > 0
        assert content.reading_time > 0
        assert "Example Domain" in content.title or "example" in content.title.lower()

    @pytest.mark.asyncio
    async def test_scrape_with_format(self, client):
        """Test scraping with different formats."""
        content_html = await client.scrape_url(
            "https://example.com",
            formats=[FirecrawlFormat.HTML]
        )

        content_text = await client.scrape_url(
            "https://example.com",
            formats=[FirecrawlFormat.TEXT]
        )

        assert content_html.format == FirecrawlFormat.HTML
        assert content_text.format == FirecrawlFormat.TEXT
        assert "<html" in content_html.content.lower()
        assert "<html" not in content_text.content.lower()

    @pytest.mark.asyncio
    async def test_map_site(self, client):
        """Test site mapping."""
        site_map = await client.map_site(
            "https://example.com",
            limit=10
        )

        assert site_map.base_url == "https://example.com"
        assert site_map.total_pages >= 1
        assert len(site_map.pages) >= 1
        assert site_map.crawled_at is not None

    @pytest.mark.asyncio
    async def test_batch_scrape(self, client):
        """Test batch scraping."""
        urls = [
            "https://example.com",
            "https://httpbin.org/html",
        ]

        contents = await client.batch_scrape(
            urls,
            formats=[FirecrawlFormat.MARKDOWN],
            concurrency=2
        )

        assert len(contents) == len(urls)
        for content in contents:
            assert isinstance(content, ScrapedContent)
            assert len(content.content) > 0

    @pytest.mark.asyncio
    async def test_clean_text(self, client):
        """Test text cleaning."""
        dirty_text = "  Hello\n\n\nWorld  \t\n  "
        clean = client.clean_text(dirty_text)

        assert clean == "Hello World"

    @pytest.mark.asyncio
    async def test_extract_links(self, client):
        """Test link extraction."""
        content = """
        <html>
        <body>
            <a href="https://example.com">Example</a>
            <a href="/page">Page</a>
            [Link](https://test.com)
        </body>
        </html>
        """

        links = client.extract_links(content, "https://base.com")

        assert "https://example.com" in links
        assert "https://base.com/page" in links
        assert "https://test.com" in links


class TestBrowserClient:
    """Test browser client functionality."""

    @pytest.fixture
    async def client(self):
        """Create browser client for testing."""
        client = BrowserClient(
            browser_type=BrowserType.CHROMIUM,
            headless=True,
            viewport=ViewportSize.DESKTOP
        )
        await client.start()
        yield client
        await client.stop()

    @pytest.mark.asyncio
    async def test_browser_start_stop(self):
        """Test browser start and stop."""
        client = BrowserClient()
        await client.start()

        assert client._browser is not None
        assert client._context is not None
        assert client._page is not None

        await client.stop()
        assert client._browser is None

    @pytest.mark.asyncio
    async def test_navigate(self, client):
        """Test page navigation."""
        result = await client.goto("https://example.com")

        assert result["success"] is True
        assert "example.com" in result["url"]
        assert result["title"] is not None
        assert result["status"] == 200

    @pytest.mark.asyncio
    async def test_get_page_content(self, client):
        """Test getting page content."""
        await client.goto("https://example.com")

        content_html = await client.get_page_content("html")
        content_text = await client.get_page_content("text")

        assert content_html["success"] is True
        assert content_text["success"] is True
        assert "<html" in content_html["content"].lower()
        assert "Example Domain" in content_text["content"]

    @pytest.mark.asyncio
    async def test_screenshot(self, client):
        """Test screenshot functionality."""
        await client.goto("https://example.com")

        result = await client.screenshot(full_page=False)

        assert result["success"] is True
        assert "data" in result  # Base64 encoded image
        assert result["size"] > 0

    @pytest.mark.asyncio
    async def test_evaluate_javascript(self, client):
        """Test JavaScript evaluation."""
        await client.goto("https://example.com")

        result = await client.evaluate("document.title")

        assert result["success"] is True
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_wait_for_selector(self, client):
        """Test waiting for selector."""
        await client.goto("https://example.com")

        result = await client.wait_for_selector("h1", timeout=5000)

        assert result["success"] is True
        assert result["selector"] == "h1"

    @pytest.mark.asyncio
    async def test_get_text(self, client):
        """Test getting element text."""
        await client.goto("https://example.com")

        result = await client.get_text("h1")

        assert result["success"] is True
        assert "Example Domain" in result["text"]

    @pytest.mark.asyncio
    async def test_browser_info(self, client):
        """Test getting browser information."""
        info = await client.get_browser_info()

        assert info["browser_type"] == BrowserType.CHROMIUM.value
        assert info["headless"] is True
        assert info["viewport"]["width"] == 1920
        assert info["viewport"]["height"] == 1080


class TestMemorySystem:
    """Test memory system functionality."""

    @pytest.fixture
    async def memory_system(self):
        """Create memory system for testing."""
        config = {
            "enable_consolidation": False,  # Disable for testing
            "enable_analytics": True,
        }
        system = MemorySystem(config)
        return system

    @pytest.mark.asyncio
    async def test_add_memory(self, memory_system):
        """Test adding a memory."""
        memory_id = await memory_system.add(
            content="Test memory content",
            category=MemoryCategory.CONTEXT,
            tags=["test", "integration"],
            importance=0.8
        )

        assert memory_id is not None
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_search_memory(self, memory_system):
        """Test searching memories."""
        # Add a memory first
        await memory_system.add(
            content="Python is a programming language",
            category=MemoryCategory.LEARNING,
            tags=["python", "programming"]
        )

        # Search for it
        results = await memory_system.search(
            query="python programming",
            limit=5
        )

        assert len(results) >= 1
        assert any("python" in r.get("memory", "").lower() for r in results)

    @pytest.mark.asyncio
    async def test_get_memory(self, memory_system):
        """Test getting a specific memory."""
        # Add a memory
        memory_id = await memory_system.add(
            content="Specific test memory",
            category=MemoryCategory.PREFERENCE
        )

        # Get it back
        memory = await memory_system.get(memory_id)

        assert memory is not None
        assert memory["content"] == "Specific test memory"
        assert memory["category"] == MemoryCategory.PREFERENCE.value

    @pytest.mark.asyncio
    async def test_update_memory(self, memory_system):
        """Test updating a memory."""
        # Add a memory
        memory_id = await memory_system.add(
            content="Original content",
            category=MemoryCategory.CONTEXT
        )

        # Update it
        success = await memory_system.update(
            memory_id,
            "Updated content"
        )

        assert success is True

        # Verify update
        memory = await memory_system.get(memory_id)
        assert memory["content"] == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_system):
        """Test deleting a memory."""
        # Add a memory
        memory_id = await memory_system.add(
            content="To be deleted",
            category=MemoryCategory.CONTEXT
        )

        # Delete it
        success = await memory_system.delete(memory_id)
        assert success is True

        # Verify deletion
        memory = await memory_system.get(memory_id)
        assert memory is None

    @pytest.mark.asyncio
    async def test_get_context_for_task(self, memory_system):
        """Test getting context for a task."""
        # Add relevant memories
        await memory_system.add(
            content="User prefers dark mode",
            category=MemoryCategory.PREFERENCE,
            tags=["ui", "theme"]
        )

        await memory_system.add(
            content="Decision: Use React for frontend",
            category=MemoryCategory.DECISION,
            tags=["frontend", "react"]
        )

        # Get context
        context = await memory_system.get_context_for_task(
            "Build a React application with dark mode",
            limit=5
        )

        assert context["task"] == "Build a React application with dark mode"
        assert "preferences" in context["summary"].lower()
        assert "decisions" in context["summary"].lower()
        assert len(context["memories"]) > 0

    @pytest.mark.asyncio
    async def test_memory_analytics(self, memory_system):
        """Test memory analytics."""
        # Add some memories
        await memory_system.add("Test 1", MemoryCategory.CONTEXT)
        await memory_system.add("Test 2", MemoryCategory.PREFERENCE)
        await memory_system.add("Test 3", MemoryCategory.LEARNING)

        # Get insights
        insights = await memory_system.get_memory_insights()

        assert insights["summary"]["total_memories"] >= 3
        assert "by_category" in insights["summary"]
        assert len(insights["summary"]["by_category"]) > 0

    @pytest.mark.asyncio
    async def test_export_memories(self, memory_system):
        """Test memory export."""
        # Add a memory
        await memory_system.add(
            content="Export test memory",
            category=MemoryCategory.CONTEXT,
            tags=["export", "test"]
        )

        # Export to JSON
        file_path = await memory_system.export_memories(
            format="json",
            category=MemoryCategory.CONTEXT
        )

        assert file_path is not None
        assert Path(file_path).exists()

        # Verify export
        with open(file_path) as f:
            data = json.load(f)
            assert len(data) >= 1
            assert any("Export test memory" in m.get("content", "") for m in data)


class TestLiteLLMRouter:
    """Test LiteLLM router functionality."""

    @pytest.fixture
    async def router(self):
        """Create LiteLLM router for testing."""
        return LiteLLMRouter()

    @pytest.mark.asyncio
    async def test_router_initialization(self, router):
        """Test router initialization."""
        assert router is not None
        assert len(router._models) > 0
        assert router._default_model is not None

    @pytest.mark.asyncio
    async def test_model_selection(self, router):
        """Test model selection logic."""
        # Simple task
        model = router.select_model(TaskType.SIMPLE)
        assert model is not None

        # Complex task
        model = router.select_model(TaskType.COMPLEX)
        assert model is not None

        # Code task
        model = router.select_model(TaskType.CODE)
        assert model is not None

    @pytest.mark.asyncio
    async def test_completion(self, router):
        """Test text completion."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("No API key provided")

        result = await router.complete(
            prompt="What is 2+2?",
            task_type=TaskType.SIMPLE,
            max_tokens=10
        )

        assert result.content is not None
        assert len(result.content) > 0
        assert result.model is not None
        assert result.usage is not None

    @pytest.mark.asyncio
    async def test_chat_completion(self, router):
        """Test chat completion."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("No API key provided")

        messages = [
            {"role": "user", "content": "Say 'Hello World'"}
        ]

        result = await router.chat(
            messages=messages,
            task_type=TaskType.SIMPLE,
            max_tokens=10
        )

        assert result.content is not None
        assert "hello" in result.content.lower()
        assert result.model is not None

    @pytest.mark.asyncio
    async def test_fallback_chain(self, router):
        """Test fallback chain functionality."""
        # This would need mocking in a real test scenario
        # For now, just verify the chain exists
        assert hasattr(router, "_fallback_chain")
        assert len(router._fallback_chain) > 0

    @pytest.mark.asyncio
    async def test_cost_tracking(self, router):
        """Test cost tracking."""
        initial_cost = router.get_total_cost()
        assert isinstance(initial_cost, float)
        assert initial_cost >= 0


# Test configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Integration test runner
async def run_all_integration_tests():
    """Run all integration tests."""
    print("\n=== Running Platform Integration Tests ===\n")

    # GitLab Tests
    print("Testing GitLab Client...")
    gitlab_client = GitLabClient()
    async with gitlab_client:
        await gitlab_client.test_connection()
        print("✓ GitLab connection test passed")

    # Firecrawl Tests
    print("\nTesting Firecrawl Client...")
    firecrawl_client = FirecrawlClient()
    async with firecrawl_client:
        await firecrawl_client.test_connection()
        content = await firecrawl_client.scrape_url("https://example.com")
        assert content.content is not None
        print("✓ Firecrawl scraping test passed")

    # Browser Tests
    print("\nTesting Browser Client...")
    browser_client = BrowserClient(headless=True)
    async with browser_client:
        await browser_client.goto("https://example.com")
        screenshot = await browser_client.screenshot()
        assert screenshot["success"] is True
        print("✓ Browser automation test passed")

    # Memory System Tests
    print("\nTesting Memory System...")
    memory_system = MemorySystem()
    memory_id = await memory_system.add("Test memory", MemoryCategory.CONTEXT)
    memory = await memory_system.get(memory_id)
    assert memory is not None
    print("✓ Memory system test passed")

    # LiteLLM Router Tests
    print("\nTesting LiteLLM Router...")
    llm_router = LiteLLMRouter()
    model = llm_router.select_model(TaskType.SIMPLE)
    assert model is not None
    print("✓ LiteLLM router test passed")

    print("\n=== All Integration Tests Passed! ===\n")


if __name__ == "__main__":
    asyncio.run(run_all_integration_tests())
