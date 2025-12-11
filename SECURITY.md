# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Supported Environments

| Environment | Status |
|-------------|--------|
| Windows 11 + Python 3.11+ | ✅ Fully Tested |
| Windows 10 + Python 3.11+ | ✅ Supported |
| Ubuntu 22.04 + Python 3.11+ | ✅ Supported |
| macOS 13+ + Python 3.11+ | ⚠️ Community Tested |
| Docker (any OS) | ✅ Supported |

## Security Considerations

### API Keys and Tokens

The AI Project Synthesizer uses various API keys for platform access:

| Service | Environment Variable | Purpose |
|---------|---------------------|---------|
| GitHub | `GITHUB_TOKEN` | Repository access, search |
| HuggingFace | `HUGGINGFACE_TOKEN` | Model/dataset access |
| Kaggle | `KAGGLE_KEY` | Dataset access |
| OpenAI | `OPENAI_API_KEY` | Cloud LLM (optional) |
| Anthropic | `ANTHROPIC_API_KEY` | Cloud LLM (optional) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Voice synthesis (optional) |

### Best Practices

1. **Never commit `.env` files** - The `.gitignore` excludes these by default
2. **Use `.env.example`** - Copy to `.env` and fill in your values
3. **Rotate tokens regularly** - Especially if you suspect exposure
4. **Use minimal scopes** - Only grant necessary permissions to tokens
5. **Local LLMs preferred** - Use Ollama/LM Studio to avoid sending code to cloud

### Secret Masking

The system automatically masks secrets in logs:

```python
# These patterns are masked:
# - GitHub tokens (ghp_*, gho_*, ghu_*, ghs_*, ghr_*)
# - OpenAI keys (sk-*)
# - Anthropic keys (sk-ant-*)
# - Generic API keys matching common patterns
```

### Input Validation

All user inputs are validated:

- **URLs**: Must be valid HTTP/HTTPS URLs
- **Repository URLs**: Must match known platform patterns
- **File paths**: Sanitized to prevent path traversal
- **Query strings**: Length-limited and sanitized

## Data Handling

### What We Access

- **Public repositories**: Code, metadata, README files
- **Your local files**: Only in specified output directories
- **LLM APIs**: Queries sent to configured providers

### What We Store

- **Synthesized projects**: In your specified output directory
- **Cache**: Temporary files in `.cache/` (auto-cleaned)
- **Logs**: In `logs/` directory (configurable retention)
- **Metrics**: In-memory or optional Redis

### What We DON'T Do

- ❌ Send your private code to external services without consent
- ❌ Store API keys anywhere except your local `.env`
- ❌ Log full API keys or tokens
- ❌ Access files outside specified directories
- ❌ Make network requests without user-initiated actions

## Network Security

### Outbound Connections

The system makes outbound connections to:

| Destination | Purpose | When |
|-------------|---------|------|
| api.github.com | Repository search/access | User-initiated search |
| huggingface.co | Model/dataset access | User-initiated search |
| kaggle.com | Dataset access | User-initiated search |
| api.openai.com | LLM queries | If cloud LLM enabled |
| api.anthropic.com | LLM queries | If cloud LLM enabled |
| localhost:11434 | Ollama | If local LLM enabled |
| localhost:1234 | LM Studio | If local LLM enabled |

### Inbound Connections

If running the dashboard or MCP server:

| Port | Service | Default Binding |
|------|---------|-----------------|
| 8000 | Dashboard/API | localhost only |
| 5678 | n8n webhooks | localhost only |

**Production Recommendation**: Use a reverse proxy (nginx) with HTTPS.

## Docker Security

When running in Docker:

1. **Don't run as root** - Use the non-root user in Dockerfile
2. **Limit resources** - Set memory and CPU limits
3. **Network isolation** - Use internal networks where possible
4. **Secret management** - Use Docker secrets, not environment variables
5. **Image scanning** - Regularly scan for vulnerabilities

## Reporting a Vulnerability

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email: [security contact - add your email]
3. Or: Open a private security advisory on GitHub

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release

## Security Checklist for Deployment

Before deploying to production:

- [ ] All API keys are in `.env`, not in code
- [ ] `.env` is in `.gitignore`
- [ ] HTTPS is enabled (if exposed to network)
- [ ] Rate limiting is configured
- [ ] Logging doesn't include secrets
- [ ] File permissions are restrictive
- [ ] Docker containers run as non-root
- [ ] Dependencies are up to date (`pip-audit` clean)
- [ ] Bandit security scan passes

## Dependency Security

We regularly scan dependencies:

```bash
# Run security audit
pip-audit

# Run static analysis
bandit -r src/ -ll

# Check for known vulnerabilities
safety check
```

### Automated Checks

- **CI/CD**: Security scans run on every PR
- **Dependabot**: Automated dependency updates
- **CodeQL**: Static analysis for security issues

## Compliance Notes

This project is designed for:

- ✅ Personal use
- ✅ Internal enterprise use
- ✅ Open source development

For regulated environments (HIPAA, SOC2, etc.), additional controls may be needed.

---

*Last updated: 2024-12-11*
