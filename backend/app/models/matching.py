from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ResearcherMatch(BaseModel):
    researcher_id: str
    researcher_name: str
    academic_expertise_score: float
    s_sparse: float  # TF-IDF score
    s_dense: float   # Semantic similarity score
    f_ge: float      # Grant experience factor
    final_affinity_score: float
    total_papers: int
    eligibility_status: str

class MatchingRequest(BaseModel):
    solicitation_id: str
    top_n_results: Optional[int] = 20
    debug_mode: Optional[bool] = False

class MatchingResults(BaseModel):
    solicitation_id: str
    solicitation_title: str
    eligible_researchers: int
    total_researchers: int
    top_matches: List[ResearcherMatch]
    skills_analyzed: List[str]
    processing_time_seconds: float
    generated_at: datetime

class MatchingStatus(BaseModel):
    solicitation_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress_percent: Optional[int] = 0
    message: Optional[str] = None
    estimated_completion: Optional[datetime] = None