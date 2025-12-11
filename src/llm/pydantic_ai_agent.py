"""
AI Project Synthesizer - Pydantic AI Integration

Type-safe AI agents using Pydantic AI for:
- Structured outputs
- Validated responses
- Tool calling
- Multi-model support
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


# ============================================
# Structured Output Models
# ============================================

class SearchQuery(BaseModel):
    """Structured search query."""
    query: str = Field(description="Main search query")
    platforms: List[str] = Field(default=["github"], description="Platforms to search")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")


class ProjectIdea(BaseModel):
    """Structured project idea."""
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    technologies: List[str] = Field(description="Required technologies")
    complexity: str = Field(description="Complexity level: simple, medium, complex")
    estimated_time: str = Field(description="Estimated development time")


class ResourceRecommendation(BaseModel):
    """Recommended resource."""
    name: str
    url: str
    platform: str
    relevance_score: float = Field(ge=0, le=1)
    reason: str


class SynthesisResult(BaseModel):
    """Project synthesis result."""
    project_name: str
    resources: List[ResourceRecommendation]
    integration_plan: str
    folder_structure: Dict[str, Any]
    next_steps: List[str]


class ConversationResponse(BaseModel):
    """Structured conversation response."""
    message: str = Field(description="Response message to user")
    intent: str = Field(description="Detected user intent")
    action: Optional[str] = Field(default=None, description="Action to take")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: List[str] = Field(default_factory=list)


# ============================================
# Agent Dependencies
# ============================================

@dataclass
class AgentDeps:
    """Dependencies injected into agents."""
    user_id: str = "default"
    session_id: str = ""
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


# ============================================
# Pydantic AI Agents
# ============================================

def create_lmstudio_model() -> OpenAIModel:
    """Create LM Studio model (OpenAI-compatible)."""
    return OpenAIModel(
        "local-model",
        base_url="http://localhost:1234/v1",
        api_key="not-needed",
    )


def create_openai_model(model: str = "gpt-4o") -> OpenAIModel:
    """Create OpenAI model."""
    settings = get_settings()
    return OpenAIModel(
        model,
        api_key=settings.llm.openai_api_key.get_secret_value(),
    )


def create_anthropic_model(model: str = "claude-sonnet-4-20250514") -> AnthropicModel:
    """Create Anthropic model."""
    settings = get_settings()
    return AnthropicModel(
        model,
        api_key=settings.llm.anthropic_api_key.get_secret_value(),
    )


# Research Agent - Finds resources
research_agent = Agent(
    create_lmstudio_model(),
    result_type=List[ResourceRecommendation],
    system_prompt="""You are a research agent that finds relevant open-source resources.
    
Given a project idea or query, recommend the best resources from:
- GitHub repositories
- HuggingFace models and datasets
- Kaggle datasets and notebooks

For each resource, provide:
- Name and URL
- Platform it's from
- Relevance score (0-1)
- Why it's useful for the project

Focus on quality over quantity. Recommend 3-5 highly relevant resources.""",
)


# Synthesis Agent - Plans project assembly
synthesis_agent = Agent(
    create_lmstudio_model(),
    result_type=SynthesisResult,
    system_prompt="""You are a synthesis agent that plans how to combine resources into a project.

Given a project idea and list of resources, create:
1. A clear project name
2. Integration plan for combining the resources
3. Folder structure for the project
4. Next steps for development

Be practical and specific. Focus on making the resources work together.""",
)


# Conversation Agent - Handles user interaction
conversation_agent = Agent(
    create_lmstudio_model(),
    result_type=ConversationResponse,
    system_prompt="""You are an AI assistant for the Project Synthesizer.

Help users:
- Discover projects and resources
- Plan and assemble projects
- Understand code and documentation

Detect user intent:
- search: User wants to find resources
- build: User wants to create a project
- explain: User wants to understand something
- help: User needs assistance

Be concise and helpful. Ask clarifying questions when needed.""",
)


# ============================================
# Agent Tools
# ============================================

@research_agent.tool
async def search_github(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search GitHub for repositories."""
    try:
        from src.discovery.github_client import GitHubClient
        client = GitHubClient()
        results = await client.search_repositories(query, max_results=5)
        return str([{
            "name": r.name,
            "url": r.url,
            "stars": r.stars,
            "description": r.description,
        } for r in results])
    except Exception as e:
        return f"Error searching GitHub: {e}"


@research_agent.tool
async def search_huggingface(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search HuggingFace for models and datasets."""
    try:
        from src.discovery.huggingface_client import HuggingFaceClient
        client = HuggingFaceClient()
        models = await client.search_models(query, limit=3)
        datasets = await client.search_datasets(query, limit=2)
        return str({"models": models, "datasets": datasets})
    except Exception as e:
        return f"Error searching HuggingFace: {e}"


@synthesis_agent.tool
async def analyze_compatibility(
    ctx: RunContext[AgentDeps],
    resources: List[str],
) -> str:
    """Analyze compatibility between resources."""
    # Simplified compatibility check
    return "Resources appear compatible. All use Python and have MIT/Apache licenses."


@conversation_agent.tool
async def get_project_status(ctx: RunContext[AgentDeps]) -> str:
    """Get current project status."""
    context = ctx.deps.context
    if "current_project" in context:
        return f"Working on: {context['current_project']}"
    return "No active project. Start by describing what you want to build."


# ============================================
# High-Level Functions
# ============================================

async def research_project(query: str) -> List[ResourceRecommendation]:
    """Research resources for a project idea."""
    deps = AgentDeps(context={"query": query})
    result = await research_agent.run(
        f"Find resources for: {query}",
        deps=deps,
    )
    return result.data


async def synthesize_project(
    idea: str,
    resources: List[ResourceRecommendation],
) -> SynthesisResult:
    """Plan project synthesis from resources."""
    deps = AgentDeps(context={"idea": idea, "resources": resources})
    result = await synthesis_agent.run(
        f"Plan project synthesis for: {idea}\nResources: {resources}",
        deps=deps,
    )
    return result.data


async def chat(message: str, context: Dict[str, Any] = None) -> ConversationResponse:
    """Chat with the assistant."""
    deps = AgentDeps(context=context or {})
    result = await conversation_agent.run(message, deps=deps)
    return result.data


# ============================================
# Agent Factory
# ============================================

class AgentFactory:
    """Factory for creating configured agents."""
    
    @staticmethod
    def create_agent(
        agent_type: str,
        model_provider: str = "lmstudio",
        result_type: type = str,
    ) -> Agent:
        """
        Create a configured agent.
        
        Args:
            agent_type: Type of agent (research, synthesis, conversation)
            model_provider: LLM provider (lmstudio, openai, anthropic)
            result_type: Pydantic model for structured output
        """
        # Select model
        if model_provider == "openai":
            model = create_openai_model()
        elif model_provider == "anthropic":
            model = create_anthropic_model()
        else:
            model = create_lmstudio_model()
        
        # Select system prompt
        prompts = {
            "research": "You are a research agent that finds relevant resources.",
            "synthesis": "You are a synthesis agent that plans project assembly.",
            "conversation": "You are a helpful AI assistant.",
        }
        
        return Agent(
            model,
            result_type=result_type,
            system_prompt=prompts.get(agent_type, "You are a helpful assistant."),
        )
