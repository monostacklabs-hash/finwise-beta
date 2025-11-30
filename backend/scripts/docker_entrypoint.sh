#!/bin/bash
set -e

# Check if we should reset the database (for development)
if [ "${RESET_DB_ON_STARTUP:-false}" = "true" ]; then
    echo "⚠️  RESET_DB_ON_STARTUP=true - Dropping and recreating database..."
    python backend/scripts/reset_db_auto.py
else
    echo "🔧 Running database migrations..."
    python backend/scripts/init_db.py
fi

echo "🚀 Starting application..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
