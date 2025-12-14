# AI Project Synthesizer - Windows PowerShell Development Commands
# Usage: .\scripts\dev.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host "AI Project Synthesizer - Development Commands" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Setup:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev.ps1 install     Install dependencies"
    Write-Host "  .\scripts\dev.ps1 hooks       Install pre-commit hooks"
    Write-Host ""
    Write-Host "Testing:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev.ps1 quick       Run smoke tests (~30s)"
    Write-Host "  .\scripts\dev.ps1 test        Run unit tests"
    Write-Host "  .\scripts\dev.ps1 test-full   Run full test suite"
    Write-Host "  .\scripts\dev.ps1 test-ci     Run CI tests with coverage"
    Write-Host ""
    Write-Host "Code Quality:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev.ps1 lint        Run linter (ruff)"
    Write-Host "  .\scripts\dev.ps1 format      Auto-format code"
    Write-Host "  .\scripts\dev.ps1 type        Run type checker (mypy)"
    Write-Host "  .\scripts\dev.ps1 check       Run all checks"
    Write-Host ""
    Write-Host "Other:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev.ps1 clean       Clean build artifacts"
    Write-Host "  .\scripts\dev.ps1 serve       Start MCP server"
}

function Install-Deps {
    Write-Host "Installing dependencies..." -ForegroundColor Green
    pip install -e ".[dev]"
}

function Install-Hooks {
    Write-Host "Installing pre-commit hooks..." -ForegroundColor Green
    pip install pre-commit
    pre-commit install
}

function Run-Quick {
    Write-Host "Running smoke tests..." -ForegroundColor Green
    python scripts/test_runner.py quick
}

function Run-Test {
    Write-Host "Running unit tests..." -ForegroundColor Green
    python scripts/test_runner.py unit
}

function Run-TestFull {
    Write-Host "Running full test suite..." -ForegroundColor Green
    python scripts/test_runner.py full
}

function Run-TestCI {
    Write-Host "Running CI tests with coverage..." -ForegroundColor Green
    python scripts/test_runner.py ci
}

function Run-Lint {
    Write-Host "Running linter..." -ForegroundColor Green
    ruff check src/ tests/
}

function Run-Format {
    Write-Host "Formatting code..." -ForegroundColor Green
    ruff format src/ tests/
    ruff check src/ tests/ --fix
}

function Run-Type {
    Write-Host "Running type checker..." -ForegroundColor Green
    mypy src/ --ignore-missing-imports
}

function Run-Check {
    Run-Lint
    Run-Type
}

function Clean-Artifacts {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Green
    $dirs = @("build", "dist", "*.egg-info", ".pytest_cache", ".ruff_cache", ".mypy_cache", "htmlcov")
    foreach ($dir in $dirs) {
        Get-ChildItem -Path . -Directory -Recurse -Filter $dir -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    }
    Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    Remove-Item -Path ".coverage", "coverage.xml" -ErrorAction SilentlyContinue
    Write-Host "Done!" -ForegroundColor Green
}

function Start-Server {
    Write-Host "Starting MCP server..." -ForegroundColor Green
    python -m src.mcp.server
}

# Command dispatch
switch ($Command.ToLower()) {
    "help"      { Show-Help }
    "install"   { Install-Deps }
    "hooks"     { Install-Hooks }
    "quick"     { Run-Quick }
    "test"      { Run-Test }
    "test-full" { Run-TestFull }
    "test-ci"   { Run-TestCI }
    "lint"      { Run-Lint }
    "format"    { Run-Format }
    "type"      { Run-Type }
    "check"     { Run-Check }
    "clean"     { Clean-Artifacts }
    "serve"     { Start-Server }
    default     { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}
