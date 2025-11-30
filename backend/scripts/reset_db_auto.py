#!/usr/bin/env python3
"""
Automated database reset script for Docker/CI environments
Drops all tables and recreates them WITHOUT confirmation
USE WITH CAUTION - Only for development/staging
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.database.session import engine
from app.database.models import Base

def main():
    """Drop and recreate all tables automatically"""
    print("🔧 Resetting database (automated)...")
    print(f"📊 Database URL: {engine.url}")
    
    try:
        # Drop all tables
        print("🗑️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        
        # Recreate all tables
        print("🔨 Creating all tables...")
        Base.metadata.create_all(bind=engine)
        
        print("\n✅ Database reset successfully!")
        
        # List created tables
        print("\n📋 Created tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
            
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
