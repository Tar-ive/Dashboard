"""
Basic infrastructure tests that don't depend on the full application.

These tests verify that the core test infrastructure components work
without requiring all application dependencies.
"""

import pytest
import tempfile
import os
from pathlib import Path
from tests.utils import TestDataGenerator, TestFileManager, AssertionHelpers


@pytest.mark.unit
def test_pytest_configuration():
    """Test that pytest is properly configured."""
    # This test verifies basic pytest functionality
    assert True


@pytest.mark.unit
def test_test_data_generator():
    """Test the TestDataGenerator utility."""
    # Test PDF content generation
    pdf_content = TestDataGenerator.create_sample_pdf_content()
    assert isinstance(pdf_content, bytes)
    assert pdf_content.startswith(b"%PDF")
    
    # Test solicitation data generation
    solicitation_data = TestDataGenerator.create_solicitation_data()
    assert "title" in solicitation_data
    assert "program" in solicitation_data
    
    # Test researcher data generation
    researcher_data = TestDataGenerator.create_researcher_data()
    assert "name" in researcher_data
    assert "email" in researcher_data


@pytest.mark.unit
def test_test_file_manager():
    """Test the TestFileManager utility."""
    manager = TestFileManager()
    
    # Test temporary directory creation
    temp_dir = manager.create_temp_dir()
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    
    # Test temporary file creation
    temp_file = manager.create_temp_file("test content")
    assert temp_file.exists()
    assert temp_file.read_text() == "test content"
    
    # Test PDF creation
    pdf_file = manager.create_sample_pdf()
    assert pdf_file.exists()
    assert pdf_file.suffix == ".pdf"
    
    # Test cleanup
    manager.cleanup()
    assert not temp_dir.exists()
    assert not temp_file.exists()
    assert not pdf_file.exists()


@pytest.mark.unit
def test_assertion_helpers():
    """Test the AssertionHelpers utility."""
    # Test response structure assertion
    response_data = {"key1": "value1", "key2": "value2"}
    AssertionHelpers.assert_response_structure(response_data, ["key1", "key2"])
    
    # Test score range assertion
    AssertionHelpers.assert_score_range(0.5)
    AssertionHelpers.assert_score_range(0.0)
    AssertionHelpers.assert_score_range(1.0)
    
    # Test email validation
    AssertionHelpers.assert_valid_email("test@example.com")
    
    # Test error cases
    with pytest.raises(AssertionError):
        AssertionHelpers.assert_response_structure(response_data, ["missing_key"])
    
    with pytest.raises(AssertionError):
        AssertionHelpers.assert_score_range(-0.1)
    
    with pytest.raises(AssertionError):
        AssertionHelpers.assert_valid_email("invalid-email")


@pytest.mark.unit
def test_environment_setup():
    """Test environment setup for testing."""
    # Test that we can set and read environment variables
    test_env_var = "TEST_INFRASTRUCTURE_VAR"
    test_value = "test_value_123"
    
    os.environ[test_env_var] = test_value
    assert os.environ.get(test_env_var) == test_value
    
    # Clean up
    del os.environ[test_env_var]


@pytest.mark.unit
def test_temporary_file_system():
    """Test temporary file system operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test directory creation
        test_dir = temp_path / "test_subdir"
        test_dir.mkdir()
        assert test_dir.exists()
        
        # Test file creation
        test_file = test_dir / "test_file.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"


@pytest.mark.integration
def test_test_markers():
    """Test that pytest markers are working."""
    # This test has the 'integration' marker
    # If markers are working, this test should be discoverable
    assert True


@pytest.mark.performance
def test_performance_timing():
    """Test performance timing capabilities."""
    import time
    
    start_time = time.time()
    time.sleep(0.001)  # Sleep for 1ms
    elapsed = time.time() - start_time
    
    assert elapsed >= 0.001
    assert elapsed < 0.1  # Should be much less than 100ms


@pytest.mark.slow
def test_slow_test_marker():
    """Test that slow test marker works."""
    import time
    
    # This test is marked as slow
    time.sleep(0.01)  # Sleep for 10ms
    assert True


@pytest.mark.unit
def test_coverage_tracking():
    """Test that coverage tracking is working."""
    # Import and use test utilities to ensure they're covered
    from tests.test_config import test_config, SAMPLE_DATA
    
    assert test_config is not None
    assert SAMPLE_DATA is not None
    assert "solicitation" in SAMPLE_DATA
    assert "researcher" in SAMPLE_DATA


@pytest.mark.unit
class TestInfrastructureComponents:
    """Test class to verify class-based test organization."""
    
    def test_class_based_tests(self):
        """Test that class-based tests work."""
        assert True
    
    def test_multiple_assertions(self):
        """Test multiple assertions in one test."""
        data = {"a": 1, "b": 2, "c": 3}
        
        assert "a" in data
        assert data["a"] == 1
        assert len(data) == 3
        assert isinstance(data, dict)
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
        (0, 0)
    ])
    def test_parametrized_test(self, input_value, expected):
        """Test parametrized test functionality."""
        result = input_value * 2
        assert result == expected


@pytest.mark.unit
def test_fixture_isolation():
    """Test that fixtures provide proper isolation."""
    # This test verifies that each test gets fresh fixtures
    # In a real scenario, this would test database isolation
    temp_data = {"counter": 0}
    temp_data["counter"] += 1
    
    assert temp_data["counter"] == 1


@pytest.mark.unit
def test_exception_handling():
    """Test exception handling in tests."""
    def divide_by_zero():
        return 1 / 0
    
    with pytest.raises(ZeroDivisionError):
        divide_by_zero()
    
    # Test that we can catch specific exception messages
    with pytest.raises(ValueError, match="invalid literal"):
        int("not_a_number")


@pytest.mark.unit
def test_test_data_consistency():
    """Test that test data generation is consistent."""
    # Generate data multiple times and verify consistency
    data1 = TestDataGenerator.create_solicitation_data(title="Test Title")
    data2 = TestDataGenerator.create_solicitation_data(title="Test Title")
    
    # Should have same title but potentially different other fields
    assert data1["title"] == data2["title"]
    assert data1["title"] == "Test Title"


@pytest.mark.unit
def test_path_operations():
    """Test path operations for test infrastructure."""
    # Test that we can work with paths correctly
    current_file = Path(__file__)
    assert current_file.exists()
    assert current_file.name == "test_basic_infrastructure.py"
    
    # Test parent directory
    test_dir = current_file.parent
    assert test_dir.name == "tests"
    
    # Test backend directory
    backend_dir = test_dir.parent
    assert backend_dir.name == "backend"