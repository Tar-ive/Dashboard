from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class ReportFormat(str, Enum):
    """Available report export formats"""
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    HTML = "html"

class GapSeverity(str, Enum):
    """Severity levels for skill gaps"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CompetitivenessLevel(str, Enum):
    """Team competitiveness levels"""
    EXCELLENT = "excellent"
    STRONG = "strong"
    COMPETITIVE = "competitive"
    DEVELOPING = "developing"
    WEAK = "weak"

class SkillGap(BaseModel):
    """Individual skill gap analysis"""
    skill_name: str = Field(..., description="Name of the skill with gap")
    current_coverage: float = Field(..., ge=0, le=100, description="Current team coverage percentage")
    required_coverage: float = Field(default=75.0, ge=0, le=100, description="Target coverage percentage")
    gap_size: float = Field(..., description="Size of the gap (required - current)")
    severity: GapSeverity = Field(..., description="Severity level of this gap")
    impact_description: str = Field(..., description="Description of potential impact")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Suggested ways to address this gap")

class StrategicRecommendation(BaseModel):
    """Strategic recommendation for team improvement"""
    category: str = Field(..., description="Category of recommendation (e.g., 'Collaboration', 'Recruitment')")
    priority: str = Field(..., description="Priority level (High, Medium, Low)")
    title: str = Field(..., description="Brief title of the recommendation")
    description: str = Field(..., description="Detailed description of the recommendation")
    implementation_effort: str = Field(..., description="Effort required (Low, Medium, High)")
    timeline: str = Field(..., description="Suggested timeline for implementation")
    expected_impact: str = Field(..., description="Expected impact on team capability")
    success_metrics: List[str] = Field(default_factory=list, description="How to measure success")

class RiskAssessment(BaseModel):
    """Risk assessment for the proposed team"""
    overall_risk_level: str = Field(..., description="Overall risk level (Low, Medium, High)")
    technical_risks: List[str] = Field(default_factory=list, description="Technical/expertise risks")
    collaboration_risks: List[str] = Field(default_factory=list, description="Team collaboration risks")
    timeline_risks: List[str] = Field(default_factory=list, description="Project timeline risks")
    mitigation_plans: List[str] = Field(default_factory=list, description="Risk mitigation strategies")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in team success (0-100)")

class CompetitivenessAnalysis(BaseModel):
    """Analysis of team competitiveness"""
    overall_score: float = Field(..., ge=0, le=100, description="Overall competitiveness score")
    competitiveness_level: CompetitivenessLevel = Field(..., description="Competitiveness level")
    strengths: List[str] = Field(default_factory=list, description="Key competitive strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas of competitive weakness")
    differentiators: List[str] = Field(default_factory=list, description="Unique competitive advantages")
    benchmark_comparison: Dict[str, float] = Field(default_factory=dict, description="Comparison to typical successful teams")
    funding_probability: float = Field(..., ge=0, le=100, description="Estimated probability of funding success")

class GapAnalysisReport(BaseModel):
    """AI-generated comprehensive gap analysis"""
    solicitation_id: str = Field(..., description="ID of the solicitation being analyzed")
    team_id: str = Field(..., description="ID of the dream team")
    analysis_date: datetime = Field(default_factory=datetime.now, description="When analysis was generated")
    
    # Core Gap Analysis
    critical_gaps: List[SkillGap] = Field(default_factory=list, description="Critical skill gaps requiring immediate attention")
    moderate_gaps: List[SkillGap] = Field(default_factory=list, description="Moderate gaps that should be addressed")
    minor_gaps: List[SkillGap] = Field(default_factory=list, description="Minor gaps with low impact")
    
    # Strategic Analysis
    strategic_recommendations: List[StrategicRecommendation] = Field(default_factory=list, description="AI-generated strategic recommendations")
    risk_assessment: RiskAssessment = Field(..., description="Comprehensive risk assessment")
    competitiveness_analysis: CompetitivenessAnalysis = Field(..., description="Team competitiveness analysis")
    
    # AI Analysis Metadata
    ai_confidence_score: float = Field(..., ge=0, le=100, description="AI confidence in the analysis")
    analysis_model: str = Field(default="claude-3-sonnet", description="AI model used for analysis")
    analysis_tokens_used: Optional[int] = Field(None, description="Number of tokens used in analysis")

class ExecutiveSummary(BaseModel):
    """Executive summary of the team analysis"""
    team_overview: str = Field(..., description="Brief overview of the assembled team")
    key_strengths: List[str] = Field(..., description="Top 3-5 key strengths")
    primary_concerns: List[str] = Field(..., description="Top 3-5 areas of concern")
    bottom_line_assessment: str = Field(..., description="Bottom line recommendation")
    confidence_level: str = Field(..., description="Overall confidence level")
    next_steps: List[str] = Field(..., description="Recommended immediate next steps")

class SupportingEvidence(BaseModel):
    """Supporting evidence for team capabilities"""
    researcher_id: str = Field(..., description="Researcher's OpenAlex ID")
    researcher_name: str = Field(..., description="Researcher's name")
    skill_area: str = Field(..., description="Skill area this evidence supports")
    evidence_type: str = Field(..., description="Type of evidence (publication, grant, etc.)")
    title: str = Field(..., description="Title of the supporting work")
    year: Optional[int] = Field(None, description="Year of the work")
    citation_count: Optional[int] = Field(None, description="Number of citations")
    relevance_score: float = Field(..., ge=0, le=100, description="Relevance to the skill area")
    description: str = Field(..., description="Brief description of relevance")

class DataExport(BaseModel):
    """Structured data export"""
    export_type: str = Field(..., description="Type of data being exported")
    column_headers: List[str] = Field(..., description="Column headers for tabular data")
    data_rows: List[List[Any]] = Field(..., description="Data rows")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ComprehensiveReport(BaseModel):
    """Complete comprehensive report"""
    # Basic Metadata
    report_id: str = Field(..., description="Unique report identifier")
    solicitation_id: str = Field(..., description="Solicitation being analyzed")
    team_id: str = Field(..., description="Dream team identifier")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation timestamp")
    generated_by: str = Field(default="NSF Matching System v1.0", description="System that generated the report")
    
    # Core Content
    executive_summary: ExecutiveSummary = Field(..., description="Executive summary")
    gap_analysis: GapAnalysisReport = Field(..., description="Comprehensive gap analysis")
    
    # Team Analysis
    team_composition: Dict[str, Any] = Field(..., description="Detailed team composition analysis")
    coverage_analysis: Dict[str, Any] = Field(..., description="Skill coverage analysis")
    affinity_scores: Dict[str, float] = Field(..., description="Team member affinity scores")
    
    # Supporting Data
    supporting_evidence: List[SupportingEvidence] = Field(default_factory=list, description="Evidence supporting team capabilities")
    data_exports: Dict[str, DataExport] = Field(default_factory=dict, description="Structured data for export")
    
    # Report Options
    include_charts: bool = Field(default=True, description="Whether to include charts in exports")
    include_raw_data: bool = Field(default=False, description="Whether to include raw matching data")
    detail_level: str = Field(default="standard", description="Level of detail (brief, standard, detailed)")
    
    # Processing Metadata
    processing_time_seconds: float = Field(..., description="Time taken to generate report")
    total_researchers_analyzed: int = Field(..., description="Total researchers in analysis")
    ai_analysis_included: bool = Field(default=True, description="Whether AI analysis was included")

class ReportExport(BaseModel):
    """Report export in specific format"""
    report_id: str = Field(..., description="Source report ID")
    format_type: ReportFormat = Field(..., description="Export format")
    content: Union[str, bytes] = Field(..., description="Report content in requested format")
    file_size_bytes: int = Field(..., description="Size of exported content")
    mime_type: str = Field(..., description="MIME type of the export")
    filename: str = Field(..., description="Suggested filename for download")
    generated_at: datetime = Field(default_factory=datetime.now, description="Export generation time")
    
    # Export Metadata
    export_options: Dict[str, Any] = Field(default_factory=dict, description="Options used for export")
    page_count: Optional[int] = Field(None, description="Number of pages (for PDF)")
    word_count: Optional[int] = Field(None, description="Word count (for text formats)")

class ReportGenerationRequest(BaseModel):
    """Request for report generation"""
    team_id: str = Field(..., description="Team ID to generate report for")
    include_ai_analysis: bool = Field(default=True, description="Include AI-powered gap analysis")
    detail_level: str = Field(default="standard", description="Level of detail (brief, standard, detailed)")
    export_formats: List[ReportFormat] = Field(default=[ReportFormat.MARKDOWN], description="Formats to generate")
    include_charts: bool = Field(default=True, description="Include visualization charts")
    include_raw_data: bool = Field(default=False, description="Include raw data exports")
    custom_analysis_prompt: Optional[str] = Field(None, description="Custom prompt for AI analysis")

class ReportStatus(BaseModel):
    """Status of report generation"""
    report_id: str = Field(..., description="Report identifier")
    status: str = Field(..., description="Generation status (pending, processing, completed, failed)")
    progress_percent: int = Field(default=0, ge=0, le=100, description="Generation progress")
    current_step: str = Field(..., description="Current processing step")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Processing Details
    ai_analysis_status: str = Field(default="pending", description="Status of AI analysis")
    export_status: Dict[str, str] = Field(default_factory=dict, description="Status of each export format")
    
class ReportTemplate(BaseModel):
    """Template for report generation"""
    template_name: str = Field(..., description="Name of the template")
    template_type: str = Field(..., description="Type (executive, technical, full)")
    sections: List[str] = Field(..., description="Sections to include")
    format_options: Dict[str, Any] = Field(default_factory=dict, description="Formatting options")
    ai_prompt_template: str = Field(..., description="Template for AI analysis prompts")

# Response Models for API
class ReportListResponse(BaseModel):
    """Response for listing reports"""
    reports: List[Dict[str, Any]] = Field(..., description="List of available reports")
    total_count: int = Field(..., description="Total number of reports")
    generated_reports: int = Field(..., description="Number of completed reports")
    pending_reports: int = Field(..., description="Number of pending reports")

class ReportGenerationResponse(BaseModel):
    """Response for report generation request"""
    report_id: str = Field(..., description="Generated report ID")
    status: str = Field(..., description="Initial status")
    estimated_completion_minutes: int = Field(..., description="Estimated minutes to completion")
    polling_url: str = Field(..., description="URL to check generation status")
    message: str = Field(..., description="Human-readable status message")