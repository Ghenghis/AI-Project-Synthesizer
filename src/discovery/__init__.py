"""
AI Project Synthesizer - Discovery Module

This module handles repository discovery across multiple platforms:
- GitHub (via ghapi)
- HuggingFace (via huggingface_hub)
- Kaggle (via kaggle API) - datasets, competitions, notebooks, models
- GitLab (via python-gitlab)
- arXiv (via arxiv)
- Papers with Code (via paperswithcode-client)
- Semantic Scholar (via semanticscholar)
"""

from src.discovery.base_client import (
    PlatformClient,
    RepositoryInfo,
    SearchResult,
    DiscoveryError,
)
from src.discovery.github_client import GitHubClient
from src.discovery.huggingface_client import HuggingFaceClient
from src.discovery.kaggle_client import (
    KaggleClient,
    KaggleDataset,
    KaggleCompetition,
    KaggleNotebook,
    KaggleModel,
    KaggleResourceType,
)
from src.discovery.unified_search import UnifiedSearch, create_unified_search

__all__ = [
    # Base
    "PlatformClient",
    "RepositoryInfo", 
    "SearchResult",
    "DiscoveryError",
    # Clients
    "GitHubClient",
    "HuggingFaceClient",
    "KaggleClient",
    # Kaggle types
    "KaggleDataset",
    "KaggleCompetition",
    "KaggleNotebook",
    "KaggleModel",
    "KaggleResourceType",
    # Unified search
    "UnifiedSearch",
    "create_unified_search",
]
