# Multi-stage build for production and testing
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base as production

# Copy application code
COPY app/ ./app/

# Create data directory
RUN mkdir -p data/uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Test stage
FROM base as test

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    httpx \
    black \
    isort \
    flake8 \
    mypy \
    bandit \
    safety

# Copy application and test code
COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .
COPY Makefile .

# Create test directories
RUN mkdir -p test_uploads test_models test_outputs htmlcov

# Set test environment
ENV TESTING=true
ENV DATABASE_URL=sqlite:///./test.db
ENV UPLOAD_DIR=./test_uploads
ENV MODEL_DIR=./test_models

# Default command for testing
CMD ["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html", "--cov-report=xml", "-v"]