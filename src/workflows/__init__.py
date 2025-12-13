"""
AI Project Synthesizer - Workflow Engine

Integrates:
- LangChain for LLM orchestration and chains
- n8n for visual workflow automation
- Pydantic AI for type-safe agents
- Custom workflow definitions
"""

from src.workflows.langchain_integration import (
    LangChainOrchestrator,
    create_research_chain,
    create_synthesis_chain,
)
from src.workflows.n8n_integration import (
    N8NClient,
    N8NWorkflow,
    N8NWorkflowTemplates,
    setup_n8n_workflows,
)
from src.workflows.orchestrator import (
    WorkflowEngine,
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowType,
    get_orchestrator,
)

__all__ = [
    # LangChain
    "LangChainOrchestrator",
    "create_research_chain",
    "create_synthesis_chain",
    # n8n
    "N8NClient",
    "N8NWorkflow",
    "N8NWorkflowTemplates",
    "setup_n8n_workflows",
    # Orchestrator
    "WorkflowOrchestrator",
    "WorkflowType",
    "WorkflowEngine",
    "WorkflowResult",
    "get_orchestrator",
]
