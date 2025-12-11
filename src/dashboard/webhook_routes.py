"""
AI Project Synthesizer - Webhook API Routes

Webhook endpoints for external integrations:
- GitHub webhooks
- n8n webhooks
- Custom webhooks
- Slack/Discord notifications
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Header
import json

from src.core.realtime import get_event_bus, EventType, emit_notification
from src.core.memory import get_memory_store, MemoryEntry, MemoryType
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# ============================================
# GitHub Webhooks
# ============================================

@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
):
    """
    Handle GitHub webhooks.

    Supported events:
    - push: Code pushed to repository
    - pull_request: PR opened/closed/merged
    - issues: Issue opened/closed
    - release: New release published
    - star: Repository starred
    """
    body = await request.body()
    payload = json.loads(body)

    event_type = x_github_event or "unknown"

    secure_logger.info(f"GitHub webhook received: {event_type}")

    # Emit real-time event
    bus = get_event_bus()

    if event_type == "push":
        commits = payload.get("commits", [])
        repo = payload.get("repository", {}).get("full_name", "unknown")

        await bus.emit_async(EventType.NOTIFICATION, {
            "title": "GitHub Push",
            "message": f"{len(commits)} commit(s) pushed to {repo}",
            "level": "info",
            "source": "github",
        })

    elif event_type == "pull_request":
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        title = pr.get("title", "")

        await bus.emit_async(EventType.NOTIFICATION, {
            "title": f"PR {action.title()}",
            "message": title,
            "level": "info",
            "source": "github",
        })

    elif event_type == "release":
        action = payload.get("action", "")
        release = payload.get("release", {})
        tag = release.get("tag_name", "")

        await bus.emit_async(EventType.NOTIFICATION, {
            "title": "New Release",
            "message": f"Version {tag} released",
            "level": "success",
            "source": "github",
        })

    elif event_type == "star":
        action = payload.get("action", "")
        repo = payload.get("repository", {}).get("full_name", "")

        if action == "created":
            await bus.emit_async(EventType.NOTIFICATION, {
                "title": "New Star",
                "message": f"{repo} was starred",
                "level": "info",
                "source": "github",
            })

    # Save to memory
    store = get_memory_store()
    store.save_memory(MemoryEntry(
        id=f"gh_{datetime.now().timestamp()}",
        type=MemoryType.WORKFLOW,
        content={
            "event": event_type,
            "payload_summary": {
                "repo": payload.get("repository", {}).get("full_name"),
                "sender": payload.get("sender", {}).get("login"),
            },
        },
        tags=["github", event_type],
    ))

    return {"status": "received", "event": event_type}


# ============================================
# n8n Webhooks
# ============================================

@router.post("/n8n/{workflow_name}")
async def n8n_webhook(workflow_name: str, request: Request):
    """
    Handle n8n workflow callbacks.

    Used for:
    - Workflow completion notifications
    - Error reporting
    - Status updates
    """
    body = await request.json()

    secure_logger.info(f"n8n webhook received: {workflow_name}")

    bus = get_event_bus()

    status = body.get("status", "unknown")

    if status == "completed":
        await bus.emit_async(EventType.WORKFLOW_COMPLETED, {
            "workflow": workflow_name,
            "result": body.get("result"),
            "duration_ms": body.get("duration_ms"),
        })

    elif status == "failed":
        await bus.emit_async(EventType.WORKFLOW_FAILED, {
            "workflow": workflow_name,
            "error": body.get("error"),
        })

    elif status == "progress":
        await bus.emit_async(EventType.WORKFLOW_PROGRESS, {
            "workflow": workflow_name,
            "progress": body.get("progress"),
            "message": body.get("message"),
        })

    return {"status": "received", "workflow": workflow_name}


# ============================================
# Custom Webhooks
# ============================================

@router.post("/custom/{hook_id}")
async def custom_webhook(hook_id: str, request: Request):
    """
    Handle custom webhooks.

    Can be used for:
    - CI/CD notifications
    - Monitoring alerts
    - External service callbacks
    """
    body = await request.json()

    secure_logger.info(f"Custom webhook received: {hook_id}")

    bus = get_event_bus()

    # Emit as notification
    await bus.emit_async(EventType.NOTIFICATION, {
        "title": f"Webhook: {hook_id}",
        "message": body.get("message", "Webhook received"),
        "level": body.get("level", "info"),
        "source": hook_id,
        "data": body,
    })

    # Save to memory
    store = get_memory_store()
    store.save_memory(MemoryEntry(
        id=f"hook_{datetime.now().timestamp()}",
        type=MemoryType.WORKFLOW,
        content=body,
        tags=["webhook", hook_id],
    ))

    return {"status": "received", "hook_id": hook_id}


# ============================================
# Slack Integration
# ============================================

@router.post("/slack")
async def slack_webhook(request: Request):
    """
    Handle Slack webhooks (slash commands, events).
    """
    form = await request.form()

    # Slash command
    if "command" in form:
        command = form.get("command", "")
        text = form.get("text", "")
        user = form.get("user_name", "")

        secure_logger.info(f"Slack command: {command} {text} from {user}")

        # Process command
        if command == "/synth-search":
            # Trigger search
            return {
                "response_type": "in_channel",
                "text": f"🔍 Searching for: {text}",
            }

        elif command == "/synth-status":
            # Get status
            return {
                "response_type": "ephemeral",
                "text": "✅ AI Synthesizer is running",
            }

    return {"status": "received"}


# ============================================
# Discord Integration
# ============================================

@router.post("/discord")
async def discord_webhook(request: Request):
    """
    Handle Discord webhooks (interactions).
    """
    body = await request.json()

    # Verify Discord signature would go here

    interaction_type = body.get("type", 0)

    # Ping
    if interaction_type == 1:
        return {"type": 1}

    # Application command
    if interaction_type == 2:
        data = body.get("data", {})
        command_name = data.get("name", "")

        secure_logger.info(f"Discord command: {command_name}")

        if command_name == "search":
            query = data.get("options", [{}])[0].get("value", "")
            return {
                "type": 4,
                "data": {
                    "content": f"🔍 Searching for: {query}",
                },
            }

    return {"status": "received"}


# ============================================
# Webhook Management
# ============================================

@router.get("/list")
async def list_webhooks():
    """List available webhook endpoints."""
    return {
        "webhooks": [
            {
                "name": "GitHub",
                "path": "/api/webhooks/github",
                "method": "POST",
                "description": "GitHub repository events",
            },
            {
                "name": "n8n",
                "path": "/api/webhooks/n8n/{workflow_name}",
                "method": "POST",
                "description": "n8n workflow callbacks",
            },
            {
                "name": "Custom",
                "path": "/api/webhooks/custom/{hook_id}",
                "method": "POST",
                "description": "Custom webhook endpoint",
            },
            {
                "name": "Slack",
                "path": "/api/webhooks/slack",
                "method": "POST",
                "description": "Slack slash commands",
            },
            {
                "name": "Discord",
                "path": "/api/webhooks/discord",
                "method": "POST",
                "description": "Discord interactions",
            },
        ]
    }


@router.post("/test")
async def test_webhook(data: Dict[str, Any]):
    """Test webhook endpoint for debugging."""
    secure_logger.info(f"Test webhook received: {data}")

    emit_notification(
        "Test Webhook",
        f"Received: {json.dumps(data)[:100]}",
        "info"
    )

    return {
        "status": "received",
        "echo": data,
        "timestamp": datetime.now().isoformat(),
    }
