#!/bin/bash
# Start the Python backend API server
# Usage: ./scripts/dev/start-backend.sh

set -e

echo "🚀 Starting backend API server..."
docker compose -f docker-compose.python.yml up
