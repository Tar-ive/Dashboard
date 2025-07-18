# Implementation Plan

- [x] 1. Set up FastAPI + RQ + Redis infrastructure foundation
  - Create Redis connection and RQ worker configuration
  - Set up basic job management system with Redis storage patterns
  - Implement core JobStatus model and job state management
  - Write infrastructure tests for Redis connectivity and job enqueueing
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 2. Implement core job management API endpoints
  - [x] 2.1 Create GET /jobs/{job_id} status endpoint with TDD
    - Write failing test for job status retrieval from Redis
    - Implement minimal endpoint that returns job status and results
    - Add error handling for non-existent jobs
    - Test Redis job state lookup functionality
    - _Requirements: 1.2, 1.3_

  - [x] 2.2 Build job enqueueing utilities and Redis integration
    - Write tests for job creation and Redis storage
    - Implement job_id generation and Redis key management
    - Create utility functions for job state updates
    - Test job queue management and status transitions
    - _Requirements: 1.1, 1.4, 1.5_

- [-] 3. Implement Milestone 1: Solicitation Deconstruction Task
  - [x] 3.1 Create POST /deconstruct endpoint with TDD approach
    - Write failing test for PDF upload endpoint
    - Implement endpoint that accepts PDF file and returns job_id immediately
    - Add file validation (PDF format, size limits)
    - Test file saving and job enqueueing without processing
    - _Requirements: 4.1, 1.1, 1.3_

  - [x] 3.2 Build PDF text extraction as pure function
    - Write unit tests for PDF text extraction with sample files
    - Implement _extract_pdf_text() function using PyMuPDF
    - Test various PDF formats and handle extraction errors
    - Ensure function is testable in isolation with mocked file system
    - _Requirements: 4.2, 3.3_

  - [x] 3.3 Implement section chunking logic as pure function
    - Write tests for _chunk_by_sections() with known section headers
    - Implement text chunking by searching for key headers ("Eligibility", "Award Information")
    - Test edge cases (missing sections, malformed headers)
    - Validate section extraction accuracy with sample solicitations
    - _Requirements: 4.3, 3.3_

  - [x] 3.4 Create StructuredSolicitation data model and validation
    - Write tests for Pydantic model validation and serialization
    - Implement StructuredSolicitation model with all required fields
    - Test JSON serialization/deserialization for Redis storage
    - Validate model constraints and field validation rules
    - _Requirements: 4.5, 3.3_

  - [x] 3.5 Build LLM integration for metadata extraction
    - Write tests for _extract_metadata_with_llm() with mocked LLM responses
    - Implement LLM API calls for section-specific data extraction
    - Create prompt templates for eligibility rules, funding details, skills
    - Test LLM response parsing and error handling
    - _Requirements: 4.4, 2.5_

  - [x] 3.6 Implement complete deconstruct_solicitation_task
    - Write integration test for full task execution with mocked dependencies
    - Implement task orchestration: PDF extraction → chunking → LLM processing → assembly
    - Add comprehensive error handling and job status updates
    - Test task execution with real PDF files and validate output structure
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 2.1_

- [ ] 4. Create Milestone 1 Postman testing workflow
  - [x] 4.1 Build Postman collection for solicitation deconstruction
    - Create "Upload PDF" request with sample NSF solicitation file
    - Add "Check Job Status" request with polling automation
    - Include Redis debugging commands for manual verification
    - Test complete workflow: upload → poll → validate structured result
    - **FIXED ISSUES DURING IMPLEMENTATION:**
      - ✅ Switched LLM model from `llama-3.3-70b-versatile` to `meta-llama/llama-4-scout-17b-16e-instruct` (rate limit fix)
      - ✅ Implemented actual background task processing (was placeholder)
      - ✅ Fixed job manager API to use separate `store_job_result()` method
      - ✅ Updated API routes to include `/api` prefix
      - ✅ Added Redis installation and setup requirements
    - _Requirements: 1.3, 2.6_

  - [x] 4.1.5 Containerize the solicitation deconstruction API with OrbStack
    - Create comprehensive Dockerfile with all dependencies
    - Set up docker-compose.yml with Redis service
    - Configure environment variables for containerized deployment
    - Test complete workflow in OrbStack environment with Postman
    - Document OrbStack setup and usage instructions
    - _Requirements: 1.3, 2.6, 4.7_

  - [x] 4.2 Validate Milestone 1 integration and error scenarios
    - Test invalid PDF uploads and error handling
    - Verify job failure scenarios and error message clarity
    - Test concurrent PDF uploads and queue management
    - Validate StructuredSolicitation output format and completeness
    - _Requirements: 4.7, 2.5, 1.4_

