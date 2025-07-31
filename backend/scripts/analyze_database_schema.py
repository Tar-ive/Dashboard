#!/usr/bin/env python3
"""
Analyze and document the complete database schema and data.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

def connect_database():
    """Connect to database using IPv4 pooler."""
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")
    
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        connect_timeout=30,
        sslmode='require',
        cursor_factory=RealDictCursor
    )

def analyze_database():
    """Analyze the complete database schema and data."""
    conn = connect_database()
    
    try:
        with conn.cursor() as cursor:
            print("🔍 COMPREHENSIVE DATABASE ANALYSIS")
            print("="*80)
            
            # Get all tables
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            print(f"\n📋 DATABASE TABLES ({len(tables)} total):")
            for table in tables:
                print(f"   {table['table_name']} ({table['table_type']})")
            
            # Analyze each table in detail
            for table in tables:
                if table['table_type'] == 'BASE TABLE':
                    analyze_table(cursor, table['table_name'])
            
            # Analyze relationships
            print("\n🔗 TABLE RELATIONSHIPS:")
            cursor.execute("""
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.column_name;
            """)
            
            relationships = cursor.fetchall()
            for rel in relationships:
                print(f"   {rel['table_name']}.{rel['column_name']} -> {rel['foreign_table_name']}.{rel['foreign_column_name']}")
            
    finally:
        conn.close()

def analyze_table(cursor, table_name):
    """Analyze a specific table in detail."""
    print(f"\n📊 TABLE: {table_name.upper()}")
    print("-" * 60)
    
    # Get column information
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = cursor.fetchall()
    
    print("Columns:")
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
        length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
        print(f"   {col['column_name']}: {col['data_type']}{length} {nullable}{default}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
    count = cursor.fetchone()['count']
    print(f"Row Count: {count:,}")
    
    # Get sample data for key tables
    if table_name in ['institutions', 'researchers', 'works', 'topics', 'cads_researchers', 'cads_works', 'cads_topics']:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        samples = cursor.fetchall()
        
        if samples:
            print("Sample Data:")
            for i, sample in enumerate(samples, 1):
                print(f"   Sample {i}:")
                for key, value in sample.items():
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"      {key}: {value}")

if __name__ == "__main__":
    analyze_database()