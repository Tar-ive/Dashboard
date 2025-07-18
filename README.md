# Intelligent Grant Matching Engine

An advanced FastAPI-based system designed to deconstruct NSF solicitation PDFs into structured data and assemble optimal research teams. The architecture leverages **Redis and RQ (Redis Queue)** for robust, scalable background job processing.

This project is built with three core principles: **Simplicity First**, **Test-Driven Development (TDD)**, and **Incremental Builds**.

---

## 🚀 Project Status & Roadmap

### Current Status: **Active Development**
- **Version**: 1.0.0-beta
- **Architecture**: Fully designed and documented
- **Implementation**: Foundation components in progress
- **Target MVP**: Q4 2025

### 🎯 MVP Milestone (Coming Soon)

Our Minimum Viable Product will deliver the complete **Solicitation Deconstruction** workflow:

**MVP Features:**
- ✅ **PDF Upload API**: FastAPI endpoint for NSF solicitation uploads
- ✅ **Asynchronous Processing**: Redis + RQ background job processing
- 🔄 **Smart PDF Extraction**: PyMuPDF-based text extraction with section recognition
- 🔄 **LLM-Powered Analysis**: Groq/Anthropic integration for metadata extraction
- 🔄 **Structured Output**: Complete `StructuredSolicitation` JSON objects
- ✅ **Job Status Tracking**: Real-time progress monitoring
- 🔄 **Comprehensive Testing**: 95%+ test coverage with TDD approach

**What You'll Be Able to Do:**
1. Upload any NSF solicitation PDF via `/api/deconstruct`
2. Receive immediate `job_id` for tracking
3. Monitor processing status via `/api/jobs/{job_id}`
4. Receive structured JSON with extracted metadata, eligibility rules, and required skills

### 🗓️ Development Timeline

**Phase 1: Foundation** *(Current - August 2025)*
- ✅ FastAPI + RQ + Redis infrastructure
- ✅ Core data models and job management
- 🔄 Basic endpoint implementations
- 🔄 Foundation testing framework

**Phase 2: MVP - Solicitation Deconstruction** *(September 2025)*
- 🔄 TDD implementation of PDF processing
- 🔄 LLM integration for metadata extraction
- 🔄 Section-based text chunking
- 🔄 Comprehensive error handling

**Phase 3: Dream Team Assembly** *(Q4 2025)*
- Dream team optimization algorithms
- Researcher affinity scoring
- Gap analysis and strategic recommendations
- End-to-end workflow completion

---

## 🏛️ Architecture

The system uses a decoupled architecture where the FastAPI web server acts as a lightweight interface for enqueuing jobs and querying their status. All heavy processing is handled asynchronously by RQ workers.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │     Redis       │    │   RQ Worker     │
│  (Web Server)   │    │  (Broker &      │    │  (Background    │
│                 │    │ State Manager)  │    │   Processor)    │
│                 │    │                 │    │                 │
│• POST /deconstruct  │◄──►│ • Job queue     │◄──►│• deconstruct_   │
│• POST /assemble-team│    │ • Job status    │    │  solicitation_  │
│• GET /jobs/{id}     │    │ • Results store │    │  task           │
│• Returns job_id     │    │                 │    │• assemble_      │
└─────────────────┘    └─────────────────┘    │  dream_team_    │
                                              │  task           │
                                              └─────────────────┘
```

---

## ✨ Core Features

### 🎯 Milestone 1: Solicitation Deconstruction *(MVP)*
- **PDF Intelligence**: Advanced PDF parsing with section recognition
- **LLM-Powered Extraction**: Structured metadata extraction using Groq/Anthropic
- **Comprehensive Analysis**: Extract funding details, eligibility rules, required skills
- **Async Processing**: Non-blocking background job processing
- **Real-time Tracking**: Monitor job progress and status

### 🚀 Milestone 2: Dream Team Assembly *(Future)*
- **Smart Team Building**: Optimal research team composition algorithms
- **Affinity Scoring**: Advanced researcher-skill matching
- **Gap Analysis**: Strategic recommendations using LLM analysis
- **Constraint Optimization**: Team size, role, and eligibility constraint handling

### 🔧 Platform Features
- **Dockerized Deployment**: Complete containerization with docker-compose
- **RESTful API**: Comprehensive REST API with interactive documentation
- **TDD Development**: 95%+ test coverage with comprehensive test suite
- **Real-time Monitoring**: Health checks and job status endpoints

---

## 📁 Project Structure

The backend has been refactored for simplicity and maintainability, eliminating unnecessary directories and circular dependencies.

```
backend/
├── app/                      # Main application source code
│   ├── __init__.py
│   ├── api/                  # FastAPI routers (endpoints)
│   │   ├── deconstruct.py    # 🔄 PDF deconstruction endpoints
│   │   ├── jobs.py           # ✅ Job status tracking
│   │   └── teams.py          # 🔜 Dream team assembly (future)
│   ├── jobs/                 # Background task management
│   │   ├── job_manager.py    # ✅ Job queue management
│   │   ├── redis_connection.py # ✅ Redis client setup
│   │   └── worker_config.py  # ✅ RQ worker configuration
│   ├── models/               # Pydantic data models
│   │   ├── solicitation.py   # 🔄 StructuredSolicitation model
│   │   ├── jobs.py          # ✅ Job tracking models
│   │   └── teams.py         # 🔜 Dream team models (future)
│   ├── services/             # Core business logic
│   │   ├── pdf_processor.py  # 🔄 PDF extraction service
│   │   ├── llm_service.py    # 🔄 LLM integration service
│   │   └── team_builder.py   # 🔜 Team assembly service (future)
│   ├── config.py             # ✅ Simplified configuration
│   ├── main.py               # ✅ FastAPI application entry point
│   └── utils.py              # 🔄 Utility functions
├── data/                     # Data storage
│   ├── uploads/              # PDF file uploads
│   └── models/               # 🔜 Researcher data (future)
├── tests/                    # Comprehensive test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── .env.example              # Environment variables template
├── Dockerfile                # Docker build instructions
├── docker-compose.yml        # Local development services
├── requirements.txt          # Python dependencies
└── worker.py                 # 🔄 RQ worker script
```

**Legend:** ✅ Complete | 🔄 In Progress | 🔜 Planned

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Redis (can be run via Docker)

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Tar-ive/Dashboard.git
   cd Dashboard/backend
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

   Required environment variables:
   ```ini
   # LLM API Keys (choose one or both)
   ANTHROPIC_API_KEY=your_anthropic_key_here
   GROQ_API_KEY=your_groq_key_here
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   
   # Application Settings
   DEBUG=true
   ```

3. **Start Services**
   ```bash
   # Start FastAPI + Redis with Docker Compose
   docker-compose up -d --build
   
   # In a separate terminal, start the worker
   python worker.py
   ```

4. **Access the Application**
   - **API**: http://localhost:8000
   - **Interactive Docs**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

---

## 🚀 Usage Example

### Step 1: Upload NSF Solicitation

```bash
curl -X POST "http://localhost:8000/api/deconstruct" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_nsf_solicitation.pdf"
```

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
  "status": "queued",
  "message": "PDF uploaded successfully. Processing started."
}
```

