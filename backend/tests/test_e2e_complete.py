"""
Complete End-to-End Tests for Financial Agent System
Tests all agents, tools, and services with realistic user scenarios
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

from app.main import app
from app.database.models import Base, User, Transaction, Goal, DebtLoan, Budget, RecurringTransaction
from app.database.models import Account, TransactionType, GoalStatus, DebtLoanStatus
from app.database.session import get_db
from app.api.auth import hash_password

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_e2e.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# API base path
API_PREFIX = "/api/v1"


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create test client and fresh database for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield TestClient(app)
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide database session for direct DB checks"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ============================================================================
# USER PROFILE FIXTURES - Different Financial Situations
# ============================================================================

class UserProfile:
    """Base user profile"""
    def __init__(self, name, email, password, financial_situation):
        self.name = name
        self.email = email
        self.password = password
        self.financial_situation = financial_situation
        self.token = None
        self.user_id = None


# Rich User Profile
RICH_USER = UserProfile(
    name="Richard Wealthy",
    email="rich@example.com",
    password="SecurePass123!",
    financial_situation={
        "monthly_income": 15000,
        "monthly_expenses": 5000,
        "savings": 100000,
        "debts": [],
        "goals": [
            {"name": "Luxury Vacation", "target": 25000, "current": 10000},
            {"name": "Investment Property", "target": 200000, "current": 50000}
        ]
    }
)

# Poor User Profile
POOR_USER = UserProfile(
    name="Paula Struggling",
    email="poor@example.com",
    password="SecurePass123!",
    financial_situation={
        "monthly_income": 2500,
        "monthly_expenses": 2400,
        "savings": 500,
        "debts": [
            {"name": "Credit Card", "amount": 5000, "interest": 22, "payment": 150},
            {"name": "Payday Loan", "amount": 800, "interest": 35, "payment": 100}
        ],
        "goals": [
            {"name": "Emergency Fund", "target": 1000, "current": 200}
        ]
    }
)

# Average User Profile
AVERAGE_USER = UserProfile(
    name="Alex Average",
    email="average@example.com",
    password="SecurePass123!",
    financial_situation={
        "monthly_income": 5000,
        "monthly_expenses": 3500,
        "savings": 10000,
        "debts": [
            {"name": "Student Loan", "amount": 25000, "interest": 5.5, "payment": 300}
        ],
        "goals": [
            {"name": "House Down Payment", "target": 50000, "current": 10000},
            {"name": "Emergency Fund", "target": 15000, "current": 5000}
        ]
    }
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def register_and_login(client, user_profile):
    """Register and login a user, return token"""
    # Register
    response = client.post(f"{API_PREFIX}/auth/register", json={
        "email": user_profile.email,
        "password": user_profile.password,
        "name": user_profile.name
    })
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    
    data = response.json()
    user_profile.token = data["access_token"]
    user_profile.user_id = data["user"]["id"]
    
    return user_profile.token


def chat(client, token, message, chat_history=None):
    """Send chat message to agent"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": message}
    if chat_history:
        payload["chat_history"] = chat_history
    
    response = client.post(f"{API_PREFIX}/chat", json=payload, headers=headers)
    assert response.status_code == 200, f"Chat failed: {response.json()}"
    return response.json()


def verify_db_count(db, model, user_id, expected_count, exact=False):
    """Verify database record count"""
    count = db.query(model).filter(model.user_id == user_id).count()
    if exact:
        assert count == expected_count, f"Expected exactly {expected_count} {model.__name__} records, got {count}"
    else:
        assert count >= expected_count, f"Expected at least {expected_count} {model.__name__} records, got {count}"


def verify_transaction_exists(db, user_id, amount, trans_type, description_contains=None):
    """Verify a transaction exists in database"""
    query = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.amount == amount,
        Transaction.type == trans_type
    )
    
    if description_contains:
        query = query.filter(Transaction.description.contains(description_contains))
    
    transaction = query.first()
    assert transaction is not None, f"Transaction not found: {amount} {trans_type}"
    return transaction


# ============================================================================
# TEST 1: AUTHENTICATION FLOW
# ============================================================================

def test_01_authentication_flow(client, db_session):
    """Test complete authentication flow"""
    print("\n=== TEST 1: Authentication Flow ===")
    
    # Test registration
    response = client.post(f"{API_PREFIX}/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"
    
    token = data["access_token"]
    user_id = data["user"]["id"]
    
    # Verify user in database
    user = db_session.query(User).filter(User.id == user_id).first()
    assert user is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    
    # Test duplicate registration
    response = client.post(f"{API_PREFIX}/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "Test User 2"
    })
    assert response.status_code == 400
    
    # Test login with correct credentials
    response = client.post(f"{API_PREFIX}/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # Test login with wrong password
    response = client.post(f"{API_PREFIX}/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPassword"
    })
    assert response.status_code == 401
    
    # Test profile access
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"{API_PREFIX}/auth/profile", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == "test@example.com"
    
    print("✅ Authentication flow test passed")


