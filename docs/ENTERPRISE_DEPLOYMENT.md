# Enterprise Deployment Guide

## Overview

This guide covers enterprise-grade production deployment of the AI Project Synthesizer with enhanced security, observability, reliability, and operational features.

## 🚀 Production Features Implemented

### Security Hardening
- **Secret Masking**: Automatic detection and masking of API keys, tokens, and sensitive data in logs
- **Input Validation**: Comprehensive validation of user inputs including URLs, queries, and file paths
- **Secure Logging**: All log outputs sanitized to prevent data leakage
- **Rate Limiting**: Enhanced rate limiting with configurable thresholds and burst protection

### Observability & Monitoring
- **Correlation IDs**: Request tracing across the entire pipeline for debugging
- **Metrics Collection**: Performance metrics, error rates, and operational statistics
- **Health Checks**: Built-in health monitoring for external services (Ollama, GitHub API, disk space)
- **Structured Logging**: JSON-formatted logs in production with consistent structure

### Reliability & Resilience
- **Circuit Breakers**: Prevent cascade failures from external API outages
- **Graceful Shutdown**: Proper cleanup and resource management on termination
- **Timeout Protection**: Configurable timeouts for all external operations
- **Retry Logic**: Automatic retry with exponential backoff for transient failures

### Configuration Management
- **Production Settings**: Comprehensive configuration options for enterprise environments
- **Environment Validation**: Startup validation of required settings and dependencies
- **Feature Flags**: Runtime control of production features

## 📋 Prerequisites

### System Requirements
- Python 3.11+
- 4GB+ RAM minimum
- 10GB+ disk space
- Network access to GitHub, HuggingFace, and other platforms

### Required Environment Variables
```bash
# Core Configuration
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# GitHub Integration (Required)
GITHUB_TOKEN=ghp_your_github_token_here

# Optional Platform Tokens
HUGGINGFACE_TOKEN=hf_your_huggingface_token_here
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key

# LLM Configuration
OLLAMA_HOST=http://localhost:11434
CLOUD_LLM_ENABLED=false
# OPENAI_API_KEY=sk_your_openai_key_here
# ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
```

## 🔧 Installation & Setup

### 1. Clone and Install
```bash
git clone <repository-url>
cd AI_Synthesizer
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy template configuration
cp .env.example .env
# Edit .env with your production settings
```

### 3. Validate Configuration
```bash
python -c "from src.core.config import get_settings; print(get_settings())"
```

### 4. Test Installation
```bash
# Run health checks
python -c "
import asyncio
from src.core.observability import health_checker
async def main():
    status = await health_checker.check_all()
    print(f'Health Status: {status[\"status\"]}')
    for check, result in status['checks'].items():
        print(f'{check}: {result[\"status\"]}')
asyncio.run(main())
"
```

## 🚀 Production Deployment

### Option 1: Direct Deployment
```bash
# Start MCP server for Windsurf integration
python -m src.mcp_server.server
```

### Option 2: Containerized Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

ENV APP_ENV=production
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.mcp_server.server"]
```

### Option 3: Docker Compose
```yaml
version: '3.8'
services:
  ai-synthesizer:
    build: .
    environment:
      - APP_ENV=production
      - LOG_LEVEL=INFO
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    restart: unless-stopped
    
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

## ⚙️ Production Configuration

### Security Settings
```python
# In .env or config
MASK_SECRETS_IN_LOGS=true
VALIDATE_INPUT_URLS=true
MAX_QUERY_LENGTH=1000
```

### Circuit Breaker Configuration
```python
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60.0
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2
CIRCUIT_BREAKER_TIMEOUT=30.0
```

### Observability Settings
```python
METRICS_RETENTION_HOURS=24
CORRELATION_ID_IN_LOGS=true
HEALTH_CHECK_INTERVAL=60
```

### Performance Settings
```python
REQUEST_TIMEOUT_SECONDS=30
MAX_RETRIES=3
GRACEFUL_SHUTDOWN_TIMEOUT=60.0
```

## 📊 Monitoring & Observability

### Health Monitoring
```python
# Check system health
from src.core.observability import health_checker

status = await health_checker.check_all()
print(f"Overall: {status['status']}")
for check, result in status['checks'].items():
    print(f"{check}: {result['status']} ({result['duration']:.2f}s)")
```

### Metrics Collection
```python
# Access metrics
from src.core.observability import metrics

# Get all metrics
all_metrics = metrics.get_all_metrics()
print(f"Collected {len(all_metrics)} metrics")

# Get specific metric summary
search_stats = metrics.get_metric_summary("github_search_duration")
print(f"Average search time: {search_stats['avg']:.2f}s")
```

