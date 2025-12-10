"""
AI Project Synthesizer - MCP Tool Handlers

Implementation of all MCP tool handlers.
These handle the actual business logic for each tool.
"""

import asyncio
import logging
import tempfile
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from src.discovery.unified_search import UnifiedSearch, create_unified_search
from src.discovery.github_client import GitHubClient
from src.discovery.huggingface_client import HuggingFaceClient
from src.analysis.dependency_analyzer import DependencyAnalyzer
from src.analysis.ast_parser import ASTParser
from src.analysis.code_extractor import CodeExtractor
from src.analysis.quality_scorer import QualityScorer
from src.analysis.compatibility_checker import CompatibilityChecker
from src.synthesis.project_builder import ProjectBuilder
from src.generation.readme_generator import ReadmeGenerator
from src.generation.diagram_generator import DiagramGenerator
from src.core.config import get_settings
from src.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

# Global instances (initialized on first use)
_unified_search: Optional[UnifiedSearch] = None
_dependency_analyzer: Optional[DependencyAnalyzer] = None
_synthesis_jobs: Dict[str, Dict[str, Any]] = {}


def get_unified_search() -> UnifiedSearch:
    """Get or create unified search instance."""
    global _unified_search
    if _unified_search is None:
        _unified_search = create_unified_search()
    return _unified_search


def get_dependency_analyzer() -> DependencyAnalyzer:
    """Get or create dependency analyzer instance."""
    global _dependency_analyzer
    if _dependency_analyzer is None:
        _dependency_analyzer = DependencyAnalyzer()
    return _dependency_analyzer


async def handle_search_repositories(args: dict) -> dict:
    """
    Handle repository search across platforms.
    
    Args:
        query: Search query string
        platforms: List of platforms to search
        max_results: Maximum results per platform
        language_filter: Optional language filter
        min_stars: Minimum star count
    
    Returns:
        Search results with repository information
    """
    query = args.get("query", "")
    platforms = args.get("platforms", ["github", "huggingface"])
    max_results = args.get("max_results", 20)
    language_filter = args.get("language_filter")
    min_stars = args.get("min_stars", 10)
    
    if not query:
        return {
            "error": True,
            "message": "Query is required",
        }
    
    logger.info(f"Searching repositories: {query} on {platforms}")
    
    try:
        search = get_unified_search()
        result = await search.search(
            query=query,
            platforms=platforms,
            max_results=max_results,
            language_filter=language_filter,
            min_stars=min_stars,
        )
        
        return {
            "status": "success",
            "query": result.query,
            "platforms_searched": result.platforms_searched,
            "total_count": result.total_count,
            "search_time_ms": result.search_time_ms,
            "repositories": [
                {
                    "platform": repo.platform,
                    "name": repo.full_name,
                    "url": repo.url,
                    "description": repo.description,
                    "stars": repo.stars,
                    "language": repo.language,
                    "updated_at": str(repo.updated_at) if repo.updated_at else None,
                    "topics": list(repo.topics) if repo.topics else [],
                }
                for repo in result.repositories
            ],
            "platform_counts": result.platform_counts,
            "errors": result.errors if result.errors else None,
        }
        
    except Exception as e:
        logger.exception("Search failed")
        return {
            "error": True,
            "message": str(e),
        }


