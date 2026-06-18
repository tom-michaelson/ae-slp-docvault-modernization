# AWS CodeArtifact authentication script for uv package manager
# Works on Windows PowerShell and PowerShell Core
# Returns success even on failure to allow chaining in make commands

param(
    # Use CODEARTIFACT_AWS_PROFILE env var if set, otherwise default to slalom-codeartifact
    [string]$Profile = $(if ($env:CODEARTIFACT_AWS_PROFILE) { $env:CODEARTIFACT_AWS_PROFILE } else { "slalom-codeartifact" }),
    [switch]$Export
)

# Configuration
$Domain = "slalom-all"
$AccountId = "825505919920"
$Repository = "slalom-pypi"
$IndexName = "slalom"

# Colors for output
$Host.UI.RawUI.ForegroundColor = "White"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

# Check if AWS CLI is installed
try {
    $null = Get-Command aws -ErrorAction Stop
} catch {
    Write-Warning-Custom "AWS CLI is not installed. Skipping CodeArtifact authentication."
    Write-Warning-Custom "To enable private package access, please install AWS CLI."
    exit 0
}

# Get the authentication token
try {
    if ($Export) {
        # In export mode, suppress all output except the environment commands
        $Token = aws codeartifact get-authorization-token `
            --domain $Domain `
            --domain-owner $AccountId `
            --query authorizationToken `
            --output text `
            --profile $Profile 2>$null

        if ($LASTEXITCODE -eq 0 -and $Token) {
            Write-Output "`$env:UV_INDEX_SLALOM_USERNAME = 'aws'"
            Write-Output "`$env:UV_INDEX_SLALOM_PASSWORD = '$Token'"
        } else {
            Write-Output "# CodeArtifact authentication failed - private packages will not be accessible"
            exit 0
        }
    } else {
        # Interactive mode with detailed output
        Write-Info "Configuring AWS CodeArtifact authentication for uv"
        Write-Info "Domain: $Domain"
        Write-Info "Account: $AccountId"
        Write-Info "Repository: $Repository"
        Write-Info "Profile: $Profile"
        Write-Host ""

        Write-Info "Getting authentication token..."
        $Token = aws codeartifact get-authorization-token `
            --domain $Domain `
            --domain-owner $AccountId `
            --query authorizationToken `
            --output text `
            --profile $Profile 2>&1

        if ($LASTEXITCODE -ne 0) {
            Write-Warning-Custom "Failed to get CodeArtifact token"
            Write-Warning-Custom "Error details: $Token"
            Write-Warning-Custom "Private packages will not be accessible"
            Write-Warning-Custom "Continuing anyway - public packages will still work"
            exit 0
        }

        if (-not $Token) {
            Write-Warning-Custom "Empty token received from AWS CLI"
            Write-Warning-Custom "Private packages will not be accessible"
            exit 0
        }

        Write-Host ""
        Write-Info "Authentication successful!" -ForegroundColor Green
        Write-Host ""
        Write-Info "To use the token, run:"
        Write-Host "  `$env:UV_INDEX_SLALOM_USERNAME = 'aws'"
        Write-Host "  `$env:UV_INDEX_SLALOM_PASSWORD = '<token>'"
        Write-Host ""
        Write-Info "Or run this to set the environment variables:"
        Write-Host "  . .\scripts\aws-codeartifact-auth.ps1 -Export | Invoke-Expression"
        Write-Host ""
        Write-Info "The token will expire in 12 hours. Re-run this script to refresh."
    }
} catch {
    Write-Warning-Custom "An error occurred: $_"
    Write-Warning-Custom "Private packages will not be accessible"
    exit 0
}
