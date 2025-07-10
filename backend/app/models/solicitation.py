from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SolicitationUpload(BaseModel):
    filename: str
    content_type: str

class SolicitationResponse(BaseModel):
    solicitation_id: str
    filename: str
    status: str  # "processing", "completed", "failed"
    upload_time: datetime
    file_size: int

class SolicitationAnalysis(BaseModel):
    solicitation_id: str
    filename: str
    title: str
    abstract: str
    text_length: int
    processing_time_seconds: float
    sections_found: List[str]
    extracted_at: datetime

class SolicitationError(BaseModel):
    solicitation_id: str
    error_type: str
    error_message: str
    timestamp: datetime