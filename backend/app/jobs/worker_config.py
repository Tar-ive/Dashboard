"""RQ worker configuration and queue management."""

from rq import Queue, Worker
from rq.job import Job
from typing import Optional, List
from app.jobs.redis_connection import get_redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class QueueManager:
    """Manages RQ queues and job operations."""
    
    def __init__(self):
        self.redis_conn = get_redis()
        self.queue = Queue(
            name=settings.RQ_QUEUE_NAME,
            connection=self.redis_conn,
            default_timeout=settings.JOB_TIMEOUT
        )
    
    def enqueue_job(self, func, *args, job_id: Optional[str] = None, **kwargs) -> Job:
        """Enqueue a job for background processing."""
        try:
            job = self.queue.enqueue(
                func,
                *args,
                job_id=job_id,
                job_timeout=settings.JOB_TIMEOUT,
                **kwargs
            )
            logger.info(f"Job enqueued: {job.id}")
            return job
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            raise
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        try:
            return Job.fetch(job_id, connection=self.redis_conn)
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            return None
    
    def get_queue_length(self) -> int:
        """Get number of jobs in queue."""
        return len(self.queue)
    
    def get_failed_jobs(self) -> List[Job]:
        """Get list of failed jobs."""
        return self.queue.failed_job_registry.get_job_ids()
    
    def clear_queue(self) -> None:
        """Clear all jobs from queue (for testing)."""
        self.queue.empty()
        logger.info("Queue cleared")

def create_worker(queue_names: Optional[List[str]] = None) -> Worker:
    """Create RQ worker instance."""
    if queue_names is None:
        queue_names = [settings.RQ_QUEUE_NAME]
    
    redis_conn = get_redis()
    queues = [Queue(name, connection=redis_conn) for name in queue_names]
    
    worker = Worker(
        queues,
        connection=redis_conn,
        name=f"worker-{settings.RQ_QUEUE_NAME}"
    )
    
    logger.info(f"Worker created for queues: {queue_names}")
    return worker

# Global queue manager instance (lazy initialization)
_queue_manager_instance = None

def get_queue_manager() -> QueueManager:
    """Get queue manager instance (lazy initialization)."""
    global _queue_manager_instance
    if _queue_manager_instance is None:
        _queue_manager_instance = QueueManager()
    return _queue_manager_instance