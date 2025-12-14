# AI Project Synthesizer - Development Commands
# Usage: make <target>

.PHONY: help install test quick lint format type clean docker

# Default target
help:
	@echo "AI Project Synthesizer - Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install dependencies"
	@echo "  make hooks       Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make quick       Run smoke tests (~30s)"
	@echo "  make test        Run unit tests"
	@echo "  make test-full   Run full test suite"
	@echo "  make test-ci     Run CI tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        Run linter (ruff)"
	@echo "  make format      Auto-format code"
	@echo "  make type        Run type checker (mypy)"
	@echo "  make check       Run all checks (lint + type)"
	@echo ""
	@echo "Other:"
	@echo "  make clean       Clean build artifacts"
	@echo "  make docker      Build Docker image"
	@echo "  make serve       Start MCP server"

# Setup
install:
	pip install -e ".[dev]"

hooks:
	pip install pre-commit
	pre-commit install

# Testing
quick:
	python scripts/test_runner.py quick

test:
	python scripts/test_runner.py unit

test-full:
	python scripts/test_runner.py full

test-ci:
	python scripts/test_runner.py ci

# Code Quality
lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check src/ tests/ --fix

type:
	mypy src/ --ignore-missing-imports

check: lint type

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Docker
docker:
	docker build -t ai-synthesizer:latest -f docker/Dockerfile .

# Server
serve:
	python -m src.mcp.server
