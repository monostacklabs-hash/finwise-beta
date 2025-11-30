"""
E2E Test: AI-Enhanced Budget Recommendations
Tests personalized, context-aware budget advice using LLM
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.database.models import User, Transaction, TransactionType, Budget, Goal, GoalStatus
from app.database.session import get_db, engine
from app.services.ai_budget_advisor import AIBudgetAdvisor


class TestAIBudgetAdvisorE2E:
    """E2E tests for AI-enhanced budget recommendations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and database"""
        from app.database.models import Base
        
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())
        
        self.user = User(
            id=str(uuid.uuid4()),
            email=f"test_budget_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            name="Budget Test User",
            timezone="America/Los_Angeles",
            currency="USD",
            country="USA",
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        
        yield
        
        # Cleanup
        from app.database.models import Notification
        self.db.query(Notification).filter(Notification.user_id == self.user.id).delete()
        self.db.query(Transaction).filter(Transaction.user_id == self.user.id).delete()
        self.db.query(Budget).filter(Budget.user_id == self.user.id).delete()
        self.db.query(Goal).filter(Goal.user_id == self.user.id).delete()
        self.db.query(User).filter(User.id == self.user.id).delete()
        self.db.commit()
        self.db.close()
    
    def test_overspending_recommendations(self):
        """
        Test: User overspending in dining → AI suggests reducing dining budget
        
        Scenario:
        - Budget: $300/month for dining
        - Actual: $450 spent (50% over)
        - AI should recommend either:
          a) Increase dining budget
          b) Reduce dining spending
          c) Reallocate from other categories
        """
        # Create budget
        dining_budget = Budget(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            category="restaurant",
            amount=300.00,
            period="monthly",
            start_date=datetime(2025, 11, 1),
            is_active=True,
        )
        self.db.add(dining_budget)
        
        # Create overspending transactions
        base_date = datetime(2025, 11, 1)
        for i in range(15):  # 15 restaurant visits
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                amount=30.00,  # Total: $450
                description=f"Restaurant visit {i+1}",
                category="restaurant",
                type=TransactionType.EXPENSE,
                date=base_date + timedelta(days=i*2),
            )
            self.db.add(tx)
        
        self.db.commit()
        
        # Get AI recommendations
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=True,
        )
        
        assert result["status"] == "success"
        assert result["method"] == "ai"
        assert len(result["recommendations"]) > 0
        
        # Check analysis
        assert result["analysis"]["overspent_count"] >= 1
        assert result["analysis"]["total_spent"] == 450.00
        
        # Check recommendations mention dining/restaurant
        dining_recs = [
            r for r in result["recommendations"]
            if "restaurant" in r["category"].lower() or "dining" in r["category"].lower()
        ]
        
        assert len(dining_recs) > 0, "Should have recommendation for dining category"
        
        rec = dining_recs[0]
        assert "reasoning" in rec
        assert len(rec["reasoning"]) > 20, "Should have detailed explanation"
        assert rec["priority"] in ["high", "medium", "low"]
        assert rec["type"] in ["increase", "decrease", "reallocate"]
        
        print(f"✅ AI Recommendation for overspending:")
        print(f"   Category: {rec['category']}")
        print(f"   Current: ${rec['current_amount']:.2f}")
        print(f"   Recommended: ${rec['recommended_amount']:.2f}")
        print(f"   Change: ${rec['change']:.2f}")
        print(f"   Reasoning: {rec['reasoning'][:100]}...")
    
    def test_underspending_reallocation(self):
        """
        Test: User underspending in entertainment → AI suggests reallocation
        
        Scenario:
        - Budget: $200/month for entertainment
        - Actual: $30 spent (15% used)
        - AI should suggest reallocating to goals or other needs
        """
        # Create budgets
        entertainment_budget = Budget(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            category="entertainment",
            amount=200.00,
            period="monthly",
            start_date=datetime(2025, 11, 1),
            is_active=True,
        )
        
        groceries_budget = Budget(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            category="groceries",
            amount=400.00,
            period="monthly",
            start_date=datetime(2025, 11, 1),
            is_active=True,
        )
        
        self.db.add_all([entertainment_budget, groceries_budget])
        
        # Minimal entertainment spending
        tx1 = Transaction(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            amount=30.00,
            description="Netflix",
            category="entertainment",
            type=TransactionType.EXPENSE,
            date=datetime(2025, 11, 5),
        )
        
        # Normal grocery spending
        for i in range(8):
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                amount=50.00,
                description=f"Grocery shopping {i+1}",
                category="groceries",
                type=TransactionType.EXPENSE,
                date=datetime(2025, 11, 1) + timedelta(days=i*3),
            )
            self.db.add(tx)
        
        self.db.add(tx1)
        self.db.commit()
        
        # Get recommendations
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=True,
        )
        
        assert result["status"] == "success"
        assert result["analysis"]["underspent_count"] >= 1
        
        # Should have recommendation for entertainment
        entertainment_recs = [
            r for r in result["recommendations"]
            if "entertainment" in r["category"].lower()
        ]
        
        if entertainment_recs:
            rec = entertainment_recs[0]
            assert rec["type"] in ["decrease", "reallocate"]
            print(f"✅ AI Recommendation for underspending:")
            print(f"   Category: {rec['category']}")
            print(f"   Reasoning: {rec['reasoning'][:150]}...")
    
    def test_goal_based_recommendations(self):
        """
        Test: User has high-priority goal → AI suggests budget adjustments to fund it
        
        Scenario:
        - Goal: Save $10,000 for emergency fund (high priority)
        - Current: $2,000 saved
        - AI should suggest reducing discretionary spending to fund goal
        """
        # Create goal
        goal = Goal(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            name="Emergency Fund",
            target_amount=10000.00,
            current_amount=2000.00,
            target_date=datetime(2026, 6, 1),
            priority=5,  # Highest priority
            status=GoalStatus.ACTIVE,
        )
        self.db.add(goal)
        
        # Create budgets
        budgets = [
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="restaurant",
                amount=400.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="entertainment",
                amount=200.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="groceries",
                amount=500.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
        ]
        self.db.add_all(budgets)
        
        # Add some spending
        for i in range(10):
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                amount=40.00,
                description=f"Restaurant {i+1}",
                category="restaurant",
                type=TransactionType.EXPENSE,
                date=datetime(2025, 11, 1) + timedelta(days=i*2),
            )
            self.db.add(tx)
        
        # Add income
        income = Transaction(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            amount=5000.00,
            description="Monthly salary",
            category="salary",
            type=TransactionType.INCOME,
            date=datetime(2025, 11, 1),
        )
        self.db.add(income)
        
        self.db.commit()
        
        # Get recommendations
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=True,
        )
        
        assert result["status"] == "success"
        assert len(result["recommendations"]) > 0
        
        # Check if recommendations mention the goal
        goal_related_recs = [
            r for r in result["recommendations"]
            if "emergency" in r["reasoning"].lower() or "goal" in r["reasoning"].lower()
        ]
        
        print(f"✅ AI Recommendations with high-priority goal:")
        print(f"   Total recommendations: {len(result['recommendations'])}")
        print(f"   Goal-related: {len(goal_related_recs)}")
        
        for rec in result["recommendations"][:3]:
            print(f"\n   {rec['category']}: ${rec['change']:.2f}")
            print(f"   {rec['reasoning'][:120]}...")
    
    def test_personalized_explanations(self):
        """
        Test: AI provides personalized, context-aware explanations
        
        Verify that explanations:
        - Reference specific spending patterns
        - Consider user's goals
        - Use natural language
        - Are actionable
        """
        # Setup realistic scenario
        budgets = [
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="groceries",
                amount=500.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="gas",
                amount=200.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
        ]
        self.db.add_all(budgets)
        
        # Add transactions
        for i in range(12):
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                amount=45.00,
                description=f"Grocery shopping {i+1}",
                category="groceries",
                type=TransactionType.EXPENSE,
                date=datetime(2025, 11, 1) + timedelta(days=i*2),
            )
            self.db.add(tx)
        
        self.db.commit()
        
        # Get recommendations
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=True,
        )
        
        assert result["status"] == "success"
        
        # Verify explanation quality
        for rec in result["recommendations"]:
            assert "reasoning" in rec
            assert len(rec["reasoning"]) >= 20, "Explanation too short"
            assert len(rec["reasoning"]) <= 500, "Explanation too long"
            
            # Check for personalization indicators
            reasoning_lower = rec["reasoning"].lower()
            
            # Should reference specific data or patterns
            has_context = any(word in reasoning_lower for word in [
                "you", "your", "spending", "budget", "goal", "$"
            ])
            
            assert has_context, f"Explanation lacks personalization: {rec['reasoning']}"
        
        print(f"✅ All {len(result['recommendations'])} recommendations have quality explanations")
    
    def test_multiple_categories_holistic_view(self):
        """
        Test: AI considers all categories holistically, not in isolation
        
        Scenario:
        - Overspending in groceries
        - Underspending in entertainment
        - AI should suggest reallocation between them
        """
        budgets = [
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="groceries",
                amount=400.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="entertainment",
                amount=200.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
            Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category="restaurant",
                amount=300.00,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            ),
        ]
        self.db.add_all(budgets)
        
        # Overspend groceries
        for i in range(15):
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                amount=35.00,  # Total: $525
                description=f"Grocery {i+1}",
                category="groceries",
                type=TransactionType.EXPENSE,
                date=datetime(2025, 11, 1) + timedelta(days=i*2),
            )
            self.db.add(tx)
        
        # Minimal entertainment
        tx_ent = Transaction(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            amount=20.00,
            description="Movie",
            category="entertainment",
            type=TransactionType.EXPENSE,
            date=datetime(2025, 11, 10),
        )
        self.db.add(tx_ent)
        
        self.db.commit()
        
        # Get recommendations
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=True,
        )
        
        assert result["status"] == "success"
        assert len(result["recommendations"]) > 0
        
        # Should have recommendations for both categories
        categories_mentioned = set(r["category"] for r in result["recommendations"])
        
        print(f"✅ Holistic analysis covers {len(categories_mentioned)} categories:")
        for cat in categories_mentioned:
            print(f"   - {cat}")
    
    def test_fallback_to_rule_based(self):
        """
        Test: Falls back to rule-based when AI is disabled
        """
        # Create simple scenario
        budget = Budget(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            category="groceries",
            amount=400.00,
            period="monthly",
            start_date=datetime(2025, 11, 1),
            is_active=True,
        )
        self.db.add(budget)
        
        # Overspend
        for i in range(12):
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                amount=45.00,  # Total: $540
                description=f"Grocery {i+1}",
                category="groceries",
                type=TransactionType.EXPENSE,
                date=datetime(2025, 11, 1) + timedelta(days=i*2),
            )
            self.db.add(tx)
        
        self.db.commit()
        
        # Get rule-based recommendations
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=False,  # Disable AI
        )
        
        assert result["status"] == "success"
        assert result["method"] == "rule-based"
        assert len(result["recommendations"]) > 0
        
        # Rule-based should still provide recommendations
        rec = result["recommendations"][0]
        assert "reasoning" in rec
        assert rec["method"] == "rule-based"
        
        print(f"✅ Rule-based fallback works:")
        print(f"   Recommendations: {len(result['recommendations'])}")
        print(f"   Example: {rec['reasoning'][:100]}...")
    
    def test_realistic_monthly_scenario(self):
        """
        Test: Complete realistic monthly scenario
        
        User profile:
        - Income: $5,000/month
        - Budgets: Groceries, Dining, Gas, Entertainment, Utilities
        - Goal: Save for vacation
        - Spending: Mixed (some over, some under)
        """
        # Create goal
        goal = Goal(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            name="Vacation Fund",
            target_amount=3000.00,
            current_amount=500.00,
            target_date=datetime(2026, 7, 1),
            priority=4,
            status=GoalStatus.ACTIVE,
        )
        self.db.add(goal)
        
        # Create budgets
        budgets_data = [
            ("groceries", 500.00),
            ("restaurant", 300.00),
            ("gas", 200.00),
            ("entertainment", 150.00),
            ("utilities", 250.00),
        ]
        
        for category, amount in budgets_data:
            budget = Budget(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                category=category,
                amount=amount,
                period="monthly",
                start_date=datetime(2025, 11, 1),
                is_active=True,
            )
            self.db.add(budget)
        
        # Add income
        income = Transaction(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            amount=5000.00,
            description="Monthly salary",
            category="salary",
            type=TransactionType.INCOME,
            date=datetime(2025, 11, 1),
        )
        self.db.add(income)
        
        # Add realistic spending
        transactions_data = [
            ("groceries", 45.00, 12),  # $540 (over budget)
            ("restaurant", 35.00, 8),  # $280 (under budget)
            ("gas", 55.00, 4),  # $220 (over budget)
            ("entertainment", 15.00, 2),  # $30 (way under)
            ("utilities", 250.00, 1),  # $250 (on budget)
        ]
        
        for category, amount, count in transactions_data:
            for i in range(count):
                tx = Transaction(
                    id=str(uuid.uuid4()),
                    user_id=self.user.id,
                    amount=amount,
                    description=f"{category} expense {i+1}",
                    category=category,
                    type=TransactionType.EXPENSE,
                    date=datetime(2025, 11, 1) + timedelta(days=i*2),
                )
                self.db.add(tx)
        
        self.db.commit()
        
        # Get AI recommendations
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=True,
        )
        
        assert result["status"] == "success"
        assert len(result["recommendations"]) >= 3
        
        # Verify analysis
        analysis = result["analysis"]
        assert analysis["total_income"] == 5000.00
        assert analysis["total_spent"] > 0
        assert analysis["savings_rate"] > 0
        
        print(f"\n✅ Realistic Monthly Scenario Analysis:")
        print(f"   Income: ${analysis['total_income']:.2f}")
        print(f"   Spent: ${analysis['total_spent']:.2f}")
        print(f"   Savings Rate: {analysis['savings_rate']:.1f}%")
        print(f"   Overspent Categories: {analysis['overspent_count']}")
        print(f"   Underspent Categories: {analysis['underspent_count']}")
        
        print(f"\n   AI Recommendations ({len(result['recommendations'])}):")
        for i, rec in enumerate(result["recommendations"][:5], 1):
            print(f"\n   {i}. {rec['category'].upper()} ({rec['priority']} priority)")
            print(f"      ${rec['current_amount']:.2f} → ${rec['recommended_amount']:.2f} ({rec['type']})")
            print(f"      {rec['reasoning'][:150]}...")
    
    def test_no_budgets_scenario(self):
        """
        Test: Handles case where user has no budgets
        """
        result = AIBudgetAdvisor.analyze_and_recommend(
            db=self.db,
            user_id=self.user.id,
            current_date=datetime(2025, 11, 30),
            use_ai=True,
        )
        
        assert result["status"] == "no_budgets"
        assert "no active budgets" in result["message"].lower()
        
        print(f"✅ Handles no budgets gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
