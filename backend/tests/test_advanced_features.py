"""
Tests for Advanced Budgeting & Forecasting Features
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.models import User, Budget, Goal, Transaction, TransactionType, GoalStatus
from app.services.dynamic_budget_adjuster import DynamicBudgetAdjuster
from app.services.goal_milestone_adjuster import GoalMilestoneAdjuster
from app.services.financial_simulator import FinancialSimulator
from app.database.category_hierarchy import CATEGORY_HIERARCHY


def test_category_hierarchy():
    """Test hierarchical category system"""
    # Test parent-child relationships
    assert CATEGORY_HIERARCHY.get_parent("groceries") == "home"
    assert CATEGORY_HIERARCHY.get_parent("fresh_produce") == "groceries"
    
    # Test root category
    assert CATEGORY_HIERARCHY.get_root_category("fresh_produce") == "home"
    
    # Test full path
    path = CATEGORY_HIERARCHY.get_full_path("fresh_produce")
    assert "home" in path
    assert "groceries" in path
    assert "fresh_produce" in path
    
    # Test children
    children = CATEGORY_HIERARCHY.get_children("home")
    assert "groceries" in children
    assert "utilities" in children
    
    # Test category suggestion
    category = CATEGORY_HIERARCHY.suggest_category("Whole Foods groceries")
    assert category in ["groceries", "fresh_produce"]


def test_dynamic_budget_adjuster(db: Session, test_user: User):
    """Test dynamic budget adjustment recommendations"""
    # Create test budgets
    budget1 = Budget(
        id="budget1",
        user_id=test_user.id,
        category="dining_out",
        amount=500,
        period="monthly",
        start_date=datetime.utcnow(),
        is_active=True,
    )
    budget2 = Budget(
        id="budget2",
        user_id=test_user.id,
        category="groceries",
        amount=400,
        period="monthly",
        start_date=datetime.utcnow(),
        is_active=True,
    )
    db.add_all([budget1, budget2])
    
    # Add transactions (overspending in dining_out)
    for i in range(10):
        txn = Transaction(
            id=f"txn{i}",
            user_id=test_user.id,
            type=TransactionType.EXPENSE,
            amount=60,  # Total $600 > $500 budget
            description=f"Restaurant {i}",
            category="dining_out",
            date=datetime.utcnow() - timedelta(days=i),
        )
        db.add(txn)
    
    db.commit()
    
    # Analyze budgets
    analysis = DynamicBudgetAdjuster.analyze_and_adjust_budgets(db, test_user.id)
    
    assert analysis["status"] == "success"
    assert analysis["total_budgets"] == 2
    assert analysis["overspent_categories"] >= 1
    assert len(analysis["adjustments"]) > 0


def test_goal_milestone_adjuster(db: Session, test_user: User):
    """Test AI-adjusted goal milestones"""
    # Create test goal
    goal = Goal(
        id="goal1",
        user_id=test_user.id,
        name="Emergency Fund",
        target_amount=10000,
        current_amount=2000,
        target_date=datetime.utcnow() + timedelta(days=365),
        status=GoalStatus.ACTIVE,
        priority=3,
    )
    db.add(goal)
    
    # Add income and expense transactions
    for i in range(30):
        income = Transaction(
            id=f"income{i}",
            user_id=test_user.id,
            type=TransactionType.INCOME,
            amount=3000,
            description="Salary",
            category="salary",
            date=datetime.utcnow() - timedelta(days=i*30),
        )
        expense = Transaction(
            id=f"expense{i}",
            user_id=test_user.id,
            type=TransactionType.EXPENSE,
            amount=2500,
            description="Living expenses",
            category="groceries",
            date=datetime.utcnow() - timedelta(days=i*30),
        )
        db.add_all([income, expense])
    
    db.commit()
    
    # Calculate milestones
    milestone_data = GoalMilestoneAdjuster.calculate_adaptive_milestones(
        db, test_user.id, goal.id
    )
    
    assert milestone_data["goal_id"] == goal.id
    assert milestone_data["target_amount"] == 10000
    assert milestone_data["current_amount"] == 2000
    assert len(milestone_data["milestones"]) == 4  # 25%, 50%, 75%, 100%
    assert "recommendations" in milestone_data
    assert len(milestone_data["recommendations"]) > 0


def test_financial_simulator(db: Session, test_user: User):
    """Test financial simulation scenarios"""
    # Add some transactions for baseline
    for i in range(30):
        income = Transaction(
            id=f"sim_income{i}",
            user_id=test_user.id,
            type=TransactionType.INCOME,
            amount=100,
            description="Daily income",
            category="salary",
            date=datetime.utcnow() - timedelta(days=i),
        )
        expense = Transaction(
            id=f"sim_expense{i}",
            user_id=test_user.id,
            type=TransactionType.EXPENSE,
            amount=80,
            description="Daily expense",
            category="groceries",
            date=datetime.utcnow() - timedelta(days=i),
        )
        db.add_all([income, expense])
    
    db.commit()
    
    # Test income change scenario
    result = FinancialSimulator.simulate_scenario(
        db,
        test_user.id,
        "income_change",
        {"change_amount": 500, "change_type": "fixed", "starting_balance": 5000},
        forecast_days=90,
    )
    
    assert result["scenario_type"] == "income_change"
    assert "baseline" in result
    assert "scenario" in result
    assert "comparison" in result
    assert result["comparison"]["is_improvement"] == True
    
    # Test expense reduction scenario
    result2 = FinancialSimulator.simulate_scenario(
        db,
        test_user.id,
        "expense_change",
        {"change_amount": -300, "starting_balance": 5000},
        forecast_days=90,
    )
    
    assert result2["scenario_type"] == "expense_change"
    assert result2["comparison"]["is_improvement"] == True


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        id="test_user_advanced",
        email="test_advanced@example.com",
        password_hash="hashed",
        name="Test User",
        timezone="UTC",
        currency="USD",
    )
    db.add(user)
    db.commit()
    return user
