# Makefile for NSF Researcher Matching API

.PHONY: help install test test-unit test-integration test-e2e test-performance test-coverage lint format security clean setup-dev

# Default target
help:
	@echo "Available targets:"
	@echo "  install          - Install dependencies"
	@echo "  test             - Run all tests"
	@echo "  test-unit        - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-e2e         - Run end-to-end tests only"
	@echo "  test-performance - Run performance tests only"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  lint             - Run linting checks"
	@echo "  format           - Format code"
	@echo "  security         - Run security checks"
	@echo "  clean            - Clean up test artifacts"
	@echo "  setup-dev        - Set up development environment"

# Installation
install:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio httpx black isort flake8 mypy bandit safety

# Test targets
test: clean
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/ -m "unit" -v

test-integration:
	python -m pytest tests/ -m "integration" -v

test-e2e:
	python -m pytest tests/ -m "e2e" -v

test-performance:
	python -m pytest tests/ -m "performance" -v --tb=short

test-coverage:
	python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

test-fast:
	python -m pytest tests/ -m "not slow" -v

test-slow:
	python -m pytest tests/ -m "slow" -v

# Code quality
lint:
	flake8 app/ tests/
	mypy app/ --ignore-missing-imports

format:
	black app/ tests/
	isort app/ tests/

format-check:
	black --check app/ tests/
	isort --check-only app/ tests/

# Security
security:
	bandit -r app/ -f json -o bandit-report.json
	safety check --json --output safety-report.json

# Development setup
setup-dev:
	mkdir -p test_uploads test_models test_outputs
	mkdir -p htmlcov
	pip install -e .

# Cleanup
clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf app/__pycache__/
	rm -rf tests/__pycache__/
	rm -f coverage.xml
	rm -f pytest-report.xml
	rm -f bandit-report.json
	rm -f safety-report.json
	rm -rf test_uploads/
	rm -rf test_models/
	rm -rf test_outputs/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker targets
docker-test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

docker-clean:
	docker-compose -f docker-compose.test.yml down -v
	docker system prune -f

# CI/CD helpers
ci-install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio httpx

ci-test:
	python -m pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing --junitxml=pytest-report.xml

ci-lint:
	black --check --diff app/ tests/
	isort --check-only --diff app/ tests/
	flake8 app/ tests/
	mypy app/ --ignore-missing-imports

ci-security:
	bandit -r app/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true

# Database targets
db-test-setup:
	python -c "from app.storage.database import Base, engine; Base.metadata.create_all(bind=engine)"

db-test-teardown:
	python -c "from app.storage.database import Base, engine; Base.metadata.drop_all(bind=engine)"

# Performance monitoring
perf-profile:
	python -m pytest tests/ -m "performance" --profile --profile-svg

perf-benchmark:
	python -m pytest tests/ -m "performance" --benchmark-only --benchmark-json=benchmark.json

# Documentation
docs-test:
	python -c "import app.main; print('API docs available at /docs')"

# Health checks
health-check:
	python scripts/health_check.py

# Environment validation
validate-env:
	python -c "from app.config import get_settings; print('Configuration valid')"