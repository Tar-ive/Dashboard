#!/usr/bin/env python3
"""
Database table creation script for Texas State University researcher data pipeline.
This script creates all necessary tables, indexes, and constraints.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return database_url

def execute_schema_file(connection, schema_file_path):
    """Execute SQL commands from schema file."""
    try:
        with open(schema_file_path, 'r') as file:
            schema_sql = file.read()
        
        cursor = connection.cursor()
        
        # Split the schema into individual statements, handling dollar-quoted strings
        statements = []
        current_statement = ""
        in_dollar_quote = False
        dollar_tag = ""
        
        lines = schema_sql.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
                
            # Check for dollar-quoted strings
            if '$' in line and not in_dollar_quote:
                # Look for dollar quote start
                import re
                dollar_match = re.search(r'\$(\w*)\$', line)
                if dollar_match:
                    dollar_tag = dollar_match.group(0)
                    in_dollar_quote = True
            elif in_dollar_quote and dollar_tag in line:
                in_dollar_quote = False
                dollar_tag = ""
            
            current_statement += line + '\n'
            
            # If we hit a semicolon and we're not in a dollar-quoted string, end the statement
            if line.endswith(';') and not in_dollar_quote:
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        for i, statement in enumerate(statements):
            try:
                logger.info(f"Executing statement {i+1}/{len(statements)}")
                cursor.execute(statement)
                connection.commit()
                logger.debug(f"Successfully executed: {statement[:100]}...")
            except Exception as e:
                logger.error(f"Error executing statement {i+1}: {e}")
                logger.error(f"Statement: {statement[:200]}...")
                connection.rollback()
                raise
        
        cursor.close()
        logger.info("Schema creation completed successfully")
        
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_file_path}")
        raise
    except Exception as e:
        logger.error(f"Error executing schema: {e}")
        raise

def verify_tables(connection):
    """Verify that all expected tables were created."""
    expected_tables = [
        'institutions',
        'researchers', 
        'works',
        'topics',
        'researcher_grants'
    ]
    
    cursor = connection.cursor()
    
    # Check if tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    
    existing_tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"Found tables: {existing_tables}")
    
    # Verify all expected tables exist
    missing_tables = set(expected_tables) - set(existing_tables)
    if missing_tables:
        logger.error(f"Missing tables: {missing_tables}")
        return False
    
    # Check if pg_vector extension is enabled
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    vector_extension = cursor.fetchone()
    if not vector_extension:
        logger.error("pg_vector extension not found")
        return False
    
    logger.info("pg_vector extension is enabled")
    
    # Verify table structures
    for table in expected_tables:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        logger.info(f"Table '{table}' has {len(columns)} columns")
        for col in columns:
            logger.debug(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
    
    cursor.close()
    return True

def test_table_relationships(connection):
    """Test foreign key relationships with sample data."""
    cursor = connection.cursor()
    
    try:
        # Test data insertion to verify relationships
        logger.info("Testing table relationships with sample data...")
        
        # Insert sample institution
        cursor.execute("""
            INSERT INTO institutions (openalex_id, name, ror_id) 
            VALUES ('https://openalex.org/I12345', 'Texas State University', 'https://ror.org/02hpadn98')
            RETURNING id;
        """)
        institution_id = cursor.fetchone()[0]
        logger.info(f"Created sample institution with ID: {institution_id}")
        
        # Insert sample researcher
        cursor.execute("""
            INSERT INTO researchers (institution_id, openalex_id, full_name, h_index, department) 
            VALUES (%s, 'https://openalex.org/A67890', 'Dr. Jane Smith', 25, 'Computer Science')
            RETURNING id;
        """, (institution_id,))
        researcher_id = cursor.fetchone()[0]
        logger.info(f"Created sample researcher with ID: {researcher_id}")
        
        # Insert sample work with embedding
        sample_embedding = [0.1] * 384  # Sample 384-dimensional vector
        cursor.execute("""
            INSERT INTO works (researcher_id, openalex_id, title, abstract, keywords, publication_year, doi, citations, embedding) 
            VALUES (%s, 'https://openalex.org/W11111', 'Sample Research Paper', 'This is a sample abstract for testing purposes.', 
                    '["machine learning", "artificial intelligence", "research"]', 2023, '10.1000/sample', 15, %s)
            RETURNING id;
        """, (researcher_id, sample_embedding))
        work_id = cursor.fetchone()[0]
        logger.info(f"Created sample work with ID: {work_id}")
        
        # Insert sample topic
        cursor.execute("""
            INSERT INTO topics (work_id, name, type, score) 
            VALUES (%s, 'Computer Science', 'topic', 0.95);
        """, (work_id,))
        logger.info("Created sample topic")
        
        # Insert sample grant
        cursor.execute("""
            INSERT INTO researcher_grants (researcher_id, award_id, award_year, role, award_amount, award_title) 
            VALUES (%s, 'NSF-2023-001', 2023, 'Principal Investigator', 500000, 'AI Research Grant');
        """, (researcher_id,))
        logger.info("Created sample grant")
        
        connection.commit()
        
        # Test queries to verify relationships
        cursor.execute("""
            SELECT r.full_name, i.name, w.title, t.name as topic_name, rg.award_title
            FROM researchers r
            JOIN institutions i ON r.institution_id = i.id
            JOIN works w ON r.id = w.researcher_id
            JOIN topics t ON w.id = t.work_id
            JOIN researcher_grants rg ON r.id = rg.researcher_id;
        """)
        
        result = cursor.fetchone()
        if result:
            logger.info(f"Relationship test successful: {result}")
        else:
            logger.error("No data returned from relationship test")
            return False
        
        # Test vector similarity query
        cursor.execute("""
            SELECT title, embedding <-> %s::vector as distance
            FROM works 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s::vector
            LIMIT 1;
        """, (sample_embedding, sample_embedding))
        
        vector_result = cursor.fetchone()
        if vector_result:
            logger.info(f"Vector similarity test successful: {vector_result[0]}, distance: {vector_result[1]}")
        else:
            logger.error("Vector similarity test failed")
            return False
        
        # Clean up test data
        cursor.execute("DELETE FROM researcher_grants WHERE award_id = 'NSF-2023-001';")
        cursor.execute("DELETE FROM topics WHERE name = 'Computer Science' AND type = 'topic';")
        cursor.execute("DELETE FROM works WHERE openalex_id = 'https://openalex.org/W11111';")
        cursor.execute("DELETE FROM researchers WHERE openalex_id = 'https://openalex.org/A67890';")
        cursor.execute("DELETE FROM institutions WHERE openalex_id = 'https://openalex.org/I12345';")
        connection.commit()
        
        logger.info("Test data cleaned up successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error testing relationships: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def main():
    """Main function to create database tables."""
    try:
        # Load configuration
        database_url = load_environment()
        logger.info("Environment loaded successfully")
        
        # Connect to database
        connection = psycopg2.connect(database_url)
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("Connected to database successfully")
        
        # Get schema file path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_file = os.path.join(script_dir, 'schema.sql')
        
        # Execute schema creation
        execute_schema_file(connection, schema_file)
        
        # Verify tables were created
        if not verify_tables(connection):
            logger.error("Table verification failed")
            return False
        
        # Test relationships
        if not test_table_relationships(connection):
            logger.error("Relationship testing failed")
            return False
        
        logger.info("Database schema creation and testing completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)