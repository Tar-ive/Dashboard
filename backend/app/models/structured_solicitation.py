"""Data models for structured solicitation processing."""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class StructuredSolicitation(BaseModel):
    """Complete structured representation of a solicitation document."""
    
    # Model configuration using Pydantic v2 style
    model_config = ConfigDict(
        json_schema_extra={
            "description": "Structured representation of a solicitation document"
        }
    )
    
    # Required identification fields
    solicitation_id: str = Field(..., description="Unique identifier for the solicitation")
    award_title: str = Field(..., description="Title of the solicitation")
    
    # Extracted Metadata
    funding_ceiling: Optional[float] = Field(None, description="Maximum funding amount in dollars")
    project_duration_months: Optional[int] = Field(None, ge=1, description="Project duration in months")
    submission_deadline: Optional[datetime] = Field(None, description="Submission deadline date and time")
    
    # Extracted Rules
    pi_eligibility_rules: List[str] = Field(default_factory=list, description="Principal Investigator eligibility rules")
    institutional_limitations: List[str] = Field(default_factory=list, description="Institutional limitations")
    team_size_constraints: Optional[Dict[str, int]] = Field(None, description="Team size constraints by role")
    
    # Core Required Skills
    required_scientific_skills: List[str] = Field(default_factory=list, description="Required scientific skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")
    
    # Complete Text
    full_text: str = Field(..., description="Complete text of the solicitation")
    extracted_sections: Dict[str, str] = Field(default_factory=dict, description="Extracted sections by name")
    
    # Processing Metadata
    processing_time_seconds: float = Field(..., description="Time taken to process the solicitation")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of extraction (0-1)")
    created_at: datetime = Field(..., description="When the structured solicitation was created")
    
    @field_validator('solicitation_id', 'award_title', 'full_text')
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('project_duration_months')
    @classmethod
    def validate_positive_duration(cls, v: Optional[int]) -> Optional[int]:
        """Ensure project duration is positive."""
        if v is not None and v <= 0:
            raise ValueError("Project duration must be positive")
        return v
    
    @field_validator('extraction_confidence')
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        return v