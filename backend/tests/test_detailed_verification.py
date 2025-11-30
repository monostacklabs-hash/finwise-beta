"""
Detailed E2E Test with Database Verification
Shows exactly what the agent is doing and verifies DB state
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from app.main import app
from app.database.models import Base, User, Transaction, Goal, DebtLoan, Budget, Account
from app.database.models import TransactionType, GoalStatus
from app.database.session import get_db
from app.api.auth import hash_password

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_detailed.db"
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
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def print_db_state(db, user_id, label=""):
    """Print current database state"""
    print(f"\n{'='*80}")
    print(f"📊 DATABASE STATE {label}")
    print(f"{'='*80}")
    
    # Transactions
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    print(f"\n💰 TRANSACTIONS ({len(transactions)}):")
    for t in transactions:
        print(f"  - {t.type.value}: ${t.amount} - {t.description} ({t.category})")
    
    # Accounts
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    print(f"\n🏦 ACCOUNTS ({len(accounts)}):")
    for a in accounts:
        print(f"  - {a.account_name}: ${a.current_balance} ({a.account_type})")
    
    # Goals
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    print(f"\n🎯 GOALS ({len(goals)}):")
    for g in goals:
        print(f"  - {g.name}: ${g.current_amount}/${g.target_amount} (target: {g.target_date})")
    
    # Debts
    debts = db.query(DebtLoan).filter(DebtLoan.user_id == user_id).all()
    print(f"\n💳 DEBTS ({len(debts)}):")
    for d in debts:
        print(f"  - {d.name}: ${d.remaining_amount} @ {d.interest_rate}% (payment: ${d.monthly_payment})")
    
    # Budgets
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    print(f"\n📊 BUDGETS ({len(budgets)}):")
    for b in budgets:
        print(f"  - {b.category}: ${b.amount}/month")
    
    print(f"{'='*80}\n")


def test_detailed_user_journey_with_verification(client, db_session):
    """
    Detailed test that shows:
    1. What message is sent
    2. What the agent responds
    3. What tools were used
    4. What was written to the database
    """
    print("\n" + "="*80)
    print("🚀 DETAILED E2E TEST WITH FULL VERIFICATION")
    print("="*80)
    
    # Register and login
    print("\n📝 Step 1: Register user")
    response = client.post(f"{API_PREFIX}/auth/register", json={
        "email": "detailed@test.com",
        "password": "Test123!",
        "name": "Detailed Tester"
    })
    assert response.status_code == 201
    data = response.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    print(f"✅ User registered: {user_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Add income
    print("\n" + "="*80)
    print("💬 Test 1: Add monthly salary")
    print("="*80)
    message = "My monthly salary is $5000"
    print(f"USER: {message}")
    
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"Success: {result['success']}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Response: {result['response'][:500]}...")
    
    print_db_state(db_session, user_id, "AFTER SALARY")
    
    # Test 2: Add expense
    print("\n" + "="*80)
    print("💬 Test 2: Add expense")
    print("="*80)
    message = "I spent $150 on groceries at Whole Foods"
    print(f"USER: {message}")
    
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"Success: {result['success']}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Response: {result['response'][:500]}...")
    
    print_db_state(db_session, user_id, "AFTER GROCERY EXPENSE")
    
    # Verify transaction was created
    transaction = db_session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.amount == 150,
        Transaction.type == TransactionType.EXPENSE
    ).first()
    assert transaction is not None, "❌ Transaction not found in database!"
    print("✅ VERIFIED: Transaction exists in database")
    
    # Test 3: Add debt
    print("\n" + "="*80)
    print("💬 Test 3: Add credit card debt")
    print("="*80)
    message = "I have a credit card debt of $5000 at 18% interest, paying $200 per month"
    print(f"USER: {message}")
    
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"Success: {result['success']}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Response: {result['response'][:500]}...")
    
    print_db_state(db_session, user_id, "AFTER DEBT")
    
    # Verify debt was created
    debt = db_session.query(DebtLoan).filter(
        DebtLoan.user_id == user_id,
        DebtLoan.remaining_amount == 5000
    ).first()
    assert debt is not None, "❌ Debt not found in database!"
    assert debt.interest_rate == 18
    print("✅ VERIFIED: Debt exists in database with correct interest rate")
    
    # Test 4: Set goal
    print("\n" + "="*80)
    print("💬 Test 4: Set savings goal")
    print("="*80)
    message = "I want to save $10,000 for a vacation by December 2025"
    print(f"USER: {message}")
    
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"Success: {result['success']}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Response: {result['response'][:500]}...")
    
    print_db_state(db_session, user_id, "AFTER GOAL")
    
    # Verify goal was created
    goal = db_session.query(Goal).filter(
        Goal.user_id == user_id,
        Goal.target_amount == 10000
    ).first()
    assert goal is not None, "❌ Goal not found in database!"
    print("✅ VERIFIED: Goal exists in database")
    
    # Test 5: Create budget
    print("\n" + "="*80)
    print("💬 Test 5: Create budget")
    print("="*80)
    message = "Set a $500 monthly budget for food"
    print(f"USER: {message}")
    
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"Success: {result['success']}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Response: {result['response'][:500]}...")
    
    print_db_state(db_session, user_id, "AFTER BUDGET")
    
    # Verify budget was created
    budget = db_session.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category == "food"
    ).first()
    assert budget is not None, "❌ Budget not found in database!"
    assert budget.amount == 500
    print("✅ VERIFIED: Budget exists in database")
    
    # Test 6: Check financial health (uses tools, doesn't write to DB)
    print("\n" + "="*80)
    print("💬 Test 6: Check financial health")
    print("="*80)
    message = "How am I doing financially?"
    print(f"USER: {message}")
    
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"Success: {result['success']}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Response: {result['response']}")
    
    # Verify calculate_financial_health tool was used
    assert "calculate_financial_health" in str(result.get('tools_used', [])), \
        "❌ calculate_financial_health tool was not used!"
    print("✅ VERIFIED: calculate_financial_health tool was called")
    
    # Test 7: Get debt optimization advice
    print("\n" + "="*80)
    print("💬 Test 7: Get debt payoff strategy")
    print("="*80)
    message = "I have $300 extra per month, how should I pay off my debt?"
    print(f"USER: {message}")
    
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"Success: {result['success']}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Response: {result['response']}")
    
    # Verify optimize_debt_repayment tool was used
    assert "optimize_debt_repayment" in str(result.get('tools_used', [])), \
        "❌ optimize_debt_repayment tool was not used!"
    print("✅ VERIFIED: optimize_debt_repayment tool was called")
    
    # Final verification
    print("\n" + "="*80)
    print("🎉 FINAL VERIFICATION")
    print("="*80)
    
    print_db_state(db_session, user_id, "FINAL STATE")
    
    # Count all records
    transaction_count = db_session.query(Transaction).filter(Transaction.user_id == user_id).count()
    account_count = db_session.query(Account).filter(Account.user_id == user_id).count()
    goal_count = db_session.query(Goal).filter(Goal.user_id == user_id).count()
    debt_count = db_session.query(DebtLoan).filter(DebtLoan.user_id == user_id).count()
    budget_count = db_session.query(Budget).filter(Budget.user_id == user_id).count()
    
    print(f"\n📈 SUMMARY:")
    print(f"  Transactions: {transaction_count} (expected >= 1)")
    print(f"  Accounts: {account_count}")
    print(f"  Goals: {goal_count} (expected >= 1)")
    print(f"  Debts: {debt_count} (expected >= 1)")
    print(f"  Budgets: {budget_count} (expected >= 1)")
    
    assert transaction_count >= 1, "No transactions created!"
    assert goal_count >= 1, "No goals created!"
    assert debt_count >= 1, "No debts created!"
    assert budget_count >= 1, "No budgets created!"
    
    print("\n" + "="*80)
    print("✅ ALL VERIFICATIONS PASSED!")
    print("="*80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
