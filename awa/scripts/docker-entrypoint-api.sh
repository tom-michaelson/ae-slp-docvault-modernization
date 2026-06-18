#!/bin/bash
set -e

# Set default values if environment variables are not set
AWA_API_HOST=${AWA_API_HOST:-0.0.0.0}
AWA_API_PORT=${AWA_API_PORT:-8001}

# Show configuration
echo "API Host: ${AWA_API_HOST}"
echo "API Port: ${AWA_API_PORT}"

# Function to handle shutdown signals
shutdown() {
    echo "Received shutdown signal, stopping API server..."
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Start the API server
echo "Starting AWA API Server..."
exec uv run -m awa.core.api
