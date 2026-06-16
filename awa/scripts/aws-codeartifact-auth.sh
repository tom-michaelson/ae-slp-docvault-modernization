#!/usr/bin/env bash
# AWS CodeArtifact authentication script for uv package manager
# Works on macOS and Linux
# Returns 0 even on failure to allow chaining in make commands

# Don't use set -e to allow script to continue on errors

# Configuration
DOMAIN="slalom-all"
ACCOUNT_ID="825505919920"
REPOSITORY="slalom-pypi"
INDEX_NAME="slalom"
# Use CODEARTIFACT_AWS_PROFILE env var if set, otherwise default to slalom-codeartifact
DEFAULT_PROFILE="${CODEARTIFACT_AWS_PROFILE:-slalom-codeartifact}"

# Colors for output (if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_warning "AWS CLI is not installed. Skipping CodeArtifact authentication."
    print_warning "To enable private package access, please install AWS CLI."
    exit 0
fi

# Parse command line arguments
EXPORT_MODE=false
PROFILE="$DEFAULT_PROFILE"

while [[ $# -gt 0 ]]; do
    case $1 in
        --export)
            EXPORT_MODE=true
            shift
            ;;
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        *)
            # Unknown option
            shift
            ;;
    esac
done

# Get the authentication token
if [ "$EXPORT_MODE" = true ]; then
    # In export mode, suppress all output except the export commands
    TOKEN=$(aws codeartifact get-authorization-token \
        --domain "$DOMAIN" \
        --domain-owner "$ACCOUNT_ID" \
        --query authorizationToken \
        --output text \
        --profile "$PROFILE" 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$TOKEN" ]; then
        echo "export UV_INDEX_SLALOM_USERNAME=\"aws\""
        echo "export UV_INDEX_SLALOM_PASSWORD=\"$TOKEN\""
    else
        # In export mode, output empty exports so eval doesn't fail
        echo "# CodeArtifact authentication failed - private packages will not be accessible"
        exit 0
    fi
else
    # Interactive mode with detailed output
    print_info "Configuring AWS CodeArtifact authentication for uv"
    print_info "Domain: $DOMAIN"
    print_info "Account: $ACCOUNT_ID"
    print_info "Repository: $REPOSITORY"
    print_info "Profile: $PROFILE"
    echo

    print_info "Getting authentication token..."
    TOKEN=$(aws codeartifact get-authorization-token \
        --domain "$DOMAIN" \
        --domain-owner "$ACCOUNT_ID" \
        --query authorizationToken \
        --output text \
        --profile "$PROFILE" 2>&1)

    if [ $? -ne 0 ]; then
        print_warning "Failed to get CodeArtifact token"
        print_warning "Error details: $TOKEN"
        print_warning "Private packages will not be accessible"
        print_warning "Continuing anyway - public packages will still work"
        exit 0
    fi

    if [ -z "$TOKEN" ]; then
        print_warning "Empty token received from AWS CLI"
        print_warning "Private packages will not be accessible"
        exit 0
    fi

    print_info "${GREEN}Authentication successful!${NC}"
fi
