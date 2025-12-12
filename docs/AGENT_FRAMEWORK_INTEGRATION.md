# 🤖 Agent Framework Integration Specification

## Overview

This document details how to integrate **AutoGen**, **OpenAI Swarm**, and **LangGraph** into the AI Project Synthesizer, alongside existing **LangChain** and **n8n** integrations.

---

## Framework Comparison & Use Cases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WHEN TO USE WHICH FRAMEWORK                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AutoGen (Microsoft)                                                        │
│  ├── Complex multi-agent conversations                                      │
│  ├── Code generation with execution                                         │
│  ├── Human-in-the-loop workflows                                           │
│  └── Best for: Complex reasoning, code review cycles                        │
│                                                                             │
│  OpenAI Swarm                                                               │
│  ├── Lightweight agent handoffs                                            │
│  ├── Simple agent routing                                                  │
│  ├── Fast context switching                                                │
│  └── Best for: Quick task delegation, simple pipelines                     │
│                                                                             │
│  LangGraph                                                                  │
│  ├── Stateful multi-step workflows                                         │
│  ├── Cyclic agent graphs                                                   │
│  ├── Persistent state across steps                                         │
│  └── Best for: Complex workflows with branching, loops                     │
│                                                                             │
│  LangChain (Already Integrated)                                            │
│  ├── Tool calling                                                          │
│  ├── RAG pipelines                                                         │
│  ├── Chain composition                                                     │
│  └── Best for: Document processing, retrieval tasks                        │
│                                                                             │
│  n8n (Already Integrated)                                                  │
│  ├── Visual workflow automation                                            │
│  ├── External service webhooks                                             │
│  ├── Scheduled tasks                                                       │
│  └── Best for: External integrations, scheduled jobs, notifications        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. AutoGen Integration

### Purpose
Microsoft's AutoGen excels at **complex multi-agent conversations** where agents debate, review code, and iterate on solutions.

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOGEN INTEGRATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 GROUP CHAT MANAGER                       │   │
│  │  Coordinates conversation between multiple agents        │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│          ┌───────────────┼───────────────┐                     │
│          ▼               ▼               ▼                     │
│  ┌───────────────┐ ┌───────────┐ ┌───────────────┐            │
│  │  Architect    │ │  Coder    │ │   Reviewer    │            │
│  │   Agent       │ │  Agent    │ │    Agent      │            │
│  │               │ │           │ │               │            │
│  │ • Design      │ │ • Write   │ │ • Review      │            │
│  │ • Plan        │ │ • Debug   │ │ • Approve     │            │
│  │ • Structure   │ │ • Refactor│ │ • Reject      │            │
│  └───────────────┘ └─────┬─────┘ └───────────────┘            │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CODE EXECUTOR (Docker Sandbox)              │   │
│  │  Safe execution environment for generated code           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

**File: `src/agents/autogen_integration.py`**

