# n8n Workflows for AI Project Synthesizer

This directory contains n8n workflow templates for automating various tasks with the AI Project Synthesizer.

## Available Workflows

| Workflow | File | Trigger | Description |
|----------|------|---------|-------------|
| GitHub Repo Sweep | `github-repo-sweep.json` | Cron (daily) | Scans GitHub for trending repos matching criteria |
| HuggingFace Model Watcher | `huggingface-watcher.json` | Cron (hourly) | Monitors new models on HuggingFace |
| Kaggle Dataset Monitor | `kaggle-monitor.json` | Cron (daily) | Tracks new datasets on Kaggle |
| Synthesis Complete Hook | `synthesis-complete.json` | Webhook | Triggered when synthesis completes |
| Error Alert | `error-alert.json` | Webhook | Sends alerts on synthesis errors |
| Daily Report | `daily-report.json` | Cron (daily) | Generates daily activity report |
| Backup Workflow | `backup.json` | Cron (weekly) | Backs up synthesized projects |
| Health Check | `health-check.json` | Cron (5min) | Monitors system health |
| Slack Notifier | `slack-notifier.json` | Webhook | Sends Slack notifications |
| Discord Bot | `discord-bot.json` | Webhook | Discord integration |

## Installation

1. Open your n8n instance
2. Go to **Workflows** → **Import**
3. Select the JSON file for the workflow you want
4. Configure credentials (GitHub token, Slack webhook, etc.)
5. Activate the workflow

## Webhook Endpoints

The AI Project Synthesizer exposes these webhook endpoints for n8n:

```
POST /api/webhooks/n8n/synthesis-complete
POST /api/webhooks/n8n/analysis-complete
POST /api/webhooks/n8n/error
POST /api/webhooks/n8n/health
```

## Configuration

Each workflow may require:
- **GitHub Token**: For repository access
- **Slack Webhook URL**: For notifications
- **Discord Webhook URL**: For Discord integration
- **Synthesizer API URL**: Usually `http://localhost:8000`

## Creating Custom Workflows

1. Start with a template from this directory
2. Modify triggers and actions as needed
3. Test with the n8n execution panel
4. Export and save to this directory

See `docs/N8N_WORKFLOWS.md` for detailed documentation.
