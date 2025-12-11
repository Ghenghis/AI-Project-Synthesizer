"""
AI Project Synthesizer - Automated Project Assembler

THE ULTIMATE GOAL:
1. Find compatible projects across GitHub, HuggingFace, Kaggle
2. Download everything: code, models (.safetensors), datasets
3. Create organized folder structure on G:\
4. Generate combined requirements.txt
5. Create GitHub repo for user
6. Prepare project for Windsurf IDE to finish

This is the BRAIN that assembles complete projects automatically.
"""

import asyncio
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


@dataclass
class ProjectResource:
    """A resource to be included in the project."""
    name: str
    source: str  # github, huggingface, kaggle, arxiv
    url: str
    resource_type: str  # code, model, dataset, paper
    description: str = ""
    download_path: Optional[Path] = None
    downloaded: bool = False
    size_mb: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssembledProject:
    """A fully assembled project ready for development."""
    name: str
    slug: str  # URL-safe name
    description: str
    base_path: Path

    # Resources
    code_repos: List[ProjectResource] = field(default_factory=list)
    models: List[ProjectResource] = field(default_factory=list)
    datasets: List[ProjectResource] = field(default_factory=list)
    papers: List[ProjectResource] = field(default_factory=list)

    # Generated files
    readme_path: Optional[Path] = None
    requirements_path: Optional[Path] = None

    # GitHub
    github_repo_url: Optional[str] = None
    github_repo_created: bool = False

    # Status
    created_at: datetime = field(default_factory=datetime.now)
    ready_for_windsurf: bool = False


@dataclass
class AssemblerConfig:
    """Configuration for project assembly."""
    # Output location
    base_output_dir: Path = Path("G:/")

    # What to download
    download_code: bool = True
    download_models: bool = True
    download_datasets: bool = True
    download_papers: bool = True

    # Limits
    max_model_size_gb: float = 10.0
    max_dataset_size_gb: float = 5.0
    max_repos: int = 5

    # GitHub
    create_github_repo: bool = True
    github_username: str = ""
    github_make_private: bool = False

    # Organization
    create_subfolders: bool = True
    folder_structure: str = "standard"  # standard, flat, by-source


