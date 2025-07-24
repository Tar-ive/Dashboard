# Project Structure & Organization

## Root Directory
```
├── app.py                 # Main Streamlit application entry point
├── pyproject.toml         # Project configuration and dependencies
├── requirements.txt       # Fallback dependency specification
├── uv.lock               # Locked dependency versions
└── replit.md             # Project documentation
```

## Core Application Structure
```
modules/
├── __pycache__/          # Python bytecode cache
├── data_loader.py        # Data loading and caching utilities
├── data_models.py        # Centralized dataclass definitions
├── matcher.py            # Researcher scoring and matching logic
├── team_builder.py       # Team assembly optimization algorithms
└── report_generator.py   # Report generation and AI analysis
```

## Data Directory
```
data/
├── .gitkeep                    # Ensures directory exists in git
├── tfidf_model.pkl            # Pre-trained TF-IDF vectorizer
├── researcher_vectors.npz     # Researcher TF-IDF representations
├── conceptual_profiles.npz    # Paper embeddings for semantic matching
├── evidence_index.json        # Researcher-to-papers mapping
├── researcher_metadata.parquet # Researcher profiles and statistics
└── processing_log.json        # Data processing history
```

## Configuration & Assets
```
.streamlit/
└── config.toml           # Streamlit configuration

attached_assets/          # User-uploaded files and screenshots
└── *.txt, *.png         # Various attached documents and images
```

## Architecture Principles

### Modular Design
- **Single Responsibility**: Each module handles one aspect of the pipeline
- **Stateless Services**: Utility classes with no persistent state between calls
- **Clear Interfaces**: Well-defined dataclasses for inter-module communication

### Data Flow Pattern
1. **app.py** → Orchestrates workflow and manages UI state
2. **data_loader.py** → Loads and caches all required data/models
3. **matcher.py** → Scores researchers against solicitation requirements
4. **team_builder.py** → Assembles optimal teams from candidate pool
5. **report_generator.py** → Creates final reports and strategic analysis

### Import Conventions
- Relative imports within modules: `from .data_models import ClassName`
- External dependencies imported at module level with try/except for optional deps
- Type hints used throughout for better code clarity

### File Naming
- **Snake_case**: All Python files and directories
- **Descriptive names**: Clear indication of module purpose
- **Consistent suffixes**: `_loader.py`, `_builder.py`, `_generator.py` for utility classes

### Data Organization
- **Persistent storage**: All ML models and datasets in `/data/` directory
- **Caching strategy**: Streamlit decorators prevent expensive reloading
- **Format consistency**: NumPy for arrays, Parquet for structured data, JSON for metadata