"""
AI Project Synthesizer - LangChain Integration

Advanced LLM workflows using LangChain:
- Research chains for multi-step discovery
- Synthesis chains for project assembly
- RAG chains for documentation
- Agent chains for autonomous tasks
"""

import asyncio
from dataclasses import dataclass
from typing import Any

# Try importing LangChain components with fallbacks
try:
    from langchain_core.messages import SystemMessage
    from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_core.runnables import RunnableLambda

    LANGCHAIN_CORE_AVAILABLE = True
except ImportError:
    LANGCHAIN_CORE_AVAILABLE = False
    ChatPromptTemplate = None
    PromptTemplate = None
    StrOutputParser = None
    JsonOutputParser = None

try:
    from langchain_community.llms import Ollama

    LANGCHAIN_COMMUNITY_AVAILABLE = True
except ImportError:
    LANGCHAIN_COMMUNITY_AVAILABLE = False
    Ollama = None

try:
    from langchain_openai import ChatOpenAI

    LANGCHAIN_OPENAI_AVAILABLE = True
except ImportError:
    LANGCHAIN_OPENAI_AVAILABLE = False
    ChatOpenAI = None

try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    from langchain.tools import Tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    AgentExecutor = None
    Tool = None

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)

# Check if LangChain is fully available
LANGCHAIN_READY = LANGCHAIN_CORE_AVAILABLE and LANGCHAIN_AVAILABLE


@dataclass
class ChainConfig:
    """Configuration for LangChain chains."""

    model_provider: str = "lmstudio"  # lmstudio, ollama, openai
    model_name: str = "local-model"
    temperature: float = 0.7
    max_tokens: int = 2000
    streaming: bool = True


class LangChainOrchestrator:
    """
    Orchestrates LangChain workflows for the synthesizer.

    Features:
    - Multi-provider LLM support (LM Studio, Ollama, OpenAI)
    - Pre-built chains for common tasks
    - Custom chain creation
    - Agent-based autonomous workflows

    Usage:
        orchestrator = LangChainOrchestrator()

        # Run research chain
        result = await orchestrator.research("machine learning project ideas")

        # Run synthesis chain
        result = await orchestrator.synthesize(project_idea, resources)
    """

    def __init__(self, config: ChainConfig | None = None):
        """Initialize orchestrator."""
        self.config = config or ChainConfig()
        self._llm = None
        self._memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is not None:
            return self._llm

        settings = get_settings()

        if self.config.model_provider == "lmstudio":
            # LM Studio uses OpenAI-compatible API
            self._llm = ChatOpenAI(
                base_url="http://localhost:1234/v1",
                api_key="not-needed",
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                streaming=self.config.streaming,
            )
        elif self.config.model_provider == "ollama":
            self._llm = Ollama(
                base_url="http://localhost:11434",
                model=self.config.model_name or "qwen2.5-coder",
                temperature=self.config.temperature,
            )
        elif self.config.model_provider == "openai":
            api_key = settings.llm.openai_api_key.get_secret_value()
            self._llm = ChatOpenAI(
                api_key=api_key,
                model=self.config.model_name or "gpt-4o",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        else:
            raise ValueError(f"Unknown provider: {self.config.model_provider}")

        return self._llm

    async def research(self, query: str) -> dict[str, Any]:
        """
        Run research chain to discover resources.

        Steps:
        1. Analyze query to understand intent
        2. Generate search queries for each platform
        3. Synthesize findings into recommendations
        """
        chain = create_research_chain(self._get_llm())

        result = await chain.ainvoke({"query": query})

        return {
            "query": query,
            "analysis": result.get("analysis", ""),
            "search_queries": result.get("search_queries", {}),
            "recommendations": result.get("recommendations", ""),
        }

    async def synthesize(
        self,
        project_idea: str,
        resources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Run synthesis chain to plan project assembly.

        Steps:
        1. Analyze resources for compatibility
        2. Plan integration strategy
        3. Generate project structure
        4. Create documentation outline
        """
        chain = create_synthesis_chain(self._get_llm())

        result = await chain.ainvoke(
            {
                "project_idea": project_idea,
                "resources": resources,
            }
        )

        return {
            "project_idea": project_idea,
            "compatibility_analysis": result.get("compatibility", ""),
            "integration_plan": result.get("plan", ""),
            "structure": result.get("structure", {}),
            "documentation": result.get("docs", ""),
        }

    async def chat(self, message: str) -> str:
        """
        Chat with memory for multi-turn conversations.
        """
        llm = self._get_llm()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AI Project Synthesizer assistant.
            You help users discover, combine, and build projects from open-source resources.
            You have access to GitHub, HuggingFace, and Kaggle for searching.
            Be helpful, concise, and proactive in suggesting improvements.""",
                ),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ]
        )

        chain = prompt | llm | StrOutputParser()

        # Get chat history
        history = self._memory.load_memory_variables({})

        response = await chain.ainvoke(
            {
                "input": message,
                "chat_history": history.get("chat_history", []),
            }
        )

        # Save to memory
        self._memory.save_context(
            {"input": message},
            {"output": response},
        )

        return response

    def create_agent(self, tools: list[Tool]) -> AgentExecutor:
        """
        Create a ReAct agent with custom tools.

        Args:
            tools: List of LangChain tools

        Returns:
            AgentExecutor ready to run
        """
        llm = self._get_llm()

        prompt = PromptTemplate.from_template("""Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}""")

        agent = create_react_agent(llm, tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self._memory,
            verbose=True,
            handle_parsing_errors=True,
        )


