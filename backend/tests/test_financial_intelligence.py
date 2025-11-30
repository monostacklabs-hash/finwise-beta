"""
Test that the AI agent actually provides intelligent financial advice
Not just that tools are called, but that the responses are meaningful
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.models import Base, User, Transaction, Goal, DebtLoan, Budget
from app.database.models import TransactionType
from app.database.session import get_db

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_intelligence.db"
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


def register_user(client, email="test@example.com"):
    """Helper to register and return token"""
    response = client.post(f"{API_PREFIX}/auth/register", json={
        "email": email,
        "password": "Test123!",
        "name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    return data["access_token"], data["user"]["id"]


def chat(client, token, message):
    """Helper to send chat message"""
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(f"{API_PREFIX}/chat", json={"message": message}, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_financial_health_assessment(client, db_session):
    """
    Test: Can the agent assess my financial health?
    Expected: Provides score, identifies issues, gives recommendations
    """
    print("\n" + "="*80)
    print("TEST: Financial Health Assessment")
    print("="*80)
    
    token, user_id = register_user(client, "health@test.com")
    
    # Setup: Poor financial situation
    chat(client, token, "I earn $3000 per month")
    chat(client, token, "My expenses are $2800 per month")
    chat(client, token, "I have $8000 credit card debt at 22% interest")
    chat(client, token, "I have no savings")
    
    # Ask for financial health
    print("\n💬 USER: How am I doing financially?")
    result = chat(client, token, "How am I doing financially?")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    # Verify the response contains actual analysis
    response_lower = result['response'].lower()
    
    # Should mention health/score
    assert any(word in response_lower for word in ['health', 'score', 'fair', 'poor', 'good']), \
        "❌ Response doesn't mention financial health or score"
    print("✅ Response mentions financial health/score")
    
    # Should identify debt as an issue
    assert 'debt' in response_lower, \
        "❌ Response doesn't identify debt as an issue"
    print("✅ Response identifies debt issue")
    
    # Should provide recommendations
    assert any(word in response_lower for word in ['recommend', 'should', 'consider', 'suggest']), \
        "❌ Response doesn't provide recommendations"
    print("✅ Response provides recommendations")
    
    # Verify tool was actually called
    assert 'calculate_financial_health' in str(result.get('tools_used', [])), \
        "❌ Financial health tool was not called"
    print("✅ Financial health tool was called")


def test_debt_payoff_strategy(client, db_session):
    """
    Test: Can the agent help me get out of debt?
    Expected: Provides specific payoff strategy with timeline
    """
    print("\n" + "="*80)
    print("TEST: Debt Payoff Strategy")
    print("="*80)
    
    token, user_id = register_user(client, "debt@test.com")
    
    # Setup: Multiple debts
    chat(client, token, "I have a credit card with $5000 at 18% interest, paying $200/month")
    chat(client, token, "I have a car loan of $15000 at 6% interest, paying $400/month")
    chat(client, token, "I have $500 extra per month")
    
    # Ask for debt strategy
    print("\n💬 USER: How should I pay off my debts faster?")
    result = chat(client, token, "How should I pay off my debts faster?")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    response_lower = result['response'].lower()
    
    # Should mention a strategy (avalanche or snowball)
    assert any(word in response_lower for word in ['avalanche', 'snowball', 'strategy', 'method']), \
        "❌ Response doesn't mention a debt payoff strategy"
    print("✅ Response mentions debt payoff strategy")
    
    # Should mention interest or savings
    assert any(word in response_lower for word in ['interest', 'save', 'saving']), \
        "❌ Response doesn't discuss interest savings"
    print("✅ Response discusses interest/savings")
    
    # Should provide timeline or specific advice
    assert any(word in response_lower for word in ['month', 'year', 'pay', 'payment']), \
        "❌ Response doesn't provide timeline or payment advice"
    print("✅ Response provides timeline/payment advice")
    
    # Verify optimization tool was called
    assert 'optimize_debt_repayment' in str(result.get('tools_used', [])), \
        "❌ Debt optimization tool was not called"
    print("✅ Debt optimization tool was called")
    
    # Verify debts exist in DB
    debt_count = db_session.query(DebtLoan).filter(DebtLoan.user_id == user_id).count()
    assert debt_count == 2, f"❌ Expected 2 debts in DB, found {debt_count}"
    print(f"✅ Both debts recorded in database ({debt_count} debts)")


def test_savings_goal_planning(client, db_session):
    """
    Test: Can the agent help me plan to reach a savings goal?
    Expected: Tells me if goal is achievable and how long it will take
    """
    print("\n" + "="*80)
    print("TEST: Savings Goal Planning")
    print("="*80)
    
    token, user_id = register_user(client, "savings@test.com")
    
    # Setup: Income and expenses
    chat(client, token, "I earn $5000 per month")
    chat(client, token, "My expenses are $3500 per month")
    
    # Set a goal
    chat(client, token, "I want to save $20,000 for a house down payment by December 2026")
    
    # Ask about goal feasibility
    print("\n💬 USER: Can I reach my down payment goal? When will I achieve it?")
    result = chat(client, token, "Can I reach my down payment goal? When will I achieve it?")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    response_lower = result['response'].lower()
    
    # Should discuss timeline
    assert any(word in response_lower for word in ['month', 'year', 'achieve', 'reach', 'complete']), \
        "❌ Response doesn't discuss timeline"
    print("✅ Response discusses timeline")
    
    # Should mention the goal or amount
    assert any(word in response_lower for word in ['goal', 'down payment', '20', 'save', 'saving']), \
        "❌ Response doesn't reference the goal"
    print("✅ Response references the goal")
    
    # Should provide feasibility assessment
    assert any(word in response_lower for word in ['can', 'will', 'able', 'possible', 'need', 'require']), \
        "❌ Response doesn't assess feasibility"
    print("✅ Response assesses feasibility")
    
    # Verify goal exists in DB
    goal = db_session.query(Goal).filter(
        Goal.user_id == user_id,
        Goal.target_amount == 20000
    ).first()
    assert goal is not None, "❌ Goal not found in database"
    print(f"✅ Goal recorded in database: ${goal.target_amount}")


def test_spending_analysis(client, db_session):
    """
    Test: Can the agent analyze where my money is going?
    Expected: Breaks down spending by category
    """
    print("\n" + "="*80)
    print("TEST: Spending Analysis")
    print("="*80)
    
    token, user_id = register_user(client, "spending@test.com")
    
    # Add diverse expenses
    chat(client, token, "I spent $800 on rent")
    chat(client, token, "I spent $300 on groceries")
    chat(client, token, "I spent $150 on restaurants")
    chat(client, token, "I spent $100 on gas")
    chat(client, token, "I spent $80 on entertainment")
    
    # Ask for spending analysis
    print("\n💬 USER: Where is my money going?")
    result = chat(client, token, "Where is my money going?")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    response_lower = result['response'].lower()
    
    # Should mention categories
    assert any(word in response_lower for word in ['category', 'categories', 'spending', 'spent']), \
        "❌ Response doesn't mention spending categories"
    print("✅ Response mentions spending categories")
    
    # Should mention specific categories or amounts
    assert any(word in response_lower for word in ['rent', 'food', 'groceries', 'restaurant', 'entertainment']), \
        "❌ Response doesn't mention specific spending categories"
    print("✅ Response mentions specific categories")
    
    # Verify analysis tool was called
    assert 'analyze_spending_by_category' in str(result.get('tools_used', [])), \
        "❌ Spending analysis tool was not called"
    print("✅ Spending analysis tool was called")
    
    # Verify transactions in DB
    transaction_count = db_session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE
    ).count()
    assert transaction_count >= 5, f"❌ Expected at least 5 transactions, found {transaction_count}"
    print(f"✅ All transactions recorded ({transaction_count} expenses)")


def test_budget_recommendations(client, db_session):
    """
    Test: Can the agent help me create a realistic budget?
    Expected: Suggests budget amounts based on my spending
    """
    print("\n" + "="*80)
    print("TEST: Budget Recommendations")
    print("="*80)
    
    token, user_id = register_user(client, "budget@test.com")
    
    # Setup: Income and some expenses
    chat(client, token, "I earn $4000 per month")
    chat(client, token, "I spent $600 on food last month")
    chat(client, token, "I spent $200 on entertainment")
    
    # Ask for budget help
    print("\n💬 USER: Help me create a budget")
    result = chat(client, token, "Help me create a budget")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    response_lower = result['response'].lower()
    
    # Should mention budget
    assert 'budget' in response_lower, \
        "❌ Response doesn't mention budget"
    print("✅ Response mentions budget")
    
    # Should provide specific amounts or percentages
    assert any(char in result['response'] for char in ['$', '%', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']), \
        "❌ Response doesn't include specific amounts"
    print("✅ Response includes specific amounts")
    
    # Should mention categories
    assert any(word in response_lower for word in ['food', 'entertainment', 'category', 'housing', 'transport']), \
        "❌ Response doesn't mention budget categories"
    print("✅ Response mentions budget categories")


def test_what_if_scenarios(client, db_session):
    """
    Test: Can the agent run what-if scenarios?
    Expected: Shows impact of financial changes
    """
    print("\n" + "="*80)
    print("TEST: What-If Scenarios")
    print("="*80)
    
    token, user_id = register_user(client, "whatif@test.com")
    
    # Setup baseline
    chat(client, token, "I earn $5000 per month")
    chat(client, token, "My expenses are $4000 per month")
    
    # Run what-if scenario
    print("\n💬 USER: What if I get a $1000 raise?")
    result = chat(client, token, "What if I get a $1000 raise?")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    response_lower = result['response'].lower()
    
    # Should discuss the scenario
    assert any(word in response_lower for word in ['raise', '1000', 'increase', 'more', 'extra']), \
        "❌ Response doesn't address the scenario"
    print("✅ Response addresses the scenario")
    
    # Should show impact
    assert any(word in response_lower for word in ['save', 'saving', 'surplus', 'extra', 'more', 'increase']), \
        "❌ Response doesn't show financial impact"
    print("✅ Response shows financial impact")
    
    # Should provide forward-looking advice
    assert any(word in response_lower for word in ['could', 'would', 'can', 'able', 'help']), \
        "❌ Response doesn't provide forward-looking advice"
    print("✅ Response provides forward-looking advice")


def test_cash_flow_forecasting(client, db_session):
    """
    Test: Can the agent predict if I'll run out of money?
    Expected: Forecasts cash flow and warns of issues
    """
    print("\n" + "="*80)
    print("TEST: Cash Flow Forecasting")
    print("="*80)
    
    token, user_id = register_user(client, "cashflow@test.com")
    
    # Setup: Tight cash situation
    chat(client, token, "I have $2000 in my checking account")
    chat(client, token, "I earn $3000 per month")
    chat(client, token, "My expenses are $2900 per month")
    
    # Ask about cash flow
    print("\n💬 USER: Will I run out of money in the next 3 months?")
    result = chat(client, token, "Will I run out of money in the next 3 months?")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    response_lower = result['response'].lower()
    
    # Should address the question
    assert any(word in response_lower for word in ['month', 'balance', 'cash', 'money', 'forecast']), \
        "❌ Response doesn't address cash flow"
    print("✅ Response addresses cash flow")
    
    # Should provide prediction or analysis
    assert any(word in response_lower for word in ['will', 'should', 'expect', 'predict', 'forecast', 'project']), \
        "❌ Response doesn't provide prediction"
    print("✅ Response provides prediction")


def test_comprehensive_financial_advice(client, db_session):
    """
    Test: Complete scenario - user in debt wants to save for a goal
    Expected: Agent provides holistic advice considering all factors
    """
    print("\n" + "="*80)
    print("TEST: Comprehensive Financial Advice")
    print("="*80)
    
    token, user_id = register_user(client, "comprehensive@test.com")
    
    # Setup: Complex financial situation
    print("\n📝 Setting up complex financial situation...")
    chat(client, token, "I earn $6000 per month")
    chat(client, token, "My expenses are $4000 per month")
    chat(client, token, "I have $10,000 credit card debt at 20% interest, paying $300/month")
    chat(client, token, "I want to save $30,000 for a wedding in 2 years")
    
    # Ask for comprehensive advice
    print("\n💬 USER: Should I focus on paying off debt or saving for my wedding?")
    result = chat(client, token, "Should I focus on paying off debt or saving for my wedding?")
    
    print(f"\n🤖 AGENT: {result['response']}\n")
    
    response_lower = result['response'].lower()
    
    # Should acknowledge both debt and goal
    assert 'debt' in response_lower, "❌ Response doesn't mention debt"
    assert any(word in response_lower for word in ['wedding', 'goal', 'save', 'saving']), \
        "❌ Response doesn't mention the savings goal"
    print("✅ Response acknowledges both debt and savings goal")
    
    # Should provide prioritization advice
    assert any(word in response_lower for word in ['first', 'priority', 'focus', 'should', 'recommend']), \
        "❌ Response doesn't provide prioritization advice"
    print("✅ Response provides prioritization advice")
    
    # Should consider interest/math
    assert any(word in response_lower for word in ['interest', 'cost', 'save', 'pay']), \
        "❌ Response doesn't consider financial math"
    print("✅ Response considers financial math")
    
    # Should provide actionable plan
    assert any(word in response_lower for word in ['plan', 'strategy', 'could', 'can', 'month']), \
        "❌ Response doesn't provide actionable plan"
    print("✅ Response provides actionable plan")
    
    # Verify data in DB
    debt_count = db_session.query(DebtLoan).filter(DebtLoan.user_id == user_id).count()
    goal_count = db_session.query(Goal).filter(Goal.user_id == user_id).count()
    assert debt_count >= 1, "❌ Debt not recorded"
    assert goal_count >= 1, "❌ Goal not recorded"
    print(f"✅ Financial situation recorded: {debt_count} debt(s), {goal_count} goal(s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
