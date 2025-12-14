"""
VIBE MCP - GitLab Client Integration

Comprehensive GitLab API client for project discovery and management.
Implements Phase 5.1 of the VIBE MCP roadmap.

Features:
- Full GitLab API v4 coverage
- Repository search and cloning
- Issue and merge request management
- CI/CD pipeline integration
- Project analytics and insights
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin

import aiohttp
import git

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class GitLabVisibility(Enum):
    """Project visibility levels."""

    PRIVATE = "private"
    INTERNAL = "internal"
    PUBLIC = "public"


class GitLabState(Enum):
    """Issue/MR state."""

    OPENED = "opened"
    CLOSED = "closed"
    MERGED = "merged"
    LOCKED = "locked"


class GitLabSort(Enum):
    """Sort options."""

    CREATED = "created_at"
    UPDATED = "updated_at"
    NAME = "name"
    PATH = "path"
    ID = "id"
    SIMILARITY = "similarity"


@dataclass
class GitLabProject:
    """GitLab project representation."""

    id: int
    name: str
    path: str
    description: str
    visibility: GitLabVisibility
    web_url: str
    http_url_to_repo: str
    ssh_url_to_repo: str
    star_count: int
    forks_count: int
    last_activity_at: datetime
    created_at: datetime
    default_branch: str
    topics: list[str] = field(default_factory=list)
    languages: dict[str, float] = field(default_factory=dict)
    readme: str | None = None
    archived: bool = False
    owner: dict[str, Any] | None = None


@dataclass
class GitLabIssue:
    """GitLab issue representation."""

    id: int
    iid: int
    title: str
    description: str
    state: GitLabState
    author: dict[str, Any]
    assignees: list[dict[str, Any]]
    labels: list[str]
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    due_date: str | None = None
    web_url: str = ""
    milestone: dict[str, Any] | None = None


@dataclass
class GitLabMergeRequest:
    """GitLab merge request representation."""

    id: int
    iid: int
    title: str
    description: str
    state: GitLabState
    author: dict[str, Any]
    source_branch: str
    target_branch: str
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None = None
    web_url: str = ""
    labels: list[str] = field(default_factory=list)
    changes: dict[str, Any] | None = None


@dataclass
class GitLabPipeline:
    """GitLab CI/CD pipeline representation."""

    id: int
    sha: str
    ref: str
    status: str
    created_at: datetime
    updated_at: datetime
    web_url: str = ""
    duration: int | None = None
    coverage: float | None = None


class GitLabClient:
    """
    Comprehensive GitLab API client.

    Provides full access to GitLab API v4 with async support,
    rate limiting, and intelligent caching.
    """

    def __init__(
        self,
        token: str | None = None,
        url: str = "https://gitlab.com",
        timeout: int = 30,
        per_page: int = 100,
    ):
        """
        Initialize GitLab client.

        Args:
            token: GitLab personal access token
            url: GitLab instance URL
            timeout: Request timeout in seconds
            per_page: Items per page for pagination
        """
        self.token = token or os.getenv("GITLAB_TOKEN")
        self.url = url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.per_page = per_page

        # Rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = datetime.now()

        # Cache
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=5)

        # Session
        self._session: aiohttp.ClientSession | None = None

        if not self.token:
            secure_logger.warning(
                "No GitLab token provided. Some features will be limited."
            )

        secure_logger.info(f"GitLab client initialized for {self.url}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self._session:
            headers = {
                "User-Agent": "VIBE-MCP/1.0",
                "Accept": "application/json",
            }

            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout,
                trust_env=True,  # Use proxy from environment
            )

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Make authenticated request to GitLab API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            use_cache: Whether to use cache for GET requests

        Returns:
            Response data
        """
        await self._ensure_session()

        # Check cache for GET requests
        if method.upper() == "GET" and use_cache:
            cache_key = f"{endpoint}:{str(params)}:{str(data)}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if datetime.now() - cached["timestamp"] < self._cache_ttl:
                    secure_logger.debug(f"Cache hit for {endpoint}")
                    return cached["data"]

        # Apply rate limiting
        await self._check_rate_limit()

        url = urljoin(f"{self.url}/api/v4/", endpoint.lstrip("/"))

        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=data,
            ) as response:
                # Update rate limit info
                if "RateLimit-Remaining" in response.headers:
                    self.rate_limit_remaining = int(
                        response.headers["RateLimit-Remaining"]
                    )
                if "RateLimit-Reset" in response.headers:
                    self.rate_limit_reset = datetime.fromtimestamp(
                        int(response.headers["RateLimit-Reset"])
                    )

                response.raise_for_status()
                data = await response.json()

                # Cache successful GET requests
                if method.upper() == "GET" and use_cache:
                    self._cache[cache_key] = {
                        "data": data,
                        "timestamp": datetime.now(),
                    }

                return data

        except aiohttp.ClientError as e:
            secure_logger.error(f"GitLab API request failed: {e}")
            raise

    async def _check_rate_limit(self):
        """Check and respect rate limits."""
        if self.rate_limit_remaining < 10:
            wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                secure_logger.warning(
                    f"Rate limit approaching. Waiting {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)

    async def _paginate(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Handle paginated responses.

        Args:
            endpoint: API endpoint
            params: Query parameters
            max_pages: Maximum pages to fetch

        Returns:
            All items from all pages
        """
        items = []
        page = 1

        while True:
            if max_pages and page > max_pages:
                break

            page_params = {"page": page, "per_page": self.per_page}
            if params:
                page_params.update(params)

            try:
                response = await self._request("GET", endpoint, params=page_params)

                if not response:
                    break

                items.extend(response)

                # Check if we have more pages
                if len(response) < self.per_page:
                    break

                page += 1

            except Exception as e:
                secure_logger.error(f"Pagination failed at page {page}: {e}")
                break

        return items

    # ========================================================================
    # PROJECT OPERATIONS
    # ========================================================================

    async def get_project(self, project_id: int | str) -> GitLabProject:
        """
        Get a single project by ID or path.

        Args:
            project_id: Project ID or path (e.g., "group/project")

        Returns:
            GitLab project
        """
        endpoint = f"/projects/{quote(str(project_id), safe='')}"
        data = await self._request("GET", endpoint)

        return self._parse_project(data)

    async def search_projects(
        self,
        query: str,
        sort: GitLabSort = GitLabSort.UPDATED,
        visibility: GitLabVisibility | None = None,
        min_stars: int = 0,
        language: str | None = None,
        archived: bool = False,
        limit: int = 50,
    ) -> list[GitLabProject]:
        """
        Search for projects.

        Args:
            query: Search query
            sort: Sort order
            visibility: Filter by visibility
            min_stars: Minimum star count
            language: Filter by programming language
            archived: Include archived projects
            limit: Maximum results

        Returns:
            List of matching projects
        """
        params = {
            "search": query,
            "sort": sort.value,
            "order_by": "desc",
            "archived": archived,
        }

        if visibility:
            params["visibility"] = visibility.value

        if min_stars > 0:
            params["min_stars"] = min_stars

        if language:
            params["language"] = language

        # Fetch with pagination
        max_pages = (limit + self.per_page - 1) // self.per_page
        results = await self._paginate("/projects", params, max_pages)

        # Parse and limit results
        projects = [self._parse_project(p) for p in results[:limit]]

        return projects

    async def get_project_languages(self, project_id: int | str) -> dict[str, float]:
        """
        Get language statistics for a project.

        Args:
            project_id: Project ID or path

        Returns:
            Dictionary mapping languages to percentages
        """
        endpoint = f"/projects/{quote(str(project_id), safe='')}/languages"
        data = await self._request("GET", endpoint)
        return data

    async def get_project_readme(self, project_id: int | str) -> str | None:
        """
        Get README content for a project.

        Args:
            project_id: Project ID or path

        Returns:
            README content or None if not found
        """
        try:
            endpoint = f"/projects/{quote(str(project_id), safe='')}/repository/files/README.md/raw"
            params = {"ref": "main"}

            try:
                async with self._session.get(
                    urljoin(f"{self.url}/api/v4/", endpoint.lstrip("/")),
                    params=params,
                ) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception:
                # Try other common README names
                for name in ["README.rst", "README.txt", "readme.md", "README"]:
                    try:
                        endpoint = f"/projects/{quote(str(project_id), safe='')}/repository/files/{quote(name, safe='')}/raw"
                        async with self._session.get(
                            urljoin(f"{self.url}/api/v4/", endpoint.lstrip("/")),
                            params=params,
                        ) as response:
                            if response.status == 200:
                                return await response.text()
                    except Exception:
                        continue

            return None

        except Exception as e:
            secure_logger.error(f"Failed to get README: {e}")
            return None

    async def clone_project(
        self,
        project: GitLabProject,
        target_dir: Path,
        use_ssh: bool = False,
    ) -> Path:
        """
        Clone a GitLab project.

        Args:
            project: Project to clone
            target_dir: Target directory
            use_ssh: Use SSH URL instead of HTTPS

        Returns:
            Path to cloned repository
        """
        repo_url = project.ssh_url_to_repo if use_ssh else project.http_url_to_repo
        repo_path = target_dir / project.path

        secure_logger.info(f"Cloning {project.name} to {repo_path}")

        try:
            git.Repo.clone_from(repo_url, repo_path)
            secure_logger.info(f"Successfully cloned {project.name}")
            return repo_path

        except git.GitError as e:
            secure_logger.error(f"Failed to clone {project.name}: {e}")
            raise

    def _parse_project(self, data: dict[str, Any]) -> GitLabProject:
        """Parse project data from API response."""
        return GitLabProject(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            description=data.get("description", ""),
            visibility=GitLabVisibility(data["visibility"]),
            web_url=data["web_url"],
            http_url_to_repo=data["http_url_to_repo"],
            ssh_url_to_repo=data["ssh_url_to_repo"],
            star_count=data["star_count"],
            forks_count=data["forks_count"],
            last_activity_at=datetime.fromisoformat(data["last_activity_at"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            default_branch=data.get("default_branch", "main"),
            topics=data.get("topics", []),
            languages=data.get("languages", {}),
            owner=data.get("owner"),
            archived=data.get("archived", False),
        )

    # ========================================================================
    # ISSUE OPERATIONS
    # ========================================================================

    async def get_issues(
        self,
        project_id: int | str,
        state: GitLabState | None = None,
        labels: list[str] | None = None,
        assignee_id: int | None = None,
        created_after: datetime | None = None,
        limit: int = 50,
    ) -> list[GitLabIssue]:
        """
        Get issues for a project.

        Args:
            project_id: Project ID or path
            state: Filter by state
            labels: Filter by labels
            assignee_id: Filter by assignee
            created_after: Filter by creation date
            limit: Maximum results

        Returns:
            List of issues
        """
        params = {}

        if state:
            params["state"] = state.value

        if labels:
            params["labels"] = ",".join(labels)

        if assignee_id:
            params["assignee_id"] = assignee_id

        if created_after:
            params["created_after"] = created_after.isoformat()

        # Fetch with pagination
        max_pages = (limit + self.per_page - 1) // self.per_page
        results = await self._paginate(
            f"/projects/{quote(str(project_id), safe='')}/issues",
            params,
            max_pages,
        )

        # Parse and limit results
        issues = [self._parse_issue(i) for i in results[:limit]]

        return issues

    async def create_issue(
        self,
        project_id: int | str,
        title: str,
        description: str,
        labels: list[str] | None = None,
        assignee_ids: list[int] | None = None,
        due_date: str | None = None,
    ) -> GitLabIssue:
        """
        Create a new issue.

        Args:
            project_id: Project ID or path
            title: Issue title
            description: Issue description
            labels: Issue labels
            assignee_ids: Assignee IDs
            due_date: Due date (YYYY-MM-DD)

        Returns:
            Created issue
        """
        endpoint = f"/projects/{quote(str(project_id), safe='')}/issues"

        data = {
            "title": title,
            "description": description,
        }

        if labels:
            data["labels"] = ",".join(labels)

        if assignee_ids:
            data["assignee_ids"] = assignee_ids

        if due_date:
            data["due_date"] = due_date

        response = await self._request("POST", endpoint, data=data)
        return self._parse_issue(response)

    def _parse_issue(self, data: dict[str, Any]) -> GitLabIssue:
        """Parse issue data from API response."""
        return GitLabIssue(
            id=data["id"],
            iid=data["iid"],
            title=data["title"],
            description=data["description"],
            state=GitLabState(data["state"]),
            author=data["author"],
            assignees=data.get("assignees", []),
            labels=data.get("labels", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            closed_at=datetime.fromisoformat(data["closed_at"])
            if data.get("closed_at")
            else None,
            due_date=data.get("due_date"),
            web_url=data["web_url"],
            milestone=data.get("milestone"),
        )

    # ========================================================================
    # MERGE REQUEST OPERATIONS
    # ========================================================================

    async def get_merge_requests(
        self,
        project_id: int | str,
        state: GitLabState | None = None,
        source_branch: str | None = None,
        target_branch: str | None = None,
        limit: int = 50,
    ) -> list[GitLabMergeRequest]:
        """
        Get merge requests for a project.

        Args:
            project_id: Project ID or path
            state: Filter by state
            source_branch: Filter by source branch
            target_branch: Filter by target branch
            limit: Maximum results

        Returns:
            List of merge requests
        """
        params = {}

        if state:
            params["state"] = state.value

        if source_branch:
            params["source_branch"] = source_branch

        if target_branch:
            params["target_branch"] = target_branch

        # Fetch with pagination
        max_pages = (limit + self.per_page - 1) // self.per_page
        results = await self._paginate(
            f"/projects/{quote(str(project_id), safe='')}/merge_requests",
            params,
            max_pages,
        )

        # Parse and limit results
        mrs = [self._parse_merge_request(mr) for mr in results[:limit]]

        return mrs

    def _parse_merge_request(self, data: dict[str, Any]) -> GitLabMergeRequest:
        """Parse merge request data from API response."""
        return GitLabMergeRequest(
            id=data["id"],
            iid=data["iid"],
            title=data["title"],
            description=data["description"],
            state=GitLabState(data["state"]),
            author=data["author"],
            source_branch=data["source_branch"],
            target_branch=data["target_branch"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            merged_at=datetime.fromisoformat(data["merged_at"])
            if data.get("merged_at")
            else None,
            web_url=data["web_url"],
            labels=data.get("labels", []),
            changes=data.get("changes"),
        )

    # ========================================================================
    # CI/CD OPERATIONS
    # ========================================================================

    async def get_pipelines(
        self,
        project_id: int | str,
        ref: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[GitLabPipeline]:
        """
        Get CI/CD pipelines for a project.

        Args:
            project_id: Project ID or path
            ref: Filter by branch/tag
            status: Filter by status
            limit: Maximum results

        Returns:
            List of pipelines
        """
        params = {}

        if ref:
            params["ref"] = ref

        if status:
            params["status"] = status

        # Fetch with pagination
        max_pages = (limit + self.per_page - 1) // self.per_page
        results = await self._paginate(
            f"/projects/{quote(str(project_id), safe='')}/pipelines",
            params,
            max_pages,
        )

        # Parse and limit results
        pipelines = [self._parse_pipeline(p) for p in results[:limit]]

        return pipelines

    def _parse_pipeline(self, data: dict[str, Any]) -> GitLabPipeline:
        """Parse pipeline data from API response."""
        return GitLabPipeline(
            id=data["id"],
            sha=data["sha"],
            ref=data["ref"],
            status=data["status"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            web_url=data["web_url"],
            duration=data.get("duration"),
            coverage=data.get("coverage"),
        )

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    async def get_project_analytics(self, project_id: int | str) -> dict[str, Any]:
        """
        Get comprehensive analytics for a project.

        Args:
            project_id: Project ID or path

        Returns:
            Analytics data
        """
        project = await self.get_project(project_id)

        # Get additional data
        languages = await self.get_project_languages(project_id)
        issues = await self.get_issues(project_id, limit=100)
        mrs = await self.get_merge_requests(project_id, limit=100)
        pipelines = await self.get_pipelines(project_id, limit=50)

        # Calculate metrics
        open_issues = sum(1 for i in issues if i.state == GitLabState.OPENED)
        closed_issues = sum(1 for i in issues if i.state == GitLabState.CLOSED)

        open_mrs = sum(1 for mr in mrs if mr.state == GitLabState.OPENED)
        merged_mrs = sum(1 for mr in mrs if mr.state == GitLabState.MERGED)

        successful_pipelines = sum(1 for p in pipelines if p.status == "success")
        total_pipelines = len(pipelines)

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "stars": project.star_count,
                "forks": project.forks_count,
                "age_days": (datetime.now() - project.created_at).days,
                "last_activity_days": (datetime.now() - project.last_activity_at).days,
            },
            "languages": languages,
            "issues": {
                "total": len(issues),
                "open": open_issues,
                "closed": closed_issues,
                "open_rate": open_issues / len(issues) if issues else 0,
            },
            "merge_requests": {
                "total": len(mrs),
                "open": open_mrs,
                "merged": merged_mrs,
                "merge_rate": merged_mrs / len(mrs) if mrs else 0,
            },
            "pipelines": {
                "total": total_pipelines,
                "successful": successful_pipelines,
                "success_rate": successful_pipelines / total_pipelines
                if total_pipelines
                else 0,
            },
            "activity": {
                "issues_per_month": self._calculate_monthly_rate(issues),
                "mrs_per_month": self._calculate_monthly_rate(mrs),
                "pipelines_per_month": self._calculate_monthly_rate(pipelines),
            },
        }

    def _calculate_monthly_rate(self, items: list[Any]) -> float:
        """Calculate monthly creation rate for items."""
        if not items:
            return 0.0

        # Get creation dates
        dates = []
        for item in items:
            if hasattr(item, "created_at"):
                dates.append(item.created_at)
            elif isinstance(item, dict) and "created_at" in item:
                dates.append(datetime.fromisoformat(item["created_at"]))

        if not dates:
            return 0.0

        # Calculate rate over last 90 days
        cutoff = datetime.now() - timedelta(days=90)
        recent = sum(1 for d in dates if d > cutoff)

        return recent / 3.0  # Per month

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    async def get_current_user(self) -> dict[str, Any]:
        """Get current authenticated user."""
        return await self._request("GET", "/user")

    async def get_user_projects(
        self,
        user_id: int | None = None,
        visibility: GitLabVisibility | None = None,
        limit: int = 50,
    ) -> list[GitLabProject]:
        """
        Get projects for a user.

        Args:
            user_id: User ID (None for current user)
            visibility: Filter by visibility
            limit: Maximum results

        Returns:
            List of user projects
        """
        endpoint = "/projects" if not user_id else f"/users/{user_id}/projects"

        params = {}
        if visibility:
            params["visibility"] = visibility.value

        # Fetch with pagination
        max_pages = (limit + self.per_page - 1) // self.per_page
        results = await self._paginate(endpoint, params, max_pages)

        # Parse and limit results
        projects = [self._parse_project(p) for p in results[:limit]]

        return projects

    # ========================================================================
    # GROUP OPERATIONS
    # ========================================================================

    async def get_group_projects(
        self,
        group_id: int | str,
        include_subgroups: bool = True,
        visibility: GitLabVisibility | None = None,
        limit: int = 50,
    ) -> list[GitLabProject]:
        """
        Get projects in a group.

        Args:
            group_id: Group ID or path
            include_subgroups: Include projects from subgroups
            visibility: Filter by visibility
            limit: Maximum results

        Returns:
            List of group projects
        """
        endpoint = f"/groups/{quote(str(group_id), safe='')}/projects"

        params = {
            "include_subgroups": include_subgroups,
        }

        if visibility:
            params["visibility"] = visibility.value

        # Fetch with pagination
        max_pages = (limit + self.per_page - 1) // self.per_page
        results = await self._paginate(endpoint, params, max_pages)

        # Parse and limit results
        projects = [self._parse_project(p) for p in results[:limit]]

        return projects

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def test_connection(self) -> bool:
        """Test connection to GitLab API."""
        try:
            await self.get_current_user()
            secure_logger.info("GitLab API connection successful")
            return True
        except Exception as e:
            secure_logger.error(f"GitLab API connection failed: {e}")
            return False

    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        secure_logger.info("Cache cleared")

    async def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status."""
        return {
            "remaining": self.rate_limit_remaining,
            "reset_at": self.rate_limit_reset.isoformat(),
            "reset_in_seconds": max(
                0, (self.rate_limit_reset - datetime.now()).total_seconds()
            ),
        }


# Factory function
async def create_gitlab_client(
    token: str | None = None,
    url: str = "https://gitlab.com",
) -> GitLabClient:
    """
    Create and initialize GitLab client.

    Args:
        token: GitLab personal access token
        url: GitLab instance URL

    Returns:
        Initialized GitLab client
    """
    client = GitLabClient(token=token, url=url)

    # Test connection
    if await client.test_connection():
        return client
    else:
        raise RuntimeError("Failed to connect to GitLab API")


# CLI interface for testing
async def main():
    """Test the GitLab client."""
    import argparse

    parser = argparse.ArgumentParser(description="GitLab Client Test")
    parser.add_argument("--token", help="GitLab personal access token")
    parser.add_argument("--url", default="https://gitlab.com", help="GitLab URL")
    parser.add_argument("--search", help="Search query for projects")
    parser.add_argument("--project", help="Project ID or path")
    parser.add_argument("--clone", help="Clone project to directory")
    parser.add_argument("--ssh", action="store_true", help="Use SSH for cloning")

    args = parser.parse_args()

    # Create client
    try:
        client = await create_gitlab_client(token=args.token, url=args.url)
    except RuntimeError as e:
        print(f"Failed to create GitLab client: {e}")
        return

    async with client:
        # Test user info
        user = await client.get_current_user()
        print(f"\nAuthenticated as: {user['name']} ({user['username']})")

        # Search projects
        if args.search:
            print(f"\nSearching for: {args.search}")
            projects = await client.search_projects(args.search, limit=10)

            for project in projects:
                print(f"\n  {project.name}")
                print(f"  URL: {project.web_url}")
                print(f"  Stars: {project.star_count} | Forks: {project.forks_count}")
                print(f"  Description: {project.description[:100]}...")

        # Get project details
        if args.project:
            print(f"\nGetting project: {args.project}")
            project = await client.get_project(args.project)

            print(f"\n  {project.name}")
            print(f"  ID: {project.id}")
            print(f"  Visibility: {project.visibility.value}")
            print(f"  Default Branch: {project.default_branch}")
            print(f"  Topics: {', '.join(project.topics)}")

            # Get analytics
            analytics = await client.get_project_analytics(project.id)
            print("\n  Analytics:")
            print(
                f"    Issues: {analytics['issues']['total']} ({analytics['issues']['open']} open)"
            )
            print(
                f"    MRs: {analytics['merge_requests']['total']} ({analytics['merge_requests']['merged']} merged)"
            )
            print(
                f"    Pipeline Success Rate: {analytics['pipelines']['success_rate']:.1%}"
            )

            # Clone if requested
            if args.clone:
                target = Path(args.clone)
                await client.clone_project(project, target, use_ssh=args.ssh)
                print(f"\n  Cloned to: {target / project.path}")

        # Rate limit status
        rate_limit = await client.get_rate_limit_status()
        print(f"\nRate Limit: {rate_limit['remaining']} requests remaining")
        print(f"Resets in: {rate_limit['reset_in_seconds']:.0f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
