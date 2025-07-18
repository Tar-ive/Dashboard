"""Tests for job enqueueing utilities and Redis integration."""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from app.jobs.job_manager import get_job_manager
from app.jobs.worker_config import get_queue_manager
from app.models.job import JobStatus
from datetime import datetime


class TestJobEnqueueingUtilities:
    """Test job enqueueing utilities and Redis integration."""
    
    @pytest.fixture
    def mock_redis_infrastructure(self):
        """Mock the entire Redis infrastructure for integration testing."""
        with patch('app.jobs.redis_connection.redis.Redis') as mock_redis_class:
            # Create a mock Redis instance
            mock_redis = MagicMock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping.return_value = True
            
            # Mock Redis operations
            redis_data = {}
            
            def mock_set(key, value):
                redis_data[key] = value
                return True
            
            def mock_get(key):
                return redis_data.get(key)
            
            def mock_delete(key):
                if key in redis_data:
                    del redis_data[key]
                return True
            
            mock_redis.set.side_effect = mock_set
            mock_redis.get.side_effect = mock_get
            mock_redis.delete.side_effect = mock_delete
            
            yield mock_redis, redis_data
    
    def test_job_creation_and_redis_storage(self, mock_redis_infrastructure):
        """Test job creation and Redis storage."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        # Create job manager
        job_manager = get_job_manager()
        
        # Test job creation
        job_id = job_manager.create_job("test_job_type")
        
        # Verify job_id is valid UUID
        assert job_id is not None
        assert len(job_id) == 36  # UUID format
        uuid.UUID(job_id)  # Should not raise exception
        
        # Verify job metadata was stored in Redis
        metadata_key = f"job:{job_id}:metadata"
        assert metadata_key in redis_data
        
        # Verify stored metadata structure
        stored_data = redis_data[metadata_key]
        assert stored_data is not None
        
        # Verify job can be retrieved
        status = job_manager.get_job_status(job_id)
        assert status is not None
        assert status.job_id == job_id
        assert status.status == JobStatus.QUEUED
    
    def test_job_id_generation(self, mock_redis_infrastructure):
        """Test job_id generation functionality."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        job_manager = get_job_manager()
        
        # Test automatic job_id generation
        job_id1 = job_manager.create_job("test_type")
        job_id2 = job_manager.create_job("test_type")
        
        # Job IDs should be different
        assert job_id1 != job_id2
        
        # Both should be valid UUIDs
        uuid.UUID(job_id1)
        uuid.UUID(job_id2)
        
        # Test custom job_id
        custom_job_id = str(uuid.uuid4())
        job_id3 = job_manager.create_job("test_type", job_id=custom_job_id)
        assert job_id3 == custom_job_id
    
    def test_redis_key_management(self, mock_redis_infrastructure):
        """Test Redis key management patterns."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        job_manager = get_job_manager()
        job_id = job_manager.create_job("test_job")
        
        # Test metadata key pattern
        metadata_key = f"job:{job_id}:metadata"
        assert metadata_key in redis_data
        
        # Test result storage
        test_result = {"output": "test data"}
        job_manager.store_job_result(job_id, test_result)
        
        result_key = f"job:{job_id}:result"
        assert result_key in redis_data
        
        # Test error storage
        job_manager.store_job_error(job_id, "test_error", "Test error message")
        
        error_key = f"job:{job_id}:error"
        assert error_key in redis_data
        
        # Test cleanup removes all keys
        job_manager.cleanup_job(job_id)
        assert metadata_key not in redis_data
        assert result_key not in redis_data
        assert error_key not in redis_data
    
    def test_job_state_updates(self, mock_redis_infrastructure):
        """Test utility functions for job state updates."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        job_manager = get_job_manager()
        job_id = job_manager.create_job("test_job")
        
        # Test status transitions
        job_manager.update_job_status(job_id, JobStatus.PROCESSING, progress=25)
        status = job_manager.get_job_status(job_id)
        assert status.status == JobStatus.PROCESSING
        assert status.progress == 25
        assert status.started_at is not None
        
        # Test progress update
        job_manager.update_job_status(job_id, JobStatus.PROCESSING, progress=75)
        status = job_manager.get_job_status(job_id)
        assert status.progress == 75
        
        # Test completion
        job_manager.update_job_status(job_id, JobStatus.COMPLETED)
        status = job_manager.get_job_status(job_id)
        assert status.status == JobStatus.COMPLETED
        assert status.completed_at is not None
        
        # Test failure with error message
        job_id2 = job_manager.create_job("test_job")
        job_manager.update_job_status(job_id2, JobStatus.FAILED, error_message="Test failure")
        status = job_manager.get_job_status(job_id2)
        assert status.status == JobStatus.FAILED
        assert status.error_message == "Test failure"
    
    def test_job_queue_management(self, mock_redis_infrastructure):
        """Test job queue management and status transitions."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        with patch('rq.Queue') as mock_queue_class:
            mock_queue = MagicMock()
            mock_queue_class.return_value = mock_queue
            
            # Mock queue length properly
            mock_queue.__len__.return_value = 0
            
            # Create queue manager
            queue_manager = get_queue_manager()
            
            # Test queue length
            assert queue_manager.get_queue_length() == 0
            
            # Test job enqueueing
            mock_job = MagicMock()
            mock_job.id = "test-job-123"
            mock_queue.enqueue.return_value = mock_job
            
            def dummy_task():
                return "completed"
            
            # Test enqueueing with custom job_id
            job = queue_manager.enqueue_job(dummy_task, job_id="test-job-123")
            assert job.id == "test-job-123"
            
            # Verify enqueue was called with correct parameters
            mock_queue.enqueue.assert_called_once()
            call_args = mock_queue.enqueue.call_args
            assert call_args[1]['job_id'] == "test-job-123"
    
    def test_error_handling_in_job_operations(self, mock_redis_infrastructure):
        """Test error handling in job operations."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        job_manager = get_job_manager()
        
        # Test handling of non-existent job updates
        job_manager.update_job_status("nonexistent-job", JobStatus.PROCESSING)
        # Should not raise exception, just log error
        
        # Test getting status of non-existent job
        status = job_manager.get_job_status("nonexistent-job")
        assert status is None
        
        # Test cleanup of non-existent job
        job_manager.cleanup_job("nonexistent-job")
        # Should not raise exception
    
    def test_job_metadata_structure(self, mock_redis_infrastructure):
        """Test job metadata structure and validation."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        job_manager = get_job_manager()
        job_id = job_manager.create_job("test_job_type")
        
        # Get job status and verify structure
        status = job_manager.get_job_status(job_id)
        
        # Verify all required fields are present
        assert hasattr(status, 'job_id')
        assert hasattr(status, 'status')
        assert hasattr(status, 'progress')
        assert hasattr(status, 'result')
        assert hasattr(status, 'error_message')
        assert hasattr(status, 'created_at')
        assert hasattr(status, 'started_at')
        assert hasattr(status, 'completed_at')
        assert hasattr(status, 'processing_time_seconds')
        
        # Verify initial values
        assert status.job_id == job_id
        assert status.status == JobStatus.QUEUED
        assert status.progress == 0
        assert status.result is None
        assert status.error_message is None
        assert status.created_at is not None
        assert status.started_at is None
        assert status.completed_at is None
        assert status.processing_time_seconds is None