```python
"""
AutoGen Integration for AI Project Synthesizer

Provides multi-agent conversation capabilities for complex
code generation, review, and iteration workflows.
"""

import logging
from typing import Any, Optional
from dataclasses import dataclass, field

# AutoGen imports
try:
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    from autogen.coding import DockerCommandLineCodeExecutor
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

from src.core.config import get_settings
from src.llm.router import LLMRouter

logger = logging.getLogger(__name__)


@dataclass
class AutoGenConfig:
    """Configuration for AutoGen agents."""
    
    max_consecutive_auto_reply: int = 10
    human_input_mode: str = "NEVER"  # NEVER, TERMINATE, ALWAYS
    code_execution_config: dict = field(default_factory=lambda: {
        "work_dir": "workspace",
        "use_docker": True,
    })
    llm_config: dict = field(default_factory=dict)


class AutoGenOrchestrator:
    """
    Orchestrates AutoGen multi-agent conversations.
    
    Use cases:
    - Complex code generation with review cycles
    - Architecture design discussions
    - Code refactoring with multiple perspectives
    """
    
    def __init__(self, config: Optional[AutoGenConfig] = None):
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen not installed. Run: pip install pyautogen")
        
        self.config = config or AutoGenConfig()
        self.settings = get_settings()
        self.llm_router = LLMRouter()
        self._setup_llm_config()
        self._create_agents()
    
    def _setup_llm_config(self) -> None:
        """Configure LLM for AutoGen agents."""
        # Use cloud LLM for reasoning-heavy tasks
        self.config.llm_config = {
            "config_list": [
                {
                    "model": self.settings.reasoning_model or "claude-sonnet-4-20250514",
                    "api_key": self.settings.anthropic_api_key,
                    "api_type": "anthropic",
                },
                {
                    "model": "gpt-4o",
                    "api_key": self.settings.openai_api_key,
                },
                # Fallback to local Ollama
                {
                    "model": self.settings.ollama_model or "llama3.1:8b",
                    "base_url": self.settings.ollama_base_url,
                    "api_type": "ollama",
                },
            ],
            "temperature": 0.7,
            "timeout": 120,
        }
    
    def _create_agents(self) -> None:
        """Initialize the agent team."""
        
        # Architect Agent - Designs system structure
        self.architect = AssistantAgent(
            name="Architect",
            system_message="""You are a senior software architect.
            Your role:
            - Design system architecture and structure
            - Define interfaces and contracts
            - Make technology decisions
            - Create high-level plans
            
            Always explain your architectural decisions clearly.""",
            llm_config=self.config.llm_config,
        )
        
        # Coder Agent - Writes implementation
        self.coder = AssistantAgent(
            name="Coder",
            system_message="""You are an expert software developer.
            Your role:
            - Write clean, production-ready code
            - Follow the architect's design
            - Implement features completely
            - Handle edge cases and errors
            
            Always write complete, working code - no placeholders.""",
            llm_config=self.config.llm_config,
        )
        
        # Reviewer Agent - Reviews and approves
        self.reviewer = AssistantAgent(
            name="Reviewer",
            system_message="""You are a thorough code reviewer.
            Your role:
            - Review code for bugs and issues
            - Check for security vulnerabilities
            - Ensure best practices
            - Approve or request changes
            
            Be constructive but thorough in reviews.""",
            llm_config=self.config.llm_config,
        )
        
        # Executor Agent - Runs code in sandbox
        self.executor = UserProxyAgent(
            name="Executor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=self.config.max_consecutive_auto_reply,
            code_execution_config=self.config.code_execution_config,
        )
    
    async def design_and_build(
        self,
        task_description: str,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Full design → code → review → execute cycle.
        
        Args:
            task_description: Natural language task description
            context: Additional context (existing code, requirements, etc.)
        
        Returns:
            Result with generated code, review notes, execution output
        """
        # Create group chat for collaboration
        group_chat = GroupChat(
            agents=[self.architect, self.coder, self.reviewer, self.executor],
            messages=[],
            max_round=20,
            speaker_selection_method="round_robin",
        )
        
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self.config.llm_config,
        )
        
        # Format initial message
        initial_message = f"""
        TASK: {task_description}
        
        CONTEXT:
        {context or 'No additional context provided.'}
        
        WORKFLOW:
        1. Architect: Design the solution structure
        2. Coder: Implement the solution
        3. Reviewer: Review the code
        4. Executor: Run and verify the code
        
        Let's begin with the architecture design.
        """
        
        # Start the conversation
        result = await self.executor.a_initiate_chat(
            manager,
            message=initial_message,
        )
        
        return {
            "success": True,
            "messages": group_chat.messages,
            "result": result,
        }
```

### AutoGen Use Cases

| Scenario | Agent Team | Workflow |
|----------|-----------|----------|
| New Feature | Architect → Coder → Reviewer | Design, implement, review |
| Bug Fix | Debugger → Coder → Tester | Diagnose, fix, verify |
| Refactor | Architect → Coder → Reviewer | Plan, refactor, review |
| Security Audit | Security → Reviewer | Scan, report, recommend |

---

## 2. OpenAI Swarm Integration

### Purpose
Lightweight agent handoffs for **quick task delegation** and **simple pipelines**.

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    SWARM INTEGRATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Request                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────┐                                               │
│  │   Triage    │──── Classify intent                           │
│  │   Agent     │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│    ┌────┴────┬────────┬────────┬────────┐                     │
│    ▼         ▼        ▼        ▼        ▼                     │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                 │
│ │ Code │ │ Test │ │ Doc  │ │Deploy│ │ Help │                 │
│ │Agent │ │Agent │ │Agent │ │Agent │ │Agent │                 │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                 │
│                                                                 │
│  Handoff: Agent returns control to next agent                  │
│  Context: Shared state passed between agents                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

