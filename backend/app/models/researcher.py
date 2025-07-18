from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class Researcher(BaseModel):
    """Base researcher model for the system."""
    researcher_id: str
    name: str
    email: Optional[str] = None
    institution: str
    department: Optional[str] = None
    title: Optional[str] = None
    expertise: List[str] = Field(default_factory=list)
    publications: int = 0
    h_index: int = 0
    years_active: int = 0
    grants_received: int = 0
    collaboration_score: float = 0.0
    recent_activity: float = 0.0

class ResearcherProfile(BaseModel):
    """Extended researcher profile with additional metadata."""
    researcher_id: str
    name: str
    email: Optional[str] = None
    institution: str
    department: Optional[str] = None
    title: Optional[str] = None
    expertise: List[str] = Field(default_factory=list)
    publications: int = 0
    h_index: int = 0
    years_active: int = 0
    grants_received: int = 0
    collaboration_score: float = 0.0
    recent_activity: float = 0.0
    bio: Optional[str] = None
    website: Optional[str] = None
    orcid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ResearcherCreate(BaseModel):
    """Model for creating new researchers."""
    name: str
    email: Optional[str] = None
    institution: str
    department: Optional[str] = None
    title: Optional[str] = None
    expertise: List[str] = Field(default_factory=list)
    publications: int = 0
    h_index: int = 0
    years_active: int = 0
    grants_received: int = 0

class ResearcherUpdate(BaseModel):
    """Model for updating researcher information."""
    name: Optional[str] = None
    email: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    expertise: Optional[List[str]] = None
    publications: Optional[int] = None
    h_index: Optional[int] = None
    years_active: Optional[int] = None
    grants_received: Optional[int] = None
    collaboration_score: Optional[float] = None
    recent_activity: Optional[float] = None