### Step 2: Monitor Processing

```bash
curl -X GET "http://localhost:8000/api/jobs/a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890"
```

**Response (when completed):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
  "status": "completed",
  "progress": 100,
  "result": {
    "solicitation_id": "NSF-25-12345",
    "award_title": "Mathematical Foundations of Artificial Intelligence",
    "funding_ceiling": 500000.0,
    "project_duration_months": 36,
    "required_scientific_skills": [
      "machine learning",
      "mathematical optimization",
      "statistical analysis"
    ],
    "pi_eligibility_rules": [
      "Must hold PhD in relevant field",
      "Must be affiliated with eligible institution"
    ],
    "processing_time_seconds": 127.5
  },
  "created_at": "2025-07-18T10:00:00Z",
  "completed_at": "2025-07-18T10:02:07Z"
}
```

---

## 🧪 Testing

The project follows a comprehensive TDD approach with multiple test categories.

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # End-to-end tests only
```

### Test Categories

- **Unit Tests**: Test individual functions in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete API-to-worker workflows
- **Performance Tests**: Validate response times and throughput

---

## 📊 Data Models

### Milestone 1: Solicitation Models

```python
class StructuredSolicitation(BaseModel):
    solicitation_id: str
    award_title: str
    funding_ceiling: Optional[float]
    project_duration_months: Optional[int]
    submission_deadline: Optional[datetime]
    pi_eligibility_rules: List[str]
    required_scientific_skills: List[str]
    full_text: str
    processing_time_seconds: float
    created_at: datetime
```

### Future: Dream Team Models

```python
class DreamTeamReport(BaseModel):
    solicitation_id: str
    team_members: List[ProposedTeamMember]
    team_coverage_score: float
    gap_analysis: Dict[str, Any]
    strategic_recommendations: List[str]
```

---

## 🔧 Development

### TDD Workflow

**Red-Green-Refactor Cycle:**
1. **Red**: Write failing tests first
2. **Green**: Implement minimal code to pass tests
3. **Refactor**: Clean and optimize implementation

### Code Quality Standards

- **Test Coverage**: Maintain 95%+ coverage
- **Type Hints**: Full type annotation coverage
- **Documentation**: Comprehensive docstrings
- **Error Handling**: Robust error handling and logging

---

## 🚀 What's Next

### Immediate Next Steps (July 2025)

1. **Complete PDF Processing Pipeline**
   - Finalize PyMuPDF integration
   - Implement section recognition algorithms
   - Add robust error handling for malformed PDFs

2. **LLM Integration Completion**
   - Complete Groq/Anthropic API integration
   - Implement retry logic and rate limiting
   - Add response validation and error recovery

3. **MVP Testing & Validation**
   - Complete end-to-end test suite
   - Performance testing and optimization
   - User acceptance testing with sample solicitations

### Future Enhancements (August 2025)

1. **Dream Team Assembly**
   - Researcher database integration
   - Affinity scoring algorithms
   - Team optimization strategies

2. **Advanced Features**
   - Multi-solicitation comparison
   - Historical success analysis
   - Real-time collaboration features

3. **Production Readiness**
   - Kubernetes deployment configurations
   - Monitoring and alerting systems
   - API rate limiting and authentication

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow TDD principles (write tests first!)
4. Ensure all tests pass (`make test`)
5. Submit a pull request

---

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Documentation**: http://localhost:8000/docs (when running locally)
- **Issues**: [GitHub Issues](https://github.com/Tar-ive/Dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Tar-ive/Dashboard/discussions)

---

**Built with ❤️ for the research community**

*Transforming how researchers discover and collaborate on NSF opportunities*