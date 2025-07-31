-- Database Schema for Texas State University Researcher Data Pipeline
-- This script creates all necessary tables, indexes, and constraints

-- Enable pg_vector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean recreation)
DROP TABLE IF EXISTS researcher_grants CASCADE;
DROP TABLE IF EXISTS topics CASCADE;
DROP TABLE IF EXISTS works CASCADE;
DROP TABLE IF EXISTS researchers CASCADE;
DROP TABLE IF EXISTS institutions CASCADE;

-- Create institutions table
CREATE TABLE institutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    openalex_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    ror_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create researchers table
CREATE TABLE researchers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    openalex_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    h_index INTEGER,
    department TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create works table with vector embedding support
CREATE TABLE works (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id UUID NOT NULL REFERENCES researchers(id) ON DELETE CASCADE,
    openalex_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    keywords TEXT, -- JSON array or comma-separated keywords
    publication_year INTEGER,
    doi TEXT,
    citations INTEGER DEFAULT 0,
    embedding VECTOR(384), -- 384-dimensional vector for sentence-transformer embeddings
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create topics table
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work_id UUID NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    score FLOAT8,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create researcher_grants table
CREATE TABLE researcher_grants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id UUID NOT NULL REFERENCES researchers(id) ON DELETE CASCADE,
    award_id TEXT NOT NULL,
    award_year INTEGER,
    role TEXT,
    award_amount BIGINT,
    award_title TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for performance optimization

-- Institutions indexes
CREATE INDEX idx_institutions_openalex_id ON institutions(openalex_id);
CREATE INDEX idx_institutions_name ON institutions(name);

-- Researchers indexes
CREATE INDEX idx_researchers_openalex_id ON researchers(openalex_id);
CREATE INDEX idx_researchers_institution_id ON researchers(institution_id);
CREATE INDEX idx_researchers_full_name ON researchers(full_name);
CREATE INDEX idx_researchers_h_index ON researchers(h_index);

-- Works indexes
CREATE INDEX idx_works_openalex_id ON works(openalex_id);
CREATE INDEX idx_works_researcher_id ON works(researcher_id);
CREATE INDEX idx_works_publication_year ON works(publication_year);
CREATE INDEX idx_works_citations ON works(citations);
CREATE INDEX idx_works_title ON works USING gin(to_tsvector('english', title));
CREATE INDEX idx_works_abstract ON works USING gin(to_tsvector('english', abstract));

-- Vector similarity index for embeddings (using cosine distance)
CREATE INDEX idx_works_embedding ON works USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Topics indexes
CREATE INDEX idx_topics_work_id ON topics(work_id);
CREATE INDEX idx_topics_name ON topics(name);
CREATE INDEX idx_topics_type ON topics(type);
CREATE INDEX idx_topics_score ON topics(score);

-- Researcher grants indexes
CREATE INDEX idx_researcher_grants_researcher_id ON researcher_grants(researcher_id);
CREATE INDEX idx_researcher_grants_award_year ON researcher_grants(award_year);
CREATE INDEX idx_researcher_grants_award_id ON researcher_grants(award_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $func$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$func$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_institutions_updated_at BEFORE UPDATE ON institutions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_researchers_updated_at BEFORE UPDATE ON researchers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_works_updated_at BEFORE UPDATE ON works FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints for data validation
ALTER TABLE researchers ADD CONSTRAINT chk_h_index_positive CHECK (h_index >= 0);
ALTER TABLE works ADD CONSTRAINT chk_publication_year_valid CHECK (publication_year >= 1900 AND publication_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1);
ALTER TABLE works ADD CONSTRAINT chk_citations_positive CHECK (citations >= 0);
ALTER TABLE topics ADD CONSTRAINT chk_score_range CHECK (score >= 0.0 AND score <= 1.0);
ALTER TABLE researcher_grants ADD CONSTRAINT chk_award_year_valid CHECK (award_year >= 1900 AND award_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 10);
ALTER TABLE researcher_grants ADD CONSTRAINT chk_award_amount_positive CHECK (award_amount >= 0);

-- Create views for common queries
CREATE VIEW researcher_summary AS
SELECT 
    r.id,
    r.full_name,
    r.department,
    r.h_index,
    i.name as institution_name,
    COUNT(w.id) as total_works,
    SUM(w.citations) as total_citations,
    MAX(w.publication_year) as latest_publication_year
FROM researchers r
JOIN institutions i ON r.institution_id = i.id
LEFT JOIN works w ON r.id = w.researcher_id
GROUP BY r.id, r.full_name, r.department, r.h_index, i.name;

-- Grant permissions (adjust as needed for your environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;