**File: `src/agents/swarm_integration.py`**

```python
"""
OpenAI Swarm Integration for AI Project Synthesizer

Provides lightweight agent handoffs for quick task delegation.
Swarm is ideal for simple, fast agent routing without heavy orchestration.
"""

import logging
from typing import Any, Callable, Optional
from dataclasses import dataclass

# Swarm imports
try:
    from swarm import Swarm, Agent
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False

from src.core.config import get_settings
from src.llm.router import LLMRouter

logger = logging.getLogger(__name__)


def transfer_to_code_agent():
    """Transfer control to the code agent."""
    return code_agent


def transfer_to_test_agent():
    """Transfer control to the test agent."""
    return test_agent


def transfer_to_deploy_agent():
    """Transfer control to the deploy agent."""
    return deploy_agent


def transfer_to_docs_agent():
    """Transfer control to the docs agent."""
    return docs_agent


# Define Agents with handoff functions
triage_agent = Agent(
    name="Triage Agent",
    instructions="""You are a helpful triage agent.
    Analyze the user's request and route to the appropriate specialist:
    - Code requests → transfer to Code Agent
    - Testing requests → transfer to Test Agent  
    - Deployment requests → transfer to Deploy Agent
    - Documentation requests → transfer to Docs Agent
    """,
    functions=[
        transfer_to_code_agent,
        transfer_to_test_agent,
        transfer_to_deploy_agent,
        transfer_to_docs_agent,
    ],
)

code_agent = Agent(
    name="Code Agent",
    instructions="""You are an expert programmer.
    Write clean, production-ready code.
    After completing, you can hand off to Test Agent for verification.""",
    functions=[transfer_to_test_agent],
)

test_agent = Agent(
    name="Test Agent",
    instructions="""You are a testing expert.
    Write and run tests for the code.
    If tests pass, hand off to Deploy Agent.
    If tests fail, hand off back to Code Agent.""",
    functions=[transfer_to_code_agent, transfer_to_deploy_agent],
)

deploy_agent = Agent(
    name="Deploy Agent",
    instructions="""You are a DevOps expert.
    Handle deployment tasks:
    - Docker containerization
    - CI/CD configuration
    - Cloud deployment
    After deployment, hand off to Docs Agent.""",
    functions=[transfer_to_docs_agent],
)

docs_agent = Agent(
    name="Docs Agent",
    instructions="""You are a technical writer.
    Generate documentation:
    - README files
    - API documentation
    - User guides
    This is typically the final step.""",
)


class SwarmOrchestrator:
    """
    Orchestrates OpenAI Swarm agent handoffs.
    
    Use cases:
    - Quick task routing
    - Simple multi-step pipelines
    - Fast context switching between specialists
    """
    
    def __init__(self):
        if not SWARM_AVAILABLE:
            raise ImportError("Swarm not installed. Run: pip install openai-swarm")
        
        self.client = Swarm()
        self.settings = get_settings()
    
    async def run(
        self,
        user_message: str,
        context_variables: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Run the swarm with automatic agent handoffs.
        
        Args:
            user_message: User's request
            context_variables: Shared state between agents
        
        Returns:
            Final response and execution trace
        """
        context = context_variables or {}
        
        response = self.client.run(
            agent=triage_agent,
            messages=[{"role": "user", "content": user_message}],
            context_variables=context,
        )
        
        return {
            "success": True,
            "response": response.messages[-1]["content"],
            "agent": response.agent.name,
            "context": response.context_variables,
        }
```

---

## 3. LangGraph Integration

