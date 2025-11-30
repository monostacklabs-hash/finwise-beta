import pytest
import json
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.financial_simulator import FinancialSimulator
from app.database.models import User, Transaction, Goal, Budget
from app.database.session import SessionLocal

class TestFinancialSimulation:
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
        """Create or retrieve a test user for simulations"""
        # Check if test user exists
        user = db_session.query(User).filter(User.email == "simulation_test@example.com").first()
        if not user:
            user = User(
                email="simulation_test@example.com",
                password_hash="hashed_test_password",
                name="Simulation Test User",
                currency="USD",
                timezone="UTC"
            )
            db_session.add(user)
            db_session.commit()
        return user

    @pytest.fixture(scope="class")
    def sample_transactions(self, db_session, test_user):
        """Create sample transactions for simulation testing"""
        # First, clear existing transactions
        db_session.query(Transaction).filter(Transaction.user_id == test_user.id).delete()

        # Create diverse transactions
        transactions = [
            Transaction(
                user_id=test_user.id,
                type="INCOME",
                amount=5000.00,
                description="Monthly Salary",
                category="Salary",
                date=datetime.utcnow() - timedelta(days=30)
            ),
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=1500.00,
                description="Rent",
                category="Housing",
                date=datetime.utcnow() - timedelta(days=25)
            ),
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=500.00,
                description="Groceries",
                category="Food",
                date=datetime.utcnow() - timedelta(days=20)
            ),
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=200.00,
                description="Entertainment",
                category="Discretionary",
                date=datetime.utcnow() - timedelta(days=15)
            )
        ]

        db_session.add_all(transactions)
        db_session.commit()
        return transactions

    @pytest.fixture(scope="class")
    def sample_goal(self, db_session, test_user):
        """Create a sample savings goal"""
        goal = Goal(
            user_id=test_user.id,
            name="Emergency Fund",
            target_amount=10000.00,
            current_amount=2000.00,
            target_date=datetime.utcnow() + timedelta(days=365),
            status="ACTIVE"
        )
        db_session.add(goal)
        db_session.commit()
        return goal

    def test_income_change_simulation(self, db_session, test_user, sample_transactions, sample_goal):
        """Simulate an income increase scenario"""
        simulator = FinancialSimulator()

        # Run simulation with 10% income increase
        simulation_result = simulator.simulate_scenario(
            user_id=test_user.id,
            scenario_type="income_change",
            change_percentage=0.1,
            db=db_session
        )

        # Validate simulation result structure
        assert isinstance(simulation_result, dict), "Simulation should return a dictionary"
        assert "baseline_balance" in simulation_result, "Baseline balance missing"
        assert "scenario_balance" in simulation_result, "Scenario balance missing"
        assert "recommendation" in simulation_result, "Recommendation missing"

        # Income should improve in scenario balance
        assert simulation_result["scenario_balance"] > simulation_result["baseline_balance"], \
            "Scenario balance should be higher after income increase"

    def test_expense_reduction_simulation(self, db_session, test_user, sample_transactions, sample_goal):
        """Simulate an expense reduction scenario"""
        simulator = FinancialSimulator()

        # Run simulation with 15% expense reduction
        simulation_result = simulator.simulate_scenario(
            user_id=test_user.id,
            scenario_type="expense_change",
            change_percentage=-0.15,
            db=db_session
        )

        # Validate simulation result structure
        assert isinstance(simulation_result, dict), "Simulation should return a dictionary"
        assert "baseline_balance" in simulation_result, "Baseline balance missing"
        assert "scenario_balance" in simulation_result, "Scenario balance missing"
        assert "recommendation" in simulation_result, "Recommendation missing"

        # Goal acceleration should be evident
        assert "goal_acceleration" in simulation_result["recommendation"].lower(), \
            "Recommendation should mention goal acceleration"

    def test_goal_acceleration_simulation(self, db_session, test_user, sample_transactions, sample_goal):
        """Simulate a goal acceleration scenario"""
        simulator = FinancialSimulator()

        # Run goal acceleration simulation
        simulation_result = simulator.simulate_scenario(
            user_id=test_user.id,
            scenario_type="goal_acceleration",
            additional_monthly_contribution=200.00,
            db=db_session
        )

        # Validate simulation result structure
        assert isinstance(simulation_result, dict), "Simulation should return a dictionary"
        assert "goal_progress" in simulation_result, "Goal progress missing"

        # Goal completion time should be shortened
        goal_progress = simulation_result["goal_progress"]
        assert goal_progress["original_completion_date"] is not None
        assert goal_progress["accelerated_completion_date"] is not None

        # Accelerated date should be earlier
        original_date = datetime.fromisoformat(goal_progress["original_completion_date"])
        accelerated_date = datetime.fromisoformat(goal_progress["accelerated_completion_date"])
        assert accelerated_date < original_date, "Accelerated completion should be earlier"

    def test_budget_cut_simulation(self, db_session, test_user, sample_transactions, sample_goal):
        """Simulate a category-specific budget cut"""
        simulator = FinancialSimulator()

        # Run budget cut simulation on discretionary spending
        simulation_result = simulator.simulate_scenario(
            user_id=test_user.id,
            scenario_type="budget_cut",
            category="Discretionary",
            change_percentage=-0.3,  # 30% reduction
            db=db_session
        )

        # Validate simulation result
        assert isinstance(simulation_result, dict), "Simulation should return a dictionary"
        assert "category_impact" in simulation_result, "Category impact missing"

        # Validate budget reduction
        category_impact = simulation_result["category_impact"]
        assert category_impact["category"] == "Discretionary"
        assert category_impact["original_spending"] is not None
        assert category_impact["reduced_spending"] is not None
        assert category_impact["reduction_percentage"] == -0.3

    def test_new_recurring_transaction_simulation(self, db_session, test_user, sample_transactions, sample_goal):
        """Simulate adding a new recurring transaction"""
        simulator = FinancialSimulator()

        # Run simulation with a new recurring expense
        simulation_result = simulator.simulate_scenario(
            user_id=test_user.id,
            scenario_type="new_recurring",
            recurring_amount=150.00,
            recurring_frequency="monthly",
            category="Subscriptions",
            db=db_session
        )

        # Validate simulation result
        assert isinstance(simulation_result, dict), "Simulation should return a dictionary"
        assert "cash_flow_impact" in simulation_result, "Cash flow impact missing"

        # Validate recurring transaction impact
        cash_flow_impact = simulation_result["cash_flow_impact"]
        assert cash_flow_impact["amount"] == 150.00
        assert cash_flow_impact["frequency"] == "monthly"
        assert cash_flow_impact["category"] == "Subscriptions"