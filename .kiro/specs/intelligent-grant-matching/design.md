# Design Document

## Overview

This design document outlines the implementation of an Intelligent Grant Matching Engine using a simplified FastAPI + RQ + Redis architecture. The system transforms raw NSF solicitation PDFs into structured data and assembles optimal research teams through two distinct, independently testable background tasks.

The design follows three core guiding principles:
- **Simplicity First**: Each background task has one clear responsibility
- **TDD is Law**: No logic written without failing tests first
- **Incremental Builds**: Build and validate each component in isolation before integration

## Architecture

### Core System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │     Redis       │    │   RQ Worker     │
│   (Web Server)  │    │   (Broker &     │    │  (Background    │
│                 │    │  State Manager) │    │   Processor)    │
│                 │    │                 │    │                 │
│ • POST /deconstruct │◄──►│ • Job queue     │◄──►│ • deconstruct_  │
│ • POST /assemble-team│    │ • Job status    │    │   solicitation_ │
│ • GET /jobs/{id}    │    │ • Results store │    │   task          │
│ • Return job_id     │    │                 │    │ • assemble_     │
└─────────────────┘    └─────────────────┘    │   dream_team_   │
                                               │   task          │
                                               └─────────────────┘
```

### Two-Milestone Development Approach

**Milestone 1: Solicitation Deconstruction Task**
- Transform raw PDF → structured JSON object
- Independent, testable component
- Foundation for Milestone 2

**Milestone 2: Dream Team Assembly Task**  
- Consume structured solicitation → optimal team report
- Depends on Milestone 1 output
- Complete end-to-end workflow

## Components and Interfaces

### API Endpoints

**Core Endpoints**:
```python
POST /deconstruct
- Accept: multipart/form-data (PDF file)
- Return: {"job_id": "uuid", "status": "queued"}
- Enqueues: deconstruct_solicitation_task

POST /assemble-team  
- Accept: {"solicitation_id": "uuid", "parameters": {...}}
- Return: {"job_id": "uuid", "status": "queued"}
- Enqueues: assemble_dream_team_task

GET /jobs/{job_id}
- Return: JobStatus with current state and results
- Redis lookup for job state and results
```

### Data Models

**Milestone 1 Models**:
```python
class StructuredSolicitation(BaseModel):
    """Source of truth for solicitation data"""
    solicitation_id: str
    
    # Extracted Metadata
    award_title: str
    funding_ceiling: Optional[float]
    project_duration_months: Optional[int]
    submission_deadline: Optional[datetime]
    
    # Extracted Rules
    pi_eligibility_rules: List[str]
    institutional_limitations: List[str]
    team_size_constraints: Optional[Dict[str, int]]
    
    # Core Required Skills
    required_scientific_skills: List[str]
    preferred_skills: List[str]
    
    # Complete Text
    full_text: str
    extracted_sections: Dict[str, str]  # section_name -> content
    
    # Processing Metadata
    processing_time_seconds: float
    extraction_confidence: float
    created_at: datetime

class DeconstructionJob(BaseModel):
    job_id: str
    file_path: str
    status: str  # "queued", "processing", "completed", "failed"
    result: Optional[StructuredSolicitation] = None
    error_message: Optional[str] = None
```

**Milestone 2 Models**:
```python
class ProposedTeamMember(BaseModel):
    researcher_id: str
    name: str
    role: str  # "PI", "Co-PI", "Senior Personnel"
    justification: str
    affinity_scores: Dict[str, float]  # skill -> score
    avg_affinity: float

class DreamTeamReport(BaseModel):
    solicitation_id: str
    job_id: str
    
    # Proposed Team
    team_members: List[ProposedTeamMember]
    team_coverage_score: float  # 0-100
    
    # Gap Analysis (from LLM)
    gap_analysis: Dict[str, Any]
    strategic_recommendations: List[str]
    risk_assessment: str
    
    # Processing Metadata
    total_researchers_evaluated: int
    algorithm_used: str
    processing_time_seconds: float
    created_at: datetime

class AssemblyJob(BaseModel):
    job_id: str
    solicitation_id: str
    parameters: Dict[str, Any]
    status: str
    result: Optional[DreamTeamReport] = None
    error_message: Optional[str] = None
```

### Background Tasks

**Milestone 1: deconstruct_solicitation_task**
```python
def deconstruct_solicitation_task(job_id: str, file_path: str) -> StructuredSolicitation:
    """
    Transform PDF into structured solicitation object
    
    Steps:
    1. Extract full text using PDF library (PyMuPDF)
    2. Chunk text by section headers ("Eligibility", "Award Information", etc.)
    3. Send each chunk to LLM for targeted extraction
    4. Assemble structured solicitation object
    5. Store result in Redis
    """
    # Implementation follows TDD approach
    pass