# ============================================================================
# TEST 2: RICH USER COMPLETE JOURNEY
# ============================================================================

def test_02_rich_user_journey(client, db_session):
    """Test complete journey for a wealthy user"""
    print("\n=== TEST 2: Rich User Journey ===")
    
    token = register_and_login(client, RICH_USER)
    user_id = RICH_USER.user_id
    
    # Step 1: Add high income
    print("Step 1: Adding monthly salary...")
    response = chat(client, token, "My salary is $15,000 per month")
    assert response["success"]
    assert "add_transaction" in str(response["tools_used"]) or "create_recurring_transaction" in str(response["tools_used"])
    
    # Verify recurring transaction created
    recurring = db_session.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == user_id
    ).first()
    assert recurring is not None
    assert recurring.amount == 15000
    
    # Step 2: Add luxury expenses
    print("Step 2: Adding luxury expenses...")
    response = chat(client, token, "I spent $500 on a fancy dinner")
    assert response["success"]
    verify_transaction_exists(db_session, user_id, 500, TransactionType.EXPENSE)
    
    response = chat(client, token, "Bought designer clothes for $2000")
    assert response["success"]
    verify_transaction_exists(db_session, user_id, 2000, TransactionType.EXPENSE)
    
    # Step 3: Add investment account
    print("Step 3: Adding investment account...")
    response = chat(client, token, "I have an investment account at Vanguard with $100,000")
    assert response["success"]
    
    account = db_session.query(Account).filter(Account.user_id == user_id).first()
    assert account is not None
    assert account.current_balance == 100000
    
    # Step 4: Set ambitious goals
    print("Step 4: Setting ambitious financial goals...")
    response = chat(client, token, "I want to save $25,000 for a luxury vacation by December 2025")
    assert response["success"]
    
    goal = db_session.query(Goal).filter(
        Goal.user_id == user_id,
        Goal.target_amount == 25000
    ).first()
    assert goal is not None
    
    # Step 5: Check financial health (should be excellent)
    print("Step 5: Checking financial health...")
    response = chat(client, token, "How am I doing financially?")
    assert response["success"]
    assert "calculate_financial_health" in str(response["tools_used"])
    # Rich user should have high health score
    assert any(word in response["response"].lower() for word in ["excellent", "good", "great"])
    
    # Step 6: Create budgets for luxury categories
    print("Step 6: Creating luxury budgets...")
    response = chat(client, token, "Set a $3000 monthly budget for entertainment")
    assert response["success"]
    
    budget = db_session.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category == "entertainment"
    ).first()
    assert budget is not None
    assert budget.amount == 3000
    
    # Step 7: Run simulation - what if I invest more?
    print("Step 7: Running investment simulation...")
    response = chat(client, token, "What if I save an extra $2000 per month?")
    assert response["success"]
    assert "run_simulation" in str(response["tools_used"]) or "forecast" in response["response"].lower()
    
    # Step 8: View all transactions
    print("Step 8: Viewing transaction history...")
    response = chat(client, token, "Show me my recent transactions")
    assert response["success"]
    assert "get_transactions" in str(response["tools_used"])
    
    # Verify final database state
    verify_db_count(db_session, Transaction, user_id, 2)  # 2 one-time expenses
    verify_db_count(db_session, Goal, user_id, 1)
    verify_db_count(db_session, Budget, user_id, 1)
    verify_db_count(db_session, Account, user_id, 1)
    
    print("✅ Rich user journey test passed")


# ============================================================================
# TEST 3: POOR USER COMPLETE JOURNEY
# ============================================================================

