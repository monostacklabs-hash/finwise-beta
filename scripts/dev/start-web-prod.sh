#!/bin/bash
# Start the web application (production mode)
# Usage: ./scripts/dev/start-web-prod.sh

set -e

cd web
echo "🏗️  Building web app..."
npm run build

echo "🚀 Starting web app in production mode..."
npm run preview
