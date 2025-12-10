# ============================================
# AI Project Synthesizer - Windows Setup Script
# ============================================
# Run this script to set up the development environment
# Usage: .\scripts\setup.ps1
# ============================================

param(
    [switch]$SkipModels,
    [switch]$Docker,
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Colors for output
function Write-Step { param($msg) Write-Host "`n[STEP] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

Write-Host @"
============================================
   AI Project Synthesizer - Setup
============================================
"@ -ForegroundColor Magenta

# ============================================
# Check Prerequisites
# ============================================
Write-Step "Checking prerequisites..."

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python not found. Please install Python 3.11+"
    Write-Host "Download from: https://www.python.org/downloads/"
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Success "Python found: $pythonVersion"

# Check Git
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Error "Git not found. Please install Git"
    Write-Host "Download from: https://git-scm.com/downloads"
    exit 1
}
Write-Success "Git found: $(git --version)"

# Check for NVIDIA GPU (optional)
$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidia) {
    Write-Success "NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
} else {
    Write-Warning "NVIDIA GPU not detected - local LLM will be slower"
}

# ============================================
# Install uv (fast Python package manager)
# ============================================
Write-Step "Installing uv package manager..."

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    pip install uv
    Write-Success "uv installed"
} else {
    Write-Success "uv already installed"
}

# ============================================
# Create Virtual Environment
# ============================================
Write-Step "Creating virtual environment..."

if (-not (Test-Path ".venv")) {
    uv venv
    Write-Success "Virtual environment created"
} else {
    Write-Success "Virtual environment exists"
}

# Activate virtual environment
Write-Step "Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

# ============================================
# Install Dependencies
# ============================================
Write-Step "Installing dependencies..."

if ($Dev) {
    Write-Host "Installing development dependencies..."
    uv pip install -r requirements.txt
    uv pip install -r requirements-dev.txt
} else {
    uv pip install -r requirements.txt
}
Write-Success "Dependencies installed"

# ============================================
# Setup Environment File
# ============================================
Write-Step "Setting up environment..."

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Success ".env file created from template"
    Write-Warning "Please edit .env with your API keys!"
} else {
    Write-Success ".env file exists"
}

# ============================================
# Create Directories
# ============================================
Write-Step "Creating directories..."

$dirs = @("logs", "output", "temp", ".cache")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}
Write-Success "Directories created"

# ============================================
# Install Ollama (if not using Docker)
# ============================================
if (-not $Docker -and -not $SkipModels) {
    Write-Step "Checking Ollama..."
    
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollama) {
        Write-Warning "Ollama not found"
        Write-Host "Please install Ollama from: https://ollama.ai/download"
        Write-Host "Then run: ollama pull qwen2.5-coder:14b-instruct-q4_K_M"
    } else {
        Write-Success "Ollama found"
        
        Write-Step "Pulling LLM models (this may take a while)..."
        Write-Host "Pulling qwen2.5-coder:7b-instruct-q8_0..."
        ollama pull qwen2.5-coder:7b-instruct-q8_0
        
        Write-Host "Pulling qwen2.5-coder:14b-instruct-q4_K_M..."
        ollama pull qwen2.5-coder:14b-instruct-q4_K_M
        
        Write-Success "Models downloaded"
    }
}

# ============================================
# Docker Setup (if requested)
# ============================================
if ($Docker) {
    Write-Step "Setting up Docker..."
    
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-Error "Docker not found. Please install Docker Desktop"
        exit 1
    }
    
    Write-Host "Building Docker images..."
    docker-compose -f docker/docker-compose.yml build
    
    Write-Host "Starting services..."
    docker-compose -f docker/docker-compose.yml up -d
    
    Write-Success "Docker services started"
}

# ============================================
# Verify Installation
# ============================================
Write-Step "Verifying installation..."

try {
    python -c "import src; print('Module import successful')"
    Write-Success "Installation verified"
} catch {
    Write-Error "Installation verification failed"
    Write-Host $_.Exception.Message
}

# ============================================
# Print Next Steps
# ============================================
Write-Host @"

============================================
   Setup Complete!
============================================

Next steps:
1. Edit .env with your API keys:
   - GITHUB_TOKEN (required)
   - HUGGINGFACE_TOKEN (optional)
   - OPENAI_API_KEY (optional fallback)

2. Start Ollama (if not using Docker):
   ollama serve

3. Add to Windsurf mcp_config.json:
   {
     "mcpServers": {
       "ai-project-synthesizer": {
         "command": "python",
         "args": ["-m", "src.mcp.server"],
         "cwd": "$PWD"
       }
     }
   }

4. Run the MCP server:
   python -m src.mcp.server

5. Run tests:
   pytest tests/ -v

For help, see: docs/guides/DEVELOPMENT.md
============================================
"@ -ForegroundColor Green
