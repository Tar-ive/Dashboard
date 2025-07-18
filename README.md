# NSF Researcher Matching API

A comprehensive FastAPI-based system for matching researchers to NSF solicitations and assembling optimal research teams using advanced machine learning algorithms.

## 🚀 Features

- **PDF Upload & Analysis**: Upload and analyze NSF solicitation PDFs with intelligent text extraction
- **Researcher Matching**: Advanced hybrid search algorithm for matching researchers to solicitations
- **Dream Team Assembly**: Optimize research team composition using affinity matrices and selection strategies
- **Real-time Processing**: Asynchronous processing with status tracking
- **RESTful API**: Complete REST API with comprehensive documentation
- **Docker Support**: Containerized deployment with Docker Compose
- **Interactive Notebooks**: Jupyter notebooks for data analysis and exploration

## 📁 Project Structure

```
Dashboard/
├── README.md                    # Project documentation
├── LICENSE                     # Project license
├── notebooks/                  # Jupyter notebooks for analysis
│   ├── brahman.ipynb          # Research analysis notebook
│   ├── dashboard_CADS.ipynb   # Dashboard prototype
│   └── krishna.ipynb          # Data exploration notebook
└── backend/                   # FastAPI backend service
    ├── .env.example           # Environment variables template
    ├── .gitignore             # Git ignore rules
    ├── app/                   # Main application code
    │   ├── __init__.py
    │   ├── main.py           # FastAPI application entry point
    │   ├── api/              # API route handlers
    │   │   ├── __init__.py
    │   │   ├── solicitations.py  # Solicitation endpoints
    │   │   ├── matching.py      # Matching endpoints
    │   │   └── teams.py        # Dream team endpoints
    │   ├── config.py          # Configuration management
    │   ├── core/              # Core functionality
    │   ├── dependencies.py    # Dependency injection
    │ |   ├── models/          # Data models
    │   ├── processors/        # Data processing modules
    │   ├── services/          # Business logic services
    │   ├── storage/           # Data storage handling
    │   └── utils/             # Utility functions
    ├── data/                  # Data storage
    │   ├── uploads/           # Uploaded PDF files
    │   └── outputs/           # Generated outputs
    ├── docker-compose.yml     # Docker composition
    ├── Dockerfile             # Docker build instructions
    ├── requirements.txt       # Python dependencies
    ├── scripts/               # Utility scripts
    └── tests/                 # Test files
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Tar-ive/Dashboard.git
   cd Dashboard
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   cd backend
   docker-compose up -d
   ```

2. **Access the containerized API**
   - API: http://localhost:8000
   - Health check: http://localhost:8000/health

## 📚 API Documentation

### Core Endpoints

#### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status

#### Solicitations API
- `GET /solicitations/` - List all solicitations
- `POST /solicitations/upload` - Upload PDF solicitation
- `POST /solicitations/{solicitation_id}/analyze` - Analyze solicitation
- `GET /solicitations/{solicitation_id}` - Get solicitation details

#### Matching API
- `GET /api/v1/matching/` - Get matching service info
- `POST /api/v1/matching/run` - Run matching algorithm
- `GET /api/v1/matching/{session_id}/status` - Get matching status
- `GET /api/v1/matching/{session_id}/results` - Get matching results
- `DELETE /api/v1/matching/{session_id}` - Delete matching session

#### Dream Teams API
- `GET /api/v1/teams/` - Get teams service info
- `POST /api/v1/teams/assemble` - Assemble dream team
- `GET /api/v1/teams/{team_id}` - Get team details
- `DELETE /api/v1/teams/{team_id}` - Delete team session
- `GET /api/v1/teams/{team_id}/matrix` - Export affinity matrix
- `POST /api/v1/teams/{team_id}/optimize` - Optimize team composition
- `POST /api/v1/teams/{team_id}/compare` - Compare selection strategies

### Request/Response Examples

#### Upload Solicitation
```bash
curl -X POST "http://localhost:8000/solicitations/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@solicitation.pdf"
```

#### Run Matching
```bash
curl -X POST "http://localhost:8000/api/v1/matching/run" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitation_id": "123",
    "algorithm": "hybrid",
    "max_results": 10
  }'
```

#### Assemble Dream Team
```bash
curl -X POST "http://localhost:8000/api/v1/teams/assemble" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitation_id": "123",
    "team_size": 5,
    "strategy": "optimal"
  }'
```

## 🧪 Data Models

### Core Models
- **SolicitationResponse**: Uploaded solicitation metadata
- **SolicitationAnalysis**: Analyzed solicitation data
- **MatchingRequest**: Matching algorithm parameters
- **MatchingResults**: Researcher matching results
- **DreamTeamRequest**: Team assembly parameters
- **DreamTeamReport**: Assembled team details
- **ResearcherMatch**: Individual researcher match data
- **AffinityMatrixExport**: Team affinity matrix data

## 🔧 Services Architecture

### Core Services
1. **PDF Processing Utilities**: Utility functions for PDF text extraction and analysis
2. **MatchingService**: Implements hybrid search algorithms
3. **DreamTeamService**: Optimizes team composition
4. **AnalysisService**: Performs solicitation analysis
5. **StorageService**: Manages data persistence

### Configuration System
The application uses a simplified configuration system that:
- Loads settings from environment variables using `os.getenv()`
- Supports `.env` files for local development
- Automatically creates required directories on startup
- Provides sensible defaults for all configuration options

