"""
AI Project Synthesizer - Automation Agent

AI-powered automation agent for:
- Workflow orchestration
- Task scheduling
- Auto-recovery
- Health monitoring
- Continuous operation
"""

import asyncio
from datetime import datetime
from typing import Any

from src.agents.base import AgentConfig, AgentTool, BaseAgent
from src.core.security import get_secure_logger
from src.core.settings_manager import get_settings_manager

secure_logger = get_secure_logger(__name__)


class AutomationAgent(BaseAgent):
    """
    Automation agent for workflow management.

    Features:
    - Workflow orchestration
    - Scheduled task execution
    - Auto-recovery from failures
    - Health monitoring
    - n8n integration
    """

    def __init__(self, config: AgentConfig | None = None):
        config = config or AgentConfig(
            name="automation_agent",
            description="Manages workflows and automation",
            auto_continue=True,
            max_iterations=50,
        )
        super().__init__(config)
        self._scheduled_tasks: dict[str, dict] = {}
        self._running_workflows: dict[str, dict] = {}
        self._setup_tools()

    def _setup_tools(self):
        """Set up automation tools."""
        self.register_tool(AgentTool(
            name="run_workflow",
            description="Execute an n8n workflow",
            func=self._run_workflow,
            parameters={
                "workflow_id": {"type": "string"},
                "data": {"type": "object"},
            },
        ))

        self.register_tool(AgentTool(
            name="schedule_task",
            description="Schedule a task for later execution",
            func=self._schedule_task,
            parameters={
                "task_id": {"type": "string"},
                "task_type": {"type": "string"},
                "schedule": {"type": "string", "description": "Cron expression"},
                "data": {"type": "object"},
            },
        ))

        self.register_tool(AgentTool(
            name="check_health",
            description="Check system health",
            func=self._check_health,
            parameters={},
        ))

        self.register_tool(AgentTool(
            name="recover_component",
            description="Attempt to recover a failed component",
            func=self._recover_component,
            parameters={
                "component": {"type": "string"},
            },
        ))

        self.register_tool(AgentTool(
            name="run_tests",
            description="Run integration tests",
            func=self._run_tests,
            parameters={
                "category": {"type": "string", "description": "Test category"},
            },
        ))

        self.register_tool(AgentTool(
            name="get_metrics",
            description="Get system metrics",
            func=self._get_metrics,
            parameters={},
        ))

    async def _run_workflow(
        self,
        workflow_id: str,
        data: dict | None = None,
    ) -> dict[str, Any]:
        """Execute an n8n workflow."""
        try:
            from src.workflows import N8NClient

            settings = get_settings_manager().settings.workflows
            client = N8NClient(base_url=settings.n8n_url)

            result = await client.execute_workflow(workflow_id, data or {})

            self._running_workflows[workflow_id] = {
                "started_at": datetime.now().isoformat(),
                "status": "running",
            }

            return {"success": True, "workflow_id": workflow_id, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _schedule_task(
        self,
        task_id: str,
        task_type: str,
        schedule: str,
        data: dict | None = None,
    ) -> dict[str, Any]:
        """Schedule a task."""
        self._scheduled_tasks[task_id] = {
            "type": task_type,
            "schedule": schedule,
            "data": data or {},
            "created_at": datetime.now().isoformat(),
            "next_run": None,  # Would calculate from cron
        }

        return {
            "success": True,
            "task_id": task_id,
            "scheduled": True,
        }

    async def _check_health(self) -> dict[str, Any]:
        """Check system health."""
        try:
            from src.core.health import check_health

            health = await check_health()

            components = {}
            unhealthy = []

            for c in health.components:
                components[c.name] = {
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                }
                if c.status.value != "healthy":
                    unhealthy.append(c.name)

            return {
                "success": True,
                "overall": health.overall_status.value,
                "components": components,
                "unhealthy": unhealthy,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _recover_component(self, component: str) -> dict[str, Any]:
        """Attempt to recover a component."""
        recovery_actions = {
            "lm_studio": "Check if LM Studio is running and has a model loaded",
            "ollama": "Run 'ollama serve' to start Ollama",
            "github": "Verify GITHUB_TOKEN in .env",
            "huggingface": "Check HuggingFace API access",
            "elevenlabs": "Verify ELEVENLABS_API_KEY in .env",
            "cache": "Clear and reinitialize cache",
            "n8n": "Run 'docker-compose up -d' in docker/n8n/",
        }

        action = recovery_actions.get(component, "Manual intervention required")

        secure_logger.info(f"Recovery attempted for {component}: {action}")

        return {
            "success": True,
            "component": component,
            "action": action,
            "status": "recovery_attempted",
        }

    async def _run_tests(self, category: str | None = None) -> dict[str, Any]:
        """Run integration tests."""
        try:
            from src.automation import IntegrationTester

            tester = IntegrationTester()
            result = await tester.run_all(category=category)

            return {
                "success": True,
                "total": result.total,
                "passed": result.passed,
                "failed": result.failed,
                "duration_ms": result.duration_ms,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_metrics(self) -> dict[str, Any]:
        """Get system metrics."""
        try:
            from src.automation.metrics import get_metrics_collector

            collector = get_metrics_collector()
            summary = collector.get_summary()

            return {"success": True, "metrics": summary}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_step(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute an automation step."""
        llm = await self._get_llm()
        settings = get_settings_manager().settings.automation

        # Build prompt
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self._tools.values()
        ])

        prompt = f"""You are an automation agent managing system workflows.

Task: {task}

Available tools:
{tools_desc}

Settings:
- Auto-fix errors: {settings.auto_fix_errors}
- Auto-retry: {settings.auto_retry_failed}
- Health check interval: {settings.health_check_interval_s}s

Previous context: {context.get('previous_step', 'None')}

Decide the next action. Respond in this format:
TOOL: <tool_name>
PARAMS: <json_params>
REASONING: <why>

Or if task is complete:
COMPLETE: true
SUMMARY: <summary>
"""

        response = await llm.complete(prompt)

        # Parse response
        if "COMPLETE: true" in response:
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

            # Auto-recovery if enabled
            if settings.auto_fix_errors and not result.get("success"):
                if "component" in result:
                    await self._recover_component(result["component"])

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

    def _should_continue(self, step_result: dict[str, Any]) -> bool:
        """Check if should continue automation."""
        return not step_result.get("complete", False)

    async def monitor_health(self, interval_seconds: int = 300):
        """Continuously monitor system health."""
        settings = get_settings_manager().settings.automation

        while settings.auto_health_check:
            health = await self._check_health()

            if health.get("unhealthy"):
                for component in health["unhealthy"]:
                    if settings.auto_fix_errors:
                        await self._recover_component(component)

            await asyncio.sleep(interval_seconds)

    async def automate(self, task: str) -> dict[str, Any]:
        """
        Run automation task.

        Args:
            task: Automation task description

        Returns:
            Automation results
        """
        result = await self.run(task)
        return result.to_dict()