async def handle_analyze_repository(args: dict) -> dict:
    """
    Handle deep repository analysis.
    
    Args:
        repo_url: Repository URL to analyze
        include_transitive_deps: Whether to include transitive dependencies
        extract_components: Whether to identify extractable components
    
    Returns:
        Analysis results with dependencies, components, and quality score
    """
    repo_url = args.get("repo_url", "")
    include_transitive = args.get("include_transitive_deps", True)
    extract_components = args.get("extract_components", True)
    
    if not repo_url:
        return {
            "error": True,
            "message": "Repository URL is required",
        }
    
    # Validate repository URL
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(repo_url):
        return {
            "error": True,
            "message": f"Invalid repository URL: {repo_url}",
        }
    
    logger.info(f"Analyzing repository: {repo_url}")
    
    try:
        # Get repository info
        search = get_unified_search()
        repo_info = await search.get_repository(repo_url)
        
        if not repo_info:
            return {
                "error": True,
                "message": f"Repository not found: {repo_url}",
            }
        
        # Clone to temp directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / repo_info.name
            
            # Get client for platform
            platform = search._detect_platform(repo_url)
            client = search._clients.get(platform)
            
            if not client:
                return {
                    "error": True,
                    "message": f"Platform not supported: {platform}",
                }
            
            # Clone repository
            repo_id = search._extract_repo_id(repo_url, platform)
            await client.clone(repo_id, temp_path, depth=1)
            
            # Analyze dependencies
            analyzer = get_dependency_analyzer()
            dep_graph = await analyzer.analyze(temp_path)
            
            # Analyze code structure
            ast_parser = ASTParser()
            code_structure = await ast_parser.analyze_project(temp_path)
            
            # Calculate quality score
            scorer = QualityScorer()
            quality = await scorer.score(temp_path, repo_info)
            
            # Extract components if requested
            components = []
            if extract_components:
                extractor = CodeExtractor()
                components = await extractor.identify_components(temp_path)
            
            return {
                "status": "success",
                "repository": {
                    "platform": repo_info.platform,
                    "name": repo_info.full_name,
                    "url": repo_info.url,
                    "description": repo_info.description,
                    "stars": repo_info.stars,
                    "language": repo_info.language,
                },
                "languages": code_structure.get("languages", {}),
                "dependencies": dep_graph.to_dict(),
                "components": [c.to_dict() for c in components] if components else [],
                "quality_score": quality.to_dict(),
                "files_analyzed": code_structure.get("file_count", 0),
                "lines_of_code": code_structure.get("total_loc", 0),
            }
            
    except Exception as e:
        logger.exception("Analysis failed")
        return {
            "error": True,
            "message": str(e),
        }


async def handle_check_compatibility(args: dict) -> dict:
    """
    Handle compatibility check between repositories.
    
    Args:
        repo_urls: List of repository URLs to check
        target_python_version: Target Python version
    
    Returns:
        Compatibility report with conflicts and suggestions
    """
    repo_urls = args.get("repo_urls", [])
    python_version = args.get("target_python_version", "3.11")
    
    if not repo_urls or len(repo_urls) < 2:
        return {
            "error": True,
            "message": "At least 2 repository URLs are required",
        }
    
    logger.info(f"Checking compatibility for {len(repo_urls)} repositories")
    
    try:
        search = get_unified_search()
        analyzer = get_dependency_analyzer()
        checker = CompatibilityChecker()
        
        all_deps = []
        repo_infos = []
        
        # Analyze each repository
        for url in repo_urls:
            repo_info = await search.get_repository(url)
            if not repo_info:
                continue
            
            repo_infos.append(repo_info)
            
            # Clone and analyze
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / repo_info.name
                platform = search._detect_platform(url)
                client = search._clients.get(platform)
                
                if client:
                    repo_id = search._extract_repo_id(url, platform)
                    await client.clone(repo_id, temp_path, depth=1)
                    dep_graph = await analyzer.analyze(temp_path)
                    all_deps.append(dep_graph)
        
        # Check compatibility
        compatibility = await checker.check(all_deps, python_version)
        
        return {
            "status": "success",
            "repositories_checked": len(repo_infos),
            "python_version": python_version,
            "compatible": compatibility.is_compatible,
            "conflicts": [
                {
                    "package": c.package_name,
                    "versions": [c.dep_a.version_spec, c.dep_b.version_spec],
                    "reason": c.reason,
                    "resolvable": c.resolvable,
                    "suggested_version": c.suggested_version,
                }
                for c in compatibility.conflicts
            ],
            "warnings": compatibility.warnings,
            "merged_dependencies": compatibility.merged_count,
        }
        
    except Exception as e:
        logger.exception("Compatibility check failed")
        return {
            "error": True,
            "message": str(e),
        }


