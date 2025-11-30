"""
Test that persists database for inspection
Run this test, then inspect the database with: python inspect_test_db.py test_persist.db
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.models import Base, User, Transaction, Goal, DebtLoan, Budget
from app.database.session import get_db

# Test database that persists
TEST_DATABASE_URL = "sqlite:///./test_persist.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_PREFIX = "/api/v1"


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    # Create tables but DON'T drop them after test
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    # Commented out so DB persists: Base.metadata.drop_all(bind=engine)


def test_create_sample_data(client):
    """Create sample financial data for inspection"""
    print("\n" + "="*80)
    print("Creating sample financial data in test_persist.db")
    print("="*80)
    
    # Register user
    response = client.post(f"{API_PREFIX}/auth/register", json={
        "email": "john@example.com",
        "password": "Test123!",
        "name": "John Doe"
    })
    assert response.status_code == 201
    data = response.json()
    token = data["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add income
    print("\n1. Adding monthly salary...")
    response = client.post(f"{API_PREFIX}/chat", 
        json={"message": "My monthly salary is $6000"}, 
        headers=headers)
    print(f"   Response: {response.json()['response'][:100]}...")
    
    # Add expenses
    print("\n2. Adding expenses...")
    expenses = [
        "I spent $1200 on rent",
        "I spent $300 on groceries",
        "I spent $150 on utilities",
        "I spent $80 on gas",
        "I spent $50 on entertainment"
    ]
    for expense in expenses:
        response = client.post(f"{API_PREFIX}/chat", 
            json={"message": expense}, 
            headers=headers)
        print(f"   {expense} - ✅")
    
    # Add debt
    print("\n3. Adding credit card debt...")
    response = client.post(f"{API_PREFIX}/chat", 
        json={"message": "I have a credit card debt of $5000 at 18% interest, paying $250/month"}, 
        headers=headers)
    print(f"   Response: {response.json()['response'][:100]}...")
    
    # Add goal
    print("\n4. Setting savings goal...")
    response = client.post(f"{API_PREFIX}/chat", 
        json={"message": "I want to save $15,000 for a vacation by December 2026"}, 
        headers=headers)
    print(f"   Response: {response.json()['response'][:100]}...")
    
    # Create budget
    print("\n5. Creating budget...")
    response = client.post(f"{API_PREFIX}/chat", 
        json={"message": "Set a $400 monthly budget for food"}, 
        headers=headers)
    print(f"   Response: {response.json()['response'][:100]}...")
    
    # Get financial health
    print("\n6. Checking financial health...")
    response = client.post(f"{API_PREFIX}/chat", 
        json={"message": "How am I doing financially?"}, 
        headers=headers)
    print(f"   Response: {response.json()['response'][:200]}...")
    
    print("\n" + "="*80)
    print("✅ Sample data created successfully!")
    print("="*80)
    print("\nTo inspect the database, run:")
    print("  python inspect_test_db.py test_persist.db")
    print("="*80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
