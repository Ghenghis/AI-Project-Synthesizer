"""
AI Project Synthesizer - Agent System

AI/ML-powered agents for automated tasks:
- Research Agent: Discovers and analyzes resources
- Synthesis Agent: Assembles projects
- Voice Agent: Handles voice interactions
- Automation Agent: Manages workflows
- Code Agent: Generates and fixes code
"""

from src.agents.automation_agent import AutomationAgent
from src.agents.base import AgentConfig, AgentResult, BaseAgent
from src.agents.code_agent import CodeAgent
from src.agents.research_agent import ResearchAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.agents.voice_agent import VoiceAgent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentResult",
    "ResearchAgent",
    "SynthesisAgent",
    "VoiceAgent",
    "AutomationAgent",
    "CodeAgent",
]
