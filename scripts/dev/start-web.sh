#!/bin/bash
# Start the web application (development mode)
# Usage: ./scripts/dev/start-web.sh

set -e

cd web
echo "🚀 Starting web app in development mode..."
npm run dev
