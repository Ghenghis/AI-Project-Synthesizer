"""
AI Project Synthesizer - MCP Tool Handlers

Implementation of all MCP tool handlers.
These handle the actual business logic for each tool.
"""

import asyncio
import logging
import re
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.analysis.ast_parser import ASTParser
from src.analysis.code_extractor import CodeExtractor
from src.analysis.compatibility_checker import CompatibilityChecker
from src.analysis.dependency_analyzer import DependencyAnalyzer
from src.analysis.quality_scorer import QualityScorer
from src.core.config import get_settings
from src.core.observability import correlation_manager, metrics, track_performance
from src.core.security import InputValidator, get_secure_logger
from src.discovery.unified_search import UnifiedSearch, create_unified_search
from src.generation.diagram_generator import DiagramGenerator
from src.generation.readme_generator import ReadmeGenerator
from src.synthesis.project_builder import ProjectBuilder

logger = logging.getLogger(__name__)

# Timeout constants for different operations
TIMEOUT_API_CALL = 30  # seconds
TIMEOUT_GIT_CLONE = 300  # seconds (5 minutes)
TIMEOUT_FILE_OPERATIONS = 60  # seconds
TIMEOUT_SYNTHESIS = 600  # seconds (10 minutes)

secure_logger = get_secure_logger(__name__)

# Global instances (initialized on first use)
_unified_search: UnifiedSearch | None = None
_dependency_analyzer: DependencyAnalyzer | None = None
_synthesis_jobs: dict[str, dict[str, Any]] = {}
_synthesis_jobs_lock = threading.Lock()  # Thread-safe access to synthesis jobs


def get_synthesis_job(job_id: str) -> dict[str, Any] | None:
    """Thread-safe getter for synthesis job."""
    with _synthesis_jobs_lock:
        return _synthesis_jobs.get(job_id)


def set_synthesis_job(job_id: str, job_data: dict[str, Any]) -> None:
    """Thread-safe setter for synthesis job."""
    with _synthesis_jobs_lock:
        _synthesis_jobs[job_id] = job_data


def update_synthesis_job(job_id: str, **updates) -> None:
    """Thread-safe update for synthesis job."""
    with _synthesis_jobs_lock:
        if job_id in _synthesis_jobs:
            _synthesis_jobs[job_id].update(updates)


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


