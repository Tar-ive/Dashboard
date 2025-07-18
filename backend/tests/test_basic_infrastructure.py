"""Basic infrastructure integration tests."""

import pytest
from unittest.mock import patch, MagicMock
from app.jobs.redis_connection import get_redis
from app.jobs.worker_config import get_queue_manager
from app.jobs.job_manager import get_job_manager
from app.models.job import JobStatus
import time

class TestBasicInfrastructure:
    """Test basic infrastructure integration."""
    
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
    
    def test_complete_job_lifecycle(self, mock_redis_infrastructure):
        """Test complete job lifecycle: create -> update -> complete -> cleanup."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        # 1. Create a job
        job_manager = get_job_manager()
        job_id = job_manager.create_job("test_job")
        assert job_id is not None
        assert len(job_id) == 36  # UUID format
        
        # Verify job metadata was stored
        metadata_key = f"job:{job_id}:metadata"
        assert metadata_key in redis_data
        
        # 2. Update job status to processing
        job_manager.update_job_status(job_id, JobStatus.PROCESSING, progress=50)
        
        # 3. Get job status
        status = job_manager.get_job_status(job_id)
        assert status is not None
        assert status.job_id == job_id
        assert status.status == JobStatus.PROCESSING
        assert status.progress == 50
        
        # 4. Store job result
        test_result = {"output": "test data", "success": True}
        job_manager.store_job_result(job_id, test_result)
        
        # 5. Get final status
        final_status = job_manager.get_job_status(job_id)
        assert final_status.status == JobStatus.COMPLETED
        assert final_status.result == test_result
        
        # 6. Cleanup job
        job_manager.cleanup_job(job_id)
        
        # Verify cleanup
        final_status_after_cleanup = job_manager.get_job_status(job_id)
        assert final_status_after_cleanup is None
    
    def test_job_error_handling(self, mock_redis_infrastructure):
        """Test job error handling and storage."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        # Create a job
        job_manager = get_job_manager()
        job_id = job_manager.create_job("test_job")
        
        # Store an error
        job_manager.store_job_error(job_id, "processing_error", "Test error message")
        
        # Verify error was stored and status updated
        status = job_manager.get_job_status(job_id)
        assert status.status == JobStatus.FAILED
        assert status.error_message == "Test error message"
        
        # Verify error key exists
        error_key = f"job:{job_id}:error"
        assert error_key in redis_data
    
    def test_queue_manager_integration(self, mock_redis_infrastructure):
        """Test queue manager integration with mocked Redis."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        with patch('rq.Queue') as mock_queue_class:
            mock_queue = MagicMock()
            mock_queue_class.return_value = mock_queue
            
            # Create queue manager
            from app.jobs.worker_config import QueueManager
            manager = QueueManager()
            
            # Test job enqueueing
            mock_job = MagicMock()
            mock_job.id = "test-job-123"
            mock_queue.enqueue.return_value = mock_job
            
            def dummy_task():
                return "completed"
            
            job = manager.enqueue_job(dummy_task, job_id="test-job-123")
            assert job.id == "test-job-123"
            mock_queue.enqueue.assert_called_once()
    
    def test_redis_connection_error_handling(self):
        """Test Redis connection error handling."""
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        with patch('app.jobs.redis_connection.redis.Redis') as mock_redis_class:
            # Simulate connection failure
            mock_redis_class.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                get_redis()
    
    def test_job_manager_with_missing_job(self, mock_redis_infrastructure):
        """Test job manager behavior with non-existent jobs."""
        mock_redis, redis_data = mock_redis_infrastructure
        
        # Clear any existing Redis instance
        from app.jobs.redis_connection import RedisConnection
        RedisConnection._instance = None
        
        # Try to get status for non-existent job
        job_manager = get_job_manager()
        status = job_manager.get_job_status("nonexistent-job")
        assert status is None
        
        # Try to update status for non-existent job (should not crash)
        job_manager.update_job_status("nonexistent-job", JobStatus.PROCESSING)
        # Should log error but not raise exception