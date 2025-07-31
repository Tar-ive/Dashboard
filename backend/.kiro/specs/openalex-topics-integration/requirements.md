# Requirements Document

## Introduction

The current pipeline is failing to process topics from OpenAlex because it's trying to extract topics from individual work records, but OpenAlex has a separate topics API endpoint that needs to be used. This feature will implement proper topics integration by fetching topics from the dedicated OpenAlex topics API and associating them with works through the topics field in work records.

## Requirements

### Requirement 1

**User Story:** As a researcher data pipeline, I want to fetch topics from the OpenAlex topics API, so that I can properly categorize and analyze research works by their subject areas.

#### Acceptance Criteria

1. WHEN the pipeline processes works THEN the system SHALL fetch topics from the OpenAlex topics API endpoint
2. WHEN fetching topics THEN the system SHALL use the correct API endpoint `https://api.openalex.org/topics`
3. WHEN processing topics THEN the system SHALL handle pagination using cursor-based navigation
4. WHEN storing topics THEN the system SHALL store topic metadata including display_name, description, and OpenAlex ID

### Requirement 2

**User Story:** As a data processor, I want to associate topics with works through the topics field in work records, so that each work can be properly categorized by its research topics.

#### Acceptance Criteria

1. WHEN processing a work record THEN the system SHALL extract topic IDs from the work's topics field
2. WHEN a work has topics THEN the system SHALL create associations between the work and each topic
3. WHEN a topic is referenced but not yet stored THEN the system SHALL fetch the topic details from the topics API
4. WHEN storing work-topic associations THEN the system SHALL include the relevance score for each topic

### Requirement 3

**User Story:** As a pipeline administrator, I want the topics processing to be efficient and avoid duplicate API calls, so that the pipeline runs quickly and respects API rate limits.

#### Acceptance Criteria

1. WHEN processing multiple works THEN the system SHALL cache topic data to avoid duplicate API calls
2. WHEN fetching topics THEN the system SHALL respect the OpenAlex rate limiting requirements
3. WHEN a topic is already cached THEN the system SHALL use the cached data instead of making a new API call
4. WHEN the pipeline completes THEN the system SHALL report the number of unique topics processed

### Requirement 4

**User Story:** As a data analyst, I want topics to be properly validated and stored with complete metadata, so that I can perform accurate research analysis and categorization.

#### Acceptance Criteria

1. WHEN storing a topic THEN the system SHALL validate that required fields (id, display_name) are present
2. WHEN a topic has a description THEN the system SHALL store the description field
3. WHEN a topic has subfields or domain information THEN the system SHALL store this hierarchical data
4. WHEN topic data is invalid or incomplete THEN the system SHALL log the error and continue processing other topics

### Requirement 5

**User Story:** As a pipeline user, I want to test the topics integration with a smaller dataset first, so that I can verify the implementation works correctly before processing large datasets.

#### Acceptance Criteria

1. WHEN running the test pipeline THEN the system SHALL support a configurable limit for the number of researchers to process
2. WHEN testing with 5 researchers THEN the system SHALL successfully process all topics for their works
3. WHEN the test completes THEN the system SHALL report topics processing statistics including success rate
4. WHEN topics processing fails THEN the system SHALL provide detailed error messages for debugging