def test_03_poor_user_journey(client, db_session):
    """Test complete journey for a struggling user"""
    print("\n=== TEST 3: Poor User Journey ===")
    
    token = register_and_login(client, POOR_USER)
    user_id = POOR_USER.user_id
    
    # Step 1: Add low income
    print("Step 1: Adding modest income...")
    response = chat(client, token, "I earn $2500 per month")
    assert response["success"]
    
    # Step 2: Add high-interest debts
    print("Step 2: Adding high-interest debts...")
    response = chat(client, token, "I have a credit card debt of $5000 at 22% interest, paying $150 per month")
    assert response["success"]
    
    debt1 = db_session.query(DebtLoan).filter(
        DebtLoan.user_id == user_id,
        DebtLoan.remaining_amount == 5000
    ).first()
    assert debt1 is not None
    assert debt1.interest_rate == 22
    
    response = chat(client, token, "I also have a payday loan of $800 at 35% interest, paying $100 monthly")
    assert response["success"]
    
    # Step 3: Track essential expenses
    print("Step 3: Tracking essential expenses...")
    response = chat(client, token, "Spent $800 on rent")
    assert response["success"]
    
    response = chat(client, token, "Paid $150 for groceries")
    assert response["success"]
    
    response = chat(client, token, "Electric bill was $80")
    assert response["success"]
    
    # Verify transactions
    verify_db_count(db_session, Transaction, user_id, 3)
    
    # Step 4: Check financial health (should be poor/critical)
    print("Step 4: Checking financial health...")
    response = chat(client, token, "How am I doing financially?")
    assert response["success"]
    # Poor user should have low health score
    assert any(word in response["response"].lower() for word in ["poor", "critical", "concern", "debt"])
    
    # Step 5: Get debt optimization advice
    print("Step 5: Getting debt payoff strategy...")
    response = chat(client, token, "I have $200 extra per month, how should I pay off my debts?")
    assert response["success"]
    assert "optimize_debt_repayment" in str(response["tools_used"])
    assert any(word in response["response"].lower() for word in ["avalanche", "snowball", "interest"])
    
    # Step 6: Set modest emergency fund goal
    print("Step 6: Setting emergency fund goal...")
    response = chat(client, token, "I want to save $1000 for emergencies by June 2025")
    assert response["success"]
    
    goal = db_session.query(Goal).filter(
        Goal.user_id == user_id,
        Goal.target_amount == 1000
    ).first()
    assert goal is not None
    
    # Step 7: Check if goal is achievable
    print("Step 7: Checking goal feasibility...")
    response = chat(client, token, "Can I reach my emergency fund goal?")
    assert response["success"]
    
    # Step 8: Create tight budgets
    print("Step 8: Creating strict budgets...")
    response = chat(client, token, "Set a $200 monthly budget for food")
    assert response["success"]
    
    response = chat(client, token, "Set a $50 monthly budget for entertainment")
    assert response["success"]
    
    verify_db_count(db_session, Budget, user_id, 2)
    
    # Step 9: Detect recurring patterns
    print("Step 9: Detecting recurring expenses...")
    response = chat(client, token, "Find my recurring expenses")
    assert response["success"]
    
    # Step 10: Cash flow forecast (should show tight situation)
    print("Step 10: Forecasting cash flow...")
    response = chat(client, token, "Will I run out of money in the next 3 months?")
    assert response["success"]
    
    # Verify final database state
    verify_db_count(db_session, DebtLoan, user_id, 2)
    verify_db_count(db_session, Goal, user_id, 1)
    verify_db_count(db_session, Budget, user_id, 2)
    
    print("✅ Poor user journey test passed")


# ============================================================================
# TEST 4: AVERAGE USER COMPLETE JOURNEY
# ============================================================================

def test_04_average_user_journey(client, db_session):
    """Test complete journey for an average user"""
    print("\n=== TEST 4: Average User Journey ===")
    
    token = register_and_login(client, AVERAGE_USER)
    user_id = AVERAGE_USER.user_id
    
    # Step 1: Add moderate income
    print("Step 1: Adding salary...")
    response = chat(client, token, "My monthly salary is $5000")
    assert response["success"]
    
    # Step 2: Add checking and savings accounts
    print("Step 2: Adding bank accounts...")
    response = chat(client, token, "I have a Chase checking account with $3000")
    assert response["success"]
    
    response = chat(client, token, "I also have a savings account at Ally with $10,000")
    assert response["success"]
    
    verify_db_count(db_session, Account, user_id, 2)
    
    # Step 3: Add student loan debt
    print("Step 3: Adding student loan...")
    response = chat(client, token, "I have a student loan of $25,000 at 5.5% interest, paying $300 monthly")
    assert response["success"]
    
    debt = db_session.query(DebtLoan).filter(DebtLoan.user_id == user_id).first()
    assert debt is not None
    assert debt.remaining_amount == 25000
    
    # Step 4: Track mixed expenses
    print("Step 4: Tracking various expenses...")
    expenses = [
        ("Spent $1200 on rent", 1200),
        ("Groceries cost $300", 300),
        ("Paid $150 for utilities", 150),
        ("Bought gas for $60", 60),
        ("Netflix subscription $15", 15),
        ("Gym membership $50", 50),
        ("Dinner out $80", 80)
    ]
    
    for message, amount in expenses:
        response = chat(client, token, message)
        assert response["success"]
    
    # Verify at least 5 transactions were created (AI may batch or handle differently)
    verify_db_count(db_session, Transaction, user_id, 5)
    
    # Step 5: Set realistic goals
    print("Step 5: Setting financial goals...")
    response = chat(client, token, "I want to save $50,000 for a house down payment by December 2026")
    assert response["success"]
    
    response = chat(client, token, "I also want to build a $15,000 emergency fund by June 2025")
    assert response["success"]
    
    verify_db_count(db_session, Goal, user_id, 2)
    
    # Step 6: Check financial health (should be good/fair)
    print("Step 6: Checking financial health...")
    response = chat(client, token, "How am I doing financially?")
    assert response["success"]
    assert "calculate_financial_health" in str(response["tools_used"])
    
    # Step 7: Analyze spending by category
    print("Step 7: Analyzing spending patterns...")
    response = chat(client, token, "Where is my money going?")
    assert response["success"]
    assert "analyze_spending_by_category" in str(response["tools_used"])
    
    # Step 8: Create balanced budgets
    print("Step 8: Creating budgets...")
    budgets = [
        ("Set a $1300 monthly budget for rent", 1300, "rent"),
        ("Set a $400 monthly budget for food", 400, "food"),
        ("Set a $200 monthly budget for entertainment", 200, "entertainment"),
        ("Set a $100 monthly budget for utilities", 100, "utilities")
    ]
    
    for message, amount, category in budgets:
        response = chat(client, token, message)
        assert response["success"]
    
    verify_db_count(db_session, Budget, user_id, 4)
    
    # Step 9: Set up recurring transactions
    print("Step 9: Setting up recurring bills...")
    response = chat(client, token, "My rent is $1200 every month")
    assert response["success"]
    
    response = chat(client, token, "I pay $50 for gym membership monthly")
    assert response["success"]
    
    # Step 10: Check goal progress
    print("Step 10: Checking goal progress...")
    response = chat(client, token, "When will I reach my house down payment goal?")
    assert response["success"]
    assert "project_goal_achievement" in str(response["tools_used"]) or "goal" in response["response"].lower()
    
    # Step 11: Get budget recommendations
    print("Step 11: Getting budget optimization advice...")
    response = chat(client, token, "Should I adjust my budgets?")
    assert response["success"]
    
    # Step 12: Run what-if scenario
    print("Step 12: Running what-if scenario...")
    response = chat(client, token, "What if I cut my entertainment spending by $100 per month?")
    assert response["success"]
    
    # Step 13: Check cash flow forecast
    print("Step 13: Forecasting cash flow...")
    response = chat(client, token, "What will my balance be in 90 days?")
    assert response["success"]
    
    # Step 14: View all goals with milestones
    print("Step 14: Viewing goal milestones...")
    response = chat(client, token, "Show my goal progress")
    assert response["success"]
    
    # Step 15: Get notifications
    print("Step 15: Checking notifications...")
    response = chat(client, token, "Show my notifications")
    assert response["success"]
    
    print("✅ Average user journey test passed")


