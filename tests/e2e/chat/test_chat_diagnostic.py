"""
Diagnostic test to understand why chat agent isn't calling tools
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"diag_{int(time.time())}@example.com"
TEST_PASSWORD = "Test123!"

def test_diagnostic():
    # Register
    print("1. Registering user...")
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": "Diagnostic User"
    })
    data = response.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    print(f"   User ID: {user_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Simple expense
    print("\n2. Testing simple expense...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "message": "I spent $50 on groceries"
    }, headers=headers)
    
    chat_data = response.json()
    print(f"   Response: {chat_data['response']}")
    print(f"   Tools used: {chat_data.get('tools_used', [])}")
    print(f"   Success: {chat_data['success']}")
    
    # Check database via REST API
    print("\n3. Checking transactions via REST API...")
    response = requests.get(f"{BASE_URL}/transactions", headers=headers)
    tx_data = response.json()
    print(f"   Transactions found: {len(tx_data.get('transactions', []))}")
    if tx_data.get('transactions'):
        for tx in tx_data['transactions']:
            print(f"     - ${tx['amount']}: {tx['description']}")
    
    # Test 2: Direct REST API transaction
    print("\n4. Adding transaction via REST API (for comparison)...")
    response = requests.post(f"{BASE_URL}/transactions", json={
        "type": "expense",
        "amount": 25.0,
        "category": "food",
        "description": "Direct API test"
    }, headers=headers)
    print(f"   Status: {response.status_code}")
    
    # Check again
    print("\n5. Checking transactions again...")
    response = requests.get(f"{BASE_URL}/transactions", headers=headers)
    tx_data = response.json()
    print(f"   Transactions found: {len(tx_data.get('transactions', []))}")
    if tx_data.get('transactions'):
        for tx in tx_data['transactions']:
            print(f"     - ${tx['amount']}: {tx['description']}")
    
    print("\n" + "="*80)
    print("DIAGNOSIS:")
    print("="*80)
    if len(tx_data.get('transactions', [])) == 0:
        print("❌ PROBLEM: Chat agent is NOT calling tools")
        print("   The agent responds as if it did something, but no tools are executed")
    elif len(tx_data.get('transactions', [])) == 1:
        print("⚠️  PARTIAL: Only REST API transaction worked, chat agent didn't call tools")
    else:
        print("✅ SUCCESS: Both methods worked")

if __name__ == "__main__":
    test_diagnostic()
