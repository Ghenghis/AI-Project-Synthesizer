# Start AI Synthesizer with LM Studio
# This script checks LM Studio is running and starts the MCP server

$ErrorActionPreference = "Stop"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "AI Project Synthesizer - LM Studio Launcher" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Configuration
$LMStudioHost = $env:LMSTUDIO_HOST
if (-not $LMStudioHost) {
    $LMStudioHost = "http://localhost:1234"
}

Write-Host "`n[1/4] Checking LM Studio..." -ForegroundColor Yellow

# Check if LM Studio is running
try {
    $response = Invoke-RestMethod -Uri "$LMStudioHost/v1/models" -Method Get -TimeoutSec 5
    Write-Host "  OK - LM Studio is running" -ForegroundColor Green
    
    if ($response.data -and $response.data.Count -gt 0) {
        Write-Host "  Loaded models:" -ForegroundColor Gray
        foreach ($model in $response.data) {
            Write-Host "    - $($model.id)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  WARNING: No models loaded in LM Studio" -ForegroundColor Yellow
        Write-Host "  Please load a model in LM Studio before continuing" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ERROR: LM Studio is not running or not accessible" -ForegroundColor Red
    Write-Host "  Please start LM Studio and enable the local server" -ForegroundColor Red
    Write-Host "  Expected URL: $LMStudioHost" -ForegroundColor Gray
    Write-Host "`nTo start LM Studio:" -ForegroundColor Yellow
    Write-Host "  1. Open LM Studio" -ForegroundColor Gray
    Write-Host "  2. Load a model (e.g., Qwen2.5-Coder)" -ForegroundColor Gray
    Write-Host "  3. Click 'Start Server' in the Local Server tab" -ForegroundColor Gray
    exit 1
}

Write-Host "`n[2/4] Checking Python environment..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK - $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/4] Checking dependencies..." -ForegroundColor Yellow

# Check if in virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Host "  OK - Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "  WARNING: No virtual environment active" -ForegroundColor Yellow
    
    # Try to activate .venv if it exists
    $venvPath = Join-Path $PSScriptRoot "..\\.venv\\Scripts\\Activate.ps1"
    if (Test-Path $venvPath) {
        Write-Host "  Activating .venv..." -ForegroundColor Gray
        & $venvPath
    }
}

Write-Host "`n[4/4] Starting MCP Server..." -ForegroundColor Yellow

# Set environment variables
$env:LMSTUDIO_HOST = $LMStudioHost
$env:LLM_PROVIDER = "lmstudio"

Write-Host "  LLM Provider: LM Studio" -ForegroundColor Gray
Write-Host "  LM Studio URL: $LMStudioHost" -ForegroundColor Gray

# Change to project root
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "Starting AI Project Synthesizer MCP Server..." -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m src.mcp_server.server