class ProjectAssembler:
    """
    Automated project assembler.

    Takes a project idea and:
    1. Searches for compatible resources
    2. Downloads everything
    3. Organizes into folder structure
    4. Creates GitHub repo
    5. Prepares for Windsurf

    Usage:
        assembler = ProjectAssembler()
        project = await assembler.assemble(
            "RAG chatbot with local LLM",
            name="my-rag-chatbot"
        )
        print(f"Project ready at: {project.base_path}")
        print(f"GitHub: {project.github_repo_url}")
    """

    def __init__(self, config: Optional[AssemblerConfig] = None):
        """Initialize assembler."""
        self.config = config or AssemblerConfig()
        self._search = None
        self._github_token = None

        self._init_credentials()

    def _init_credentials(self):
        """Load credentials."""
        settings = get_settings()
        self._github_token = settings.platforms.github_token.get_secret_value()
        self.config.github_username = settings.platforms.github_token.get_secret_value()[:20] if self._github_token else ""

    async def assemble(
        self,
        idea: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AssembledProject:
        """
        Assemble a complete project from an idea.

        Args:
            idea: Project idea/description
            name: Project name (auto-generated if not provided)
            description: Project description

        Returns:
            AssembledProject ready for development
        """
        secure_logger.info(f"Starting project assembly for: {idea}")

        # Generate project name if not provided
        if not name:
            name = self._generate_project_name(idea)

        slug = self._slugify(name)

        # Create project structure
        project = AssembledProject(
            name=name,
            slug=slug,
            description=description or idea,
            base_path=self.config.base_output_dir / slug,
        )

        # Create folder structure
        await self._create_folder_structure(project)

        # Search for resources
        await self._search_resources(project, idea)

        # Download everything
        await self._download_all(project)

        # Generate project files
        await self._generate_project_files(project)

        # Create GitHub repo
        if self.config.create_github_repo:
            await self._create_github_repo(project)

        # Mark as ready
        project.ready_for_windsurf = True

        # Save project manifest
        await self._save_manifest(project)

        secure_logger.info(f"Project assembled at: {project.base_path}")

        return project

    def _generate_project_name(self, idea: str) -> str:
        """Generate a project name from idea."""
        # Extract key words
        words = idea.lower().split()

        # Remove common words
        stop_words = {"a", "an", "the", "with", "for", "to", "and", "or", "using", "build", "create", "make"}
        key_words = [w for w in words if w not in stop_words and len(w) > 2]

        # Take first 3-4 words
        name_words = key_words[:4]

        return "-".join(name_words) if name_words else f"project-{datetime.now().strftime('%Y%m%d')}"

    def _slugify(self, name: str) -> str:
        """Convert name to URL-safe slug."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug

    async def _create_folder_structure(self, project: AssembledProject):
        """Create project folder structure."""
        base = project.base_path

        # Create main folder
        base.mkdir(parents=True, exist_ok=True)

        if self.config.create_subfolders:
            # Standard structure
            folders = [
                "src",           # Main source code
                "models",        # Downloaded models (.safetensors, .bin, etc.)
                "data",          # Datasets
                "data/raw",      # Raw downloaded data
                "data/processed",# Processed data
                "docs",          # Documentation
                "docs/papers",   # Research papers
                "notebooks",     # Jupyter notebooks
                "scripts",       # Utility scripts
                "tests",         # Test files
                "config",        # Configuration files
                ".windsurf",     # Windsurf IDE config
            ]

            for folder in folders:
                (base / folder).mkdir(parents=True, exist_ok=True)

        secure_logger.info(f"Created folder structure at {base}")

    async def _search_resources(self, project: AssembledProject, idea: str):
        """Search for resources across all platforms."""
        if self._search is None:
            from src.discovery.unified_search import create_unified_search
            self._search = create_unified_search()

        # Search GitHub for code
        secure_logger.info("Searching GitHub for code repositories...")
        github_results = await self._search.search(
            query=idea,
            platforms=["github"],
            max_results=self.config.max_repos,
        )

        for repo in github_results.repositories:
            project.code_repos.append(ProjectResource(
                name=repo.name,
                source="github",
                url=repo.url,
                resource_type="code",
                description=repo.description or "",
                metadata={
                    "stars": repo.stars,
                    "language": repo.language,
                    "full_name": repo.full_name,
                }
            ))

        # Search HuggingFace for models
        secure_logger.info("Searching HuggingFace for models...")
        hf_results = await self._search.search(
            query=idea,
            platforms=["huggingface"],
            max_results=5,
        )

        for repo in hf_results.repositories:
            project.models.append(ProjectResource(
                name=repo.name,
                source="huggingface",
                url=repo.url,
                resource_type="model",
                description=repo.description or "",
                metadata={
                    "likes": repo.stars,
                    "full_name": repo.full_name,
                }
            ))

        # Search Kaggle for datasets
        secure_logger.info("Searching Kaggle for datasets...")
        kaggle_results = await self._search.search(
            query=idea,
            platforms=["kaggle"],
            max_results=3,
        )

        for repo in kaggle_results.repositories:
            project.datasets.append(ProjectResource(
                name=repo.name,
                source="kaggle",
                url=repo.url,
                resource_type="dataset",
                description=repo.description or "",
                metadata={
                    "votes": repo.stars,
                    "full_name": repo.full_name,
                }
            ))

        # Search arXiv for papers
        secure_logger.info("Searching arXiv for papers...")
        await self._search_arxiv(project, idea)

        secure_logger.info(
            f"Found: {len(project.code_repos)} repos, "
            f"{len(project.models)} models, "
            f"{len(project.datasets)} datasets, "
            f"{len(project.papers)} papers"
        )

    async def _search_arxiv(self, project: AssembledProject, query: str):
        """Search arXiv for research papers."""
        try:
            import aiohttp

            search_query = query.replace(" ", "+")
            url = f"http://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results=5"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()

                        # Parse entries
                        import re
                        entries = re.findall(r'<entry>(.*?)</entry>', text, re.DOTALL)

                        for entry in entries[:5]:
                            title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                            link_match = re.search(r'<id>(.*?)</id>', entry)
                            pdf_match = re.search(r'href="([^"]+\.pdf)"', entry)

                            if title_match:
                                project.papers.append(ProjectResource(
                                    name=title_match.group(1).strip().replace('\n', ' ')[:100],
                                    source="arxiv",
                                    url=pdf_match.group(1) if pdf_match else link_match.group(1) if link_match else "",
                                    resource_type="paper",
                                ))
        except Exception as e:
            secure_logger.warning(f"arXiv search error: {e}")

    async def _download_all(self, project: AssembledProject):
        """Download all resources."""
        # Download code repos
        if self.config.download_code:
            for repo in project.code_repos:
                await self._download_github_repo(project, repo)

        # Download models
        if self.config.download_models:
            for model in project.models:
                await self._download_huggingface_model(project, model)

        # Download datasets
        if self.config.download_datasets:
            for dataset in project.datasets:
                await self._download_kaggle_dataset(project, dataset)

        # Download papers
        if self.config.download_papers:
            for paper in project.papers:
                await self._download_paper(project, paper)

    async def _download_github_repo(self, project: AssembledProject, resource: ProjectResource):
        """Clone a GitHub repository."""
        try:
            dest = project.base_path / "src" / resource.name

            secure_logger.info(f"Cloning {resource.metadata.get('full_name', resource.name)}...")

            # Clone with git
            process = await asyncio.create_subprocess_exec(
                "git", "clone", "--depth", "1", resource.url, str(dest),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()

            if dest.exists():
                resource.download_path = dest
                resource.downloaded = True
                secure_logger.info(f"Cloned to {dest}")

        except Exception as e:
            secure_logger.error(f"Failed to clone {resource.name}: {e}")

    async def _download_huggingface_model(self, project: AssembledProject, resource: ProjectResource):
        """Download a HuggingFace model."""
        try:
            dest = project.base_path / "models" / resource.name
            dest.mkdir(parents=True, exist_ok=True)

            secure_logger.info(f"Downloading model {resource.metadata.get('full_name', resource.name)}...")

            # Use huggingface_hub to download
            from huggingface_hub import snapshot_download

            model_id = resource.metadata.get('full_name', resource.name)

            # Download (this handles .safetensors, config.json, etc.)
            downloaded_path = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: snapshot_download(
                    repo_id=model_id,
                    local_dir=str(dest),
                    local_dir_use_symlinks=False,
                )
            )

            resource.download_path = Path(downloaded_path)
            resource.downloaded = True
            secure_logger.info(f"Downloaded model to {dest}")

        except Exception as e:
            secure_logger.warning(f"Failed to download model {resource.name}: {e}")

    async def _download_kaggle_dataset(self, project: AssembledProject, resource: ProjectResource):
        """Download a Kaggle dataset."""
        try:
            dest = project.base_path / "data" / "raw" / resource.name
            dest.mkdir(parents=True, exist_ok=True)

            secure_logger.info(f"Downloading dataset {resource.metadata.get('full_name', resource.name)}...")

            # Use kaggle API
            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            dataset_ref = resource.metadata.get('full_name', resource.name)

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: api.dataset_download_files(
                    dataset_ref,
                    path=str(dest),
                    unzip=True,
                )
            )

            resource.download_path = dest
            resource.downloaded = True
            secure_logger.info(f"Downloaded dataset to {dest}")

        except Exception as e:
            secure_logger.warning(f"Failed to download dataset {resource.name}: {e}")

    async def _download_paper(self, project: AssembledProject, resource: ProjectResource):
        """Download a research paper PDF."""
        try:
            if not resource.url or not resource.url.endswith('.pdf'):
                return

            dest = project.base_path / "docs" / "papers"
            dest.mkdir(parents=True, exist_ok=True)

            filename = self._slugify(resource.name[:50]) + ".pdf"
            filepath = dest / filename

            secure_logger.info(f"Downloading paper: {resource.name[:50]}...")

            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(resource.url) as response:
                    if response.status == 200:
                        content = await response.read()
                        filepath.write_bytes(content)
                        resource.download_path = filepath
                        resource.downloaded = True
                        secure_logger.info(f"Downloaded paper to {filepath}")

        except Exception as e:
            secure_logger.warning(f"Failed to download paper: {e}")

    async def _generate_project_files(self, project: AssembledProject):
        """Generate project files (README, requirements, etc.)."""
        # Generate README
        readme_content = self._generate_readme(project)
        readme_path = project.base_path / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        project.readme_path = readme_path

        # Generate requirements.txt
        requirements = await self._collect_requirements(project)
        req_path = project.base_path / "requirements.txt"
        req_path.write_text("\n".join(requirements), encoding="utf-8")
        project.requirements_path = req_path

        # Generate .gitignore
        gitignore = self._generate_gitignore()
        (project.base_path / ".gitignore").write_text(gitignore, encoding="utf-8")

        # Generate Windsurf config
        windsurf_config = self._generate_windsurf_config(project)
        (project.base_path / ".windsurf" / "config.json").write_text(
            json.dumps(windsurf_config, indent=2), encoding="utf-8"
        )

        secure_logger.info("Generated project files")

    def _generate_readme(self, project: AssembledProject) -> str:
        """Generate README.md content."""
        lines = [
            f"# {project.name}",
            "",
            f"> {project.description}",
            "",
            f"*Assembled by AI Project Synthesizer on {project.created_at.strftime('%Y-%m-%d')}*",
            "",
            "## Project Structure",
            "",
            "```",
            f"{project.slug}/",
            "├── src/           # Source code from GitHub repos",
            "├── models/        # AI models (.safetensors, etc.)",
            "├── data/          # Datasets",
            "│   ├── raw/       # Raw downloaded data",
            "│   └── processed/ # Processed data",
            "├── docs/          # Documentation",
            "│   └── papers/    # Research papers",
            "├── notebooks/     # Jupyter notebooks",
            "├── scripts/       # Utility scripts",
            "├── tests/         # Tests",
            "└── config/        # Configuration",
            "```",
            "",
        ]

        # Code repos
        if project.code_repos:
            lines.extend([
                "## Source Code",
                "",
            ])
            for repo in project.code_repos:
                status = "✅" if repo.downloaded else "⏳"
                lines.append(f"- {status} **{repo.name}** - {repo.description[:100]}")
                lines.append(f"  - Source: {repo.url}")
                if repo.metadata.get("stars"):
                    lines.append(f"  - ⭐ {repo.metadata['stars']} stars")
            lines.append("")

        # Models
        if project.models:
            lines.extend([
                "## AI Models",
                "",
            ])
            for model in project.models:
                status = "✅" if model.downloaded else "⏳"
                lines.append(f"- {status} **{model.name}**")
                lines.append(f"  - Source: {model.url}")
            lines.append("")

        # Datasets
        if project.datasets:
            lines.extend([
                "## Datasets",
                "",
            ])
            for ds in project.datasets:
                status = "✅" if ds.downloaded else "⏳"
                lines.append(f"- {status} **{ds.name}** - {ds.description[:100]}")
                lines.append(f"  - Source: {ds.url}")
            lines.append("")

        # Papers
        if project.papers:
            lines.extend([
                "## Research Papers",
                "",
            ])
            for paper in project.papers:
                status = "✅" if paper.downloaded else "📄"
                lines.append(f"- {status} {paper.name}")
            lines.append("")

        # Getting started
        lines.extend([
            "## Getting Started",
            "",
            "1. Install dependencies:",
            "   ```bash",
            "   pip install -r requirements.txt",
            "   ```",
            "",
            "2. Open in Windsurf IDE for AI-assisted development",
            "",
            "3. Review the source code in `src/` and adapt for your needs",
            "",
            "## Next Steps",
            "",
            "This project has been assembled from multiple sources.",
            "Use Windsurf IDE to:",
            "- Integrate the different components",
            "- Customize for your specific use case",
            "- Add your own code and features",
            "",
        ])

        return "\n".join(lines)

    async def _collect_requirements(self, project: AssembledProject) -> List[str]:
        """Collect requirements from all repos."""
        requirements = set()

        # Common requirements
        requirements.update([
            "# Core dependencies",
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "datasets>=2.0.0",
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "",
            "# Utilities",
            "tqdm",
            "python-dotenv",
            "pyyaml",
        ])

        # Scan downloaded repos for requirements
        for repo in project.code_repos:
            if repo.download_path and repo.download_path.exists():
                req_file = repo.download_path / "requirements.txt"
                if req_file.exists():
                    requirements.add(f"\n# From {repo.name}")
                    for line in req_file.read_text().splitlines():
                        if line.strip() and not line.startswith("#"):
                            requirements.add(line.strip())

        return sorted(requirements)

    def _generate_gitignore(self) -> str:
        """Generate .gitignore content."""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Data
data/raw/*
!data/raw/.gitkeep
*.csv
*.parquet
*.json.gz

# Models (large files)
models/*
!models/.gitkeep
*.safetensors
*.bin
*.pt
*.pth
*.ckpt

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets
.env
*.key
"""

    def _generate_windsurf_config(self, project: AssembledProject) -> Dict[str, Any]:
        """Generate Windsurf IDE configuration."""
        return {
            "project": {
                "name": project.name,
                "description": project.description,
                "assembled_by": "AI Project Synthesizer",
                "created_at": project.created_at.isoformat(),
            },
            "sources": {
                "code_repos": [r.metadata.get("full_name", r.name) for r in project.code_repos],
                "models": [m.metadata.get("full_name", m.name) for m in project.models],
                "datasets": [d.metadata.get("full_name", d.name) for d in project.datasets],
            },
            "tasks": [
                "Review and integrate source code from src/",
                "Configure model loading from models/",
                "Set up data pipeline from data/",
                "Write main application logic",
                "Add tests",
                "Update documentation",
            ],
            "ai_context": {
                "project_type": "synthesized",
                "primary_language": "python",
                "frameworks": ["pytorch", "transformers"],
            }
        }

    async def _create_github_repo(self, project: AssembledProject):
        """Create a GitHub repository for the project."""
        if not self._github_token:
            secure_logger.warning("No GitHub token - skipping repo creation")
            return

        try:
            import aiohttp

            # Create repo via GitHub API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.github.com/user/repos",
                    headers={
                        "Authorization": f"token {self._github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={
                        "name": project.slug,
                        "description": project.description[:200],
                        "private": self.config.github_make_private,
                        "auto_init": False,
                    }
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        project.github_repo_url = data["html_url"]
                        project.github_repo_created = True

                        # Initialize git and push
                        await self._init_and_push_git(project, data["clone_url"])

                        secure_logger.info(f"Created GitHub repo: {project.github_repo_url}")
                    else:
                        error = await response.text()
                        secure_logger.warning(f"Failed to create GitHub repo: {error}")

        except Exception as e:
            secure_logger.error(f"GitHub repo creation error: {e}")

    async def _init_and_push_git(self, project: AssembledProject, clone_url: str):
        """Initialize git and push to GitHub."""
        cwd = project.base_path

        commands = [
            ["git", "init"],
            ["git", "add", "."],
            ["git", "commit", "-m", "Initial commit - assembled by AI Project Synthesizer"],
            ["git", "branch", "-M", "main"],
            ["git", "remote", "add", "origin", clone_url],
            ["git", "push", "-u", "origin", "main"],
        ]

        for cmd in commands:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()

    async def _save_manifest(self, project: AssembledProject):
        """Save project manifest for future reference."""
        manifest = {
            "name": project.name,
            "slug": project.slug,
            "description": project.description,
            "base_path": str(project.base_path),
            "created_at": project.created_at.isoformat(),
            "github_repo_url": project.github_repo_url,
            "ready_for_windsurf": project.ready_for_windsurf,
            "resources": {
                "code_repos": [
                    {"name": r.name, "url": r.url, "downloaded": r.downloaded}
                    for r in project.code_repos
                ],
                "models": [
                    {"name": m.name, "url": m.url, "downloaded": m.downloaded}
                    for m in project.models
                ],
                "datasets": [
                    {"name": d.name, "url": d.url, "downloaded": d.downloaded}
                    for d in project.datasets
                ],
                "papers": [
                    {"name": p.name, "url": p.url, "downloaded": p.downloaded}
                    for p in project.papers
                ],
            }
        }

        manifest_path = project.base_path / "project-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


async def assemble_project(
    idea: str,
    name: Optional[str] = None,
    output_dir: Path = Path("G:/"),
    create_github: bool = True,
) -> AssembledProject:
    """
    Quick function to assemble a project.

    Args:
        idea: Project idea/description
        name: Project name
        output_dir: Where to create project
        create_github: Create GitHub repo

    Returns:
        AssembledProject ready for Windsurf

    Example:
        project = await assemble_project(
            "RAG chatbot with local LLM and vector database",
            name="my-rag-bot"
        )
    """
    config = AssemblerConfig(
        base_output_dir=output_dir,
        create_github_repo=create_github,
    )

    assembler = ProjectAssembler(config)
    return await assembler.assemble(idea, name)
