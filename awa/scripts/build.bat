@echo off
REM AWA Build Script for Windows

setlocal EnableDelayedExpansion

echo.
echo ^🚀 AWA Build Process
echo.

REM Step 1: Build UI assets
REM UI assets building temporarily disabled for package mode
REM echo ℹ️  Building UI assets...
REM uv run scripts\build_ui_assets.py
REM if %errorlevel% neq 0 (
REM     echo ❌ UI asset build failed
REM     pause
REM     exit /b 1
REM )
REM echo ✅ UI assets built successfully

REM Step 2: Build wheel
echo ℹ️  Building wheel package...
uv build
if %errorlevel% neq 0 (
    echo ❌ Wheel build failed
    pause
    exit /b 1
)
echo ✅ Wheel built successfully

REM Step 3: Show results
echo ℹ️  Build artifacts:
dir dist\

echo.
echo ✅ Build completed! Wheel is ready for installation.
echo ℹ️  To install: scripts\install.bat dist\slalom-agentic-workflow-accelerator-*.whl

pause
