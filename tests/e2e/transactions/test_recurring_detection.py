#!/usr/bin/env python3
"""
Test script for recurring transaction pattern detection
Run this AFTER starting the backend to test with real API calls

Prerequisites:
1. Backend running: cd backend && python run.py
2. User registered and logged in
3. Set TOKEN environment variable with your auth token

Usage:
  export TOKEN="your-auth-token-here"
  python test_recurring_detection.py
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def get_token():
    """Get auth token from environment or prompt user"""
    import os
    token = os.environ.get('TOKEN')
    if not token:
        print("❌ No TOKEN environment variable set")
        print("\nTo get a token:")
        print("1. Register/Login via the app or API")
        print("2. Copy your access token")
        print("3. Run: export TOKEN='your-token-here'")
        print("4. Run this script again")
        exit(1)
    return token

def test_recurring_detection():
    """Test recurring pattern detection with real API calls"""
    print("🧪 Testing Smart Recurring Transaction Detection\n")
    print("="*60)
    
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Add similar transactions
    print("\n📝 Test 1: Adding similar transactions (Netflix)")
    print("-" * 60)
    
    transactions = [
        {"type": "expense", "amount": 14.99, "description": "Netflix", "category": "entertainment"},
        {"type": "expense", "amount": 14.99, "description": "Netflix subscription", "category": "entertainment"},
        {"type": "expense", "amount": 14.99, "description": "Netflix", "category": "entertainment"},
    ]
    
    for i, trans_data in enumerate(transactions, 1):
        print(f"\n  Adding transaction {i}/3...")
        response = requests.post(
            f"{BASE_URL}/transactions",
            headers=headers,
            json=trans_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Added: ${result['amount']} - {result['description']}")
            
            # Check if suggestion was returned
            if 'recurring_suggestion' in result:
                suggestion = result['recurring_suggestion']
                if suggestion['detected']:
                    print(f"\n  🔍 PATTERN DETECTED!")
                    print(f"     {suggestion['message']}")
                    pattern = suggestion['pattern']
                    print(f"     Frequency: {pattern['frequency']}")
                    print(f"     Confidence: {pattern['confidence']*100:.0f}%")
                    print(f"     Occurrences: {pattern['occurrences']}")
        else:
            print(f"  ❌ Error: {response.status_code}")
            print(f"     {response.text}")
        
        time.sleep(0.5)  # Small delay between requests
    
    # Test 2: Get all suggestions
    print("\n\n📊 Test 2: Getting all recurring suggestions")
    print("-" * 60)
    
    response = requests.get(
        f"{BASE_URL}/recurring-transactions/suggestions",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n  {result['message']}")
        
        if result['suggestions']:
            print(f"\n  Found {len(result['suggestions'])} pattern(s):\n")
            for i, pattern in enumerate(result['suggestions'], 1):
                print(f"  {i}. {pattern['description']}")
                print(f"     Amount: ${pattern['amount']}")
                print(f"     Frequency: {pattern['frequency']}")
                print(f"     Confidence: {pattern['confidence']*100:.0f}%")
                print(f"     Occurrences: {pattern['occurrences']}")
                print(f"     Next expected: {pattern['next_date']}")
                print()
    else:
        print(f"  ❌ Error: {response.status_code}")
        print(f"     {response.text}")
    
    # Test 3: Test via AI Chat
    print("\n\n💬 Test 3: Testing via AI Chat")
    print("-" * 60)
    
    chat_messages = [
        "What recurring patterns do you see in my transactions?",
        "Do I have any subscriptions?",
    ]
    
    for message in chat_messages:
        print(f"\n  User: {message}")
        response = requests.post(
            f"{BASE_URL}/chat",
            headers=headers,
            json={"message": message}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  AI: {result['response'][:200]}...")
            if result.get('tools_used'):
                print(f"  Tools used: {', '.join(result['tools_used'])}")
        else:
            print(f"  ❌ Error: {response.status_code}")
        
        time.sleep(1)
    
    print("\n" + "="*60)
    print("\n✅ All tests completed!")
    print("\n💡 Next steps:")
    print("   • Check the mobile app - suggestions should appear")
    print("   • Try: 'I spent $14.99 on Netflix' in chat")
    print("   • The AI should suggest automating it!")


if __name__ == "__main__":
    try:
        test_recurring_detection()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at http://localhost:8000")
        print("\nMake sure the backend is running:")
        print("  cd backend && python run.py")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
