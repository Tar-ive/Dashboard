"""Job status and management models."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobResponse(BaseModel):
    """Response model for job creation."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: Optional[str] = Field(None, description="Status message")

class JobStatusResponse(BaseModel):
    """Response model for job status queries."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[datetime] = Field(None, description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")

class JobError(BaseModel):
    """Job error information."""
    job_id: str = Field(..., description="Job identifier")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(..., description="Error timestamp")
    retry_count: int = Field(0, description="Number of retry attempts")

class JobMetadata(BaseModel):
    """Job metadata for storage."""
    job_id: str
    job_type: str  # "deconstruct" or "assemble_team"
    status: JobStatus
    progress: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True