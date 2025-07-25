# AI-Powered Research Team Matching & Assembly System

## Overview

This is a Streamlit-based AI application that matches researchers to research solicitations and assembles optimal teams. The system analyzes research solicitations, scores individual researchers based on their expertise and skills, and then uses optimization algorithms to build dream teams that maximize coverage of required skills.

The application processes large datasets of researcher profiles, uses TF-IDF and sentence transformers for semantic matching, and provides AI-powered strategic analysis of assembled teams.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular, object-oriented architecture with clear separation of concerns:

- **Frontend**: Streamlit web interface for user interaction
- **Backend**: Python-based processing pipeline with modular classes
- **Data Processing**: Machine learning models for text analysis and similarity matching
- **AI Integration**: Optional Groq API integration for strategic analysis
- **State Management**: Streamlit session state for workflow orchestration

The architecture is designed as a stateless service where the main app.py orchestrates the workflow between specialized utility classes.

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Streamlit UI controller and workflow orchestrator
- **Responsibilities**: Page configuration, session state management, sidebar setup
- **Design Pattern**: Acts as the single source of truth for application state

### 2. Data Models (modules/data_models.py)
- **Purpose**: Centralized type definitions and data structures
- **Key Classes**:
  - `ResearcherMatch`: Individual researcher scoring results
  - `MatchingResults`: Complete matching process results
  - `TeamAssemblyResult`: Team building outcomes
  - `DreamTeamReport`: Final report structure
  - `Solicitation`: Research solicitation data structure

### 3. Data Loader (modules/data_loader.py)
- **Purpose**: Handles loading and caching of large data files and ML models
- **Key Features**:
  - Streamlit caching decorators for performance optimization
  - TF-IDF model loading with pickle compatibility handling
  - SentenceTransformer model management
  - Researcher data and metadata loading
- **Caching Strategy**: Uses `@st.cache_resource` for models and `@st.cache_data` for datasets

### 4. Researcher Matcher (modules/matcher.py)
- **Purpose**: Scores and ranks researchers against solicitation requirements
- **Key Algorithms**:
  - Eligibility filtering (early-career, grant experience)
  - Keyword extraction from skills
  - Hybrid scoring combining TF-IDF (sparse) and sentence embeddings (dense)
  - Weighted scoring with configurable alpha/beta parameters

### 5. Team Builder (modules/team_builder.py)
- **Purpose**: Assembles optimal teams from candidate pools
- **Key Features**:
  - Affinity matrix generation
  - Team optimization algorithms
  - Coverage score calculation
- **Approach**: Uses cosine similarity between researcher vectors and skill requirements

### 6. Report Generator (modules/report_generator.py)
- **Purpose**: Generates human-readable reports and AI analysis
- **Key Features**:
  - Optional Groq API integration for strategic analysis
  - Fallback to basic analysis when AI is unavailable
  - Markdown report generation
- **AI Integration**: Uses Groq's language models for enhanced team analysis

## Data Flow

1. **Input Phase**: User uploads research solicitation document
2. **Loading Phase**: DataLoader retrieves cached models and researcher datasets
3. **Analysis Phase**: Solicitation is parsed and skill requirements extracted
4. **Matching Phase**: ResearcherMatcher scores all eligible researchers
5. **Assembly Phase**: TeamBuilder creates affinity matrix and optimizes team selection
6. **Reporting Phase**: ReportGenerator creates comprehensive analysis and recommendations

The workflow is stateful, with each phase storing results in Streamlit session state for subsequent steps.

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **scikit-learn**: Machine learning utilities (TF-IDF, cosine similarity)
- **sentence-transformers**: Dense text embeddings

### Optional Dependencies
- **Groq**: AI-powered strategic analysis (graceful fallback if unavailable)

### Data Storage
- **Pickle files**: Pre-trained TF-IDF models
- **Parquet files**: Researcher datasets and metadata
- **JSON files**: Configuration and structured data

### Model Dependencies
- Pre-trained SentenceTransformer models for semantic similarity
- Custom TF-IDF vectorizers trained on research domain corpus

## Deployment Strategy

### Local Development
- Uses local file system paths for data storage
- Streamlit development server for rapid iteration
- Session state management for multi-step workflows

### Production Considerations
- **Data Persistence**: Large datasets and models stored in persistent storage
- **Caching**: Aggressive use of Streamlit caching to prevent reloading
- **Error Handling**: Graceful degradation when optional services unavailable
- **Performance**: Limits processing to top candidates for scalability

### Configuration Management
- Environment-based configuration for API keys
- Fallback mechanisms for missing dependencies
- Configurable scoring parameters and thresholds

The system is designed to be robust and fault-tolerant, with clear error messages and fallback behaviors when external services or optional components are unavailable.

## Recent Changes

### 2025-01-22: Complete System Implementation
- ✓ Created all modular components following FDD principles
- ✓ Implemented DataLoader with Streamlit caching for performance
- ✓ Built ResearcherMatcher with hybrid TF-IDF and semantic similarity
- ✓ Developed TeamBuilder using affinity matrices and optimization
- ✓ Created ReportGenerator with Groq AI integration and fallback
- ✓ Built comprehensive Streamlit UI with step-by-step workflow
- ✓ Added graceful handling for optional dependencies (sentence-transformers)
- ✓ System is running and ready for data upload

### Current Status
- All core modules implemented and functional
- Application running on port 5000
- Data directory created - ready for user data upload
- Streamlit workflow configured and active

## Next Steps
1. User needs to upload research data files to `/data/` directory:
   - tfidf_model.pkl
   - researcher_vectors.npz  
   - conceptual_profiles.npz
   - evidence_index.json
   - researcher_metadata.parquet
2. Test system with actual solicitation data
3. Optional: Configure Groq API key for enhanced AI analysis