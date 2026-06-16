#!/bin/bash
# Cross-platform shell script wrapper for dependency verification
# This script calls the Python version of the dependency checker

# Get the directory where this script is located
# Use BASH_SOURCE if available (bash), otherwise fall back to $0 (POSIX shell)
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

# Path to the Python script
PYTHON_SCRIPT="$SCRIPT_DIR/verify_install_prerequisites.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Try to run with uv first, then python3, then python
if command -v uv &> /dev/null; then
    uv run "$PYTHON_SCRIPT" "$@"
elif command -v python3 &> /dev/null; then
    python3 "$PYTHON_SCRIPT" "$@"
elif command -v python &> /dev/null; then
    python "$PYTHON_SCRIPT" "$@"
else
    echo "Error: Python not found in PATH"
    echo "Please install Python 3.12+ before running this script"
    exit 1
fi
