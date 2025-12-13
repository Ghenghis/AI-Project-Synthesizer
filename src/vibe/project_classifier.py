"""
Project Classifier for VIBE MCP

Automatically detects project patterns and characteristics:
- Project type classification
- Technology stack detection
- Architecture pattern recognition
- Complexity assessment
- Best practice recommendations

Helps Vibe Coding make informed decisions based on project context.
"""

import builtins
import contextlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.llm.litellm_router import LiteLLMRouter
from src.memory.mem0_integration import MemorySystem


class ProjectType(Enum):
    """Common project types."""
    WEB_API = "web_api"
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"
    MICROSERVICE = "microservice"
    MONOLITH = "monolith"
    DESKTOP_APP = "desktop_app"
    GAME = "game"
    IOT = "iot"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Project complexity levels."""
    SIMPLE = "simple"  # < 1000 lines, single module
    MODERATE = "moderate"  # < 5000 lines, few modules
    COMPLEX = "complex"  # < 20000 lines, many modules
    ENTERPRISE = "enterprise"  # > 20000 lines, complex architecture


class ArchitecturePattern(Enum):
    """Common architecture patterns."""
    MVC = "mvc"
    MVVM = "mvvm"
    CLEAN_ARCHITECTURE = "clean_architecture"
    HEXAGONAL = "hexagonal"
    MICROSERVICES = "microservices"
    LAYERED = "layered"
    EVENT_DRIVEN = "event_driven"
    SERVERLESS = "serverless"
    MONOLITH = "monolith"
    PLUGIN = "plugin"
    UNKNOWN = "unknown"


@dataclass
class TechnologyStack:
    """Detected technology stack."""
    languages: list[str]
    frameworks: list[str]
    databases: list[str]
    testing: list[str]
    deployment: list[str]
    tools: list[str]


@dataclass
class ProjectCharacteristics:
    """Characteristics of the project."""
    type: ProjectType
    complexity: ComplexityLevel
    architecture: ArchitecturePattern
    stack: TechnologyStack
    patterns: list[str]
    conventions: list[str]
    size_metrics: dict[str, int]
    quality_indicators: dict[str, Any]


class ProjectClassifier:
    """
    Automatically classifies projects and detects patterns.

    Features:
    - Multi-language project detection
    - Architecture pattern recognition
    - Technology stack identification
    - Complexity assessment
    - Best practice recommendations
    """

    def __init__(self):
        self.config = get_settings()
        self.llm_router = LiteLLMRouter()
        self.memory = MemorySystem()

        # Detection patterns
        self.framework_patterns = {
            "python": {
                "django": ["django", "wsgi.py", "settings.py", "urls.py"],
                "flask": ["flask", "@app.route", "Flask(__name__)"],
                "fastapi": ["fastapi", "@app.", "FastAPI()"],
                "streamlit": ["streamlit", "st.", "streamlit run"],
                "pytest": ["pytest", "@pytest", "conftest.py"],
                "pandas": ["import pandas", "pd.", "DataFrame"],
                "numpy": ["import numpy", "np.", "array"],
                "scikit": ["sklearn", "from sklearn"],
                "tensorflow": ["tensorflow", "tf.", "keras"],
                "pytorch": ["torch", "nn.Module", "import torch"],
            },
            "javascript": {
                "react": ["react", "import React", "useState", "useEffect"],
                "vue": ["vue", "Vue.", "createApp"],
                "angular": ["angular", "@Component", "@NgModule"],
                "express": ["express", "app.", "require('express')"],
                "next": ["next/", "getStaticProps", "Link"],
                "jest": ["jest", "describe(", "it(", "expect("],
            },
            "typescript": {
                "nest": ["@nestjs", "Controller", "Injectable"],
                "angular": ["angular", "@Component", "NgModule"],
                "react": ["react", "useState", "useEffect"],
            },
            "java": {
                "spring": ["spring", "@SpringBootApplication", "@RestController"],
                "maven": ["pom.xml", "<groupId>", "<artifactId>"],
                "gradle": ["build.gradle", "implementation", "dependencies"],
            },
            "go": {
                "gin": ["gin.", "router.", "Context)"],
                "echo": ["echo.", "Echo", "Context)"],
                "gorm": ["gorm.", "db.", "Model struct"],
            },
            "rust": {
                "actix": ["actix_web", "HttpServer", "App"],
                "rocket": ["rocket", "#[get(", "routes!"],
                "tokio": ["tokio", "async", "await"],
            }
        }

        self.database_patterns = {
            "postgresql": ["postgresql", "psycopg2", "pg"],
            "mysql": ["mysql", "pymysql", "mysql2"],
            "mongodb": ["mongodb", "pymongo", "mongoose"],
            "sqlite": ["sqlite", "sqlite3", ".db"],
            "redis": ["redis", "Redis("],
            "elasticsearch": ["elasticsearch", "Elasticsearch("],
        }

        self.deployment_patterns = {
            "docker": ["Dockerfile", "docker-compose", "docker build"],
            "kubernetes": ["k8s", "kubectl", "deployment.yaml"],
            "terraform": ["terraform", ".tf", "resource "],
            "ansible": ["ansible", "playbook", "inventory"],
            "ci_cd": [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"],
        }

    async def classify_project(self, project_path: str = ".") -> ProjectCharacteristics:
        """
        Classify the project at the given path.

        Args:
            project_path: Path to the project directory

        Returns:
            ProjectCharacteristics with all detected information
        """
        project_path = Path(project_path).resolve()

        # Gather project information
        files = self._get_project_files(project_path)
        structure = self._analyze_structure(files)
        stack = self._detect_technology_stack(files)
        patterns = self._detect_patterns(files, stack)

        # Classify project
        project_type = await self._classify_project_type(files, stack, structure)
        complexity = self._assess_complexity(structure, files)
        architecture = self._detect_architecture(files, patterns, stack)

        # Analyze conventions
        conventions = self._detect_conventions(files, stack)

        # Quality indicators
        quality = self._assess_quality_indicators(files, structure)

        # Create characteristics
        characteristics = ProjectCharacteristics(
            type=project_type,
            complexity=complexity,
            architecture=architecture,
            stack=stack,
            patterns=patterns,
            conventions=conventions,
            size_metrics=structure,
            quality_indicators=quality
        )

        # Save classification for learning
        await self._save_classification(characteristics, str(project_path))

        return characteristics

    def _get_project_files(self, path: Path) -> list[Path]:
        """Get all relevant project files."""
        files = []
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "target", "build"}

        for file_path in path.rglob("*"):
            if file_path.is_file() and not any(skip in str(file_path) for skip in skip_dirs):
                if file_path.suffix in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
                                      ".json", ".yaml", ".yml", ".toml", ".xml", ".md"]:
                    files.append(file_path)

        return files

    def _analyze_structure(self, files: list[Path]) -> dict[str, int]:
        """Analyze project structure and size."""
        structure = {
            "total_files": len(files),
            "total_lines": 0,
            "directories": len({f.parent for f in files}),
            "languages": {},
            "test_files": 0,
            "config_files": 0,
            "doc_files": 0
        }

        for file_path in files:
            # Count lines
            try:
                with open(file_path, encoding='utf-8') as f:
                    lines = len(f.readlines())
                    structure["total_lines"] += lines
            except Exception:
                pass

            # Count languages
            ext = file_path.suffix
            if ext not in structure["languages"]:
                structure["languages"][ext] = 0
            structure["languages"][ext] += 1

            # Count special files
            if "test" in file_path.name.lower() or "spec" in file_path.name.lower():
                structure["test_files"] += 1
            elif ext in [".json", ".yaml", ".yml", ".toml", ".xml"]:
                structure["config_files"] += 1
            elif ext in [".md", ".rst", ".txt"]:
                structure["doc_files"] += 1

        return structure

    def _detect_technology_stack(self, files: list[Path]) -> TechnologyStack:
        """Detect the technology stack."""
        stack = TechnologyStack(
            languages=[],
            frameworks=[],
            databases=[],
            testing=[],
            deployment=[],
            tools=[]
        )

        # Read file contents for analysis
        file_contents = {}
        for file_path in files[:50]:  # Limit for performance
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read().lower()
                    file_contents[str(file_path)] = content
            except Exception:
                pass

        # Detect languages
        for file_path in files:
            ext = file_path.suffix
            lang_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "javascript",
                ".tsx": "typescript",
                ".java": "java",
                ".go": "go",
                ".rs": "rust",
                ".cpp": "c++",
                ".c": "c",
                ".cs": "c#",
                ".php": "php",
                ".rb": "ruby"
            }
            if ext in lang_map and lang_map[ext] not in stack.languages:
                stack.languages.append(lang_map[ext])

        # Detect frameworks
        for lang, frameworks in self.framework_patterns.items():
            if lang in stack.languages:
                for framework, patterns in frameworks.items():
                    for content in file_contents.values():
                        if any(pattern in content for pattern in patterns):
                            if framework not in stack.frameworks:
                                stack.frameworks.append(framework)
                            break

        # Detect databases
        for content in file_contents.values():
            for db, patterns in self.database_patterns.items():
                if any(pattern in content for pattern in patterns):
                    if db not in stack.databases:
                        stack.databases.append(db)

        # Detect testing frameworks
        testing_patterns = {
            "pytest": ["pytest", "@pytest"],
            "jest": ["jest", "describe(", "it("],
            "mocha": ["mocha", "describe(", "it("],
            "junit": ["@Test", "assertEquals", "JUnit"],
            "go test": ["go test", "testing.T"],
        }

        for test, patterns in testing_patterns.items():
            for content in file_contents.values():
                if any(pattern in content for pattern in patterns):
                    if test not in stack.testing:
                        stack.testing.append(test)

        # Detect deployment tools
        for file_path in files:
            file_name = file_path.name.lower()
            content = file_contents.get(str(file_path), "")

            for tool, patterns in self.deployment_patterns.items():
                if any(pattern in file_name or pattern in content for pattern in patterns):
                    if tool not in stack.deployment:
                        stack.deployment.append(tool)

        # Detect other tools
        tool_patterns = {
            "webpack": ["webpack", "webpack.config"],
            "babel": ["babel", "@babel"],
            "eslint": ["eslint", ".eslintrc"],
            "prettier": ["prettier", ".prettierrc"],
            "black": ["black", "pyproject.toml"],
            "mypy": ["mypy", "mypy.ini"],
            "poetry": ["poetry", "[tool.poetry]"],
            "npm": ["package.json", "npm"],
            "pip": ["requirements.txt", "pip"],
            "maven": ["pom.xml", "maven"],
            "gradle": ["build.gradle", "gradle"],
        }

        for content in file_contents.values():
            for tool, patterns in tool_patterns.items():
                if any(pattern in content for pattern in patterns):
                    if tool not in stack.tools:
                        stack.tools.append(tool)

        return stack

    def _detect_patterns(self, files: list[Path], stack: TechnologyStack) -> list[str]:
        """Detect design patterns in the code."""
        patterns = []

        # Read some files for pattern detection
        file_contents = {}
        for file_path in files[:20]:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                    file_contents[str(file_path)] = content
            except Exception:
                pass

        # Common patterns
        pattern_indicators = {
            "singleton": ["instance = None", "__new__", "getInstance"],
            "factory": ["create_", "Factory", "build("],
            "observer": ["observer", "notify(", "subscribe("],
            "decorator": ["@", "decorator", "wrapper"],
            "repository": ["Repository", "save(", "find(", "delete("],
            "service": ["Service", "business logic", "process"],
            "controller": ["Controller", "request", "response"],
            "model": ["Model", "class.*Model", "schema"],
            "dto": ["DTO", "DataTransferObject", "request_dto"],
            "api": ["API", "endpoint", "route", "/api/"],
            "config": ["Config", "configuration", "settings"],
        }

        for pattern, indicators in pattern_indicators.items():
            for content in file_contents.values():
                if any(indicator in content for indicator in indicators):
                    patterns.append(pattern)
                    break

        return patterns

    async def _classify_project_type(self, files: list[Path],
                                   stack: TechnologyStack,
                                   structure: dict[str, int]) -> ProjectType:
        """Classify the project type."""
        # Check for specific indicators
        file_names = [f.name.lower() for f in files]
        file_paths = [str(f).lower() for f in files]

        # Web API indicators
        if (any(fw in stack.frameworks for fw in ["fastapi", "flask", "express", "spring", "django"]) and
            any("api" in name or "route" in name for name in file_names)):
            return ProjectType.WEB_API

        # Web App indicators
        if (any(fw in stack.frameworks for fw in ["react", "vue", "angular", "next"]) and
            any("public" in path or "static" in path for path in file_paths)):
            return ProjectType.WEB_APP

        # Mobile App indicators
        if any(indicator in " ".join(file_paths) for indicator in
               ["android", "ios", "react-native", "flutter", "cordova", "ionic"]):
            return ProjectType.MOBILE_APP

        # CLI Tool indicators
        if (any("main" in name and "cli" in name for name in file_names) or
            any("argparse" in path or "click" in path or "typer" in path for path in file_paths)):
            return ProjectType.CLI_TOOL

        # Library indicators
        if (any("setup.py" in name or "pyproject.toml" in name or "package.json" in name for name in file_names) and
            structure["total_files"] < 100 and structure["test_files"] > 0):
            return ProjectType.LIBRARY

        # Data Pipeline indicators
        if any(fw in stack.frameworks for fw in ["pandas", "spark", "airflow", "dagster", "luigi"]):
            return ProjectType.DATA_PIPELINE

        # Machine Learning indicators
        if any(fw in stack.frameworks for fw in ["tensorflow", "pytorch", "sklearn", "keras", "jax"]):
            return ProjectType.MACHINE_LEARNING

        # Microservice indicators
        if (any("service" in name for name in file_names) and
            any(fw in stack.frameworks for fw in ["fastapi", "flask", "express"]) and
            "docker" in stack.deployment):
            return ProjectType.MICROSERVICE

        # Game indicators
        if any(indicator in " ".join(file_paths) for indicator in
               ["unity", "unreal", "pygame", "godot", "game"]):
            return ProjectType.GAME

        # IoT indicators
        if any(indicator in " ".join(file_paths) for indicator in
               ["arduino", "raspberry", "embedded", "firmware", "mqtt"]):
            return ProjectType.IOT

        return ProjectType.UNKNOWN

    def _assess_complexity(self, structure: dict[str, int], _files: list[Path]) -> ComplexityLevel:
        """Assess project complexity."""
        lines = structure["total_lines"]
        files_count = structure["total_files"]
        dirs = structure["directories"]

        # Calculate complexity score
        score = 0

        # Lines of code
        if lines < 1000:
            score += 1
        elif lines < 5000:
            score += 2
        elif lines < 20000:
            score += 3
        else:
            score += 4

        # Number of files
        if files_count < 50:
            score += 1
        elif files_count < 200:
            score += 2
        elif files_count < 1000:
            score += 3
        else:
            score += 4

        # Directory depth
        if dirs < 10:
            score += 1
        elif dirs < 50:
            score += 2
        elif dirs < 200:
            score += 3
        else:
            score += 4

        # Determine complexity
        avg_score = score / 3

        if avg_score <= 1.5:
            return ComplexityLevel.SIMPLE
        elif avg_score <= 2.5:
            return ComplexityLevel.MODERATE
        elif avg_score <= 3.5:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.ENTERPRISE

    def _detect_architecture(self, files: list[Path],
                           patterns: list[str],
                           stack: TechnologyStack) -> ArchitecturePattern:
        """Detect architecture pattern."""
        file_names = [f.name.lower() for f in files]
        file_paths = [str(f).lower() for f in files]

        # MVC pattern
        if (all(p in patterns for p in ["model", "view", "controller"]) or
            all(p in " ".join(file_names) for p in ["model", "view", "controller"])):
            return ArchitecturePattern.MVC

        # MVVM pattern
        if ("viewmodel" in " ".join(file_names) or
            "ViewModel" in " ".join(file_paths)):
            return ArchitecturePattern.MVVM

        # Clean Architecture
        if (any(layer in " ".join(file_paths) for layer in
               ["entities", "use_cases", "interfaces", "frameworks"]) or
            "clean" in " ".join(file_paths)):
            return ArchitecturePattern.CLEAN_ARCHITECTURE

        # Hexagonal
        if (any(port in " ".join(file_paths) for port in
               ["ports", "adapters", "infrastructure"]) or
            "hexagonal" in " ".join(file_paths)):
            return ArchitecturePattern.HEXAGONAL

        # Microservices
        if (len([f for f in file_names if "service" in f]) > 1 and
            "docker" in stack.deployment):
            return ArchitecturePattern.MICROSERVICES

        # Layered
        if (any(layer in " ".join(file_paths) for layer in
               ["layers", "repository", "service", "controller"]) and
            "repository" in patterns):
            return ArchitecturePattern.LAYERED

        # Event-driven
        if (any(event in " ".join(file_paths) for event in
               ["event", "message", "queue", "publisher", "subscriber"]) or
            "kafka" in stack.tools or "rabbitmq" in stack.tools):
            return ArchitecturePattern.EVENT_DRIVEN

        # Serverless
        if (any(serverless in " ".join(file_paths) for serverless in
               ["lambda", "function", "serverless", "faas"]) or
            "serverless" in stack.deployment):
            return ArchitecturePattern.SERVERLESS

        # Plugin
        if (any(plugin in " ".join(file_paths) for plugin in
               ["plugin", "extension", "module", "addon"]) and
            len([f for f in file_names if "plugin" in f or "module" in f]) > 0):
            return ArchitecturePattern.PLUGIN

        return ArchitecturePattern.UNKNOWN

    def _detect_conventions(self, files: list[Path], _stack: TechnologyStack) -> list[str]:
        """Detect coding conventions used."""
        conventions = []

        # File naming conventions
        py_files = [f for f in files if f.suffix == ".py"]
        if py_files:
            # Check for snake_case
            snake_case = sum(1 for f in py_files if "_" in f.name)
            if snake_case > len(py_files) * 0.7:
                conventions.append("snake_case_files")

        js_files = [f for f in files if f.suffix in [".js", ".jsx"]]
        if js_files:
            # Check for camelCase
            camel_case = sum(1 for f in js_files if any(c.isupper() for c in f.name[1:-3]))
            if camel_case > len(js_files) * 0.7:
                conventions.append("camelCase_files")

        # Read some files for style detection
        for file_path in files[:10]:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                    # Indentation style
                    if content.startswith("    "):
                        conventions.append("4_space_indent")
                    elif content.startswith("\t"):
                        conventions.append("tab_indent")

                    # Documentation
                    if '"""' in content or "'''" in content:
                        conventions.append("docstrings")
                    if "/**" in content:
                        conventions.append("jsdoc")

                    # Type hints (Python)
                    if file_path.suffix == ".py" and ":" in content and "def " in content:
                        conventions.append("type_hints")

                    # Semicolons (JavaScript)
                    if file_path.suffix in [".js", ".jsx"] and content.count(";") > 10:
                        conventions.append("semicolons")

                    break  # Only need to check one file for style
            except Exception:
                pass

        return conventions

    def _assess_quality_indicators(self, files: list[Path],
                                 structure: dict[str, int]) -> dict[str, Any]:
        """Assess code quality indicators."""
        indicators = {
            "has_tests": structure["test_files"] > 0,
            "test_coverage": "unknown",  # Would need actual coverage tool
            "has_docs": structure["doc_files"] > 0,
            "has_ci_cd": any("ci" in str(f).lower() or "workflow" in str(f).lower()
                           for f in files),
            "has_git": any(".git" in str(f) for f in files),
            "config_management": structure["config_files"] > 0,
            "average_file_size": 0,
            "file_count": structure["total_files"]
        }

        # Calculate average file size
        total_size = 0
        for file_path in files[:50]:  # Sample for performance
            with contextlib.suppress(builtins.BaseException):
                total_size += file_path.stat().st_size

        if len(files) > 0:
            indicators["average_file_size"] = total_size // min(len(files), 50)

        # Quality score
        score = 0
        if indicators["has_tests"]:
            score += 20
        if indicators["has_docs"]:
            score += 15
        if indicators["has_ci_cd"]:
            score += 20
        if indicators["config_management"]:
            score += 15
        if indicators["average_file_size"] < 10000:  # Files not too large
            score += 15
        if indicators["file_count"] < 1000:  # Not too many files
            score += 15

        indicators["quality_score"] = score

        return indicators

    async def _save_classification(self, characteristics: ProjectCharacteristics,
                                 project_path: str) -> None:
        """Save classification to memory for learning."""
        data = {
            "project_path": project_path,
            "type": characteristics.type.value,
            "complexity": characteristics.complexity.value,
            "architecture": characteristics.architecture.value,
            "stack": {
                "languages": characteristics.stack.languages,
                "frameworks": characteristics.stack.frameworks,
                "databases": characteristics.stack.databases
            },
            "patterns": characteristics.patterns,
            "size_metrics": characteristics.size_metrics,
            "quality_score": characteristics.quality_indicators.get("quality_score", 0),
            "timestamp": datetime.now().isoformat()
        }

        await self.memory.add(
            content=json.dumps(data),
            category="PROJECT_CLASSIFICATION",
            tags=["project", characteristics.type.value, characteristics.complexity.value],
            importance=0.7
        )

    def get_recommendations(self, characteristics: ProjectCharacteristics) -> list[str]:
        """Get recommendations based on project characteristics."""
        recommendations = []

        # Type-specific recommendations
        if characteristics.type == ProjectType.WEB_API:
            if "fastapi" not in characteristics.stack.frameworks:
                recommendations.append("Consider using FastAPI for modern Python APIs")
            if "pytest" not in characteristics.stack.testing:
                recommendations.append("Add pytest for comprehensive API testing")

        elif characteristics.type == ProjectType.WEB_APP:
            if "typescript" not in characteristics.stack.languages:
                recommendations.append("Consider TypeScript for better type safety")
            if not any(fw in characteristics.stack.frameworks for fw in ["react", "vue", "angular"]):
                recommendations.append("Adopt a modern frontend framework")

        # Complexity recommendations
        if characteristics.complexity == ComplexityLevel.ENTERPRISE:
            if characteristics.architecture != ArchitecturePattern.MICROSERVICES:
                recommendations.append("Consider microservices for better scalability")
            if "kubernetes" not in characteristics.stack.deployment:
                recommendations.append("Use Kubernetes for container orchestration")

        elif characteristics.complexity == ComplexityLevel.SIMPLE:
            recommendations.append("Keep it simple - avoid over-engineering")

        # Quality recommendations
        quality = characteristics.quality_indicators
        if not quality["has_tests"]:
            recommendations.append("Add unit tests to improve code quality")
        if not quality["has_docs"]:
            recommendations.append("Document your code and API")
        if not quality["has_ci_cd"]:
            recommendations.append("Set up CI/CD pipeline for automated testing")

        # Architecture recommendations
        if characteristics.architecture == ArchitecturePattern.UNKNOWN:
            if characteristics.type == ProjectType.WEB_API:
                recommendations.append("Consider adopting Clean Architecture")
            elif characteristics.type in [ProjectType.WEB_APP, ProjectType.MOBILE_APP]:
                recommendations.append("Consider MVC or MVVM pattern")

        return recommendations


# CLI interface for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        classifier = ProjectClassifier()

        print("Classifying project...")
        characteristics = await classifier.classify_project(".")

        print(f"\nProject Type: {characteristics.type.value}")
        print(f"Complexity: {characteristics.complexity.value}")
        print(f"Architecture: {characteristics.architecture.value}")

        print("\nTechnology Stack:")
        print(f"  Languages: {', '.join(characteristics.stack.languages)}")
        print(f"  Frameworks: {', '.join(characteristics.stack.frameworks)}")
        print(f"  Databases: {', '.join(characteristics.stack.databases)}")
        print(f"  Testing: {', '.join(characteristics.stack.testing)}")

        print(f"\nPatterns: {', '.join(characteristics.patterns)}")
        print(f"Conventions: {', '.join(characteristics.conventions)}")

        print("\nSize Metrics:")
        for key, value in characteristics.size_metrics.items():
            print(f"  {key}: {value}")

        print("\nQuality Indicators:")
        for key, value in characteristics.quality_indicators.items():
            print(f"  {key}: {value}")

        print("\nRecommendations:")
        recommendations = classifier.get_recommendations(characteristics)
        for rec in recommendations:
            print(f"  - {rec}")

    asyncio.run(main())