### Purpose
**Stateful workflows** with cycles, branches, and persistent state. Perfect for complex multi-step processes.

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│              ┌─────────────┐                                   │
│              │    START    │                                   │
│              └──────┬──────┘                                   │
│                     │                                          │
│                     ▼                                          │
│              ┌─────────────┐                                   │
│         ┌────│   ANALYZE   │────┐                              │
│         │    └─────────────┘    │                              │
│         │                       │                              │
│    (simple)                (complex)                           │
│         │                       │                              │
│         ▼                       ▼                              │
│  ┌─────────────┐        ┌─────────────┐                       │
│  │QUICK BUILD  │        │   DESIGN    │                       │
│  └──────┬──────┘        └──────┬──────┘                       │
│         │                      │                               │
│         │                      ▼                               │
│         │               ┌─────────────┐                       │
│         │               │   IMPLEMENT │◄───┐                  │
│         │               └──────┬──────┘    │                  │
│         │                      │           │                   │
│         │                      ▼           │                   │
│         │               ┌─────────────┐    │                  │
│         │               │    TEST     │    │                  │
│         │               └──────┬──────┘    │                  │
│         │                      │           │                   │
│         │              (pass)  │  (fail)   │                  │
│         │                 ┌────┴────┐      │                  │
│         │                 │         │      │                  │
│         │                 ▼         └──────┘                  │
│         │          ┌─────────────┐                            │
│         └─────────►│   DEPLOY    │                            │
│                    └──────┬──────┘                            │
│                           │                                    │
│                           ▼                                    │
│                    ┌─────────────┐                            │
│                    │     END     │                            │
│                    └─────────────┘                            │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

**File: `src/agents/langgraph_integration.py`**

