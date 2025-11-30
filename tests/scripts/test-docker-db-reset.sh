#!/bin/bash
# Test script to verify Docker DB reset functionality

set -e

echo "🧪 Testing Docker DB Reset Functionality"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.python.example .env
    echo "✅ Created .env file"
fi

echo "📋 Test Plan:"
echo "1. Start containers with RESET_DB_ON_STARTUP=false (default)"
echo "2. Verify database is created"
echo "3. Stop containers"
echo "4. Start containers with RESET_DB_ON_STARTUP=true"
echo "5. Verify database is dropped and recreated"
echo ""

read -p "Press Enter to start test 1 (default behavior)..."

echo ""
echo "🔧 Test 1: Starting with RESET_DB_ON_STARTUP=false"
echo "---------------------------------------------------"
RESET_DB_ON_STARTUP=false docker compose -f docker-compose.python.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

echo ""
echo "📊 Checking backend logs..."
docker logs fin-agent-backend | tail -20

echo ""
echo "✅ Test 1 complete. Stopping containers..."
docker compose -f docker-compose.python.yml down

echo ""
read -p "Press Enter to start test 2 (with DB reset)..."

echo ""
echo "🔧 Test 2: Starting with RESET_DB_ON_STARTUP=true"
echo "--------------------------------------------------"
RESET_DB_ON_STARTUP=true docker compose -f docker-compose.python.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

echo ""
echo "📊 Checking backend logs (should show DB drop/recreate)..."
docker logs fin-agent-backend | tail -30

echo ""
echo "✅ Test 2 complete. Stopping containers..."
docker compose -f docker-compose.python.yml down

echo ""
echo "=========================================="
echo "✅ All tests complete!"
echo ""
echo "Summary:"
echo "- Test 1: Normal startup (creates tables if not exist)"
echo "- Test 2: Reset startup (drops and recreates all tables)"
echo ""
echo "Check the logs above to verify:"
echo "- Test 1 should show: '🔧 Running database migrations...'"
echo "- Test 2 should show: '⚠️  RESET_DB_ON_STARTUP=true - Dropping and recreating database...'"
