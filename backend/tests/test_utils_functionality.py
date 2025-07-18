"""
Test the utility functions and custom assertions.

This test file validates that all the test utilities work correctly
and can be used reliably in other test modules.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from tests.utils.test_helpers import (
    create_test_file, create_test_pdf, create_test_json,
    generate_test_id, validate_response_structure,
    measure_execution_time, TestTimer
)
from tests.utils.assertions import (
    assert_http_status, assert_response_structure, assert_performance_threshold,
    assert_file_exists, assert_valid_uuid, assert_datetime_format,
    assert_numeric_range, assert_researcher_data_structure
)
from tests.utils.mock_factories import (
    MockAIService, MockPDFProcessor, create_mock_researcher,
    create_mock_solicitation, create_mock_matching_result
)
from tests.utils.accuracy_metrics import (
    calculate_precision, calculate_recall, calculate_f1_score,
    AccuracyCalculator, GroundTruthValidator
)


class TestTestHelpers:
    """Test the test helper utilities."""
    
    def test_create_test_file(self):
        """Test file creation utility."""
        content = "Test file content"
        file_path = create_test_file(content)
        
        assert Path(file_path).exists()
        with open(file_path, 'r') as f:
            assert f.read() == content
        
        # Cleanup
        Path(file_path).unlink()
    
    def test_create_test_pdf(self):
        """Test PDF creation utility."""
        pdf_path = create_test_pdf("Test PDF content")
        
        assert Path(pdf_path).exists()
        assert pdf_path.endswith('.pdf')
        
        # Cleanup
        Path(pdf_path).unlink()
    
    def test_create_test_json(self):
        """Test JSON file creation utility."""
        test_data = {"key": "value", "number": 42}
        json_path = create_test_json(test_data)
        
        assert Path(json_path).exists()
        with open(json_path, 'r') as f:
            loaded_data = json.load(f)
            assert loaded_data == test_data
        
        # Cleanup
        Path(json_path).unlink()
    
    def test_generate_test_id(self):
        """Test ID generation utility."""
        test_id = generate_test_id("test")
        assert test_id.startswith("test_")
        assert len(test_id) > 5
        
        # Test uniqueness
        id1 = generate_test_id()
        id2 = generate_test_id()
        assert id1 != id2
    
    def test_validate_response_structure(self):
        """Test response structure validation."""
        response_data = {"name": "test", "id": 123, "active": True}
        expected_keys = ["name", "id", "active"]
        
        # Should not raise exception
        assert validate_response_structure(response_data, expected_keys)
        
        # Should raise exception for missing keys
        with pytest.raises(AssertionError):
            validate_response_structure(response_data, ["name", "missing_key"])
    
    def test_measure_execution_time(self):
        """Test execution time measurement."""
        def slow_function():
            import time
            time.sleep(0.1)
            return "result"
        
        result, execution_time = measure_execution_time(slow_function)
        assert result == "result"
        assert execution_time >= 0.1
    
    def test_timer_context_manager(self):
        """Test timer context manager."""
        with TestTimer() as timer:
            import time
            time.sleep(0.05)
        
        assert timer.elapsed >= 0.05


class TestCustomAssertions:
    """Test the custom assertion functions."""
    
    def test_assert_http_status_success(self):
        """Test HTTP status assertion with success."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        # Should not raise exception
        assert_http_status(mock_response, 200)
    
    def test_assert_http_status_failure(self):
        """Test HTTP status assertion with failure."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_response.json.return_value = {"error": "Not found"}
        
        with pytest.raises(Exception):  # pytest.fail raises an exception
            assert_http_status(mock_response, 200)
    
    def test_assert_response_structure(self):
        """Test response structure assertion."""
        response_data = {
            "name": "test",
            "count": 42,
            "items": ["a", "b", "c"]
        }
        
        expected_structure = {
            "name": str,
            "count": int,
            "items": list
        }
        
        # Should not raise exception
        assert_response_structure(response_data, expected_structure)
        
        # Should raise exception for wrong type
        with pytest.raises(Exception):
            wrong_structure = {"name": int}  # name should be str
            assert_response_structure(response_data, wrong_structure)
    
    def test_assert_performance_threshold(self):
        """Test performance threshold assertion."""
        # Should not raise exception
        assert_performance_threshold(0.5, 1.0, "Test operation")
        
        # Should raise exception
        with pytest.raises(Exception):
            assert_performance_threshold(2.0, 1.0, "Slow operation")
    
    def test_assert_file_exists(self):
        """Test file existence assertion."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        # Should not raise exception
        assert_file_exists(tmp_path)
        
        # Cleanup
        Path(tmp_path).unlink()
        
        # Should raise exception for non-existent file
        with pytest.raises(Exception):
            assert_file_exists(tmp_path)
    
    def test_assert_valid_uuid(self):
        """Test UUID validation assertion."""
        import uuid
        
        valid_uuid = str(uuid.uuid4())
        assert_valid_uuid(valid_uuid)
        
        # Should raise exception for invalid UUID
        with pytest.raises(Exception):
            assert_valid_uuid("not-a-uuid")
    
    def test_assert_datetime_format(self):
        """Test datetime format assertion."""
        valid_datetime = "2024-01-15T10:30:00"
        assert_datetime_format(valid_datetime)
        
        # Should raise exception for invalid format
        with pytest.raises(Exception):
            assert_datetime_format("invalid-datetime")
    
    def test_assert_numeric_range(self):
        """Test numeric range assertion."""
        # Should not raise exception
        assert_numeric_range(5.0, 0.0, 10.0)
        assert_numeric_range(5.0, min_val=0.0)
        assert_numeric_range(5.0, max_val=10.0)
        
        # Should raise exception for out of range
        with pytest.raises(Exception):
            assert_numeric_range(15.0, 0.0, 10.0)
    
    def test_assert_researcher_data_structure(self):
        """Test researcher data structure assertion."""
        valid_researcher = {
            "name": "Dr. Test Researcher",
            "email": "test@university.edu",
            "institution": "Test University",
            "expertise": ["AI", "ML"]
        }
        
        # Should not raise exception
        assert_researcher_data_structure(valid_researcher)
        
        # Should raise exception for missing required field
        invalid_researcher = {
            "name": "Dr. Test Researcher",
            # missing email
            "institution": "Test University",
            "expertise": ["AI", "ML"]
        }
        
        with pytest.raises(Exception):
            assert_researcher_data_structure(invalid_researcher)


