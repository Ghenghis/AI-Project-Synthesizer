# 🔗 n8n + AutoGen Bridge

## Overview

This document explains how to connect **n8n** (visual workflow automation) with **AutoGen** (multi-agent conversations) to create powerful hybrid automation pipelines.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        n8n + AUTOGEN INTEGRATION                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         n8n WORKFLOW                                 │    │
│  │                                                                      │    │
│  │  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐      │    │
│  │  │Trigger  │────►│Process  │────►│ AutoGen │────►│ Action  │      │    │
│  │  │(Webhook)│     │  Data   │     │  Node   │     │(Deploy) │      │    │
│  │  └─────────┘     └─────────┘     └─────────┘     └─────────┘      │    │
│  │                                        │                           │    │
│  └────────────────────────────────────────┼───────────────────────────┘    │
│                                           │                                 │
│                                           ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      AUTOGEN ORCHESTRATOR                            │   │
│  │                                                                      │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐       │   │
│  │  │ Architect │  │  Coder    │  │  Tester   │  │  DevOps   │       │   │
│  │  │   Agent   │  │   Agent   │  │   Agent   │  │   Agent   │       │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘       │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                           │                                 │
│                                           ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         RESULTS BACK TO n8n                          │   │
│  │  • Generated code files                                              │   │
│  │  • Test results                                                      │   │
│  │  • Deployment status                                                 │   │
│  │  • Documentation                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Combine n8n + AutoGen?

| n8n Strengths | AutoGen Strengths |
|---------------|-------------------|
| Visual workflow design | Complex AI reasoning |
| External integrations (500+) | Multi-agent collaboration |
| Scheduling & triggers | Code generation |
| Webhook handling | Iterative refinement |
| No-code automation | Human-in-the-loop |

**Together**: Trigger complex AI agent workflows from any external event!

---

## Use Cases

### 1. GitHub Issue → Auto-Implementation
```
GitHub Issue Created
       ↓
  n8n Webhook Trigger
       ↓
  AutoGen Multi-Agent
  (Architect → Coder → Tester)
       ↓
  n8n: Create PR with Solution
       ↓
  n8n: Notify on Slack
```

### 2. Customer Request → Custom Solution
```
Typeform Submission
       ↓
  n8n: Parse Requirements
       ↓
  AutoGen: Design & Build
       ↓
  n8n: Deploy to Customer's Server
       ↓
  n8n: Send Email with Access Link
```

### 3. Scheduled Code Maintenance
```
n8n: Daily Schedule (2 AM)
       ↓
  AutoGen: Security Audit
       ↓
  AutoGen: Update Dependencies
       ↓
  AutoGen: Run Tests
       ↓
  n8n: Send Report to Team
```

---

## Implementation

### 1. AutoGen API Server

**File: `src/automation/autogen_api.py`**

```python
"""
AutoGen API Server - Exposes AutoGen to n8n via HTTP.

Endpoints:
- POST /tasks - Submit task to AutoGen
- GET /tasks/{id} - Get task status
- GET /tasks/{id}/result - Get task result
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.agents.autogen_integration import AutoGenOrchestrator

logger = logging.getLogger(__name__)

app = FastAPI(title="AutoGen Bridge API", version="1.0.0")

# Task storage (use Redis in production)
tasks: dict[str, dict] = {}


class TaskRequest(BaseModel):
    """Request to create a new AutoGen task."""
    
    task_type: str  # design_and_build, debug, refactor
    description: str
    context: Optional[dict] = None
    callback_url: Optional[str] = None  # n8n webhook to call when done


class TaskResponse(BaseModel):
    """Response with task status."""
    
    task_id: str
    status: str  # pending, running, complete, failed
    created_at: str
    result: Optional[dict] = None


@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    Create a new AutoGen task.
    
    The task runs asynchronously. Poll /tasks/{id} for status
    or provide a callback_url to be notified when complete.
    """
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "request": request.dict(),
        "result": None,
    }
    
    # Run task in background
    background_tasks.add_task(
        run_autogen_task,
        task_id,
        request,
    )
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        created_at=tasks[task_id]["created_at"],
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task status and result."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        created_at=task["created_at"],
        result=task["result"],
    )


async def run_autogen_task(task_id: str, request: TaskRequest):
    """Run AutoGen task and update status."""
    try:
        tasks[task_id]["status"] = "running"
        
        orchestrator = AutoGenOrchestrator()
        
        if request.task_type == "design_and_build":
            result = await orchestrator.design_and_build(
                task_description=request.description,
                context=request.context,
            )
        else:
            result = {"error": f"Unknown task type: {request.task_type}"}
        
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = result
        
        # Callback to n8n if provided
        if request.callback_url:
            await send_callback(request.callback_url, tasks[task_id])
            
    except Exception as e:
        logger.exception(f"Task {task_id} failed")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["result"] = {"error": str(e)}


async def send_callback(url: str, data: dict):
    """Send webhook callback to n8n."""
    import httpx
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=data, timeout=30)
        except Exception as e:
            logger.error(f"Callback failed: {e}")
```

