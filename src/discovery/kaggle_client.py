"""
AI Project Synthesizer - Kaggle Client

Full-featured Kaggle API client for discovering datasets, competitions,
notebooks, and models. Provides comprehensive search and analysis capabilities.
"""

import asyncio
import os
import time
import tempfile
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

from src.discovery.base_client import (
    PlatformClient,
    RepositoryInfo,
    SearchResult,
    FileContent,
    DirectoryListing,
    AuthenticationError,
    RepositoryNotFoundError,
)
from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class KaggleResourceType(str, Enum):
    """Types of Kaggle resources."""
    DATASET = "dataset"
    COMPETITION = "competition"
    NOTEBOOK = "notebook"
    MODEL = "model"


@dataclass
class KaggleDataset:
    """Kaggle dataset information."""
    ref: str  # owner/dataset-slug
    title: str
    subtitle: Optional[str]
    creator_name: str
    total_bytes: int
    url: str
    last_updated: Optional[str]
    download_count: int
    vote_count: int
    usability_rating: float
    tags: List[str] = field(default_factory=list)
    file_types: List[str] = field(default_factory=list)
    license_name: Optional[str] = None


@dataclass
class KaggleCompetition:
    """Kaggle competition information."""
    ref: str
    title: str
    description: Optional[str]
    url: str
    deadline: Optional[str]
    category: str
    reward: Optional[str]
    team_count: int
    user_has_entered: bool
    tags: List[str] = field(default_factory=list)
    evaluation_metric: Optional[str] = None


@dataclass
class KaggleNotebook:
    """Kaggle notebook/kernel information."""
    ref: str  # owner/notebook-slug
    title: str
    author: str
    url: str
    last_run_time: Optional[str]
    total_votes: int
    language: str
    kernel_type: str
    is_private: bool
    dataset_sources: List[str] = field(default_factory=list)
    competition_sources: List[str] = field(default_factory=list)


@dataclass
class KaggleModel:
    """Kaggle model information."""
    ref: str  # owner/model-slug
    title: str
    subtitle: Optional[str]
    author: str
    url: str
    model_framework: str
    overview: Optional[str]
    instance_count: int
    download_count: int
    tags: List[str] = field(default_factory=list)