class TestMockFactories:
    """Test the mock factory functions."""
    
    def test_mock_ai_service(self):
        """Test MockAIService functionality."""
        mock_service = MockAIService()
        
        # Test text analysis
        result = mock_service.analyze_text("test text")
        assert "keywords" in result
        assert "summary" in result
        assert mock_service.call_count == 1
        
        # Test embeddings
        embeddings = mock_service.generate_embeddings("test text")
        assert isinstance(embeddings, list)
        assert len(embeddings) > 0
        assert mock_service.call_count == 2
    
    def test_mock_pdf_processor(self):
        """Test MockPDFProcessor functionality."""
        mock_processor = MockPDFProcessor()
        
        # Test text extraction
        text = mock_processor.extract_text("test.pdf")
        assert isinstance(text, str)
        assert len(text) > 0
        assert "test.pdf" in mock_processor.processed_files
        
        # Test metadata extraction
        metadata = mock_processor.extract_metadata("test.pdf")
        assert "title" in metadata
        assert "pages" in metadata
    
    def test_create_mock_researcher(self):
        """Test mock researcher creation."""
        researcher = create_mock_researcher()
        
        assert "id" in researcher
        assert "name" in researcher
        assert "email" in researcher
        assert "expertise" in researcher
        assert isinstance(researcher["expertise"], list)
        
        # Test with custom parameters
        custom_researcher = create_mock_researcher(
            name="Custom Researcher",
            expertise=["custom", "expertise"]
        )
        assert custom_researcher["name"] == "Custom Researcher"
        assert custom_researcher["expertise"] == ["custom", "expertise"]
    
    def test_create_mock_solicitation(self):
        """Test mock solicitation creation."""
        solicitation = create_mock_solicitation()
        
        assert "id" in solicitation
        assert "title" in solicitation
        assert "keywords" in solicitation
        assert isinstance(solicitation["keywords"], list)
        
        # Test with custom parameters
        custom_solicitation = create_mock_solicitation(
            title="Custom Solicitation",
            keywords=["custom", "keywords"]
        )
        assert custom_solicitation["title"] == "Custom Solicitation"
        assert custom_solicitation["keywords"] == ["custom", "keywords"]
    
    def test_create_mock_matching_result(self):
        """Test mock matching result creation."""
        result = create_mock_matching_result()
        
        assert "researcher_id" in result
        assert "score" in result
        assert "rank" in result
        assert 0.0 <= result["score"] <= 1.0
        
        # Test with custom score
        custom_result = create_mock_matching_result(score=0.85)
        assert custom_result["score"] == 0.85


