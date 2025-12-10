# AI Project Synthesizer - Docker Configuration
# Multi-stage build for efficient production images

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install -r requirements.txt


# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim as runtime

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set work directory
WORKDIR $APP_HOME

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p logs output temp .cache && \
    chown -R appuser:appuser $APP_HOME

# Switch to non-root user
USER appuser

# Expose port (if running as HTTP server)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src; print('healthy')" || exit 1

# Default command - run MCP server
CMD ["python", "-m", "src.mcp.server"]


# ============================================
# Stage 3: Development
# ============================================
FROM runtime as development

# Switch to root for dev tool installation
USER root

# Install development tools
RUN pip install pytest pytest-asyncio pytest-cov black ruff mypy

# Switch back to appuser
USER appuser

# Development command with auto-reload
CMD ["python", "-m", "src.mcp.server", "--debug"]


# ============================================
# Build Commands:
# ============================================
# Production: docker build -t ai-synthesizer .
# Development: docker build --target development -t ai-synthesizer:dev .
# 
# Run Commands:
# docker run -it --rm -v $(pwd)/output:/app/output ai-synthesizer
# docker-compose up
