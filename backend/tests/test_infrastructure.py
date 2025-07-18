"""Infrastructure tests for Redis connectivity and job enqueueing."""

import pytest
import redis
from unittest.mock import patch, MagicMock
from app.jobs.redis_connection import RedisConnection, get_redis
from app.jobs.worker_config import QueueManager, create_worker
from app.jobs.job_manager import JobManager
from app.models.job import JobStatus, JobMetadata
from datetime import datetime
import json

class TestRedisConnection:
    """Test Redis connection management."""
    
    def test_redis_connection_singleton(self):
        """Test that Redis connection uses singleton pattern."""
        # Clear any existing instance
        RedisConnection._instance = None
        
        with patch('redis.Redis') as mock_redis:
            mock_instance = MagicMock()
            mock_redis.return_value = mock_instance
            mock_instance.ping.return_value = True
            
            # Get connection twice
            conn1 = RedisConnection.get_connection()
            conn2 = RedisConnection.get_connection()
            
            # Should be the same instance
            assert conn1 is conn2
            # Redis should only be instantiated once
            mock_redis.assert_called_once()
    
    def test_redis_connection_with_config(self):
        """Test Redis connection uses correct configuration."""
        RedisConnection._instance = None
        
        with patch('redis.Redis') as mock_redis:
            mock_instance = MagicMock()
            mock_redis.return_value = mock_instance
            mock_instance.ping.return_value = True
            
            RedisConnection.get_connection()
            
            # Verify Redis was called with correct parameters
            mock_redis.assert_called_once_with(
                host='localhost',  # Default from config
                port=6379,
                db=0,
                password=None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
    
    def test_redis_connection_failure(self):
        """Test Redis connection failure handling."""
        RedisConnection._instance = None
        
        with patch('redis.Redis') as mock_redis:
            mock_redis.side_effect = redis.ConnectionError("Connection failed")
            
            with pytest.raises(redis.ConnectionError):
                RedisConnection.get_connection()
    
    def test_redis_connection_test(self):
        """Test Redis connection health check."""
        RedisConnection._instance = None
        
        with patch('redis.Redis') as mock_redis:
            mock_instance = MagicMock()
            mock_redis.return_value = mock_instance
            
            # Test successful connection
            mock_instance.ping.return_value = True
            assert RedisConnection.test_connection() is True
            
            # Test failed connection
            mock_instance.ping.side_effect = redis.ConnectionError("Ping failed")
            assert RedisConnection.test_connection() is False
    
    def test_redis_connection_close(self):
        """Test Redis connection cleanup."""
        RedisConnection._instance = None
        
        with patch('redis.Redis') as mock_redis:
            mock_instance = MagicMock()
            mock_redis.return_value = mock_instance
            mock_instance.ping.return_value = True
            
            # Get connection and close it
            RedisConnection.get_connection()
            RedisConnection.close_connection()
            
            # Instance should be cleared
            assert RedisConnection._instance is None
            mock_instance.close.assert_called_once()

class TestQueueManager:
    """Test RQ queue management."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection for testing."""
        with patch('app.jobs.worker_config.get_redis') as mock:
            mock_conn = MagicMock()
            mock.return_value = mock_conn
            yield mock_conn
    
    @pytest.fixture
    def queue_manager(self, mock_redis):
        """Create QueueManager instance with mocked Redis."""
        with patch('rq.Queue') as mock_queue_class:
            mock_queue = MagicMock()
            mock_queue_class.return_value = mock_queue
            
            manager = QueueManager()
            manager.queue = mock_queue
            return manager
    
    def test_enqueue_job(self, queue_manager):
        """Test job enqueueing."""
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        queue_manager.queue.enqueue.return_value = mock_job
        
        def dummy_function():
            return "test"
        
        job = queue_manager.enqueue_job(dummy_function, job_id="test-job-123")
        
        assert job.id == "test-job-123"
        queue_manager.queue.enqueue.assert_called_once()
    
    def test_enqueue_job_failure(self, queue_manager):
        """Test job enqueueing failure handling."""
        queue_manager.queue.enqueue.side_effect = Exception("Enqueue failed")
        
        def dummy_function():
            return "test"
        
        with pytest.raises(Exception, match="Enqueue failed"):
            queue_manager.enqueue_job(dummy_function)
    
    def test_get_job(self, queue_manager, mock_redis):
        """Test job retrieval."""
        with patch('rq.job.Job.fetch') as mock_fetch:
            mock_job = MagicMock()
            mock_fetch.return_value = mock_job
            
            job = queue_manager.get_job("test-job-123")
            
            assert job is mock_job
            mock_fetch.assert_called_once_with("test-job-123", connection=mock_redis)
    
    def test_get_job_not_found(self, queue_manager, mock_redis):
        """Test job retrieval when job doesn't exist."""
        with patch('rq.job.Job.fetch') as mock_fetch:
            mock_fetch.side_effect = Exception("Job not found")
            
            job = queue_manager.get_job("nonexistent-job")
            
            assert job is None
    
    def test_get_queue_length(self, queue_manager):
        """Test queue length retrieval."""
        queue_manager.queue.__len__ = MagicMock(return_value=5)
        
        length = queue_manager.get_queue_length()
        
        assert length == 5
    
    def test_clear_queue(self, queue_manager):
        """Test queue clearing."""
        queue_manager.clear_queue()
        
        queue_manager.queue.empty.assert_called_once()

class TestJobManager:
    """Test job state management."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection for testing."""
        with patch('app.jobs.job_manager.get_redis') as mock:
            mock_conn = MagicMock()
            mock.return_value = mock_conn
            yield mock_conn
    
    @pytest.fixture
    def job_manager(self, mock_redis):
        """Create JobManager instance with mocked Redis."""
        return JobManager()
    
    def test_create_job(self, job_manager, mock_redis):
        """Test job creation."""
        job_id = job_manager.create_job("test_job")
        
        # Should generate a UUID
        assert len(job_id) == 36  # UUID length
        assert "-" in job_id
        
        # Should store metadata in Redis
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == f"job:{job_id}:metadata"
    
    def test_create_job_with_custom_id(self, job_manager, mock_redis):
        """Test job creation with custom ID."""
        custom_id = "custom-job-123"
        job_id = job_manager.create_job("test_job", job_id=custom_id)
        
        assert job_id == custom_id
        mock_redis.set.assert_called_once()
    
    def test_update_job_status(self, job_manager, mock_redis):
        """Test job status updates."""
        # Mock existing job metadata
        existing_metadata = JobMetadata(
            job_id="test-job",
            job_type="test",
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        mock_redis.get.return_value = existing_metadata.model_dump_json()
        
        job_manager.update_job_status("test-job", JobStatus.PROCESSING, progress=50)
        
        # Should fetch and update metadata
        mock_redis.get.assert_called_with("job:test-job:metadata")
        mock_redis.set.assert_called()
    
    def test_store_job_result(self, job_manager, mock_redis):
        """Test job result storage."""
        # Mock existing job metadata
        existing_metadata = JobMetadata(
            job_id="test-job",
            job_type="test",
            status=JobStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        mock_redis.get.return_value = existing_metadata.model_dump_json()
        
        result = {"data": "test result"}
        job_manager.store_job_result("test-job", result)
        
        # Should store result and update metadata
        assert mock_redis.set.call_count >= 2  # Result + metadata
    
    def test_get_job_status(self, job_manager, mock_redis):
        """Test job status retrieval."""
        # Mock job metadata
        metadata = JobMetadata(
            job_id="test-job",
            job_type="test",
            status=JobStatus.COMPLETED,
            progress=100,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        mock_redis.get.side_effect = [
            metadata.model_dump_json(),  # metadata call
            json.dumps({"result": "data"})  # result call
        ]
        
        status = job_manager.get_job_status("test-job")
        
        assert status is not None
        assert status.job_id == "test-job"
        assert status.status == JobStatus.COMPLETED
        assert status.progress == 100
    
    def test_get_job_status_not_found(self, job_manager, mock_redis):
        """Test job status retrieval for non-existent job."""
        mock_redis.get.return_value = None
        
        status = job_manager.get_job_status("nonexistent-job")
        
        assert status is None
    
    def test_store_job_error(self, job_manager, mock_redis):
        """Test job error storage."""
        # Mock existing job metadata
        existing_metadata = JobMetadata(
            job_id="test-job",
            job_type="test",
            status=JobStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        mock_redis.get.return_value = existing_metadata.model_dump_json()
        
        job_manager.store_job_error("test-job", "test_error", "Test error message")
        
        # Should store error and update status
        assert mock_redis.set.call_count >= 2  # Error + metadata update
    
    def test_cleanup_job(self, job_manager, mock_redis):
        """Test job cleanup."""
        job_manager.cleanup_job("test-job")
        
        # Should delete all job-related keys
        expected_keys = [
            "job:test-job:metadata",
            "job:test-job:result", 
            "job:test-job:error"
        ]
        
        assert mock_redis.delete.call_count == len(expected_keys)
        for key in expected_keys:
            mock_redis.delete.assert_any_call(key)

class TestWorkerCreation:
    """Test RQ worker creation."""
    
    def test_create_worker(self):
        """Test worker creation."""
        with patch('app.jobs.worker_config.get_redis') as mock_get_redis, \
             patch('app.jobs.worker_config.Queue') as mock_queue_class, \
             patch('app.jobs.worker_config.Worker') as mock_worker_class:
            
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            mock_queue = MagicMock()
            mock_queue_class.return_value = mock_queue
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker
            
            worker = create_worker()
            
            # Should create queue and worker
            mock_queue_class.assert_called_once_with('default', connection=mock_redis)
            mock_worker_class.assert_called_once()
            assert worker is mock_worker
    
    def test_create_worker_custom_queues(self):
        """Test worker creation with custom queue names."""
        with patch('app.jobs.worker_config.get_redis') as mock_get_redis, \
             patch('app.jobs.worker_config.Queue') as mock_queue_class, \
             patch('app.jobs.worker_config.Worker') as mock_worker_class:
            
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            mock_queue = MagicMock()
            mock_queue_class.return_value = mock_queue
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker
            
            custom_queues = ['queue1', 'queue2']
            worker = create_worker(custom_queues)
            
            # Should create multiple queues
            assert mock_queue_class.call_count == len(custom_queues)
            mock_worker_class.assert_called_once()
            assert worker is mock_worker