```python
"""
LangGraph Integration for AI Project Synthesizer

Provides stateful workflow orchestration with cycles and branches.
Ideal for complex multi-step processes that need persistent state.
"""

import logging
from typing import Any, TypedDict, Annotated, Literal
from dataclasses import dataclass

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State shared across all workflow nodes."""
    
    messages: list  # Conversation history
    task: str  # Current task description
    complexity: str  # "simple" or "complex"
    code: str  # Generated code
    tests: str  # Generated tests
    test_results: str  # Test execution results
    deployment_status: str  # Deployment status
    iteration: int  # Current iteration count
    max_iterations: int  # Max retries before failing


class LangGraphOrchestrator:
    """
    Orchestrates LangGraph stateful workflows.
    
    Use cases:
    - Complex multi-step build processes
    - Workflows with retry loops
    - State persistence across sessions
    """
    
    def __init__(self, checkpoint_path: str = "data/langgraph_checkpoints.db"):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not installed. Run: pip install langgraph")
        
        self.settings = get_settings()
        self.checkpoint_path = checkpoint_path
        self._setup_llm()
        self._build_graph()
    
    def _setup_llm(self) -> None:
        """Configure LLM for workflow nodes."""
        # Use Claude for complex reasoning
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=self.settings.anthropic_api_key,
        )
        
        # Fallback to OpenAI
        self.llm_fallback = ChatOpenAI(
            model="gpt-4o",
            api_key=self.settings.openai_api_key,
        )
    
    def _analyze_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze task complexity."""
        task = state["task"]
        
        response = self.llm.invoke([
            HumanMessage(content=f"""
            Analyze this development task and determine complexity:
            
            Task: {task}
            
            Respond with ONLY "simple" or "complex".
            
            Simple: Single file, < 100 lines, no external dependencies
            Complex: Multiple files, architecture needed, dependencies
            """)
        ])
        
        complexity = response.content.strip().lower()
        state["complexity"] = complexity if complexity in ["simple", "complex"] else "complex"
        state["messages"].append(AIMessage(content=f"Task complexity: {state['complexity']}"))
        
        return state
    
    def _design_node(self, state: WorkflowState) -> WorkflowState:
        """Design architecture for complex tasks."""
        task = state["task"]
        
        response = self.llm.invoke([
            HumanMessage(content=f"""
            Design the architecture for this task:
            
            Task: {task}
            
            Provide:
            1. File structure
            2. Key components
            3. Data flow
            4. Dependencies needed
            """)
        ])
        
        state["messages"].append(AIMessage(content=f"Architecture:\n{response.content}"))
        return state
    
    def _implement_node(self, state: WorkflowState) -> WorkflowState:
        """Implement the code."""
        task = state["task"]
        context = "\n".join([m.content for m in state["messages"][-5:]])
        
        response = self.llm.invoke([
            HumanMessage(content=f"""
            Implement this task with production-ready code:
            
            Task: {task}
            Context: {context}
            
            Write complete, working code. No placeholders.
            Include error handling and logging.
            """)
        ])
        
        state["code"] = response.content
        state["messages"].append(AIMessage(content=f"Code implemented"))
        return state
    
    def _test_node(self, state: WorkflowState) -> WorkflowState:
        """Generate and run tests."""
        code = state["code"]
        
        # Generate tests
        response = self.llm.invoke([
            HumanMessage(content=f"""
            Write comprehensive tests for this code:
            
            {code}
            
            Use pytest. Cover edge cases.
            """)
        ])
        
        state["tests"] = response.content
        
        # Simulate test execution (in real impl, use subprocess)
        state["test_results"] = "PASS"  # or "FAIL"
        state["iteration"] = state.get("iteration", 0) + 1
        state["messages"].append(AIMessage(content=f"Tests: {state['test_results']}"))
        
        return state
    
    def _deploy_node(self, state: WorkflowState) -> WorkflowState:
        """Deploy the code."""
        state["deployment_status"] = "DEPLOYED"
        state["messages"].append(AIMessage(content="Deployment complete"))
        return state
    
    def _route_complexity(self, state: WorkflowState) -> Literal["quick_build", "design"]:
        """Route based on complexity."""
        return "quick_build" if state["complexity"] == "simple" else "design"
    
    def _route_tests(self, state: WorkflowState) -> Literal["deploy", "implement"]:
        """Route based on test results."""
        if state["test_results"] == "PASS":
            return "deploy"
        elif state["iteration"] < state.get("max_iterations", 3):
            return "implement"  # Retry
        else:
            return "deploy"  # Give up, deploy anyway with warning
    
    def _build_graph(self) -> None:
        """Build the workflow graph."""
        graph = StateGraph(WorkflowState)
        
        # Add nodes
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("design", self._design_node)
        graph.add_node("quick_build", self._implement_node)
        graph.add_node("implement", self._implement_node)
        graph.add_node("test", self._test_node)
        graph.add_node("deploy", self._deploy_node)
        
        # Set entry point
        graph.set_entry_point("analyze")
        
        # Add conditional edges
        graph.add_conditional_edges(
            "analyze",
            self._route_complexity,
            {"quick_build": "quick_build", "design": "design"}
        )
        
        graph.add_edge("design", "implement")
        graph.add_edge("quick_build", "test")
        graph.add_edge("implement", "test")
        
        graph.add_conditional_edges(
            "test",
            self._route_tests,
            {"deploy": "deploy", "implement": "implement"}
        )
        
        graph.add_edge("deploy", END)
        
        # Compile with checkpointing
        self.memory = SqliteSaver.from_conn_string(self.checkpoint_path)
        self.graph = graph.compile(checkpointer=self.memory)
    
    async def run(
        self,
        task: str,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            task: Task description
            thread_id: ID for state persistence
        
        Returns:
            Final state with code, tests, deployment status
        """
        initial_state = {
            "messages": [],
            "task": task,
            "complexity": "",
            "code": "",
            "tests": "",
            "test_results": "",
            "deployment_status": "",
            "iteration": 0,
            "max_iterations": 3,
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        final_state = await self.graph.ainvoke(initial_state, config)
        
        return {
            "success": final_state["deployment_status"] == "DEPLOYED",
            "code": final_state["code"],
            "tests": final_state["tests"],
            "iterations": final_state["iteration"],
        }
```

---

## 4. Framework Selection Logic

**File: `src/agents/framework_router.py`**

