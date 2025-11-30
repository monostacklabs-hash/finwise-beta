import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.dynamic_budget_adjuster import DynamicBudgetAdjuster
from app.database.models import User, Transaction, Budget
from app.database.session import SessionLocal

class TestDynamicBudgetAdjustments:
    @pytest.fixture(scope="class")
    def db_session(self):
        """Create a database session for the entire test class"""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture(scope="class")
    def test_user(self, db_session):
        """Create or retrieve a test user for budget adjustments"""
        user = db_session.query(User).filter(User.email == "budget_test@example.com").first()
        if not user:
            user = User(
                email="budget_test@example.com",
                password_hash="hashed_test_password",
                name="Budget Test User",
                currency="USD",
                timezone="UTC"
            )
            db_session.add(user)
            db_session.commit()
        return user

    @pytest.fixture(scope="class")
    def sample_budgets(self, db_session, test_user):
        """Create sample budgets with various categories"""
        # Clear existing budgets
        db_session.query(Budget).filter(Budget.user_id == test_user.id).delete()

        budgets = [
            Budget(
                user_id=test_user.id,
                category="Food",
                amount=500.00,
                period="monthly",
                start_date=datetime.utcnow(),
                is_active=True
            ),
            Budget(
                user_id=test_user.id,
                category="Transportation",
                amount=200.00,
                period="monthly",
                start_date=datetime.utcnow(),
                is_active=True
            ),
            Budget(
                user_id=test_user.id,
                category="Entertainment",
                amount=150.00,
                period="monthly",
                start_date=datetime.utcnow(),
                is_active=True
            )
        ]

        db_session.add_all(budgets)
        db_session.commit()
        return budgets

    @pytest.fixture(scope="class")
    def sample_transactions(self, db_session, test_user):
        """Create sample transactions to test budget adjustments"""
        # Clear existing transactions
        db_session.query(Transaction).filter(Transaction.user_id == test_user.id).delete()

        transactions = [
            # Overspending in Food category
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=600.00,
                description="Groceries and Dining",
                category="Food",
                date=datetime.utcnow() - timedelta(days=10)
            ),
            # Normal spending in Transportation
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=180.00,
                description="Public Transport and Gas",
                category="Transportation",
                date=datetime.utcnow() - timedelta(days=15)
            ),
            # Underspending in Entertainment
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=50.00,
                description="Movie and Snacks",
                category="Entertainment",
                date=datetime.utcnow() - timedelta(days=5)
            )
        ]

        db_session.add_all(transactions)
        db_session.commit()
        return transactions

    def test_overspending_budget_adjustment(self, db_session, test_user, sample_budgets, sample_transactions):
        """Test dynamic budget adjustment for overspent categories"""
        adjuster = DynamicBudgetAdjuster()

        # Analyze and adjust budgets
        adjustment_result = adjuster.analyze_and_adjust_budgets(
            user_id=test_user.id,
            db=db_session
        )

        # Validate adjustment results
        assert "adjustments" in adjustment_result, "Missing budget adjustments"
        adjustments = adjustment_result["adjustments"]

        # Check Food category adjustment (overspent)
        food_adjustment = next(
            (adj for adj in adjustments if adj["category"] == "Food"),
            None
        )
        assert food_adjustment is not None, "No adjustment for overspent Food category"
        assert food_adjustment["change_type"] == "reduce", "Should recommend reducing Food budget"
        assert food_adjustment["change_percentage"] < 0, "Budget reduction should be negative"

    def test_underspending_budget_reallocation(self, db_session, test_user, sample_budgets, sample_transactions):
        """Test budget reallocation from underspent categories"""
        adjuster = DynamicBudgetAdjuster()

        # Analyze and adjust budgets
        adjustment_result = adjuster.analyze_and_adjust_budgets(
            user_id=test_user.id,
            db=db_session
        )

        # Validate adjustment results
        assert "adjustments" in adjustment_result, "Missing budget adjustments"
        adjustments = adjustment_result["adjustments"]

        # Check Entertainment category (underspent)
        entertainment_adjustment = next(
            (adj for adj in adjustments if adj["category"] == "Entertainment"),
            None
        )
        assert entertainment_adjustment is not None, "No adjustment for underspent Entertainment category"
        assert entertainment_adjustment["change_type"] == "reallocate", "Should recommend reallocating Entertainment budget"

    def test_goal_based_budget_optimization(self, db_session, test_user, sample_budgets, sample_transactions):
        """Test budget adjustments based on active financial goals"""
        from app.database.models import Goal

        # Create a savings goal
        goal = Goal(
            user_id=test_user.id,
            name="Emergency Fund",
            target_amount=12000.00,  # $1000/month for a year
            current_amount=3000.00,
            target_date=datetime.utcnow() + timedelta(days=365),
            status="ACTIVE",
            priority=4
        )
        db_session.add(goal)
        db_session.commit()

        adjuster = DynamicBudgetAdjuster()

        # Analyze and adjust budgets with goal context
        adjustment_result = adjuster.analyze_and_adjust_budgets(
            user_id=test_user.id,
            db=db_session,
            include_goal_optimization=True
        )

        # Validate adjustment results
        assert "goal_optimization" in adjustment_result, "Missing goal optimization details"
        goal_optimization = adjustment_result["goal_optimization"]

        assert goal_optimization["goal_name"] == "Emergency Fund", "Goal optimization for wrong goal"
        assert "recommended_savings_increase" in goal_optimization, "No recommended savings increase"

        # Validate recommendation
        savings_increase = goal_optimization["recommended_savings_increase"]
        assert savings_increase > 0, "Should recommend increasing savings for goal"

    def test_budget_adjustment_approval_workflow(self, db_session, test_user, sample_budgets, sample_transactions):
        """Test budget adjustment approval workflow"""
        adjuster = DynamicBudgetAdjuster()

        # Analyze and generate budget adjustments
        adjustment_result = adjuster.analyze_and_adjust_budgets(
            user_id=test_user.id,
            db=db_session,
            approval_mode=True
        )

        # Validate adjustment results
        assert "adjustments" in adjustment_result, "Missing budget adjustments"
        adjustments = adjustment_result["adjustments"]

        # Check that all adjustments require user approval
        for adjustment in adjustments:
            assert adjustment.get("requires_approval", False) is True, \
                f"Adjustment for {adjustment['category']} should require approval in approval mode"

        # Validate approval status
        approval_status = adjustment_result.get("approval_status", {})
        assert "pending_adjustments" in approval_status, "Missing pending adjustments status"
        assert approval_status["pending_adjustments"] > 0, "No pending adjustments to review"