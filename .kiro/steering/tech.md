# Technology Stack

## Core Framework
- **FastAPI**: Modern, fast web framework for building APIs with Python 3.8+
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation and settings management using Python type annotations

## Machine Learning & AI
- **scikit-learn**: Machine learning library for TF-IDF vectorization and similarity calculations
- **sentence-transformers**: Pre-trained models for semantic text embeddings
- **huggingface_hub**: Access to Hugging Face model repository
- **numpy**: Numerical computing for vector operations
- **pandas**: Data manipulation and analysis

## Document Processing
- **PyMuPDF**: PDF text extraction and processing
- **python-multipart**: File upload handling

## Security & Authentication
- **python-jose[cryptography]**: JWT token handling and cryptographic operations

## Development & Deployment
- **Docker**: Containerization with multi-stage builds
- **Docker Compose**: Local development orchestration
- **Python 3.11**: Runtime environment

## Common Commands

### Local Development
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Operations
```bash
# Build and run with Docker Compose
cd backend
docker-compose up -d

# Build standalone container
docker build -t nsf-matcher:latest .

# Run container
docker run -p 8000:8000 nsf-matcher:latest
```

### Testing
```bash
# Run tests
cd backend
python -m pytest tests/

# Run with coverage
python -m pytest --cov=app tests/
```

### Data Management
```bash
# Setup initial data
python scripts/setup_data.py

# Update ML models
python scripts/update_models.py

# Health check
python scripts/health_check.py
```

## API Documentation
- **Swagger UI**: Available at `/docs` endpoint
- **ReDoc**: Available at `/redoc` endpoint
- **OpenAPI**: JSON schema available at `/openapi.json`

## Environment Configuration
- Use `.env` files for environment-specific settings
- Copy `.env.example` to `.env` for local development
- Configure production variables for deployment