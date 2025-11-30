#!/bin/bash

# Test script for recurring transaction update endpoint
# Tests the play/pause functionality

BASE_URL="http://localhost:8000"
TOKEN=""

echo "=========================================="
echo "Testing Recurring Transaction Update"
echo "=========================================="

# Step 1: Login
echo -e "\n1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✓ Login successful"

# Step 2: Create a recurring transaction
echo -e "\n2. Creating recurring transaction..."
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/recurring-transactions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "type": "expense",
    "amount": 15.99,
    "description": "Netflix Subscription",
    "category": "Entertainment",
    "frequency": "monthly",
    "next_date": "2025-12-01",
    "reminder_days_before": 3
  }')

RECURRING_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$RECURRING_ID" ]; then
  echo "❌ Failed to create recurring transaction"
  echo "Response: $CREATE_RESPONSE"
  exit 1
fi

echo "✓ Created recurring transaction: $RECURRING_ID"
echo "Response: $CREATE_RESPONSE"

# Step 3: Get recurring transactions (verify it's active)
echo -e "\n3. Getting recurring transactions..."
GET_RESPONSE=$(curl -s -X GET "$BASE_URL/recurring-transactions" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $GET_RESPONSE"

# Step 4: Pause the recurring transaction (is_active = false)
echo -e "\n4. Pausing recurring transaction (Play button → Pause)..."
PAUSE_RESPONSE=$(curl -s -X PUT "$BASE_URL/recurring-transactions/$RECURRING_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "is_active": false
  }')

echo "Response: $PAUSE_RESPONSE"

if echo "$PAUSE_RESPONSE" | grep -q '"is_active":false'; then
  echo "✓ Successfully paused"
else
  echo "❌ Failed to pause"
fi

# Step 5: Resume the recurring transaction (is_active = true)
echo -e "\n5. Resuming recurring transaction (Pause button → Play)..."
RESUME_RESPONSE=$(curl -s -X PUT "$BASE_URL/recurring-transactions/$RECURRING_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "is_active": true
  }')

echo "Response: $RESUME_RESPONSE"

if echo "$RESUME_RESPONSE" | grep -q '"is_active":true'; then
  echo "✓ Successfully resumed"
else
  echo "❌ Failed to resume"
fi

# Step 6: Update other fields
echo -e "\n6. Updating amount and description..."
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/recurring-transactions/$RECURRING_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "amount": 17.99,
    "description": "Netflix Premium Subscription"
  }')

echo "Response: $UPDATE_RESPONSE"

if echo "$UPDATE_RESPONSE" | grep -q '"amount":17.99'; then
  echo "✓ Successfully updated"
else
  echo "❌ Failed to update"
fi

# Step 7: Clean up - delete the test recurring transaction
echo -e "\n7. Cleaning up..."
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/recurring-transactions/$RECURRING_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $DELETE_RESPONSE"

if echo "$DELETE_RESPONSE" | grep -q '"success":true'; then
  echo "✓ Successfully deleted"
else
  echo "❌ Failed to delete"
fi

echo -e "\n=========================================="
echo "Test Complete!"
echo "=========================================="
