# Requirements Document

## Introduction

This feature implements a comprehensive data pipeline to populate a Supabase database with Texas State University researcher information from the OpenAlex API. The system will fetch institution data, researcher profiles, their complete publication histories, generate vector embeddings for publications, and populate five interconnected database tables to support research analysis and evidence indexing.

## Requirements

### Requirement 1

**User Story:** As a research administrator, I want to automatically populate our database with all current Texas State University researchers and their publications, so that I can analyze institutional research output and capabilities.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL connect to the Supabase database using the provided DATABASE_URL
2. WHEN the system initializes THEN it SHALL load the sentence-transformer model for generating 384-dimension embeddings
3. WHEN fetching institution data THEN the system SHALL query the OpenAlex API for "Texas State University" and retrieve its unique OpenAlex ID
4. WHEN institution data is retrieved THEN the system SHALL insert or update the institution record in the institutions table
5. IF the institution already exists THEN the system SHALL update the existing record rather than create a duplicate

### Requirement 2

**User Story:** As a data analyst, I want to retrieve all researchers affiliated with Texas State University, so that I can build comprehensive faculty profiles with their academic metrics.

#### Acceptance Criteria

1. WHEN fetching researchers THEN the system SHALL use the institution's OpenAlex ID to query for all affiliated authors
2. WHEN processing each researcher THEN the system SHALL extract their full name, h-index, and department information
3. WHEN researcher data is incomplete THEN the system SHALL handle missing department information gracefully by storing NULL values
4. WHEN inserting researcher data THEN the system SHALL use upsert operations to handle existing records
5. WHEN a researcher already exists THEN the system SHALL update their profile with the latest information from OpenAlex

### Requirement 3

**User Story:** As a research analyst, I want to collect complete publication histories for each researcher, so that I can analyze their scholarly output and research impact.

#### Acceptance Criteria

1. WHEN processing each researcher THEN the system SHALL fetch all their publications using paginated API calls
2. WHEN retrieving publications THEN the system SHALL handle API rate limits by implementing appropriate delays
3. WHEN processing publication data THEN the system SHALL extract title, abstract, publication year, DOI, and citation count
4. IF a publication's abstract is missing THEN the system SHALL attempt to reconstruct it from the abstract_inverted_index
5. IF both abstract and abstract_inverted_index are missing THEN the system SHALL create a proxy abstract from curated_topics
6. WHEN storing publication data THEN the system SHALL use upsert operations based on the OpenAlex ID

### Requirement 4

**User Story:** As a machine learning engineer, I want to generate vector embeddings for each publication, so that I can enable semantic search and similarity analysis of research works.

#### Acceptance Criteria

1. WHEN processing each publication THEN the system SHALL generate a 384-dimension vector embedding from the title and abstract
2. WHEN creating embeddings THEN the system SHALL use the sentence-transformer model for consistent vector generation
3. WHEN the abstract is reconstructed or proxy-generated THEN the system SHALL still create embeddings using the available text
4. WHEN storing embeddings THEN the system SHALL use the pg_vector format compatible with Supabase
5. IF embedding generation fails THEN the system SHALL log the error and continue processing other publications

### Requirement 4.1

**User Story:** As a research analyst, I want to extract and store keywords from publication abstracts, so that I can perform keyword-based searches and analysis of research content.

#### Acceptance Criteria

1. WHEN processing each publication abstract THEN the system SHALL extract meaningful keywords from the text
2. WHEN abstracts average 300 words THEN the system SHALL break them down into relevant keywords and key phrases
3. WHEN storing keyword data THEN the system SHALL add a keywords field to the works table
4. WHEN keywords are extracted THEN the system SHALL store them as a structured format (JSON array or comma-separated string)
5. IF abstract is missing or reconstructed THEN the system SHALL still attempt keyword extraction from available text

### Requirement 5

**User Story:** As a topic analyst, I want to extract and store research topics for each publication, so that I can categorize and analyze research themes across the institution.

#### Acceptance Criteria

1. WHEN processing publication topics THEN the system SHALL parse the curated_topics JSON from OpenAlex
2. WHEN extracting topics THEN the system SHALL filter for primary topics with type "topic"
3. WHEN storing topic data THEN the system SHALL include the topic name, type, and confidence score
4. WHEN linking topics to publications THEN the system SHALL use the work_id foreign key relationship
5. IF topic data is malformed THEN the system SHALL log the error and skip that topic while continuing with others

### Requirement 6

**User Story:** As a grants administrator, I want to track historical grant information for researchers, so that I can analyze funding patterns and success rates.

#### Acceptance Criteria

1. WHEN researcher grant data is available THEN the system SHALL extract award ID, year, role, amount, and title
2. WHEN processing grant information THEN the system SHALL handle different role types (PI, Co-PI, etc.)
3. WHEN storing grant data THEN the system SHALL link grants to researchers using the researcher_id foreign key
4. IF grant data is incomplete THEN the system SHALL store available fields and mark missing fields as NULL
5. WHEN grant information is unavailable THEN the system SHALL continue processing without failing

### Requirement 7

**User Story:** As a system administrator, I want robust error handling and logging throughout the data pipeline, so that I can monitor the process and troubleshoot issues effectively.

#### Acceptance Criteria

1. WHEN API calls fail THEN the system SHALL implement retry logic with exponential backoff
2. WHEN database operations fail THEN the system SHALL log detailed error information and continue processing
3. WHEN processing large datasets THEN the system SHALL provide progress indicators and status updates
4. WHEN encountering data quality issues THEN the system SHALL log warnings but continue processing
5. WHEN the process completes THEN the system SHALL provide a summary of records processed and any errors encountered

### Requirement 8

**User Story:** As a developer, I want the system to be configurable and maintainable, so that I can easily modify parameters and extend functionality.

#### Acceptance Criteria

1. WHEN connecting to the database THEN the system SHALL use environment variables from python-dotenv
2. WHEN making API calls THEN the system SHALL include proper email identification for the polite pool
3. WHEN processing data THEN the system SHALL use configurable batch sizes and rate limits
4. WHEN extending functionality THEN the system SHALL follow modular design patterns for easy maintenance
5. WHEN running tests THEN the system SHALL include comprehensive test coverage for all major functions