def create_research_chain(llm):
    """
    Create a research chain for discovering resources.

    Chain flow:
    1. Query Analysis → Understanding what user wants
    2. Search Query Generation → Platform-specific queries
    3. Recommendation Synthesis → Actionable suggestions
    """

    # Step 1: Analyze the query
    analysis_prompt = ChatPromptTemplate.from_template("""
Analyze this project research query and identify:
1. Main topic/domain
2. Key technologies mentioned
3. Type of resources needed (code, models, datasets, papers)
4. Complexity level

Query: {query}

Analysis:""")

    analysis_chain = analysis_prompt | llm | StrOutputParser()

    # Step 2: Generate search queries
    search_prompt = ChatPromptTemplate.from_template("""
Based on this analysis, generate optimized search queries for each platform:

Analysis: {analysis}

Generate JSON with search queries:
{{
    "github": ["query1", "query2"],
    "huggingface": ["query1", "query2"],
    "kaggle": ["query1", "query2"],
    "arxiv": ["query1"]
}}

Search Queries:""")

    search_chain = search_prompt | llm | StrOutputParser()

    # Step 3: Synthesize recommendations
    recommend_prompt = ChatPromptTemplate.from_template("""
Based on the analysis and search strategy, provide recommendations:

Original Query: {query}
Analysis: {analysis}
Search Strategy: {search_queries}

Provide 3-5 specific recommendations for finding the best resources:""")

    recommend_chain = recommend_prompt | llm | StrOutputParser()

    # Combine into sequential chain
    async def run_chain(inputs):
        query = inputs["query"]

        analysis = await analysis_chain.ainvoke({"query": query})
        search_queries = await search_chain.ainvoke({"analysis": analysis})
        recommendations = await recommend_chain.ainvoke(
            {
                "query": query,
                "analysis": analysis,
                "search_queries": search_queries,
            }
        )

        return {
            "analysis": analysis,
            "search_queries": search_queries,
            "recommendations": recommendations,
        }

    return RunnableLambda(run_chain)


