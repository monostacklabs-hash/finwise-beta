import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Assuming these are the correct import paths
from app.database.models import Transaction, User
from app.database.session import SessionLocal

class TestChatIntegration:
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for chat interactions"""
        db = SessionLocal()
        try:
            # Check if test user exists
            existing_user = db.query(User).filter(User.email == "test_chat@example.com").first()
            if not existing_user:
                # Create test user if not exists
                test_user = User(
                    email="test_chat@example.com",
                    password_hash="$2b$12$fakeHashForTestUser",  # Hashed password
                    name="Chat Test User",
                    timezone="UTC",
                    currency="USD"
                )
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
                return test_user
            return existing_user
        finally:
            db.close()

    @pytest.fixture(scope="class")
    def auth_token(self, test_user):
        """Get authentication token for test user"""
        from app.api.auth import create_access_token
        return create_access_token(data={"sub": test_user.id})

    def test_chat_transaction_recording(self, test_user, auth_token):
        """Test chat API can record a transaction"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

        # Prepare chat payload
        payload = {
            "message": "I spent $50 on groceries at Whole Foods",
            "chat_history": None
        }

        # Make chat request
        with httpx.Client(base_url="http://localhost:8000") as client:
            response = client.post("/api/v1/chat", json=payload, headers=headers)

        # Assertions
        assert response.status_code == 200, f"Chat API failed: {response.text}"

        # Check database for new transaction
        db = SessionLocal()
        try:
            # Find most recent transaction for the test user
            recent_transaction = (
                db.query(Transaction)
                .filter(Transaction.user_id == test_user.id)
                .order_by(Transaction.date.desc())
                .first()
            )

            assert recent_transaction is not None, "No transaction recorded"
            assert recent_transaction.amount == 50.0, "Transaction amount incorrect"
            assert recent_transaction.category is not None, "Transaction category not set"
        finally:
            db.close()

    def test_chat_multiple_messages(self, test_user, auth_token):
        """Test chat with multiple messages and context"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

        # Prepare chat payload with history
        chat_history = [
            {"role": "user", "content": "I want to save money"},
            {"role": "assistant", "content": "Great goal! Let's discuss ways to save."}
        ]
        payload = {
            "message": "How can I reduce my monthly expenses?",
            "chat_history": chat_history
        }

        # Make chat request
        with httpx.Client(base_url="http://localhost:8000") as client:
            response = client.post("/api/v1/chat", json=payload, headers=headers)

        # Assertions
        assert response.status_code == 200, f"Chat API failed: {response.text}"

        # Check response content
        response_data = response.json()
        assert "response" in response_data, "No response from AI"
        assert len(response_data["response"]) > 0, "Empty AI response"
        assert "tools_used" in response_data, "No tools used information"

    def test_chat_error_handling(self, test_user, auth_token):
        """Test chat API error handling"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

        # Test cases
        test_cases = [
            {"message": "", "expected_status": 400},  # Empty message
            {"message": "x" * 2000, "expected_status": 400},  # Too long message
            {"message": "<script>alert('XSS')</script>", "expected_status": 400},  # XSS attempt
        ]

        for case in test_cases:
            payload = {
                "message": case["message"],
                "chat_history": None
            }

            with httpx.Client(base_url="http://localhost:8000") as client:
                response = client.post("/api/v1/chat", json=payload, headers=headers)

            assert response.status_code == case["expected_status"], f"Unexpected response for payload: {payload}"