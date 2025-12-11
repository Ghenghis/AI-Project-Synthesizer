# AI Project Synthesizer - n8n Workflow Integration

> **Version:** 2.0.0 | **Status:** Production Ready

This document describes the n8n workflow integration for automating tasks with the AI Project Synthesizer.

---

## Overview

The AI Project Synthesizer integrates with [n8n](https://n8n.io/) for workflow automation. n8n is an open-source workflow automation tool that can connect to various services and APIs.

### Benefits

- **Automated Discovery**: Continuously scan platforms for new repositories
- **Event-Driven Actions**: Trigger workflows when synthesis completes
- **Notifications**: Send alerts to Slack, Discord, email, etc.
- **Scheduled Tasks**: Run daily reports, backups, health checks
- **Custom Integrations**: Connect to any service with HTTP or webhooks

---

## Available Workflows

The following workflows are available in `workflows/n8n/`:

### 1. GitHub Repo Sweep

**File:** `github-repo-sweep.json`  
**Trigger:** Cron (daily at midnight)  
**Purpose:** Scans GitHub for trending repositories matching your search criteria.

**Actions:**
1. Triggers daily at configured time
2. Calls the Synthesizer search API with predefined queries
3. Filters results based on stars, language, activity
4. Optionally triggers analysis on promising repos

**Configuration:**
- Set your search queries in the workflow
- Configure minimum star count threshold
- Set target languages to filter

---

### 2. HuggingFace Model Watcher

**File:** `huggingface-watcher.json`  
**Trigger:** Cron (hourly)  
**Purpose:** Monitors HuggingFace for new models in specific categories.

**Actions:**
1. Queries HuggingFace API for new models
2. Filters by task type (text-generation, image-classification, etc.)
3. Sends notifications for interesting new models
4. Optionally adds to synthesis queue

---

### 3. Kaggle Dataset Monitor

**File:** `kaggle-monitor.json`  
**Trigger:** Cron (daily)  
**Purpose:** Tracks new datasets on Kaggle matching your interests.

**Actions:**
1. Queries Kaggle API for new datasets
2. Filters by tags and competition relevance
3. Sends digest of new datasets

---

### 4. Synthesis Complete Hook

**File:** `synthesis-complete.json`  
**Trigger:** Webhook (POST /api/webhooks/n8n/synthesis-complete)  
**Purpose:** Triggered when a synthesis operation completes successfully.

**Actions:**
1. Receives synthesis completion event
2. Sends Slack/Discord notification
3. Triggers documentation generation
4. Optionally runs tests on synthesized project

**Payload:**
```json
{
  "project_id": "uuid",
  "project_name": "my-project",
  "output_path": "/path/to/output",
  "repository_count": 3,
  "duration_seconds": 120,
  "status": "success"
}
```

---

### 5. Error Alert

**File:** `error-alert.json`  
**Trigger:** Webhook (POST /api/webhooks/n8n/error)  
**Purpose:** Sends alerts when synthesis or analysis errors occur.

**Actions:**
1. Receives error event
2. Formats error details
3. Sends to configured alert channels
4. Logs to error tracking system

---

### 6. Daily Report

**File:** `daily-report.json`  
**Trigger:** Cron (daily at 9 AM)  
**Purpose:** Generates and sends a daily activity report.

**Actions:**
1. Queries metrics API for last 24 hours
2. Compiles statistics (searches, syntheses, errors)
3. Generates summary report
4. Sends to configured recipients

---

### 7. Backup Workflow

**File:** `backup.json`  
**Trigger:** Cron (weekly on Sunday)  
**Purpose:** Backs up synthesized projects and configuration.

**Actions:**
1. Lists all synthesized projects
2. Creates compressed archives
3. Uploads to configured storage (S3, GCS, local)
4. Cleans up old backups

---

### 8. Health Check

**File:** `health-check.json`  
**Trigger:** Cron (every 5 minutes)  
**Purpose:** Monitors system health and alerts on issues.

**Actions:**
1. Calls health check endpoint
2. Checks component status (database, cache, LLM)
3. Alerts if any component is unhealthy
4. Logs health history

---

### 9. Slack Notifier

**File:** `slack-notifier.json`  
**Trigger:** Webhook  
**Purpose:** Generic Slack notification workflow.

**Actions:**
1. Receives notification request
2. Formats message for Slack
3. Posts to configured channel

---

### 10. Discord Bot

**File:** `discord-bot.json`  
**Trigger:** Webhook  
**Purpose:** Discord integration for notifications and commands.

**Actions:**
1. Receives Discord events
2. Processes slash commands
3. Sends formatted responses

---

## Installation

### Prerequisites

1. n8n instance running (self-hosted or cloud)
2. AI Project Synthesizer running with API enabled
3. Network connectivity between n8n and Synthesizer

### Import Workflows

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select the JSON file from `workflows/n8n/`
4. Configure credentials:
   - **Synthesizer API**: `http://localhost:8000` (or your URL)
   - **Slack**: Your Slack webhook URL
   - **GitHub**: Your GitHub token
5. Activate the workflow

### Configure Webhooks

For webhook-triggered workflows, configure the Synthesizer to call n8n:

```bash
# In your .env file
N8N_WEBHOOK_URL=http://your-n8n-instance:5678/webhook
N8N_SYNTHESIS_COMPLETE_PATH=/synthesis-complete
N8N_ERROR_PATH=/error
```

---

## API Endpoints

The Synthesizer exposes these endpoints for n8n integration:

### Webhook Receivers

```http
POST /api/webhooks/n8n/synthesis-complete
POST /api/webhooks/n8n/analysis-complete
POST /api/webhooks/n8n/error
POST /api/webhooks/n8n/health
```

### API Endpoints for n8n to Call

```http
GET  /api/health
GET  /api/metrics
POST /api/search
POST /api/analyze
POST /api/synthesize
GET  /api/projects
GET  /api/projects/{id}
```

---

## Creating Custom Workflows

### Template Structure

```json
{
  "name": "My Custom Workflow",
  "nodes": [
    {
      "name": "Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": { ... }
    },
    {
      "name": "Call Synthesizer",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/...",
        "method": "POST"
      }
    }
  ],
  "connections": { ... }
}
```

### Best Practices

1. **Error Handling**: Always add error handling nodes
2. **Rate Limiting**: Don't overwhelm the Synthesizer API
3. **Logging**: Log important events for debugging
4. **Credentials**: Use n8n's credential management
5. **Testing**: Test workflows in n8n's execution panel first

---

## Troubleshooting

### Workflow Not Triggering

1. Check workflow is activated (toggle is green)
2. Verify cron expression is correct
3. Check n8n logs for errors

### API Connection Failed

1. Verify Synthesizer is running
2. Check network connectivity
3. Verify API URL is correct
4. Check authentication if required

### Webhook Not Received

1. Verify webhook URL is correct
2. Check firewall/network rules
3. Test with curl or Postman first

---

## Security Considerations

1. **API Keys**: Store in n8n credentials, not in workflow
2. **Network**: Use HTTPS in production
3. **Authentication**: Enable API key auth for webhooks
4. **Rate Limiting**: Configure rate limits on Synthesizer
5. **Logging**: Don't log sensitive data

---

## Support

- **n8n Documentation**: https://docs.n8n.io/
- **Synthesizer Issues**: https://github.com/Ghenghis/AI-Project-Synthesizer/issues
- **Community**: Join our Discord for help
