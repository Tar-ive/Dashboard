from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class DreamTeamRequest(BaseModel):
    solicitation_id: str
    max_team_size: Optional[int] = 4
    guaranteed_top_n: Optional[int] = 2
    strategy: Optional[str] = "hybrid"  # "hybrid", "greedy", "rankings"
    marginal_threshold: Optional[float] = 0.25

class DreamTeamMember(BaseModel):
    researcher_id: str
    name: str
    role: str  # "PI", "Co-I 1", "Co-I 2", etc.
    avg_affinity: float
    top_skills: List[Dict[str, Any]]  # [{"skill": "...", "score": 123.4}]
    selection_reason: str

class SkillCoverage(BaseModel):
    skill: str
    coverage_score: float
    level: str  # "High", "Medium", "Low"
    expert: str  # Best team member for this skill
    expert_score: float

class SelectionStep(BaseModel):
    step: int
    action: str
    researcher_name: str
    reason: str
    team_coverage: float

class DreamTeamReport(BaseModel):
    solicitation_id: str
    solicitation_title: str
    team_members: List[DreamTeamMember]
    overall_coverage_score: float
    skill_analysis: List[SkillCoverage]
    strategic_analysis: str
    selection_history: List[SelectionStep]
    strategy_used: str
    generated_at: datetime
    affinity_matrix_shape: tuple  # (researchers, skills)

class AffinityMatrixExport(BaseModel):
    solicitation_id: str
    researchers: List[str]
    skills: List[str]
    matrix: List[List[float]]  # 2D array as list of lists
    generated_at: datetime

class TeamComparison(BaseModel):
    solicitation_id: str
    strategies: Dict[str, Dict]  # strategy_name -> {coverage, team_members}
    recommended_strategy: str
    comparison_notes: str