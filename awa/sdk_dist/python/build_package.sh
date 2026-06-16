#!/bin/bash

# Cross-platform PyPI package build script wrapper for Unix/Linux/macOS
# This script provides a convenient shell interface to the Python build script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    cat << EOF
AWA Client Package Build Script

Usage: $0

Options:
    --help, -h            Show this help message

The script will:
1. Install dependencies
2. Run linting checks
3. Build package distributions
4. Generate checksums
5. Verify package contents
6. Test package installation

Build artifacts will be available in the 'dist/' directory.
EOF
}

# Function to detect Python executable
detect_python() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    else
        print_error "Python not found. Please install Python 3.12 or later."
        exit 1
    fi
}

# Function to check if we're in the right directory
check_directory() {
    if [[ ! -f "pyproject.toml" ]]; then
        print_error "pyproject.toml not found. Please run this script from the package root directory."
        exit 1
    fi

    if [[ ! -f "build_package.py" ]]; then
        print_error "build_package.py not found. Please ensure the build script is in the current directory."
        exit 1
    fi
}

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    local version_output

    if ! version_output=$($python_cmd --version 2>&1); then
        print_error "Failed to get Python version"
        exit 1
    fi

    # Extract version numbers
    local version=$(echo "$version_output" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 12 ]]; then
        print_error "Python 3.12 or later is required. Found: $version"
        exit 1
    fi

    print_success "Python version check passed: $version"
}

# Function to make script executable
make_executable() {
    if [[ ! -x "build_package.py" ]]; then
        chmod +x build_package.py
    fi
}

# Main function
main() {
    print_status "AWA Client Package Build Script"
    print_status "================================"

    # Check if we're in the right directory
    check_directory

    # Handle help flag early
    for arg in "$@"; do
        if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
            show_help
            exit 0
        fi
    done

    # Detect Python executable
    local python_cmd
    python_cmd=$(detect_python)
    print_status "Using Python executable: $python_cmd"

    # Check Python version
    check_python_version "$python_cmd"

    # Make build script executable
    make_executable

    # Check if virtual environment is activated
    if [[ -n "$VIRTUAL_ENV" ]]; then
        print_status "Virtual environment detected: $VIRTUAL_ENV"
    else
        print_warning "No virtual environment detected. Consider using 'uv' or activating a virtual environment."
    fi

    # Check for package manager
    if command -v uv >/dev/null 2>&1; then
        print_status "Package manager: uv (recommended)"
    elif command -v pip >/dev/null 2>&1; then
        print_status "Package manager: pip"
    else
        print_error "No package manager found. Please install 'uv' or 'pip'."
        exit 1
    fi

    # Run the Python build script
    print_status "Starting build process..."
    exec "$python_cmd" build_package.py
}

# Handle script interruption
trap 'print_warning "Build interrupted by user"; exit 130' INT

# Run main function with all arguments
main "$@"
