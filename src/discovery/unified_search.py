"""
AI Project Synthesizer - Unified Search

Cross-platform repository search with intelligent ranking.
Aggregates results from GitHub, HuggingFace, Kaggle, and more.
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
import hashlib
import json

from src.discovery.base_client import (
    PlatformClient,
    RepositoryInfo,
    SearchResult,
)
from src.discovery.github_client import GitHubClient
from src.discovery.huggingface_client import HuggingFaceClient
from src.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSearchResult:
    """Result from unified multi-platform search."""
    
    query: str
    platforms_searched: List[str]
    total_count: int
    repositories: List[RepositoryInfo]
    search_time_ms: int
    platform_counts: Dict[str, int] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "platforms_searched": self.platforms_searched,
            "total_count": self.total_count,
            "repositories": [
                {
                    "platform": r.platform,
                    "id": r.id,
                    "url": r.url,
                    "name": r.name,
                    "full_name": r.full_name,
                    "description": r.description,
                    "owner": r.owner,
                    "stars": r.stars,
                    "language": r.language,
                    "topics": list(r.topics) if r.topics else [],
                }
                for r in self.repositories
            ],
            "search_time_ms": self.search_time_ms,
            "platform_counts": self.platform_counts,
            "errors": self.errors,
        }


class UnifiedSearch:
    """
    Unified search across multiple code hosting platforms.
    
    Features:
    - Parallel search across platforms
    - Result deduplication
    - Intelligent ranking
    - Caching
    - Error handling per platform
    
    Example:
        search = UnifiedSearch()
        results = await search.search(
            "machine learning pytorch",
            platforms=["github", "huggingface"],
            max_results=20,
        )
    """
    
    SUPPORTED_PLATFORMS = ["github", "huggingface", "kaggle", "arxiv"]
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        huggingface_token: Optional[str] = None,
        kaggle_credentials: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize unified search with platform credentials.
        
        Args:
            github_token: GitHub personal access token
            huggingface_token: HuggingFace API token
            kaggle_credentials: Kaggle API credentials dict
        """
        self._clients: Dict[str, PlatformClient] = {}
        self._cache: Dict[str, UnifiedSearchResult] = {}
        self._cache_ttl = 3600  # 1 hour
        
        # Initialize available clients
        self._init_clients(github_token, huggingface_token, kaggle_credentials)
    
    def _init_clients(
        self,
        github_token: Optional[str],
        huggingface_token: Optional[str],
        kaggle_credentials: Optional[Dict[str, str]],
    ):
        """Initialize platform clients."""
        settings = get_settings()
        
        # GitHub client
        if settings.platforms.github_token.get_secret_value():
            token = github_token or settings.platforms.github_token.get_secret_value()
            try:
                self._clients["github"] = GitHubClient(token=token)
                logger.info("GitHub client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub client: {e}")
        
        # HuggingFace client
        if settings.platforms.huggingface_token.get_secret_value():
            token = huggingface_token or settings.platforms.huggingface_token.get_secret_value()
            try:
                self._clients["huggingface"] = HuggingFaceClient(token=token)
                logger.info("HuggingFace client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize HuggingFace client: {e}")
        
        # Kaggle client
        if settings.platforms.kaggle_username and settings.platforms.kaggle_key.get_secret_value():
            try:
                from src.discovery.kaggle_client import KaggleClient
                kaggle_creds = kaggle_credentials or {
                    "username": settings.platforms.kaggle_username,
                    "key": settings.platforms.kaggle_key.get_secret_value(),
                }
                self._clients["kaggle"] = KaggleClient(
                    username=kaggle_creds.get("username"),
                    key=kaggle_creds.get("key"),
                )
                logger.info("Kaggle client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Kaggle client: {e}")
    
    @property
    def available_platforms(self) -> List[str]:
        """Get list of available (initialized) platforms."""
        return list(self._clients.keys())
    
    async def search(
        self,
        query: str,
        platforms: Optional[List[str]] = None,
        max_results: int = 20,
        language_filter: Optional[str] = None,
        min_stars: int = 0,
        sort_by: str = "relevance",
        use_cache: bool = True,
    ) -> UnifiedSearchResult:
        """
        Search across multiple platforms.
        
        Args:
            query: Natural language search query
            platforms: Platforms to search (defaults to all available)
            max_results: Maximum results per platform
            language_filter: Filter by programming language
            min_stars: Minimum star/like count
            sort_by: Sort method (relevance, stars, updated)
            use_cache: Whether to use cached results
        
        Returns:
            UnifiedSearchResult with aggregated results
        """
        start_time = time.time()
        
        # Default to all available platforms
        if platforms is None:
            platforms = self.available_platforms
        else:
            # Filter to only available platforms
            platforms = [p for p in platforms if p in self._clients]
        
        if not platforms:
            logger.warning("No platforms available for search")
            return UnifiedSearchResult(
                query=query,
                platforms_searched=[],
                total_count=0,
                repositories=[],
                search_time_ms=0,
                errors={"general": "No platforms available"},
            )
        
        # Check cache
        cache_key = self._cache_key(query, platforms, language_filter, min_stars)
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            logger.debug(f"Cache hit for query: {query}")
            return cached
        
        # Search all platforms in parallel
        tasks = {}
        for platform in platforms:
            client = self._clients[platform]
            tasks[platform] = asyncio.create_task(
                self._search_platform(
                    client,
                    query,
                    language_filter,
                    min_stars,
                    max_results,
                )
            )
        
        # Gather results
        all_repos: List[RepositoryInfo] = []
        platform_counts: Dict[str, int] = {}
        errors: Dict[str, str] = {}
        
        for platform, task in tasks.items():
            try:
                result = await task
                all_repos.extend(result.repositories)
                platform_counts[platform] = len(result.repositories)
                logger.info(f"Found {len(result.repositories)} results from {platform}")
            except Exception as e:
                logger.warning(f"Search failed for {platform}: {e}")
                errors[platform] = str(e)
                platform_counts[platform] = 0
        
        # Deduplicate and rank
        unique_repos = self._deduplicate(all_repos)
        ranked_repos = self._rank_results(unique_repos, query, sort_by)
        
        # Limit total results
        final_repos = ranked_repos[:max_results * len(platforms)]
        
        result = UnifiedSearchResult(
            query=query,
            platforms_searched=platforms,
            total_count=len(final_repos),
            repositories=final_repos,
            search_time_ms=int((time.time() - start_time) * 1000),
            platform_counts=platform_counts,
            errors=errors,
        )
        
        # Cache result
        if use_cache:
            self._cache[cache_key] = result
        
        return result
    
    async def _search_platform(
        self,
        client: PlatformClient,
        query: str,
        language: Optional[str],
        min_stars: int,
        max_results: int,
    ) -> SearchResult:
        """Search a single platform."""
        try:
            return await client.search(
                query=query,
                language=language,
                min_stars=min_stars,
                max_results=max_results,
            )
        except Exception as e:
            logger.exception(f"Platform search error: {client.platform_name}")
            raise
    
    def _deduplicate(
        self,
        repositories: List[RepositoryInfo],
    ) -> List[RepositoryInfo]:
        """Remove duplicate repositories across platforms."""
        seen_urls: Set[str] = set()
        unique: List[RepositoryInfo] = []
        
        for repo in repositories:
            # Normalize URL for comparison
            url_key = repo.url.lower().rstrip("/")
            
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                unique.append(repo)
        
        return unique
    
    def _rank_results(
        self,
        repositories: List[RepositoryInfo],
        query: str,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Rank results using composite scoring."""
        if sort_by == "stars":
            return sorted(repositories, key=lambda r: r.stars, reverse=True)
        elif sort_by == "updated":
            return sorted(
                repositories,
                key=lambda r: r.updated_at or "",
                reverse=True,
            )
        else:
            # Relevance-based ranking
            scored = []
            for repo in repositories:
                score = self._calculate_score(repo, query)
                scored.append((score, repo))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [repo for _, repo in scored]
    
    def _calculate_score(
        self,
        repo: RepositoryInfo,
        query: str,
    ) -> float:
        """Calculate relevance score for a repository."""
        score = 0.0
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        # Name match (0.3)
        name_lower = repo.name.lower()
        if query_lower in name_lower:
            score += 0.3
        else:
            name_terms = set(name_lower.replace("-", " ").replace("_", " ").split())
            term_overlap = len(query_terms & name_terms) / len(query_terms) if query_terms else 0
            score += 0.3 * term_overlap
        
        # Description match (0.2)
        if repo.description:
            desc_lower = repo.description.lower()
            if query_lower in desc_lower:
                score += 0.2
            else:
                desc_terms = set(desc_lower.split())
                term_overlap = len(query_terms & desc_terms) / len(query_terms) if query_terms else 0
                score += 0.2 * term_overlap
        
        # Topics match (0.15)
        if repo.topics:
            topics_lower = {t.lower() for t in repo.topics}
            topic_overlap = len(query_terms & topics_lower)
            score += 0.15 * min(1.0, topic_overlap / 2)
        
        # Popularity (0.2) - log scaled
        import math
        if repo.stars > 0:
            star_score = min(1.0, math.log10(repo.stars + 1) / 5)
            score += 0.2 * star_score
        
        # Recency (0.15)
        if repo.updated_at:
            from datetime import datetime, timezone
            try:
                if isinstance(repo.updated_at, str):
                    updated = datetime.fromisoformat(repo.updated_at.replace("Z", "+00:00"))
                else:
                    updated = repo.updated_at
                
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                days_ago = (now - updated).days
                recency_score = math.exp(-days_ago / 180)  # 6-month half-life
                score += 0.15 * recency_score
            except Exception as e:
                logger.debug("Failed to calculate recency score: %s", e)
        
        return score
    
    def _cache_key(
        self,
        query: str,
        platforms: List[str],
        language: Optional[str],
        min_stars: int,
    ) -> str:
        """Generate cache key for search parameters."""
        key_data = {
            "query": query.lower().strip(),
            "platforms": sorted(platforms),
            "language": language,
            "min_stars": min_stars,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the search cache."""
        self._cache.clear()
        logger.info("Search cache cleared")
    
    async def get_repository(
        self,
        repo_url: str,
    ) -> Optional[RepositoryInfo]:
        """
        Get repository info from URL.
        
        Automatically detects platform and routes to appropriate client.
        """
        # Detect platform from URL
        platform = self._detect_platform(repo_url)
        
        if platform not in self._clients:
            logger.warning(f"Platform not available: {platform}")
            return None
        
        client = self._clients[platform]
        
        # Extract repo ID from URL
        repo_id = self._extract_repo_id(repo_url, platform)
        
        try:
            return await client.get_repository(repo_id)
        except Exception as e:
            logger.warning(f"Failed to get repository: {e}")
            return None
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()
        
        if "github.com" in url_lower:
            return "github"
        elif "huggingface.co" in url_lower:
            return "huggingface"
        elif "gitlab.com" in url_lower:
            return "gitlab"
        elif "kaggle.com" in url_lower:
            return "kaggle"
        elif "bitbucket.org" in url_lower:
            return "bitbucket"
        else:
            return "unknown"
    
    def _extract_repo_id(self, url: str, platform: str) -> str:
        """Extract repository ID from URL."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        if platform == "github":
            # github.com/owner/repo
            parts = path.split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        elif platform == "huggingface":
            # huggingface.co/owner/model
            # huggingface.co/datasets/owner/dataset
            # huggingface.co/spaces/owner/space
            if path.startswith("datasets/"):
                return path
            elif path.startswith("spaces/"):
                return path
            else:
                parts = path.split("/")
                if len(parts) >= 2:
                    return f"{parts[0]}/{parts[1]}"
        
        return path


# Factory function
def create_unified_search() -> UnifiedSearch:
    """Create UnifiedSearch instance with settings from config."""
    settings = get_settings()
    
    return UnifiedSearch(
        github_token=settings.platforms.github_token.get_secret_value(),
        huggingface_token=settings.platforms.huggingface_token.get_secret_value(),
    )