def _extract_pdf_text(file_path: str) -> str:
    """Pure function for PDF text extraction"""
    pass

def _chunk_by_sections(text: str) -> Dict[str, str]:
    """Pure function for section identification"""
    pass

def _extract_metadata_with_llm(section_text: str, section_type: str) -> Dict[str, Any]:
    """LLM-powered data extraction"""
    pass
```

**Milestone 2: assemble_dream_team_task**
```python
def assemble_dream_team_task(job_id: str, solicitation_id: str, 
                           parameters: Dict[str, Any]) -> DreamTeamReport:
    """
    Assemble optimal research team for solicitation
    
    Steps:
    1. Load structured solicitation object
    2. Load researcher profiles from datastore
    3. Calculate affinity scores (pure functions)
    4. Run greedy team-building algorithm
    5. Apply constraint filters
    6. Generate gap analysis with LLM
    7. Return final strategic report
    """
    pass

def _calculate_affinity_score(researcher: Dict, skill: str) -> float:
    """Pure function for affinity calculation"""
    pass

def _greedy_team_selection(researchers: List[Dict], 
                          constraints: Dict) -> List[Dict]:
    """Pure function for team selection"""
    pass

def _generate_gap_analysis_with_llm(team_data: Dict, 
                                  solicitation_data: Dict) -> Dict[str, Any]:
    """LLM-powered gap analysis"""
    pass
```

## TDD Development Workflow

### Milestone 1 TDD Cycle

**RED Phase - Write Failing Tests**:
```python
# test_deconstruct_endpoint.py
def test_deconstruct_endpoint_returns_job_id():
    # Test POST /deconstruct endpoint
    # Should fail - endpoint doesn't exist yet
    pass

# test_deconstruction_task.py  
def test_deconstruct_solicitation_task():
    # Mock PDF file, LLM calls
    # Test task returns StructuredSolicitation
    # Should fail - task not implemented
    pass

# test_pdf_extraction.py
def test_extract_pdf_text():
    # Test pure function with sample PDF
    # Should fail - function not implemented
    pass
```

**GREEN Phase - Minimal Implementation**:
```python
# app/api/deconstruct.py
@router.post("/deconstruct")
async def deconstruct_solicitation(file: UploadFile):
    job_id = str(uuid.uuid4())
    # Save file, enqueue task, return job_id
    return {"job_id": job_id, "status": "queued"}

# app/tasks/deconstruction.py
def deconstruct_solicitation_task(job_id: str, file_path: str):
    # Minimal implementation to pass tests
    # Mock LLM calls initially
    pass
```

**REFACTOR Phase - Clean Implementation**:
- Add error handling
- Improve code structure
- Add logging and monitoring

### Milestone 2 TDD Cycle

**RED Phase - Write Failing Tests**:
```python
# test_scoring_functions.py
def test_calculate_affinity_score():
    # Test pure scoring functions
    # Should fail - functions not implemented
    pass

# test_assemble_team_endpoint.py
def test_assemble_team_endpoint():
    # Test POST /assemble-team
    # Should fail - endpoint doesn't exist
    pass

# test_assembly_task.py
def test_assemble_dream_team_task():
    # Mock solicitation data, researcher profiles
    # Should fail - task not implemented
    pass
```

**GREEN Phase - Minimal Implementation**:
```python
# Implement scoring functions as pure functions
# Create /assemble-team endpoint
# Implement basic assembly task logic
```

**REFACTOR Phase - Polish Implementation**:
- Optimize algorithms
- Add comprehensive error handling
- Integrate real LLM calls

## Testing Strategy

### Unit Testing Approach

**Pure Function Testing**:
```python
# Test mathematical functions in isolation
def test_affinity_calculation():
    researcher = {"skills": ["AI", "ML"], "experience": 5}
    skill = "AI"
    score = calculate_affinity_score(researcher, skill)
    assert 0 <= score <= 1

# Test data transformation functions
def test_section_chunking():
    sample_text = "...Eligibility...Award Information..."
    sections = chunk_by_sections(sample_text)
    assert "Eligibility" in sections
    assert "Award Information" in sections
```

**API Endpoint Testing**:
```python
def test_deconstruct_endpoint_immediate_response():
    response = client.post("/deconstruct", files={"file": sample_pdf})
    assert response.status_code == 200
    assert "job_id" in response.json()
    # Should return immediately without processing
```

**Background Task Testing**:
```python
def test_deconstruction_task_with_mocks():
    # Mock PDF extraction
    # Mock LLM calls
    # Test task logic in isolation
    with patch('app.tasks.extract_pdf_text') as mock_extract:
        mock_extract.return_value = "sample text"
        result = deconstruct_solicitation_task("job123", "path/to/file")
        assert isinstance(result, StructuredSolicitation)
