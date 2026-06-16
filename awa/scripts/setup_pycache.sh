#!/bin/bash

# Set up centralized Python bytecode cache directory
# This script configures PYTHONPYCACHEPREFIX to store all __pycache__ files
# in a single pycache directory at the project root

PROJECT_ROOT=$(pwd)
PYCACHE_DIR="$PROJECT_ROOT/.cache/pycache"

# Clean up existing __pycache__ directories
echo "🧹 Cleaning up existing __pycache__ directories..."
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Existing __pycache__ directories removed!"
echo ""

# Clean up existing __pycache__ directories
echo "🧹 Cleaning up existing __pycache__ directories..."
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Existing __pycache__ directories removed!"
echo ""

# Create the centralized cache directory if it doesn't exist
mkdir -p "$PYCACHE_DIR"

# Export the environment variable
export PYTHONPYCACHEPREFIX="$PYCACHE_DIR"

echo "✅ Python bytecode cache configured!"
echo "📁 Cache directory: $PYCACHE_DIR"
echo "🔧 PYTHONPYCACHEPREFIX set to: $PYTHONPYCACHEPREFIX"
echo ""
echo "To make this permanent, add this line to your shell profile:"
echo "export PYTHONPYCACHEPREFIX=\"$PYCACHE_DIR\""
echo ""
echo "Or run: source setup_pycache.sh"
