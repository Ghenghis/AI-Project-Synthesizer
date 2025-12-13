@echo off
REM ============================================================
REM Enterprise Test Generator - Windows Batch Script
REM ============================================================
REM Generates 6000+ tests for 100% code coverage
REM Uses multi-threading for maximum speed
REM ============================================================

setlocal enabledelayedexpansion

cd /d %~dp0..

echo.
echo ============================================================
echo   ENTERPRISE TEST GENERATOR
echo   Target: 100%% Code Coverage
echo   Tests: 6000+ Unit, 300+ Integration, 200+ E2E
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Check argument
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=help

if "%COMMAND%"=="help" goto :help
if "%COMMAND%"=="analyze" goto :analyze
if "%COMMAND%"=="generate" goto :generate
if "%COMMAND%"=="run" goto :run
if "%COMMAND%"=="coverage" goto :coverage
if "%COMMAND%"=="full" goto :full

:help
echo Usage: generate_tests.bat [command]
echo.
echo Commands:
echo   analyze   - Analyze codebase and estimate tests needed
echo   generate  - Generate all test files
echo   run       - Run all tests in parallel
echo   coverage  - Run tests with coverage report
echo   full      - Complete pipeline (generate + run + coverage)
echo.
echo Examples:
echo   generate_tests.bat analyze
echo   generate_tests.bat generate
echo   generate_tests.bat full
echo.
goto :eof

:analyze
echo [STEP 1] Analyzing codebase...
python scripts\run_test_generator.py analyze --project . --workers 16
goto :eof

:generate
echo [STEP 1] Generating tests...
python scripts\run_test_generator.py generate --project . --output tests\generated --workers 16
echo.
echo Tests generated in: tests\generated\
goto :eof

:run
echo [STEP 1] Running tests in parallel...
python scripts\run_test_generator.py run --project . --workers 16 --report test_results.json
goto :eof

:coverage
echo [STEP 1] Running tests with coverage...
python scripts\run_test_generator.py coverage --project . --workers 16
echo.
echo Coverage report: htmlcov\index.html
goto :eof

:full
echo Starting full pipeline...
echo.

echo [STEP 1/4] Analyzing codebase...
python scripts\run_test_generator.py analyze --project . --workers 16

echo.
echo [STEP 2/4] Generating tests...
python scripts\run_test_generator.py generate --project . --output tests\generated --workers 16 --overwrite

echo.
echo [STEP 3/4] Running tests...
python scripts\run_test_generator.py run --project . --workers 16 --generated-only --report test_results.json

echo.
echo [STEP 4/4] Generating coverage report...
python -m pytest tests\generated\ --cov=src --cov-report=html --cov-report=term -n 16

echo.
echo ============================================================
echo   PIPELINE COMPLETE
echo ============================================================
echo   Test Results: test_results.json
echo   Coverage:     htmlcov\index.html
echo ============================================================
goto :eof

:eof
endlocal