@track_performance("tool_search_repositories")
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

    correlation_id = correlation_manager.get_correlation_id()
    settings = get_settings()

    # Input validation
    if not query:
        return {
            "error": True,
            "message": "Query is required",
            "correlation_id": correlation_id,
        }

    if not InputValidator.validate_search_query(query):
        return {
            "error": True,
            "message": f"Invalid search query: exceeds maximum length of {settings.app.max_query_length} characters",
            "correlation_id": correlation_id,
        }

    if max_results < 1 or max_results > 100:
        return {
            "error": True,
            "message": "max_results must be between 1 and 100",
            "correlation_id": correlation_id,
        }

    if min_stars < 0:
        return {
            "error": True,
            "message": "min_stars must be non-negative",
            "correlation_id": correlation_id,
        }

    secure_logger.info(
        "Searching repositories",
        correlation_id=correlation_id,
        query=query[:100],  # Limit in logs
        platforms=platforms,
        max_results=max_results,
    )

    metrics.increment("search_requests_total", tags={"platforms": ",".join(platforms)})

    try:
        search = get_unified_search()

        # Add timeout protection to search operation
        result = await asyncio.wait_for(
            search.search(
                query=query,
                platforms=platforms,
                max_results=max_results,
                language_filter=language_filter,
                min_stars=min_stars,
            ),
            timeout=TIMEOUT_API_CALL,
        )

        secure_logger.info(
            "Search completed successfully",
            correlation_id=correlation_id,
            result_count=len(result.repositories),
            total_results=result.total_count,
        )

        metrics.increment(
            "search_success_total", tags={"platforms": ",".join(platforms)}
        )
        metrics.record_histogram("search_results_count", len(result.repositories))

        return {
            "success": True,
            "query": query,
            "platforms": platforms,
            "total_count": result.total_count,
            "repositories": [
                {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "url": repo.url,
                    "description": repo.description,
                    "stars": repo.stars,
                    "language": repo.language,
                    "platform": repo.platform,
                    "updated_at": repo.updated_at.isoformat()
                    if hasattr(repo.updated_at, "isoformat")
                    else repo.updated_at,
                }
                for repo in result.repositories
            ],
            "search_time_ms": result.search_time_ms,
            "correlation_id": correlation_id,
        }

    except TimeoutError:
        secure_logger.error(
            f"Search timed out after {TIMEOUT_API_CALL}s", correlation_id=correlation_id
        )
        metrics.increment("search_timeout_total")
        return {
            "error": True,
            "message": f"Search timed out after {TIMEOUT_API_CALL} seconds",
            "correlation_id": correlation_id,
        }

    except Exception as e:
        secure_logger.error(
            f"Search failed: {str(e)[:200]}",
            correlation_id=correlation_id,
            error_type=type(e).__name__,
        )
        metrics.increment("search_error_total", tags={"error_type": type(e).__name__})
        return {
            "error": True,
            "message": f"Search failed: {str(e)[:200]}",
            "correlation_id": correlation_id,
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
    args.get("include_transitive_deps", True)
    extract_components = args.get("extract_components", True)

    if not repo_url:
        return {
            "error": True,
            "message": "Repository URL is required",
        }

    # Validate repository URL
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

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

            # Clone repository with timeout protection
            try:
                repo_id = search._extract_repo_id(repo_url, platform)
                await asyncio.wait_for(
                    client.clone(repo_id, temp_path, depth=1), timeout=TIMEOUT_GIT_CLONE
                )
            except TimeoutError:
                return {
                    "error": True,
                    "message": f"Git clone timed out after {TIMEOUT_GIT_CLONE} seconds",
                }

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
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    for repo in repositories:
        repo_url = repo.get("repo_url", "")
        if not url_pattern.match(repo_url):
            return {
                "error": True,
                "message": f"Invalid repository URL: {repo_url}",
            }

    # Create synthesis job (thread-safe)
    job_id = str(uuid.uuid4())
    set_synthesis_job(
        job_id,
        {
            "id": job_id,
            "status": "started",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "repositories": len(repositories),
        },
    )

    logger.info(f"Starting synthesis job {job_id}: {project_name}")

    try:
        builder = ProjectBuilder()

        # Update progress (thread-safe)
        update_synthesis_job(job_id, status="cloning", progress=10)

        # Add timeout protection to synthesis operation
        result = await asyncio.wait_for(
            builder.build(
                repositories=repositories,
                project_name=project_name,
                output_path=Path(output_path),
                template=template,
                progress_callback=lambda p, s: _update_job(job_id, p, s),
            ),
            timeout=TIMEOUT_SYNTHESIS,
        )

        update_synthesis_job(
            job_id,
            status="complete",
            progress=100,
            completed_at=datetime.now().isoformat(),
        )

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

    except TimeoutError:
        update_synthesis_job(
            job_id,
            status="failed",
            error=f"Synthesis timed out after {TIMEOUT_SYNTHESIS} seconds",
        )
        return {
            "error": True,
            "message": f"Synthesis timed out after {TIMEOUT_SYNTHESIS} seconds",
            "synthesis_id": job_id,
        }

    except Exception as e:
        logger.exception("Synthesis failed")
        update_synthesis_job(job_id, status="failed", error=str(e))

        return {
            "error": True,
            "message": str(e),
            "synthesis_id": job_id,
        }


def _update_job(job_id: str, progress: int, status: str):
    """Update synthesis job progress (thread-safe)."""
    update_synthesis_job(job_id, progress=progress, status=status)


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
            generated.append(
                {
                    "type": "readme",
                    "path": str(readme_path),
                }
            )

        # Architecture documentation
        if "architecture" in doc_types:
            diagram_gen = DiagramGenerator()
            arch_path = await diagram_gen.generate_architecture(path)
            generated.append(
                {
                    "type": "architecture",
                    "path": str(arch_path),
                }
            )

        # API documentation
        if "api" in doc_types:
            # Generate API docs based on project type
            docs_path = path / "docs" / "api"
            docs_path.mkdir(parents=True, exist_ok=True)

            # Placeholder for API doc generation
            api_doc = docs_path / "API_REFERENCE.md"
            api_doc.write_text("# API Reference\n\nGenerated API documentation.\n")
            generated.append(
                {
                    "type": "api",
                    "path": str(api_doc),
                }
            )

        # Diagrams
        if "diagrams" in doc_types:
            diagram_gen = DiagramGenerator()
            diagrams = await diagram_gen.generate_all(path)
            for diagram_type, diagram_path in diagrams.items():
                generated.append(
                    {
                        "type": f"diagram_{diagram_type}",
                        "path": str(diagram_path),
                    }
                )

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

    job = get_synthesis_job(synthesis_id)
    if job is None:
        return {
            "error": True,
            "message": f"Synthesis job not found: {synthesis_id}",
        }

    return {
        "status": "success",
        "synthesis_id": synthesis_id,
        "job_status": job["status"],
        "progress": job["progress"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "error": job.get("error"),
    }


# ============================================
# Direct Tool Functions (for CLI and testing)
# ============================================


async def search_repositories(
    query: str,
    platforms: list[str] = None,
    max_results: int = 20,
    language_filter: str | None = None,
    min_stars: int = 10,
) -> dict:
    """
    Search for repositories across platforms.

    Direct function wrapper for handle_search_repositories.
    """
    return await handle_search_repositories(
        {
            "query": query,
            "platforms": platforms or ["github", "huggingface"],
            "max_results": max_results,
            "language_filter": language_filter,
            "min_stars": min_stars,
        }
    )


async def analyze_repository(
    repo_url: str,
    include_transitive_deps: bool = True,
    extract_components: bool = True,
) -> dict:
    """
    Analyze a repository.

    Direct function wrapper for handle_analyze_repository.
    """
    return await handle_analyze_repository(
        {
            "repo_url": repo_url,
            "include_transitive_deps": include_transitive_deps,
            "extract_components": extract_components,
        }
    )


async def check_compatibility(
    repo_urls: list[str],
    target_python_version: str = "3.11",
) -> dict:
    """
    Check compatibility between repositories.

    Direct function wrapper for handle_check_compatibility.
    """
    return await handle_check_compatibility(
        {
            "repo_urls": repo_urls,
            "target_python_version": target_python_version,
        }
    )


async def resolve_dependencies(
    repositories: list[str],
    constraints: list[str] = None,
    python_version: str = "3.11",
) -> dict:
    """
    Resolve dependencies across repositories.

    Direct function wrapper for handle_resolve_dependencies.
    """
    return await handle_resolve_dependencies(
        {
            "repositories": repositories,
            "constraints": constraints or [],
            "python_version": python_version,
        }
    )


async def synthesize_project(
    repositories: list[dict],
    project_name: str,
    output_path: str,
    template: str = "python-default",
) -> dict:
    """
    Synthesize a project from multiple repositories.

    Direct function wrapper for handle_synthesize_project.
    """
    return await handle_synthesize_project(
        {
            "repositories": repositories,
            "project_name": project_name,
            "output_path": output_path,
            "template": template,
        }
    )


async def generate_documentation(
    project_path: str,
    doc_types: list[str] = None,
    llm_enhanced: bool = True,
) -> dict:
    """
    Generate documentation for a project.

    Direct function wrapper for handle_generate_documentation.
    """
    return await handle_generate_documentation(
        {
            "project_path": project_path,
            "doc_types": doc_types or ["readme", "architecture", "api"],
            "llm_enhanced": llm_enhanced,
        }
    )


async def get_synthesis_status(synthesis_id: str) -> dict:
    """
    Get the status of a synthesis operation.

    Direct function wrapper for handle_get_synthesis_status.
    """
    return await handle_get_synthesis_status(
        {
            "synthesis_id": synthesis_id,
        }
    )


async def get_platforms() -> dict:
    """
    Get available platforms for repository search.

    Returns:
        Dictionary with platform information
    """
    settings = get_settings()
    enabled = settings.platforms.get_enabled_platforms()

    return {
        "status": "success",
        "platforms": {
            "github": {
                "enabled": "github" in enabled,
                "description": "GitHub repositories",
            },
            "huggingface": {
                "enabled": "huggingface" in enabled,
                "description": "HuggingFace models, datasets, and spaces",
            },
            "kaggle": {
                "enabled": "kaggle" in enabled,
                "description": "Kaggle datasets and notebooks",
            },
            "arxiv": {
                "enabled": "arxiv" in enabled,
                "description": "arXiv papers with code",
            },
        },
    }


# ==================== ASSISTANT TOOLS ====================

_assistant = None


def get_assistant():
    """Get or create assistant instance."""
    global _assistant
    if _assistant is None:
        from src.assistant.core import AssistantConfig, ConversationalAssistant

        _assistant = ConversationalAssistant(
            AssistantConfig(
                voice_enabled=True,
                auto_speak=False,  # Don't auto-generate audio for MCP
            )
        )
    return _assistant


async def handle_assistant_chat(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Chat with the AI assistant.

    The assistant will:
    - Understand your request
    - Ask clarifying questions if needed
    - Search for projects
    - Provide recommendations

    Args:
        message: Your message to the assistant
        voice_enabled: Whether to generate voice audio (default: false)

    Returns:
        Assistant's response with text and optional audio
    """
    correlation_id = correlation_manager.get_correlation_id()

    message = arguments.get("message", "")
    voice_enabled = arguments.get("voice_enabled", False)

    if not message:
        return {
            "error": True,
            "message": "Please provide a message",
        }

    try:
        assistant = get_assistant()
        assistant.config.voice_enabled = voice_enabled

        response = await assistant.chat(message)

        return {
            "success": True,
            "response": response["text"],
            "has_audio": response["audio"] is not None,
            "state": response["state"],
            "suggested_actions": response["actions"],
            "correlation_id": correlation_id,
        }

    except Exception as e:
        secure_logger.error(f"Assistant error: {e}", correlation_id=correlation_id)
        return {
            "error": True,
            "message": f"Assistant error: {str(e)}",
            "correlation_id": correlation_id,
        }


async def handle_assistant_voice(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Generate voice audio for text AND auto-play it.

    LM STUDIO INTEGRATION:
    LM Studio doesn't have native audio playback, so this tool
    automatically plays the generated audio through system speakers.

    Args:
        text: Text to convert to speech
        voice: Voice name (rachel, josh, adam, etc.) or voice ID
        auto_play: Whether to auto-play (default: true for LM Studio)

    Returns:
        Audio data as base64 + playback status
    """
    import base64

    text = arguments.get("text", "")
    voice = arguments.get("voice", "rachel")
    auto_play = arguments.get("auto_play", True)  # Default ON for LM Studio

    if not text:
        return {"error": True, "message": "Please provide text"}

    try:
        from src.voice.elevenlabs_client import ElevenLabsClient

        client = ElevenLabsClient()

        audio = await client.text_to_speech(text, voice=voice)
        audio_base64 = base64.b64encode(audio).decode()

        # Auto-play for LM Studio
        playback_status = "skipped"
        if auto_play:
            try:
                from src.voice.player import play_audio

                result = await play_audio(audio_base64, format="mp3", wait=False)
                playback_status = (
                    "playing" if result.success else f"failed: {result.error}"
                )
            except Exception as e:
                playback_status = f"error: {e}"

        await client.close()

        return {
            "success": True,
            "audio_base64": audio_base64,
            "format": "mp3",
            "voice": voice,
            "text_length": len(text),
            "audio_size_bytes": len(audio),
            "playback_status": playback_status,
            "note": "Audio is playing through your speakers"
            if auto_play and playback_status == "playing"
            else None,
        }

    except Exception as e:
        return {"error": True, "message": f"Voice error: {str(e)}"}


async def handle_assistant_toggle_voice(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Toggle voice on/off for the assistant.

    Args:
        enabled: Whether voice should be enabled

    Returns:
        Current voice status
    """
    enabled = arguments.get("enabled", True)

    assistant = get_assistant()
    assistant.set_voice_enabled(enabled)

    return {
        "success": True,
        "voice_enabled": assistant.config.voice_enabled,
        "message": f"Voice {'enabled' if enabled else 'disabled'}",
    }


async def handle_get_voices(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Get available voices for text-to-speech.

    Returns:
        List of available voices with descriptions
    """
    from src.voice.elevenlabs_client import PREMADE_VOICES

    voices = []
    for name, voice in PREMADE_VOICES.items():
        voices.append(
            {
                "name": name,
                "voice_id": voice.voice_id,
                "description": voice.description,
            }
        )

    return {
        "success": True,
        "voices": voices,
        "default": "rachel",
    }


async def handle_speak_fast(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    FAST streaming voice - optimized for speed and smooth playback.

    LM STUDIO INTEGRATION:
    Uses turbo model + streaming for lowest latency.
    Audio plays as it's generated - no waiting, no gaps.

    Args:
        text: Text to speak
        voice: Voice name (rachel, josh, adam, etc.)

    Returns:
        Success status
    """
    text = arguments.get("text", "")
    voice = arguments.get("voice", "rachel")

    if not text:
        return {"error": True, "message": "Please provide text"}

    try:
        from src.voice.streaming_player import speak_fast

        success = await speak_fast(text, voice)

        return {
            "success": success,
            "voice": voice,
            "mode": "streaming",
            "model": "eleven_turbo_v2_5",
            "note": "Audio streamed directly to speakers"
            if success
            else "Playback failed",
        }

    except Exception as e:
        return {"error": True, "message": f"Streaming error: {str(e)}"}


async def handle_synthesize_from_idea(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Alias for handle_assemble_project for backward compatibility.

    This function synthesizes a project from an idea by searching,
    downloading, and assembling compatible resources.
    """
    return await handle_assemble_project(arguments)


async def handle_assemble_project(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Assemble a complete project from an idea.

    Automatically:
    1. Searches GitHub, HuggingFace, Kaggle for compatible resources
    2. Downloads code, models (.safetensors), datasets, papers
    3. Creates organized folder structure
    4. Generates README, requirements.txt
    5. Creates GitHub repo
    6. Prepares for Windsurf IDE

    Args:
        idea: Project idea/description
        name: Project name (optional, auto-generated)
        output_dir: Output directory (default: G:/)
        create_github: Create GitHub repo (default: true)

    Returns:
        Project details and location
    """
    idea = arguments.get("idea", "")
    name = arguments.get("name")
    output_dir = arguments.get("output_dir", "G:/")
    create_github = arguments.get("create_github", True)

    if not idea:
        return {"error": True, "message": "Please provide a project idea"}

    try:
        from pathlib import Path

        from src.synthesis.project_assembler import AssemblerConfig, ProjectAssembler

        config = AssemblerConfig(
            base_output_dir=Path(output_dir),
            create_github_repo=create_github,
        )

        assembler = ProjectAssembler(config)
        project = await assembler.assemble(idea, name)

        return {
            "success": True,
            "project": {
                "name": project.name,
                "path": str(project.base_path),
                "github_url": project.github_repo_url,
                "ready_for_windsurf": project.ready_for_windsurf,
            },
            "resources": {
                "code_repos": len(project.code_repos),
                "models": len(project.models),
                "datasets": len(project.datasets),
                "papers": len(project.papers),
            },
            "downloaded": {
                "code": [r.name for r in project.code_repos if r.downloaded],
                "models": [m.name for m in project.models if m.downloaded],
                "datasets": [d.name for d in project.datasets if d.downloaded],
            },
            "next_steps": [
                f"Open {project.base_path} in Windsurf IDE",
                "Review assembled resources in src/, models/, data/",
                "Run: pip install -r requirements.txt",
                "Let Windsurf help integrate everything!",
            ],
        }

    except Exception as e:
        secure_logger.error(f"Project assembly error: {e}")
        return {"error": True, "message": f"Assembly error: {str(e)}"}


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
