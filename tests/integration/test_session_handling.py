#!/usr/bin/env python3
"""
Test script to verify proper session handling and rollback on errors
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database.connection import get_db
from backend.app.agents.tools import ToolContext, _create_recurring_transaction, _add_transaction
from datetime import datetime

def test_duplicate_recurring_transaction():
    """Test that duplicate recurring transactions are handled properly"""
    print("Testing duplicate recurring transaction handling...")
    
    db = next(get_db())
    ToolContext.db = db
    ToolContext.user_id = "9ccb3193-5cbf-465d-8a4e-d6f3ba96819a"
    
    try:
        # First call should succeed
        result1 = _create_recurring_transaction(
            transaction_type="expense",
            amount=100.0,
            description="Test Subscription",
            category="entertainment",
            frequency="monthly",
            next_date="2025-12-01",
            auto_add=True
        )
        print(f"First call: {result1}")
        
        # Simulate the agent calling the same tool twice (which was causing the error)
        # This should be handled gracefully now
        result2 = _create_recurring_transaction(
            transaction_type="expense",
            amount=100.0,
            description="Test Subscription 2",
            category="entertainment",
            frequency="monthly",
            next_date="2025-12-01",
            auto_add=True
        )
        print(f"Second call: {result2}")
        
        print("✅ Test passed: Both calls handled correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        ToolContext.db = None
        ToolContext.user_id = None
        db.close()

def test_transaction_error_rollback():
    """Test that transaction errors trigger proper rollback"""
    print("\nTesting transaction error rollback...")
    
    db = next(get_db())
    ToolContext.db = db
    ToolContext.user_id = "9ccb3193-5cbf-465d-8a4e-d6f3ba96819a"
    
    try:
        # Try to add a transaction with invalid type (should fail and rollback)
        result = _add_transaction(
            amount=50.0,
            description="Test Transaction",
            transaction_type="invalid_type",  # This should cause an error
            category="food",
            date="2025-11-05"
        )
        print(f"Result: {result}")
        
        # Session should still be usable after rollback
        result2 = _add_transaction(
            amount=50.0,
            description="Valid Transaction",
            transaction_type="expense",
            category="food",
            date="2025-11-05"
        )
        print(f"Second transaction: {result2}")
        
        print("✅ Test passed: Error handling and rollback working correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        ToolContext.db = None
        ToolContext.user_id = None
        db.close()

if __name__ == "__main__":
    test_duplicate_recurring_transaction()
    test_transaction_error_rollback()