- [ ] 5. Implement Milestone 2: Dream Team Assembly Task
  - [ ] 5.1 Create POST /assemble-team endpoint with TDD
    - Write failing test for team assembly endpoint
    - Implement endpoint that accepts solicitation_id and returns job_id
    - Add validation for solicitation_id existence and parameters
    - Test immediate response without blocking on team assembly
    - _Requirements: 5.1, 1.1, 1.3_

  - [ ] 5.2 Build affinity scoring functions as pure functions
    - Write comprehensive tests for _calculate_affinity_score() with known inputs
    - Implement mathematical scoring algorithm for researcher-skill affinity
    - Test edge cases (missing skills, zero experience, boundary conditions)
    - Validate scoring accuracy against expected researcher-skill matches
    - _Requirements: 5.4, 3.3_

  - [ ] 5.3 Implement greedy team selection algorithm
    - Write tests for _greedy_team_selection() with controlled researcher data
    - Implement team building algorithm with constraint filtering
    - Test team size constraints and role distribution requirements
    - Validate algorithm produces optimal team composition within constraints
    - _Requirements: 5.5, 3.3_

  - [ ] 5.4 Create DreamTeamReport data model and team member models
    - Write tests for ProposedTeamMember and DreamTeamReport validation
    - Implement Pydantic models with all required fields for team reporting
    - Test model serialization for Redis storage and API responses
    - Validate nested model relationships and data integrity
    - _Requirements: 5.7, 3.3_

  - [ ] 5.5 Build gap analysis LLM integration
    - Write tests for _generate_gap_analysis_with_llm() with mocked responses
    - Implement LLM integration for strategic team analysis
    - Create comprehensive prompt templates for gap analysis
    - Test LLM response parsing and strategic recommendation extraction
    - _Requirements: 5.6, 2.2, 2.3_

  - [ ] 5.6 Implement complete assemble_dream_team_task
    - Write integration test for full assembly task with mocked data loading
    - Implement task orchestration: load data → calculate scores → select team → gap analysis
    - Add error handling for missing solicitation data and researcher profiles
    - Test complete task execution and validate DreamTeamReport output
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 2.1_

- [ ] 6. Create Milestone 2 Postman testing workflow
  - [ ] 6.1 Build Postman collection for dream team assembly
    - Create "Assemble Team" request using solicitation_id from Milestone 1
    - Add "Monitor Assembly Progress" request with status polling
    - Include validation steps for affinity matrices and team metrics
    - Test gap analysis content and strategic recommendations
    - _Requirements: 1.3, 2.4, 2.6_

  - [ ] 6.2 Validate end-to-end workflow integration
    - Test complete pipeline: PDF upload → deconstruction → team assembly
    - Verify data consistency between milestones (solicitation_id references)
    - Test error propagation and handling across milestone boundaries
    - Validate final DreamTeamReport completeness and accuracy
    - _Requirements: 5.8, 2.2, 2.3, 2.4_

- [ ] 7. Implement comprehensive error handling and monitoring
  - [ ] 7.1 Add robust error handling for all failure scenarios
    - Test and handle PDF extraction failures (corrupted files, unsupported formats)
    - Implement LLM API timeout and rate limiting error handling
    - Add validation for missing or invalid solicitation_id references
    - Test researcher database connectivity and fallback mechanisms
    - _Requirements: 4.7, 5.8, 2.5_

  - [ ] 7.2 Build job monitoring and debugging capabilities
    - Implement detailed job progress tracking and status updates
    - Add comprehensive logging for background task execution
    - Create Redis debugging utilities and CLI commands
    - Test job failure recovery and retry mechanisms
    - _Requirements: 1.5, 2.5, 3.4_

- [ ] 8. Performance optimization and production readiness
  - [ ] 8.1 Optimize background task performance
    - Profile and optimize PDF processing and LLM API calls
    - Implement efficient researcher data loading and caching
    - Test concurrent job processing and resource utilization
    - Validate API response times meet performance requirements (<200ms)
    - _Requirements: 2.1, 2.2_

  - [ ] 8.2 Add comprehensive integration testing
    - Create automated test suite for complete workflow validation
    - Test system behavior under load with multiple concurrent requests
    - Validate Redis job storage and retrieval under stress
    - Test error recovery and system stability
    - _Requirements: 3.1, 3.2, 3.4_

- [ ] 9. Documentation and deployment preparation
  - [ ] 9.1 Create comprehensive API documentation
    - Document all endpoints with request/response examples
    - Create Postman collection documentation and usage guides
    - Add Redis debugging command reference
    - Document TDD workflow and testing procedures
    - _Requirements: 1.3, 3.5_

  - [ ] 9.2 Prepare production deployment configuration
    - Configure Redis and RQ worker deployment settings
    - Set up environment variables and configuration management
    - Create Docker containers for FastAPI app and RQ workers
    - Test deployment configuration and service orchestration
    - _Requirements: 1.4, 2.1_