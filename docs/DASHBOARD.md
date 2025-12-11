# AI Project Synthesizer - Web Dashboard

> **Version:** 2.0.0 | **Status:** Production Ready

The web dashboard provides a visual interface for managing projects, monitoring synthesis operations, and configuring the system.

---

## Quick Start

### Starting the Dashboard

```bash
# Using CLI
python -m src.cli dashboard

# Or directly
python -m src.dashboard.app

# With custom port
python -m src.cli dashboard --port 8080
```

### Default URL

```
http://localhost:8000
```

---

## Dashboard Views

### 1. Home / Overview

**URL:** `/`

Displays:
- System status (healthy/degraded)
- Active synthesis jobs
- Recent activity
- Quick actions

### 2. Projects

**URL:** `/projects`

Manage synthesized projects:
- List all projects
- View project details
- Re-run synthesis
- Delete projects

### 3. Search

**URL:** `/search`

Search repositories across platforms:
- GitHub
- HuggingFace
- Kaggle
- ArXiv

### 4. Synthesis

**URL:** `/synthesis`

Create new projects:
- Select repositories
- Configure synthesis options
- Monitor progress
- View results

### 5. Plugins

**URL:** `/plugins`

Manage plugins:
- View installed plugins
- Enable/disable plugins
- Plugin configuration
- Install new plugins

### 6. Settings

**URL:** `/settings`

Configure the system:
- API keys
- LLM providers
- Platform settings
- Cache management

### 7. Metrics

**URL:** `/metrics`

View system metrics:
- Request counts
- Response times
- Error rates
- Resource usage

---

## API Endpoints

The dashboard exposes a REST API for programmatic access.

### Health Check

```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "components": {
    "database": "ok",
    "cache": "ok",
    "llm": "ok"
  }
}
```

### Projects

```http
GET /api/projects
GET /api/projects/{id}
POST /api/projects
DELETE /api/projects/{id}
```

### Synthesis

```http
POST /api/synthesis
GET /api/synthesis/{job_id}
GET /api/synthesis/{job_id}/status
DELETE /api/synthesis/{job_id}
```

Example request:
```json
POST /api/synthesis
{
  "repositories": [
    {"repo_url": "https://github.com/owner/repo1"},
    {"repo_url": "https://github.com/owner/repo2"}
  ],
  "project_name": "my-project",
  "output_path": "G:/projects",
  "template": "python-default"
}
```

### Search

```http
GET /api/search?q={query}&platforms=github,huggingface&max_results=20
```

### Plugins

```http
GET /api/plugins
GET /api/plugins/{id}
POST /api/plugins/{id}/enable
POST /api/plugins/{id}/disable
```

### Metrics

```http
GET /api/metrics
GET /api/metrics/prometheus
```

### Automation

```http
GET /api/automation/status
POST /api/automation/trigger/{workflow}
GET /api/automation/jobs
```

---

## Authentication

### API Key Authentication

For API access, include your API key in the header:

```http
Authorization: Bearer your-api-key
```

Or as a query parameter:

```http
GET /api/projects?api_key=your-api-key
```

### Session Authentication

The web UI uses session-based authentication:

1. Navigate to `/login`
2. Enter credentials
3. Session cookie is set automatically

---

## Configuration

### Environment Variables

```bash
# Dashboard settings
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000
DASHBOARD_DEBUG=false

# Authentication
DASHBOARD_SECRET_KEY=your-secret-key
DASHBOARD_API_KEY=your-api-key

# CORS
DASHBOARD_CORS_ORIGINS=http://localhost:3000,https://myapp.com
```

### Config File

Create `config/dashboard.yaml`:

```yaml
dashboard:
  host: 0.0.0.0
  port: 8000
  debug: false
  
  auth:
    enabled: true
    api_key_required: true
    session_timeout: 3600
  
  cors:
    enabled: true
    origins:
      - http://localhost:3000
      - https://myapp.com
  
  rate_limiting:
    enabled: true
    requests_per_minute: 60
```

