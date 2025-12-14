"""
AI Project Synthesizer - Proactive Research Engine

When user is idle, the AI automatically:
1. Analyzes conversation context to understand user's goals
2. Searches for related projects across all platforms
3. Finds research papers on arXiv
4. Discovers complementary tools and libraries
5. Prepares recommendations for when user returns

IDLE BEHAVIOR:
- User idle > 30 seconds: Start light research
- User idle > 60 seconds: Deep research (papers, more projects)
- User idle > 120 seconds: Synthesis recommendations ready

All research happens in background - ready when user returns.
"""

import asyncio
import contextlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class ResearchDepth(str, Enum):
    """How deep to research."""

    LIGHT = "light"  # Quick search, top results
    MEDIUM = "medium"  # More results, some analysis
    DEEP = "deep"  # Papers, synthesis recommendations


@dataclass
class ResearchResult:
    """Results from proactive research."""

    query: str
    depth: ResearchDepth

    # Discovered items
    projects: list[dict[str, Any]] = field(default_factory=list)
    papers: list[dict[str, Any]] = field(default_factory=list)
    datasets: list[dict[str, Any]] = field(default_factory=list)
    models: list[dict[str, Any]] = field(default_factory=list)

    # Analysis
    recommendations: list[str] = field(default_factory=list)
    synthesis_ideas: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    # Metadata
    research_time_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def summary(self) -> str:
        """Get summary of research."""
        parts = []
        if self.projects:
            parts.append(f"{len(self.projects)} projects")
        if self.papers:
            parts.append(f"{len(self.papers)} papers")
        if self.datasets:
            parts.append(f"{len(self.datasets)} datasets")
        if self.models:
            parts.append(f"{len(self.models)} models")
        if self.recommendations:
            parts.append(f"{len(self.recommendations)} recommendations")

        return f"Found: {', '.join(parts)}" if parts else "No results yet"


@dataclass
class ResearchConfig:
    """Configuration for proactive research."""

    # Idle thresholds (seconds)
    light_research_after: float = 30.0
    medium_research_after: float = 60.0
    deep_research_after: float = 120.0

    # Research limits
    max_projects_per_platform: int = 10
    max_papers: int = 10
    max_datasets: int = 5
    max_models: int = 5

    # Platforms to search
    search_github: bool = True
    search_huggingface: bool = True
    search_kaggle: bool = True
    search_arxiv: bool = True

    # Callbacks
    on_research_start: Callable[[ResearchDepth], None] | None = None
    on_research_complete: Callable[[ResearchResult], None] | None = None