class KaggleClient(PlatformClient):
    """
    Kaggle API client for discovering datasets, competitions, notebooks, and models.
    
    Features:
    - Search datasets by query, tags, file types
    - Search competitions (active, completed, all)
    - Search notebooks/kernels
    - Search models
    - Download datasets and notebooks
    - Get detailed metadata
    - Trending and popular content discovery
    
    Example:
        client = KaggleClient(username="user", key="xxx")
        
        # Search datasets
        results = await client.search("machine learning", resource_type="dataset")
        
        # Search competitions
        comps = await client.search_competitions(category="featured")
        
        # Get trending notebooks
        notebooks = await client.get_trending_notebooks(language="python")
    """

    def __init__(
        self,
        username: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """
        Initialize Kaggle client.
        
        Args:
            username: Kaggle username
            key: Kaggle API key
        """
        settings = get_settings()
        self._username = username or settings.platforms.kaggle_username
        self._key = key or settings.platforms.kaggle_key.get_secret_value()

        self._api = None
        self._init_api()

    def _init_api(self):
        """Initialize Kaggle API client."""
        if not self._username or not self._key:
            secure_logger.warning("Kaggle credentials not provided")
            return

        # Set environment variables for kaggle library
        os.environ['KAGGLE_USERNAME'] = self._username
        os.environ['KAGGLE_KEY'] = self._key

        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            self._api = KaggleApi()
            self._api.authenticate()
            secure_logger.info("Kaggle API client initialized and authenticated")
        except ImportError:
            secure_logger.warning("kaggle package not installed")
            self._api = None
        except Exception as e:
            secure_logger.error(f"Failed to initialize Kaggle API: {e}")
            self._api = None

    @property
    def platform_name(self) -> str:
        return "kaggle"

    @property
    def is_authenticated(self) -> bool:
        return self._api is not None

    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: int = 0,
        max_results: int = 20,
        sort_by: str = "votes",
        order: str = "desc",
        resource_type: str = "dataset",
    ) -> SearchResult:
        """
        Search Kaggle for datasets, competitions, notebooks, or models.
        
        Args:
            query: Search query
            language: Filter by language (for notebooks)
            min_stars: Minimum vote count
            max_results: Maximum results
            sort_by: Sort field (votes, updated, hotness, relevance)
            order: Sort order
            resource_type: Type of resource (dataset, competition, notebook, model)
        
        Returns:
            SearchResult with matching resources
        """
        start_time = time.time()

        if not self._api:
            secure_logger.warning("Kaggle API not initialized")
            return SearchResult(
                query=query,
                platform=self.platform_name,
                total_count=0,
                repositories=[],
                search_time_ms=0,
            )

        try:
            if resource_type == "dataset":
                results = await self._search_datasets(query, min_stars, max_results, sort_by)
            elif resource_type == "competition":
                results = await self._search_competitions(query, max_results, sort_by)
            elif resource_type == "notebook":
                results = await self._search_notebooks(query, language, max_results, sort_by)
            elif resource_type == "model":
                results = await self._search_models(query, max_results, sort_by)
            else:
                # Default to datasets
                results = await self._search_datasets(query, min_stars, max_results, sort_by)

            search_time_ms = int((time.time() - start_time) * 1000)

            secure_logger.info(
                "Kaggle search completed",
                query=query[:50],
                resource_type=resource_type,
                result_count=len(results)
            )

            return SearchResult(
                query=query,
                platform=self.platform_name,
                total_count=len(results),
                repositories=results,
                search_time_ms=search_time_ms,
                has_more=len(results) >= max_results,
            )

        except Exception as e:
            secure_logger.error(f"Kaggle search error: {e}")
            return SearchResult(
                query=query,
                platform=self.platform_name,
                total_count=0,
                repositories=[],
                search_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _search_datasets(
        self,
        query: str,
        min_votes: int,
        max_results: int,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Search Kaggle datasets."""
        # Map sort field
        sort_map = {
            "votes": "votes",
            "stars": "votes",
            "updated": "updated",
            "hotness": "hotness",
            "relevance": "relevance",
        }
        kaggle_sort = sort_map.get(sort_by, "votes")

        # Run in executor since kaggle API is synchronous
        loop = asyncio.get_event_loop()
        datasets = await loop.run_in_executor(
            None,
            lambda: list(self._api.dataset_list(
                search=query,
                sort_by=kaggle_sort,
            ))[:max_results]
        )

        # Convert to RepositoryInfo
        repositories = []
        for ds in datasets:
            if hasattr(ds, 'voteCount') and ds.voteCount < min_votes:
                continue

            # Convert tags to strings (Kaggle returns Tag objects)
            tags = getattr(ds, 'tags', []) or []
            tag_strings = [str(t.name) if hasattr(t, 'name') else str(t) for t in tags]

            repo_info = RepositoryInfo(
                platform="kaggle",
                id=ds.ref,
                url=f"https://www.kaggle.com/datasets/{ds.ref}",
                name=ds.ref.split("/")[-1] if "/" in ds.ref else ds.ref,
                full_name=ds.ref,
                description=getattr(ds, 'subtitle', None) or getattr(ds, 'title', ''),
                owner=ds.ref.split("/")[0] if "/" in ds.ref else "unknown",
                stars=getattr(ds, 'voteCount', 0),
                forks=0,
                watchers=getattr(ds, 'downloadCount', 0),
                open_issues=0,
                language=None,
                license=getattr(ds, 'licenseName', None),
                created_at=None,
                updated_at=str(getattr(ds, 'lastUpdated', None)),
                topics=tag_strings,
                size_kb=getattr(ds, 'totalBytes', 0) // 1024,
            )
            repositories.append(repo_info)

        return repositories[:max_results]

    async def _search_competitions(
        self,
        query: str,
        max_results: int,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Search Kaggle competitions."""
        loop = asyncio.get_event_loop()

        # Get competitions - filter by search query manually since API doesn't support search
        competitions = await loop.run_in_executor(
            None,
            lambda: list(self._api.competitions_list(
                sort_by="latestDeadline",
                page=1,
                page_size=100,  # Get more to filter
            ))
        )

        # Filter by query
        query_lower = query.lower()
        filtered = [
            c for c in competitions
            if query_lower in getattr(c, 'title', '').lower()
            or query_lower in getattr(c, 'description', '').lower()
            or query_lower in str(getattr(c, 'tags', [])).lower()
        ]

        # Convert to RepositoryInfo
        repositories = []
        for comp in filtered[:max_results]:
            repo_info = RepositoryInfo(
                platform="kaggle",
                id=comp.ref,
                url=f"https://www.kaggle.com/competitions/{comp.ref}",
                name=comp.ref,
                full_name=f"competition/{comp.ref}",
                description=getattr(comp, 'description', None) or getattr(comp, 'title', ''),
                owner="kaggle",
                stars=getattr(comp, 'teamCount', 0),
                forks=0,
                watchers=getattr(comp, 'teamCount', 0),
                open_issues=0,
                language=None,
                license=None,
                created_at=None,
                updated_at=str(getattr(comp, 'deadline', None)),
                topics=getattr(comp, 'tags', []) or [],
            )
            repositories.append(repo_info)

        return repositories

    async def _search_notebooks(
        self,
        query: str,
        language: Optional[str],
        max_results: int,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Search Kaggle notebooks/kernels."""
        loop = asyncio.get_event_loop()

        # Map sort field
        sort_map = {
            "votes": "voteCount",
            "stars": "voteCount",
            "updated": "dateRun",
            "hotness": "hotness",
            "relevance": "relevance",
        }
        kaggle_sort = sort_map.get(sort_by, "voteCount")

        # Build search params
        search_params = {
            "search": query,
            "sort_by": kaggle_sort,
            "page": 1,
            "page_size": max_results,
        }
        if language:
            search_params["language"] = language

        notebooks = await loop.run_in_executor(
            None,
            lambda: list(self._api.kernels_list(**search_params))
        )

        # Convert to RepositoryInfo
        repositories = []
        for nb in notebooks:
            repo_info = RepositoryInfo(
                platform="kaggle",
                id=nb.ref,
                url=f"https://www.kaggle.com/code/{nb.ref}",
                name=nb.ref.split("/")[-1] if "/" in nb.ref else nb.ref,
                full_name=nb.ref,
                description=getattr(nb, 'title', ''),
                owner=nb.ref.split("/")[0] if "/" in nb.ref else "unknown",
                stars=getattr(nb, 'totalVotes', 0),
                forks=0,
                watchers=0,
                open_issues=0,
                language=getattr(nb, 'language', None),
                license=None,
                created_at=None,
                updated_at=str(getattr(nb, 'lastRunTime', None)),
                topics=[],
            )
            repositories.append(repo_info)

        return repositories[:max_results]

    async def _search_models(
        self,
        query: str,
        max_results: int,
        sort_by: str,
    ) -> List[RepositoryInfo]:
        """Search Kaggle models."""
        loop = asyncio.get_event_loop()

        try:
            # Model search may not be available in all kaggle versions
            models = await loop.run_in_executor(
                None,
                lambda: list(self._api.model_list(
                    search=query,
                    page_size=max_results,
                ))
            )
        except AttributeError:
            secure_logger.warning("Kaggle model search not available in this version")
            return []
        except Exception as e:
            secure_logger.warning(f"Kaggle model search failed: {e}")
            return []

        # Convert to RepositoryInfo
        repositories = []
        for model in models:
            repo_info = RepositoryInfo(
                platform="kaggle",
                id=getattr(model, 'ref', str(model)),
                url=f"https://www.kaggle.com/models/{getattr(model, 'ref', '')}",
                name=getattr(model, 'title', str(model)),
                full_name=f"model/{getattr(model, 'ref', '')}",
                description=getattr(model, 'subtitle', None) or getattr(model, 'overview', ''),
                owner=getattr(model, 'author', 'unknown'),
                stars=getattr(model, 'downloadCount', 0),
                forks=0,
                watchers=getattr(model, 'instanceCount', 0),
                open_issues=0,
                language=getattr(model, 'modelFramework', None),
                license=None,
                created_at=None,
                updated_at=None,
                topics=getattr(model, 'tags', []) or [],
            )
            repositories.append(repo_info)

        return repositories[:max_results]

    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        """
        Get detailed information about a Kaggle dataset.
        
        Args:
            repo_id: Dataset reference (owner/dataset-slug)
        
        Returns:
            RepositoryInfo with dataset details
        """
        if not self._api:
            raise AuthenticationError("Kaggle API not initialized")

        loop = asyncio.get_event_loop()

        try:
            # Parse the repo_id to determine type
            if repo_id.startswith("competition/"):
                comp_ref = repo_id.replace("competition/", "")
                # Get competition details - not directly supported, search for it
                comps = await loop.run_in_executor(
                    None,
                    lambda: list(self._api.competitions_list())
                )
                comp = next((c for c in comps if c.ref == comp_ref), None)
                if not comp:
                    raise RepositoryNotFoundError(f"Competition not found: {comp_ref}")

                return RepositoryInfo(
                    platform="kaggle",
                    id=comp.ref,
                    url=f"https://www.kaggle.com/competitions/{comp.ref}",
                    name=comp.ref,
                    full_name=f"competition/{comp.ref}",
                    description=getattr(comp, 'description', ''),
                    owner="kaggle",
                    stars=getattr(comp, 'teamCount', 0),
                    topics=getattr(comp, 'tags', []) or [],
                )
            else:
                # Assume it's a dataset
                owner, slug = repo_id.split("/") if "/" in repo_id else ("", repo_id)

                datasets = await loop.run_in_executor(
                    None,
                    lambda: list(self._api.dataset_list(search=slug, page_size=10))
                )

                ds = next((d for d in datasets if d.ref == repo_id), None)
                if not ds:
                    raise RepositoryNotFoundError(f"Dataset not found: {repo_id}")

                return RepositoryInfo(
                    platform="kaggle",
                    id=ds.ref,
                    url=f"https://www.kaggle.com/datasets/{ds.ref}",
                    name=slug,
                    full_name=ds.ref,
                    description=getattr(ds, 'subtitle', None) or getattr(ds, 'title', ''),
                    owner=owner,
                    stars=getattr(ds, 'voteCount', 0),
                    watchers=getattr(ds, 'downloadCount', 0),
                    license=getattr(ds, 'licenseName', None),
                    updated_at=str(getattr(ds, 'lastUpdated', None)),
                    topics=getattr(ds, 'tags', []) or [],
                    size_kb=getattr(ds, 'totalBytes', 0) // 1024,
                )

        except RepositoryNotFoundError:
            raise
        except Exception as e:
            secure_logger.error(f"Failed to get Kaggle resource: {e}")
            raise RepositoryNotFoundError(f"Resource not found: {repo_id}")

    async def get_contents(self, repo_id: str, path: str = "") -> DirectoryListing:
        """Get contents of a directory in the dataset."""
        return await self.list_directory(repo_id, path)

    async def get_file(self, repo_id: str, file_path: str) -> FileContent:
        """Get contents of a specific file."""
        return await self.get_file_content(repo_id, file_path)

    async def clone(self, repo_id: str, destination: Path, depth: int = 1, branch: Optional[str] = None) -> Path:
        """Download dataset to local filesystem."""
        return await self.download_dataset(repo_id, destination, unzip=True)

    async def get_file_content(
        self,
        repo_id: str,
        file_path: str,
    ) -> FileContent:
        """
        Get content of a file from a Kaggle dataset.
        
        Note: This downloads the entire dataset to get a single file.
        For large datasets, consider using download_dataset instead.
        """
        if not self._api:
            raise AuthenticationError("Kaggle API not initialized")

        loop = asyncio.get_event_loop()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Download dataset
            await loop.run_in_executor(
                None,
                lambda: self._api.dataset_download_files(
                    repo_id,
                    path=tmpdir,
                    unzip=True,
                )
            )

            # Read the specific file
            file_full_path = Path(tmpdir) / file_path
            if not file_full_path.exists():
                raise RepositoryNotFoundError(f"File not found: {file_path}")

            content = file_full_path.read_bytes()

            return FileContent(
                path=file_path,
                name=file_full_path.name,
                content=content,
                size=len(content),
            )

    async def list_directory(
        self,
        repo_id: str,
        path: str = "",
    ) -> DirectoryListing:
        """
        List files in a Kaggle dataset.
        
        Args:
            repo_id: Dataset reference (owner/dataset-slug)
            path: Not used for Kaggle (always lists root)
        
        Returns:
            DirectoryListing with dataset files
        """
        if not self._api:
            raise AuthenticationError("Kaggle API not initialized")

        loop = asyncio.get_event_loop()

        try:
            files = await loop.run_in_executor(
                None,
                lambda: list(self._api.dataset_list_files(repo_id).files)
            )

            file_list = []
            for f in files:
                file_list.append({
                    "name": f.name,
                    "size": getattr(f, 'totalBytes', 0),
                    "type": "file",
                })

            return DirectoryListing(
                path="/",
                files=file_list,
                directories=[],
            )

        except Exception as e:
            secure_logger.error(f"Failed to list dataset files: {e}")
            raise RepositoryNotFoundError(f"Dataset not found: {repo_id}")

    # ==================== Extended Kaggle Features ====================

    async def get_trending_datasets(
        self,
        max_results: int = 20,
    ) -> List[KaggleDataset]:
        """Get trending/hot datasets."""
        if not self._api:
            return []

        loop = asyncio.get_event_loop()
        datasets = await loop.run_in_executor(
            None,
            lambda: list(self._api.dataset_list(
                sort_by="hotness",
                page_size=max_results,
            ))
        )

        return [
            KaggleDataset(
                ref=ds.ref,
                title=getattr(ds, 'title', ''),
                subtitle=getattr(ds, 'subtitle', None),
                creator_name=ds.ref.split("/")[0] if "/" in ds.ref else "unknown",
                total_bytes=getattr(ds, 'totalBytes', 0),
                url=f"https://www.kaggle.com/datasets/{ds.ref}",
                last_updated=str(getattr(ds, 'lastUpdated', None)),
                download_count=getattr(ds, 'downloadCount', 0),
                vote_count=getattr(ds, 'voteCount', 0),
                usability_rating=getattr(ds, 'usabilityRating', 0.0),
                tags=getattr(ds, 'tags', []) or [],
                license_name=getattr(ds, 'licenseName', None),
            )
            for ds in datasets
        ]

    async def get_active_competitions(
        self,
        category: Optional[str] = None,
        max_results: int = 20,
    ) -> List[KaggleCompetition]:
        """
        Get active competitions.
        
        Args:
            category: Filter by category (featured, research, playground, etc.)
            max_results: Maximum results
        """
        if not self._api:
            return []

        loop = asyncio.get_event_loop()

        params = {
            "sort_by": "latestDeadline",
            "page_size": max_results,
        }
        if category:
            params["category"] = category

        competitions = await loop.run_in_executor(
            None,
            lambda: list(self._api.competitions_list(**params))
        )

        return [
            KaggleCompetition(
                ref=comp.ref,
                title=getattr(comp, 'title', ''),
                description=getattr(comp, 'description', None),
                url=f"https://www.kaggle.com/competitions/{comp.ref}",
                deadline=str(getattr(comp, 'deadline', None)),
                category=getattr(comp, 'category', ''),
                reward=getattr(comp, 'reward', None),
                team_count=getattr(comp, 'teamCount', 0),
                user_has_entered=getattr(comp, 'userHasEntered', False),
                tags=getattr(comp, 'tags', []) or [],
                evaluation_metric=getattr(comp, 'evaluationMetric', None),
            )
            for comp in competitions
        ]

    async def get_trending_notebooks(
        self,
        language: Optional[str] = None,
        max_results: int = 20,
    ) -> List[KaggleNotebook]:
        """
        Get trending notebooks.
        
        Args:
            language: Filter by language (python, r, etc.)
            max_results: Maximum results
        """
        if not self._api:
            return []

        loop = asyncio.get_event_loop()

        params = {
            "sort_by": "hotness",
            "page_size": max_results,
        }
        if language:
            params["language"] = language

        notebooks = await loop.run_in_executor(
            None,
            lambda: list(self._api.kernels_list(**params))
        )

        return [
            KaggleNotebook(
                ref=nb.ref,
                title=getattr(nb, 'title', ''),
                author=nb.ref.split("/")[0] if "/" in nb.ref else "unknown",
                url=f"https://www.kaggle.com/code/{nb.ref}",
                last_run_time=str(getattr(nb, 'lastRunTime', None)),
                total_votes=getattr(nb, 'totalVotes', 0),
                language=getattr(nb, 'language', 'python'),
                kernel_type=getattr(nb, 'kernelType', 'notebook'),
                is_private=getattr(nb, 'isPrivate', False),
            )
            for nb in notebooks
        ]

    async def download_dataset(
        self,
        dataset_ref: str,
        destination: Path,
        unzip: bool = True,
    ) -> Path:
        """
        Download a Kaggle dataset.
        
        Args:
            dataset_ref: Dataset reference (owner/dataset-slug)
            destination: Download destination directory
            unzip: Whether to unzip the downloaded files
        
        Returns:
            Path to downloaded dataset
        """
        if not self._api:
            raise AuthenticationError("Kaggle API not initialized")

        loop = asyncio.get_event_loop()

        destination.mkdir(parents=True, exist_ok=True)

        await loop.run_in_executor(
            None,
            lambda: self._api.dataset_download_files(
                dataset_ref,
                path=str(destination),
                unzip=unzip,
            )
        )

        secure_logger.info(f"Downloaded dataset {dataset_ref} to {destination}")
        return destination

    async def download_competition_data(
        self,
        competition_ref: str,
        destination: Path,
    ) -> Path:
        """
        Download competition data files.
        
        Args:
            competition_ref: Competition reference
            destination: Download destination directory
        
        Returns:
            Path to downloaded data
        """
        if not self._api:
            raise AuthenticationError("Kaggle API not initialized")

        loop = asyncio.get_event_loop()

        destination.mkdir(parents=True, exist_ok=True)

        await loop.run_in_executor(
            None,
            lambda: self._api.competition_download_files(
                competition_ref,
                path=str(destination),
            )
        )

        secure_logger.info(f"Downloaded competition data {competition_ref} to {destination}")
        return destination


def create_kaggle_client() -> Optional[KaggleClient]:
    """Factory function to create Kaggle client if credentials are available."""
    settings = get_settings()

    if settings.platforms.kaggle_username and settings.platforms.kaggle_key.get_secret_value():
        return KaggleClient()

    return None
