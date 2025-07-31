"""
Test suite for DatabaseManager class.
Tests database connection, basic operations, connection pooling, and vector extension compatibility.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2 import pool

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.database_manager import DatabaseManager


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""
    
    def test_init_with_database_url(self):
        """Test DatabaseManager initialization with provided database URL."""
        test_url = "postgresql://test:test@localhost:5432/test"
        db_manager = DatabaseManager(database_url=test_url)
        
        assert db_manager.database_url == test_url
        assert db_manager.min_connections == 1
        assert db_manager.max_connections == 10
        assert db_manager.connection_pool is None
    
    def test_init_with_env_variable(self):
        """Test DatabaseManager initialization using environment variable."""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://env:env@localhost:5432/env'}):
            db_manager = DatabaseManager()
            assert db_manager.database_url == 'postgresql://env:env@localhost:5432/env'
    
    def test_init_without_database_url(self):
        """Test DatabaseManager initialization fails without database URL."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL must be provided"):
                DatabaseManager()
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_connect_success(self, mock_pool):
        """Test successful database connection."""
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        
        # Mock connection for testing
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'version': 'PostgreSQL 15.0'}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance.getconn.return_value = mock_conn
        
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        db_manager.connect()
        
        assert db_manager.connection_pool is not None
        mock_pool.assert_called_once()
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_connect_failure(self, mock_pool):
        """Test database connection failure."""
        mock_pool.side_effect = psycopg2.OperationalError("Connection failed")
        
        db_manager = DatabaseManager(database_url="postgresql://invalid:invalid@localhost:5432/invalid")
        
        with pytest.raises(psycopg2.OperationalError):
            db_manager.connect()
    
    def test_get_connection_without_pool(self):
        """Test get_connection fails when pool is not initialized."""
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        
        with pytest.raises(RuntimeError, match="Database connection pool not initialized"):
            with db_manager.get_connection():
                pass
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_get_connection_success(self, mock_pool):
        """Test successful connection retrieval from pool."""
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        
        mock_conn = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        db_manager.connection_pool = mock_pool_instance
        
        with db_manager.get_connection() as conn:
            assert conn == mock_conn
        
        mock_pool_instance.putconn.assert_called_once_with(mock_conn)
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_execute_query_success(self, mock_pool):
        """Test successful query execution."""
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance.getconn.return_value = mock_conn
        
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        db_manager.connection_pool = mock_pool_instance
        
        result = db_manager.execute_query("SELECT * FROM test", fetch=True)
        
        assert result == [{'id': 1, 'name': 'test'}]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test", None)
        mock_conn.commit.assert_called_once()
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_execute_query_with_params(self, mock_pool):
        """Test query execution with parameters."""
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance.getconn.return_value = mock_conn
        
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        db_manager.connection_pool = mock_pool_instance
        
        db_manager.execute_query("INSERT INTO test (name) VALUES (%s)", ("test_name",))
        
        mock_cursor.execute.assert_called_once_with("INSERT INTO test (name) VALUES (%s)", ("test_name",))
        mock_conn.commit.assert_called_once()
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_execute_query_error_handling(self, mock_pool):
        """Test query execution error handling."""
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Query failed")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance.getconn.return_value = mock_conn
        
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        db_manager.connection_pool = mock_pool_instance
        
        with pytest.raises(psycopg2.Error):
            db_manager.execute_query("INVALID SQL")
        
        # Rollback should be called (may be called multiple times due to context manager)
        assert mock_conn.rollback.called
    
    def test_close_with_pool(self):
        """Test closing connection pool."""
        mock_pool = MagicMock()
        
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        db_manager.connection_pool = mock_pool
        
        db_manager.close()
        
        mock_pool.closeall.assert_called_once()
    
    def test_close_without_pool(self):
        """Test closing when no pool exists."""
        db_manager = DatabaseManager(database_url="postgresql://test:test@localhost:5432/test")
        
        # Should not raise an exception
        db_manager.close()


@pytest.mark.integration
class TestDatabaseManagerIntegration:
    """Integration tests for DatabaseManager (requires actual database)."""
    
    @pytest.fixture
    def db_manager(self):
        """Create DatabaseManager instance for integration tests."""
        # Skip if no DATABASE_URL is available
        if not os.getenv('DATABASE_URL'):
            pytest.skip("DATABASE_URL not available for integration tests")
        
        manager = DatabaseManager()
        manager.connect()
        yield manager
        manager.close()
    
    def test_real_database_connection(self, db_manager):
        """Test actual database connection."""
        # Test basic query
        result = db_manager.execute_query("SELECT 1 as test_value", fetch=True)
        assert result[0]['test_value'] == 1
    
    def test_basic_operations_integration(self, db_manager):
        """Test basic database operations with real database."""
        test_results = db_manager.test_basic_operations()
        
        assert test_results['success'] is True
        assert 'create_table' in test_results['operations']
        assert 'insert' in test_results['operations']
        assert 'select' in test_results['operations']
        assert 'update' in test_results['operations']
        assert 'delete' in test_results['operations']
        assert 'cleanup' in test_results['operations']
    
    def test_connection_pooling_integration(self, db_manager):
        """Test connection pooling with real database."""
        pool_results = db_manager.test_connection_pooling()
        
        assert pool_results['success'] is True
        assert pool_results['max_connections_test'] is True
        assert pool_results['concurrent_operations'] is True
        assert pool_results['pool_exhaustion_handling'] is True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])