#!/usr/bin/env python3
"""
Clear all data from the database tables for a fresh test.
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database.database_manager import DatabaseManager

# Load environment variables
load_dotenv()


def clear_database():
    """Clear all data from the database tables."""
    db_manager = DatabaseManager()
    db_manager.connect()
    
    try:
        print("Clearing database tables...")
        
        # Clear tables in reverse dependency order
        tables = ['topics', 'researcher_grants', 'works', 'researchers', 'institutions']
        
        for table in tables:
            result = db_manager.execute_query(f"DELETE FROM {table};")
            count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table};", fetch=True)
            print(f"  Cleared {table}: {count_result[0]['count']} rows remaining")
        
        print("✅ Database cleared successfully!")
        
    finally:
        db_manager.close()


if __name__ == "__main__":
    clear_database()