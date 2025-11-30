"""
E2E Test using PRODUCTION DATABASE
⚠️ WARNING: This will write real data to your production database!

This test uses:
- Real business logic (same as production)
- Real database (same as production)
- Real LLM agent (same as production)
- Real tools and services (same as production)

Run with: pytest backend/tests/test_production_db.py -v -s
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.main import app
from app.database.models import Base, User, Transaction, Goal, DebtLoan, Budget
from app.database.models import TransactionType
from app.database.session import get_db
from app.config import settings

# ⚠️ USE PRODUCTION DATABASE
print("\n" + "="*80)
print("⚠️  WARNING: USING PRODUCTION DATABASE")
print(f"Database: {settings.DATABASE_URL}")
print("="*80)

# Use the REAL production database
engine = create_engine(settings.DATABASE_URL)
ProductionSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_PREFIX = "/api/v1"


def override_get_db():
    """Use production database"""
    try:
        db = ProductionSessionLocal()
        yield db
    finally:
        db.close()


# Override to use production DB
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create test client using production database"""
    yield TestClient(app)


@pytest.fixture
def db_session():
    """Provide production database session"""
    db = ProductionSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_production_e2e_flow(client, db_session):
    """
    Complete E2E test using production database
    Tests the EXACT same flow a real user would experience
    """
    print("\n" + "="*80)
    print("🚀 PRODUCTION E2E TEST")
    print("="*80)
    
    # Use a unique email for testing
    test_email = "e2e_test_user@example.com"
    
    # Clean up any existing test user
    existing_user = db_session.query(User).filter(User.email == test_email).first()
    if existing_user:
        print(f"\n🧹 Cleaning up existing test user: {existing_user.id}")
        # Delete related records
        db_session.query(Transaction).filter(Transaction.user_id == existing_user.id).delete()
        db_session.query(Goal).filter(Goal.user_id == existing_user.id).delete()
        db_session.query(DebtLoan).filter(DebtLoan.user_id == existing_user.id).delete()
        db_session.query(Budget).filter(Budget.user_id == existing_user.id).delete()
        db_session.delete(existing_user)
        db_session.commit()
    
    # Step 1: Register user
    print("\n📝 Step 1: Register user")
    response = client.post(f"{API_PREFIX}/auth/register", json={
        "email": test_email,
        "password": "Test123!",
        "name": "E2E Test User"
    })
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    data = response.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    print(f"✅ User registered: {user_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verify user exists in production DB
    user = db_session.query(User).filter(User.id == user_id).first()
    assert user is not None, "User not found in production database!"
    print(f"✅ User verified in production DB: {user.email}")
    
    # Step 2: Add income via chat
    print("\n💬 Step 2: Add monthly income")
    message = "My monthly salary is $7000"
    print(f"USER: {message}")
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    print(f"AGENT: {result['response'][:150]}...")
    print(f"Tools used: {result.get('tools_used', [])}")
    
    # Step 3: Add expenses
    print("\n💬 Step 3: Add expenses")
    expenses = [
        "I spent $1500 on rent",
        "I spent $400 on groceries",
        "I spent $200 on utilities"
    ]
    for expense in expenses:
        print(f"USER: {expense}")
        response = client.post(f"{API_PREFIX}/chat", json={"message": expense}, headers=headers)
        assert response.status_code == 200
        print(f"  ✅ Recorded")
    
    # Verify transactions in production DB
    transaction_count = db_session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE
    ).count()
    print(f"✅ Verified {transaction_count} transactions in production DB")
    assert transaction_count >= 3, f"Expected at least 3 transactions, found {transaction_count}"
    
    # Step 4: Add debt
    print("\n💬 Step 4: Add credit card debt")
    message = "I have a credit card debt of $8000 at 19% interest, paying $300/month"
    print(f"USER: {message}")
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    print(f"AGENT: {result['response'][:150]}...")
    
    # Verify debt in production DB
    debt = db_session.query(DebtLoan).filter(
        DebtLoan.user_id == user_id,
        DebtLoan.remaining_amount == 8000
    ).first()
    assert debt is not None, "Debt not found in production database!"
    print(f"✅ Verified debt in production DB: ${debt.remaining_amount} at {debt.interest_rate}%")
    
    # Step 5: Set goal
    print("\n💬 Step 5: Set savings goal")
    message = "I want to save $20,000 for a house down payment by December 2026"
    print(f"USER: {message}")
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    print(f"AGENT: {result['response'][:150]}...")
    
    # Verify goal in production DB
    goal = db_session.query(Goal).filter(
        Goal.user_id == user_id,
        Goal.target_amount == 20000
    ).first()
    assert goal is not None, "Goal not found in production database!"
    print(f"✅ Verified goal in production DB: ${goal.target_amount} by {goal.target_date}")
    
    # Step 6: Create budget
    print("\n💬 Step 6: Create budget")
    message = "Set a $600 monthly budget for food"
    print(f"USER: {message}")
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    print(f"AGENT: {result['response'][:150]}...")
    
    # Verify budget in production DB
    budget = db_session.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category == "food"
    ).first()
    assert budget is not None, "Budget not found in production database!"
    print(f"✅ Verified budget in production DB: ${budget.amount}/month for {budget.category}")
    
    # Step 7: Get financial health assessment
    print("\n💬 Step 7: Check financial health")
    message = "How am I doing financially?"
    print(f"USER: {message}")
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    print(f"\nAGENT RESPONSE:")
    print(result['response'])
    print(f"\nTools used: {result.get('tools_used', [])}")
    
    # Verify financial health tool was called
    assert 'calculate_financial_health' in str(result.get('tools_used', [])), \
        "Financial health tool was not called!"
    print("✅ Financial health calculation verified")
    
    # Step 8: Get debt payoff strategy
    print("\n💬 Step 8: Get debt payoff strategy")
    message = "I have $500 extra per month, how should I pay off my debt?"
    print(f"USER: {message}")
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    print(f"\nAGENT RESPONSE:")
    print(result['response'])
    print(f"\nTools used: {result.get('tools_used', [])}")
    
    # Verify debt optimization tool was called
    assert 'optimize_debt_repayment' in str(result.get('tools_used', [])), \
        "Debt optimization tool was not called!"
    print("✅ Debt optimization verified")
    
    # Final verification
    print("\n" + "="*80)
    print("📊 FINAL PRODUCTION DATABASE STATE")
    print("="*80)
    
    # Count all records for this user
    transactions = db_session.query(Transaction).filter(Transaction.user_id == user_id).count()
    goals = db_session.query(Goal).filter(Goal.user_id == user_id).count()
    debts = db_session.query(DebtLoan).filter(DebtLoan.user_id == user_id).count()
    budgets = db_session.query(Budget).filter(Budget.user_id == user_id).count()
    
    print(f"User ID: {user_id}")
    print(f"Transactions: {transactions}")
    print(f"Goals: {goals}")
    print(f"Debts: {debts}")
    print(f"Budgets: {budgets}")
    
    assert transactions >= 3, "Not enough transactions"
    assert goals >= 1, "No goals created"
    assert debts >= 1, "No debts created"
    assert budgets >= 1, "No budgets created"
    
    print("\n" + "="*80)
    print("✅ ALL PRODUCTION E2E TESTS PASSED!")
    print("="*80)
    print(f"\n⚠️  Test data remains in production database for user: {test_email}")
    print("To clean up, delete this user from the database or run the cleanup script")
    print("="*80)


if __name__ == "__main__":
    print("\n⚠️  WARNING: This test writes to PRODUCTION database!")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    input()
    pytest.main([__file__, "-v", "-s"])
