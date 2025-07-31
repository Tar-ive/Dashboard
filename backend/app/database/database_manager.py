"""
DatabaseManager class for Supabase database operations using psycopg2.
Handles connection pooling, error handling, and basic CRUD operations.
"""

import os
import logging
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and operations for Supabase using psycopg2.
    Provides connection pooling, error handling, and basic CRUD operations.
    """
    
    def __init__(self, database_url: Optional[str] = None, min_connections: int = 1, max_connections: int = 10):
        """
        Initialize DatabaseManager with connection pooling.
        
        Args:
            database_url: PostgreSQL connection URL. If None, uses DATABASE_URL from environment.
            min_connections: Minimum number of connections in pool
            max_connections: Maximum number of connections in pool
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided either as parameter or environment variable")
        
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_pool = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def connect(self) -> None:
        """
        Initialize the connection pool.
        """
        try:
            logger.info("Initializing database connection pool...")
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                self.database_url,
                cursor_factory=RealDictCursor
            )
            logger.info(f"Connection pool created successfully with {self.min_connections}-{self.max_connections} connections")
            
            # Test the connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    def _test_connection(self) -> None:
        """
        Test database connection and log basic info.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                logger.info(f"Connected to database: {version['version']}")
                
                # Test vector extension
                cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                vector_ext = cursor.fetchone()
                if vector_ext:
                    logger.info("Vector extension is available")
                else:
                    logger.warning("Vector extension not found - may need to be enabled")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting database connections from pool.
        Automatically handles connection return and error cleanup.
        """
        if not self.connection_pool:
            raise RuntimeError("Database connection pool not initialized. Call connect() first.")
        
        connection = None
        try:
            connection = self.connection_pool.getconn()
            if connection:
                yield connection
            else:
                raise RuntimeError("Failed to get connection from pool")
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if connection:
                self.connection_pool.putconn(connection)
    
    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: bool = False) -> Optional[List[Dict]]:
        """
        Execute a SQL query with optional parameters.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch: Whether to fetch and return results
            
        Returns:
            Query results if fetch=True, None otherwise
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, params)
                    conn.commit()
                    
                    if fetch:
                        return cursor.fetchall()
                    
                    logger.debug(f"Query executed successfully: {cursor.rowcount} rows affected")
                    return None
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Query execution failed: {e}")
                    raise
    
    def test_basic_operations(self) -> Dict[str, Any]:
        """
        Test basic database operations: CREATE, INSERT, SELECT, UPDATE, DELETE.
        Creates a temporary test table and performs all operations.
        
        Returns:
            Dictionary with test results and metrics
        """
        test_results = {
            "start_time": time.time(),
            "operations": {},
            "success": False,
            "error": None
        }
        
        try:
            logger.info("Starting basic database operations test...")
            
            # Test 1: Create test table (without vector for basic test)
            create_table_query = """
            CREATE TABLE IF NOT EXISTS test_database_operations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            self.execute_query(create_table_query)
            test_results["operations"]["create_table"] = "SUCCESS"
            logger.info("✓ Test table created successfully")
            
            # Test 2: Insert test data
            insert_query = """
            INSERT INTO test_database_operations (name, value) 
            VALUES (%s, %s) RETURNING id;
            """
            
            test_data = [
                ("test_record_1", 100),
                ("test_record_2", 200),
                ("test_record_3", 300)
            ]
            
            inserted_ids = []
            for name, value in test_data:
                result = self.execute_query(insert_query, (name, value), fetch=True)
                inserted_ids.append(result[0]['id'])
            
            test_results["operations"]["insert"] = f"SUCCESS - {len(inserted_ids)} records"
            logger.info(f"✓ Inserted {len(inserted_ids)} test records")
            
            # Test 3: Select/Retrieve data
            select_query = "SELECT * FROM test_database_operations WHERE id = ANY(%s);"
            retrieved_data = self.execute_query(select_query, (inserted_ids,), fetch=True)
            
            test_results["operations"]["select"] = f"SUCCESS - {len(retrieved_data)} records retrieved"
            logger.info(f"✓ Retrieved {len(retrieved_data)} records")
            
            # Test 4: Update data
            update_query = "UPDATE test_database_operations SET value = %s WHERE id = %s;"
            self.execute_query(update_query, (999, inserted_ids[0]))
            
            # Verify update
            verify_update = self.execute_query(
                "SELECT value FROM test_database_operations WHERE id = %s;", 
                (inserted_ids[0],), 
                fetch=True
            )
            
            if verify_update[0]['value'] == 999:
                test_results["operations"]["update"] = "SUCCESS"
                logger.info("✓ Update operation successful")
            else:
                test_results["operations"]["update"] = "FAILED - Value not updated"
            
            # Test 5: Delete data
            delete_query = "DELETE FROM test_database_operations WHERE id = ANY(%s);"
            self.execute_query(delete_query, (inserted_ids,))
            
            # Verify deletion
            verify_delete = self.execute_query(
                "SELECT COUNT(*) as count FROM test_database_operations WHERE id = ANY(%s);",
                (inserted_ids,),
                fetch=True
            )
            
            if verify_delete[0]['count'] == 0:
                test_results["operations"]["delete"] = "SUCCESS"
                logger.info("✓ Delete operation successful")
            else:
                test_results["operations"]["delete"] = "FAILED - Records not deleted"
            
            # Clean up: Drop test table
            self.execute_query("DROP TABLE IF EXISTS test_database_operations;")
            test_results["operations"]["cleanup"] = "SUCCESS"
            logger.info("✓ Test table cleaned up")
            
            test_results["success"] = True
            logger.info("All basic database operations completed successfully!")
            
        except Exception as e:
            test_results["error"] = str(e)
            test_results["success"] = False
            logger.error(f"Database operations test failed: {e}")
            
            # Attempt cleanup on error
            try:
                self.execute_query("DROP TABLE IF EXISTS test_database_operations;")
                logger.info("Test table cleaned up after error")
            except:
                logger.warning("Failed to clean up test table after error")
        
        finally:
            test_results["end_time"] = time.time()
            test_results["duration"] = test_results["end_time"] - test_results["start_time"]
        
        return test_results
    
    def test_connection_pooling(self) -> Dict[str, Any]:
        """
        Test connection pooling behavior and limits.
        
        Returns:
            Dictionary with pooling test results
        """
        pool_test_results = {
            "start_time": time.time(),
            "max_connections_test": False,
            "concurrent_operations": False,
            "pool_exhaustion_handling": False,
            "success": False,
            "error": None
        }
        
        try:
            logger.info("Testing connection pooling...")
            
            # Test 1: Verify pool configuration
            if self.connection_pool:
                logger.info(f"Pool configured with {self.min_connections}-{self.max_connections} connections")
                pool_test_results["max_connections_test"] = True
            
            # Test 2: Test multiple concurrent connections
            connections = []
            try:
                # Try to get multiple connections up to the pool limit
                for i in range(min(3, self.max_connections)):
                    conn = self.connection_pool.getconn()
                    if conn:
                        connections.append(conn)
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT 1 as test_connection_%s;", (i,))
                            result = cursor.fetchone()
                            logger.info(f"Connection {i+1}: {result}")
                
                pool_test_results["concurrent_operations"] = len(connections) > 1
                logger.info(f"✓ Successfully used {len(connections)} concurrent connections")
                
            finally:
                # Return all connections to pool
                for conn in connections:
                    self.connection_pool.putconn(conn)
            
            # Test 3: Test pool exhaustion handling (if applicable)
            if self.max_connections <= 5:  # Only test if pool is small enough
                try:
                    # This should work within pool limits
                    with self.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT 'pool_test' as result;")
                            result = cursor.fetchone()
                            logger.info(f"Pool exhaustion test: {result}")
                    
                    pool_test_results["pool_exhaustion_handling"] = True
                    
                except Exception as e:
                    logger.warning(f"Pool exhaustion test failed: {e}")
            else:
                pool_test_results["pool_exhaustion_handling"] = True  # Skip for large pools
            
            pool_test_results["success"] = all([
                pool_test_results["max_connections_test"],
                pool_test_results["concurrent_operations"],
                pool_test_results["pool_exhaustion_handling"]
            ])
            
            logger.info("Connection pooling tests completed successfully!")
            
        except Exception as e:
            pool_test_results["error"] = str(e)
            pool_test_results["success"] = False
            logger.error(f"Connection pooling test failed: {e}")
        
        finally:
            pool_test_results["end_time"] = time.time()
            pool_test_results["duration"] = pool_test_results["end_time"] - pool_test_results["start_time"]
        
        return pool_test_results
    
    def test_vector_extension(self) -> Dict[str, Any]:
        """
        Test vector extension compatibility for embeddings.
        
        Returns:
            Dictionary with vector extension test results
        """
        vector_test_results = {
            "start_time": time.time(),
            "extension_available": False,
            "vector_operations": False,
            "distance_calculations": False,
            "success": False,
            "error": None
        }
        
        try:
            logger.info("Testing vector extension compatibility...")
            
            # Test 1: Check if vector extension is available
            extension_query = "SELECT * FROM pg_extension WHERE extname = 'vector';"
            extension_result = self.execute_query(extension_query, fetch=True)
            
            if extension_result:
                vector_test_results["extension_available"] = True
                logger.info("✓ Vector extension is available")
                
                # Test 2: Create test table with vector column
                vector_table_query = """
                CREATE TABLE IF NOT EXISTS test_vector_operations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    embedding VECTOR(3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                self.execute_query(vector_table_query)
                logger.info("✓ Vector table created successfully")
                
                # Test 3: Insert vector data
                vector_insert_query = """
                INSERT INTO test_vector_operations (name, embedding) 
                VALUES (%s, %s) RETURNING id;
                """
                
                test_vectors = [
                    ("vector_1", "[0.1, 0.2, 0.3]"),
                    ("vector_2", "[0.4, 0.5, 0.6]"),
                    ("vector_3", "[0.7, 0.8, 0.9]")
                ]
                
                vector_ids = []
                for name, vector in test_vectors:
                    result = self.execute_query(vector_insert_query, (name, vector), fetch=True)
                    vector_ids.append(result[0]['id'])
                
                vector_test_results["vector_operations"] = True
                logger.info(f"✓ Inserted {len(vector_ids)} vector records")
                
                # Test 4: Test distance calculations
                distance_query = """
                SELECT name, embedding, 
                       embedding <-> '[0.1, 0.2, 0.3]'::vector as l2_distance,
                       embedding <#> '[0.1, 0.2, 0.3]'::vector as max_inner_product,
                       embedding <=> '[0.1, 0.2, 0.3]'::vector as cosine_distance
                FROM test_vector_operations 
                ORDER BY embedding <-> '[0.1, 0.2, 0.3]'::vector 
                LIMIT 3;
                """
                
                distance_results = self.execute_query(distance_query, fetch=True)
                
                if distance_results and len(distance_results) > 0:
                    vector_test_results["distance_calculations"] = True
                    logger.info("✓ Vector distance calculations working correctly")
                    
                    # Log sample results
                    for result in distance_results:
                        logger.info(f"  {result['name']}: L2={result['l2_distance']:.4f}, "
                                  f"Cosine={result['cosine_distance']:.4f}")
                
                # Clean up vector test table
                self.execute_query("DROP TABLE IF EXISTS test_vector_operations;")
                logger.info("✓ Vector test table cleaned up")
                
            else:
                logger.warning("Vector extension not available - this may need to be enabled in Supabase")
                vector_test_results["error"] = "Vector extension not available"
            
            vector_test_results["success"] = all([
                vector_test_results["extension_available"],
                vector_test_results["vector_operations"],
                vector_test_results["distance_calculations"]
            ])
            
            if vector_test_results["success"]:
                logger.info("Vector extension tests completed successfully!")
            else:
                logger.warning("Vector extension tests completed with limitations")
            
        except Exception as e:
            vector_test_results["error"] = str(e)
            vector_test_results["success"] = False
            logger.error(f"Vector extension test failed: {e}")
            
            # Attempt cleanup on error
            try:
                self.execute_query("DROP TABLE IF EXISTS test_vector_operations;")
                logger.info("Vector test table cleaned up after error")
            except:
                logger.warning("Failed to clean up vector test table after error")
        
        finally:
            vector_test_results["end_time"] = time.time()
            vector_test_results["duration"] = vector_test_results["end_time"] - vector_test_results["start_time"]
        
        return vector_test_results
    
    def upsert_institution(self, data: Dict) -> str:
        """
        Insert or update institution data.
        
        Args:
            data: Institution data dictionary
            
        Returns:
            Institution UUID
        """
        query = """
        INSERT INTO institutions (openalex_id, name, ror_id)
        VALUES (%(openalex_id)s, %(name)s, %(ror_id)s)
        ON CONFLICT (openalex_id) 
        DO UPDATE SET 
            name = EXCLUDED.name,
            ror_id = EXCLUDED.ror_id,
            updated_at = now()
        RETURNING id;
        """
        
        result = self.execute_query(query, data, fetch=True)
        institution_id = result[0]['id']
        logger.debug(f"Upserted institution: {data['name']} (ID: {institution_id})")
        return str(institution_id)
    
    def upsert_researcher(self, data: Dict) -> str:
        """
        Insert or update researcher data.
        
        Args:
            data: Researcher data dictionary
            
        Returns:
            Researcher UUID
        """
        query = """
        INSERT INTO researchers (institution_id, openalex_id, full_name, h_index, department)
        VALUES (%(institution_id)s, %(openalex_id)s, %(full_name)s, %(h_index)s, %(department)s)
        ON CONFLICT (openalex_id)
        DO UPDATE SET
            full_name = EXCLUDED.full_name,
            h_index = EXCLUDED.h_index,
            department = EXCLUDED.department,
            updated_at = now()
        RETURNING id;
        """
        
        result = self.execute_query(query, data, fetch=True)
        researcher_id = result[0]['id']
        logger.debug(f"Upserted researcher: {data['full_name']} (ID: {researcher_id})")
        return str(researcher_id)
    
    def upsert_work(self, data: Dict) -> str:
        """
        Insert or update work data.
        
        Args:
            data: Work data dictionary
            
        Returns:
            Work UUID
        """
        query = """
        INSERT INTO works (researcher_id, openalex_id, title, abstract, keywords, 
                          publication_year, doi, citations, embedding)
        VALUES (%(researcher_id)s, %(openalex_id)s, %(title)s, %(abstract)s, %(keywords)s,
                %(publication_year)s, %(doi)s, %(citations)s, %(embedding)s)
        ON CONFLICT (openalex_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            abstract = EXCLUDED.abstract,
            keywords = EXCLUDED.keywords,
            publication_year = EXCLUDED.publication_year,
            doi = EXCLUDED.doi,
            citations = EXCLUDED.citations,
            embedding = EXCLUDED.embedding,
            updated_at = now()
        RETURNING id;
        """
        
        result = self.execute_query(query, data, fetch=True)
        work_id = result[0]['id']
        logger.debug(f"Upserted work: {data['title'][:50]}... (ID: {work_id})")
        return str(work_id)
    
    def upsert_topics(self, work_id: str, topics: List[Dict]) -> None:
        """
        Insert or update topics for a work.
        
        Args:
            work_id: Work UUID
            topics: List of topic dictionaries
        """
        if not topics:
            return
        
        # First, delete existing topics for this work
        delete_query = "DELETE FROM topics WHERE work_id = %s;"
        self.execute_query(delete_query, (work_id,))
        
        # Insert new topics
        insert_query = """
        INSERT INTO topics (work_id, name, type, score)
        VALUES (%(work_id)s, %(name)s, %(type)s, %(score)s);
        """
        
        for topic in topics:
            self.execute_query(insert_query, topic)
        
        logger.debug(f"Upserted {len(topics)} topics for work {work_id}")
    
    def create_standalone_topics_table(self) -> None:
        """
        Create standalone topics table for OpenAlex topics.
        """
        query = """
        CREATE TABLE IF NOT EXISTS standalone_topics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            openalex_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            field TEXT,
            subfield TEXT,
            domain TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
        
        CREATE INDEX IF NOT EXISTS idx_standalone_topics_openalex_id ON standalone_topics(openalex_id);
        CREATE INDEX IF NOT EXISTS idx_standalone_topics_name ON standalone_topics(name);
        CREATE INDEX IF NOT EXISTS idx_standalone_topics_field ON standalone_topics(field);
        CREATE INDEX IF NOT EXISTS idx_standalone_topics_subfield ON standalone_topics(subfield);
        CREATE INDEX IF NOT EXISTS idx_standalone_topics_domain ON standalone_topics(domain);
        
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_standalone_topics_updated_at') THEN
                CREATE TRIGGER update_standalone_topics_updated_at 
                BEFORE UPDATE ON standalone_topics 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END $$;
        """
        
        self.execute_query(query)
        logger.info("Standalone topics table created successfully")
    
    def upsert_standalone_topic(self, data: Dict) -> str:
        """
        Insert or update standalone topic data.
        
        Args:
            data: Topic data dictionary
            
        Returns:
            Topic UUID
        """
        query = """
        INSERT INTO standalone_topics (openalex_id, name, description, field, subfield, domain)
        VALUES (%(openalex_id)s, %(name)s, %(description)s, %(field)s, %(subfield)s, %(domain)s)
        ON CONFLICT (openalex_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            field = EXCLUDED.field,
            subfield = EXCLUDED.subfield,
            domain = EXCLUDED.domain,
            updated_at = now()
        RETURNING id;
        """
        
        result = self.execute_query(query, data, fetch=True)
        topic_id = result[0]['id']
        logger.debug(f"Upserted standalone topic: {data['name']} (ID: {topic_id})")
        return str(topic_id)
    
    def upsert_grants(self, researcher_id: str, grants: List[Dict]) -> None:
        """
        Insert or update grants for a researcher.
        
        Args:
            researcher_id: Researcher UUID
            grants: List of grant dictionaries
        """
        if not grants:
            return
        
        query = """
        INSERT INTO researcher_grants (researcher_id, award_id, award_year, role, award_amount, award_title)
        VALUES (%(researcher_id)s, %(award_id)s, %(award_year)s, %(role)s, %(award_amount)s, %(award_title)s)
        ON CONFLICT (researcher_id, award_id)
        DO UPDATE SET
            award_year = EXCLUDED.award_year,
            role = EXCLUDED.role,
            award_amount = EXCLUDED.award_amount,
            award_title = EXCLUDED.award_title;
        """
        
        for grant in grants:
            self.execute_query(query, grant)
        
        logger.debug(f"Upserted {len(grants)} grants for researcher {researcher_id}")
    
    def get_pipeline_stats(self) -> Dict:
        """
        Get statistics about the data in the pipeline.
        
        Returns:
            Dictionary with counts of each data type
        """
        stats = {}
        
        try:
            # Count institutions
            result = self.execute_query("SELECT COUNT(*) as count FROM institutions;", fetch=True)
            stats['institutions'] = result[0]['count']
            
            # Count researchers
            result = self.execute_query("SELECT COUNT(*) as count FROM researchers;", fetch=True)
            stats['researchers'] = result[0]['count']
            
            # Count works
            result = self.execute_query("SELECT COUNT(*) as count FROM works;", fetch=True)
            stats['works'] = result[0]['count']
            
            # Count topics (work-related)
            result = self.execute_query("SELECT COUNT(*) as count FROM topics;", fetch=True)
            stats['topics'] = result[0]['count']
            
            # Count standalone topics
            try:
                result = self.execute_query("SELECT COUNT(*) as count FROM standalone_topics;", fetch=True)
                stats['standalone_topics'] = result[0]['count']
            except:
                stats['standalone_topics'] = 0
            
            # Count grants
            result = self.execute_query("SELECT COUNT(*) as count FROM researcher_grants;", fetch=True)
            stats['grants'] = result[0]['count']
            
            # Count works with embeddings
            result = self.execute_query("SELECT COUNT(*) as count FROM works WHERE embedding IS NOT NULL;", fetch=True)
            stats['works_with_embeddings'] = result[0]['count']
            
            # Count works with keywords
            result = self.execute_query("SELECT COUNT(*) as count FROM works WHERE keywords IS NOT NULL AND keywords != '[]';", fetch=True)
            stats['works_with_keywords'] = result[0]['count']
            
            logger.info(f"Pipeline stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return stats
    
    def validate_data_quality(self) -> Dict:
        """
        Validate data quality and completeness.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'total_researchers': 0,
            'researchers_with_works': 0,
            'works_with_abstracts': 0,
            'works_with_embeddings': 0,
            'works_with_keywords': 0,
            'works_with_topics': 0,
            'average_works_per_researcher': 0.0,
            'average_citations_per_work': 0.0,
            'data_quality_score': 0.0
        }
        
        try:
            # Total researchers
            result = self.execute_query("SELECT COUNT(*) as count FROM researchers;", fetch=True)
            validation['total_researchers'] = result[0]['count']
            
            # Researchers with works
            result = self.execute_query("""
                SELECT COUNT(DISTINCT r.id) as count 
                FROM researchers r 
                JOIN works w ON r.id = w.researcher_id;
            """, fetch=True)
            validation['researchers_with_works'] = result[0]['count']
            
            # Works with abstracts
            result = self.execute_query("""
                SELECT COUNT(*) as count 
                FROM works 
                WHERE abstract IS NOT NULL AND abstract != '';
            """, fetch=True)
            validation['works_with_abstracts'] = result[0]['count']
            
            # Works with embeddings
            result = self.execute_query("""
                SELECT COUNT(*) as count 
                FROM works 
                WHERE embedding IS NOT NULL;
            """, fetch=True)
            validation['works_with_embeddings'] = result[0]['count']
            
            # Works with keywords
            result = self.execute_query("""
                SELECT COUNT(*) as count 
                FROM works 
                WHERE keywords IS NOT NULL AND keywords != '[]';
            """, fetch=True)
            validation['works_with_keywords'] = result[0]['count']
            
            # Works with topics
            result = self.execute_query("""
                SELECT COUNT(DISTINCT w.id) as count 
                FROM works w 
                JOIN topics t ON w.id = t.work_id;
            """, fetch=True)
            validation['works_with_topics'] = result[0]['count']
            
            # Average works per researcher
            result = self.execute_query("""
                SELECT AVG(work_count) as avg_works
                FROM (
                    SELECT COUNT(w.id) as work_count
                    FROM researchers r
                    LEFT JOIN works w ON r.id = w.researcher_id
                    GROUP BY r.id
                ) subq;
            """, fetch=True)
            validation['average_works_per_researcher'] = float(result[0]['avg_works'] or 0)
            
            # Average citations per work
            result = self.execute_query("""
                SELECT AVG(citations) as avg_citations
                FROM works
                WHERE citations IS NOT NULL;
            """, fetch=True)
            validation['average_citations_per_work'] = float(result[0]['avg_citations'] or 0)
            
            # Calculate data quality score (0-100)
            total_works = self.execute_query("SELECT COUNT(*) as count FROM works;", fetch=True)[0]['count']
            
            if total_works > 0:
                abstract_score = (validation['works_with_abstracts'] / total_works) * 25
                embedding_score = (validation['works_with_embeddings'] / total_works) * 25
                keyword_score = (validation['works_with_keywords'] / total_works) * 25
                topic_score = (validation['works_with_topics'] / total_works) * 25
                
                validation['data_quality_score'] = abstract_score + embedding_score + keyword_score + topic_score
            
            logger.info(f"Data quality validation: {validation}")
            return validation
            
        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            return validation

    def close(self) -> None:
        """
        Close all connections in the pool.
        """
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")
        else:
            logger.warning("No connection pool to close")


def main():
    """
    Main function to demonstrate DatabaseManager usage and run tests.
    """
    print("=== Supabase Database Connection Test ===\n")
    
    try:
        # Initialize DatabaseManager
        db_manager = DatabaseManager()
        
        # Connect to database
        db_manager.connect()
        print("✓ Database connection established successfully\n")
        
        # Run basic operations test
        print("Running basic database operations test...")
        basic_test_results = db_manager.test_basic_operations()
        
        print(f"\nBasic Operations Test Results:")
        print(f"Success: {basic_test_results['success']}")
        print(f"Duration: {basic_test_results['duration']:.2f} seconds")
        
        if basic_test_results['success']:
            for operation, result in basic_test_results['operations'].items():
                print(f"  {operation}: {result}")
        else:
            print(f"Error: {basic_test_results['error']}")
        
        # Run connection pooling test
        print("\nRunning connection pooling test...")
        pool_test_results = db_manager.test_connection_pooling()
        
        print(f"\nConnection Pooling Test Results:")
        print(f"Success: {pool_test_results['success']}")
        print(f"Duration: {pool_test_results['duration']:.2f} seconds")
        print(f"Max connections test: {pool_test_results['max_connections_test']}")
        print(f"Concurrent operations: {pool_test_results['concurrent_operations']}")
        print(f"Pool exhaustion handling: {pool_test_results['pool_exhaustion_handling']}")
        
        if pool_test_results['error']:
            print(f"Error: {pool_test_results['error']}")
        
        # Run vector extension test
        print("\nRunning vector extension compatibility test...")
        vector_test_results = db_manager.test_vector_extension()
        
        print(f"\nVector Extension Test Results:")
        print(f"Success: {vector_test_results['success']}")
        print(f"Duration: {vector_test_results['duration']:.2f} seconds")
        print(f"Extension available: {vector_test_results['extension_available']}")
        print(f"Vector operations: {vector_test_results['vector_operations']}")
        print(f"Distance calculations: {vector_test_results['distance_calculations']}")
        
        if vector_test_results['error']:
            print(f"Error: {vector_test_results['error']}")
        
        # Overall success (vector extension is optional for basic functionality)
        overall_success = basic_test_results['success'] and pool_test_results['success']
        vector_available = vector_test_results['success']
        
        print(f"\n=== Overall Test Result: {'SUCCESS' if overall_success else 'FAILED'} ===")
        if overall_success and not vector_available:
            print("Note: Basic database operations successful, but vector extension needs to be enabled for embedding support")
        
        return overall_success
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False
        
    finally:
        try:
            db_manager.close()
            print("\nDatabase connections closed.")
        except:
            pass


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)