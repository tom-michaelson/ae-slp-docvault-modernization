#!/bin/bash
set -e

# Function to handle shutdown signals
shutdown() {
    echo "Received shutdown signal, stopping API server..."
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Start Temporal Worker
echo "Starting AWA Worker..."
exec uv run -m awa.core.engine.temporal_worker