```python
"""
Framework Router - Selects optimal agent framework for each task.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class Framework(Enum):
    AUTOGEN = "autogen"
    SWARM = "swarm"
    LANGGRAPH = "langgraph"
    LANGCHAIN = "langchain"
    N8N = "n8n"


@dataclass
class TaskAnalysis:
    """Analysis of a task to determine framework."""
    
    complexity: str  # simple, medium, complex
    needs_code_execution: bool
    needs_human_approval: bool
    needs_state_persistence: bool
    needs_external_webhooks: bool
    needs_multi_agent_debate: bool
    estimated_steps: int


class FrameworkRouter:
    """Routes tasks to optimal agent framework."""
    
    def select_framework(self, analysis: TaskAnalysis) -> Framework:
        """
        Select framework based on task characteristics.
        
        Decision tree:
        1. External webhooks/scheduling → n8n
        2. Complex multi-agent debate → AutoGen
        3. Stateful cycles/branches → LangGraph
        4. Simple handoffs → Swarm
        5. RAG/document processing → LangChain
        """
        
        # n8n for external integrations
        if analysis.needs_external_webhooks:
            return Framework.N8N
        
        # AutoGen for complex debates
        if analysis.needs_multi_agent_debate and analysis.needs_code_execution:
            return Framework.AUTOGEN
        
        # LangGraph for stateful workflows
        if analysis.needs_state_persistence or analysis.estimated_steps > 5:
            return Framework.LANGGRAPH
        
        # Swarm for simple routing
        if analysis.complexity == "simple" and analysis.estimated_steps <= 3:
            return Framework.SWARM
        
        # LangChain as default
        return Framework.LANGCHAIN
    
    def get_recommendation(self, task_description: str) -> dict:
        """Get framework recommendation with explanation."""
        # In production, use LLM to analyze task
        # For now, return default recommendation
        
        return {
            "recommended": Framework.LANGGRAPH,
            "reason": "Task appears to need stateful multi-step processing",
            "alternatives": [Framework.AUTOGEN, Framework.SWARM],
        }
```

---

## 5. Unified Agent Interface

**File: `src/agents/unified_interface.py`**

```python
"""
Unified Agent Interface - Single entry point for all frameworks.
"""

from typing import Any, Optional
from src.agents.autogen_integration import AutoGenOrchestrator
from src.agents.swarm_integration import SwarmOrchestrator
from src.agents.langgraph_integration import LangGraphOrchestrator
from src.agents.framework_router import FrameworkRouter, Framework


class UnifiedAgentInterface:
    """
    Single interface to all agent frameworks.
    
    Users don't need to know which framework is used -
    the router selects automatically.
    """
    
    def __init__(self):
        self.router = FrameworkRouter()
        self._orchestrators = {}
    
    def _get_orchestrator(self, framework: Framework):
        """Lazy-load orchestrators."""
        if framework not in self._orchestrators:
            if framework == Framework.AUTOGEN:
                self._orchestrators[framework] = AutoGenOrchestrator()
            elif framework == Framework.SWARM:
                self._orchestrators[framework] = SwarmOrchestrator()
            elif framework == Framework.LANGGRAPH:
                self._orchestrators[framework] = LangGraphOrchestrator()
        
        return self._orchestrators.get(framework)
    
    async def execute(
        self,
        task: str,
        context: Optional[dict] = None,
        force_framework: Optional[Framework] = None,
    ) -> dict[str, Any]:
        """
        Execute a task using the optimal framework.
        
        Args:
            task: Natural language task description
            context: Additional context
            force_framework: Override auto-selection
        
        Returns:
            Execution result
        """
        # Select framework
        if force_framework:
            framework = force_framework
        else:
            recommendation = self.router.get_recommendation(task)
            framework = recommendation["recommended"]
        
        # Get orchestrator
        orchestrator = self._get_orchestrator(framework)
        
        # Execute
        if framework == Framework.AUTOGEN:
            return await orchestrator.design_and_build(task, context)
        elif framework == Framework.SWARM:
            return await orchestrator.run(task, context)
        elif framework == Framework.LANGGRAPH:
            return await orchestrator.run(task)
        
        return {"error": f"Framework {framework} not implemented"}
```

---

## Dependencies to Add

```toml
# pyproject.toml additions

[project.optional-dependencies]
agents = [
    "pyautogen>=0.2.0",      # Microsoft AutoGen
    "openai-swarm>=0.1.0",    # OpenAI Swarm (when released)
    "langgraph>=0.0.40",      # LangGraph
    "langchain>=0.1.0",       # LangChain (already present)
    "langchain-anthropic",    # Claude integration
    "langchain-openai",       # OpenAI integration
]
```

---

## Next Document

See **[CLI_AUTOMATION_SPEC.md](./CLI_AUTOMATION_SPEC.md)** for how agents execute shell commands.
