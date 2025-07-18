"""Job state management and Redis storage patterns."""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from app.jobs.redis_connection import get_redis
from app.models.job import JobStatus, JobMetadata, JobStatusResponse, JobError
import logging

logger = logging.getLogger(__name__)

class JobManager:
    """Manages job state and Redis storage patterns."""
    
    def __init__(self):
        self.redis = get_redis()
    
    def create_job(self, job_type: str, job_id: Optional[str] = None) -> str:
        """Create a new job and store initial state in Redis."""
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        metadata = JobMetadata(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        
        self._store_job_metadata(metadata)
        logger.info(f"Job created: {job_id} (type: {job_type})")
        return job_id
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         progress: Optional[int] = None,
                         error_message: Optional[str] = None) -> None:
        """Update job status in Redis."""
        try:
            metadata = self._get_job_metadata(job_id)
            if not metadata:
                logger.error(f"Job not found: {job_id}")
                return
            
            metadata.status = status
            if progress is not None:
                metadata.progress = progress
            if error_message:
                metadata.error_message = error_message
            
            # Update timestamps
            now = datetime.utcnow()
            if status == JobStatus.PROCESSING and not metadata.started_at:
                metadata.started_at = now
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                metadata.completed_at = now
            
            self._store_job_metadata(metadata)
            logger.info(f"Job {job_id} status updated to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
    
    def store_job_result(self, job_id: str, result: Dict[str, Any]) -> None:
        """Store job result in Redis."""
        try:
            # Store result separately for large data
            result_key = f"job:{job_id}:result"
            self.redis.set(result_key, json.dumps(result, default=str))
            
            # Update metadata with completion
            metadata = self._get_job_metadata(job_id)
            if metadata:
                metadata.result = {"stored": True, "key": result_key}
                metadata.status = JobStatus.COMPLETED
                metadata.completed_at = datetime.utcnow()
                self._store_job_metadata(metadata)
            
            logger.info(f"Job result stored: {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to store job result for {job_id}: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """Get complete job status from Redis."""
        try:
            metadata = self._get_job_metadata(job_id)
            if not metadata:
                return None
            
            # Get result if available
            result = None
            if metadata.result and metadata.result.get("stored"):
                result_key = metadata.result["key"]
                result_data = self.redis.get(result_key)
                if result_data:
                    result = json.loads(result_data)
            
            # Calculate processing time
            processing_time = None
            if metadata.started_at and metadata.completed_at:
                processing_time = (metadata.completed_at - metadata.started_at).total_seconds()
            
            return JobStatusResponse(
                job_id=job_id,
                status=metadata.status,
                progress=metadata.progress,
                result=result,
                error_message=metadata.error_message,
                created_at=metadata.created_at,
                started_at=metadata.started_at,
                completed_at=metadata.completed_at,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    def store_job_error(self, job_id: str, error_type: str, error_message: str) -> None:
        """Store job error information."""
        try:
            error = JobError(
                job_id=job_id,
                error_type=error_type,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            
            error_key = f"job:{job_id}:error"
            self.redis.set(error_key, error.model_dump_json())
            
            # Update job status to failed
            self.update_job_status(job_id, JobStatus.FAILED, error_message=error_message)
            
            logger.error(f"Job error stored: {job_id} - {error_type}: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to store job error for {job_id}: {e}")
    
    def cleanup_job(self, job_id: str) -> None:
        """Clean up job data from Redis."""
        try:
            keys_to_delete = [
                f"job:{job_id}:metadata",
                f"job:{job_id}:result",
                f"job:{job_id}:error"
            ]
            
            for key in keys_to_delete:
                self.redis.delete(key)
            
            logger.info(f"Job data cleaned up: {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup job {job_id}: {e}")
    
    def _store_job_metadata(self, metadata: JobMetadata) -> None:
        """Store job metadata in Redis."""
        key = f"job:{metadata.job_id}:metadata"
        self.redis.set(key, metadata.model_dump_json())
    
    def _get_job_metadata(self, job_id: str) -> Optional[JobMetadata]:
        """Get job metadata from Redis."""
        key = f"job:{job_id}:metadata"
        data = self.redis.get(key)
        if data:
            return JobMetadata.model_validate_json(data)
        return None

# Global job manager instance (lazy initialization)
_job_manager_instance = None

def get_job_manager() -> JobManager:
    """Get job manager instance (lazy initialization)."""
    global _job_manager_instance
    if _job_manager_instance is None:
        _job_manager_instance = JobManager()
    return _job_manager_instance