#!/usr/bin/env python3
"""
Test script to verify database connection and basic data fetching
"""

import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

def test_database_connection():
    """Test basic database connection and data fetching"""
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ Error: DATABASE_URL must be set in .env file")
        print("   Copy .env.example to .env and fill in your credentials")
        return False
    
    try:
        # Create database connection
        print("🔗 Testing database connection...")
        conn = psycopg2.connect(database_url)
        
        # Test connection by fetching a small sample from each table
        print("📊 Testing cads_works table...")
        works_query = "SELECT id, title, researcher_id FROM cads_works LIMIT 5"
        works_df = pd.read_sql(works_query, conn)
        print(f"   ✅ Successfully fetched {len(works_df)} sample works")
        
        print("👥 Testing cads_researchers table...")
        researchers_query = "SELECT id, full_name, department FROM cads_researchers LIMIT 5"
        researchers_df = pd.read_sql(researchers_query, conn)
        print(f"   ✅ Successfully fetched {len(researchers_df)} sample researchers")
        
        # Get total counts
        print("📈 Getting total record counts...")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cads_works")
        total_works = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cads_researchers")
        total_researchers = cursor.fetchone()[0]
        
        print(f"   📚 Total works: {total_works}")
        print(f"   👥 Total researchers: {total_researchers}")
        
        cursor.close()
        conn.close()
        
        print("✅ Database connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_embeddings_format():
    """Test parsing of pgvector embeddings format"""
    
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ Skipping embeddings test - no DATABASE_URL")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        
        print("🧮 Testing embeddings format...")
        # Fetch a few records with embeddings
        query = "SELECT id, title, embedding FROM cads_works WHERE embedding IS NOT NULL LIMIT 3"
        df = pd.read_sql(query, conn)
        
        for _, record in df.iterrows():
            if record['embedding']:
                embedding_str = str(record['embedding'])
                print(f"   📄 {record['title'][:50]}...")
                print(f"   🔢 Embedding format: {embedding_str[:50]}...")
                
                # Test parsing
                if embedding_str.startswith('[') and embedding_str.endswith(']'):
                    values = embedding_str.strip('[]').split(',')
                    print(f"   ✅ Parsed {len(values)} embedding dimensions")
                else:
                    print(f"   ⚠️  Unexpected embedding format")
                break
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 CADS Research Visualization - Connection Test")
    print("=" * 50)
    
    # Test database connection
    connection_ok = test_database_connection()
    
    if connection_ok:
        # Test embeddings format
        test_embeddings_format()
    
    print("\n" + "=" * 50)
    if connection_ok:
        print("✅ All tests passed! Ready to run process_data.py")
    else:
        print("❌ Setup incomplete. Please check your .env configuration")