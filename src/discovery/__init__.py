"""
AI Project Synthesizer - Discovery Module

This module handles repository discovery across multiple platforms:
- GitHub (via ghapi)
- HuggingFace (via huggingface_hub)
- Kaggle (via kaggle API)
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
from src.discovery.unified_search import UnifiedSearch

__all__ = [
    "PlatformClient",
    "RepositoryInfo", 
    "SearchResult",
    "DiscoveryError",
    "GitHubClient",
    "UnifiedSearch",
]
