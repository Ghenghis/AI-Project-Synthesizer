"""
AI Project Synthesizer - Scaffolder

Project template scaffolding using standard project structures.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScaffoldResult:
    """Result of scaffolding operation."""
    success: bool
    files_created: int = 0
    warnings: list[str] = field(default_factory=list)




class Scaffolder:
    """
    Project scaffolder for creating standard project structures.

    Templates:
    - python-default: Standard Python package
    - python-fastapi: FastAPI web application
    - python-ml: Machine learning project
    - fullstack: Frontend + Backend

    Usage:
        scaffolder = Scaffolder()
        result = await scaffolder.scaffold(
            output_path=Path("./my-project"),
            template="python-default",
            project_name="my-project"
        )
    """

    TEMPLATES = {
        "python-default": {
            "dirs": ["src", "tests", "docs", "scripts"],
            "files": {
                "src/__init__.py": "",
                "tests/__init__.py": "",
                "tests/conftest.py": '"""Pytest configuration."""\n\nimport pytest\n',
            }
        },
        "python-fastapi": {
            "dirs": ["src", "src/api", "src/models", "src/services", "tests", "docs"],
            "files": {
                "src/__init__.py": "",
                "src/api/__init__.py": "",
                "src/models/__init__.py": "",
                "src/services/__init__.py": "",
                "src/main.py": '''"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{project_name}",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy"}}
''',
            }
        },
        "python-ml": {
            "dirs": ["src", "data", "models", "notebooks", "tests", "docs"],
            "files": {
                "src/__init__.py": "",
                "data/.gitkeep": "",
                "models/.gitkeep": "",
                "notebooks/.gitkeep": "",
            }
        },
    }

    async def scaffold(
        self,
        output_path: Path,
        template: str,
        project_name: str,
        python_version: str = "3.11",
        include_docker: bool = True,
        include_tests: bool = True,
        include_ci: bool = True,
    ) -> ScaffoldResult:
        """
        Apply project template scaffolding.

        Args:
            output_path: Project output directory
            template: Template name
            project_name: Project name
            python_version: Python version
            include_docker: Include Docker files
            include_tests: Include test scaffolding
            include_ci: Include CI/CD configuration

        Returns:
            ScaffoldResult with scaffolding details
        """
        files_created = 0
        warnings = []

        # Get template
        template_config = self.TEMPLATES.get(template, self.TEMPLATES["python-default"])

        # Create directories
        for dir_name in template_config["dirs"]:
            dir_path = output_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create template files
        for file_path, content in template_config["files"].items():
            full_path = output_path / file_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                # Replace placeholders
                content = content.format(project_name=project_name)
                full_path.write_text(content)
                files_created += 1

        # Generate common files
        files_created += self._generate_gitignore(output_path)
        files_created += self._generate_readme(output_path, project_name)
        files_created += self._generate_pyproject(output_path, project_name, python_version)

        if include_docker:
            files_created += self._generate_docker(output_path, project_name)

        if include_ci:
            files_created += self._generate_ci(output_path)

        return ScaffoldResult(
            success=True,
            files_created=files_created,
            warnings=warnings,
        )

    def _generate_gitignore(self, path: Path) -> int:
        """Generate .gitignore file."""
        gitignore = path / ".gitignore"
        if gitignore.exists():
            return 0

        content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.tox/
.nox/
.coverage
.coverage.*
htmlcov/
.pytest_cache/
.mypy_cache/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Project specific
.cache/
temp/
output/
"""
        gitignore.write_text(content)
        return 1

    def _generate_readme(self, path: Path, project_name: str) -> int:
        """Generate README.md if not exists."""
        readme = path / "README.md"
        if readme.exists():
            return 0

        content = f"""# {project_name}

> Generated by AI Project Synthesizer

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main
```

## Project Structure

```
{project_name}/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
└── requirements.txt
```

## License

MIT License

---

*Generated on {datetime.now().strftime("%Y-%m-%d")}*
"""
        readme.write_text(content)
        return 1

    def _generate_pyproject(
        self,
        path: Path,
        project_name: str,
        python_version: str
    ) -> int:
        """Generate pyproject.toml if not exists."""
        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            return 0

        content = f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Generated project"
requires-python = ">={python_version}"
readme = "README.md"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 88
target-version = "py{python_version.replace(".", "")}"

[tool.mypy]
python_version = "{python_version}"
warn_return_any = true
'''
        pyproject.write_text(content)
        return 1

    def _generate_docker(self, path: Path, project_name: str) -> int:
        """Generate Docker configuration."""
        files_created = 0

        # Dockerfile
        dockerfile = path / "Dockerfile"
        if not dockerfile.exists():
            content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["python", "-m", "src.main"]
'''
            dockerfile.write_text(content)
            files_created += 1

        # docker-compose.yml
        compose = path / "docker-compose.yml"
        if not compose.exists():
            content = f'''version: "3.8"

services:
  app:
    build: .
    container_name: {project_name}
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - PYTHONUNBUFFERED=1
'''
            compose.write_text(content)
            files_created += 1

        return files_created

    def _generate_ci(self, path: Path) -> int:
        """Generate CI configuration."""
        files_created = 0

        # GitHub Actions
        workflows_dir = path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        ci_file = workflows_dir / "ci.yml"
        if not ci_file.exists():
            content = '''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio ruff mypy

      - name: Lint
        run: ruff check .

      - name: Type check
        run: mypy src/ --ignore-missing-imports

      - name: Test
        run: pytest tests/ -v
'''
            ci_file.write_text(content)
            files_created += 1

        return files_created
