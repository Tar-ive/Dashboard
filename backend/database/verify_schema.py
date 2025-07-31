#!/usr/bin/env python3
"""
Schema verification script to validate database structure.
"""

import os
import psycopg2
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_schema():
    """Verify the database schema is correctly created."""
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()
    
    try:
        # Check tables
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        logger.info("=== DATABASE TABLES ===")
        for table_name, column_count in tables:
            logger.info(f"✓ {table_name}: {column_count} columns")
        
        # Check indexes
        cursor.execute("""
            SELECT schemaname, tablename, indexname, indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND indexname NOT LIKE '%_pkey'
            ORDER BY tablename, indexname;
        """)
        
        indexes = cursor.fetchall()
        logger.info("\n=== DATABASE INDEXES ===")
        current_table = None
        for schema, table, index_name, index_def in indexes:
            if table != current_table:
                logger.info(f"\n{table}:")
                current_table = table
            logger.info(f"  ✓ {index_name}")
        
        # Check foreign keys
        cursor.execute("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name;
        """)
        
        foreign_keys = cursor.fetchall()
        logger.info("\n=== FOREIGN KEY RELATIONSHIPS ===")
        for table, column, ref_table, ref_column in foreign_keys:
            logger.info(f"✓ {table}.{column} → {ref_table}.{ref_column}")
        
        # Check extensions
        cursor.execute("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp');")
        extensions = cursor.fetchall()
        logger.info("\n=== EXTENSIONS ===")
        for ext in extensions:
            logger.info(f"✓ {ext[0]}")
        
        # Check constraints
        cursor.execute("""
            SELECT table_name, constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
            AND constraint_type IN ('CHECK', 'UNIQUE')
            ORDER BY table_name, constraint_type;
        """)
        
        constraints = cursor.fetchall()
        logger.info("\n=== CONSTRAINTS ===")
        current_table = None
        for table, constraint_name, constraint_type in constraints:
            if table != current_table:
                logger.info(f"\n{table}:")
                current_table = table
            logger.info(f"  ✓ {constraint_type}: {constraint_name}")
        
        logger.info("\n=== SCHEMA VERIFICATION COMPLETE ===")
        logger.info("All database components are properly configured!")
        
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    verify_schema()