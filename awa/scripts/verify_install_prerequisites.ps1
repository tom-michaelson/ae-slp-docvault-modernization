# PowerShell script wrapper for dependency verification
# This script calls the Python version of the dependency checker

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition

# Path to the Python script
$PythonScript = Join-Path $ScriptDir "verify_install_prerequisites.py"

# Check if Python script exists
if (-not (Test-Path $PythonScript)) {
    Write-Host "Error: Python script not found at $PythonScript" -ForegroundColor Red
    exit 1
}

# Function to test if a command exists
function Test-Command {
    param($CommandName)
    try {
        if (Get-Command $CommandName -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Try to run with uv first, then python, then python3, then py
$PythonCommands = @("uv run", "python", "python3", "py")
$PythonFound = $false

foreach ($PythonCmd in $PythonCommands) {
    if (Test-Command $PythonCmd) {
        try {
            # Pass all arguments to the Python script
            & $PythonCmd $PythonScript $args
            $PythonFound = $true
            break
        }
        catch {
            # Continue to next Python command if this one fails
            continue
        }
    }
}

if (-not $PythonFound) {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.12+ before running this script" -ForegroundColor Yellow
    exit 1
}
