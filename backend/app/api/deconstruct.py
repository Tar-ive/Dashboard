"""Deconstruct endpoint for PDF solicitation processing."""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.job import JobResponse, JobStatus
from app.jobs.job_manager import get_job_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["deconstruct"])

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/deconstruct", response_model=JobResponse)
async def deconstruct_solicitation(file: UploadFile = File(...)):
    """
    Upload a PDF solicitation for deconstruction into structured data.
    Returns job_id immediately without processing.
    """
    try:
        # Validate file format
        if not file.content_type == "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are accepted."
            )
        
        # Read file content to check size and validate
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({len(content)} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)."
            )
        
        # Validate file is not empty
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty. Please upload a valid PDF file."
            )
        
        # Create job
        job_manager = get_job_manager()
        job_id = job_manager.create_job("deconstruct")
        
        # Save file
        upload_dir = "data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{job_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Enqueue background task
        enqueue_deconstruct_task(job_id, file_path)
        
        logger.info(f"Deconstruct job created: {job_id} for file: {file.filename}")
        
        return JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            message="PDF uploaded successfully. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

def enqueue_deconstruct_task(job_id: str, file_path: str) -> None:
    """
    Enqueue deconstruction task for background processing.
    For testing purposes, this runs the task directly.
    In production, this should use RQ or similar queue system.
    """
    logger.info(f"Enqueuing deconstruct task for job {job_id} with file {file_path}")
    
    # Import here to avoid circular imports
    from app.tasks.deconstruction_task import deconstruct_solicitation_task
    import threading
    
    # Run task in background thread for testing
    def run_task():
        try:
            logger.info(f"Starting background task for job {job_id}")
            result = deconstruct_solicitation_task(job_id, file_path)
            logger.info(f"Background task completed for job {job_id}")
        except Exception as e:
            logger.error(f"Background task failed for job {job_id}: {e}")
    
    # Start background thread
    thread = threading.Thread(target=run_task)
    thread.daemon = True
    thread.start()
    logger.info(f"Background task thread started for job {job_id}")