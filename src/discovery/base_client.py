"""
AI Project Synthesizer - Platform Client Base

Abstract base class and data models for all platform API clients.
Each platform (GitHub, HuggingFace, etc.) implements this interface.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Supported platforms for repository discovery."""
    GITHUB = "github"
    GITLAB = "gitlab"
    HUGGINGFACE = "huggingface"
    KAGGLE = "kaggle"
    ARXIV = "arxiv"
    PAPERS_WITH_CODE = "papers_with_code"
    SEMANTIC_SCHOLAR = "semantic_scholar"


class DiscoveryError(Exception):
    """Base exception for discovery errors."""
    pass


class AuthenticationError(DiscoveryError):
    """Authentication failed."""
    pass


class RateLimitError(DiscoveryError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class RepositoryNotFoundError(DiscoveryError):
    """Repository not found."""
    pass


@dataclass
class RepositoryInfo:
    """
    Standard repository information across all platforms.
    
    This is the unified data model that all platform clients
    convert their responses to.
    """
    # Identity
    platform: str
    id: str
    url: str
    name: str
    full_name: str
    
    # Metadata
    description: Optional[str] = None
    owner: str = ""
    
    # Metrics
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    
    # Languages
    language: Optional[str] = None
    languages: Dict[str, int] = field(default_factory=dict)
    
    # License
    license: Optional[str] = None
    license_url: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    
    # Topics/Tags
    topics: List[str] = field(default_factory=list)
    
    # Repository info
    default_branch: str = "main"
    size_kb: int = 0
    
    # Quality indicators
    has_readme: bool = False
    has_tests: bool = False
    has_ci: bool = False
    has_docs: bool = False
    
    # Computed scores (set by ranker)
    relevance_score: float = 0.0
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "platform": self.platform,
            "id": self.id,
            "url": self.url,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "owner": self.owner,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "license": self.license,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "topics": self.topics,
            "relevance_score": self.relevance_score,
            "quality_score": self.quality_score,
        }


@dataclass
class SearchResult:
    """Result of a search operation."""
    query: str
    platform: str
    total_count: int
    repositories: List[RepositoryInfo]
    search_time_ms: int
    has_more: bool = False
    next_page_token: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "platform": self.platform,
            "total_count": self.total_count,
            "repositories": [r.to_dict() for r in self.repositories],
            "search_time_ms": self.search_time_ms,
            "has_more": self.has_more,
        }


@dataclass
class FileContent:
    """Content of a file from a repository."""
    path: str
    name: str
    content: bytes
    size: int
    encoding: str = "utf-8"
    sha: Optional[str] = None
    
    @property
    def text(self) -> str:
        """Get content as text."""
        return self.content.decode(self.encoding)


@dataclass
class DirectoryListing:
    """Listing of files in a repository directory."""
    path: str
    files: List[Dict[str, Any]]
    directories: List[Dict[str, Any]]


class PlatformClient(ABC):
    """
    Abstract base class for platform API clients.
    
    All platform clients (GitHub, HuggingFace, etc.) must implement
    this interface to ensure consistent behavior across the discovery layer.
    
    Example implementation:
        class GitHubClient(PlatformClient):
            @property
            def platform_name(self) -> str:
                return "github"
            
            async def search(self, query: str, ...) -> SearchResult:
                # Implementation
                pass
    """
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """
        Return the platform identifier.
        
        Returns:
            Platform name (e.g., "github", "huggingface")
        """
        pass
    
    @property
    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return False
    
    @abstractmethod
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
        Search for repositories matching the query.
        
        Args:
            query: Search query string
            language: Filter by programming language
            min_stars: Minimum star count
            max_results: Maximum number of results
            sort_by: Sort field (stars, updated, relevance)
            order: Sort order (asc, desc)
            
        Returns:
            SearchResult with matching repositories
            
        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
        """
        pass
    
    @abstractmethod
    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        """
        Get detailed information about a specific repository.
        
        Args:
            repo_id: Repository identifier (e.g., "owner/repo")
            
        Returns:
            RepositoryInfo with full details
            
        Raises:
            RepositoryNotFoundError: If repository doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_contents(
        self,
        repo_id: str,
        path: str = "",
    ) -> DirectoryListing:
        """
        Get contents of a directory in the repository.
        
        Args:
            repo_id: Repository identifier
            path: Path within repository (empty for root)
            
        Returns:
            DirectoryListing with files and subdirectories
        """
        pass
    
    @abstractmethod
    async def get_file(
        self,
        repo_id: str,
        file_path: str,
    ) -> FileContent:
        """
        Get contents of a specific file.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to file within repository
            
        Returns:
            FileContent with file data
        """
        pass
    
    @abstractmethod
    async def clone(
        self,
        repo_id: str,
        destination: Path,
        depth: int = 1,
        branch: Optional[str] = None,
    ) -> Path:
        """
        Clone repository to local filesystem.
        
        Args:
            repo_id: Repository identifier
            destination: Local path for clone
            depth: Git clone depth (1 for shallow)
            branch: Specific branch to clone
            
        Returns:
            Path to cloned repository
        """
        pass
    
    async def get_readme(self, repo_id: str) -> Optional[str]:
        """
        Get repository README content.
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            README content as string, or None if not found
        """
        readme_names = ["README.md", "README.rst", "README.txt", "README"]
        
        for name in readme_names:
            try:
                content = await self.get_file(repo_id, name)
                return content.text
            except Exception as e:
                logger.debug("README %s not found: %s", name, e)
                continue
        
        return None
    
    async def get_license(self, repo_id: str) -> Optional[str]:
        """
        Get repository license content.
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            License content as string, or None if not found
        """
        license_names = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
        
        for name in license_names:
            try:
                content = await self.get_file(repo_id, name)
                return content.text
            except Exception as e:
                logger.debug("License %s not found: %s", name, e)
                continue
        
        return None
    
    async def check_health(self) -> bool:
        """
        Check if the platform API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            await self.search("test", max_results=1)
            return True
        except Exception:
            return False
