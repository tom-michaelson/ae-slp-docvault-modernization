#!/bin/bash
# AWA Installation Script for Unix-like systems (macOS/Linux)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_colored() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    echo ""
    print_colored "🚀 $1" "${BOLD}${CYAN}"
    echo ""
}

print_success() {
    print_colored "✅ $1" "${GREEN}"
}

print_error() {
    print_colored "❌ $1" "${RED}"
}

print_warning() {
    print_colored "⚠️  $1" "${YELLOW}"
}

print_info() {
    print_colored "ℹ️  $1" "${BLUE}"
}

print_usage() {
    echo "Usage: $0 [OPTIONS] [WHEEL_PATH]"
    echo ""
    echo "Options:"
    echo "  --force     Force installation/upgrade even if backup fails"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 path/to/awa-wheel.whl"
    echo "  $0 --force path/to/awa-wheel.whl"
    echo ""
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        return 1
    fi

    # Check Python version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"; then
        print_error "Python 3.12+ required, found $python_version"
        return 1
    fi

    print_success "Python $python_version ✓"
    return 0
}

main() {
    # Parse arguments
    if [[ "$1" == "--help" ]]; then
        print_usage
        exit 0
    fi

    print_header "AWA Installation/Upgrade"

    # Check if Python is available
    if ! check_python; then
        print_error "Python 3.12+ is required but not found"
        print_info "Please install Python 3.12+ and try again"

        # Platform-specific installation instructions
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_info "macOS: brew install python@3.12"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            print_info "Ubuntu/Debian: sudo apt update && sudo apt install python3.12"
            print_info "CentOS/RHEL: sudo yum install python3.12"
        fi

        exit 1
    fi

    # Check if installation script exists
    if [[ ! -f "$INSTALL_SCRIPT" ]]; then
        print_error "Installation script not found: $INSTALL_SCRIPT"
        exit 1
    fi

    # Run the Python installation script with all arguments
    print_info "Running AWA installation script..."
    python3 "$INSTALL_SCRIPT" "$@"
}

# Run main function with all arguments
main "$@"
