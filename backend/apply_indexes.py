#!/usr/bin/env python3
"""
Apply database indexes using SQLAlchemy
This works with any database (PostgreSQL, SQLite, MySQL, etc.)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import engine
from app.database.models import Base

def apply_indexes():
    """Create all tables and indexes defined in models"""
    print("=" * 60)
    print("Applying Database Indexes")
    print("=" * 60)
    
    try:
        print("\n📊 Creating tables and indexes...")
        
        # This will create all tables and indexes defined in models.py
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables and indexes created successfully!")
        
        # Verify indexes were created
        print("\n🔍 Verifying indexes...")
        
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        # Check transactions table indexes
        tx_indexes = inspector.get_indexes('transactions')
        print(f"\nTransactions table indexes ({len(tx_indexes)}):")
        for idx in tx_indexes:
            print(f"  ✅ {idx['name']}")
        
        # Check budgets table indexes
        budget_indexes = inspector.get_indexes('budgets')
        print(f"\nBudgets table indexes ({len(budget_indexes)}):")
        for idx in budget_indexes:
            print(f"  ✅ {idx['name']}")
        
        print("\n" + "=" * 60)
        print("✅ Database optimization complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart your backend service")
        print("2. Run: python test_optimizations.py")
        print("3. Test API endpoints for improved performance")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error applying indexes: {e}")
        print("\nTroubleshooting:")
        print("1. Check your DATABASE_URL in .env or config.py")
        print("2. Ensure database server is running")
        print("3. Verify database credentials")
        return 1

if __name__ == "__main__":
    sys.exit(apply_indexes())
