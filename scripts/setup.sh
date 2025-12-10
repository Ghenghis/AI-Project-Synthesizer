#!/bin/bash
# ============================================
# AI Project Synthesizer - Unix/WSL Setup Script
# ============================================
# Run this script to set up the development environment
# Usage: ./scripts/setup.sh [--dev] [--docker] [--skip-models]
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_step() { echo -e "\n${CYAN}[STEP]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
DEV_MODE=false
DOCKER_MODE=false
SKIP_MODELS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev) DEV_MODE=true; shift ;;
        --docker) DOCKER_MODE=true; shift ;;
        --skip-models) SKIP_MODELS=true; shift ;;
        *) shift ;;
    esac
done

echo -e "${MAGENTA}"
echo "============================================"
echo "   AI Project Synthesizer - Setup"
echo "============================================"
echo -e "${NC}"

# ============================================
# Check Prerequisites
# ============================================
log_step "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
log_success "Python found: $PYTHON_VERSION"

# Check Git
if ! command -v git &> /dev/null; then
    log_error "Git not found. Please install Git"
    exit 1
fi
log_success "Git found: $(git --version)"

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    log_success "NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    log_warning "NVIDIA GPU not detected - local LLM will be slower"
fi

# ============================================
# Install uv
# ============================================
log_step "Installing uv package manager..."

if ! command -v uv &> /dev/null; then
    pip install uv
    log_success "uv installed"
else
    log_success "uv already installed"
fi

# ============================================
# Create Virtual Environment
# ============================================
log_step "Creating virtual environment..."

if [ ! -d ".venv" ]; then
    uv venv
    log_success "Virtual environment created"
else
    log_success "Virtual environment exists"
fi

# Activate virtual environment
log_step "Activating virtual environment..."
source .venv/bin/activate

# ============================================
# Install Dependencies
# ============================================
log_step "Installing dependencies..."

if [ "$DEV_MODE" = true ]; then
    echo "Installing development dependencies..."
    uv pip install -r requirements.txt
    uv pip install -r requirements-dev.txt
else
    uv pip install -r requirements.txt
fi
log_success "Dependencies installed"

# ============================================
# Setup Environment
# ============================================
log_step "Setting up environment..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    log_success ".env file created from template"
    log_warning "Please edit .env with your API keys!"
else
    log_success ".env file exists"
fi

# ============================================
# Create Directories
# ============================================
log_step "Creating directories..."

mkdir -p logs output temp .cache
log_success "Directories created"

# ============================================
# Install Ollama
# ============================================
if [ "$DOCKER_MODE" = false ] && [ "$SKIP_MODELS" = false ]; then
    log_step "Checking Ollama..."
    
    if ! command -v ollama &> /dev/null; then
        log_warning "Ollama not found"
        echo "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    
    if command -v ollama &> /dev/null; then
        log_success "Ollama found"
        
        log_step "Pulling LLM models (this may take a while)..."
        echo "Pulling qwen2.5-coder:7b-instruct-q8_0..."
        ollama pull qwen2.5-coder:7b-instruct-q8_0
        
        echo "Pulling qwen2.5-coder:14b-instruct-q4_K_M..."
        ollama pull qwen2.5-coder:14b-instruct-q4_K_M
        
        log_success "Models downloaded"
    fi
fi

# ============================================
# Docker Setup
# ============================================
if [ "$DOCKER_MODE" = true ]; then
    log_step "Setting up Docker..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker"
        exit 1
    fi
    
    echo "Building Docker images..."
    docker-compose -f docker/docker-compose.yml build
    
    echo "Starting services..."
    docker-compose -f docker/docker-compose.yml up -d
    
    log_success "Docker services started"
fi

# ============================================
# Verify Installation
# ============================================
log_step "Verifying installation..."

if python3 -c "import src; print('Module import successful')"; then
    log_success "Installation verified"
else
    log_error "Installation verification failed"
fi

# ============================================
# Print Next Steps
# ============================================
echo -e "${GREEN}"
echo ""
echo "============================================"
echo "   Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys:"
echo "   - GITHUB_TOKEN (required)"
echo "   - HUGGINGFACE_TOKEN (optional)"
echo "   - OPENAI_API_KEY (optional fallback)"
echo ""
echo "2. Start Ollama (if not using Docker):"
echo "   ollama serve"
echo ""
echo "3. Add to Windsurf mcp_config.json"
echo ""
echo "4. Run the MCP server:"
echo "   python -m src.mcp.server"
echo ""
echo "5. Run tests:"
echo "   pytest tests/ -v"
echo ""
echo "For help, see: docs/guides/DEVELOPMENT.md"
echo "============================================"
echo -e "${NC}"