### Processing Pipeline
1. **PDF Upload** → Utility-based Text Extraction → Content Analysis
2. **Solicitation Analysis** → Title/Abstract Detection → Section Mapping
3. **Researcher Matching** → Similarity Scoring → Ranking
4. **Team Assembly** → Affinity Calculation → Optimization

### PDF Processing Architecture
The system now uses a streamlined utility-based approach for PDF processing:

- **`extract_pdf_text()`**: Core utility function for PDF text extraction using PyMuPDF
- **Intelligent Text Analysis**: Automatic title and abstract detection
- **Section Recognition**: Identifies key NSF solicitation sections (Program Description, Award Information, Eligibility, etc.)
- **Performance Optimized**: Direct utility functions for faster processing without service layer overhead

## 📊 Notebooks

### Available Notebooks
1. **brahman.ipynb**: Research analysis and algorithm development
2. **dashboard_CADS.ipynb**: Dashboard prototype and visualization
3. **krishna.ipynb**: Data exploration and preprocessing

### Running Notebooks
```bash
cd notebooks
jupyter notebook
```

## 🧪 Testing

The project uses a simplified, pragmatic testing approach that starts minimal and grows with complexity as needed.

### Current Test Infrastructure

The testing framework currently provides:
- **Basic Test Client**: FastAPI test client for API endpoint testing
- **Temporary File System**: Isolated temporary directories for file-based tests
- **Sample Test Data**: Basic PDF content fixtures for upload testing
- **Pytest Configuration**: Comprehensive test configuration with coverage reporting

### Run Tests
```bash
cd backend
python -m pytest tests/
```

### Test Coverage
```bash
python -m pytest --cov=app tests/
```

### Test Coverage Report
```bash
# Generate HTML coverage report
python -m pytest --cov=app --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

### Test Categories
The project supports multiple test categories through pytest markers:
- `unit`: Unit tests for individual components
- `integration`: Integration tests for component interactions  
- `e2e`: End-to-end tests for complete workflows
- `performance`: Performance and load tests
- `golden`: Ground-truth validation tests
- `slow`: Tests that take longer to run
- `external`: Tests that require external services

### Running Specific Test Categories
```bash
# Run only unit tests
python -m pytest -m unit

# Run integration tests
python -m pytest -m integration

# Skip slow tests
python -m pytest -m "not slow"
```

### Test Development Philosophy

The testing approach follows these principles:
1. **Start Simple**: Begin with basic fixtures and grow complexity as needed
2. **Pragmatic Coverage**: Focus on critical paths and business logic
3. **Fast Feedback**: Prioritize fast-running tests for development workflow
4. **Realistic Data**: Use meaningful test data that reflects real-world scenarios
5. **Isolated Tests**: Each test runs independently with proper cleanup

### Current Test Infrastructure Details

The simplified test configuration (`backend/tests/conftest.py`) provides:

```python
@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
```

### Writing Tests

Example test structure:

```python
def test_api_endpoint(test_client):
    """Test API endpoint with basic client."""
    response = test_client.get("/health")
    assert response.status_code == 200

def test_file_processing(temp_dir, sample_pdf_content):
    """Test file processing with temporary directory."""
    pdf_path = Path(temp_dir) / "test.pdf"
    pdf_path.write_bytes(sample_pdf_content)
    
    # Test file processing logic
    assert pdf_path.exists()
```

### Future Testing Enhancements

As the project grows, the testing infrastructure will expand to include:
- Advanced fixture management for complex test scenarios
- Mock services for external dependencies
- Performance benchmarking and load testing
- Ground-truth validation against historical data
- Automated test data generation

### Testing Best Practices

1. **Keep Tests Simple**: Start with basic assertions and grow complexity as needed
2. **Use Descriptive Names**: Test names should clearly describe what is being tested
3. **Isolate Tests**: Each test should be independent and not rely on other tests
4. **Test Edge Cases**: Include tests for boundary conditions and error scenarios
5. **Maintain Fast Feedback**: Prioritize fast-running tests for development workflow

## 📈 Performance & Scalability

### Optimization Features
- **Asynchronous Processing**: Non-blocking API operations
- **Caching**: Intelligent result caching
- **Batch Processing**: Efficient bulk operations
- **Resource Management**: Optimized memory usage

### Monitoring
- Health check endpoints for monitoring
- Detailed status tracking for long-running operations
- Performance metrics collection

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   export ENVIRONMENT=production
   export DATABASE_URL=your_production_db
   export SECRET_KEY=your_secret_key
   ```

2. **Docker Production Build**
   ```bash
   docker build -t nsf-matcher:latest .
   docker run -p 8000:8000 nsf-matcher:latest
   ```

3. **Kubernetes Deployment** (Optional)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nsf-matcher
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nsf-matcher
  template:
    metadata:
      labels:
        app: nsf-matcher
    spec:
      containers:
      - name: nsf-matcher
        image: nsf-matcher:latest
        ports:
        - containerPort: 8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use semantic commit messages

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please:
1. Check the API documentation
2. Review existing issues
3. Create a new issue with detailed description

## 🙏 Acknowledgments

- NSF for solicitation data standards
- FastAPI team for the excellent framework
- Contributors and researchers who made this possible

## 📊 API Status

- **Version**: 1.0.0
- **Status**: Active Development
- **Last Updated**: July 2025
- **Endpoints**: 17 active endpoints
- **Features**: PDF Processing, Matching, Team Assembly

**Built with ❤️ for the research community**