class TestAccuracyMetrics:
    """Test the accuracy metrics calculations."""
    
    def test_calculate_precision(self):
        """Test precision calculation."""
        predicted = ["a", "b", "c"]
        actual = ["a", "b", "d"]
        
        precision = calculate_precision(predicted, actual)
        assert precision == 2/3  # 2 correct out of 3 predicted
        
        # Test edge cases
        assert calculate_precision([], ["a", "b"]) == 0.0
        assert calculate_precision(["a"], ["a"]) == 1.0
    
    def test_calculate_recall(self):
        """Test recall calculation."""
        predicted = ["a", "b", "c"]
        actual = ["a", "b", "d"]
        
        recall = calculate_recall(predicted, actual)
        assert recall == 2/3  # 2 correct out of 3 actual
        
        # Test edge cases
        assert calculate_recall(["a"], []) == 1.0
        assert calculate_recall([], ["a"]) == 0.0
    
    def test_calculate_f1_score(self):
        """Test F1 score calculation."""
        precision = 0.8
        recall = 0.6
        
        f1 = calculate_f1_score(precision, recall)
        expected_f1 = 2 * (0.8 * 0.6) / (0.8 + 0.6)
        assert abs(f1 - expected_f1) < 0.001
        
        # Test edge case
        assert calculate_f1_score(0.0, 0.0) == 0.0
    
    def test_accuracy_calculator(self):
        """Test AccuracyCalculator class."""
        calculator = AccuracyCalculator()
        
        # Add some results
        calculator.add_result(["a", "b"], ["a", "c"])
        calculator.add_result(["x", "y"], ["x", "y"])
        
        # Get aggregate metrics
        aggregate = calculator.get_aggregate_metrics()
        assert "precision" in aggregate
        assert "recall" in aggregate
        assert "f1_score" in aggregate
        
        # Get detailed report
        report = calculator.get_detailed_report()
        assert "individual_results" in report
        assert "aggregate_metrics" in report
        assert "summary" in report
    
    def test_ground_truth_validator(self):
        """Test GroundTruthValidator functionality."""
        valid_ground_truth = {
            "solicitation_id": "test-123",
            "expected_researchers": [
                {"researcher_id": "r1", "relevance_score": 0.9},
                {"researcher_id": "r2", "relevance_score": 0.7}
            ],
            "metadata": {"test": True}
        }
        
        # Should return no errors
        errors = GroundTruthValidator.validate_ground_truth_format(valid_ground_truth)
        assert len(errors) == 0
        
        # Test invalid format
        invalid_ground_truth = {
            "solicitation_id": "test-123"
            # missing required fields
        }
        
        errors = GroundTruthValidator.validate_ground_truth_format(invalid_ground_truth)
        assert len(errors) > 0


@pytest.mark.integration
class TestUtilsIntegration:
    """Integration tests for utility functions working together."""
    
    def test_end_to_end_testing_workflow(self):
        """Test a complete testing workflow using all utilities."""
        # Create mock data
        researcher = create_mock_researcher()
        solicitation = create_mock_solicitation()
        
        # Create mock services
        ai_service = MockAIService()
        pdf_processor = MockPDFProcessor()
        
        # Test AI service
        analysis = ai_service.analyze_text(solicitation["description"])
        assert "keywords" in analysis
        
        # Test PDF processing
        pdf_path = create_test_pdf("Test solicitation content")
        extracted_text = pdf_processor.extract_text(pdf_path)
        assert len(extracted_text) > 0
        
        # Create mock matching results
        matching_results = [
            create_mock_matching_result(score=0.9),
            create_mock_matching_result(score=0.8),
            create_mock_matching_result(score=0.7)
        ]
        
        # Test accuracy calculations
        ground_truth = [matching_results[0]["researcher_id"], matching_results[1]["researcher_id"]]
        predicted = [r["researcher_id"] for r in matching_results[:2]]
        
        precision = calculate_precision(predicted, ground_truth)
        assert precision == 1.0  # Perfect match
        
        # Test assertions
        assert_numeric_range(precision, 0.0, 1.0)
        assert_researcher_data_structure(researcher)
        
        # Cleanup
        Path(pdf_path).unlink()
    
    def test_performance_testing_workflow(self):
        """Test performance testing utilities."""
        def mock_matching_algorithm():
            import time
            time.sleep(0.01)  # Simulate processing time
            return ["researcher1", "researcher2", "researcher3"]
        
        # Measure execution time
        results, execution_time = measure_execution_time(mock_matching_algorithm)
        
        # Test performance assertion
        assert_performance_threshold(execution_time, 0.1, "Matching algorithm")
        
        # Test results
        assert len(results) == 3
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])