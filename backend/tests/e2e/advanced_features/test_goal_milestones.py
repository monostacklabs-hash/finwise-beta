import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.goal_milestone_adjuster import GoalMilestoneAdjuster
from app.database.models import User, Goal, Transaction
from app.database.session import SessionLocal

class TestGoalMilestones:
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
        """Create or retrieve a test user for goal milestones"""
        user = db_session.query(User).filter(User.email == "milestones_test@example.com").first()
        if not user:
            user = User(
                email="milestones_test@example.com",
                password_hash="hashed_test_password",
                name="Milestones Test User",
                currency="USD",
                timezone="UTC"
            )
            db_session.add(user)
            db_session.commit()
        return user

    @pytest.fixture(scope="class")
    def sample_transactions(self, db_session, test_user):
        """Create sample transactions to track goal progress"""
        # Clear existing transactions
        db_session.query(Transaction).filter(Transaction.user_id == test_user.id).delete()

        # Create transactions showing consistent savings
        transactions = [
            Transaction(
                user_id=test_user.id,
                type="INCOME",
                amount=6000.00,
                description="Monthly Salary",
                category="Salary",
                date=datetime.utcnow() - timedelta(days=30)
            ),
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=4000.00,
                description="Monthly Expenses",
                category="Living Expenses",
                date=datetime.utcnow() - timedelta(days=30)
            ),
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=1000.00,
                description="Savings Contribution",
                category="Savings",
                date=datetime.utcnow() - timedelta(days=15)
            )
        ]

        db_session.add_all(transactions)
        db_session.commit()
        return transactions

    def test_create_goal_with_milestones(self, db_session, test_user, sample_transactions):
        """Create a goal and verify milestone generation"""
        # Create a 1-year savings goal
        goal = Goal(
            user_id=test_user.id,
            name="Down Payment Savings",
            target_amount=24000.00,  # $2000/month for a year
            current_amount=6000.00,  # Already saved some
            target_date=datetime.utcnow() + timedelta(days=365),
            status="ACTIVE",
            priority=4
        )
        db_session.add(goal)
        db_session.commit()

        # Use milestone adjuster to calculate milestones
        milestone_adjuster = GoalMilestoneAdjuster()
        milestone_result = milestone_adjuster.calculate_adaptive_milestones(goal.id, db_session)

        # Validate milestone results
        assert isinstance(milestone_result, dict), "Milestone result should be a dictionary"

        # Check milestone percentages
        milestone_percentages = [0.25, 0.50, 0.75, 1.0]
        for percentage in milestone_percentages:
            milestone_key = f"{int(percentage * 100)}%_milestone"
            assert milestone_key in milestone_result, f"Missing {milestone_key}"

            milestone = milestone_result[milestone_key]
            assert "date" in milestone, f"Missing date for {milestone_key}"
            assert "status" in milestone, f"Missing status for {milestone_key}"

    def test_goal_tracking_with_changing_savings_rate(self, db_session, test_user, sample_transactions):
        """Test milestone tracking with variable savings rates"""
        # Create a 2-year long-term goal
        goal = Goal(
            user_id=test_user.id,
            name="Retirement Fund",
            target_amount=60000.00,  # $2500/month for 2 years
            current_amount=10000.00,
            target_date=datetime.utcnow() + timedelta(days=730),
            status="ACTIVE",
            priority=5
        )
        db_session.add(goal)
        db_session.commit()

        # Simulate varying savings rates
        varying_transactions = [
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=2500.00,  # Savings contribution
                description="Goal Contribution - Strong Month",
                category="Savings",
                date=datetime.utcnow() - timedelta(days=60)
            ),
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=1000.00,  # Lower contribution
                description="Goal Contribution - Moderate Month",
                category="Savings",
                date=datetime.utcnow() - timedelta(days=30)
            ),
            Transaction(
                user_id=test_user.id,
                type="EXPENSE",
                amount=500.00,  # Low contribution
                description="Goal Contribution - Weak Month",
                category="Savings",
                date=datetime.utcnow() - timedelta(days=15)
            )
        ]
        db_session.add_all(varying_transactions)
        db_session.commit()

        # Calculate milestones
        milestone_adjuster = GoalMilestoneAdjuster()
        milestone_result = milestone_adjuster.calculate_adaptive_milestones(goal.id, db_session)

        # Validate milestone results with changing savings rate
        assert "projection_details" in milestone_result, "Missing projection details"
        projection_details = milestone_result["projection_details"]

        assert "initial_savings_rate" in projection_details
        assert "current_savings_rate" in projection_details
        assert "projected_completion_date" in projection_details

        # Savings rate should show decline
        initial_rate = projection_details["initial_savings_rate"]
        current_rate = projection_details["current_savings_rate"]
        assert current_rate < initial_rate, "Savings rate should show decline"

    def test_goal_milestone_recommendations(self, db_session, test_user, sample_transactions):
        """Test generating recommendations based on milestone tracking"""
        goal = Goal(
            user_id=test_user.id,
            name="Emergency Fund",
            target_amount=36000.00,  # $3000/month for a year
            current_amount=15000.00,
            target_date=datetime.utcnow() + timedelta(days=365),
            status="ACTIVE",
            priority=3
        )
        db_session.add(goal)
        db_session.commit()

        milestone_adjuster = GoalMilestoneAdjuster()
        milestone_result = milestone_adjuster.calculate_adaptive_milestones(goal.id, db_session)

        # Validate recommendations
        assert "recommendations" in milestone_result, "Missing milestone recommendations"
        recommendations = milestone_result["recommendations"]

        assert isinstance(recommendations, list), "Recommendations should be a list"
        assert len(recommendations) > 0, "Should have at least one recommendation"

        # Check recommendation structure
        for rec in recommendations:
            assert "type" in rec, "Recommendation missing type"
            assert "description" in rec, "Recommendation missing description"
            assert "impact" in rec, "Recommendation missing impact"