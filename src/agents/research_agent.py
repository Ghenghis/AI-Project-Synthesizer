"""
AI Project Synthesizer - Research Agent

AI-powered research agent for:
- Multi-platform resource discovery
- Code analysis and evaluation
- Trend identification
- Recommendation generation
"""

from typing import Optional, Dict, Any

from src.agents.base import BaseAgent, AgentConfig, AgentTool
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research agent for discovering and analyzing resources.

    Capabilities:
    - Search GitHub, HuggingFace, Kaggle
    - Analyze code quality and patterns
    - Identify trending technologies
    - Generate recommendations
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        config = config or AgentConfig(
            name="research_agent",
            description="Discovers and analyzes resources across platforms",
            auto_continue=True,
            max_iterations=5,
        )
        super().__init__(config)
        self._setup_tools()

    def _setup_tools(self):
        """Set up research tools."""
        self.register_tool(AgentTool(
            name="search_github",
            description="Search GitHub for repositories",
            func=self._search_github,
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 10},
            },
        ))

        self.register_tool(AgentTool(
            name="search_huggingface",
            description="Search HuggingFace for models and datasets",
            func=self._search_huggingface,
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "type": {"type": "string", "enum": ["model", "dataset"]},
            },
        ))

        self.register_tool(AgentTool(
            name="analyze_repo",
            description="Analyze a GitHub repository",
            func=self._analyze_repo,
            parameters={
                "repo_url": {"type": "string", "description": "Repository URL"},
            },
        ))

        self.register_tool(AgentTool(
            name="get_trends",
            description="Get trending topics in AI/ML",
            func=self._get_trends,
            parameters={},
        ))

    async def _search_github(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search GitHub repositories."""
        try:
            from src.discovery.unified_search import create_unified_search

            search = create_unified_search()
            results = await search.search(
                query=query,
                platforms=["github"],
                max_results=max_results,
            )

            return {
                "success": True,
                "count": len(results.repositories),
                "repositories": [
                    {
                        "name": r.name,
                        "full_name": r.full_name,
                        "url": r.url,
                        "description": r.description,
                        "stars": r.stars,
                        "language": r.language,
                    }
                    for r in results.repositories
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search_huggingface(
        self,
        query: str,
        type: str = "model",
    ) -> Dict[str, Any]:
        """Search HuggingFace."""
        try:
            from src.discovery.unified_search import create_unified_search

            search = create_unified_search()
            results = await search.search(
                query=query,
                platforms=["huggingface"],
                max_results=10,
            )

            return {
                "success": True,
                "count": len(results.models) if type == "model" else len(results.datasets),
                "results": [
                    {"name": m.name, "url": m.url}
                    for m in (results.models if type == "model" else results.datasets)
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _analyze_repo(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a repository."""
        try:
            from src.analysis.code_analyzer import CodeAnalyzer

            analyzer = CodeAnalyzer()
            analysis = await analyzer.analyze_url(repo_url)

            return {
                "success": True,
                "analysis": {
                    "languages": analysis.languages,
                    "file_count": analysis.file_count,
                    "quality_score": analysis.quality_score,
                    "patterns": analysis.patterns,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_trends(self) -> Dict[str, Any]:
        """Get trending topics."""
        # Could integrate with GitHub trending, HN, etc.
        return {
            "success": True,
            "trends": [
                {"topic": "RAG", "category": "AI"},
                {"topic": "Local LLMs", "category": "AI"},
                {"topic": "Voice AI", "category": "AI"},
                {"topic": "Agents", "category": "AI"},
                {"topic": "MCP", "category": "Tools"},
            ],
        }

    async def _execute_step(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a research step."""
        llm = await self._get_llm()

        # Build prompt
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self._tools.values()
        ])

        prompt = f"""You are a research agent. Your task is to research: {task}

Available tools:
{tools_desc}

Previous context: {context.get('previous_step', 'None')}

Decide which tool to use and what parameters. Respond in this format:
TOOL: <tool_name>
PARAMS: <json_params>
REASONING: <why this tool>

Or if research is complete:
COMPLETE: true
SUMMARY: <research summary>
RECOMMENDATIONS: <list of recommendations>
"""

        # Get LLM response
        response = await llm.complete(prompt)

        # Parse response
        if "COMPLETE: true" in response:
            # Extract summary
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

    def _should_continue(self, step_result: Dict[str, Any]) -> bool:
        """Check if should continue research."""
        return not step_result.get("complete", False)

    async def research(self, topic: str) -> Dict[str, Any]:
        """
        Convenience method to research a topic.

        Args:
            topic: Research topic

        Returns:
            Research results
        """
        result = await self.run(f"Research: {topic}")
        return result.to_dict()
