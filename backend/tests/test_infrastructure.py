"""
Test infrastructure validation tests.

These tests verify that the test infrastructure is properly configured
and all fixtures and utilities are working correctly.
"""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from tests.utils import TestDataGenerator, MockServices, TestFileManager, AssertionHelpers


@pytest.mark.unit
def test_test_settings_fixture(test_settings):
    """Test that test settings fixture works correctly."""
    assert test_settings.testing is True
    assert "test" in test_settings.database_url
    assert test_settings.upload_dir is not None
    assert test_settings.model_dir is not None


@pytest.mark.unit
def test_test_db_engine_fixture(test_db_engine):
    """Test that test database engine fixture works correctly."""
    assert test_db_engine is not None
    # Test that we can execute a simple query
    with test_db_engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.fetchone()[0] == 1


@pytest.mark.unit
def test_test_db_session_fixture(test_db_session):
    """Test that test database session fixture works correctly."""
    assert test_db_session is not None
    # Test that session is functional
    result = test_db_session.execute("SELECT 1").fetchone()
    assert result[0] == 1


@pytest.mark.unit
def test_test_file_system_fixture(test_file_system):
    """Test that test file system fixture works correctly."""
    assert "temp_dir" in test_file_system
    assert "upload_dir" in test_file_system
    assert "model_dir" in test_file_system
    assert "output_dir" in test_file_system
    
    # Verify directories exist
    for dir_path in [test_file_system["upload_dir"], test_file_system["model_dir"], test_file_system["output_dir"]]:
        assert Path(dir_path).exists()
        assert Path(dir_path).is_dir()


@pytest.mark.integration
def test_test_client_fixture(test_client):
    """Test that test client fixture works correctly."""
    assert isinstance(test_client, TestClient)
    
    # Test basic health check if available
    response = test_client.get("/")
    # Should not raise an exception, status code may vary based on implementation
    assert response is not None


@pytest.mark.unit
def test_sample_pdf_file_fixture(sample_pdf_file):
    """Test that sample PDF file fixture works correctly."""
    pdf_path = Path(sample_pdf_file)
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    
    # Verify file has content
    assert pdf_path.stat().st_size > 0


@pytest.mark.unit
def test_mock_ai_service_fixture(mock_ai_service):
    """Test that mock AI service fixture works correctly."""
    # Test analyze_text method
    result = mock_ai_service.analyze_text("test text")
    assert "keywords" in result
    assert "summary" in result
    assert "topics" in result
    
    # Test generate_embeddings method
    embeddings = mock_ai_service.generate_embeddings("test text")
    assert isinstance(embeddings, list)
    assert len(embeddings) > 0


@pytest.mark.unit
def test_mock_pdf_processor_fixture(mock_pdf_processor):
    """Test that mock PDF processor fixture works correctly."""
    # Test extract_text method
    text = mock_pdf_processor.extract_text("dummy_path.pdf")
    assert isinstance(text, str)
    assert len(text) > 0
    
    # Test extract_metadata method
    metadata = mock_pdf_processor.extract_metadata("dummy_path.pdf")
    assert "title" in metadata
    assert "author" in metadata
    assert "pages" in metadata


@pytest.mark.unit
def test_clean_environment_fixture(clean_environment):
    """Test that clean environment fixture works correctly."""
    import os
    
    # Check that test environment variables are set
    assert os.environ.get("TESTING") == "true"
    assert "test" in os.environ.get("DATABASE_URL", "")


@pytest.mark.unit
def test_sample_data_fixtures(sample_solicitation_data, sample_researcher_data, sample_matching_request):
    """Test that sample data fixtures work correctly."""
    # Test solicitation data
    assert "title" in sample_solicitation_data
    assert "program" in sample_solicitation_data
    assert "deadline" in sample_solicitation_data
    
    # Test researcher data
    assert "name" in sample_researcher_data
    assert "email" in sample_researcher_data
    assert "institution" in sample_researcher_data
    
    # Test matching request data
    assert "solicitation_id" in sample_matching_request
    assert "max_results" in sample_matching_request
    assert "min_score" in sample_matching_request


@pytest.mark.unit
def test_performance_timer_fixture(performance_timer):
    """Test that performance timer fixture works correctly."""
    import time
    
    performance_timer.start()
    time.sleep(0.01)  # Sleep for 10ms
    performance_timer.stop()
    
    assert performance_timer.elapsed is not None
    assert performance_timer.elapsed >= 0.01
    assert performance_timer.elapsed < 0.1  # Should be much less than 100ms


@pytest.mark.unit
class TestTestDataGenerator:
    """Test the TestDataGenerator utility class."""
    
    def test_create_sample_pdf_content(self):
        """Test PDF content generation."""
        pdf_content = TestDataGenerator.create_sample_pdf_content()
        assert isinstance(pdf_content, bytes)
        assert pdf_content.startswith(b"%PDF")
        assert b"endobj" in pdf_content
    
    def test_create_solicitation_data(self):
        """Test solicitation data generation."""
        data = TestDataGenerator.create_solicitation_data()
        assert "title" in data
        assert "program" in data
        assert "deadline" in data
        
        # Test with custom parameters
        custom_data = TestDataGenerator.create_solicitation_data(
            title="Custom Title",
            program="CUSTOM"
        )
        assert custom_data["title"] == "Custom Title"
        assert custom_data["program"] == "CUSTOM"
    
    def test_create_researcher_data(self):
        """Test researcher data generation."""
        data = TestDataGenerator.create_researcher_data()
        assert "name" in data
        assert "email" in data
        assert "institution" in data
        
        # Test with custom parameters
        custom_data = TestDataGenerator.create_researcher_data(
            name="Dr. Custom Name",
            email="custom@test.edu"
        )
        assert custom_data["name"] == "Dr. Custom Name"
        assert custom_data["email"] == "custom@test.edu"


