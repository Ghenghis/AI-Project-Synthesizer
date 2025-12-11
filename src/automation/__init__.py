"""
AI Project Synthesizer - Automation System

Complete automation framework with:
- n8n workflow orchestration
- Timing metrics (ms between actions)
- Integrated testing
- Seamless coordination
"""

from src.automation.coordinator import AutomationCoordinator
from src.automation.metrics import MetricsCollector, ActionTimer
from src.automation.testing import IntegrationTester

__all__ = [
    "AutomationCoordinator",
    "MetricsCollector",
    "ActionTimer",
    "IntegrationTester",
]