class ProactiveResearchEngine:
    """
    Automatically researches when user is idle.

    Gathers projects, papers, and ideas based on conversation context.
    Ready to present when user returns.

    Usage:
        engine = ProactiveResearchEngine()
        engine.set_context("I want to build a RAG chatbot")
        engine.start_monitoring()

        # ... user goes idle ...
        # Engine automatically researches in background

        # When user returns:
        results = engine.get_latest_research()
        print(results.summary())
    """

    def __init__(self, config: ResearchConfig | None = None):
        """Initialize research engine."""
        self.config = config or ResearchConfig()

        # State
        self._context: list[str] = []  # Conversation context
        self._current_topic: str = ""
        self._last_user_activity: float = time.time()
        self._research_results: list[ResearchResult] = []

        # Control
        self._running = False
        self._research_task: asyncio.Task | None = None
        self._current_depth: ResearchDepth | None = None

        # Components
        self._search = None

    def set_context(self, text: str):
        """Add context from conversation."""
        self._context.append(text)
        self._last_user_activity = time.time()
        self._current_topic = self._extract_topic()

        # Reset research when user is active
        self._current_depth = None

    def user_active(self):
        """Mark user as active (resets idle timer)."""
        self._last_user_activity = time.time()
        self._current_depth = None

    def _extract_topic(self) -> str:
        """Extract main topic from context."""
        if not self._context:
            return ""

        # Use last few messages to determine topic
        recent = self._context[-5:]
        combined = " ".join(recent).lower()

        # Extract key terms
        keywords = []

        # Tech keywords
        tech_terms = [
            "chatbot",
            "rag",
            "llm",
            "machine learning",
            "ml",
            "ai",
            "web",
            "api",
            "database",
            "frontend",
            "backend",
            "python",
            "javascript",
            "react",
            "pytorch",
            "tensorflow",
            "nlp",
            "computer vision",
            "data",
            "pipeline",
        ]

        for term in tech_terms:
            if term in combined:
                keywords.append(term)

        return " ".join(keywords[:5]) if keywords else combined[:100]

    async def start_monitoring(self):
        """Start monitoring for idle and auto-research."""
        if self._running:
            return

        self._running = True
        self._research_task = asyncio.create_task(self._monitor_loop())
        secure_logger.info("Proactive research engine started")

    async def stop_monitoring(self):
        """Stop monitoring."""
        self._running = False
        if self._research_task:
            self._research_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._research_task

    async def _monitor_loop(self):
        """Monitor idle time and trigger research."""
        while self._running:
            await asyncio.sleep(5)  # Check every 5 seconds

            if not self._current_topic:
                continue

            idle_time = time.time() - self._last_user_activity

            # Determine research depth based on idle time
            if idle_time >= self.config.deep_research_after:
                target_depth = ResearchDepth.DEEP
            elif idle_time >= self.config.medium_research_after:
                target_depth = ResearchDepth.MEDIUM
            elif idle_time >= self.config.light_research_after:
                target_depth = ResearchDepth.LIGHT
            else:
                continue

            # Only research if we haven't at this depth yet
            if self._current_depth != target_depth:
                self._current_depth = target_depth
                await self._do_research(target_depth)

    async def _do_research(self, depth: ResearchDepth):
        """Perform research at specified depth."""
        secure_logger.info(f"Starting {depth.value} research on: {self._current_topic}")

        if self.config.on_research_start:
            self.config.on_research_start(depth)

        start_time = time.time()
        result = ResearchResult(query=self._current_topic, depth=depth)

        try:
            # Initialize search if needed
            if self._search is None:
                from src.discovery.unified_search import create_unified_search

                self._search = create_unified_search()

            # Search projects
            if depth in [ResearchDepth.LIGHT, ResearchDepth.MEDIUM, ResearchDepth.DEEP]:
                await self._search_projects(result, depth)

            # Search papers (medium and deep)
            if depth in [ResearchDepth.MEDIUM, ResearchDepth.DEEP]:
                await self._search_papers(result)

            # Generate recommendations (deep only)
            if depth == ResearchDepth.DEEP:
                await self._generate_recommendations(result)

            result.research_time_seconds = time.time() - start_time
            self._research_results.append(result)

            secure_logger.info(f"Research complete: {result.summary()}")

            if self.config.on_research_complete:
                self.config.on_research_complete(result)

        except Exception as e:
            secure_logger.error(f"Research error: {e}")

    async def _search_projects(self, result: ResearchResult, depth: ResearchDepth):
        """Search for projects across platforms."""
        max_results = {
            ResearchDepth.LIGHT: 5,
            ResearchDepth.MEDIUM: 10,
            ResearchDepth.DEEP: 15,
        }[depth]

        platforms = []
        if self.config.search_github:
            platforms.append("github")
        if self.config.search_huggingface:
            platforms.append("huggingface")
        if self.config.search_kaggle:
            platforms.append("kaggle")

        search_result = await self._search.search(
            query=self._current_topic,
            platforms=platforms,
            max_results=max_results,
        )

        for repo in search_result.repositories:
            item = {
                "name": repo.full_name,
                "platform": repo.platform,
                "url": repo.url,
                "description": repo.description,
                "stars": repo.stars,
            }

            if repo.platform == "github":
                result.projects.append(item)
            elif repo.platform == "huggingface":
                result.models.append(item)
            elif repo.platform == "kaggle":
                result.datasets.append(item)

    async def _search_papers(self, result: ResearchResult):
        """Search for research papers on arXiv."""
        try:
            import aiohttp

            # arXiv API search
            query = self._current_topic.replace(" ", "+")
            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={self.config.max_papers}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        papers = self._parse_arxiv_response(text)
                        result.papers.extend(papers)

        except Exception as e:
            secure_logger.warning(f"arXiv search error: {e}")

    def _parse_arxiv_response(self, xml_text: str) -> list[dict[str, Any]]:
        """Parse arXiv API response."""
        import re

        papers = []

        # Simple regex parsing (avoid XML dependency)
        entries = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)

        for entry in entries[: self.config.max_papers]:
            title_match = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
            summary_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
            link_match = re.search(r"<id>(.*?)</id>", entry)

            if title_match:
                papers.append(
                    {
                        "title": title_match.group(1).strip().replace("\n", " "),
                        "summary": summary_match.group(1).strip()[:200] + "..."
                        if summary_match
                        else "",
                        "url": link_match.group(1) if link_match else "",
                    }
                )

        return papers

    async def _generate_recommendations(self, result: ResearchResult):
        """Generate recommendations based on research."""
        # Analyze what we found
        if result.projects:
            top_project = result.projects[0]
            result.recommendations.append(
                f"Start with {top_project['name']} - it has {top_project['stars']} stars and matches your needs"
            )

        if result.models:
            result.recommendations.append(
                f"Consider using {result.models[0]['name']} from HuggingFace for your AI component"
            )

        if result.datasets:
            result.recommendations.append(
                f"Train/test with {result.datasets[0]['name']} dataset from Kaggle"
            )

        if result.papers:
            result.recommendations.append(
                f"Read '{result.papers[0]['title']}' for latest research approaches"
            )

        # Synthesis ideas
        if len(result.projects) >= 2:
            result.synthesis_ideas.append(
                f"Combine {result.projects[0]['name']} with {result.projects[1]['name']} for a complete solution"
            )

        # Next steps
        result.next_steps = [
            "1. Clone the top recommended project",
            "2. Review the research paper for implementation ideas",
            "3. Set up the dataset for testing",
            "4. Integrate the HuggingFace model",
        ]

    def get_latest_research(self) -> ResearchResult | None:
        """Get the most recent research results."""
        return self._research_results[-1] if self._research_results else None

    def get_all_research(self) -> list[ResearchResult]:
        """Get all research results."""
        return self._research_results.copy()

    def format_for_user(self) -> str:
        """Format research results for presenting to user."""
        result = self.get_latest_research()
        if not result:
            return "No research available yet."

        lines = [
            f"🔍 **While you were away, I researched '{result.query}':**\n",
        ]

        if result.projects:
            lines.append("**📦 Projects Found:**")
            for p in result.projects[:5]:
                lines.append(
                    f"  • {p['name']} ({p['stars']} ⭐) - {p['description'][:60]}..."
                )
            lines.append("")

        if result.papers:
            lines.append("**📄 Research Papers:**")
            for p in result.papers[:3]:
                lines.append(f"  • {p['title'][:80]}...")
            lines.append("")

        if result.models:
            lines.append("**🤖 AI Models:**")
            for m in result.models[:3]:
                lines.append(f"  • {m['name']}")
            lines.append("")

        if result.datasets:
            lines.append("**📊 Datasets:**")
            for d in result.datasets[:3]:
                lines.append(f"  • {d['name']}")
            lines.append("")

        if result.recommendations:
            lines.append("**💡 Recommendations:**")
            for r in result.recommendations:
                lines.append(f"  • {r}")
            lines.append("")

        if result.next_steps:
            lines.append("**📋 Suggested Next Steps:**")
            for s in result.next_steps:
                lines.append(f"  {s}")

        lines.append(f"\n_Research completed in {result.research_time_seconds:.1f}s_")

        return "\n".join(lines)


# Global instance
_research_engine: ProactiveResearchEngine | None = None


def get_research_engine() -> ProactiveResearchEngine:
    """Get or create research engine."""
    global _research_engine
    if _research_engine is None:
        _research_engine = ProactiveResearchEngine()
    return _research_engine