async def handle_resolve_dependencies(args: dict) -> dict:
    """
    Handle dependency resolution across repositories.
    
    Args:
        repositories: List of repository URLs
        constraints: Additional version constraints
        python_version: Target Python version
    
    Returns:
        Resolved dependencies with unified requirements
    """
    repositories = args.get("repositories", [])
    constraints = args.get("constraints", [])
    python_version = args.get("python_version", "3.11")
    
    if not repositories:
        return {
            "error": True,
            "message": "At least one repository URL is required",
        }
    
    logger.info(f"Resolving dependencies for {len(repositories)} repositories")
    
    try:
        from src.resolution.unified_resolver import UnifiedResolver
        
        resolver = UnifiedResolver()
        result = await resolver.resolve(
            repository_urls=repositories,
            python_version=python_version,
            additional_constraints=constraints,
        )
        
        return {
            "status": "success",
            "python_version": python_version,
            "packages_resolved": len(result.packages),
            "packages": [
                {
                    "name": pkg.name,
                    "version": pkg.version,
                    "source": pkg.source,
                }
                for pkg in result.packages
            ],
            "requirements_txt": result.requirements_txt,
            "conflicts_resolved": len(result.conflicts_resolved),
            "warnings": result.warnings,
        }
        
    except Exception as e:
        logger.exception("Dependency resolution failed")
        return {
            "error": True,
            "message": str(e),
        }


async def handle_synthesize_project(args: dict) -> dict:
    """
    Handle project synthesis from multiple repositories.
    
    Args:
        repositories: List of repo configs (url, components, destination)
        project_name: Name for the synthesized project
        output_path: Output directory path
        template: Project template to use
    
    Returns:
        Synthesis result with project path and status
    """
    repositories = args.get("repositories", [])
    project_name = args.get("project_name", "")
    output_path = args.get("output_path", "")
    template = args.get("template", "python-default")
    
    if not repositories:
        return {
            "error": True,
            "message": "At least one repository is required",
        }
    
    if not project_name:
        return {
            "error": True,
            "message": "Project name is required",
        }
    
    if not output_path:
        return {
            "error": True,
            "message": "Output path is required",
        }
    
    # Validate repository URLs
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    for repo in repositories:
        repo_url = repo.get("repo_url", "")
        if not url_pattern.match(repo_url):
            return {
                "error": True,
                "message": f"Invalid repository URL: {repo_url}",
            }
    
    # Create synthesis job
    job_id = str(uuid.uuid4())
    _synthesis_jobs[job_id] = {
        "id": job_id,
        "status": "started",
        "progress": 0,
        "started_at": datetime.now().isoformat(),
        "repositories": len(repositories),
    }
    
    logger.info(f"Starting synthesis job {job_id}: {project_name}")
    
    try:
        builder = ProjectBuilder()
        
        # Update progress
        _synthesis_jobs[job_id]["status"] = "cloning"
        _synthesis_jobs[job_id]["progress"] = 10
        
        result = await builder.build(
            repositories=repositories,
            project_name=project_name,
            output_path=Path(output_path),
            template=template,
            progress_callback=lambda p, s: _update_job(job_id, p, s),
        )
        
        _synthesis_jobs[job_id]["status"] = "complete"
        _synthesis_jobs[job_id]["progress"] = 100
        _synthesis_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "synthesis_id": job_id,
            "project_path": str(result.project_path),
            "project_name": project_name,
            "repositories_processed": result.repos_processed,
            "components_extracted": result.components_extracted,
            "dependencies_merged": result.deps_merged,
            "files_created": result.files_created,
            "documentation": result.docs_generated,
            "warnings": result.warnings,
        }
        
    except Exception as e:
        logger.exception("Synthesis failed")
        _synthesis_jobs[job_id]["status"] = "failed"
        _synthesis_jobs[job_id]["error"] = str(e)
        
        return {
            "error": True,
            "message": str(e),
            "synthesis_id": job_id,
        }


