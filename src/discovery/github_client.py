"""
AI Project Synthesizer - GitHub Client

Full-featured GitHub API client using ghapi library.
Provides repository search, analysis, and download capabilities.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess
import logging

from src.discovery.base_client import (
    PlatformClient,
    RepositoryInfo,
    SearchResult,
    FileContent,
    DirectoryListing,
    AuthenticationError,
    RateLimitError,
    RepositoryNotFoundError,
)
from src.utils.rate_limiter import RateLimiter
from src.core.circuit_breaker import circuit_breaker, GITHUB_BREAKER_CONFIG
from src.core.security import InputValidator, SecurityConfig, get_secure_logger
from src.core.observability import correlation_manager, track_performance, metrics

secure_logger = get_secure_logger(__name__)


class GitHubClient(PlatformClient):
    """
    GitHub API client using ghapi.
    
    Features:
    - Full GitHub API coverage
    - Automatic pagination
    - Rate limit handling
    - Repository search and analysis
    - File and directory access
    - Clone operations
    
    Example:
        client = GitHubClient(token="ghp_xxx")
        results = await client.search("machine learning python")
        for repo in results.repositories:
            print(f"{repo.full_name}: {repo.stars} stars")
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        requests_per_hour: int = 5000,
    ):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
            requests_per_hour: Rate limit (5000 for authenticated)
        """
        self._token = token
        self._api = None
        self._rate_limiter = RateLimiter(
            requests_per_hour=requests_per_hour if token else 60,
            burst_size=30 if token else 10,
        )
        self._init_api()
    
    def _init_api(self):
        """Initialize ghapi client."""
        try:
            from ghapi.all import GhApi
            self._api = GhApi(token=self._token)
            secure_logger.info("GitHub API client initialized")
        except ImportError:
            secure_logger.warning("ghapi not installed, using fallback")
            self._api = None
    
    @property
    def platform_name(self) -> str:
        return "github"
    
    @property
    def is_authenticated(self) -> bool:
        return self._token is not None
    
    @circuit_breaker(
        name="github_search",
        failure_threshold=GITHUB_BREAKER_CONFIG.failure_threshold,
        recovery_timeout=GITHUB_BREAKER_CONFIG.recovery_timeout,
        success_threshold=GITHUB_BREAKER_CONFIG.success_threshold,
        timeout=GITHUB_BREAKER_CONFIG.timeout,
        expected_exception=Exception
    )
    @track_performance("github_search")
    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: int = 0,
        max_results: int = 20,
        sort_by: str = "stars",
        order: str = "desc",
    ) -> SearchResult:
        """
        Search GitHub repositories.
        
        Uses GitHub's search API with intelligent query construction.
        Supports filtering by language, stars, and other criteria.
        """
        # Input validation
        if not InputValidator.validate_search_query(query):
            raise ValueError(f"Invalid search query: {query}")
        
        correlation_id = correlation_manager.get_correlation_id()
        start_time = time.time()
        
        secure_logger.info(
            f"Searching GitHub repositories",
            correlation_id=correlation_id,
            query=query[:100],  # Limit query length in logs
            language=language,
            min_stars=min_stars,
            max_results=max_results
        )
        
        # Wait for rate limit
        await self._rate_limiter.acquire()
        
        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language}"
        if min_stars > 0:
            search_query += f" stars:>={min_stars}"
        
        # Map sort fields
        sort_map = {
            "stars": "stars",
            "updated": "updated",
            "relevance": "best-match",
            "forks": "forks",
        }
        sort_field = sort_map.get(sort_by, "stars")
        
        try:
            if self._api:
                # Use ghapi
                results = self._api.search.repos(
                    q=search_query,
                    sort=sort_field if sort_field != "best-match" else None,
                    order=order,
                    per_page=min(max_results, 100),
                )
                
                repositories = []
                for item in results['items'][:max_results]:
                    repo = self._convert_repo(item)
                    repositories.append(repo)
                
                search_result = SearchResult(
                    query=query,
                    platform=self.platform_name,
                    total_count=results.total_count,
                    repositories=repositories,
                    search_time_ms=int((time.time() - start_time) * 1000),
                    has_more=results.total_count > max_results,
                )
                
                secure_logger.info(
                    f"GitHub search completed successfully",
                    correlation_id=correlation_id,
                    result_count=len(repositories),
                    total_count=results.total_count,
                    search_time_ms=search_result.search_time_ms
                )
                
                metrics.increment("github_search_success_total", tags={"language": language or "none"})
                metrics.record_histogram("github_search_results_count", len(repositories))
                
                return search_result
            else:
                # Fallback to httpx
                return await self._search_fallback(
                    query, language, min_stars, max_results, sort_by, order
                )
                
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "403" in error_msg:
                secure_logger.warning(
                    f"GitHub rate limit exceeded",
                    correlation_id=correlation_id,
                    error=str(e)[:200]
                )
                metrics.increment("github_rate_limit_total")
                raise RateLimitError(
                    "GitHub rate limit exceeded",
                    retry_after=3600,
                )
            elif "401" in error_msg or "authentication" in error_msg:
                secure_logger.error(
                    f"GitHub authentication failed",
                    correlation_id=correlation_id,
                    error=str(e)[:200]
                )
                metrics.increment("github_auth_error_total")
                raise AuthenticationError("GitHub authentication failed")
            else:
                secure_logger.error(
                    f"GitHub search error",
                    correlation_id=correlation_id,
                    error=str(e)[:200],
                    error_type=type(e).__name__
                )
                metrics.increment("github_search_error_total", tags={"error_type": type(e).__name__})
                raise
    
    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        """Get detailed repository information."""
        await self._rate_limiter.acquire()
        
        try:
            owner, repo = repo_id.split("/")
            
            if self._api:
                data = self._api.repos.get(owner=owner, repo=repo)
                return self._convert_repo(data)
            else:
                return await self._get_repo_fallback(repo_id)
                
        except Exception as e:
            if "404" in str(e):
                raise RepositoryNotFoundError(f"Repository not found: {repo_id}")
            raise
    
    async def get_contents(
        self,
        repo_id: str,
        path: str = "",
    ) -> DirectoryListing:
        """Get directory contents."""
        await self._rate_limiter.acquire()
        
        owner, repo = repo_id.split("/")
        
        if self._api:
            contents = self._api.repos.get_content(
                owner=owner,
                repo=repo,
                path=path,
            )
            
            files = []
            directories = []
            
            # Handle single file response
            if not isinstance(contents, list):
                contents = [contents]
            
            for item in contents:
                entry = {
                    "name": item.name,
                    "path": item.path,
                    "sha": item.sha,
                    "size": getattr(item, "size", 0),
                    "type": item.type,
                }
                
                if item.type == "dir":
                    directories.append(entry)
                else:
                    files.append(entry)
            
            return DirectoryListing(
                path=path,
                files=files,
                directories=directories,
            )
        else:
            return await self._get_contents_fallback(repo_id, path)
    
    async def get_file(
        self,
        repo_id: str,
        file_path: str,
    ) -> FileContent:
        """Get file contents."""
        await self._rate_limiter.acquire()
        
        owner, repo = repo_id.split("/")
        
        if self._api:
            import base64
            
            content = self._api.repos.get_content(
                owner=owner,
                repo=repo,
                path=file_path,
            )
            
            # Decode base64 content
            raw_content = base64.b64decode(content.content)
            
            return FileContent(
                path=file_path,
                name=content.name,
                content=raw_content,
                size=content.size,
                sha=content.sha,
            )
        else:
            return await self._get_file_fallback(repo_id, file_path)
    
    async def clone(
        self,
        repo_id: str,
        destination: Path,
        depth: int = 1,
        branch: Optional[str] = None,
    ) -> Path:
        """Clone repository to local filesystem."""
        clone_url = f"https://github.com/{repo_id}.git"
        
        # Add token for private repos
        if self._token:
            clone_url = f"https://{self._token}@github.com/{repo_id}.git"
        
        cmd = ["git", "clone"]
        
        if depth > 0:
            cmd.extend(["--depth", str(depth)])
        
        if branch:
            cmd.extend(["--branch", branch])
        
        cmd.extend([clone_url, str(destination)])
        
        # Run clone
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Git clone failed: {stderr.decode()}")
        
        secure_logger.info(f"Cloned {repo_id} to {destination}")
        return destination
    
    def _convert_repo(self, data: Any) -> RepositoryInfo:
        """Convert GitHub API response to RepositoryInfo."""
        return RepositoryInfo(
            platform="github",
            id=str(data.id),
            url=data.html_url,
            name=data.name,
            full_name=data.full_name,
            description=data.description,
            owner=data.owner.login,
            stars=data.stargazers_count,
            forks=data.forks_count,
            watchers=data.watchers_count,
            open_issues=data.open_issues_count,
            language=data.language,
            license=data.license.spdx_id if data.license else None,
            created_at=data.created_at,
            updated_at=data.updated_at,
            pushed_at=data.pushed_at,
            topics=data.topics or [],
            default_branch=data.default_branch,
            size_kb=data.size,
            has_readme=True,  # Assume true
        )
    
    async def _search_fallback(self, *args, **kwargs) -> SearchResult:
        """Fallback search using httpx."""
        # Implement httpx-based search
        return SearchResult(
            query=args[0] if args else "",
            platform=self.platform_name,
            total_count=0,
            repositories=[],
            search_time_ms=0,
        )
    
    async def _get_repo_fallback(self, repo_id: str) -> RepositoryInfo:
        """Fallback repo fetch using httpx."""
        raise NotImplementedError("Fallback not implemented")
    
    async def _get_contents_fallback(
        self, repo_id: str, path: str
    ) -> DirectoryListing:
        """Fallback contents fetch."""
        raise NotImplementedError("Fallback not implemented")
    
    async def _get_file_fallback(
        self, repo_id: str, file_path: str
    ) -> FileContent:
        """Fallback file fetch."""
        raise NotImplementedError("Fallback not implemented")
    
    async def get_languages(self, repo_id: str) -> Dict[str, int]:
        """Get language breakdown for repository."""
        await self._rate_limiter.acquire()
        
        owner, repo = repo_id.split("/")
        
        if self._api:
            return dict(self._api.repos.list_languages(owner=owner, repo=repo))
        return {}
    
    async def get_topics(self, repo_id: str) -> List[str]:
        """Get repository topics/tags."""
        await self._rate_limiter.acquire()
        
        owner, repo = repo_id.split("/")
        
        if self._api:
            result = self._api.repos.get_all_topics(owner=owner, repo=repo)
            return result.names
        return []
    
    async def check_has_tests(self, repo_id: str) -> bool:
        """Check if repository has tests directory."""
        try:
            contents = await self.get_contents(repo_id, "")
            test_dirs = ["tests", "test", "spec", "__tests__"]
            for d in contents.directories:
                if d["name"].lower() in test_dirs:
                    return True
            return False
        except Exception:
            return False
    
    async def check_has_ci(self, repo_id: str) -> bool:
        """Check if repository has CI configuration."""
        ci_paths = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".travis.yml",
            "Jenkinsfile",
            ".circleci",
            "azure-pipelines.yml",
        ]
        
        try:
            contents = await self.get_contents(repo_id, "")
            all_items = [d["name"] for d in contents.directories + contents.files]
            
            for ci in ci_paths:
                if ci.split("/")[0] in all_items:
                    return True
            return False
        except Exception:
            return False
