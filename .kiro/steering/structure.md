# Project Structure

## Repository Layout

The project follows a clean architecture pattern with clear separation of concerns:

```
├── backend/                    # FastAPI backend service
│   ├── app/                   # Main application code
│   │   ├── api/              # API route handlers
│   │   │   ├── v1/           # Versioned API endpoints
│   │   │   ├── solicitations.py  # Solicitation endpoints
│   │   │   ├── matching.py       # Matching endpoints
│   │   │   ├── teams.py          # Dream team endpoints
│   │   │   └── middleware.py     # Custom middleware
│   │   ├── core/             # Core business logic
│   │   │   ├── matching_engine.py    # Matching algorithms
│   │   │   ├── dream_team_engine.py  # Team assembly logic
│   │   │   ├── affinity_calculator.py # Affinity calculations
│   │   │   └── scoring_algorithms.py  # Scoring methods
│   │   ├── models/           # Pydantic data models
│   │   │   ├── solicitation.py   # Solicitation models
│   │   │   ├── matching.py       # Matching models
│   │   │   ├── researcher.py     # Researcher models
│   │   │   └── team.py           # Team models
│   │   ├── services/         # Business logic services
│   │   │   ├── matching_service.py   # Matching service
│   │   │   ├── pdf_service.py        # PDF processing
│   │   │   ├── dream_team_service.py # Team assembly
│   │   │   └── ai_service.py         # AI/ML operations
│   │   ├── processors/       # Data processing modules
│   │   │   ├── pdf_processor.py      # PDF text extraction
│   │   │   ├── ai_analyzer.py        # AI analysis
│   │   │   ├── embedding_processor.py # Vector embeddings
│   │   │   └── data_preprocessor.py   # Data preprocessing
│   │   ├── storage/          # Data storage handling
│   │   │   ├── database.py       # Database operations
│   │   │   ├── file_storage.py   # File management
│   │   │   ├── cache_storage.py  # Caching layer
│   │   │   └── model_storage.py  # ML model storage
│   │   ├── utils/            # Utility functions
│   │   │   ├── exceptions.py     # Custom exceptions
│   │   │   ├── validators.py     # Data validation
│   │   │   ├── formatters.py     # Data formatting
│   │   │   └── logging.py        # Logging configuration
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── config.py         # Configuration management
│   │   └── dependencies.py   # Dependency injection
│   ├── data/                 # Data storage
│   │   ├── models/           # Preprocessed ML models
│   │   ├── uploads/          # Uploaded PDF files
│   │   └── outputs/          # Generated outputs
│   ├── scripts/              # Utility scripts
│   │   ├── setup_data.py     # Data initialization
│   │   ├── update_models.py  # Model updates
│   │   └── health_check.py   # Health monitoring
│   ├── tests/                # Test files
│   │   ├── test_api/         # API endpoint tests
│   │   ├── test_core/        # Core logic tests
│   │   └── test_services/    # Service tests
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Docker build instructions
│   └── docker-compose.yml   # Docker composition
├── notebooks/               # Jupyter notebooks for analysis
│   ├── brahman.ipynb       # Research analysis
│   ├── dashboard_CADS.ipynb # Dashboard prototype
│   └── krishna.ipynb       # Data exploration
└── Dashboard/              # Legacy/alternative implementation
```

## Architecture Patterns

### API Layer (`app/api/`)
- RESTful endpoints organized by domain
- Version-specific routes in `v1/` subdirectory
- Consistent response models using Pydantic
- Proper HTTP status codes and error handling

### Core Logic (`app/core/`)
- Pure business logic without external dependencies
- Algorithms and engines for matching and team assembly
- Reusable components across different services

### Service Layer (`app/services/`)
- Orchestrates core logic with external dependencies
- Handles complex business workflows
- Manages state and transactions

### Data Models (`app/models/`)
- Pydantic models for request/response validation
- Type-safe data structures
- Clear separation between input/output models

### Storage Layer (`app/storage/`)
- Abstracted data access patterns
- Separate concerns for different storage types
- Caching and performance optimization

## File Naming Conventions

- **Snake case** for Python files: `matching_service.py`
- **Descriptive names** that indicate purpose: `pdf_processor.py`
- **Consistent suffixes**: `_service.py`, `_processor.py`, `_engine.py`
- **Test files** mirror source structure: `test_matching_service.py`

## Import Organization

```python
# Standard library imports
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# Third-party imports
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local imports
from app.models.matching import MatchingResults
from app.services.pdf_service import PDFService
from app.core.matching_engine import MatchingEngine
```

## Configuration Management

- Environment-specific settings in `.env` files
- Configuration classes in `app/config.py`
- Dependency injection through `app/dependencies.py`
- Separate development/production configurations