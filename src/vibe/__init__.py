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

from .prompt_enhancer import PromptEnhancer, EnhancedPrompt, PromptLayer, PromptComplexity
from .rules_engine import RulesEngine, Rule, RuleSet, RuleCategory, RulePriority
from .context_injector import ContextInjector, ProjectContext
from .task_decomposer import TaskDecomposer, TaskPlan, TaskPhase, PhaseType, TaskComplexity
from .context_manager import ContextManager, TaskContext, PhaseState, PhaseStatus, Checkpoint
from .auto_commit import AutoCommit, CommitInfo, CommitConfig, CommitStrategy, CommitStatus
from .architect_agent import ArchitectAgent, ArchitecturePlan, Component, DataFlow, ArchitecturePattern as ArchPattern
from .auto_rollback import AutoRollback, RollbackPoint, RollbackResult, RollbackStrategy, RollbackMode, RollbackStatus
from .explain_mode import ExplainMode, Explanation, ExplanationType, ExplanationLevel
from .project_classifier import ProjectClassifier, ProjectCharacteristics, ProjectType, ComplexityLevel, ArchitecturePattern, TechnologyStack

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