def _update_job(job_id: str, progress: int, status: str):
    """Update synthesis job progress."""
    if job_id in _synthesis_jobs:
        _synthesis_jobs[job_id]["progress"] = progress
        _synthesis_jobs[job_id]["status"] = status


async def handle_generate_documentation(args: dict) -> dict:
    """
    Handle documentation generation for a project.
    
    Args:
        project_path: Path to the project
        doc_types: Types of documentation to generate
        llm_enhanced: Whether to use LLM for enhanced docs
    
    Returns:
        Generated documentation paths
    """
    project_path = args.get("project_path", "")
    doc_types = args.get("doc_types", ["readme", "architecture", "api"])
    llm_enhanced = args.get("llm_enhanced", True)
    
    if not project_path:
        return {
            "error": True,
            "message": "Project path is required",
        }
    
    path = Path(project_path)
    if not path.exists():
        return {
            "error": True,
            "message": f"Project path does not exist: {project_path}",
        }
    
    logger.info(f"Generating documentation for: {project_path}")
    
    try:
        generated = []
        
        # README generation
        if "readme" in doc_types:
            readme_gen = ReadmeGenerator(use_llm=llm_enhanced)
            readme_path = await readme_gen.generate(path)
            generated.append({
                "type": "readme",
                "path": str(readme_path),
            })
        
        # Architecture documentation
        if "architecture" in doc_types:
            diagram_gen = DiagramGenerator()
            arch_path = await diagram_gen.generate_architecture(path)
            generated.append({
                "type": "architecture",
                "path": str(arch_path),
            })
        
        # API documentation
        if "api" in doc_types:
            # Generate API docs based on project type
            docs_path = path / "docs" / "api"
            docs_path.mkdir(parents=True, exist_ok=True)
            
            # Placeholder for API doc generation
            api_doc = docs_path / "API_REFERENCE.md"
            api_doc.write_text("# API Reference\n\nGenerated API documentation.\n")
            generated.append({
                "type": "api",
                "path": str(api_doc),
            })
        
        # Diagrams
        if "diagrams" in doc_types:
            diagram_gen = DiagramGenerator()
            diagrams = await diagram_gen.generate_all(path)
            for diagram_type, diagram_path in diagrams.items():
                generated.append({
                    "type": f"diagram_{diagram_type}",
                    "path": str(diagram_path),
                })
        
        return {
            "status": "success",
            "project_path": project_path,
            "documents_generated": len(generated),
            "documents": generated,
            "llm_enhanced": llm_enhanced,
        }
        
    except Exception as e:
        logger.exception("Documentation generation failed")
        return {
            "error": True,
            "message": str(e),
        }


async def handle_get_synthesis_status(args: dict) -> dict:
    """
    Handle status query for synthesis operations.
    
    Args:
        synthesis_id: ID of the synthesis operation
    
    Returns:
        Current status of the synthesis operation
    """
    synthesis_id = args.get("synthesis_id", "")
    
    if not synthesis_id:
        return {
            "error": True,
            "message": "Synthesis ID is required",
        }
    
    if synthesis_id not in _synthesis_jobs:
        return {
            "error": True,
            "message": f"Synthesis job not found: {synthesis_id}",
        }
    
    job = _synthesis_jobs[synthesis_id]
    
    return {
        "status": "success",
        "synthesis_id": synthesis_id,
        "job_status": job["status"],
        "progress": job["progress"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "error": job.get("error"),
    }


# Register tools with MCP server
def register_all_tools(server):
    """Register all tool handlers with the MCP server."""
    # Tools are registered via decorators in server.py
    pass


def register_all_resources(server):
    """Register all resources with the MCP server."""
    # Resources for cached data access
    pass


def register_all_prompts(server):
    """Register all prompts with the MCP server."""
    # Pre-defined prompts for common tasks
    pass
