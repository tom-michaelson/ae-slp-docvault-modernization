@echo off
REM AWA Installation Script for Windows

setlocal EnableDelayedExpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "INSTALL_SCRIPT=%SCRIPT_DIR%install.py"

REM Check for help flag
if "%1"=="--help" (
    echo Usage: %0 [OPTIONS] [WHEEL_PATH]
    echo.
    echo Options:
    echo   --force     Force installation/upgrade even if backup fails
    echo   --help      Show this help message
    echo.
    echo Examples:
    echo   %0 path\to\awa-wheel.whl
    echo   %0 --force path\to\awa-wheel.whl
    echo.
    pause
    exit /b 0
)

REM Check if Python is available
echo.
echo ^🚀 AWA Installation/Upgrade
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo ℹ️  Please install Python 3.12+ from https://python.org/downloads/
    echo ℹ️  Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "python_version=%%i"
echo ✅ Python %python_version% found

REM Check if Python version is 3.12+
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.12+ required, found %python_version%
    echo ℹ️  Please upgrade Python from https://python.org/downloads/
    pause
    exit /b 1
)

REM Check if installation script exists
if not exist "%INSTALL_SCRIPT%" (
    echo ❌ Installation script not found: %INSTALL_SCRIPT%
    pause
    exit /b 1
)

REM Run the Python installation script with all arguments
echo ℹ️  Running AWA installation script...
python "%INSTALL_SCRIPT%" %*

REM Check if installation was successful
if %errorlevel% neq 0 (
    echo.
    echo ❌ Installation failed
    pause
    exit /b 1
)

echo.
echo ✅ Installation/upgrade completed successfully!
pause