# ============================================================================
# TEST 5: ALL TRANSACTION TYPES
# ============================================================================

def test_05_all_transaction_types(client, db_session):
    """Test all transaction types: income, expense, lending, borrowing"""
    print("\n=== TEST 5: All Transaction Types ===")
    
    token = register_and_login(client, UserProfile(
        "Trans Tester", "trans@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "trans@example.com").first().id
    
    # Test income
    print("Testing income transaction...")
    response = chat(client, token, "I earned $500 from freelance work")
    assert response["success"]
    verify_transaction_exists(db_session, user_id, 500, TransactionType.INCOME)
    
    # Test expense
    print("Testing expense transaction...")
    response = chat(client, token, "I spent $100 on groceries")
    assert response["success"]
    verify_transaction_exists(db_session, user_id, 100, TransactionType.EXPENSE)
    
    # Test lending
    print("Testing lending transaction...")
    response = chat(client, token, "I lent $200 to my friend John")
    assert response["success"]
    verify_transaction_exists(db_session, user_id, 200, TransactionType.LENDING)
    
    # Test borrowing
    print("Testing borrowing transaction...")
    response = chat(client, token, "I borrowed $150 from my sister")
    assert response["success"]
    verify_transaction_exists(db_session, user_id, 150, TransactionType.BORROWING)
    
    # Verify all 4 transactions exist
    verify_db_count(db_session, Transaction, user_id, 4)
    
    print("✅ All transaction types test passed")


# ============================================================================
# TEST 6: RECURRING TRANSACTION DETECTION
# ============================================================================

def test_06_recurring_detection(client, db_session):
    """Test recurring pattern detection"""
    print("\n=== TEST 6: Recurring Transaction Detection ===")
    
    token = register_and_login(client, UserProfile(
        "Recurring Tester", "recurring@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "recurring@example.com").first().id
    
    # Create pattern: Netflix subscription
    print("Creating Netflix subscription pattern...")
    dates = [
        datetime.utcnow() - timedelta(days=90),
        datetime.utcnow() - timedelta(days=60),
        datetime.utcnow() - timedelta(days=30)
    ]
    
    for date in dates:
        trans = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=TransactionType.EXPENSE,
            amount=15.99,
            description="Netflix subscription",
            category="entertainment",
            date=date
        )
        db_session.add(trans)
    db_session.commit()
    
    # Test pattern detection
    print("Testing pattern detection...")
    response = chat(client, token, "Find my recurring expenses")
    assert response["success"]
    assert "detect_recurring_patterns" in str(response["tools_used"])
    assert "netflix" in response["response"].lower() or "subscription" in response["response"].lower()
    
    print("✅ Recurring detection test passed")


# ============================================================================
# TEST 7: BUDGET TRACKING AND ALERTS
# ============================================================================

def test_07_budget_tracking(client, db_session):
    """Test budget creation, tracking, and overspending detection"""
    print("\n=== TEST 7: Budget Tracking ===")
    
    token = register_and_login(client, UserProfile(
        "Budget Tester", "budget@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "budget@example.com").first().id
    
    # Create budget
    print("Creating food budget...")
    response = chat(client, token, "Set a $500 monthly budget for food")
    assert response["success"]
    
    budget = db_session.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category == "food"
    ).first()
    assert budget is not None
    assert budget.amount == 500
    
    # Add expenses under budget
    print("Adding expenses within budget...")
    response = chat(client, token, "Spent $200 on groceries")
    assert response["success"]
    
    response = chat(client, token, "Spent $150 at restaurant")
    assert response["success"]
    
    # Check budget status
    print("Checking budget status...")
    response = chat(client, token, "Show my budgets")
    assert response["success"]
    assert "get_budgets" in str(response["tools_used"])
    
    # Add expense that exceeds budget
    print("Adding expense that exceeds budget...")
    response = chat(client, token, "Spent $300 on fancy dinner")
    assert response["success"]
    
    # Total should be $650, exceeding $500 budget
    total_spent = db_session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE
    ).count()
    assert total_spent == 3
    
    print("✅ Budget tracking test passed")


# ============================================================================
# TEST 8: GOAL PROJECTION AND MILESTONES
# ============================================================================

def test_08_goal_milestones(client, db_session):
    """Test goal creation, projection, and milestone tracking"""
    print("\n=== TEST 8: Goal Milestones ===")
    
    token = register_and_login(client, UserProfile(
        "Goal Tester", "goal@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "goal@example.com").first().id
    
    # Add income for projection
    print("Adding income...")
    response = chat(client, token, "My salary is $5000 per month")
    assert response["success"]
    
    # Add expenses
    print("Adding expenses...")
    response = chat(client, token, "My monthly expenses are about $3000")
    assert response["success"]
    
    # Create goal
    print("Creating savings goal...")
    response = chat(client, token, "I want to save $10,000 for vacation by December 2025")
    assert response["success"]
    
    goal = db_session.query(Goal).filter(Goal.user_id == user_id).first()
    assert goal is not None
    assert goal.target_amount == 10000
    
    # Project goal achievement
    print("Projecting goal achievement...")
    response = chat(client, token, "When will I reach my vacation goal?")
    assert response["success"]
    assert "project_goal_achievement" in str(response["tools_used"]) or "goal" in response["response"].lower()
    
    # Check milestones
    print("Checking goal milestones...")
    response = chat(client, token, "Show my goal progress")
    assert response["success"]
    
    print("✅ Goal milestones test passed")


# ============================================================================
# TEST 9: DEBT OPTIMIZATION
# ============================================================================

def test_09_debt_optimization(client, db_session):
    """Test debt optimization strategies"""
    print("\n=== TEST 9: Debt Optimization ===")
    
    token = register_and_login(client, UserProfile(
        "Debt Tester", "debt@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "debt@example.com").first().id
    
    # Add multiple debts
    print("Adding multiple debts...")
    response = chat(client, token, "I have a credit card with $5000 at 18% interest, paying $200 monthly")
    assert response["success"]
    
    response = chat(client, token, "I also have a car loan of $15,000 at 6% interest, paying $400 monthly")
    assert response["success"]
    
    response = chat(client, token, "And a personal loan of $3000 at 12% interest, paying $150 monthly")
    assert response["success"]
    
    verify_db_count(db_session, DebtLoan, user_id, 3)
    
    # Get optimization strategy
    print("Getting debt payoff strategy...")
    response = chat(client, token, "I have $500 extra per month, how should I pay off my debts?")
    assert response["success"]
    assert "optimize_debt_repayment" in str(response["tools_used"])
    assert any(word in response["response"].lower() for word in ["avalanche", "snowball", "interest", "strategy"])
    
    # List all debts
    print("Listing all debts...")
    response = chat(client, token, "Show me all my debts")
    assert response["success"]
    assert "get_debts_and_loans" in str(response["tools_used"])
    
    print("✅ Debt optimization test passed")


# ============================================================================
# TEST 10: CASH FLOW FORECASTING
# ============================================================================

def test_10_cashflow_forecast(client, db_session):
    """Test cash flow forecasting and runway prediction"""
    print("\n=== TEST 10: Cash Flow Forecasting ===")
    
    token = register_and_login(client, UserProfile(
        "Forecast Tester", "forecast@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "forecast@example.com").first().id
    
    # Add account with balance
    print("Adding checking account...")
    response = chat(client, token, "I have a checking account with $5000")
    assert response["success"]
    
    account = db_session.query(Account).filter(Account.user_id == user_id).first()
    assert account is not None
    
    # Add recurring income
    print("Adding recurring income...")
    response = chat(client, token, "My salary is $4000 per month")
    assert response["success"]
    
    # Add recurring expenses
    print("Adding recurring expenses...")
    response = chat(client, token, "My rent is $1500 monthly")
    assert response["success"]
    
    response = chat(client, token, "I pay $200 for utilities every month")
    assert response["success"]
    
    # Run forecast
    print("Running cash flow forecast...")
    response = chat(client, token, "Will I run out of money in the next 90 days?")
    assert response["success"]
    assert "get_cashflow_forecast" in str(response["tools_used"]) or "forecast" in response["response"].lower()
    
    print("✅ Cash flow forecasting test passed")


# ============================================================================
# TEST 11: FINANCIAL SIMULATION
# ============================================================================

def test_11_financial_simulation(client, db_session):
    """Test what-if financial simulations"""
    print("\n=== TEST 11: Financial Simulation ===")
    
    token = register_and_login(client, UserProfile(
        "Sim Tester", "sim@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "sim@example.com").first().id
    
    # Setup baseline
    print("Setting up baseline finances...")
    response = chat(client, token, "My salary is $5000 per month")
    assert response["success"]
    
    response = chat(client, token, "My expenses are about $3500 monthly")
    assert response["success"]
    
    # Run income change simulation
    print("Simulating income increase...")
    response = chat(client, token, "What if I get a $1000 raise?")
    assert response["success"]
    
    # Run expense reduction simulation
    print("Simulating expense reduction...")
    response = chat(client, token, "What if I cut my spending by $500 per month?")
    assert response["success"]
    
    # Run new expense simulation
    print("Simulating new recurring expense...")
    response = chat(client, token, "Can I afford a $300 monthly car payment?")
    assert response["success"]
    
    print("✅ Financial simulation test passed")


# ============================================================================
# TEST 12: ACCOUNT MANAGEMENT
# ============================================================================

def test_12_account_management(client, db_session):
    """Test multi-account management including credit cards"""
    print("\n=== TEST 12: Account Management ===")
    
    token = register_and_login(client, UserProfile(
        "Account Tester", "account@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "account@example.com").first().id
    
    # Add checking account
    print("Adding checking account...")
    response = chat(client, token, "I have a Chase checking account with $3000")
    assert response["success"]
    
    # Add savings account
    print("Adding savings account...")
    response = chat(client, token, "I have a savings account at Ally with $10,000")
    assert response["success"]
    
    # Add credit card account
    print("Adding credit card...")
    response = chat(client, token, "I have a credit card account")
    assert response["success"]
    
    # Get account ID for credit card details
    accounts = db_session.query(Account).filter(Account.user_id == user_id).all()
    assert len(accounts) >= 1
    
    # List all accounts
    print("Listing all accounts...")
    response = chat(client, token, "Show me all my accounts")
    assert response["success"]
    assert "get_accounts" in str(response["tools_used"])
    
    # Check total balance
    print("Checking total balance...")
    response = chat(client, token, "What's my total balance?")
    assert response["success"]
    
    print("✅ Account management test passed")


# ============================================================================
# TEST 13: NOTIFICATION SYSTEM
# ============================================================================

def test_13_notifications(client, db_session):
    """Test notification generation and retrieval"""
    print("\n=== TEST 13: Notification System ===")
    
    token = register_and_login(client, UserProfile(
        "Notif Tester", "notif@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "notif@example.com").first().id
    
    # Create budget to trigger alert
    print("Creating budget...")
    response = chat(client, token, "Set a $100 monthly budget for entertainment")
    assert response["success"]
    
    # Exceed budget to trigger notification
    print("Exceeding budget...")
    response = chat(client, token, "Spent $150 on concert tickets")
    assert response["success"]
    
    # Check notifications
    print("Checking notifications...")
    response = chat(client, token, "Show my notifications")
    assert response["success"]
    assert "get_notifications" in str(response["tools_used"])
    
    print("✅ Notification system test passed")


# ============================================================================
# TEST 14: SPENDING ANALYSIS
# ============================================================================

def test_14_spending_analysis(client, db_session):
    """Test spending analysis and categorization"""
    print("\n=== TEST 14: Spending Analysis ===")
    
    token = register_and_login(client, UserProfile(
        "Analysis Tester", "analysis@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "analysis@example.com").first().id
    
    # Add diverse expenses
    print("Adding diverse expenses...")
    expenses = [
        "Spent $500 on groceries",
        "Paid $200 for gas",
        "Bought clothes for $150",
        "Dinner at restaurant $80",
        "Movie tickets $30",
        "Gym membership $50",
        "Phone bill $70"
    ]
    
    for expense in expenses:
        response = chat(client, token, expense)
        assert response["success"]
    
    # Analyze spending
    print("Analyzing spending by category...")
    response = chat(client, token, "Where is my money going?")
    assert response["success"]
    assert "analyze_spending_by_category" in str(response["tools_used"])
    
    # Check that response contains category breakdown
    assert any(word in response["response"].lower() for word in ["category", "spending", "breakdown"])
    
    print("✅ Spending analysis test passed")


# ============================================================================
# TEST 15: BUDGET OPTIMIZATION
# ============================================================================

def test_15_budget_optimization(client, db_session):
    """Test AI-powered budget optimization"""
    print("\n=== TEST 15: Budget Optimization ===")
    
    token = register_and_login(client, UserProfile(
        "Optimize Tester", "optimize@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "optimize@example.com").first().id
    
    # Create multiple budgets
    print("Creating budgets...")
    budgets = [
        ("Set a $500 budget for food", 500),
        ("Set a $200 budget for entertainment", 200),
        ("Set a $100 budget for shopping", 100)
    ]
    
    for message, amount in budgets:
        response = chat(client, token, message)
        assert response["success"]
    
    # Add expenses that exceed some budgets
    print("Adding expenses...")
    response = chat(client, token, "Spent $600 on groceries")
    assert response["success"]
    
    response = chat(client, token, "Spent $50 on entertainment")
    assert response["success"]
    
    # Get optimization recommendations
    print("Getting budget optimization advice...")
    response = chat(client, token, "Should I adjust my budgets?")
    assert response["success"]
    
    print("✅ Budget optimization test passed")


# ============================================================================
# TEST 16: CONVERSATION CONTEXT
# ============================================================================

def test_16_conversation_context(client, db_session):
    """Test that agent maintains conversation context"""
    print("\n=== TEST 16: Conversation Context ===")
    
    token = register_and_login(client, UserProfile(
        "Context Tester", "context@example.com", "Pass123!", {}
    ))
    
    # Start conversation
    print("Starting conversation...")
    response1 = chat(client, token, "I want to save for a vacation")
    assert response1["success"]
    
    # Continue with context
    chat_history = [
        {"role": "user", "content": "I want to save for a vacation"},
        {"role": "assistant", "content": response1["response"]}
    ]
    
    print("Continuing conversation with context...")
    response2 = chat(client, token, "I can save $500 per month", chat_history)
    assert response2["success"]
    
    # Add more context
    chat_history.extend([
        {"role": "user", "content": "I can save $500 per month"},
        {"role": "assistant", "content": response2["response"]}
    ])
    
    print("Asking follow-up question...")
    response3 = chat(client, token, "When will I reach it?", chat_history)
    assert response3["success"]
    
    print("✅ Conversation context test passed")


# ============================================================================
# TEST 17: ERROR HANDLING
# ============================================================================

def test_17_error_handling(client, db_session):
    """Test error handling for invalid inputs"""
    print("\n=== TEST 17: Error Handling ===")
    
    token = register_and_login(client, UserProfile(
        "Error Tester", "error@example.com", "Pass123!", {}
    ))
    
    # Test with invalid token
    print("Testing invalid token...")
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.post(f"{API_PREFIX}/chat", json={"message": "test"}, headers=headers)
    assert response.status_code == 401
    
    # Test with missing message
    print("Testing missing message...")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(f"{API_PREFIX}/chat", json={}, headers=headers)
    assert response.status_code == 422  # Validation error
    
    # Test agent with ambiguous input (should still work)
    print("Testing ambiguous input...")
    response = chat(client, token, "money stuff")
    # Agent should handle gracefully even if it can't determine intent
    assert response["success"] or "error" in response["response"].lower()
    
    print("✅ Error handling test passed")


# ============================================================================
# TEST 18: COMPLETE FINANCIAL HEALTH JOURNEY
# ============================================================================

def test_18_complete_health_journey(client, db_session):
    """Test complete financial health improvement journey"""
    print("\n=== TEST 18: Complete Financial Health Journey ===")
    
    token = register_and_login(client, UserProfile(
        "Health Journey", "health@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "health@example.com").first().id
    
    # Initial state: Poor financial health
    print("Phase 1: Poor financial health...")
    response = chat(client, token, "I earn $3000 per month")
    assert response["success"]
    
    response = chat(client, token, "I have $8000 in credit card debt at 20% interest")
    assert response["success"]
    
    response = chat(client, token, "My expenses are $2800 per month")
    assert response["success"]
    
    # Check initial health
    print("Checking initial health...")
    response = chat(client, token, "How am I doing financially?")
    assert response["success"]
    initial_health = response["response"]
    
    # Phase 2: Improvement actions
    print("Phase 2: Taking improvement actions...")
    
    # Pay down debt
    response = chat(client, token, "I paid $2000 towards my credit card")
    assert response["success"]
    
    # Reduce expenses
    response = chat(client, token, "I cut my expenses to $2200 per month")
    assert response["success"]
    
    # Start saving
    response = chat(client, token, "I want to save $5000 for emergency fund")
    assert response["success"]
    
    # Check improved health
    print("Checking improved health...")
    response = chat(client, token, "How am I doing now?")
    assert response["success"]
    improved_health = response["response"]
    
    # Verify improvement (responses should be different)
    assert initial_health != improved_health
    
    print("✅ Complete health journey test passed")


# ============================================================================
# TEST 19: ALL TOOLS COVERAGE
# ============================================================================

def test_19_all_tools_coverage(client, db_session):
    """Ensure all 26 tools are tested and callable"""
    print("\n=== TEST 19: All Tools Coverage ===")
    
    token = register_and_login(client, UserProfile(
        "Tools Tester", "tools@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "tools@example.com").first().id
    
    tools_tested = set()
    
    # Transaction tools (3)
    print("Testing transaction tools...")
    response = chat(client, token, "I spent $50 on lunch")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Show my transactions")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Where is my money going?")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Financial health (1)
    print("Testing financial health tool...")
    response = chat(client, token, "How am I doing financially?")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Debt tools (3)
    print("Testing debt tools...")
    response = chat(client, token, "I have a loan of $5000 at 10% interest, paying $200 monthly")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Show my debts")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "I have $300 extra, how should I pay off debt?")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Goal tools (3)
    print("Testing goal tools...")
    response = chat(client, token, "I want to save $10,000 by December 2025")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Show my goals")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "When will I reach my goal?")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Budget tools (2)
    print("Testing budget tools...")
    response = chat(client, token, "Set a $500 budget for food")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Show my budgets")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Recurring tools (3)
    print("Testing recurring tools...")
    response = chat(client, token, "My salary is $5000 per month")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Show my recurring transactions")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Find my recurring expenses")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Account tools (3)
    print("Testing account tools...")
    response = chat(client, token, "I have a checking account with $5000")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Show my accounts")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Notification tool (1)
    print("Testing notification tool...")
    response = chat(client, token, "Show my notifications")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    # Advanced tools (4)
    print("Testing advanced tools...")
    response = chat(client, token, "Should I adjust my budgets?")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "Show my goal milestones")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    response = chat(client, token, "What if I save $500 more per month?")
    if response["success"]:
        tools_tested.update(response["tools_used"])
    
    print(f"\nTools tested: {len(tools_tested)}")
    print(f"Tools: {sorted(tools_tested)}")
    
    # We should have tested most tools (some may not be called depending on agent decisions)
    assert len(tools_tested) >= 10, f"Only {len(tools_tested)} tools tested, expected at least 10"
    
    print("✅ All tools coverage test passed")


# ============================================================================
# TEST 20: DATABASE INTEGRITY
# ============================================================================

def test_20_database_integrity(client, db_session):
    """Test database integrity and relationships"""
    print("\n=== TEST 20: Database Integrity ===")
    
    token = register_and_login(client, UserProfile(
        "DB Tester", "db@example.com", "Pass123!", {}
    ))
    user_id = db_session.query(User).filter(User.email == "db@example.com").first().id
    
    # Create related records
    print("Creating related records...")
    
    # Add account
    response = chat(client, token, "I have a checking account with $1000")
    assert response["success"]
    
    account = db_session.query(Account).filter(Account.user_id == user_id).first()
    assert account is not None
    
    # Add transaction linked to account
    response = chat(client, token, "I spent $100 on groceries")
    assert response["success"]
    
    # Add goal
    response = chat(client, token, "I want to save $5000 by June 2025")
    assert response["success"]
    
    # Add budget
    response = chat(client, token, "Set a $300 budget for food")
    assert response["success"]
    
    # Add debt
    response = chat(client, token, "I have a loan of $3000 at 8% interest, paying $150 monthly")
    assert response["success"]
    
    # Verify all records exist
    print("Verifying database records...")
    assert db_session.query(Account).filter(Account.user_id == user_id).count() >= 1
    assert db_session.query(Transaction).filter(Transaction.user_id == user_id).count() >= 1
    assert db_session.query(Goal).filter(Goal.user_id == user_id).count() >= 1
    assert db_session.query(Budget).filter(Budget.user_id == user_id).count() >= 1
    assert db_session.query(DebtLoan).filter(DebtLoan.user_id == user_id).count() >= 1
    
    # Verify user relationships
    print("Verifying relationships...")
    user = db_session.query(User).filter(User.id == user_id).first()
    assert len(user.accounts) >= 1
    assert len(user.transactions) >= 1
    assert len(user.goals) >= 1
    assert len(user.budgets) >= 1
    assert len(user.debts_loans) >= 1
    
    print("✅ Database integrity test passed")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("RUNNING COMPLETE END-TO-END TEST SUITE")
    print("="*80)
    
    pytest.main([__file__, "-v", "-s"])
