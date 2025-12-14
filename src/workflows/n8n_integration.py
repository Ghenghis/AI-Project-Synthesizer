"""
AI Project Synthesizer - n8n Integration

Local n8n workflow automation for:
- Visual workflow design
- Scheduled tasks
- Webhook triggers
- Multi-step automations

n8n runs locally at http://localhost:5678
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import httpx

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class N8NConfig:
    """n8n connection configuration."""

    base_url: str = "http://localhost:5678"
    api_key: str | None = None
    timeout: int = 30


@dataclass
class N8NWorkflow:
    """Represents an n8n workflow."""

    id: str
    name: str
    active: bool = False
    nodes: list[dict[str, Any]] = field(default_factory=list)
    connections: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "active": self.active,
            "nodes": self.nodes,
            "connections": self.connections,
            "settings": self.settings,
        }


@dataclass
class WorkflowExecution:
    """Workflow execution result."""

    id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    finished_at: datetime | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class N8NClient:
    """
    Client for interacting with local n8n instance.

    Features:
    - Create/manage workflows
    - Execute workflows via API
    - Webhook integration
    - Workflow templates for common tasks

    Usage:
        client = N8NClient()

        # Check connection
        if await client.health_check():
            # List workflows
            workflows = await client.list_workflows()

            # Execute a workflow
            result = await client.execute_workflow("workflow-id", {"input": "data"})
    """

    def __init__(self, config: N8NConfig | None = None):
        """Initialize n8n client."""
        self.config = config or N8NConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["X-N8N-API-KEY"] = self.config.api_key

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if n8n is running."""
        try:
            client = await self._get_client()
            response = await client.get("/healthz")
            return response.status_code == 200
        except Exception as e:
            secure_logger.debug(f"n8n health check failed: {e}")
            return False

    async def list_workflows(self) -> list[N8NWorkflow]:
        """List all workflows."""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/workflows")

            if response.status_code == 200:
                data = response.json()
                return [
                    N8NWorkflow(
                        id=w["id"],
                        name=w["name"],
                        active=w.get("active", False),
                        nodes=w.get("nodes", []),
                        connections=w.get("connections", {}),
                    )
                    for w in data.get("data", [])
                ]
        except Exception as e:
            secure_logger.error(f"Failed to list workflows: {e}")

        return []

    async def get_workflow(self, workflow_id: str) -> N8NWorkflow | None:
        """Get a specific workflow."""
        try:
            client = await self._get_client()
            response = await client.get(f"/api/v1/workflows/{workflow_id}")

            if response.status_code == 200:
                w = response.json()
                return N8NWorkflow(
                    id=w["id"],
                    name=w["name"],
                    active=w.get("active", False),
                    nodes=w.get("nodes", []),
                    connections=w.get("connections", {}),
                )
        except Exception as e:
            secure_logger.error(f"Failed to get workflow: {e}")

        return None

    async def create_workflow(self, workflow: N8NWorkflow) -> str | None:
        """Create a new workflow."""
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/v1/workflows",
                json=workflow.to_dict(),
            )

            if response.status_code in (200, 201):
                data = response.json()
                return data.get("id")
        except Exception as e:
            secure_logger.error(f"Failed to create workflow: {e}")

        return None

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict[str, Any] = None,
    ) -> WorkflowExecution | None:
        """Execute a workflow."""
        try:
            client = await self._get_client()
            response = await client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                json={"data": input_data or {}},
            )

            if response.status_code == 200:
                data = response.json()
                return WorkflowExecution(
                    id=data.get("executionId", ""),
                    workflow_id=workflow_id,
                    status=WorkflowStatus.SUCCESS,
                    started_at=datetime.now(),
                    finished_at=datetime.now(),
                    data=data.get("data", {}),
                )
        except Exception as e:
            secure_logger.error(f"Failed to execute workflow: {e}")
            return WorkflowExecution(
                id="",
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                started_at=datetime.now(),
                error=str(e),
            )

        return None

    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow."""
        try:
            client = await self._get_client()
            response = await client.patch(
                f"/api/v1/workflows/{workflow_id}",
                json={"active": True},
            )
            return response.status_code == 200
        except Exception as e:
            secure_logger.error(f"Failed to activate workflow: {e}")
            return False

    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow."""
        try:
            client = await self._get_client()
            response = await client.patch(
                f"/api/v1/workflows/{workflow_id}",
                json={"active": False},
            )
            return response.status_code == 200
        except Exception as e:
            secure_logger.error(f"Failed to deactivate workflow: {e}")
            return False


