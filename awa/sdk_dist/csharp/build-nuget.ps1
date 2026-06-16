#!/usr/bin/env pwsh
<#
.SYNOPSIS
    NuGet package build script wrapper for Windows (PowerShell)

.DESCRIPTION
    This PowerShell script is a wrapper around the Python build script.

.EXAMPLE
    ./build-nuget.ps1
    Builds and packages
#>

[CmdletBinding()]
param()

# Set error handling
$ErrorActionPreference = 'Stop'

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonScript = Join-Path $ScriptDir "build_nuget.py"

# Check if Python script exists
if (-not (Test-Path $PythonScript)) {
    Write-Error "❌ Python build script not found: $PythonScript"
    exit 1
}

# Find Python 3
$PythonCmd = $null
$pythonCommands = @('python3', 'python', 'py')

foreach ($cmd in $pythonCommands) {
    try {
        $pythonVersion = & $cmd -c "import sys; print(sys.version_info[0])" 2>$null
        if ($pythonVersion -eq '3') {
            $PythonCmd = $cmd
            break
        }
    } catch {
        # Command not found, continue
    }
}

if (-not $PythonCmd) {
    Write-Error "❌ Python 3 is required but not found. Please install Python 3.7 or later."
    exit 1
}

try {
    # Execute the Python script (no arguments needed - uses defaults)
    & $PythonCmd $PythonScript

    # Check exit code
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
} catch {
    Write-Error "Failed to execute Python build script: $($_.Exception.Message)"
    exit 1
}
