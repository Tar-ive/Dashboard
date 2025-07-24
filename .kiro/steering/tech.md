# Technology Stack & Build System

## Core Technologies
- **Python 3.11+**: Primary language with type hints and dataclasses
- **Streamlit**: Web application framework for interactive UI
- **scikit-learn**: Machine learning utilities (TF-IDF, cosine similarity)
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing and array operations

## Optional Dependencies
- **sentence-transformers**: Dense text embeddings (graceful fallback if unavailable)
- **Groq API**: AI-powered strategic analysis (basic analysis fallback)
- **torch/torchvision/torchaudio**: PyTorch ecosystem for ML models

## Package Management
- **uv**: Modern Python package manager with lock file (`uv.lock`)
- **pyproject.toml**: Project configuration and dependencies
- **requirements.txt**: Fallback dependency specification

## Data Storage & Formats
- **Pickle (.pkl)**: Serialized TF-IDF models with compatibility handling
- **NumPy (.npz)**: Compressed arrays for vectors and embeddings
- **Parquet**: Researcher metadata storage
- **JSON**: Configuration and structured data

## Common Commands

### Development
```bash
# Install dependencies
uv sync

# Run application
streamlit run app.py

# Run on specific port
streamlit run app.py --server.port 5000
```

### Data Management
```bash
# Check data directory structure
ls -la data/

# Verify required data files
ls data/*.pkl data/*.npz data/*.json data/*.parquet
```

## Architecture Patterns
- **Modular Design**: Separate classes for data loading, matching, team building, and reporting
- **Stateless Services**: Utility classes with no persistent state
- **Caching Strategy**: Streamlit decorators (`@st.cache_resource`, `@st.cache_data`)
- **Graceful Degradation**: Fallback mechanisms for optional dependencies
- **Error Handling**: Try-catch blocks with user-friendly error messages