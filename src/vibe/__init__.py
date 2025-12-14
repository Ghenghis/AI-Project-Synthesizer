"""
VIBE MCP - Vibe Coding Automation

This module implements the Vibe Coding Platform automation features:
- Prompt Engineering Automation
- Structured Process Management
- Quality Pipeline Integration
- Learning & Iteration Features

Components:
- PromptEnhancer: Enhances user prompts with context and constraints
- RulesEngine: Manages and injects coding rules automatically
- ContextInjector: Provides project context for prompts
- TaskDecomposer: Breaks complex requests into structured phases
- ContextManager: Tracks state across phases with persistence
- AutoCommit: Handles Git commits after each phase
- ArchitectAgent: Creates architectural plans before coding
- AutoRollback: Automatically rolls back on phase failures
"""

from .architect_agent import ArchitectAgent
from .architect_agent import ArchitecturePattern as ArchPattern
from .architect_agent import ArchitecturePlan, Component, DataFlow
from .auto_commit import (
    AutoCommit,
    CommitConfig,
    CommitInfo,
    CommitStatus,
    CommitStrategy,
)
from .auto_rollback import (
    AutoRollback,
    RollbackMode,
    RollbackPoint,
    RollbackResult,
    RollbackStatus,
    RollbackStrategy,
)
from .context_injector import ContextInjector, ProjectContext
from .context_manager import (
    Checkpoint,
    ContextManager,
    PhaseState,
    PhaseStatus,
    TaskContext,
)
from .explain_mode import ExplainMode, Explanation, ExplanationLevel, ExplanationType
from .project_classifier import (
    ArchitecturePattern,
    ComplexityLevel,
    ProjectCharacteristics,
    ProjectClassifier,
    ProjectType,
    TechnologyStack,
)
from .prompt_enhancer import (
    EnhancedPrompt,
    PromptComplexity,
    PromptEnhancer,
    PromptLayer,
)
from .rules_engine import Rule, RuleCategory, RulePriority, RulesEngine, RuleSet
from .task_decomposer import (
    PhaseType,
    TaskComplexity,
    TaskDecomposer,
    TaskPhase,
    TaskPlan,
)

__version__ = "1.0.0"
__all__ = [
    # Prompt Engineering
    "PromptEnhancer",
    "EnhancedPrompt",
    "PromptLayer",
    "PromptComplexity",
    # Rules Management
    "RulesEngine",
    "Rule",
    "RuleSet",
    "RuleCategory",
    "RulePriority",
    # Context Injection
    "ContextInjector",
    "ProjectContext",
    # Task Decomposition
    "TaskDecomposer",
    "TaskPlan",
    "TaskPhase",
    "PhaseType",
    "TaskComplexity",
    # Context Management
    "ContextManager",
    "TaskContext",
    "PhaseState",
    "PhaseStatus",
    "Checkpoint",
    # Auto Commit
    "AutoCommit",
    "CommitInfo",
    "CommitConfig",
    "CommitStrategy",
    "CommitStatus",
    # Architecture
    "ArchitectAgent",
    "ArchitecturePlan",
    "Component",
    "DataFlow",
    "ArchPattern",
    # Auto Rollback
    "AutoRollback",
    "RollbackPoint",
    "RollbackResult",
    "RollbackStrategy",
    "RollbackMode",
    "RollbackStatus",
    # Explain Mode
    "ExplainMode",
    "Explanation",
    "ExplanationType",
    "ExplanationLevel",
    # Project Classifier
    "ProjectClassifier",
    "ProjectCharacteristics",
    "ProjectType",
    "ComplexityLevel",
    "ArchitecturePattern",
    "TechnologyStack",
]
