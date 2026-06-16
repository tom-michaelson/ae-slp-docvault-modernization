# Cross-platform PyPI package build script wrapper for Windows PowerShell
# This script provides a convenient PowerShell interface to the Python build script

[CmdletBinding()]
param(
    [switch]$Help
)

# Error handling
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    $color = switch ($Level) {
        "INFO"    { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR"   { "Red" }
        default   { "White" }
    }

    Write-Host "[$Level] $Message" -ForegroundColor $color
}

# Function to show help
function Show-Help {
    Write-Host @"
AWA Client Package Build Script

Usage: .\build_package.ps1

Options:
    -Help                 Show this help message

The script will:
1. Install dependencies
2. Run linting checks
3. Build package distributions
4. Generate checksums
5. Verify package contents
6. Test package installation

Build artifacts will be available in the 'dist/' directory.
"@
}

# Function to detect Python executable
function Get-PythonExecutable {
    $pythonCandidates = @("python", "python3", "py")

    foreach ($candidate in $pythonCandidates) {
        try {
            $version = & $candidate --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        catch {
            continue
        }
    }

    Write-ColoredOutput "Python not found. Please install Python 3.12 or later." "ERROR"
    exit 1
}

# Function to check if we're in the right directory
function Test-Directory {
    if (-not (Test-Path "pyproject.toml")) {
        Write-ColoredOutput "pyproject.toml not found. Please run this script from the package root directory." "ERROR"
        exit 1
    }

    if (-not (Test-Path "build_package.py")) {
        Write-ColoredOutput "build_package.py not found. Please ensure the build script is in the current directory." "ERROR"
        exit 1
    }
}

# Function to check Python version
function Test-PythonVersion {
    param([string]$PythonCommand)

    try {
        $versionOutput = & $PythonCommand --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColoredOutput "Failed to get Python version" "ERROR"
            exit 1
        }

        # Extract version numbers (e.g., "Python 3.12.0" -> "3.12.0")
        $version = ($versionOutput -replace "Python ", "").Trim()
        $versionParts = $version -split "\."
        $major = [int]$versionParts[0]
        $minor = [int]$versionParts[1]

        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
            Write-ColoredOutput "Python 3.12 or later is required. Found: $version" "ERROR"
            exit 1
        }

        Write-ColoredOutput "Python version check passed: $version" "SUCCESS"
    }
    catch {
        Write-ColoredOutput "Error checking Python version: $_" "ERROR"
        exit 1
    }
}

# Function to check for package managers
function Test-PackageManager {
    $hasUv = $false
    $hasPip = $false

    try {
        & uv --version 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $hasUv = $true
        }
    }
    catch {
        # uv not available
    }

    try {
        & pip --version 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $hasPip = $true
        }
    }
    catch {
        # pip not available
    }

    if ($hasUv) {
        Write-ColoredOutput "Package manager: uv (recommended)" "INFO"
    }
    elseif ($hasPip) {
        Write-ColoredOutput "Package manager: pip" "INFO"
    }
    else {
        Write-ColoredOutput "No package manager found. Please install 'uv' or 'pip'." "ERROR"
        exit 1
    }
}

# Function to check virtual environment
function Test-VirtualEnvironment {
    if ($env:VIRTUAL_ENV) {
        Write-ColoredOutput "Virtual environment detected: $env:VIRTUAL_ENV" "INFO"
    }
    elseif ($env:CONDA_DEFAULT_ENV) {
        Write-ColoredOutput "Conda environment detected: $env:CONDA_DEFAULT_ENV" "INFO"
    }
    else {
        Write-ColoredOutput "No virtual environment detected. Consider using 'uv' or activating a virtual environment." "WARNING"
    }
}

# Main function
function Main {
    Write-ColoredOutput "AWA Client Package Build Script" "INFO"
    Write-ColoredOutput "================================" "INFO"

    # Handle help flag
    if ($Help) {
        Show-Help
        exit 0
    }

    # Check if we're in the right directory
    Test-Directory

    # Detect Python executable
    $pythonCmd = Get-PythonExecutable
    Write-ColoredOutput "Using Python executable: $pythonCmd" "INFO"

    # Check Python version
    Test-PythonVersion -PythonCommand $pythonCmd

    # Check for package managers
    Test-PackageManager

    # Check virtual environment
    Test-VirtualEnvironment

    # Run the Python build script
    Write-ColoredOutput "Starting build process..." "INFO"

    try {
        & $pythonCmd "build_package.py"
        if ($LASTEXITCODE -ne 0) {
            Write-ColoredOutput "Build process failed with exit code: $LASTEXITCODE" "ERROR"
            exit $LASTEXITCODE
        }
    }
    catch {
        Write-ColoredOutput "Build process failed: $_" "ERROR"
        exit 1
    }
}

# Handle script interruption
trap {
    Write-ColoredOutput "Build interrupted by user" "WARNING"
    exit 130
}

# Run main function
Main