### 2. n8n Custom Node (Optional)

**File: `n8n-nodes/AutoGenNode.ts`**

```typescript
import {
    IExecuteFunctions,
    INodeExecutionData,
    INodeType,
    INodeTypeDescription,
} from 'n8n-workflow';

export class AutoGenNode implements INodeType {
    description: INodeTypeDescription = {
        displayName: 'AutoGen',
        name: 'autoGen',
        icon: 'file:autogen.svg',
        group: ['transform'],
        version: 1,
        description: 'Execute AutoGen multi-agent tasks',
        defaults: {
            name: 'AutoGen',
        },
        inputs: ['main'],
        outputs: ['main'],
        properties: [
            {
                displayName: 'Task Type',
                name: 'taskType',
                type: 'options',
                options: [
                    { name: 'Design & Build', value: 'design_and_build' },
                    { name: 'Debug', value: 'debug' },
                    { name: 'Refactor', value: 'refactor' },
                ],
                default: 'design_and_build',
            },
            {
                displayName: 'Description',
                name: 'description',
                type: 'string',
                typeOptions: {
                    rows: 4,
                },
                default: '',
                description: 'Describe what you want AutoGen to do',
            },
            {
                displayName: 'AutoGen API URL',
                name: 'apiUrl',
                type: 'string',
                default: 'http://localhost:8001',
            },
        ],
    };

    async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
        const items = this.getInputData();
        const results: INodeExecutionData[] = [];

        for (let i = 0; i < items.length; i++) {
            const taskType = this.getNodeParameter('taskType', i) as string;
            const description = this.getNodeParameter('description', i) as string;
            const apiUrl = this.getNodeParameter('apiUrl', i) as string;

            // Create task
            const createResponse = await this.helpers.httpRequest({
                method: 'POST',
                url: `${apiUrl}/tasks`,
                body: {
                    task_type: taskType,
                    description: description,
                    context: items[i].json,
                },
            });

            const taskId = createResponse.task_id;

            // Poll for completion
            let task;
            do {
                await new Promise(resolve => setTimeout(resolve, 2000));
                task = await this.helpers.httpRequest({
                    method: 'GET',
                    url: `${apiUrl}/tasks/${taskId}`,
                });
            } while (task.status === 'pending' || task.status === 'running');

            results.push({
                json: task,
            });
        }

        return [results];
    }
}
```

### 3. n8n Workflow Example (JSON)

