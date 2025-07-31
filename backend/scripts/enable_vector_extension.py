#!/usr/bin/env python3
"""
Script to enable the vector extension in Supabase database.
This script should be run once to enable vector operations for embeddings.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.database_manager import DatabaseManager


def enable_vector_extension():
    """
    Enable the vector extension in the Supabase database.
    This is required for storing and querying vector embeddings.
    """
    print("=== Enabling Vector Extension in Supabase ===\n")
    
    try:
        # Initialize DatabaseManager
        db_manager = DatabaseManager()
        db_manager.connect()
        print("✓ Connected to database successfully\n")
        
        # Check if extension is already enabled
        print("Checking current vector extension status...")
        extension_check = db_manager.execute_query(
            "SELECT * FROM pg_extension WHERE extname = 'vector';",
            fetch=True
        )
        
        if extension_check:
            print("✓ Vector extension is already enabled")
            print(f"  Extension details: {extension_check[0]}")
        else:
            print("Vector extension not found. Attempting to enable...")
            
            # Enable the vector extension
            try:
                db_manager.execute_query("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✓ Vector extension enabled successfully!")
                
                # Verify it was enabled
                verification = db_manager.execute_query(
                    "SELECT * FROM pg_extension WHERE extname = 'vector';",
                    fetch=True
                )
                
                if verification:
                    print(f"✓ Verification successful: {verification[0]}")
                else:
                    print("⚠ Extension may not have been enabled properly")
                    
            except Exception as e:
                print(f"✗ Failed to enable vector extension: {e}")
                print("\nNote: You may need to enable the vector extension manually in Supabase:")
                print("1. Go to your Supabase project dashboard")
                print("2. Navigate to Database > Extensions")
                print("3. Search for 'vector' and enable it")
                print("4. Or run this SQL command in the SQL editor:")
                print("   CREATE EXTENSION IF NOT EXISTS vector;")
                return False
        
        # Test vector operations
        print("\nTesting vector operations...")
        vector_test_results = db_manager.test_vector_extension()
        
        if vector_test_results['success']:
            print("✓ Vector extension is working correctly!")
            print(f"  Test duration: {vector_test_results['duration']:.2f} seconds")
        else:
            print(f"✗ Vector extension test failed: {vector_test_results['error']}")
            return False
        
        print("\n=== Vector Extension Setup Complete ===")
        return True
        
    except Exception as e:
        print(f"Setup failed with error: {e}")
        return False
        
    finally:
        try:
            db_manager.close()
            print("Database connections closed.")
        except:
            pass


if __name__ == "__main__":
    success = enable_vector_extension()
    exit(0 if success else 1)