class N8NWorkflowTemplates:
    """
    Pre-built n8n workflow templates for common tasks.

    Templates:
    - Project research workflow
    - Scheduled search workflow
    - Webhook trigger workflow
    - Notification workflow
    """

    @staticmethod
    def research_workflow(name: str = "Project Research") -> N8NWorkflow:
        """
        Create a research workflow template.

        Trigger → Search GitHub → Search HuggingFace → Merge Results → Notify
        """
        return N8NWorkflow(
            id="",
            name=name,
            nodes=[
                {
                    "id": "trigger",
                    "type": "n8n-nodes-base.manualTrigger",
                    "position": [250, 300],
                    "parameters": {},
                },
                {
                    "id": "github_search",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 200],
                    "parameters": {
                        "url": "http://localhost:8000/api/search",
                        "method": "POST",
                        "body": {
                            "query": "={{ $json.query }}",
                            "platforms": ["github"],
                        },
                    },
                },
                {
                    "id": "hf_search",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 400],
                    "parameters": {
                        "url": "http://localhost:8000/api/search",
                        "method": "POST",
                        "body": {
                            "query": "={{ $json.query }}",
                            "platforms": ["huggingface"],
                        },
                    },
                },
                {
                    "id": "merge",
                    "type": "n8n-nodes-base.merge",
                    "position": [650, 300],
                    "parameters": {"mode": "append"},
                },
                {
                    "id": "output",
                    "type": "n8n-nodes-base.set",
                    "position": [850, 300],
                    "parameters": {
                        "values": {
                            "string": [
                                {"name": "results", "value": "={{ $json }}"},
                            ],
                        },
                    },
                },
            ],
            connections={
                "trigger": {
                    "main": [[{"node": "github_search"}, {"node": "hf_search"}]]
                },
                "github_search": {"main": [[{"node": "merge"}]]},
                "hf_search": {"main": [[{"node": "merge"}]]},
                "merge": {"main": [[{"node": "output"}]]},
            },
        )

    @staticmethod
    def scheduled_search_workflow(
        name: str = "Scheduled Search",
        cron: str = "0 9 * * *",  # Daily at 9 AM
        query: str = "machine learning",
    ) -> N8NWorkflow:
        """
        Create a scheduled search workflow.

        Cron Trigger → Search → Save Results → Notify
        """
        return N8NWorkflow(
            id="",
            name=name,
            nodes=[
                {
                    "id": "cron",
                    "type": "n8n-nodes-base.cron",
                    "position": [250, 300],
                    "parameters": {
                        "triggerTimes": {
                            "item": [{"mode": "custom", "cronExpression": cron}]
                        },
                    },
                },
                {
                    "id": "search",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "http://localhost:8000/api/search",
                        "method": "POST",
                        "body": {
                            "query": query,
                            "platforms": ["github", "huggingface"],
                        },
                    },
                },
                {
                    "id": "save",
                    "type": "n8n-nodes-base.writeBinaryFile",
                    "position": [650, 300],
                    "parameters": {
                        "fileName": "search_results_{{$now.format('YYYY-MM-DD')}}.json",
                    },
                },
            ],
            connections={
                "cron": {"main": [[{"node": "search"}]]},
                "search": {"main": [[{"node": "save"}]]},
            },
        )

    @staticmethod
    def webhook_assembly_workflow(name: str = "Webhook Assembly") -> N8NWorkflow:
        """
        Create a webhook-triggered assembly workflow.

        Webhook → Validate → Assemble Project → Notify
        """
        return N8NWorkflow(
            id="",
            name=name,
            nodes=[
                {
                    "id": "webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {
                        "path": "assemble",
                        "httpMethod": "POST",
                    },
                },
                {
                    "id": "validate",
                    "type": "n8n-nodes-base.if",
                    "position": [450, 300],
                    "parameters": {
                        "conditions": {
                            "string": [
                                {
                                    "value1": "={{ $json.idea }}",
                                    "operation": "isNotEmpty",
                                }
                            ],
                        },
                    },
                },
                {
                    "id": "assemble",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 250],
                    "parameters": {
                        "url": "http://localhost:8000/api/assemble",
                        "method": "POST",
                        "body": {"idea": "={{ $json.idea }}"},
                    },
                },
                {
                    "id": "error",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "position": [650, 400],
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": {"error": "Missing 'idea' parameter"},
                        "responseCode": 400,
                    },
                },
                {
                    "id": "success",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "position": [850, 250],
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": "={{ $json }}",
                    },
                },
            ],
            connections={
                "webhook": {"main": [[{"node": "validate"}]]},
                "validate": {
                    "main": [
                        [{"node": "assemble"}],  # true
                        [{"node": "error"}],  # false
                    ],
                },
                "assemble": {"main": [[{"node": "success"}]]},
            },
        )

    @staticmethod
    def voice_notification_workflow(name: str = "Voice Notification") -> N8NWorkflow:
        """
        Create a voice notification workflow.

        Trigger → Generate Speech → Play Audio
        """
        return N8NWorkflow(
            id="",
            name=name,
            nodes=[
                {
                    "id": "trigger",
                    "type": "n8n-nodes-base.manualTrigger",
                    "position": [250, 300],
                    "parameters": {},
                },
                {
                    "id": "speak",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "http://localhost:8000/api/speak",
                        "method": "POST",
                        "body": {
                            "text": "={{ $json.message }}",
                            "voice": "rachel",
                        },
                    },
                },
            ],
            connections={
                "trigger": {"main": [[{"node": "speak"}]]},
            },
        )


async def setup_n8n_workflows(client: N8NClient) -> dict[str, str]:
    """
    Set up default workflows in n8n.

    Returns:
        Dict mapping workflow names to IDs
    """
    templates = N8NWorkflowTemplates()
    workflows = {}

    # Create research workflow
    research = templates.research_workflow()
    research_id = await client.create_workflow(research)
    if research_id:
        workflows["research"] = research_id
        secure_logger.info(f"Created research workflow: {research_id}")

    # Create scheduled search
    scheduled = templates.scheduled_search_workflow()
    scheduled_id = await client.create_workflow(scheduled)
    if scheduled_id:
        workflows["scheduled_search"] = scheduled_id
        secure_logger.info(f"Created scheduled search workflow: {scheduled_id}")

    # Create webhook assembly
    webhook = templates.webhook_assembly_workflow()
    webhook_id = await client.create_workflow(webhook)
    if webhook_id:
        workflows["webhook_assembly"] = webhook_id
        secure_logger.info(f"Created webhook assembly workflow: {webhook_id}")

    return workflows
