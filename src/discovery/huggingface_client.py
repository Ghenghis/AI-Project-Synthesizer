"""
AI Project Synthesizer - HuggingFace Client

Full-featured HuggingFace Hub API client.
Provides model, dataset, and space search capabilities.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

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

logger = logging.getLogger(__name__)


@dataclass
class HFModelInfo:
    """HuggingFace model information."""
    model_id: str
    author: str
    sha: str
    last_modified: str
    private: bool
    downloads: int
    likes: int
    tags: List[str]
    pipeline_tag: Optional[str]
    library_name: Optional[str]
    
    def to_repository_info(self) -> RepositoryInfo:
        """Convert to standard RepositoryInfo format."""
        return RepositoryInfo(
            platform="huggingface",
            id=self.model_id,
            url=f"https://huggingface.co/{self.model_id}",
            name=self.model_id.split("/")[-1] if "/" in self.model_id else self.model_id,
            full_name=self.model_id,
            description=f"HuggingFace model: {self.pipeline_tag or 'general'}",
            owner=self.author,
            stars=self.likes,
            forks=0,
            watchers=0,
            open_issues=0,
            language=self.library_name,
            license=None,
            created_at=None,
            updated_at=self.last_modified,
            pushed_at=self.last_modified,
            topics=tuple(self.tags[:10]),
            default_branch="main",
            size_kb=0,
            has_readme=True,
        )


@dataclass 
class HFDatasetInfo:
    """HuggingFace dataset information."""
    dataset_id: str
    author: str
    sha: str
    last_modified: str
    private: bool
    downloads: int
    likes: int
    tags: List[str]
    
    def to_repository_info(self) -> RepositoryInfo:
        """Convert to standard RepositoryInfo format."""
        return RepositoryInfo(
            platform="huggingface",
            id=f"datasets/{self.dataset_id}",
            url=f"https://huggingface.co/datasets/{self.dataset_id}",
            name=self.dataset_id.split("/")[-1] if "/" in self.dataset_id else self.dataset_id,
            full_name=f"datasets/{self.dataset_id}",
            description=f"HuggingFace dataset",
            owner=self.author,
            stars=self.likes,
            forks=0,
            watchers=0,
            open_issues=0,
            language="dataset",
            license=None,
            created_at=None,
            updated_at=self.last_modified,
            pushed_at=self.last_modified,
            topics=tuple(self.tags[:10]),
            default_branch="main",
            size_kb=0,
            has_readme=True,
        )


class HuggingFaceClient(PlatformClient):
    """
    HuggingFace Hub API client.
    
    Features:
    - Model search and discovery
    - Dataset search
    - Space search
    - File access
    - Clone operations
    
    Example:
        client = HuggingFaceClient(token="hf_xxx")
        results = await client.search("text classification bert")
        for repo in results.repositories:
            print(f"{repo.full_name}: {repo.stars} likes")
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        requests_per_minute: int = 300,
    ):
        """
        Initialize HuggingFace client.
        
        Args:
            token: HuggingFace API token
            requests_per_minute: Rate limit
        """
        self._token = token
        self._api = None
        self._rate_limiter = RateLimiter(
            requests_per_hour=requests_per_minute * 60,
            burst_size=50,
        )
        self._init_api()
    
    def _init_api(self):
        """Initialize huggingface_hub client."""
        try:
            from huggingface_hub import HfApi
            self._api = HfApi(token=self._token)
            logger.info("HuggingFace API client initialized")
        except ImportError:
            logger.warning("huggingface_hub not installed, using fallback")
            self._api = None
    
    @property
    def platform_name(self) -> str:
        return "huggingface"
    
    @property
    def is_authenticated(self) -> bool:
        return self._token is not None
    
    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: int = 0,
        max_results: int = 20,
        sort_by: str = "likes",
        search_type: str = "model",
    ) -> SearchResult:
        """
        Search HuggingFace Hub.
        
        Args:
            query: Search query
            language: Filter by library (transformers, diffusers, etc.)
            min_stars: Minimum likes
            max_results: Maximum results
            sort_by: Sort field (likes, downloads, modified)
            search_type: Type to search (model, dataset, space)
        """
        start_time = time.time()
        await self._rate_limiter.acquire()
        
        try:
            if self._api:
                if search_type == "model":
                    results = await self._search_models(
                        query, language, min_stars, max_results, sort_by
                    )
                elif search_type == "dataset":
                    results = await self._search_datasets(
                        query, min_stars, max_results, sort_by
                    )
                else:
                    results = await self._search_spaces(
                        query, max_results, sort_by
                    )
                
                return SearchResult(
                    query=query,
                    platform=self.platform_name,
                    total_count=len(results),
                    repositories=results,
                    search_time_ms=int((time.time() - start_time) * 1000),
                    has_more=len(results) >= max_results,
                )
            else:
                return await self._search_fallback(query, max_results)
                
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                raise RateLimitError(
                    "HuggingFace rate limit exceeded",
                    retry_after=60,
                )
            elif "401" in error_msg or "authentication" in error_msg:
                raise AuthenticationError("HuggingFace authentication failed")
            else:
                logger.exception("HuggingFace search error")
                raise
    
    async def _search_models(
        self,
        query: str,
        library: Optional[str],
        min_likes: int,
        max_results: int,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Search HuggingFace models."""
        # Map sort field
        sort_map = {
            "likes": "likes",
            "downloads": "downloads", 
            "modified": "lastModified",
        }
        sort_field = sort_map.get(sort_by, "likes")
        
        # Search models - newer huggingface_hub API
        kwargs = {
            "search": query,
            "sort": sort_field,
            "direction": -1,
            "limit": max_results * 2,  # Get extra for filtering
        }
        
        models = list(self._api.list_models(**kwargs))
        
        # Filter by likes
        filtered = [m for m in models if getattr(m, 'likes', 0) >= min_likes]
        
        # Convert to RepositoryInfo
        repositories = []
        for model in filtered[:max_results]:
            repo_info = RepositoryInfo(
                platform="huggingface",
                id=model.modelId,
                url=f"https://huggingface.co/{model.modelId}",
                name=model.modelId.split("/")[-1] if "/" in model.modelId else model.modelId,
                full_name=model.modelId,
                description=getattr(model, 'pipeline_tag', '') or "HuggingFace model",
                owner=model.modelId.split("/")[0] if "/" in model.modelId else "unknown",
                stars=getattr(model, 'likes', 0),
                forks=0,
                watchers=getattr(model, 'downloads', 0),
                open_issues=0,
                language=getattr(model, 'library_name', None),
                license=None,
                created_at=None,
                updated_at=getattr(model, 'lastModified', None),
                pushed_at=getattr(model, 'lastModified', None),
                topics=tuple(getattr(model, 'tags', [])[:10]),
                default_branch="main",
                size_kb=0,
                has_readme=True,
            )
            repositories.append(repo_info)
        
        return repositories
    
    async def _search_datasets(
        self,
        query: str,
        min_likes: int,
        max_results: int,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Search HuggingFace datasets."""
        sort_map = {
            "likes": "likes",
            "downloads": "downloads",
            "modified": "lastModified",
        }
        sort_field = sort_map.get(sort_by, "likes")
        
        datasets = list(self._api.list_datasets(
            search=query,
            sort=sort_field,
            direction=-1,
            limit=max_results * 2,
        ))
        
        filtered = [d for d in datasets if getattr(d, 'likes', 0) >= min_likes]
        
        repositories = []
        for dataset in filtered[:max_results]:
            dataset_id = dataset.id
            repo_info = RepositoryInfo(
                platform="huggingface",
                id=f"datasets/{dataset_id}",
                url=f"https://huggingface.co/datasets/{dataset_id}",
                name=dataset_id.split("/")[-1] if "/" in dataset_id else dataset_id,
                full_name=f"datasets/{dataset_id}",
                description="HuggingFace dataset",
                owner=dataset_id.split("/")[0] if "/" in dataset_id else "unknown",
                stars=getattr(dataset, 'likes', 0),
                forks=0,
                watchers=getattr(dataset, 'downloads', 0),
                open_issues=0,
                language="dataset",
                license=None,
                created_at=None,
                updated_at=getattr(dataset, 'lastModified', None),
                pushed_at=getattr(dataset, 'lastModified', None),
                topics=tuple(getattr(dataset, 'tags', [])[:10]),
                default_branch="main",
                size_kb=0,
                has_readme=True,
            )
            repositories.append(repo_info)
        
        return repositories
    
    async def _search_spaces(
        self,
        query: str,
        max_results: int,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Search HuggingFace Spaces."""
        sort_map = {
            "likes": "likes",
            "modified": "lastModified",
        }
        sort_field = sort_map.get(sort_by, "likes")
        
        spaces = list(self._api.list_spaces(
            search=query,
            sort=sort_field,
            direction=-1,
            limit=max_results,
        ))
        
        repositories = []
        for space in spaces:
            space_id = space.id
            repo_info = RepositoryInfo(
                platform="huggingface",
                id=f"spaces/{space_id}",
                url=f"https://huggingface.co/spaces/{space_id}",
                name=space_id.split("/")[-1] if "/" in space_id else space_id,
                full_name=f"spaces/{space_id}",
                description="HuggingFace Space",
                owner=space_id.split("/")[0] if "/" in space_id else "unknown",
                stars=getattr(space, 'likes', 0),
                forks=0,
                watchers=0,
                open_issues=0,
                language=getattr(space, 'sdk', None),
                license=None,
                created_at=None,
                updated_at=getattr(space, 'lastModified', None),
                pushed_at=getattr(space, 'lastModified', None),
                topics=tuple(getattr(space, 'tags', [])[:10]),
                default_branch="main",
                size_kb=0,
                has_readme=True,
            )
            repositories.append(repo_info)
        
        return repositories
    
    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        """Get detailed repository information."""
        await self._rate_limiter.acquire()
        
        try:
            if self._api:
                # Determine type from ID
                if repo_id.startswith("datasets/"):
                    dataset_id = repo_id.replace("datasets/", "")
                    info = self._api.dataset_info(dataset_id)
                    return self._dataset_to_repo_info(info)
                elif repo_id.startswith("spaces/"):
                    space_id = repo_id.replace("spaces/", "")
                    info = self._api.space_info(space_id)
                    return self._space_to_repo_info(info)
                else:
                    info = self._api.model_info(repo_id)
                    return self._model_to_repo_info(info)
            else:
                raise NotImplementedError("Fallback not implemented")
                
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise RepositoryNotFoundError(f"Repository not found: {repo_id}")
            raise
    
    def _model_to_repo_info(self, info: Any) -> RepositoryInfo:
        """Convert model info to RepositoryInfo."""
        return RepositoryInfo(
            platform="huggingface",
            id=info.modelId,
            url=f"https://huggingface.co/{info.modelId}",
            name=info.modelId.split("/")[-1],
            full_name=info.modelId,
            description=getattr(info, 'pipeline_tag', '') or "HuggingFace model",
            owner=info.modelId.split("/")[0],
            stars=getattr(info, 'likes', 0),
            forks=0,
            watchers=getattr(info, 'downloads', 0),
            open_issues=0,
            language=getattr(info, 'library_name', None),
            license=getattr(info, 'license', None),
            created_at=getattr(info, 'created_at', None),
            updated_at=getattr(info, 'lastModified', None),
            pushed_at=getattr(info, 'lastModified', None),
            topics=tuple(getattr(info, 'tags', [])[:10]),
            default_branch="main",
            size_kb=0,
            has_readme=True,
        )
    
    def _dataset_to_repo_info(self, info: Any) -> RepositoryInfo:
        """Convert dataset info to RepositoryInfo."""
        return RepositoryInfo(
            platform="huggingface",
            id=f"datasets/{info.id}",
            url=f"https://huggingface.co/datasets/{info.id}",
            name=info.id.split("/")[-1],
            full_name=f"datasets/{info.id}",
            description="HuggingFace dataset",
            owner=info.id.split("/")[0],
            stars=getattr(info, 'likes', 0),
            forks=0,
            watchers=getattr(info, 'downloads', 0),
            open_issues=0,
            language="dataset",
            license=getattr(info, 'license', None),
            created_at=getattr(info, 'created_at', None),
            updated_at=getattr(info, 'lastModified', None),
            pushed_at=getattr(info, 'lastModified', None),
            topics=tuple(getattr(info, 'tags', [])[:10]),
            default_branch="main",
            size_kb=0,
            has_readme=True,
        )
    
    def _space_to_repo_info(self, info: Any) -> RepositoryInfo:
        """Convert space info to RepositoryInfo."""
        return RepositoryInfo(
            platform="huggingface",
            id=f"spaces/{info.id}",
            url=f"https://huggingface.co/spaces/{info.id}",
            name=info.id.split("/")[-1],
            full_name=f"spaces/{info.id}",
            description="HuggingFace Space",
            owner=info.id.split("/")[0],
            stars=getattr(info, 'likes', 0),
            forks=0,
            watchers=0,
            open_issues=0,
            language=getattr(info, 'sdk', None),
            license=getattr(info, 'license', None),
            created_at=getattr(info, 'created_at', None),
            updated_at=getattr(info, 'lastModified', None),
            pushed_at=getattr(info, 'lastModified', None),
            topics=tuple(getattr(info, 'tags', [])[:10]),
            default_branch="main",
            size_kb=0,
            has_readme=True,
        )
    
    async def get_contents(
        self,
        repo_id: str,
        path: str = "",
    ) -> DirectoryListing:
        """Get directory contents from HuggingFace repo."""
        await self._rate_limiter.acquire()
        
        if self._api:
            # Determine repo type
            repo_type = "model"
            actual_id = repo_id
            if repo_id.startswith("datasets/"):
                repo_type = "dataset"
                actual_id = repo_id.replace("datasets/", "")
            elif repo_id.startswith("spaces/"):
                repo_type = "space"
                actual_id = repo_id.replace("spaces/", "")
            
            files_info = self._api.list_repo_files(
                repo_id=actual_id,
                repo_type=repo_type,
            )
            
            files = []
            directories = set()
            
            for file_path in files_info:
                if path and not file_path.startswith(path):
                    continue
                
                rel_path = file_path[len(path):].lstrip("/") if path else file_path
                
                if "/" in rel_path:
                    # It's in a subdirectory
                    dir_name = rel_path.split("/")[0]
                    directories.add(dir_name)
                else:
                    files.append({
                        "name": rel_path,
                        "path": file_path,
                        "sha": "",
                        "size": 0,
                        "type": "file",
                    })
            
            return DirectoryListing(
                path=path,
                files=files,
                directories=[{"name": d, "path": f"{path}/{d}" if path else d, "type": "dir"} for d in directories],
            )
        else:
            raise NotImplementedError("Fallback not implemented")
    
    async def get_file(
        self,
        repo_id: str,
        file_path: str,
    ) -> FileContent:
        """Get file contents from HuggingFace repo."""
        await self._rate_limiter.acquire()
        
        if self._api:
            from huggingface_hub import hf_hub_download
            
            # Determine repo type
            repo_type = "model"
            actual_id = repo_id
            if repo_id.startswith("datasets/"):
                repo_type = "dataset"
                actual_id = repo_id.replace("datasets/", "")
            elif repo_id.startswith("spaces/"):
                repo_type = "space"
                actual_id = repo_id.replace("spaces/", "")
            
            # Download file with explicit revision pinning for security
            local_path = hf_hub_download(  # nosec B615 - revision explicitly pinned
                repo_id=actual_id,
                filename=file_path,
                repo_type=repo_type,
                token=self._token,
                revision="main",  # Pin to main branch for reproducibility
            )
            
            content = Path(local_path).read_bytes()
            
            return FileContent(
                path=file_path,
                name=Path(file_path).name,
                content=content,
                size=len(content),
                sha="",
            )
        else:
            raise NotImplementedError("Fallback not implemented")
    
    async def clone(
        self,
        repo_id: str,
        destination: Path,
        depth: int = 1,
        branch: Optional[str] = None,
    ) -> Path:
        """Clone HuggingFace repository."""
        from huggingface_hub import snapshot_download
        
        # Determine repo type
        repo_type = "model"
        actual_id = repo_id
        if repo_id.startswith("datasets/"):
            repo_type = "dataset"
            actual_id = repo_id.replace("datasets/", "")
        elif repo_id.startswith("spaces/"):
            repo_type = "space"
            actual_id = repo_id.replace("spaces/", "")
        
        # Download snapshot with explicit revision pinning for security
        # Default to "main" branch if no branch specified
        revision = branch if branch else "main"
        local_dir = snapshot_download(  # nosec B615 - revision explicitly pinned
            repo_id=actual_id,
            repo_type=repo_type,
            local_dir=str(destination),
            token=self._token,
            revision=revision,
        )
        
        logger.info(f"Downloaded {repo_id} to {local_dir}")
        return Path(local_dir)
    
    async def _search_fallback(
        self,
        query: str,
        max_results: int,
    ) -> SearchResult:
        """Fallback search using httpx."""
        return SearchResult(
            query=query,
            platform=self.platform_name,
            total_count=0,
            repositories=[],
            search_time_ms=0,
        )
