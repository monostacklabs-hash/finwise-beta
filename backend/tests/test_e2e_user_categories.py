"""
E2E Test: User-Specific Category Collections
Tests personalized category system with AI learning
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.models import User, Transaction, Category, TransactionType
from app.database.session import get_db, engine
from app.agents.financial_agent import get_financial_agent
from app.services.category_manager import CategoryManager
from app.services.ai_transaction_categorizer import AITransactionCategorizer


class TestUserCategoriesE2E:
    """E2E tests for user-specific category collections"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and database"""
        from app.database.models import Base
        
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())
        
        self.user = User(
            id=str(uuid.uuid4()),
            email=f"test_categories_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            name="Category Test User",
            timezone="America/Los_Angeles",
            currency="USD",
            country="USA",
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        
        # Seed default categories
        CategoryManager.seed_default_categories(self.user.id, self.db)
        
        self.agent = get_financial_agent()
        
        yield
        
        self.db.query(Transaction).filter(Transaction.user_id == self.user.id).delete()
        self.db.query(Category).filter(Category.user_id == self.user.id).delete()
        self.db.query(User).filter(User.id == self.user.id).delete()
        self.db.commit()
        self.db.close()
    
    def test_default_categories_seeded(self):
        """
        Test: New user gets default categories seeded
        """
        categories = CategoryManager.get_user_categories(self.user.id, self.db)
        
        assert len(categories) > 0, "User should have default categories"
        assert len(categories) >= 30, f"Expected at least 30 categories, got {len(categories)}"
        
        # Check for key categories
        category_names = [c["name"] for c in categories]
        assert "groceries" in category_names
        assert "restaurant" in category_names
        assert "gas" in category_names
        assert "streaming" in category_names
        assert "rent" in category_names
        
        print(f"✅ User has {len(categories)} default categories")
        print(f"   Sample: {', '.join(category_names[:10])}")
    
    def test_ai_uses_user_categories(self):
        """
        Test: AI categorizer uses user's specific categories
        """
        # Add a transaction
        result = self.agent.sync_invoke(
            message="I spent $85 at Whole Foods",
            db=self.db,
            user_id=self.user.id,
            user_data={
                "timezone": self.user.timezone,
                "currency": self.user.currency,
                "country": self.user.country,
                "name": self.user.name,
            },
        )
        
        assert result["success"]
        
        # Check transaction was categorized
        transaction = (
            self.db.query(Transaction)
            .filter(Transaction.user_id == self.user.id)
            .first()
        )
        
        assert transaction is not None
        assert transaction.category is not None
        
        # Check category exists in user's collection
        user_categories = CategoryManager.get_category_names(self.user.id, self.db)
        assert transaction.category in user_categories, \
            f"Category '{transaction.category}' should be in user's categories"
        
        print(f"✅ Transaction categorized as: {transaction.category}")
        print(f"   User has {len(user_categories)} categories")
    
    def test_category_usage_count_increments(self):
        """
        Test: Category usage count increments when used
        """
        # Get initial total usage across all categories
        categories_before = CategoryManager.get_user_categories(self.user.id, self.db)
        total_usage_before = sum(c["usage_count"] for c in categories_before)
        
        # Add multiple grocery transactions
        for i in range(3):
            result = self.agent.sync_invoke(
                message=f"Bought groceries for ${50 + i*10}",
                db=self.db,
                user_id=self.user.id,
                user_data={
                    "timezone": self.user.timezone,
                    "currency": self.user.currency,
                    "country": self.user.country,
                    "name": self.user.name,
                },
            )
            assert result["success"]
        
        # Check that total usage has increased
        categories_after = CategoryManager.get_user_categories(self.user.id, self.db)
        total_usage_after = sum(c["usage_count"] for c in categories_after)
        used_categories = [c for c in categories_after if c["usage_count"] > 0]
        
        assert total_usage_after > total_usage_before, \
            f"Total usage should increase: {total_usage_before} → {total_usage_after}"
        assert len(used_categories) > 0, "At least one category should have been used"
        
        print(f"✅ Total usage count: {total_usage_before} → {total_usage_after}")
        print(f"   {len(used_categories)} categories have been used:")
        for cat in used_categories[:5]:
            print(f"   - {cat['display_name']}: {cat['usage_count']} uses")
    
    def test_ai_suggests_new_category(self):
        """
        Test: AI can suggest and create new categories
        """
        # Use a very specific transaction that doesn't fit existing categories
        result = self.agent.sync_invoke(
            message="I spent $45 on cryptocurrency trading fees",
            db=self.db,
            user_id=self.user.id,
            user_data={
                "timezone": self.user.timezone,
                "currency": self.user.currency,
                "country": self.user.country,
                "name": self.user.name,
            },
        )
        
        assert result["success"]
        
        # Check transaction
        transaction = (
            self.db.query(Transaction)
            .filter(Transaction.user_id == self.user.id)
            .first()
        )
        
        assert transaction is not None
        print(f"✅ Transaction categorized as: {transaction.category}")
        
        # Check if category exists (either existing or newly created)
        category = self.db.query(Category).filter(
            Category.user_id == self.user.id,
            Category.name == transaction.category
        ).first()
        
        assert category is not None, f"Category '{transaction.category}' should exist"
        
        if category.ai_suggested:
            print(f"   ✅ AI suggested new category: {category.display_name}")
        else:
            print(f"   Used existing category: {category.display_name}")
    
    def test_user_can_add_custom_category(self):
        """
        Test: User can manually add custom categories
        """
        # Add a custom category
        new_cat = CategoryManager.add_category(
            user_id=self.user.id,
            name="side_hustle",
            display_name="Side Hustle Income",
            db=self.db,
            parent_category="income",
            icon="briefcase",
            color="#00BCD4",
            ai_suggested=False,
        )
        
        assert new_cat is not None
        assert new_cat["name"] == "side_hustle"
        assert new_cat["display_name"] == "Side Hustle Income"
        
        print(f"✅ Created custom category: {new_cat['display_name']}")
        
        # Verify it's in user's categories
        user_categories = CategoryManager.get_category_names(self.user.id, self.db)
        assert "side_hustle" in user_categories
        
        # Use the custom category
        result = self.agent.sync_invoke(
            message="I earned $500 from my side hustle",
            db=self.db,
            user_id=self.user.id,
            user_data={
                "timezone": self.user.timezone,
                "currency": self.user.currency,
                "country": self.user.country,
                "name": self.user.name,
            },
        )
        
        assert result["success"]
        
        transaction = (
            self.db.query(Transaction)
            .filter(Transaction.user_id == self.user.id)
            .order_by(Transaction.created_at.desc())
            .first()
        )
        
        # AI might or might not use the custom category
        print(f"   Transaction categorized as: {transaction.category}")
    
    def test_categories_isolated_per_user(self):
        """
        Test: Categories are isolated per user
        """
        # Create second user
        user2 = User(
            id=str(uuid.uuid4()),
            email=f"test_categories_2_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            name="Category Test User 2",
            timezone="America/New_York",
            currency="USD",
            country="USA",
        )
        self.db.add(user2)
        self.db.commit()
        
        # Seed categories for user2
        CategoryManager.seed_default_categories(user2.id, self.db)
        
        # Add custom category for user1
        CategoryManager.add_category(
            user_id=self.user.id,
            name="user1_custom",
            display_name="User 1 Custom",
            db=self.db,
        )
        
        # Add different custom category for user2
        CategoryManager.add_category(
            user_id=user2.id,
            name="user2_custom",
            display_name="User 2 Custom",
            db=self.db,
        )
        
        # Get categories for each user
        user1_cats = CategoryManager.get_category_names(self.user.id, self.db)
        user2_cats = CategoryManager.get_category_names(user2.id, self.db)
        
        # Verify isolation
        assert "user1_custom" in user1_cats
        assert "user1_custom" not in user2_cats
        assert "user2_custom" in user2_cats
        assert "user2_custom" not in user1_cats
        
        print(f"✅ User 1 has {len(user1_cats)} categories")
        print(f"✅ User 2 has {len(user2_cats)} categories")
        print(f"   Categories are properly isolated")
        
        # Cleanup user2
        self.db.query(Category).filter(Category.user_id == user2.id).delete()
        self.db.query(User).filter(User.id == user2.id).delete()
        self.db.commit()
    
    def test_most_used_categories_prioritized(self):
        """
        Test: Most used categories appear first in AI prompts
        """
        # Add multiple transactions in different categories
        transactions = [
            ("Groceries at Safeway $50", 5),  # Use groceries 5 times
            ("Gas at Shell $40", 3),  # Use gas 3 times
            ("Netflix $15", 1),  # Use streaming 1 time
        ]
        
        for message, count in transactions:
            for _ in range(count):
                result = self.agent.sync_invoke(
                    message=message,
                    db=self.db,
                    user_id=self.user.id,
                    user_data={
                        "timezone": self.user.timezone,
                        "currency": self.user.currency,
                        "country": self.user.country,
                        "name": self.user.name,
                    },
                )
                assert result["success"]
        
        # Get categories sorted by usage
        categories = CategoryManager.get_user_categories(self.user.id, self.db)
        used_cats = [c for c in categories if c["usage_count"] > 0]
        
        # Verify they're sorted by usage
        for i in range(len(used_cats) - 1):
            assert used_cats[i]["usage_count"] >= used_cats[i+1]["usage_count"], \
                "Categories should be sorted by usage count"
        
        print(f"✅ Top used categories:")
        for cat in used_cats[:5]:
            print(f"   - {cat['display_name']}: {cat['usage_count']} uses")
    
    def test_direct_categorizer_with_user_categories(self):
        """
        Test: Direct AI categorizer call uses user's categories
        """
        # Get user's categories
        user_cats = CategoryManager.get_category_names(self.user.id, self.db)
        
        # Categorize a transaction
        result = AITransactionCategorizer.categorize(
            description="Whole Foods Market",
            amount=75.50,
            trans_type="expense",
            user_id=self.user.id,
            db=self.db,
            use_ai=True,
        )
        
        assert result["category"] in user_cats, \
            f"Category '{result['category']}' should be in user's categories"
        
        print(f"✅ Categorized 'Whole Foods' as: {result['category']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Method: {result['method']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
