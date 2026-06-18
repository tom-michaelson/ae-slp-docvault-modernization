#!/bin/bash
# AWA Build Script for Unix-like systems (macOS/Linux)

set -e

# Colors for output
GREEN='\033[0;32m'
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

print_info() {
    print_colored "ℹ️  $1" "${BLUE}"
}

main() {
    print_header "AWA Build Process"

    # Step 1: Build UI assets
    # UI assets building temporarily disabled for package mode
    # print_info "Building UI assets..."
    # uv run scripts/build_ui_assets.py
    # print_success "UI assets built successfully"

    # Step 2: Build wheel
    print_info "Building wheel package..."
    uv build
    print_success "Wheel built successfully"

    # Step 3: Show results
    print_info "Build artifacts:"
    ls -la dist/

    echo ""
    print_success "Build completed! Wheel is ready for installation."
    print_info "To install: ./scripts/install.sh dist/slalom_agentic_workflow_accelerator*.whl"
}

# Run main function
main "$@"
