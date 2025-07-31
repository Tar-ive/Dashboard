# NSF Researcher Matching Database - Complete Schema Documentation

## Overview

This database contains comprehensive research data for Texas State University, with a specialized subset for the Computer Science Department (CADS). The system is designed to support advanced researcher matching, collaboration discovery, and research analytics.

## Database Architecture

### Technology Stack
- **Database**: PostgreSQL with Supabase
- **Vector Extension**: pgvector for semantic search capabilities
- **Connection**: IPv4 pooler for reliable connectivity
- **Data Source**: OpenAlex API for research metadata

## Core Database Schema

### 1. INSTITUTIONS Table
**Purpose**: Stores university and research institution data

```sql
CREATE TABLE institutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    openalex_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    ror_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 1 institution (Texas State University)
- **OpenAlex ID**: https://openalex.org/I13511017
- **ROR ID**: https://ror.org/05h9q1g27

### 2. RESEARCHERS Table (Main)
**Purpose**: Complete repository of all researchers from Texas State University

```sql
CREATE TABLE researchers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institution_id UUID NOT NULL REFERENCES institutions(id),
    openalex_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    h_index INTEGER,
    department TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 87 researchers
- **Coverage**: Multi-disciplinary across all departments
- **Metadata**: H-index, department affiliations, OpenAlex profiles
- **Examples**: Manfred Schartl (h-index: 87), Togay Ozbakkaloglu (h-index: 79)

### 3. WORKS Table (Main)
**Purpose**: Complete repository of all research publications

