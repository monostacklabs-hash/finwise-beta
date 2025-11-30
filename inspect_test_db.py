#!/usr/bin/env python3
"""
Script to inspect test database contents
Shows what data was actually written during tests
"""
import sqlite3
import sys
from datetime import datetime

def inspect_database(db_path):
    """Inspect and display database contents"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("="*80)
        print(f"📊 DATABASE: {db_path}")
        print("="*80)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("\n❌ No tables found in database")
            return
        
        print(f"\n📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Inspect each table
        for table in tables:
            table_name = table[0]
            print(f"\n{'='*80}")
            print(f"📊 TABLE: {table_name}")
            print(f"{'='*80}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Total rows: {count}")
            
            if count == 0:
                print("(empty)")
                continue
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            # Get all rows
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Display data
            print(f"\nColumns: {', '.join(col_names)}")
            print("-" * 80)
            
            for i, row in enumerate(rows, 1):
                print(f"\nRow {i}:")
                for col_name, value in zip(col_names, row):
                    # Format value for display
                    if value is None:
                        display_value = "NULL"
                    elif isinstance(value, str) and len(value) > 100:
                        display_value = value[:100] + "..."
                    else:
                        display_value = value
                    print(f"  {col_name}: {display_value}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ Database inspection complete")
        print("="*80)
        
    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
    except FileNotFoundError:
        print(f"❌ Database file not found: {db_path}")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default to test_intelligence.db
        db_path = "test_intelligence.db"
    
    print("\n🔍 Database Inspector")
    print(f"Inspecting: {db_path}\n")
    
    inspect_database(db_path)


if __name__ == "__main__":
    main()