---

## Integration with n8n

The dashboard integrates with n8n for workflow automation.

### Webhook Endpoints

```http
POST /api/webhooks/n8n/synthesis-complete
POST /api/webhooks/n8n/analysis-complete
POST /api/webhooks/n8n/error
```

### Triggering Workflows

```http
POST /api/automation/trigger/daily-sync
POST /api/automation/trigger/backup
```

### Viewing Automation Status

```http
GET /api/automation/status
```

Response:
```json
{
  "n8n_connected": true,
  "active_workflows": 5,
  "recent_executions": [
    {
      "workflow": "daily-sync",
      "status": "success",
      "completed_at": "2024-12-11T10:00:00Z"
    }
  ]
}
```

---

## Real-Time Updates

The dashboard supports real-time updates via WebSocket.

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

### Event Types

| Event | Description |
|-------|-------------|
| `synthesis.started` | Synthesis job started |
| `synthesis.progress` | Progress update |
| `synthesis.completed` | Synthesis finished |
| `synthesis.failed` | Synthesis failed |
| `plugin.loaded` | Plugin loaded |
| `plugin.error` | Plugin error |

---

## Customization

### Themes

The dashboard supports light and dark themes:

```bash
DASHBOARD_THEME=dark  # or 'light'
```

### Custom Branding

Add custom branding in `config/dashboard.yaml`:

```yaml
dashboard:
  branding:
    title: "My Synthesizer"
    logo: "/static/logo.png"
    favicon: "/static/favicon.ico"
    primary_color: "#007bff"
```

---

## Deployment

### Docker

```bash
docker run -p 8000:8000 \
  -e DASHBOARD_SECRET_KEY=your-secret \
  -e GITHUB_TOKEN=your-token \
  ai-synthesizer:latest dashboard
```

### Docker Compose

```yaml
services:
  dashboard:
    image: ai-synthesizer:latest
    command: python -m src.cli dashboard
    ports:
      - "8000:8000"
    environment:
      - DASHBOARD_HOST=0.0.0.0
      - DASHBOARD_PORT=8000
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./data:/app/data
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name synthesizer.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### Dashboard Won't Start

1. Check port availability: `netstat -an | grep 8000`
2. Verify environment variables are set
3. Check logs: `python -m src.cli dashboard --debug`

### API Errors

1. Verify API key is correct
2. Check CORS settings for browser requests
3. Review rate limiting configuration

### WebSocket Issues

1. Ensure WebSocket upgrade is allowed by proxy
2. Check firewall settings
3. Verify client WebSocket implementation

### Performance Issues

1. Enable caching: `DASHBOARD_CACHE_ENABLED=true`
2. Increase worker count for production
3. Use Redis for session storage

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Set strong secret keys**
3. **Enable rate limiting**
4. **Use API keys for programmatic access**
5. **Restrict CORS origins**
6. **Keep dependencies updated**
7. **Monitor access logs**

---

## Screenshots

### Home Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  🧬 AI Project Synthesizer                    [Settings]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  System Status: ● Healthy                               │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Projects    │  │ Active Jobs │  │ Plugins     │     │
│  │     12      │  │      3      │  │     8       │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  Recent Activity                                        │
│  ─────────────────────────────────────────────────────  │
│  • Project "rag-chatbot" synthesized (2 min ago)       │
│  • Search completed: "machine learning" (5 min ago)    │
│  • Plugin "gitlab" enabled (1 hour ago)                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Synthesis Progress
```
┌─────────────────────────────────────────────────────────┐
│  Synthesis: my-new-project                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Progress: [████████████░░░░░░░░] 60%                   │
│                                                         │
│  Steps:                                                 │
│  ✓ Cloning repositories                                │
│  ✓ Analyzing dependencies                              │
│  ● Merging code                                        │
│  ○ Generating documentation                            │
│  ○ Running tests                                       │
│                                                         │
│  Repositories: 3/3 processed                           │
│  Files created: 47                                     │
│  Time elapsed: 2m 34s                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