```json
{
  "name": "GitHub Issue to Code",
  "nodes": [
    {
      "name": "GitHub Trigger",
      "type": "n8n-nodes-base.githubTrigger",
      "parameters": {
        "events": ["issues"],
        "owner": "your-org",
        "repository": "your-repo"
      }
    },
    {
      "name": "Filter New Issues",
      "type": "n8n-nodes-base.filter",
      "parameters": {
        "conditions": {
          "string": [{
            "value1": "={{$json.action}}",
            "operation": "equals",
            "value2": "opened"
          }]
        }
      }
    },
    {
      "name": "Parse Issue",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "return [{ json: { description: $json.issue.title + '\\n' + $json.issue.body } }];"
      }
    },
    {
      "name": "AutoGen",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8001/tasks",
        "body": {
          "task_type": "design_and_build",
          "description": "={{$json.description}}"
        }
      }
    },
    {
      "name": "Wait for Completion",
      "type": "n8n-nodes-base.wait",
      "parameters": {
        "amount": 60,
        "unit": "seconds"
      }
    },
    {
      "name": "Get Result",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://localhost:8001/tasks/={{$json.task_id}}"
      }
    },
    {
      "name": "Create Pull Request",
      "type": "n8n-nodes-base.github",
      "parameters": {
        "operation": "create",
        "resource": "pullRequest",
        "owner": "your-org",
        "repository": "your-repo",
        "title": "Auto-fix: {{$json.request.description}}",
        "body": "Generated by AutoGen agents"
      }
    },
    {
      "name": "Slack Notification",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#dev-notifications",
        "text": "🤖 AutoGen created a PR for issue #{{$json.issue.number}}"
      }
    }
  ],
  "connections": {
    "GitHub Trigger": { "main": [["Filter New Issues"]] },
    "Filter New Issues": { "main": [["Parse Issue"]] },
    "Parse Issue": { "main": [["AutoGen"]] },
    "AutoGen": { "main": [["Wait for Completion"]] },
    "Wait for Completion": { "main": [["Get Result"]] },
    "Get Result": { "main": [["Create Pull Request"]] },
    "Create Pull Request": { "main": [["Slack Notification"]] }
  }
}
```

---

## Docker Compose Setup

```yaml
# docker-compose.automation.yml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - automation

  autogen-api:
    build:
      context: .
      dockerfile: docker/Dockerfile.autogen
    ports:
      - "8001:8001"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - ./workspace:/workspace
    networks:
      - automation

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - automation

volumes:
  n8n_data:
  ollama_data:

networks:
  automation:
    driver: bridge
```

---

## Common n8n + AutoGen Workflows

### Workflow 1: Scheduled Dependency Updates

```
Schedule (Weekly)
     ↓
AutoGen: Check for outdated packages
     ↓
AutoGen: Update & test
     ↓
n8n: Create PR if tests pass
     ↓
n8n: Email report
```

### Workflow 2: Customer Feature Request

```
Typeform/Jotform Submission
     ↓
n8n: Parse & validate request
     ↓
AutoGen: Estimate complexity
     ↓
n8n: If simple, auto-build
     ↓
n8n: Send quote if complex
```

### Workflow 3: Monitoring Alert → Auto-Fix

```
Prometheus Alert
     ↓
n8n: Webhook trigger
     ↓
AutoGen: Debug agent analyzes
     ↓
AutoGen: Coder fixes if possible
     ↓
n8n: Deploy fix
     ↓
n8n: Notify team
```

---

## Best Practices

### 1. Use Callbacks for Long Tasks
```python
# Instead of polling, use callback_url
await client.post("/tasks", json={
    "task_type": "design_and_build",
    "description": "...",
    "callback_url": "https://your-n8n.com/webhook/autogen-complete"
})
```

### 2. Handle Timeouts
```javascript
// n8n: Set reasonable timeouts
const timeout = 300000; // 5 minutes for complex tasks
```

### 3. Error Handling
```javascript
// n8n: Add error handling branches
if ($json.status === 'failed') {
    // Route to error handling workflow
}
```

### 4. Rate Limiting
```python
# Limit concurrent AutoGen tasks
MAX_CONCURRENT_TASKS = 5
```

---

## Summary

| Component | Role |
|-----------|------|
| **n8n** | Visual automation, triggers, external integrations |
| **AutoGen API** | Bridge server exposing AutoGen via HTTP |
| **AutoGen** | Complex multi-agent AI tasks |
| **Ollama/Cloud LLMs** | Language model backends |

This creates a powerful **no-code → AI → automation** pipeline where vibe coders can trigger complex AI development workflows from any external event!
