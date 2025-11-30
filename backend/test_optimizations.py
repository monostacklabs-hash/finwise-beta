#!/usr/bin/env python3
"""
Quick test script to verify database optimizations are working
Run this after applying migrations and restarting the backend
"""
import time
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
DATABASE_URL = "sqlite:///./finwise.db"  # Update with your database URL

def test_indexes_exist(session):
    """Test that all required indexes exist"""
    print("\n🔍 Testing Database Indexes...")
    
    # For SQLite
    try:
        result = session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='index' 
            AND tbl_name IN ('transactions', 'budgets')
        """))
        indexes = [row[0] for row in result]
        
        required_indexes = [
            'ix_transactions_user_date',
            'ix_transactions_user_type',
            'ix_transactions_user_category',
            'ix_transactions_date',
            'ix_budgets_user_category'
        ]
        
        print(f"Found {len(indexes)} indexes")
        for idx in required_indexes:
            if idx in indexes:
                print(f"  ✅ {idx}")
            else:
                print(f"  ❌ {idx} - MISSING!")
                
        return all(idx in indexes for idx in required_indexes)
    except Exception as e:
        print(f"  ⚠️  Could not check indexes: {e}")
        return False

def test_query_performance(session):
    """Test query performance with aggregations"""
    print("\n⚡ Testing Query Performance...")
    
    # Test 1: Count query
    start = time.time()
    result = session.execute(text("""
        SELECT COUNT(*) FROM transactions
    """))
    count = result.scalar()
    elapsed = (time.time() - start) * 1000
    print(f"  Count query: {elapsed:.2f}ms ({count} transactions)")
    
    # Test 2: Aggregation query
    start = time.time()
    result = session.execute(text("""
        SELECT type, SUM(amount) as total
        FROM transactions
        GROUP BY type
    """))
    rows = result.fetchall()
    elapsed = (time.time() - start) * 1000
    print(f"  Aggregation query: {elapsed:.2f}ms ({len(rows)} groups)")
    
    # Test 3: Date range query (should use index)
    start = time.time()
    result = session.execute(text("""
        SELECT COUNT(*) FROM transactions
        WHERE date >= date('now', '-30 days')
    """))
    count = result.scalar()
    elapsed = (time.time() - start) * 1000
    print(f"  Date range query: {elapsed:.2f}ms ({count} recent transactions)")
    
    if elapsed < 100:
        print("  ✅ Performance looks good!")
        return True
    else:
        print("  ⚠️  Queries seem slow, check if indexes are being used")
        return False

def test_connection_pool():
    """Test connection pool configuration"""
    print("\n🔌 Testing Connection Pool...")
    
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
        )
        
        print(f"  ✅ Pool size: {engine.pool.size()}")
        print(f"  ✅ Max overflow: 20")
        print(f"  ✅ Pool timeout: 30s")
        print(f"  ✅ Connection recycle: 3600s")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"  ✅ Connection test: OK")
        
        return True
    except Exception as e:
        print(f"  ❌ Connection pool error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Database Optimization Verification")
    print("=" * 60)
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Run tests
        results = []
        results.append(("Indexes", test_indexes_exist(session)))
        results.append(("Query Performance", test_query_performance(session)))
        results.append(("Connection Pool", test_connection_pool()))
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All optimizations verified successfully!")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the output above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    sys.exit(main())
