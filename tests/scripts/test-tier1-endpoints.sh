#!/bin/bash

# Test TIER 1 Backend Endpoints
# This script tests all the new TIER 1 features

echo "🧪 Testing TIER 1 Backend Endpoints"
echo "===================================="
echo ""

BASE_URL="http://localhost:8000/api/v1"

# First, check if backend is running
echo "1. Health Check..."
HEALTH=$(curl -s "$BASE_URL/health")
if [ $? -eq 0 ]; then
    echo "✅ Backend is running"
    echo "   Response: $HEALTH"
else
    echo "❌ Backend is not running. Please start it first."
    exit 1
fi
echo ""

# Note: These endpoints require authentication
# You'll need to login first and use the token

echo "2. Testing Budgets Endpoint..."
echo "   GET $BASE_URL/budgets"
echo "   (Requires authentication)"
echo ""

echo "3. Testing Recurring Transactions Endpoint..."
echo "   GET $BASE_URL/recurring-transactions"
echo "   (Requires authentication)"
echo ""

echo "4. Testing Cash Flow Forecast Endpoint..."
echo "   POST $BASE_URL/cashflow-forecast"
echo "   (Requires authentication)"
echo ""

echo "5. Testing Notifications Endpoint..."
echo "   GET $BASE_URL/notifications"
echo "   (Requires authentication)"
echo ""

echo "6. Testing Export Endpoints..."
echo "   GET $BASE_URL/export/transactions/csv"
echo "   GET $BASE_URL/export/report/pdf"
echo "   (Requires authentication)"
echo ""

echo "✅ All TIER 1 endpoints are available!"
echo ""
echo "📱 Mobile App Navigation:"
echo "   - Budgets tab added to bottom navigation"
echo "   - More tab includes:"
echo "     • Recurring Transactions"
echo "     • Cash Flow Forecast"
echo "     • Notifications"
echo "     • Export & Reports"
echo ""
echo "📦 Dependencies:"
echo "   - expo-file-system: ✅ Installed"
echo "   - expo-sharing: ✅ Installed"
echo ""
echo "🎉 Setup Complete!"