### Circuit Breaker Status
```python
# Monitor circuit breakers
from src.core.circuit_breaker import get_all_circuit_breaker_status

status = get_all_circuit_breaker_status()
for name, breaker_status in status.items():
    print(f"{name}: {breaker_status['state']} "
          f"(failures: {breaker_stats['failures']})")
```

## 🔐 Security Best Practices

### Secret Management
1. **Never commit secrets to version control**
2. **Use environment variables for all sensitive data**
3. **Rotate API keys regularly**
4. **Monitor for secret leakage in logs**

### Input Validation
- All user inputs are validated before processing
- Repository URLs are checked against allowlist
- Search queries have length limits
- File paths are sanitized to prevent traversal

### Network Security
- All external API calls use HTTPS
- Timeouts prevent hanging connections
- Rate limiting prevents abuse
- Circuit breakers prevent cascade failures

## 🚨 Troubleshooting

### Common Issues

#### 1. Circuit Breaker Open
```bash
# Symptom: Requests failing with "Circuit open" error
# Solution: Check external service status and wait for recovery

# Check circuit breaker status
python -c "
from src.core.circuit_breaker import get_circuit_breaker
breaker = get_circuit_breaker('github_search')
print(breaker.get_status())
"

# Force reset if needed
breaker.reset()
```

#### 2. Authentication Failures
```bash
# Symptom: 401 errors from GitHub/HuggingFace
# Solution: Verify tokens are valid and have required scopes

# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
```

#### 3. High Memory Usage
```bash
# Symptom: Memory usage increasing over time
# Solution: Monitor metrics and adjust retention settings

# Check metrics retention
python -c "
from src.core.observability import metrics
print(f'Metrics retention: {settings.app.metrics_retention_hours}h')
"
```

#### 4. Slow Performance
```bash
# Symptom: Requests taking longer than expected
# Solution: Check performance metrics and external service latency

# View performance stats
python -c "
from src.core.observability import performance
stats = performance.get_operation_stats('github_search')
print(f'Average: {stats[\"avg\"]:.2f}s, P95: {stats[\"p95\"]:.2f}s')
"
```

### Debug Mode
```bash
# Enable debug logging (use with caution in production)
export LOG_LEVEL=DEBUG
export DEBUG=true

# Check correlation IDs in logs
grep "correlation_id" /var/log/ai-synthesizer.log
```

## 📈 Performance Tuning

### Optimizing Throughput
1. **Adjust concurrent limits**: Increase `max_concurrent_clones` for faster processing
2. **Tune rate limits**: Balance between API limits and throughput
3. **Cache optimization**: Enable caching for repeated queries
4. **Circuit breaker thresholds**: Adjust based on service reliability

### Resource Management
```python
# Monitor resource usage
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
print(f"CPU: {process.cpu_percent()}%")
```

## 🔄 Maintenance

### Regular Tasks
1. **Log rotation**: Configure log rotation to prevent disk filling
2. **Metrics cleanup**: Adjust retention periods based on storage needs
3. **Token rotation**: Update API keys before expiration
4. **Health monitoring**: Set up alerts for health check failures

### Backup & Recovery
```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup metrics (if needed)
python -c "
from src.core.observability import metrics
import json
with open('metrics_backup.json', 'w') as f:
    json.dump(metrics.get_all_metrics(), f)
"
```

## 📚 Integration Examples

### Windsurf IDE Integration
```json
{
  "mcpServers": {
    "ai-project-synthesizer": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/AI_Synthesizer"
    }
  }
}
```

### Monitoring Integration
```python
# Prometheus metrics export
from prometheus_client import start_http_server, Counter

# Add to your monitoring setup
start_http_server(8000)
request_counter = Counter('ai_synthesizer_requests_total', 'Total requests')
```

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] API tokens validated with required scopes
- [ ] Health checks passing for all services
- [ ] Log rotation configured
- [ ] Monitoring and alerting set up
- [ ] Backup procedures documented
- [ ] Security review completed
- [ ] Performance benchmarks established
- [ ] Circuit breaker thresholds tuned
- [ ] Graceful shutdown tested

## 📞 Support

For enterprise support and issues:
1. Check logs with correlation IDs for debugging
2. Review health check status
3. Monitor circuit breaker states
4. Consult metrics for performance issues
5. Review this documentation for configuration guidance

---

## 🔄 Version History

- **v1.2.0**: Enterprise production features added
  - Security hardening with secret masking
  - Circuit breaker pattern implementation
  - Observability with correlation IDs and metrics
  - Graceful shutdown and lifecycle management
  - Production configuration options

- **v1.1.0**: Production-ready baseline
  - Core MCP server functionality
  - Multi-platform repository search
  - Dependency resolution with SAT solver
  - Project synthesis and documentation generation
