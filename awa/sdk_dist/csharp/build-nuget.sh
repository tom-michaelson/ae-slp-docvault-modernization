#!/bin/bash

# NuGet package build script wrapper for Unix-like systems (Mac, Linux)

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/build_nuget.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Python build script not found: $PYTHON_SCRIPT"
    exit 1
fi

# Try to find Python 3
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if it's Python 3
    PYTHON_VERSION=$(python -c "import sys; print(sys.version_info[0])")
    if [ "$PYTHON_VERSION" = "3" ]; then
        PYTHON_CMD="python"
    else
        echo "❌ Python 3 is required but not found"
        exit 1
    fi
else
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Execute the Python script
exec "$PYTHON_CMD" "$PYTHON_SCRIPT"
