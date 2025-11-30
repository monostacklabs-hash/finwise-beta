#!/usr/bin/env python3
"""
Test script for provider fallback functionality
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def login():
    """Login and get token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def test_chat(token, message):
    """Send a chat message"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        headers=headers,
        json={"message": message}
    )
    return response

def main():
    print("=" * 60)
    print("TESTING PROVIDER FALLBACK")
    print("=" * 60)
    
    # Login
    print("\n1. Logging in...")
    token = login()
    if not token:
        print("❌ Login failed")
        return
    print("✅ Login successful")
    
    # Test chat
    print("\n2. Testing chat with Anthropic (primary)...")
    response = test_chat(token, "I spent $50 on groceries")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data.get('response', '')[:200]}")
        if 'usage' in data:
            print(f"📊 Token usage: {data['usage']}")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n3. Testing another message...")
    response = test_chat(token, "Show my recent transactions")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data.get('response', '')[:200]}")
        if 'usage' in data:
            print(f"📊 Token usage: {data['usage']}")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nCheck Docker logs for fallback messages:")
    print("docker logs fin-agent-backend --tail 50 | grep -E '(Attempting|Switching|Success|Creating)' ")

if __name__ == "__main__":
    main()
