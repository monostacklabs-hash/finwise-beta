#!/usr/bin/env python3
"""
E2E Test: Chat Agent Behavior and Database State
Tests the chat agent's ability to process messages and update database correctly.
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
    raise Exception(f"Login failed: {response.status_code}")

if __name__ == "__main__":
    print("🧪 Testing Chat Agent...")
    token = login()
    print(f"✅ Logged in successfully")
    # Add more test logic here