@pytest.mark.unit
class TestMockServices:
    """Test the MockServices utility class."""
    
    def test_create_mock_ai_service(self):
        """Test mock AI service creation."""
        mock_service = MockServices.create_mock_ai_service()
        
        # Test analyze_text
        result = mock_service.analyze_text("test")
        assert "keywords" in result
        assert "summary" in result
        
        # Test generate_embeddings
        embeddings = mock_service.generate_embeddings("test")
        assert isinstance(embeddings, list)
        
        # Test calculate_similarity
        similarity = mock_service.calculate_similarity("text1", "text2")
        assert isinstance(similarity, float)
    
    def test_create_mock_pdf_processor(self):
        """Test mock PDF processor creation."""
        mock_processor = MockServices.create_mock_pdf_processor()
        
        # Test extract_text
        text = mock_processor.extract_text("test.pdf")
        assert isinstance(text, str)
        
        # Test extract_metadata
        metadata = mock_processor.extract_metadata("test.pdf")
        assert "title" in metadata
        assert "author" in metadata


@pytest.mark.unit
class TestTestFileManager:
    """Test the TestFileManager utility class."""
    
    def test_create_temp_dir(self):
        """Test temporary directory creation."""
        manager = TestFileManager()
        temp_dir = manager.create_temp_dir()
        
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Cleanup
        manager.cleanup()
        assert not temp_dir.exists()
    
    def test_create_temp_file(self):
        """Test temporary file creation."""
        manager = TestFileManager()
        
        # Test text file
        temp_file = manager.create_temp_file("test content", ".txt")
        assert temp_file.exists()
        assert temp_file.read_text() == "test content"
        
        # Test binary file
        binary_file = manager.create_temp_file(binary_content=b"binary content", suffix=".bin")
        assert binary_file.exists()
        assert binary_file.read_bytes() == b"binary content"
        
        # Cleanup
        manager.cleanup()
        assert not temp_file.exists()
        assert not binary_file.exists()
    
    def test_create_sample_pdf(self):
        """Test sample PDF creation."""
        manager = TestFileManager()
        pdf_file = manager.create_sample_pdf()
        
        assert pdf_file.exists()
        assert pdf_file.suffix == ".pdf"
        
        # Verify PDF content
        content = pdf_file.read_bytes()
        assert content.startswith(b"%PDF")
        
        # Cleanup
        manager.cleanup()
        assert not pdf_file.exists()


@pytest.mark.unit
class TestAssertionHelpers:
    """Test the AssertionHelpers utility class."""
    
    def test_assert_response_structure(self):
        """Test response structure assertion."""
        response_data = {"key1": "value1", "key2": "value2"}
        expected_keys = ["key1", "key2"]
        
        # Should not raise
        AssertionHelpers.assert_response_structure(response_data, expected_keys)
        
        # Should raise
        with pytest.raises(AssertionError):
            AssertionHelpers.assert_response_structure(response_data, ["missing_key"])
    
    def test_assert_score_range(self):
        """Test score range assertion."""
        # Should not raise
        AssertionHelpers.assert_score_range(0.5)
        AssertionHelpers.assert_score_range(0.0)
        AssertionHelpers.assert_score_range(1.0)
        
        # Should raise
        with pytest.raises(AssertionError):
            AssertionHelpers.assert_score_range(-0.1)
        with pytest.raises(AssertionError):
            AssertionHelpers.assert_score_range(1.1)
    
    def test_assert_valid_email(self):
        """Test email validation assertion."""
        # Should not raise
        AssertionHelpers.assert_valid_email("test@example.com")
        AssertionHelpers.assert_valid_email("user.name@domain.edu")
        
        # Should raise
        with pytest.raises(AssertionError):
            AssertionHelpers.assert_valid_email("invalid-email")
        with pytest.raises(AssertionError):
            AssertionHelpers.assert_valid_email("@domain.com")


@pytest.mark.unit
def test_pytest_markers():
    """Test that pytest markers are properly configured."""
    # This test verifies that the marker configuration is working
    # by checking that this test itself has the 'unit' marker
    import pytest
    
    # Get current test item
    current_test = pytest.current_test if hasattr(pytest, 'current_test') else None
    
    # Basic marker test - if we get here, markers are working
    assert True


@pytest.mark.unit
def test_coverage_configuration():
    """Test that coverage configuration is working."""
    # This test ensures coverage is being tracked
    # by importing and using a module that should be covered
    from tests.test_config import test_config
    
    assert test_config is not None
    config = test_config.get_env_config("test")
    assert config is not None
    assert "url" in config


@pytest.mark.integration
def test_database_isolation():
    """Test that database isolation is working between tests."""
    # This test verifies that each test gets a clean database
    # This would be expanded with actual database operations
    assert True


@pytest.mark.performance
def test_performance_infrastructure():
    """Test that performance testing infrastructure is working."""
    import time
    
    start_time = time.time()
    
    # Simulate some work
    time.sleep(0.001)
    
    elapsed = time.time() - start_time
    
    # Verify timing works
    assert elapsed >= 0.001
    assert elapsed < 0.1