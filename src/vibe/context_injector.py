"""
Context Injector for VIBE MCP

Provides project context for prompt enhancement:
- Project state and configuration
- Component references and relationships
- Past decisions and patterns
- Current working directory context
- Git status and recent changes

Integrates with Mem0 to learn from project history.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.memory.mem0_integration import MemorySystem


@dataclass
class ProjectContext:
    """Complete project context for prompt enhancement."""
    project_name: str
    project_type: str
    tech_stack: list[str]
    current_state: str
    components: list[str]
    past_decisions: list[str]
    recent_changes: list[str]
    environment: dict[str, Any]
    git_status: dict[str, Any] | None = None


class ContextInjector:
    """
    Injects relevant project context into prompts.

    Features:
    - Automatic project detection
    - Component discovery
    - History tracking via Mem0
    - Git integration
    - Environment awareness
    """

    def __init__(self):
        self.config = get_settings()
        self.memory = MemorySystem()

        # Cache for context
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)

        # Project detection patterns
        self.project_patterns = {
            "python": {
                "files": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
                "dirs": ["src", "tests"]
            },
            "javascript": {
                "files": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
                "dirs": ["src", "lib", "components"]
            },
            "typescript": {
                "files": ["tsconfig.json", "package.json"],
                "dirs": ["src", "types"]
            },
            "web": {
                "files": ["index.html", "webpack.config.js", "vite.config.js"],
                "dirs": ["public", "assets"]
            }
        }

    async def get_context(self, prompt: str, project_context: dict[str, Any] | None = None) -> ProjectContext:
        """
        Get comprehensive project context.

        Args:
            prompt: The user prompt (used to determine relevant context)
            project_context: Optional pre-defined context

        Returns:
            ProjectContext with all relevant information
        """
        # Check cache first
        cache_key = self._get_cache_key()
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached["timestamp"] < self._cache_ttl:
                return cached["context"]

        # Build context
        context = await self._build_context(prompt, project_context)

        # Cache result
        self._cache[cache_key] = {
            "context": context,
            "timestamp": datetime.now()
        }

        return context

    async def _build_context(self, prompt: str, project_context: dict[str, Any] | None) -> ProjectContext:
        """Build project context from various sources."""
        # Get current directory
        cwd = Path.cwd()

        # Detect project type and tech stack
        project_type, tech_stack = self._detect_project_type(cwd)

        # Get project name
        project_name = self._get_project_name(cwd)

        # Get current state
        current_state = await self._get_current_state(cwd, prompt)

        # Discover components
        components = await self._discover_components(cwd, project_type)

        # Get past decisions from memory
        past_decisions = await self._get_past_decisions(prompt, project_type)

        # Get recent changes
        recent_changes = self._get_recent_changes(cwd)

        # Get environment info
        environment = self._get_environment_info()

        # Get git status if available
        git_status = self._get_git_status(cwd)

        return ProjectContext(
            project_name=project_name,
            project_type=project_type,
            tech_stack=tech_stack,
            current_state=current_state,
            components=components,
            past_decisions=past_decisions,
            recent_changes=recent_changes,
            environment=environment,
            git_status=git_status
        )

    def _detect_project_type(self, directory: Path) -> tuple[str, list[str]]:
        """Detect project type and tech stack."""
        detected_type = "unknown"
        tech_stack = []

        # Check for patterns
        for proj_type, patterns in self.project_patterns.items():
            score = 0

            # Check files
            for file in patterns["files"]:
                if (directory / file).exists():
                    score += 2

            # Check directories
            for dir_name in patterns["dirs"]:
                if (directory / dir_name).exists():
                    score += 1

            if score > 0 and score > (tech_stack.count(detected_type) if detected_type == proj_type else 0):
                detected_type = proj_type

        # Build tech stack from files
        if detected_type == "python":
            tech_stack = ["Python"]
            if (directory / "requirements.txt").exists():
                tech_stack.append("pip")
            if (directory / "pyproject.toml").exists():
                tech_stack.append("poetry")
            if (directory / "Dockerfile").exists():
                tech_stack.append("Docker")
            if (directory / "docker-compose.yml").exists():
                tech_stack.append("Docker Compose")

        elif detected_type in ["javascript", "typescript"]:
            tech_stack = ["JavaScript" if detected_type == "javascript" else "TypeScript"]
            if (directory / "package.json").exists():
                tech_stack.append("npm")
            if (directory / "yarn.lock").exists():
                tech_stack.append("Yarn")
            if (directory / "pnpm-lock.yaml").exists():
                tech_stack.append("pnpm")
            if (directory / "webpack.config.js").exists():
                tech_stack.append("Webpack")
            if (directory / "vite.config.js").exists():
                tech_stack.append("Vite")

        elif detected_type == "web":
            tech_stack = ["HTML", "CSS", "JavaScript"]

        return detected_type, tech_stack

    def _get_project_name(self, directory: Path) -> str:
        """Get project name from directory or config."""
        # Try to get from package.json or pyproject.toml
        if (directory / "package.json").exists():
            try:
                with open(directory / "package.json") as f:
                    data = json.load(f)
                return data.get("name", directory.name)
            except:
                pass

        if (directory / "pyproject.toml").exists():
            try:
                import toml
                with open(directory / "pyproject.toml") as f:
                    data = toml.load(f)
                return data.get("project", {}).get("name", directory.name)
            except:
                pass

        # Use directory name
        return directory.name

    async def _get_current_state(self, directory: Path, prompt: str) -> str:
        """Get description of current project state."""
        states = []

        # Check if it's a new project
        if self._is_new_project(directory):
            states.append("New project setup")

        # Check for recent activity
        recent_files = self._get_recent_files(directory, hours=24)
        if recent_files:
            states.append(f"Recently modified {len(recent_files)} files")

        # Check for build/deployment status
        if (directory / "build").exists() or (directory / "dist").exists():
            states.append("Project has been built")

        if (directory / ".venv").exists() or (directory / "venv").exists():
            states.append("Virtual environment setup")

        # Infer from prompt
        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in ["test", "testing"]):
            states.append("Working on tests")
        if any(word in prompt_lower for word in ["deploy", "deployment"]):
            states.append("Preparing for deployment")
        if any(word in prompt_lower for word in ["fix", "bug", "error"]):
            states.append("Debugging/fixing issues")

        return "; ".join(states) if states else "Active development"

    async def _discover_components(self, directory: Path, project_type: str) -> list[str]:
        """Discover project components."""
        components = []

        if project_type == "python":
            # Find Python modules
            for py_file in directory.rglob("*.py"):
                if py_file.is_file() and not any(skip in str(py_file) for skip in [".venv", "__pycache__", "node_modules"]):
                    # Get module path relative to src if exists
                    try:
                        rel_path = py_file.relative_to(directory / "src")
                        components.append(f"src.{str(rel_path.with_suffix('')).replace(os.sep, '.')}")
                    except ValueError:
                        # Not in src, use relative path
                        rel_path = py_file.relative_to(directory)
                        components.append(str(rel_path.with_suffix('')).replace(os.sep, '.'))

            # Limit to main components
            components = [c for c in components if not c.endswith((".test", ".tests", "__init__"))]

        elif project_type in ["javascript", "typescript"]:
            # Find components
            for ext in ["*.js", "*.jsx", "*.ts", "*.tsx"]:
                for file in directory.rglob(ext):
                    if file.is_file() and not any(skip in str(file) for skip in ["node_modules", ".git"]):
                        try:
                            rel_path = file.relative_to(directory)
                            components.append(str(rel_path))
                        except ValueError:
                            pass

        # Limit number and prioritize
        if len(components) > 20:
            # Prioritize based on location and name
            components = sorted(components, key=lambda x: (
                0 if "src" in x else 1,
                0 if "main" in x or "index" in x else 1,
                0 if "app" in x else 1,
                x
            ))[:20]

        return components

    async def _get_past_decisions(self, prompt: str, project_type: str) -> list[str]:
        """Get relevant past decisions from memory."""
        # Search memory for similar contexts
        query = f"project decision {project_type} {prompt[:50]}"

        try:
            results = await self.memory.search(
                query=query,
                category="DECISION",
                limit=5
            )

            decisions = []
            for result in results:
                try:
                    data = json.loads(result["content"])
                    if "decision" in data:
                        decisions.append(data["decision"])
                except:
                    decisions.append(result["content"][:100])

            return decisions
        except:
            return []

    def _get_recent_changes(self, directory: Path) -> list[str]:
        """Get recent file changes."""
        changes = []

        # Get recently modified files
        recent_files = self._get_recent_files(directory, hours=48)

        for file_path in recent_files[:10]:
            rel_path = file_path.relative_to(directory)
            changes.append(f"Modified: {rel_path}")

        return changes

    def _get_recent_files(self, directory: Path, hours: int = 24) -> list[Path]:
        """Get files modified in the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime > cutoff:
                        # Skip certain directories
                        if not any(skip in str(file_path) for skip in [".git", ".venv", "node_modules", "__pycache__"]):
                            recent.append(file_path)
                except:
                    continue

        return sorted(recent, key=lambda x: x.stat().st_mtime, reverse=True)

    def _get_environment_info(self) -> dict[str, Any]:
        """Get current environment information."""
        return {
            "python_version": os.sys.version,
            "platform": os.name,
            "cwd": str(Path.cwd()),
            "env_vars": {
                "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
                "CONDA_DEFAULT_ENV": os.environ.get("CONDA_DEFAULT_ENV"),
                "NODE_ENV": os.environ.get("NODE_ENV")
            }
        }

    def _get_git_status(self, directory: Path) -> dict[str, Any] | None:
        """Get git repository status."""
        try:
            import subprocess

            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=directory,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return None

            # Get branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=directory,
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=directory,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                changed_files = len([line for line in result.stdout.strip().split('\n') if line])
                return {
                    "branch": branch,
                    "changed_files": changed_files,
                    "has_uncommitted": changed_files > 0
                }

        except FileNotFoundError:
            # Git not installed
            pass
        except Exception as e:
            print(f"Git status error: {e}")

        return None

    def _is_new_project(self, directory: Path) -> bool:
        """Check if this appears to be a new project."""
        # Very few files in root
        root_files = [f for f in directory.iterdir() if f.is_file() and not f.name.startswith('.')]

        # Check for common project files
        has_config = any(
            (directory / f).exists()
            for f in ["package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod"]
        )

        return len(root_files) < 5 and not has_config

    def _get_cache_key(self) -> str:
        """Generate cache key based on current directory."""
        return str(Path.cwd())

    async def add_decision(self, decision: str, context: dict[str, Any]) -> None:
        """
        Add a project decision to memory.

        Args:
            decision: The decision made
            context: Context around the decision
        """
        memory_entry = {
            "type": "project_decision",
            "decision": decision,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

        await self.memory.add(
            content=json.dumps(memory_entry),
            category="DECISION",
            tags=["decision", "project"],
            importance=0.8
        )

    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._cache.clear()


# CLI interface for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        injector = ContextInjector()

        # Test context injection
        prompt = "Create a new API endpoint for user authentication"
        context = await injector.get_context(prompt)

        print("PROJECT CONTEXT:")
        print(f"Name: {context.project_name}")
        print(f"Type: {context.project_type}")
        print(f"Tech Stack: {', '.join(context.tech_stack)}")
        print(f"State: {context.current_state}")
        print(f"\nComponents ({len(context.components)}):")
        for comp in context.components[:10]:
            print(f"  - {comp}")
        print(f"\nRecent Decisions ({len(context.past_decisions)}):")
        for decision in context.past_decisions:
            print(f"  - {decision}")

        if context.git_status:
            print("\nGit Status:")
            print(f"  Branch: {context.git_status['branch']}")
            print(f"  Changed files: {context.git_status['changed_files']}")

    asyncio.run(main())