```

### Integration Testing with Postman

**Milestone 1 Postman Workflow**:
```
Collection: "Solicitation Deconstruction"

1. Upload PDF
   POST /deconstruct
   - Upload sample NSF solicitation PDF
   - Verify immediate job_id response
   - Store job_id for next requests

2. Check Job Status (Polling)
   GET /jobs/{{job_id}}
   - Poll every 5 seconds
   - Verify status progression: queued → processing → completed
   - Validate final StructuredSolicitation object

3. Redis Debugging
   - Manual Redis CLI commands
   - Verify job storage: redis-cli GET job:{{job_id}}:status
   - Check result storage: redis-cli GET job:{{job_id}}:result
```

**Milestone 2 Postman Workflow**:
```
Collection: "Dream Team Assembly"

1. Assemble Team
   POST /assemble-team
   - Use solicitation_id from Milestone 1
   - Verify immediate job_id response

2. Monitor Team Assembly
   GET /jobs/{{job_id}}
   - Poll for completion
   - Verify DreamTeamReport structure
   - Validate affinity matrices
   - Check gap analysis content

3. End-to-End Validation
   - Complete workflow: PDF → structured data → team report
   - Verify data consistency across milestones
```

## Error Handling and Job Management

### Job State Management

**Redis Storage Pattern**:
```
job:{job_id}:status     -> "queued|processing|completed|failed"
job:{job_id}:result     -> JSON serialized result object
job:{job_id}:error      -> Error message if failed
job:{job_id}:progress   -> Progress percentage (0-100)
job:{job_id}:metadata   -> Job metadata (created_at, etc.)
```

**Error Scenarios**:
```python
class JobError(BaseModel):
    job_id: str
    error_type: str  # "pdf_extraction", "llm_timeout", "data_validation"
    error_message: str
    timestamp: datetime
    retry_count: int

# Common error types:
# - PDF file corrupted or unreadable
# - LLM API timeout or rate limiting
# - Invalid solicitation_id reference
# - Researcher database unavailable
# - Constraint validation failures
```

## LLM Integration Points

### Milestone 1 LLM Usage

**Section-Specific Extraction**:
```python
def extract_eligibility_rules(section_text: str) -> List[str]:
    prompt = f"""
    Extract PI eligibility rules from this NSF solicitation section:
    
    {section_text}
    
    Return as JSON list of specific eligibility requirements.
    """
    # Call LLM API (Groq/Anthropic)
    # Parse JSON response
    # Return structured data

def extract_funding_details(section_text: str) -> Dict[str, Any]:
    prompt = f"""
    Extract funding information from this section:
    
    {section_text}
    
    Return JSON with: funding_ceiling, project_duration, submission_deadline
    """
    # Similar LLM processing
```

### Milestone 2 LLM Usage

**Gap Analysis Generation**:
```python
def generate_strategic_gap_analysis(team_data: Dict, 
                                  solicitation_data: Dict) -> Dict[str, Any]:
    prompt = f"""
    Analyze this research team for NSF solicitation competitiveness:
    
    SOLICITATION: {solicitation_data['award_title']}
    REQUIRED SKILLS: {solicitation_data['required_scientific_skills']}
    
    PROPOSED TEAM:
    {format_team_summary(team_data)}
    
    Provide strategic analysis including:
    - Critical skill gaps
    - Team strengths
    - Competitive positioning
    - Recommendations for improvement
    
    Return as structured JSON.
    """
    # Process with LLM
    # Return structured analysis
```

## Incremental Development Plan

### Phase 1: Foundation 
- Set up FastAPI + RQ + Redis infrastructure
- Implement basic job management system
- Create core data models
- Write foundational tests

### Phase 2: Milestone 1 
- TDD implementation of deconstruction task
- PDF text extraction
- Section chunking logic
- LLM integration for metadata extraction
- Postman testing workflow

### Phase 3: Milestone 1 Validation
- Integration testing
- Error handling refinement
- Performance optimization
- Documentation and examples

### Phase 4: Milestone 2 
- TDD implementation of assembly task
- Scoring algorithm development
- Team selection logic
- Gap analysis LLM integration

### Phase 5: End-to-End Integration 
- Complete workflow testing
- Performance tuning
- Production readiness
- Comprehensive documentation

## Success Metrics

**Technical Metrics**:
- API response time < 200ms for job enqueueing
- Background task completion within 2-5 minutes
- 95%+ test coverage for core logic
- Zero blocking operations in API layer

**Quality Metrics**:
- Structured solicitation extraction accuracy > 90%
- Team recommendation relevance validation
- Error handling coverage for all failure modes
- Postman workflow success rate > 95%

**Development Metrics**:
- TDD cycle compliance (red-green-refactor)
- Independent milestone validation
- Incremental feature delivery
- Clear separation of concerns