# Requirements Document

## Introduction

This feature focuses on implementing a simplified FastAPI + RQ + Redis architecture for the NSF Researcher Matching API. The goal is to move heavy processing (PDF parsing, analysis, matching) out of the API process into background workers while creating essential automated tests and enabling incremental validation with Postman.

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