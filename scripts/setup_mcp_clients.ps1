# AI Project Synthesizer - MCP Client Setup Script
# Run this script to configure MCP for Windsurf, Claude Desktop, and LM Studio

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Project Synthesizer - MCP Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = "C:\Users\Admin\AI_Synthesizer"
$ConfigDir = "$ProjectRoot\config"

# ========================================
# 1. WINDSURF SETUP
# ========================================
Write-Host "[1/3] Setting up Windsurf MCP..." -ForegroundColor Yellow

$WindsurfConfigDir = "$env:USERPROFILE\.windsurf"
$WindsurfConfigFile = "$WindsurfConfigDir\mcp_config.json"

# Create directory if not exists
if (-not (Test-Path $WindsurfConfigDir)) {
    New-Item -ItemType Directory -Path $WindsurfConfigDir -Force | Out-Null
}

# Copy config
Copy-Item "$ConfigDir\mcp_windsurf.json" $WindsurfConfigFile -Force
Write-Host "  Done - Windsurf config installed: $WindsurfConfigFile" -ForegroundColor Green

# ========================================
# 2. CLAUDE DESKTOP SETUP
# ========================================
Write-Host "[2/3] Setting up Claude Desktop MCP..." -ForegroundColor Yellow

$ClaudeConfigDir = "$env:APPDATA\Claude"
$ClaudeConfigFile = "$ClaudeConfigDir\claude_desktop_config.json"

# Create directory if not exists
if (-not (Test-Path $ClaudeConfigDir)) {
    New-Item -ItemType Directory -Path $ClaudeConfigDir -Force | Out-Null
}

# Copy config (simple approach - just copy the file)
Copy-Item "$ConfigDir\mcp_claude_desktop.json" $ClaudeConfigFile -Force
Write-Host "  Done - Claude Desktop config installed: $ClaudeConfigFile" -ForegroundColor Green

# ========================================
# 3. LM STUDIO SETUP
# ========================================
Write-Host "[3/3] Setting up LM Studio MCP..." -ForegroundColor Yellow

$LMStudioConfigDir = "$env:USERPROFILE\.lmstudio"
$LMStudioMCPDir = "$LMStudioConfigDir\mcp-servers"

# Create directory if not exists
if (-not (Test-Path $LMStudioMCPDir)) {
    New-Item -ItemType Directory -Path $LMStudioMCPDir -Force | Out-Null
}

# Copy config
Copy-Item "$ConfigDir\lmstudio_mcp_config.json" "$LMStudioMCPDir\ai-project-synthesizer.json" -Force
Write-Host "  Done - LM Studio config installed: $LMStudioMCPDir\ai-project-synthesizer.json" -ForegroundColor Green

# ========================================
# SUMMARY
# ========================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration files installed:" -ForegroundColor White
Write-Host "  Windsurf:       $WindsurfConfigFile" -ForegroundColor Gray
Write-Host "  Claude Desktop: $ClaudeConfigFile" -ForegroundColor Gray
Write-Host "  LM Studio:      $LMStudioMCPDir\ai-project-synthesizer.json" -ForegroundColor Gray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Start LM Studio and load a model (7B recommended)" -ForegroundColor White
Write-Host "  2. Restart Windsurf/Claude Desktop to load MCP servers" -ForegroundColor White
Write-Host "  3. Update GITHUB_TOKEN in config files if needed" -ForegroundColor White
Write-Host ""
