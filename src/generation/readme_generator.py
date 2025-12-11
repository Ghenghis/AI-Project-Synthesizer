"""
AI Project Synthesizer - README Generator

Generates high-quality README documentation for projects.
Uses LLM enhancement when available.
"""

import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """Extracted project information."""
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    language: Optional[str] = None
    frameworks: List[str] = None
    dependencies: List[str] = None
    has_tests: bool = False
    has_docs: bool = False
    has_ci: bool = False
    license: Optional[str] = None

    def __post_init__(self):
        if self.frameworks is None:
            self.frameworks = []
        if self.dependencies is None:
            self.dependencies = []


class ReadmeGenerator:
    """
    Generates README.md documentation for projects.

    Features:
    - Project structure analysis
    - Dependency extraction
    - LLM-enhanced descriptions
    - Template-based generation
    - Badge generation

    Example:
        generator = ReadmeGenerator()
        readme_path = await generator.generate(Path("./my-project"))
    """

    # README template
    TEMPLATE = '''# {name}

{badges}

{description}

## ✨ Features

{features}

## 🚀 Quick Start

### Prerequisites

{prerequisites}

### Installation

```bash
{installation}
```

### Usage

```{language}
{usage}
```

## 📁 Project Structure

```
{structure}
```

## 🔧 Configuration

{configuration}

## 🧪 Testing

```bash
{testing}
```

## 📚 Documentation

{documentation}

## 🤝 Contributing

{contributing}

## 📄 License

{license}
'''

    def __init__(self, use_llm: bool = True):
        """
        Initialize the README generator.

        Args:
            use_llm: Whether to use LLM for enhanced generation
        """
        self.use_llm = use_llm
        self._llm_client = None

        if use_llm:
            try:
                from src.llm.ollama_client import OllamaClient
                self._llm_client = OllamaClient()
            except Exception as e:
                logger.warning(f"LLM not available: {e}")

    async def generate(
        self,
        project_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generate README for a project.

        Args:
            project_path: Path to project root
            output_path: Custom output path (default: project_path/README.md)

        Returns:
            Path to generated README
        """
        # Extract project information
        info = await self._analyze_project(project_path)

        # Generate sections
        content = await self._generate_content(info, project_path)

        # Write README
        readme_path = output_path or (project_path / "README.md")
        readme_path.write_text(content, encoding="utf-8")

        logger.info(f"Generated README at {readme_path}")
        return readme_path

    async def _analyze_project(self, project_path: Path) -> ProjectInfo:
        """Analyze project to extract information."""
        info = ProjectInfo(name=project_path.name)

        # Check for pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            info = self._parse_pyproject(pyproject, info)

        # Check for setup.py
        setup_py = project_path / "setup.py"
        if setup_py.exists():
            info = self._parse_setup_py(setup_py, info)

        # Check for package.json (Node.js)
        package_json = project_path / "package.json"
        if package_json.exists():
            info = self._parse_package_json(package_json, info)

        # Detect language
        if info.language is None:
            info.language = self._detect_language(project_path)

        # Detect frameworks
        info.frameworks = self._detect_frameworks(project_path)

        # Check for tests
        info.has_tests = (
            (project_path / "tests").exists() or
            (project_path / "test").exists()
        )

        # Check for docs
        info.has_docs = (project_path / "docs").exists()

        # Check for CI
        info.has_ci = (
            (project_path / ".github" / "workflows").exists() or
            (project_path / ".gitlab-ci.yml").exists()
        )

        # Check for LICENSE
        for lic_name in ["LICENSE", "LICENSE.md", "LICENSE.txt"]:
            lic_path = project_path / lic_name
            if lic_path.exists():
                info.license = self._detect_license_type(lic_path)
                break

        return info

    def _parse_pyproject(self, path: Path, info: ProjectInfo) -> ProjectInfo:
        """Parse pyproject.toml for project info."""
        try:
            import toml
            data = toml.load(path)

            project = data.get("project", {})
            info.name = project.get("name", info.name)
            info.description = project.get("description")
            info.version = project.get("version")
            info.language = "python"

            deps = project.get("dependencies", [])
            info.dependencies = [d.split("[")[0].split("<")[0].split(">")[0].split("=")[0] for d in deps]

        except Exception as e:
            logger.debug(f"Failed to parse pyproject.toml: {e}")

        return info

    def _parse_setup_py(self, path: Path, info: ProjectInfo) -> ProjectInfo:
        """Parse setup.py for project info."""
        try:
            content = path.read_text()

            # Extract name
            match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                info.name = match.group(1)

            # Extract description
            match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                info.description = match.group(1)

            info.language = "python"

        except Exception as e:
            logger.debug(f"Failed to parse setup.py: {e}")

        return info

    def _parse_package_json(self, path: Path, info: ProjectInfo) -> ProjectInfo:
        """Parse package.json for project info."""
        try:
            import json
            data = json.loads(path.read_text())

            info.name = data.get("name", info.name)
            info.description = data.get("description")
            info.version = data.get("version")
            info.language = "javascript"

            deps = list(data.get("dependencies", {}).keys())
            info.dependencies = deps

        except Exception as e:
            logger.debug(f"Failed to parse package.json: {e}")

        return info

    def _detect_language(self, project_path: Path) -> str:
        """Detect primary programming language."""
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
        }

        counts = {}
        for ext, lang in extensions.items():
            count = len(list(project_path.rglob(f"*{ext}")))
            if count > 0:
                counts[lang] = count

        if counts:
            return max(counts, key=counts.get)
        return "python"

    def _detect_frameworks(self, project_path: Path) -> List[str]:
        """Detect frameworks used in project."""
        frameworks = []

        # Check Python frameworks
        reqs_files = list(project_path.glob("requirements*.txt"))
        pyproject = project_path / "pyproject.toml"

        all_deps = ""
        for req_file in reqs_files:
            all_deps += req_file.read_text().lower()

        if pyproject.exists():
            all_deps += pyproject.read_text().lower()

        framework_patterns = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "pytorch": "PyTorch",
            "tensorflow": "TensorFlow",
            "transformers": "Transformers",
            "langchain": "LangChain",
            "streamlit": "Streamlit",
            "gradio": "Gradio",
        }

        for pattern, name in framework_patterns.items():
            if pattern in all_deps:
                frameworks.append(name)

        # Check JS frameworks
        package_json = project_path / "package.json"
        if package_json.exists():
            pkg_content = package_json.read_text().lower()
            js_frameworks = {
                "react": "React",
                "vue": "Vue.js",
                "angular": "Angular",
                "next": "Next.js",
                "express": "Express",
            }
            for pattern, name in js_frameworks.items():
                if pattern in pkg_content:
                    frameworks.append(name)

        return frameworks

    def _detect_license_type(self, path: Path) -> str:
        """Detect license type from LICENSE file."""
        try:
            content = path.read_text()[:1000].lower()

            if "mit license" in content or "permission is hereby granted" in content:
                return "MIT"
            elif "apache license" in content:
                return "Apache-2.0"
            elif "gnu general public license" in content:
                return "GPL-3.0"
            elif "bsd" in content:
                return "BSD-3-Clause"
            else:
                return "See LICENSE file"
        except Exception:
            return "See LICENSE file"

    async def _generate_content(
        self,
        info: ProjectInfo,
        project_path: Path,
    ) -> str:
        """Generate README content from project info."""
        # Generate badges
        badges = self._generate_badges(info)

        # Generate description
        description = info.description or f"A {info.language} project"
        if self.use_llm and self._llm_client:
            try:
                description = await self._enhance_description(info, project_path)
            except Exception as e:
                logger.debug(f"LLM enhancement failed: {e}")

        # Generate features
        features = self._generate_features(info)

        # Generate prerequisites
        prerequisites = self._generate_prerequisites(info)

        # Generate installation
        installation = self._generate_installation(info)

        # Generate usage
        usage = self._generate_usage(info)

        # Generate structure
        structure = self._generate_structure(project_path)

        # Generate configuration
        configuration = self._generate_configuration(info)

        # Generate testing
        testing = self._generate_testing(info)

        # Generate documentation
        documentation = self._generate_documentation_section(info)

        # Generate contributing
        contributing = self._generate_contributing(info)

        # Generate license
        license_text = self._generate_license_section(info)

        # Fill template
        content = self.TEMPLATE.format(
            name=info.name,
            badges=badges,
            description=description,
            features=features,
            prerequisites=prerequisites,
            installation=installation,
            language=info.language or "python",
            usage=usage,
            structure=structure,
            configuration=configuration,
            testing=testing,
            documentation=documentation,
            contributing=contributing,
            license=license_text,
        )

        return content

    def _generate_badges(self, info: ProjectInfo) -> str:
        """Generate badge markdown."""
        badges = []

        if info.language == "python":
            badges.append("![Python](https://img.shields.io/badge/python-3.11+-blue.svg)")
        elif info.language == "javascript":
            badges.append("![Node.js](https://img.shields.io/badge/node-18+-green.svg)")

        if info.license:
            badges.append(f"![License](https://img.shields.io/badge/license-{info.license}-yellow.svg)")

        if info.has_tests:
            badges.append("![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)")

        return " ".join(badges) if badges else ""

    def _generate_features(self, info: ProjectInfo) -> str:
        """Generate features list."""
        features = []

        if info.frameworks:
            for framework in info.frameworks:
                features.append(f"- Built with **{framework}**")

        if info.has_tests:
            features.append("- Comprehensive test suite")

        if info.has_ci:
            features.append("- CI/CD pipeline configured")

        if info.has_docs:
            features.append("- Detailed documentation")

        if not features:
            features = ["- Feature 1", "- Feature 2", "- Feature 3"]

        return "\n".join(features)

    def _generate_prerequisites(self, info: ProjectInfo) -> str:
        """Generate prerequisites section."""
        prereqs = []

        if info.language == "python":
            prereqs.append("- Python 3.11 or higher")
            prereqs.append("- pip or uv package manager")
        elif info.language == "javascript":
            prereqs.append("- Node.js 18 or higher")
            prereqs.append("- npm or pnpm")

        return "\n".join(prereqs) if prereqs else "- See requirements"

    def _generate_installation(self, info: ProjectInfo) -> str:
        """Generate installation instructions."""
        if info.language == "python":
            return '''# Clone the repository
git clone https://github.com/username/''' + info.name + '''.git
cd ''' + info.name + '''

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\\Scripts\\activate   # Windows

# Install dependencies
pip install -r requirements.txt'''

        elif info.language == "javascript":
            return '''# Clone the repository
git clone https://github.com/username/''' + info.name + '''.git
cd ''' + info.name + '''

# Install dependencies
npm install'''

        return "# See documentation for installation instructions"

    def _generate_usage(self, info: ProjectInfo) -> str:
        """Generate usage example."""
        if info.language == "python":
            return f'''from {info.name.replace("-", "_")} import main

# Example usage
result = main.run()
print(result)'''

        elif info.language == "javascript":
            return f'''import {{ main }} from '{info.name}';

// Example usage
const result = await main();
console.log(result);'''

        return "// See documentation for usage examples"

    def _generate_structure(self, project_path: Path) -> str:
        """Generate project structure tree."""
        structure_lines = [f"{project_path.name}/"]

        # Get top-level items
        items = sorted(project_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

        for i, item in enumerate(items[:15]):  # Limit to 15 items
            if item.name.startswith(".") and item.name not in [".github", ".env.example"]:
                continue

            prefix = "├── " if i < len(items) - 1 else "└── "
            if item.is_dir():
                structure_lines.append(f"{prefix}{item.name}/")
            else:
                structure_lines.append(f"{prefix}{item.name}")

        return "\n".join(structure_lines)

    def _generate_configuration(self, info: ProjectInfo) -> str:
        """Generate configuration section."""
        return '''Configuration options can be set via:
- Environment variables (see `.env.example`)
- Configuration files (see `config/` directory)
'''

    def _generate_testing(self, info: ProjectInfo) -> str:
        """Generate testing instructions."""
        if info.language == "python":
            return '''# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html'''

        elif info.language == "javascript":
            return '''# Run tests
npm test

# Run with coverage
npm run test:coverage'''

        return "# See documentation for testing instructions"

    def _generate_documentation_section(self, info: ProjectInfo) -> str:
        """Generate documentation section."""
        if info.has_docs:
            return "See the [docs/](./docs/) directory for detailed documentation."
        return "Documentation is available in the source code comments and this README."

    def _generate_contributing(self, info: ProjectInfo) -> str:
        """Generate contributing section."""
        return '''Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request'''

    def _generate_license_section(self, info: ProjectInfo) -> str:
        """Generate license section."""
        if info.license:
            return f"This project is licensed under the {info.license} License - see the [LICENSE](LICENSE) file for details."
        return "See the [LICENSE](LICENSE) file for details."

    async def _enhance_description(
        self,
        info: ProjectInfo,
        project_path: Path,
    ) -> str:
        """Use LLM to enhance project description."""
        if not self._llm_client:
            return info.description or f"A {info.language} project"

        prompt = f"""Write a brief, professional description for a software project with these details:
- Name: {info.name}
- Language: {info.language}
- Frameworks: {', '.join(info.frameworks) if info.frameworks else 'None specified'}
- Has tests: {info.has_tests}
- Has CI/CD: {info.has_ci}

Write 2-3 sentences describing what this project likely does and its key benefits.
Be specific but don't make up features that aren't implied by the project structure."""

        try:
            response = await self._llm_client.complete(prompt, max_tokens=200)
            return response.strip()
        except Exception:
            return info.description or f"A {info.language} project"
