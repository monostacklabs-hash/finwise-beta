#!/usr/bin/env python3
"""
Test script to verify chat agent behavior and database state
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "mail4areeb1@gmail.com"
PASSWORD = "password123"  # Adjust if different

def login():
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": EMAIL, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def send_chat_message(token, message):
    """Send a chat message to the agent"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": message,
        "chat_history": []
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        headers=headers,
        json=payload
    )
    return response.json()

def get_recurring_transactions(token):
    """Get recurring transactions"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/recurring-transactions",
        headers=headers
    )
    return response.json()

def get_transactions(token):
    """Get transactions"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/transactions?limit=50",
        headers=headers
    )
    return response.json()

def get_debts_loans(token):
    """Get debts and loans"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/debts-loans",
        headers=headers
    )
    return response.json()

if __name__ == "__main__":
    print("🔐 Logging in...")
    token = login()
    if not token:
        print("❌ Failed to login")
        exit(1)
    
    print("✅ Logged in successfully\n")
    
    # Check current state
    print("📊 Current Database State:")
    print("-" * 50)
    
    recurring = get_recurring_transactions(token)
    print(f"Recurring Transactions: {len(recurring)}")
    for r in recurring:
        print(f"  - {r['description']}: ${r['amount']} ({r['frequency']})")
    
    transactions = get_transactions(token)
    print(f"\nTransactions: {len(transactions)}")
    
    debts = get_debts_loans(token)
    print(f"Debts/Loans: {len(debts)}")
    
    print("\n" + "=" * 50)
    print("🧪 Testing Chat Agent")
    print("=" * 50)
    
    # Test adding a recurring expense
    test_message = "Set up a recurring expense of $90 for internet, monthly"
    print(f"\n📤 Sending: {test_message}")
    response = send_chat_message(token, test_message)
    print(f"📥 Response: {response['response'][:200]}...")
    print(f"Tools used: {response.get('tools_used', [])}")
    
    # Check if it was actually added
    print("\n🔍 Checking database after chat...")
    recurring_after = get_recurring_transactions(token)
    print(f"Recurring Transactions: {len(recurring_after)}")
    for r in recurring_after:
        print(f"  - {r['description']}: ${r['amount']} ({r['frequency']})")
    
    if len(recurring_after) > len(recurring):
        print("\n✅ SUCCESS: Data was actually added!")
    else:
        print("\n❌ PROBLEM: AI responded but didn't add data to database!")
