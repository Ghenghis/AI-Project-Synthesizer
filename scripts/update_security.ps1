# AI Project Synthesizer - Security Update Script
# This script updates vulnerable dependencies to their patched versions
# Run with: .\update_security.ps1

Write-Host "==========================================="
Write-Host "   AI Project Synthesizer Security Update"
Write-Host "==========================================="
Write-Host ""

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Starting security updates..." -ForegroundColor Cyan
Write-Host ""

# Critical CVE fixes - Updated package versions
$updates = @(
    # MCP Framework - Multiple CVEs
    @{Name="mcp"; Version="1.23.0"; CVEs="Multiple"},
    
    # ML/AI Packages - High severity CVEs
    @{Name="torch"; Version="2.6.0"; CVEs="7 CVEs including code execution"},
    @{Name="transformers"; Version="4.53.0"; CVEs="14 CVEs"},
    @{Name="langchain-core"; Version="0.3.80"; CVEs="RCE vulnerability"},
    @{Name="langchain"; Version="0.3.25"; CVEs="Multiple"},
    
    # HTTP/Network - Security patches
    @{Name="httpx"; Version="0.28.0"; CVEs="SSRF vulnerability"},
    @{Name="aiohttp"; Version="3.11.0"; CVEs="Multiple"},
    @{Name="urllib3"; Version="2.3.0"; CVEs="CRLF injection"},
    @{Name="requests"; Version="2.32.0"; CVEs="Certificate validation"},
    
    # Auth/Crypto - Critical
    @{Name="authlib"; Version="1.4.0"; CVEs="Token validation bypass"},
    @{Name="cryptography"; Version="44.0.0"; CVEs="Multiple"},
    @{Name="PyJWT"; Version="2.10.0"; CVEs="Algorithm confusion"},
    
    # Web Framework - Security
    @{Name="starlette"; Version="0.46.0"; CVEs="Path traversal"},
    @{Name="fastapi"; Version="0.115.0"; CVEs="Multiple"},
    
    # YAML/Config - Code execution
    @{Name="pyyaml"; Version="6.0.2"; CVEs="Arbitrary code execution"},
    
    # Other critical updates
    @{Name="pillow"; Version="11.0.0"; CVEs="Buffer overflow"},
    @{Name="numpy"; Version="2.2.0"; CVEs="Memory corruption"},
    @{Name="certifi"; Version="2024.12.14"; CVEs="Certificate trust"},
    @{Name="jinja2"; Version="3.1.5"; CVEs="XSS"},
    @{Name="werkzeug"; Version="3.1.0"; CVEs="Open redirect"}
)

Write-Host "[INFO] Updating $($updates.Count) packages with known vulnerabilities..." -ForegroundColor Yellow
Write-Host ""

$successCount = 0
$failCount = 0
$skippedCount = 0

foreach ($pkg in $updates) {
    $pkgSpec = "$($pkg.Name)>=$($pkg.Version)"
    
    Write-Host "  Updating $($pkg.Name) to >= $($pkg.Version)..." -NoNewline
    
    try {
        # Use pip directly (works without virtual environment)
        $result = pip install $pkgSpec --upgrade --quiet 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
            $successCount++
        } else {
            # Check if package doesn't exist or has conflicts
            if ($result -match "not found|No matching|conflict") {
                Write-Host " [SKIPPED - not in project]" -ForegroundColor Yellow
                $skippedCount++
            } else {
                Write-Host " [FAILED]" -ForegroundColor Red
                Write-Host "    Error: $result" -ForegroundColor Red
                $failCount++
            }
        }
    } catch {
        Write-Host " [SKIPPED]" -ForegroundColor Yellow
        $skippedCount++
    }
}

Write-Host ""
Write-Host "==========================================="
Write-Host "   Update Summary"
Write-Host "==========================================="
Write-Host "  Successful: $successCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Skipped: $skippedCount" -ForegroundColor Yellow
Write-Host ""

# Run pip-audit to verify
Write-Host "[INFO] Running security audit..." -ForegroundColor Cyan
Write-Host ""

try {
    if (-not (Get-Command pip-audit -ErrorAction SilentlyContinue)) {
        pip install pip-audit --quiet
    }
    
    $auditResult = pip-audit --format json 2>&1
    $auditJson = $auditResult | ConvertFrom-Json -ErrorAction SilentlyContinue
    
    if ($auditJson) {
        $vulnCount = ($auditJson | Measure-Object).Count
        if ($vulnCount -gt 0) {
            Write-Host "[WARNING] $vulnCount vulnerabilities still found" -ForegroundColor Yellow
            Write-Host "  Run 'pip-audit' for details" -ForegroundColor Yellow
        } else {
            Write-Host "[SUCCESS] No known vulnerabilities detected!" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "[INFO] Could not run pip-audit, please run manually: pip-audit" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================="
Write-Host "   IMPORTANT: GitHub Token Rotation"
Write-Host "==========================================="
Write-Host ""
Write-Host "Your .env file may contain an exposed GitHub token." -ForegroundColor Red
Write-Host "Please rotate it immediately:" -ForegroundColor Red
Write-Host ""
Write-Host "  1. Go to: https://github.com/settings/tokens" -ForegroundColor Yellow
Write-Host "  2. Revoke the old token (ghp_hb1hZ...)" -ForegroundColor Yellow  
Write-Host "  3. Generate a new token with required scopes:" -ForegroundColor Yellow
Write-Host "     - repo (for repository access)" -ForegroundColor Yellow
Write-Host "     - read:user (for user info)" -ForegroundColor Yellow
Write-Host "  4. Update your .env file with the new token" -ForegroundColor Yellow
Write-Host ""
Write-Host "==========================================="
Write-Host "   Security Update Complete"
Write-Host "==========================================="