def create_synthesis_chain(llm):
    """
    Create a synthesis chain for project assembly planning.

    Chain flow:
    1. Compatibility Analysis → Check if resources work together
    2. Integration Planning → How to combine them
    3. Structure Generation → Project folder layout
    4. Documentation Outline → README and docs
    """

    # Step 1: Compatibility analysis
    compat_prompt = ChatPromptTemplate.from_template("""
Analyze compatibility of these resources for the project:

Project Idea: {project_idea}
Resources: {resources}

Check for:
1. Language/framework compatibility
2. Dependency conflicts
3. License compatibility
4. Integration complexity

Compatibility Analysis:""")

    compat_chain = compat_prompt | llm | StrOutputParser()

    # Step 2: Integration plan
    plan_prompt = ChatPromptTemplate.from_template("""
Create an integration plan for these resources:

Project: {project_idea}
Compatibility: {compatibility}
Resources: {resources}

Plan should include:
1. Order of integration
2. Required adapters/wrappers
3. Configuration needed
4. Testing strategy

Integration Plan:""")

    plan_chain = plan_prompt | llm | StrOutputParser()

    # Step 3: Project structure
    structure_prompt = ChatPromptTemplate.from_template("""
Generate project folder structure:

Project: {project_idea}
Integration Plan: {plan}

Provide a tree structure with key files:""")

    structure_chain = structure_prompt | llm | StrOutputParser()

    # Step 4: Documentation outline
    docs_prompt = ChatPromptTemplate.from_template("""
Create README.md outline:

Project: {project_idea}
Structure: {structure}

Include sections for:
- Overview
- Features
- Installation
- Usage
- Configuration
- Contributing

README Outline:""")

    docs_chain = docs_prompt | llm | StrOutputParser()

    # Combine
    async def run_chain(inputs):
        project_idea = inputs["project_idea"]
        resources = inputs["resources"]

        compatibility = await compat_chain.ainvoke(
            {
                "project_idea": project_idea,
                "resources": str(resources),
            }
        )

        plan = await plan_chain.ainvoke(
            {
                "project_idea": project_idea,
                "compatibility": compatibility,
                "resources": str(resources),
            }
        )

        structure = await structure_chain.ainvoke(
            {
                "project_idea": project_idea,
                "plan": plan,
            }
        )

        docs = await docs_chain.ainvoke(
            {
                "project_idea": project_idea,
                "structure": structure,
            }
        )

        return {
            "compatibility": compatibility,
            "plan": plan,
            "structure": structure,
            "docs": docs,
        }

    return RunnableLambda(run_chain)


# Pre-built tools for agents
def create_synthesizer_tools() -> list[Tool]:
    """Create LangChain tools for the synthesizer agent."""

    async def search_github(query: str) -> str:
        """Search GitHub repositories."""
        from src.discovery.github_client import GitHubClient

        client = GitHubClient()
        results = await client.search_repositories(query, max_results=5)
        return str([{"name": r.name, "url": r.url, "stars": r.stars} for r in results])

    async def search_huggingface(query: str) -> str:
        """Search HuggingFace models."""
        from src.discovery.huggingface_client import HuggingFaceClient

        client = HuggingFaceClient()
        results = await client.search_models(query, limit=5)
        return str(results)

    async def assemble_project(idea: str) -> str:
        """Assemble a project from an idea."""
        from src.synthesis.project_assembler import ProjectAssembler

        assembler = ProjectAssembler()
        result = await assembler.assemble(idea)
        return f"Project assembled at: {result.base_path}"

    return [
        Tool(
            name="search_github",
            description="Search GitHub for repositories. Input: search query string.",
            func=lambda q: asyncio.run(search_github(q)),
            coroutine=search_github,
        ),
        Tool(
            name="search_huggingface",
            description="Search HuggingFace for models and datasets. Input: search query.",
            func=lambda q: asyncio.run(search_huggingface(q)),
            coroutine=search_huggingface,
        ),
        Tool(
            name="assemble_project",
            description="Assemble a complete project from an idea. Input: project idea description.",
            func=lambda i: asyncio.run(assemble_project(i)),
            coroutine=assemble_project,
        ),
    ]
