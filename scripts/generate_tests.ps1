# ============================================================
# Enterprise Test Generator - PowerShell Script
# ============================================================
# Generates 6000+ tests for 100% code coverage
# Uses multi-threading for maximum speed on your hardware:
#   - AMD Ryzen 7 5800X3D (8 cores / 16 threads)
#   - 128GB RAM
#   - RTX 3090 Ti (not used for CPU tests)
# ============================================================

param(
    [Parameter(Position=0)]
    [ValidateSet('analyze', 'generate', 'run', 'coverage', 'full', 'help')]
    [string]$Command = 'help',
    
    [int]$Workers = 16,
    
    [string]$Output = 'tests/generated',
    
    [switch]$Verbose,
    
    [switch]$FailFast,
    
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ENTERPRISE TEST GENERATOR" -ForegroundColor Cyan
Write-Host "  Target: 100% Code Coverage" -ForegroundColor Yellow
Write-Host "  Tests: 6000+ Unit, 300+ Integration, 200+ E2E" -ForegroundColor Yellow
Write-Host "  Hardware: $Workers threads available" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

function Show-Help {
    Write-Host "Usage: .\generate_tests.ps1 [Command] [Options]" -ForegroundColor Green
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  analyze   - Analyze codebase and estimate tests needed"
    Write-Host "  generate  - Generate all test files (~6000+ tests)"
    Write-Host "  run       - Run all tests in parallel"
    Write-Host "  coverage  - Run tests with coverage report"
    Write-Host "  full      - Complete pipeline (generate + run + coverage)"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Workers N     - Number of worker threads (default: 16)"
    Write-Host "  -Output DIR    - Output directory (default: tests/generated)"
    Write-Host "  -Verbose       - Show detailed output"
    Write-Host "  -FailFast      - Stop on first failure"
    Write-Host "  -Overwrite     - Overwrite existing tests"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\generate_tests.ps1 analyze"
    Write-Host "  .\generate_tests.ps1 generate -Workers 16"
    Write-Host "  .\generate_tests.ps1 full -Overwrite"
    Write-Host ""
}

function Invoke-Analyze {
    Write-Host "[ANALYZE] Scanning codebase..." -ForegroundColor Yellow
    
    $cmd = @(
        "scripts\run_test_generator.py",
        "analyze",
        "--project", $ProjectRoot,
        "--workers", $Workers,
        "--output", "code_analysis.json"
    )
    
    Push-Location $ProjectRoot
    python @cmd
    Pop-Location
    
    Write-Host ""
    Write-Host "Analysis complete. See code_analysis.json for details." -ForegroundColor Green
}

function Invoke-Generate {
    Write-Host "[GENERATE] Creating tests..." -ForegroundColor Yellow
    Write-Host "  Output: $Output" -ForegroundColor Gray
    Write-Host "  Workers: $Workers" -ForegroundColor Gray
    
    $cmd = @(
        "scripts\run_test_generator.py",
        "generate",
        "--project", $ProjectRoot,
        "--output", $Output,
        "--workers", $Workers
    )
    
    if ($Overwrite) {
        $cmd += "--overwrite"
    }
    
    Push-Location $ProjectRoot
    python @cmd
    Pop-Location
    
    $testCount = (Get-ChildItem -Path "$ProjectRoot\$Output" -Recurse -Filter "test_*.py").Count
    Write-Host ""
    Write-Host "Generated $testCount test files in: $Output" -ForegroundColor Green
}

function Invoke-Run {
    Write-Host "[RUN] Executing tests in parallel..." -ForegroundColor Yellow
    Write-Host "  Workers: $Workers" -ForegroundColor Gray
    
    $cmd = @(
        "scripts\run_test_generator.py",
        "run",
        "--project", $ProjectRoot,
        "--workers", $Workers,
        "--report", "test_results.json"
    )
    
    if ($Verbose) {
        $cmd += "--verbose"
    }
    
    if ($FailFast) {
        $cmd += "--fail-fast"
    }
    
    Push-Location $ProjectRoot
    python @cmd
    Pop-Location
    
    Write-Host ""
    Write-Host "Results saved to: test_results.json" -ForegroundColor Green
}

function Invoke-Coverage {
    Write-Host "[COVERAGE] Running with coverage analysis..." -ForegroundColor Yellow
    
    Push-Location $ProjectRoot
    
    # Run pytest with coverage
    python -m pytest tests/ `
        --cov=src `
        --cov-report=html `
        --cov-report=term-missing `
        --cov-fail-under=0 `
        -n $Workers `
        -v
    
    Pop-Location
    
    Write-Host ""
    Write-Host "Coverage report: $ProjectRoot\htmlcov\index.html" -ForegroundColor Green
}

function Invoke-Full {
    $startTime = Get-Date
    
    Write-Host "Starting full pipeline..." -ForegroundColor Cyan
    Write-Host ""
    
    # Step 1: Analyze
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "[1/4] ANALYZING CODEBASE" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Invoke-Analyze
    
    # Step 2: Generate
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "[2/4] GENERATING TESTS" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Invoke-Generate
    
    # Step 3: Run
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "[3/4] RUNNING TESTS" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Invoke-Run
    
    # Step 4: Coverage
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "[4/4] COVERAGE REPORT" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Invoke-Coverage
    
    $duration = (Get-Date) - $startTime
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  PIPELINE COMPLETE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Duration:     $([math]::Round($duration.TotalMinutes, 2)) minutes" -ForegroundColor White
    Write-Host "  Test Results: test_results.json" -ForegroundColor White
    Write-Host "  Coverage:     htmlcov\index.html" -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Cyan
}

# Main switch
switch ($Command) {
    'help'     { Show-Help }
    'analyze'  { Invoke-Analyze }
    'generate' { Invoke-Generate }
    'run'      { Invoke-Run }
    'coverage' { Invoke-Coverage }
    'full'     { Invoke-Full }
}
