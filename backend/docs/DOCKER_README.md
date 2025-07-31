# OrbStack Setup for NSF Researcher Matching API

This guide will help you set up the complete NSF Researcher Matching API using OrbStack, including all dependencies and services.

## 🚀 Quick Start

### Prerequisites

- OrbStack (latest version)
- Your API keys (Anthropic and Groq)

> **Note**: OrbStack is fully Docker-compatible, so all `docker` and `docker-compose` commands work exactly the same!

### 1. Environment Setup

Copy the Docker environment template:
```bash
cp .env.docker .env
```

Edit `.env` file and add your API keys:
```bash
# Required API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

### 2. Build and Start Services

```bash
# Build the container images with OrbStack
docker-compose build

# Start all services (API + Redis)
docker-compose up -d

# Check service status
docker-compose ps
```

> **OrbStack Benefits**: Faster startup, better resource usage, and native macOS integration!

### 3. Verify Setup

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Redis**: localhost:6379

## 🧪 Testing with Postman

1. Import the Postman collection from `./postman/Solicitation_Deconstruction_Collection.json`
2. Set environment variables:
   - `base_url`: `http://localhost:8000/api`
3. Run the complete workflow:
   - Upload PDF → Check Status → Validate Results

## 🔧 Development & Debugging

### View Logs
```bash
# API logs
docker-compose logs -f api

# Redis logs
docker-compose logs -f redis

# All logs
docker-compose logs -f
```

### Redis Debugging
```bash
# Start Redis Commander (web UI)
docker-compose --profile debug up -d redis-commander
# Visit: http://localhost:8081

# Or use Redis CLI directly
docker-compose exec redis redis-cli
```

### Development Mode
```bash
# Mount local code for development
docker-compose up -d

# The API will auto-reload when you change files in ./app/
```

## 📊 Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │      Redis      │
│   Port: 8000    │◄──►│   Port: 6379    │
│                 │    │                 │
│ • PDF Upload    │    │ • Job Storage   │
│ • LLM Processing│    │ • Status Track  │
│ • Job Management│    │ • Result Cache  │
└─────────────────┘    └─────────────────┘
```

## 🐛 Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **API keys not working**:
   - Verify `.env` file has correct keys
   - Restart services: `docker-compose restart api`

3. **Redis connection issues**:
   ```bash
   docker-compose exec redis redis-cli ping
   # Should return: PONG
   ```

4. **Port conflicts**:
   - Change ports in `docker-compose.yml` if 8000 or 6379 are in use

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check Redis health
docker-compose exec redis redis-cli ping

# Check all service status
docker-compose ps
```

## 📁 Directory Structure

```
backend/
├── docker-compose.yml      # Service orchestration
├── Dockerfile             # API container definition
├── .env.docker           # Environment template
├── .env                  # Your environment (create this)
├── app/                  # Application code
├── data/                 # Data directory (mounted)
│   ├── uploads/         # PDF uploads
│   ├── models/          # ML models
│   └── outputs/         # Generated outputs
└── postman/             # API testing collection
```

## 🔄 Workflow Testing

The complete solicitation deconstruction workflow:

1. **Upload PDF**: POST `/api/deconstruct`
   - Returns job_id immediately
   - Starts background processing

2. **Check Status**: GET `/api/jobs/{job_id}`
   - Polls job progress
   - Returns structured result when complete

3. **Validate Results**: 
   - Award title, funding, duration
   - PI eligibility rules
   - Required skills
   - Full extracted text

## 🛑 Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (clears all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## 🔐 Security Notes

- API keys are passed via environment variables
- Non-root user in production container
- Health checks for service monitoring
- Redis data persistence with volumes

## 📈 Performance

- **Startup time**: ~30-60 seconds (includes model loading)
- **PDF processing**: 5-15 seconds per document
- **Memory usage**: ~2GB (includes ML models)
- **Storage**: Persistent Redis data and uploaded files