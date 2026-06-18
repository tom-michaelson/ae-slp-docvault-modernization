#!/bin/bash
set -e

# Set default values if environment variables are not set
AWA_UI_HOST=${AWA_UI_HOST:-0.0.0.0}
AWA_UI_PORT=${AWA_UI_PORT:-4321}

# Function to handle shutdown signals
shutdown() {
    echo "Received shutdown signal, stopping UI server..."
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Start the UI server in production mode
echo "Starting AWA UI Server in production mode on $AWA_UI_HOST:$AWA_UI_PORT..."
cd ui
exec pnpm run preview --host "$AWA_UI_HOST" --port "$AWA_UI_PORT"
