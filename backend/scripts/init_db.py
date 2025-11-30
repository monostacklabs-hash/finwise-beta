#!/usr/bin/env python3
"""
Database initialization script
Run this to create all tables from scratch
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.database.session import init_db, engine
from app.database.models import Base

def main():
    """Initialize database tables"""
    print("🔧 Initializing database...")
    print(f"📊 Database URL: {engine.url}")
    
    try:
        # Create all tables
        init_db()
        print("✅ Database tables created successfully!")
        
        # List created tables
        print("\n📋 Created tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
