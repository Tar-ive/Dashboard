"""Simplified tests for job enqueueing utilities and Redis integration."""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from app.jobs.job_manager import get_job_manager
from app.jobs.worker_config import get_queue_manager
from app.models.job import JobStatus


class TestJobEnqueueingSimple:
    """Test job enqueueing utilities and Redis integration - simplified version."""
    
    def test_job_id_generation_functionality(self):
        """Test job_id generation and Redis key management."""
        with patch('app.jobs.redis_connection.redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping.return_value = True
            
            # Mock Redis operations
            redis_data = {}
            mock_redis.set.side_effect = lambda k, v: redis_data.update({k: v})
            mock_redis.get.side_effect = lambda k: redis_data.get(k)
            mock_redis.delete.side_effect = lambda k: redis_data.pop(k, None)
            
            # Clear any existing Redis instance
            from app.jobs.redis_connection import RedisConnection
            RedisConnection._instance = None
            
            job_manager = get_job_manager()
            
            # Test automatic job_id generation
            job_id1 = job_manager.create_job("test_type")
            job_id2 = job_manager.create_job("test_type")
            
            # Job IDs should be different and valid UUIDs
            assert job_id1 != job_id2
            assert len(job_id1) == 36  # UUID format
            assert len(job_id2) == 36  # UUID format
            uuid.UUID(job_id1)  # Should not raise exception
            uuid.UUID(job_id2)  # Should not raise exception
            
            # Test custom job_id
            custom_job_id = str(uuid.uuid4())
            job_id3 = job_manager.create_job("test_type", job_id=custom_job_id)
            assert job_id3 == custom_job_id
    
    def test_redis_key_management_patterns(self):
        """Test Redis key management patterns."""
        with patch('app.jobs.redis_connection.redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping.return_value = True
            
            # Mock Redis operations with tracking
            redis_data = {}
            mock_redis.set.side_effect = lambda k, v: redis_data.update({k: v})
            mock_redis.get.side_effect = lambda k: redis_data.get(k)
            mock_redis.delete.side_effect = lambda k: redis_data.pop(k, None)
            
            # Clear any existing Redis instance
            from app.jobs.redis_connection import RedisConnection
            RedisConnection._instance = None
            
            job_manager = get_job_manager()
            job_id = job_manager.create_job("test_job")
            
            # Verify Redis key patterns are used correctly
            expected_keys = [
                f"job:{job_id}:metadata"
            ]
            
            # Check that metadata key was created
            for key in expected_keys:
                assert key in redis_data, f"Expected Redis key {key} not found"
            
            # Test result storage creates correct key
            test_result = {"output": "test data"}
            job_manager.store_job_result(job_id, test_result)
            result_key = f"job:{job_id}:result"
            assert result_key in redis_data
            
            # Test error storage creates correct key
            job_manager.store_job_error(job_id, "test_error", "Test error message")
            error_key = f"job:{job_id}:error"
            assert error_key in redis_data
    
    def test_job_state_update_utilities(self):
        """Test utility functions for job state updates."""
        with patch('app.jobs.redis_connection.redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping.return_value = True
            
            # Mock Redis operations
            redis_data = {}
            mock_redis.set.side_effect = lambda k, v: redis_data.update({k: v})
            mock_redis.get.side_effect = lambda k: redis_data.get(k)
            
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
            
            # Test completion status
            job_manager.update_job_status(job_id, JobStatus.COMPLETED)
            status = job_manager.get_job_status(job_id)
            assert status.status == JobStatus.COMPLETED
            
            # Test failure with error message
            job_id2 = job_manager.create_job("test_job")
            job_manager.update_job_status(job_id2, JobStatus.FAILED, error_message="Test failure")
            status = job_manager.get_job_status(job_id2)
            assert status.status == JobStatus.FAILED
            assert status.error_message == "Test failure"
    
    def test_queue_management_integration(self):
        """Test job queue management and status transitions."""
        with patch('app.jobs.redis_connection.redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping.return_value = True
            
            # Clear any existing Redis instance
            from app.jobs.redis_connection import RedisConnection
            RedisConnection._instance = None
            
            with patch('rq.Queue') as mock_queue_class:
                mock_queue = MagicMock()
                mock_queue_class.return_value = mock_queue
                
                # Mock queue operations
                mock_queue.__len__.return_value = 0
                mock_job = MagicMock()
                mock_job.id = "test-job-123"
                mock_queue.enqueue.return_value = mock_job
                
                # Create queue manager
                queue_manager = get_queue_manager()
                
                # Test job enqueueing
                def dummy_task():
                    return "completed"
                
                job = queue_manager.enqueue_job(dummy_task, job_id="test-job-123")
                assert job.id == "test-job-123"
                
                # Verify enqueue was called
                mock_queue.enqueue.assert_called_once()
                call_args = mock_queue.enqueue.call_args
                assert call_args[1]['job_id'] == "test-job-123"
    
    def test_error_handling_in_operations(self):
        """Test error handling in job operations."""
        with patch('app.jobs.redis_connection.redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping.return_value = True
            
            # Mock Redis operations
            redis_data = {}
            mock_redis.set.side_effect = lambda k, v: redis_data.update({k: v})
            mock_redis.get.side_effect = lambda k: redis_data.get(k)
            
            # Clear any existing Redis instance
            from app.jobs.redis_connection import RedisConnection
            RedisConnection._instance = None
            
            job_manager = get_job_manager()
            
            # Test handling of non-existent job operations
            # These should not raise exceptions
            job_manager.update_job_status("nonexistent-job", JobStatus.PROCESSING)
            status = job_manager.get_job_status("nonexistent-job")
            assert status is None
            
            job_manager.cleanup_job("nonexistent-job")
            # Should complete without error