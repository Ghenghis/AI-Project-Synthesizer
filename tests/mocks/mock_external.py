"""
Mock external API services for testing.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock


class MockGitLabClient:
    """Mock GitLab client for testing."""

    def __init__(self):
        self.projects = []
        self.merge_requests = []
        self.issues = []
        self.pipelines = []
        self.webhooks = []

    def add_project(self, project: dict[str, Any]):
        """Add a mock project."""
        self.projects.append(project)

    def add_merge_request(self, mr: dict[str, Any]):
        """Add a mock merge request."""
        self.merge_requests.append(mr)

    async def get_project(self, project_id: int) -> dict[str, Any]:
        """Mock get project."""
        for project in self.projects:
            if project["id"] == project_id:
                return project
        return None

    async def get_merge_requests(
        self, project_id: int, state: str = "opened"
    ) -> list[dict[str, Any]]:
        """Mock get merge requests."""
        return [
            mr
            for mr in self.merge_requests
            if mr["project_id"] == project_id and mr["state"] == state
        ]

    async def create_merge_request(
        self, project_id: int, title: str, source_branch: str, target_branch: str
    ) -> dict[str, Any]:
        """Mock create merge request."""
        mr = {
            "id": len(self.merge_requests) + 1,
            "project_id": project_id,
            "title": title,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "state": "opened",
            "created_at": datetime.now().isoformat(),
        }
        self.merge_requests.append(mr)
        return mr

    async def get_pipeline(self, project_id: int, pipeline_id: int) -> dict[str, Any]:
        """Mock get pipeline."""
        for pipeline in self.pipelines:
            if pipeline["id"] == pipeline_id and pipeline["project_id"] == project_id:
                return pipeline
        return None

    async def create_pipeline(self, project_id: int, ref: str) -> dict[str, Any]:
        """Mock create pipeline."""
        pipeline = {
            "id": len(self.pipelines) + 1,
            "project_id": project_id,
            "ref": ref,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        self.pipelines.append(pipeline)
        return pipeline


class MockFirecrawlClient:
    """Mock Firecrawl client for testing."""

    def __init__(self):
        self.crawled_urls = []
        self.scraped_content = {}
        self.crawl_results = []

    def set_scraped_content(self, url: str, content: dict[str, Any]):
        """Set scraped content for a URL."""
        self.scraped_content[url] = content

    async def scrape_url(
        self, url: str, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Mock scrape URL."""
        self.crawled_urls.append(url)
        if url in self.scraped_content:
            return self.scraped_content[url]
        return {
            "url": url,
            "title": f"Mock Title for {url}",
            "content": f"Mock content for {url}",
            "markdown": f"# Mock Title\n\nMock content for {url}",
            "metadata": {"sourceURL": url, "pageStatusCode": 200, "pageError": None},
        }

    async def crawl_urls(
        self, urls: list[str], options: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Mock crawl URLs."""
        results = []
        for url in urls:
            result = await self.scrape_url(url, options)
            results.append(result)
        self.crawl_results.extend(results)
        return results

    async def search(
        self, query: str, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Mock search."""
        return {
            "success": True,
            "data": [
                {
                    "url": f"https://example.com/result1?q={query}",
                    "title": f"Mock Result 1 for {query}",
                    "description": f"Mock description for {query}",
                    "score": 0.95,
                },
                {
                    "url": f"https://example.com/result2?q={query}",
                    "title": f"Mock Result 2 for {query}",
                    "description": f"Another mock result for {query}",
                    "score": 0.85,
                },
            ],
        }


class MockSupabaseClient:
    """Mock Supabase client for testing."""

    def __init__(self):
        self.tables = {"projects": [], "tasks": [], "agent_memory": []}
        self.auth = MagicMock()
        self.auth.user = lambda: {"id": "mock_user_id"}

    def table(self, table_name: str):
        """Get table reference."""
        return MockTable(self.tables.get(table_name, []))

    async def rpc(self, function_name: str, params: dict[str, Any]) -> Any:
        """Mock RPC call."""
        if function_name == "get_project_stats":
            return {"total_projects": 10, "active_projects": 5, "completed_tasks": 100}
        return None


class MockTable:
    """Mock database table."""

    def __init__(self, data: list[dict[str, Any]]):
        self.data = data

    def select(self, columns: str = "*"):
        """Mock select."""
        return self

    def insert(self, record: dict[str, Any]):
        """Mock insert."""
        if isinstance(record, list):
            self.data.extend(record)
        else:
            self.data.append(record)
        return self

    def update(self, updates: dict[str, Any]):
        """Mock update."""
        return self

    def delete(self):
        """Mock delete."""
        return self

    def eq(self, column: str, value: Any):
        """Mock equals filter."""
        filtered_data = [row for row in self.data if row.get(column) == value]
        return MockTable(filtered_data)

    async def execute(self) -> list[dict[str, Any]]:
        """Mock execute."""
        return self.data.copy()


class MockGitHubClient:
    """Mock GitHub client for testing."""

    def __init__(self):
        self.repositories = []
        self.issues = []
        self.pull_requests = []
        self.commits = []

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Mock get repository."""
        for repo_data in self.repositories:
            if repo_data["owner"] == owner and repo_data["name"] == repo:
                return repo_data
        return {
            "id": 1,
            "name": repo,
            "owner": {"login": owner},
            "description": f"Mock {owner}/{repo} repository",
            "stars": 100,
            "forks": 50,
        }

    async def create_pull_request(
        self, owner: str, repo: str, title: str, head: str, base: str
    ) -> dict[str, Any]:
        """Mock create pull request."""
        pr = {
            "id": len(self.pull_requests) + 1,
            "number": len(self.pull_requests) + 1,
            "title": title,
            "head": head,
            "base": base,
            "state": "open",
            "created_at": datetime.now().isoformat(),
        }
        self.pull_requests.append(pr)
        return pr

    async def get_commits(
        self, owner: str, repo: str, sha: str | None = None
    ) -> list[dict[str, Any]]:
        """Mock get commits."""
        return self.commits.copy()
