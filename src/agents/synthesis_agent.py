"""
AI Project Synthesizer - Synthesis Agent

AI-powered project synthesis agent for:
- Project planning and structure
- Code generation
- Dependency resolution
- Documentation creation
"""

from pathlib import Path
from typing import Any

from src.agents.base import AgentConfig, AgentTool, BaseAgent
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class SynthesisAgent(BaseAgent):
    """
    Synthesis agent for assembling projects.

    Capabilities:
    - Plan project structure
    - Generate code files
    - Resolve dependencies
    - Create documentation
    - Set up configurations
    """

    def __init__(self, config: AgentConfig | None = None):
        config = config or AgentConfig(
            name="synthesis_agent",
            description="Assembles complete projects from ideas",
            auto_continue=True,
            max_iterations=10,
        )
        super().__init__(config)
        self._setup_tools()

    def _setup_tools(self):
        """Set up synthesis tools."""
        self.register_tool(AgentTool(
            name="plan_project",
            description="Create project structure plan",
            func=self._plan_project,
            parameters={
                "idea": {"type": "string", "description": "Project idea"},
                "type": {"type": "string", "enum": ["python", "web", "api", "ml"]},
            },
        ))

        self.register_tool(AgentTool(
            name="generate_file",
            description="Generate a code file",
            func=self._generate_file,
            parameters={
                "path": {"type": "string", "description": "File path"},
                "description": {"type": "string", "description": "What the file should do"},
            },
        ))

        self.register_tool(AgentTool(
            name="resolve_dependencies",
            description="Resolve and list project dependencies",
            func=self._resolve_dependencies,
            parameters={
                "project_type": {"type": "string"},
                "features": {"type": "array", "items": {"type": "string"}},
            },
        ))

        self.register_tool(AgentTool(
            name="create_readme",
            description="Generate README documentation",
            func=self._create_readme,
            parameters={
                "project_name": {"type": "string"},
                "description": {"type": "string"},
                "features": {"type": "array", "items": {"type": "string"}},
            },
        ))

        self.register_tool(AgentTool(
            name="assemble_project",
            description="Assemble complete project",
            func=self._assemble_project,
            parameters={
                "idea": {"type": "string"},
                "output_dir": {"type": "string"},
            },
        ))

    async def _plan_project(
        self,
        idea: str,
        type: str = "python",
    ) -> dict[str, Any]:
        """Plan project structure."""
        llm = await self._get_llm()

        prompt = f"""Plan a {type} project structure for: {idea}

Return a JSON structure with:
- name: project name
- directories: list of directories to create
- files: list of files with their purpose
- dependencies: key dependencies needed

Be specific and practical."""

        response = await llm.complete(prompt)

        # Parse response
        import json
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
                plan = json.loads(json_str)
            elif "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                plan = json.loads(response[start:end])
            else:
                plan = {"raw": response}
        except Exception:
            plan = {"raw": response}

        return {"success": True, "plan": plan}

    async def _generate_file(
        self,
        path: str,
        description: str,
    ) -> dict[str, Any]:
        """Generate a code file."""
        llm = await self._get_llm()

        # Determine language from extension
        ext = Path(path).suffix
        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".html": "HTML",
            ".css": "CSS",
            ".json": "JSON",
            ".md": "Markdown",
        }
        language = lang_map.get(ext, "code")

        prompt = f"""Generate {language} code for: {description}

File: {path}

Requirements:
- Production-ready code
- Include proper imports
- Add docstrings/comments
- Follow best practices
- Handle errors appropriately

Return ONLY the code, no explanations."""

        code = await llm.complete(prompt)

        # Clean up code
        if "```" in code:
            code = code.split("```")[1]
            if code.startswith(language.lower()) or code.startswith("python"):
                code = "\n".join(code.split("\n")[1:])
            if "```" in code:
                code = code.split("```")[0]

        return {
            "success": True,
            "path": path,
            "code": code.strip(),
            "language": language,
        }

    async def _resolve_dependencies(
        self,
        project_type: str,
        features: list[str],
    ) -> dict[str, Any]:
        """Resolve project dependencies."""
        # Common dependencies by type
        base_deps = {
            "python": ["python>=3.11"],
            "web": ["react", "vite"],
            "api": ["fastapi", "uvicorn", "pydantic"],
            "ml": ["torch", "transformers", "numpy"],
        }

        feature_deps = {
            "voice": ["elevenlabs", "sounddevice"],
            "llm": ["openai", "anthropic", "ollama"],
            "database": ["sqlalchemy", "aiosqlite"],
            "web": ["httpx", "aiohttp"],
            "cli": ["typer", "rich"],
        }

        deps = base_deps.get(project_type, [])

        for feature in features:
            if feature in feature_deps:
                deps.extend(feature_deps[feature])

        return {
            "success": True,
            "dependencies": list(set(deps)),
            "project_type": project_type,
        }

    async def _create_readme(
        self,
        project_name: str,
        description: str,
        features: list[str],
    ) -> dict[str, Any]:
        """Generate README."""
        llm = await self._get_llm()

        prompt = f"""Create a professional README.md for:

Project: {project_name}
Description: {description}
Features: {', '.join(features)}

Include:
- Title and badges
- Description
- Features list
- Installation instructions
- Usage examples
- Configuration
- Contributing guidelines
- License section"""

        readme = await llm.complete(prompt)

        return {
            "success": True,
            "readme": readme,
        }

    async def _assemble_project(
        self,
        idea: str,
        output_dir: str = "G:/",
    ) -> dict[str, Any]:
        """Assemble complete project."""
        try:
            from src.synthesis.project_assembler import (
                AssemblerConfig,
                ProjectAssembler,
            )

            config = AssemblerConfig(
                base_output_dir=Path(output_dir),
            )

            assembler = ProjectAssembler(config)
            project = await assembler.assemble(idea)

            return {
                "success": True,
                "project": {
                    "name": project.name,
                    "path": str(project.base_path),
                    "github_url": project.github_repo_url,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_step(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a synthesis step."""
        llm = await self._get_llm()

        # Build prompt
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self._tools.values()
        ])

        previous = context.get("previous_step", {})

        prompt = f"""You are a project synthesis agent. Your task: {task}

Available tools:
{tools_desc}

Previous step result: {previous.get('result', 'None')}
Steps completed: {context.get('steps_completed', 0)}

Decide the next action. Respond in this format:
TOOL: <tool_name>
PARAMS: <json_params>
REASONING: <why this tool>

Or if synthesis is complete:
COMPLETE: true
SUMMARY: <what was created>
"""

        response = await llm.complete(prompt)

        # Parse response
        if "COMPLETE: true" in response:
            summary = ""
            if "SUMMARY:" in response:
                summary = response.split("SUMMARY:")[1].split("\n")[0].strip()

            return {
                "action": "complete",
                "output": summary,
                "complete": True,
            }

        # Extract tool call
        tool_name = None
        params = {}

        if "TOOL:" in response:
            tool_name = response.split("TOOL:")[1].split("\n")[0].strip()

        if "PARAMS:" in response:
            import json
            try:
                params_str = response.split("PARAMS:")[1].split("\n")[0].strip()
                params = json.loads(params_str)
            except Exception:
                params = {}

        # Execute tool
        if tool_name and tool_name in self._tools:
            tool = self._tools[tool_name]
            result = await tool.execute(**params)

            self.add_memory("assistant", f"Used {tool_name}: {result}")

            return {
                "action": "tool_call",
                "tool": tool_name,
                "params": params,
                "result": result,
                "complete": False,
            }

        return {
            "action": "thinking",
            "output": response,
            "complete": False,
        }

    def _should_continue(self, step_result: dict[str, Any]) -> bool:
        """Check if should continue synthesis."""
        return not step_result.get("complete", False)

    async def synthesize(self, idea: str, output_dir: str = "G:/") -> dict[str, Any]:
        """
        Convenience method to synthesize a project.

        Args:
            idea: Project idea
            output_dir: Output directory

        Returns:
            Synthesis results
        """
        result = await self.run(
            f"Synthesize project: {idea}",
            context={"output_dir": output_dir}
        )
        return result.to_dict()
