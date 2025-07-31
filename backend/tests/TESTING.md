# Testing Guide

## Overview

The NSF Researcher Matching API uses a simplified, pragmatic testing approach that prioritizes fast feedback and maintainable tests. This guide explains the current testing infrastructure and provides best practices for writing effective tests.

## Philosophy

Our testing approach follows these core principles:

1. **Start Simple**: Begin with basic fixtures and grow complexity as needed
2. **Pragmatic Coverage**: Focus on critical paths and business logic
3. **Fast Feedback**: Prioritize fast-running tests for development workflow
4. **Realistic Data**: Use meaningful test data that reflects real-world scenarios
5. **Isolated Tests**: Each test runs independently with proper cleanup

## Current Test Infrastructure

### Test Configuration (`conftest.py`)

The simplified test configuration provides three essential fixtures:

```python
@pytest.fixture
def test_client():
    """Create a test client for API testing."""
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

### Pytest Configuration (`pytest.ini`)

The project includes comprehensive pytest configuration with:
- Coverage reporting (HTML, XML, terminal)
- Test categorization with markers
- Environment variables for testing
- Asyncio support
- Warning filters

## Writing Tests

### Basic API Test

```python
def test_health_endpoint(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
```

### File Processing Test

```python
def test_pdf_upload(test_client, temp_dir, sample_pdf_content):
    """Test PDF file upload functionality."""
    # Create test PDF file
    pdf_path = Path(temp_dir) / "test.pdf"
    pdf_path.write_bytes(sample_pdf_content)
    
    # Test file upload
    with open(pdf_path, "rb") as f:
        response = test_client.post(
            "/solicitations/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 200
    assert "solicitation_id" in response.json()
```

### Service Layer Test

```python
def test_matching_service():
    """Test matching service logic."""
    from app.services.matching_service import MatchingService
    
    service = MatchingService()
    
    # Test with sample data
    solicitation_data = {
        "title": "AI Research Grant",
        "description": "Machine learning and artificial intelligence research"
    }
    
    researchers = [
        {"name": "Dr. Smith", "expertise": ["machine learning", "AI"]},
        {"name": "Dr. Jones", "expertise": ["biology", "chemistry"]}
    ]
    
    matches = service.find_matches(solicitation_data, researchers)
    
    assert len(matches) > 0
    assert matches[0]["name"] == "Dr. Smith"  # Better match should be first
```

## Test Categories

Use pytest markers to categorize tests:

### Unit Tests
```python
import pytest

@pytest.mark.unit
def test_pdf_text_extraction():
    """Test PDF text extraction utility."""
    # Test individual function
    pass
```

### Integration Tests
```python
@pytest.mark.integration
def test_full_matching_workflow(test_client):
    """Test complete matching workflow."""
    # Test multiple components working together
    pass
```

### Performance Tests
```python
@pytest.mark.performance
def test_matching_performance(test_client):
    """Test matching algorithm performance."""
    import time
    
    start_time = time.time()
    # Run matching algorithm
    end_time = time.time()
    
    assert (end_time - start_time) < 5.0  # Should complete in under 5 seconds
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_api/test_solicitations.py

# Run specific test function
python -m pytest tests/test_api/test_solicitations.py::test_upload_pdf
```

### Test Categories
```bash
# Run only unit tests
python -m pytest -m unit

# Run integration tests
python -m pytest -m integration

# Skip slow tests
python -m pytest -m "not slow"

# Run multiple categories
python -m pytest -m "unit or integration"
```

### Coverage Reporting
```bash
# Basic coverage
python -m pytest --cov=app

# HTML coverage report
python -m pytest --cov=app --cov-report=html

# Coverage with missing lines
python -m pytest --cov=app --cov-report=term-missing

# Fail if coverage below threshold
python -m pytest --cov=app --cov-fail-under=80
```

## Test Data Management

### Creating Test Data

```python
# Simple test data
def test_researcher_model():
    researcher_data = {
        "name": "Dr. Test",
        "institution": "Test University",
        "expertise": ["testing", "quality assurance"]
    }
    
    researcher = Researcher(**researcher_data)
    assert researcher.name == "Dr. Test"
```

### Using Temporary Files

```python
def test_file_processing(temp_dir):
    """Test file processing with temporary directory."""
    # Create test file
    test_file = Path(temp_dir) / "data.json"
    test_file.write_text('{"test": "data"}')
    
    # Process file
    result = process_file(test_file)
    
    # Verify result
    assert result["test"] == "data"
    
    # Cleanup is automatic via fixture
```

## Best Practices

### Test Structure
1. **Arrange**: Set up test data and conditions
2. **Act**: Execute the code being tested
3. **Assert**: Verify the results

```python
def test_matching_algorithm():
    # Arrange
    solicitation = create_test_solicitation()
    researchers = create_test_researchers()
    
    # Act
    matches = run_matching(solicitation, researchers)
    
    # Assert
    assert len(matches) > 0
    assert matches[0].score > 0.5
```

### Test Naming
- Use descriptive names that explain what is being tested
- Follow the pattern: `test_[what]_[when]_[expected]`

```python
def test_matching_returns_empty_list_when_no_researchers():
    """Test that matching returns empty list when no researchers available."""
    pass

def test_pdf_upload_fails_with_invalid_file_format():
    """Test that PDF upload fails gracefully with invalid file format."""
    pass
```

### Error Testing
```python
def test_api_returns_404_for_nonexistent_solicitation(test_client):
    """Test API returns 404 for non-existent solicitation."""
    response = test_client.get("/solicitations/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### Async Testing
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test asynchronous operation."""
    result = await some_async_function()
    assert result is not None
```

## Debugging Tests

### Running Single Test with Debug Output
```bash
# Run single test with print statements
python -m pytest tests/test_api/test_solicitations.py::test_upload_pdf -s

# Run with pdb debugger
python -m pytest tests/test_api/test_solicitations.py::test_upload_pdf --pdb
```

### Using Print Statements
```python
def test_debug_example(test_client):
    """Example test with debug output."""
    response = test_client.get("/health")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == 200
```

## Future Enhancements

As the project grows, the testing infrastructure will expand to include:

### Advanced Fixtures
- Database fixtures with test data
- Mock services for external dependencies
- Authentication fixtures for secured endpoints
- Complex test scenarios with multiple components

### Performance Testing
- Load testing with multiple concurrent requests
- Memory usage monitoring
- Response time benchmarking
- Stress testing for edge cases

### Ground-Truth Validation
- Historical data validation
- Accuracy metrics calculation
- Regression testing against known results
- A/B testing for algorithm improvements

### Test Automation
- Continuous integration hooks
- Automated test data generation
- Test result reporting and analysis
- Flaky test detection and management

## Common Patterns

### Testing API Endpoints
```python
def test_api_endpoint_pattern(test_client):
    """Common pattern for testing API endpoints."""
    # Test successful request
    response = test_client.get("/endpoint")
    assert response.status_code == 200
    
    # Test with parameters
    response = test_client.get("/endpoint?param=value")
    assert response.status_code == 200
    
    # Test error conditions
    response = test_client.get("/endpoint/invalid")
    assert response.status_code == 404
```

### Testing Business Logic
```python
def test_business_logic_pattern():
    """Common pattern for testing business logic."""
    # Test normal case
    result = business_function(valid_input)
    assert result.is_valid()
    
    # Test edge cases
    result = business_function(edge_case_input)
    assert result.handles_edge_case()
    
    # Test error cases
    with pytest.raises(ValueError):
        business_function(invalid_input)
```

### Testing File Operations
```python
def test_file_operation_pattern(temp_dir):
    """Common pattern for testing file operations."""
    # Create test file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("test content")
    
    # Test file operation
    result = process_file(test_file)
    
    # Verify result
    assert result is not None
    
    # Verify file state
    assert test_file.exists()  # or not, depending on operation
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes the app directory
2. **File Permissions**: Use temp_dir fixture for file operations
3. **Async Issues**: Use `@pytest.mark.asyncio` for async tests
4. **Coverage Issues**: Ensure test files are in the correct location

### Getting Help

1. Check pytest documentation: https://docs.pytest.org/
2. Review existing tests in the codebase
3. Use `python -m pytest --help` for command options
4. Check the project's GitHub issues for testing-related questions

## Contributing

When adding new tests:

1. Follow the existing patterns and conventions
2. Add appropriate markers for test categorization
3. Include docstrings explaining what the test does
4. Ensure tests are isolated and don't depend on external state
5. Update this guide if you add new testing patterns or utilities

Remember: Good tests are simple, focused, and maintainable. Start with basic assertions and add complexity only when needed.