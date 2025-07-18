# Design Document

## Overview

This design document outlines the implementation of a simplified FastAPI + RQ + Redis architecture for the NSF Researcher Matching API. The architecture moves heavy processing operations into background workers while enabling incremental development and testing with Postman.

The design emphasizes **simplicity and testability** - each component can be built, tested with Postman, and validated independently before moving to the next. This approach ensures rapid feedback and reduces complexity.

## Architecture

### New Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │     Redis       │    │   RQ Worker     │
│   (Web Server)  │    │   (Broker &     │    │  (Background    │
│                 │    │  State Manager) │    │   Processor)    │
│                 │    │                 │    │                 │
│ • Accept requests│◄──►│ • Job queue     │◄──►│ • Process jobs  │
│ • Validate data │    │ • Job status    │    │ • Update status │
│ • Enqueue jobs  │    │ • Results store │    │ • Store results │
│ • Return job ID │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**FastAPI (Web Server)**: 
- Accepts requests and validates data
- Enqueues jobs to Redis immediately
- Returns job ID for status tracking
- No heavy processing

**Redis (Broker & State Manager)**:
- Stores job queue for RQ workers
- Maintains job status and progress
- Stores final results
- Replaces in-memory sessions

**RQ Worker (Background Processor)**:
- Watches Redis for new jobs
- Executes heavy processing tasks
- Updates job status in Redis
- Stores results for API retrieval

### Simplified Test Structure

```
backend/tests/
├── conftest.py              # Basic fixtures and test client
├── test_job_enqueueing.py   # Test job creation and Redis storage
├── test_worker_tasks.py     # Test background task execution
├── test_api_endpoints.py    # Test API responses and job IDs
└── utils/
    └── test_helpers.py      # Simple test utilities
```

## Components and Interfaces

### Job Management System

**Job Models**:
```python
class JobRequest(BaseModel):
    job_type: str  # "analyze_pdf", "match_researchers", "assemble_team"
    file_path: Optional[str] = None
    parameters: Dict[str, Any] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    progress: int = 0  # 0-100
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

**API Endpoints**:
- `POST /upload` - Upload PDF and return job ID
- `GET /jobs/{job_id}/status` - Check job status and get results
- `POST /match` - Start matching job and return job ID
- `POST /assemble-team` - Start team assembly job and return job ID

### Background Task Functions

**Core Worker Tasks**:
```python
def analyze_pdf_task(job_id: str, file_path: str) -> Dict[str, Any]:
    """Extract and analyze PDF content"""
    
def match_researchers_task(job_id: str, solicitation_data: Dict) -> Dict[str, Any]:
    """Find matching researchers with comprehensive results"""
    return {
        "matches": [...],  # Researcher matches with scores
        "affinity_matrix": [...],  # Full affinity matrix for team analysis
        "accuracy_metrics": {
            "precision": 0.85,
            "recall": 0.78,
            "f1_score": 0.81,
            "confidence_score": 0.82
        },
        "evaluation_details": {
            "total_researchers_evaluated": 1500,
            "matching_algorithm": "hybrid_tfidf_semantic",
            "processing_time_seconds": 12.3
        }
    }
    
def assemble_team_task(job_id: str, match_results: Dict, params: Dict) -> Dict[str, Any]:
    """Assemble optimal research team with affinity analysis"""
    return {
        "recommended_team": [...],
        "affinity_matrix": [...],  # Team member affinity scores
        "team_metrics": {
            "diversity_score": 0.75,
            "collaboration_potential": 0.88,
            "expertise_coverage": 0.92
        }
    }
```

### Redis Integration

**Job Storage Pattern**:
- Job queue: `rq:queue:default`
- Job status: `job:{job_id}:status`
- Job results: `job:{job_id}:result`
- Job errors: `job:{job_id}:error`

## Data Models

### Simple Test Models

```python
class SimpleTestData(BaseModel):
    """Basic test data for validating job processing"""
    test_file_path: str
    expected_job_status: str
    expected_result_keys: List[str]

class PostmanTestCase(BaseModel):
    """Test case for Postman validation"""
    name: str
    endpoint: str
    method: str
    expected_status_code: int
    validation_steps: List[str]
```

## Error Handling

### Simple Error Scenarios

**Job Processing Errors**:
- Invalid file uploads (wrong format, too large)
- Worker task failures (processing errors)
- Redis connection issues
- Job timeout scenarios

**Error Response Format**:
```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    job_id: Optional[str] = None
```

## Testing Strategy

### Simple TDD Workflow

1. **Red Phase**: Write failing test for job enqueueing/worker task
2. **Green Phase**: Write minimal code to make test pass
3. **Refactor Phase**: Clean up code while keeping tests green

### Postman Testing Workflow

**Step 1: Test Job Enqueueing**
```
POST /upload
- Upload test PDF file
- Verify immediate response with job_id
- Check Redis for job creation: redis-cli GET job:{job_id}:status
```

**Step 2: Test Job Status Checking**
```
GET /jobs/{job_id}/status
- Check job status (should be "queued" initially)
- Verify response format matches JobStatus model
- Monitor status changes as worker processes job
```

**Step 3: Test Background Processing**
```
1. Start RQ worker: rq worker
2. Upload file via Postman
3. Monitor job status changes: queued → processing → completed
4. Verify final results in GET /jobs/{job_id}/status
5. Validate affinity_matrix is present and properly formatted
6. Check accuracy_metrics contain precision, recall, f1_score
7. Verify evaluation_details include processing time and algorithm info
```

### Simple Automated Tests

**Unit Tests**:
- Test job creation in Redis
- Test worker task functions in isolation
- Test API endpoint responses

**Integration Tests**:
- Test complete workflow: upload → process → results
- Test error handling scenarios
- Test Redis connection and job storage

## Postman Collection Structure

### Collection: "FastAPI + RQ + Redis Testing"

**Folder 1: Job Enqueueing**
- Upload PDF File
- Check Initial Job Status
- Verify Redis Job Creation

**Folder 2: Background Processing**
- Monitor Job Progress
- Check Completed Job Results
- Test Error Scenarios

**Folder 3: End-to-End Workflows**
- Complete PDF Analysis Flow
- Complete Matching Flow
- Complete Team Assembly Flow

### Redis Debugging Commands

**Check Job Status**:
```bash
redis-cli GET job:{job_id}:status
redis-cli GET job:{job_id}:result
redis-cli GET job:{job_id}:error
```

**Monitor Job Queue**:
```bash
redis-cli LLEN rq:queue:default
redis-cli LRANGE rq:queue:default 0 -1
```