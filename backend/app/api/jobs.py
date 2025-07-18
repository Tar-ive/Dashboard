"""Job status API endpoints."""

from fastapi import APIRouter, HTTPException
from app.models.job import JobStatusResponse
from app.jobs.job_manager import get_job_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status and results."""
    try:
        job_manager = get_job_manager()
        status = job_manager.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/jobs/{job_id}")
async def cleanup_job(job_id: str):
    """Clean up job data (for testing/maintenance)."""
    try:
        job_manager = get_job_manager()
        # Check if job exists first
        status = job_manager.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job_manager.cleanup_job(job_id)
        return {"message": f"Job {job_id} cleaned up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")