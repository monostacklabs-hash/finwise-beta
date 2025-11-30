#!/usr/bin/env python3
"""
Demo script showing advanced budgeting and forecasting features

Run this after starting the backend:
    docker compose -f docker-compose.python.yml up

Then:
    python examples/advanced_features_demo.py
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# Demo user credentials
EMAIL = "demo@example.com"
PASSWORD = "demo123"
NAME = "Demo User"


def register_or_login():
    """Register or login to get access token"""
    # Try to register
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": EMAIL, "password": PASSWORD, "name": NAME}
    )
    
    if response.status_code == 201:
        print("✅ Registered new user")
        return response.json()["access_token"]
    
    # If registration fails, try login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        print("✅ Logged in")
        return response.json()["access_token"]
    
    raise Exception("Failed to register or login")


def chat(token, message):
    """Send a chat message to the AI agent"""
    print(f"\n💬 You: {message}")
    response = requests.post(
        f"{BASE_URL}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": message}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"🤖 AI: {result['response']}")
        return result
    else:
        print(f"❌ Error: {response.text}")
        return None


def demo_hierarchical_categories(token):
    """Demo hierarchical category system"""
    print("\n" + "="*60)
    print("DEMO 1: Hierarchical Categories")
    print("="*60)
    
    # Get all categories
    response = requests.get(
        f"{BASE_URL}/categories",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📁 Total categories: {len(data['categories'])}")
        print(f"Root categories: {list(data['hierarchy'].keys())}")
    
    # Get category path
    response = requests.get(
        f"{BASE_URL}/categories/fresh_produce/path",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🔍 Category: {data['category']}")
        print(f"   Full path: {data['path']}")
        print(f"   Root: {data['root']}")
        print(f"   Parent: {data['parent']}")
        print(f"   Children: {data['children']}")


def demo_dynamic_budgeting(token):
    """Demo dynamic budget adjustments"""
    print("\n" + "="*60)
    print("DEMO 2: Dynamic Budget Adjustments")
    print("="*60)
    
    # Create some budgets
    chat(token, "Set a $500 monthly budget for dining_out")
    chat(token, "Set a $400 monthly budget for groceries")
    chat(token, "Set a $200 monthly budget for entertainment")
    
    # Add some transactions (overspend in dining)
    for i in range(10):
        chat(token, f"I spent $60 at restaurant {i}")
    
    # Analyze budgets
    chat(token, "Should I adjust my budgets?")


def demo_goal_milestones(token):
    """Demo AI-adjusted goal milestones"""
    print("\n" + "="*60)
    print("DEMO 3: AI-Adjusted Goal Milestones")
    print("="*60)
    
    # Create a goal
    target_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    chat(token, f"I want to save $10,000 for an emergency fund by {target_date}")
    
    # Add some income and expenses to establish savings rate
    chat(token, "My monthly salary is $5000")
    chat(token, "I spent $3500 on living expenses this month")
    
    # Check goal milestones
    chat(token, "How am I tracking on my goals?")


def demo_financial_simulation(token):
    """Demo financial simulations"""
    print("\n" + "="*60)
    print("DEMO 4: Financial Simulations (What-If Scenarios)")
    print("="*60)
    
    # Simulate income increase
    chat(token, "What if I save $500 more per month?")
    
    # Simulate expense reduction
    chat(token, "What if I cut my spending by $300 per month?")
    
    # Simulate new subscription
    chat(token, "Can I afford a $99/month gym membership?")


def main():
    """Run all demos"""
    print("🚀 Advanced Features Demo")
    print("="*60)
    
    try:
        # Get access token
        token = register_or_login()
        
        # Run demos
        demo_hierarchical_categories(token)
        demo_dynamic_budgeting(token)
        demo_goal_milestones(token)
        demo_financial_simulation(token)
        
        print("\n" + "="*60)
        print("✅ Demo completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the backend is running:")
        print("  docker compose -f docker-compose.python.yml up")


if __name__ == "__main__":
    main()