```sql
CREATE TABLE works (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id UUID NOT NULL REFERENCES researchers(id),
    openalex_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    keywords TEXT,
    publication_year INTEGER,
    doi TEXT,
    citations INTEGER DEFAULT 0,
    embedding VECTOR(384),  -- Semantic embeddings for similarity search
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 13,915 research works
- **Semantic Search**: 384-dimensional embeddings for each work
- **Keywords**: Extracted and processed from abstracts and concepts
- **Citation Data**: Citation counts from OpenAlex
- **Time Range**: Publications spanning multiple decades
- **DOI Coverage**: Digital Object Identifiers for publication linking

### 4. TOPICS Table (Main)
**Purpose**: Research topics and concepts extracted from publications

```sql
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work_id UUID NOT NULL REFERENCES works(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    score DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 14,428 research topics
- **Topic Extraction**: AI-powered topic identification from OpenAlex
- **Confidence Scores**: Relevance scores for each topic-work relationship
- **Examples**: "Cytokine Signaling Pathways", "thermodynamics and calorimetric analyses"

### 5. RESEARCHER_GRANTS Table
**Purpose**: Grant and funding information for researchers

```sql
CREATE TABLE researcher_grants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id UUID NOT NULL REFERENCES researchers(id),
    award_id TEXT NOT NULL,
    award_year INTEGER,
    role TEXT,
    award_amount BIGINT,
    award_title TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 0 grants (ready for future population)

## CADS-Specific Schema (Computer Science Department)

### 6. CADS_RESEARCHERS Table
**Purpose**: Specialized subset of Computer Science Department faculty

```sql
CREATE TABLE cads_researchers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institution_id UUID NOT NULL REFERENCES institutions(id),
    openalex_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    h_index INTEGER,
    department TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 32 CADS professors
- **Key Faculty**: Apan Qasem, Barbara Hewitt, Carolyn Chang, Chul-Ho Lee, Cindy Royal
- **Research Leaders**: Togay Ozbakkaloglu, Subasish Das, Larry R. Price
- **H-Index Range**: 0-79 (Togay Ozbakkaloglu highest)

### 7. CADS_WORKS Table
**Purpose**: All research publications by CADS faculty

```sql
CREATE TABLE cads_works (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id UUID NOT NULL REFERENCES cads_researchers(id),
    openalex_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    keywords TEXT,
    publication_year INTEGER,
    doi TEXT,
    citations INTEGER DEFAULT 0,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 2,454 research works
- **Research Areas**: Computer Science, Engineering, Data Science, AI/ML
- **Publication Range**: 1999-2025
- **High-Impact Works**: Including works with 795+ citations
- **Semantic Embeddings**: Full vector search capability

### 8. CADS_TOPICS Table
**Purpose**: Research topics specific to CADS publications

```sql
CREATE TABLE cads_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work_id UUID NOT NULL REFERENCES cads_works(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    score DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Current Data**: 6,834 research topics
- **CS-Specific Topics**: "Caching and Content Delivery", "IoT and Edge/Fog Computing"
- **High Confidence**: Topics with scores up to 0.9994
- **Interdisciplinary**: Spanning computer science, engineering, and applied research

## Database Views

### 9. RESEARCHER_SUMMARY View
**Purpose**: Aggregated statistics for all researchers

```sql
CREATE VIEW researcher_summary AS
SELECT 
    r.id,
    r.full_name,
    r.department,
    r.h_index,
    i.name as institution_name,
    COUNT(w.id) as total_works,
    SUM(w.citations) as total_citations,
    MAX(w.publication_year) as latest_publication_year,
    COUNT(t.id) as total_topics
FROM researchers r
JOIN institutions i ON r.institution_id = i.id
LEFT JOIN works w ON r.id = w.researcher_id
LEFT JOIN topics t ON w.id = t.work_id
GROUP BY r.id, r.full_name, r.department, r.h_index, i.name;
```

### 10. CADS_RESEARCHER_SUMMARY View
**Purpose**: Aggregated statistics specifically for CADS faculty

```sql
CREATE VIEW cads_researcher_summary AS
SELECT 
    cr.id,
    cr.full_name,
    cr.department,
    cr.h_index,
    i.name as institution_name,
    COUNT(cw.id) as total_works,
    SUM(cw.citations) as total_citations,
    MAX(cw.publication_year) as latest_publication_year,
    COUNT(ct.id) as total_topics
FROM cads_researchers cr
JOIN institutions i ON cr.institution_id = i.id
LEFT JOIN cads_works cw ON cr.id = cw.researcher_id
LEFT JOIN cads_topics ct ON cw.id = ct.work_id
GROUP BY cr.id, cr.full_name, cr.department, cr.h_index, i.name
ORDER BY total_works DESC;
```

## Data Relationships

### Primary Relationships
```
institutions (1) ←→ (many) researchers
researchers (1) ←→ (many) works
works (1) ←→ (many) topics
researchers (1) ←→ (many) researcher_grants

institutions (1) ←→ (many) cads_researchers
cads_researchers (1) ←→ (many) cads_works
cads_works (1) ←→ (many) cads_topics
```

### Foreign Key Constraints
- All relationships enforced with CASCADE DELETE
- UUID primary keys throughout for scalability
- Unique constraints on OpenAlex IDs to prevent duplicates

## Data Quality and Characteristics

### Research Coverage
- **Total Publications**: 13,915 works across all researchers
- **CADS Publications**: 2,454 works (17.6% of total)
- **Citation Impact**: 81,939+ total citations in CADS subset
- **Topic Diversity**: 14,428 unique research topics

### Temporal Distribution
- **Publication Years**: 1999-2025
- **Recent Activity**: Active publication pipeline through 2025
- **Historical Depth**: Comprehensive coverage of career spans

### Data Quality Metrics
- **Embedding Coverage**: 100% of works have semantic embeddings
- **Keyword Extraction**: Automated keyword generation from abstracts
- **Citation Tracking**: Real-time citation counts from OpenAlex
- **Topic Confidence**: Scored topic assignments (0.0-1.0)

## Advanced Features

### Vector Search Capabilities
- **Embedding Dimension**: 384-dimensional vectors
- **Search Type**: Cosine similarity for semantic matching
- **Index Type**: IVFFlat with 100 lists for performance
- **Use Cases**: Similar research discovery, collaboration matching

### Full-Text Search
- **Title Search**: GIN indexes on work titles
- **Abstract Search**: GIN indexes on abstracts
- **Keyword Search**: Structured keyword fields
- **Multi-language**: English text processing

### Performance Optimizations
- **Indexes**: Strategic indexing on frequently queried fields
- **Partitioning**: Ready for temporal partitioning if needed
- **Connection Pooling**: IPv4 pooler for reliable connections

## Data Sources and Updates

### Primary Data Source
- **OpenAlex API**: Comprehensive academic publication database
- **Update Frequency**: On-demand via pipeline scripts
- **Data Freshness**: Real-time citation and publication data

### Data Pipeline
- **Extraction**: Automated researcher and publication discovery
- **Processing**: Text processing, embedding generation, topic extraction
- **Loading**: Batch processing with error handling and rollback

## Security and Access

### Database Security
- **SSL/TLS**: Required for all connections
- **Authentication**: Username/password with connection pooling
- **Network**: IPv4 pooler for stable connectivity

### Data Privacy
- **Public Data**: All data sourced from public academic databases
- **No PII**: No personal identifiable information stored
- **Research Focus**: Academic and professional information only

## Usage Patterns

### Primary Use Cases
1. **Researcher Matching**: Find collaborators based on research similarity
2. **Expertise Discovery**: Identify experts in specific research areas
3. **Collaboration Analysis**: Analyze research networks and partnerships
4. **Impact Assessment**: Track citation patterns and research influence
5. **Trend Analysis**: Identify emerging research topics and directions

### Query Patterns
- **Semantic Search**: Vector similarity queries for related research
- **Faceted Search**: Multi-dimensional filtering by year, citations, topics
- **Aggregation**: Statistical analysis of research output and impact
- **Relationship Queries**: Cross-researcher collaboration discovery

This database represents a comprehensive research intelligence platform specifically designed for academic collaboration and discovery at Texas State University, with specialized focus on the Computer Science Department.