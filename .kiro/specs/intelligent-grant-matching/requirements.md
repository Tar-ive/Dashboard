# Requirements Document

## Introduction

This feature implements an Intelligent Grant Matching Engine using a simplified FastAPI + RQ + Redis architecture. The system transforms raw NSF solicitation PDFs into structured data and assembles optimal research teams through two distinct background tasks. The design emphasizes simplicity, testability, and incremental development with clear TDD workflows and comprehensive testing capabilities.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to implement FastAPI + RQ + Redis architecture with job enqueueing, so that heavy processing operations don't block API responses and I can test each step incrementally with Postman.

#### Acceptance Criteria

1. WHEN I upload a PDF THEN the API SHALL immediately return a job ID without processing the file
2. WHEN I check job status THEN Redis SHALL store and return the current status and results
3. WHEN I test with Postman THEN I SHALL have clear endpoints to upload files and check job status
4. WHEN multiple requests arrive THEN they SHALL be queued in Redis for background processing
5. IF I need to debug THEN I SHALL have Redis CLI commands to inspect job states

### Requirement 2

**User Story:** As a developer, I want to implement RQ background workers that return comprehensive matching results including affinity matrices and accuracy measures, so that I can validate the quality of recommendations and ensure the system provides actionable insights.

#### Acceptance Criteria

1. WHEN heavy processing occurs THEN it SHALL happen in a separate RQ worker process
2. WHEN matching is completed THEN results SHALL include the full affinity matrix for team analysis
3. WHEN matching is completed THEN results SHALL include accuracy measures and evaluation metrics
4. WHEN I test background processing THEN I SHALL have Postman requests to verify affinity matrix and accuracy data
5. WHEN a worker fails THEN the job status SHALL reflect the failure with appropriate error messages
6. IF I need to verify worker execution THEN I SHALL have step-by-step Postman procedures to validate result quality

### Requirement 3

**User Story:** As a developer, I want simplified automated tests for the new architecture, so that I can build with confidence using TDD while keeping tests maintainable and focused.

#### Acceptance Criteria

1. WHEN I write new code THEN I SHALL write tests first following TDD red-green-refactor cycle
2. WHEN I test job enqueueing THEN unit tests SHALL verify Redis job creation simply
3. WHEN I test worker functions THEN tests SHALL validate background task execution without complexity
4. WHEN I test API endpoints THEN tests SHALL verify immediate responses with job IDs
5. IF tests become complex THEN they SHALL be refactored to focus on essential functionality only

### Requirement 4

**User Story:** As a user, I want to upload a solicitation PDF and receive a structured JSON object containing its key requirements, rules, and scientific objectives, so that I can have machine-readable solicitation data for further processing.

#### Acceptance Criteria

1. WHEN I upload a PDF via POST /deconstruct THEN the system SHALL immediately return a job_id without blocking
2. WHEN the deconstruction task processes the PDF THEN it SHALL extract full text using a PDF library
3. WHEN text is extracted THEN the system SHALL chunk text by searching for key section headers (e.g., "Eligibility," "Award Information")
4. WHEN text chunks are identified THEN each chunk SHALL be sent to an LLM for targeted data extraction
5. WHEN LLM processing completes THEN the system SHALL assemble a structured solicitation object containing:
   - Extracted metadata (solicitation ID, award title, funding ceiling, project duration)
   - Extracted rules (PI eligibility rules, institutional limitations)
   - Core required scientific skills
   - Complete text for contextual analysis
6. WHEN I check job status THEN I SHALL receive the structured JSON object as the final result
7. IF the PDF cannot be processed THEN the system SHALL return appropriate error messages with failure status

### Requirement 5

**User Story:** As a user, I want to request a "Dream Team" for a deconstructed solicitation and receive a final report that includes the proposed team and a strategic gap analysis, so that I can make informed decisions about team composition for grant applications.

#### Acceptance Criteria

1. WHEN I submit a solicitation_id via POST /assemble-team THEN the system SHALL immediately return a job_id without blocking
2. WHEN the dream team assembly task starts THEN it SHALL load the corresponding structured solicitation object from Milestone 1
3. WHEN solicitation data is loaded THEN the system SHALL load all researcher profiles from the datastore
4. WHEN researcher data is available THEN the system SHALL calculate final affinity scores for each researcher against each required skill
5. WHEN affinity scores are calculated THEN the system SHALL run the greedy team-building algorithm while applying constraint filters from the solicitation object
6. WHEN team candidates are selected THEN the system SHALL prepare a dossier for final "Gap Analysis" LLM agent
7. WHEN gap analysis completes THEN the system SHALL return a final strategic report containing:
   - List of proposed team members (ID, name, role, justification)
   - Team coverage score
   - Full gap analysis from the LLM call
8. IF any step fails THEN the system SHALL provide detailed error information and failure status