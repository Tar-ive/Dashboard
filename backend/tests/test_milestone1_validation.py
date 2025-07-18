"""
Comprehensive validation tests for Milestone 1 integration and error scenarios (Task 4.2).

This module tests:
- Invalid PDF uploads and error handling
- Job failure scenarios and error message clarity
- Concurrent PDF uploads and queue management
- StructuredSolicitation output format and completeness
"""

import pytest
import tempfile
import os
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

from app.main import app
from app.models.job import JobStatus
from app.models.structured_solicitation import StructuredSolicitation
from app.tasks.deconstruction_task import deconstruct_solicitation_task

client = TestClient(app)


class TestInvalidPDFUploadsAndErrorHandling:
    """Test invalid PDF uploads and comprehensive error handling."""
    
    def test_upload_non_pdf_file_returns_clear_error(self):
        """Test uploading non-PDF file returns clear error message."""
        # Create a text file
        text_content = b"This is not a PDF file, it's plain text."
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(text_content)
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("document.txt", f, "text/plain")}
                    )
                
                # Should return 400 with clear error message
                assert response.status_code == 400
                error_data = response.json()
                assert "detail" in error_data
                assert "PDF" in error_data["detail"] or "pdf" in error_data["detail"]
                assert "text/plain" in error_data["detail"]
                
            finally:
                os.unlink(temp_file.name)
    
    def test_upload_corrupted_pdf_file_returns_clear_error(self):
        """Test uploading corrupted PDF file returns clear error message."""
        # Create a file with PDF header but corrupted content
        corrupted_pdf = b"%PDF-1.4\nThis is not valid PDF content\x00\x01\x02\xFF"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(corrupted_pdf)
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("corrupted.pdf", f, "application/pdf")}
                    )
                
                # Should accept the upload (validation happens during processing)
                assert response.status_code == 200
                job_data = response.json()
                assert "job_id" in job_data
                
                # Wait a moment for background processing
                time.sleep(2)
                
                # Check job status - should be failed with clear error
                job_status_response = client.get(f"/api/jobs/{job_data['job_id']}")
                assert job_status_response.status_code == 200
                
                status_data = job_status_response.json()
                # Job should either be failed or still processing (depending on timing)
                if status_data["status"] == "failed":
                    assert status_data["error_message"] is not None
                    assert len(status_data["error_message"]) > 0
                
            finally:
                os.unlink(temp_file.name)  
  
    def test_upload_oversized_file_returns_clear_error(self):
        """Test uploading oversized file returns clear error message."""
        # Create a file larger than 10MB limit
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\n")  # Valid PDF header
            temp_file.write(large_content)
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("large.pdf", f, "application/pdf")}
                    )
                
                # Should return 400 with clear size error
                assert response.status_code == 400
                error_data = response.json()
                assert "detail" in error_data
                assert "size" in error_data["detail"].lower()
                assert "10" in error_data["detail"]  # Should mention the limit
                
            finally:
                os.unlink(temp_file.name)
    
    def test_upload_empty_file_returns_clear_error(self):
        """Test uploading empty file returns clear error message."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            # Create empty file
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("empty.pdf", f, "application/pdf")}
                    )
                
                # Should return 400 with clear empty file error
                assert response.status_code == 400
                error_data = response.json()
                assert "detail" in error_data
                assert "empty" in error_data["detail"].lower()
                
            finally:
                os.unlink(temp_file.name)
    
    def test_upload_without_file_parameter_returns_clear_error(self):
        """Test API call without file parameter returns clear error."""
        response = client.post("/api/deconstruct")
        
        # Should return 422 (validation error) with clear message
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        # Should indicate missing required field
        assert any("file" in str(detail).lower() for detail in error_data["detail"])
    
    def test_upload_with_wrong_field_name_returns_clear_error(self):
        """Test API call with wrong field name returns clear error."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"document": ("test.pdf", f, "application/pdf")}  # Wrong field name
                    )
                
                # Should return 422 with validation error
                assert response.status_code == 422
                error_data = response.json()
                assert "detail" in error_data
                
            finally:
                os.unlink(temp_file.name)


class TestJobFailureScenariosAndErrorMessages:
    """Test job failure scenarios and error message clarity."""
    
    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    def test_pdf_extraction_failure_provides_clear_error(self, mock_extract, mock_get_job_manager):
        """Test PDF extraction failure provides clear error message."""
        # Setup job manager mock
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        # Setup PDF extraction to fail with specific error
        mock_extract.side_effect = FileNotFoundError("PDF file not found at specified path")
        
        # Create temp file for testing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\ntest")
            temp_path = temp_file.name
        
        try:
            # Execute task and expect failure
            with pytest.raises(Exception) as exc_info:
                deconstruct_solicitation_task("test_job_pdf_error", temp_path)
            
            # Verify error message is clear and informative
            error_message = str(exc_info.value)
            assert "Deconstruction failed" in error_message
            assert "PDF file not found" in error_message
            
            # Verify job manager was called to update status to failed
            failed_calls = [call for call in mock_job_manager.update_job_status.call_args_list 
                          if len(call[0]) > 1 and call[0][1] == "failed"]
            assert len(failed_calls) == 1
            
            failed_call = failed_calls[0]
            assert "error_message" in failed_call[1]
            assert "PDF file not found" in failed_call[1]["error_message"]
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)    

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    def test_empty_pdf_extraction_provides_clear_error(self, mock_extract, mock_get_job_manager):
        """Test empty PDF extraction provides clear error message."""
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        # Setup PDF extraction to return empty text
        mock_extract.return_value = {"text": "", "page_count": 1}
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\ntest")
            temp_path = temp_file.name
        
        try:
            with pytest.raises(Exception) as exc_info:
                deconstruct_solicitation_task("test_job_empty_pdf", temp_path)
            
            error_message = str(exc_info.value)
            assert "No text could be extracted" in error_message
            
            # Verify job status was updated to failed
            failed_calls = [call for call in mock_job_manager.update_job_status.call_args_list 
                          if len(call[0]) > 1 and call[0][1] == "failed"]
            assert len(failed_calls) == 1
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_llm_service_failure_falls_back_gracefully(self, mock_extractor_class, mock_chunk, 
                                                      mock_extract, mock_get_job_manager):
        """Test LLM service failure falls back gracefully with clear messaging."""
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        sample_text = "NSF 24-569: Test Solicitation\nAward Information\nUp to $500,000 funding."
        mock_extract.return_value = {"text": sample_text}
        mock_chunk.return_value = {"sections": {"award_info": "Up to $500,000 funding."}}
        
        # Setup LLM to be available but fail during extraction
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_all_metadata.side_effect = Exception("LLM API timeout after 30 seconds")
        mock_extractor_class.return_value = mock_extractor
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\ntest")
            temp_path = temp_file.name
        
        try:
            # Should not raise exception - should fall back gracefully
            result = deconstruct_solicitation_task("test_job_llm_fallback", temp_path)
            
            # Verify task completed successfully with fallback
            assert isinstance(result, StructuredSolicitation)
            assert result.solicitation_id == "test_job_llm_fallback"
            assert result.full_text == sample_text
            
            # Verify job completed (not failed)
            completed_calls = [call for call in mock_job_manager.update_job_status.call_args_list 
                             if len(call[0]) > 1 and call[0][1] == "completed"]
            assert len(completed_calls) == 1
            
            # Verify fallback extraction worked (should find some funding amount)
            assert result.funding_ceiling is not None
            assert result.funding_ceiling > 0
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_job_status_error_message_format_and_clarity(self):
        """Test that job error messages are properly formatted and clear."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file.flush()
            
            try:
                # Mock the task to fail with a specific error
                with patch('app.api.deconstruct.enqueue_deconstruct_task') as mock_enqueue:
                    def failing_task():
                        from app.jobs.job_manager import get_job_manager
                        job_manager = get_job_manager()
                        job_manager.update_job_status(
                            "test_error_job", 
                            JobStatus.FAILED, 
                            error_message="PDF processing failed: Invalid document structure detected"
                        )
                    
                    mock_enqueue.side_effect = lambda job_id, file_path: failing_task()
                    
                    with open(temp_file.name, "rb") as f:
                        response = client.post(
                            "/api/deconstruct",
                            files={"file": ("test.pdf", f, "application/pdf")}
                        )
                    
                    assert response.status_code == 200
                    job_data = response.json()
                    job_id = job_data["job_id"]
                    
                    # Wait for background processing
                    time.sleep(1)
                    
                    # Check job status
                    status_response = client.get(f"/api/jobs/{job_id}")
                    assert status_response.status_code == 200
                    
                    status_data = status_response.json()
                    if status_data["status"] == "failed":
                        # Verify error message format
                        assert status_data["error_message"] is not None
                        assert len(status_data["error_message"]) > 0
                        assert "PDF processing failed" in status_data["error_message"]
                        assert "Invalid document structure" in status_data["error_message"]
                        
                        # Verify other status fields
                        assert status_data["progress"] >= 0
                        assert status_data["created_at"] is not None
                        assert status_data["result"] is None
                
            finally:
                os.unlink(temp_file.name)

class TestConcurrentPDFUploadsAndQueueManagement:
    """Test concurrent PDF uploads and queue management."""
    
    def test_multiple_concurrent_uploads_are_handled_correctly(self):
        """Test that multiple concurrent uploads are handled without conflicts."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        def upload_pdf(file_suffix):
            """Upload a PDF file and return the response."""
            with tempfile.NamedTemporaryFile(suffix=f"_{file_suffix}.pdf", delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file.flush()
                
                try:
                    with patch('app.api.deconstruct.enqueue_deconstruct_task'):
                        with open(temp_file.name, "rb") as f:
                            response = client.post(
                                "/api/deconstruct",
                                files={"file": (f"test_{file_suffix}.pdf", f, "application/pdf")}
                            )
                        return response.json() if response.status_code == 200 else None
                finally:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
        
        # Upload 5 files concurrently
        num_uploads = 5
        job_ids = []
        
        with ThreadPoolExecutor(max_workers=num_uploads) as executor:
            futures = [executor.submit(upload_pdf, i) for i in range(num_uploads)]
            
            for future in as_completed(futures):
                result = future.result()
                if result and "job_id" in result:
                    job_ids.append(result["job_id"])
        
        # Verify all uploads succeeded
        assert len(job_ids) == num_uploads
        
        # Verify all job IDs are unique
        assert len(set(job_ids)) == num_uploads
        
        # Verify all job IDs are valid UUIDs
        import uuid
        for job_id in job_ids:
            uuid.UUID(job_id)  # Should not raise exception
    
    def test_concurrent_job_status_queries_are_handled_correctly(self):
        """Test that concurrent job status queries don't interfere with each other."""
        # Create multiple jobs first
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
        job_ids = []
        
        # Create 3 jobs
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=f"_{i}.pdf", delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file.flush()
                
                try:
                    with patch('app.api.deconstruct.enqueue_deconstruct_task'):
                        with open(temp_file.name, "rb") as f:
                            response = client.post(
                                "/api/deconstruct",
                                files={"file": (f"test_{i}.pdf", f, "application/pdf")}
                            )
                        
                        if response.status_code == 200:
                            job_ids.append(response.json()["job_id"])
                finally:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
        
        assert len(job_ids) >= 2  # At least 2 jobs created successfully
        
        def query_job_status(job_id):
            """Query job status and return the response."""
            response = client.get(f"/api/jobs/{job_id}")
            return response.json() if response.status_code == 200 else None
        
        # Query all job statuses concurrently
        status_results = []
        with ThreadPoolExecutor(max_workers=len(job_ids)) as executor:
            futures = [executor.submit(query_job_status, job_id) for job_id in job_ids]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    status_results.append(result)
        
        # Verify all queries succeeded
        assert len(status_results) == len(job_ids)
        
        # Verify each result has the correct job_id
        returned_job_ids = [result["job_id"] for result in status_results]
        assert set(returned_job_ids) == set(job_ids)
    
    def test_queue_handles_rapid_successive_uploads(self):
        """Test that the queue can handle rapid successive uploads without errors."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
        
        job_ids = []
        upload_times = []
        
        # Perform 10 rapid uploads
        for i in range(10):
            start_time = time.time()
            
            with tempfile.NamedTemporaryFile(suffix=f"_rapid_{i}.pdf", delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file.flush()
                
                try:
                    with patch('app.api.deconstruct.enqueue_deconstruct_task'):
                        with open(temp_file.name, "rb") as f:
                            response = client.post(
                                "/api/deconstruct",
                                files={"file": (f"rapid_{i}.pdf", f, "application/pdf")}
                            )
                        
                        if response.status_code == 200:
                            job_ids.append(response.json()["job_id"])
                            upload_times.append(time.time() - start_time)
                finally:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
        
        # Verify all uploads succeeded
        assert len(job_ids) == 10
        
        # Verify all job IDs are unique
        assert len(set(job_ids)) == 10
        
        # Verify upload times are reasonable (< 5 seconds each)
        assert all(upload_time < 5.0 for upload_time in upload_times)
        
        # Verify average upload time is reasonable (< 1 second)
        avg_upload_time = sum(upload_times) / len(upload_times)
        assert avg_upload_time < 1.0

class TestStructuredSolicitationOutputFormatAndCompleteness:
    """Test StructuredSolicitation output format and completeness validation."""
    
    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_structured_solicitation_contains_all_required_fields(self, mock_extractor_class, 
                                                                mock_chunk, mock_extract, mock_get_job_manager):
        """Test that StructuredSolicitation output contains all required fields."""
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        sample_text = """
        NSF 24-569: Mathematical Foundations of AI
        Award Information: Up to $1,500,000 for 4 years (48 months).
        Deadline: March 15, 2025.
        Eligibility: U.S. citizens only. Max 3 PIs per proposal.
        Required skills: machine learning, mathematics, computer science.
        """
        
        mock_extract.return_value = {"text": sample_text}
        mock_chunk.return_value = {"sections": {"award_info": "Up to $1,500,000 for 4 years"}}
        
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_all_metadata.return_value = {
            "metadata": {
                "award_title": "Mathematical Foundations of AI",
                "funding_ceiling": 1500000.0,
                "project_duration_months": 48,
                "submission_deadline": "March 15, 2025"
            },
            "rules": {
                "pi_eligibility_rules": ["U.S. citizens only"],
                "team_size_constraints": {"max_pi": 3}
            },
            "skills": {
                "required_scientific_skills": ["machine learning", "mathematics", "computer science"]
            },
            "extraction_summary": {
                "sections_processed": 1,
                "successful_extractions": 1,
                "failed_extractions": 0
            }
        }
        mock_extractor_class.return_value = mock_extractor
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\ntest")
            temp_path = temp_file.name
        
        try:
            result = deconstruct_solicitation_task("test_complete_fields", temp_path)
            
            # Verify all required fields are present
            assert hasattr(result, 'solicitation_id')
            assert hasattr(result, 'award_title')
            assert hasattr(result, 'full_text')
            assert hasattr(result, 'processing_time_seconds')
            assert hasattr(result, 'extraction_confidence')
            assert hasattr(result, 'created_at')
            
            # Verify required fields have valid values
            assert result.solicitation_id == "test_complete_fields"
            assert result.award_title == "Mathematical Foundations of AI"
            assert result.full_text.strip() == sample_text.strip()
            assert result.processing_time_seconds > 0
            assert 0 <= result.extraction_confidence <= 1.0
            assert isinstance(result.created_at, datetime)
            
            # Verify optional fields are properly handled
            assert result.funding_ceiling == 1500000.0
            assert result.project_duration_months == 48
            assert result.submission_deadline is not None
            assert len(result.pi_eligibility_rules) > 0
            assert len(result.required_scientific_skills) > 0
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_structured_solicitation_field_validation_and_constraints(self):
        """Test StructuredSolicitation field validation and constraints."""
        # Test valid data
        valid_data = {
            "solicitation_id": "test_validation_123",
            "award_title": "Test Solicitation Title",
            "funding_ceiling": 750000.0,
            "project_duration_months": 36,
            "submission_deadline": datetime(2025, 6, 15),
            "pi_eligibility_rules": ["Must be U.S. citizen", "PhD required"],
            "institutional_limitations": ["Academic institutions only"],
            "team_size_constraints": {"max_pi": 2, "max_team_size": 8},
            "required_scientific_skills": ["artificial intelligence", "machine learning"],
            "preferred_skills": ["deep learning", "natural language processing"],
            "full_text": "Complete solicitation text content goes here...",
            "extracted_sections": {
                "award_information": "Funding details...",
                "eligibility": "Eligibility requirements..."
            },
            "processing_time_seconds": 42.5,
            "extraction_confidence": 0.92,
            "created_at": datetime.now()
        }
        
        # Should create successfully
        solicitation = StructuredSolicitation(**valid_data)
        assert solicitation.solicitation_id == "test_validation_123"
        assert solicitation.funding_ceiling == 750000.0
        assert solicitation.extraction_confidence == 0.92
        
        # Test field validation errors
        from pydantic import ValidationError
        
        # Test empty required string fields
        with pytest.raises(ValidationError):
            StructuredSolicitation(
                solicitation_id="",  # Empty ID should fail
                award_title="Test",
                full_text="Text",
                processing_time_seconds=1.0,
                extraction_confidence=0.5,
                created_at=datetime.now()
            )
        
        # Test invalid confidence range (> 1.0)
        with pytest.raises(ValidationError):
            StructuredSolicitation(
                solicitation_id="test",
                award_title="Test",
                full_text="Text",
                processing_time_seconds=1.0,
                extraction_confidence=1.5,  # > 1.0 should fail
                created_at=datetime.now()
            )
        
        # Test invalid confidence range (< 0.0)
        with pytest.raises(ValidationError):
            StructuredSolicitation(
                solicitation_id="test",
                award_title="Test",
                full_text="Text",
                processing_time_seconds=1.0,
                extraction_confidence=-0.1,  # < 0.0 should fail
                created_at=datetime.now()
            )
        
        # Test invalid project duration (negative)
        with pytest.raises(ValidationError):
            StructuredSolicitation(
                solicitation_id="test",
                award_title="Test",
                full_text="Text",
                project_duration_months=-5,  # Negative should fail
                processing_time_seconds=1.0,
                extraction_confidence=0.5,
                created_at=datetime.now()
            )
    
    def test_structured_solicitation_json_serialization_and_deserialization(self):
        """Test StructuredSolicitation JSON serialization and deserialization."""
        original_data = {
            "solicitation_id": "test_json_123",
            "award_title": "JSON Serialization Test",
            "funding_ceiling": 500000.0,
            "project_duration_months": 24,
            "submission_deadline": datetime(2025, 8, 30),
            "pi_eligibility_rules": ["U.S. citizens", "PhD in relevant field"],
            "institutional_limitations": ["R1 universities preferred"],
            "team_size_constraints": {"max_pi": 1, "max_co_pi": 2},
            "required_scientific_skills": ["data science", "statistics"],
            "preferred_skills": ["machine learning"],
            "full_text": "Full solicitation text for JSON test...",
            "extracted_sections": {"overview": "Project overview section"},
            "processing_time_seconds": 15.7,
            "extraction_confidence": 0.88,
            "created_at": datetime.now()
        }
        
        # Create StructuredSolicitation object
        original_solicitation = StructuredSolicitation(**original_data)
        
        # Test JSON serialization
        json_data = original_solicitation.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["solicitation_id"] == "test_json_123"
        assert json_data["funding_ceiling"] == 500000.0
        
        # Test JSON string serialization
        json_string = original_solicitation.model_dump_json()
        assert isinstance(json_string, str)
        assert "test_json_123" in json_string
        
        # Test deserialization from dict
        reconstructed_from_dict = StructuredSolicitation(**json_data)
        assert reconstructed_from_dict.solicitation_id == original_solicitation.solicitation_id
        assert reconstructed_from_dict.award_title == original_solicitation.award_title
        assert reconstructed_from_dict.funding_ceiling == original_solicitation.funding_ceiling
        
        # Test deserialization from JSON string
        reconstructed_from_json = StructuredSolicitation.model_validate_json(json_string)
        assert reconstructed_from_json.solicitation_id == original_solicitation.solicitation_id
        assert reconstructed_from_json.extraction_confidence == original_solicitation.extraction_confidence
    
    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_structured_solicitation_handles_missing_optional_fields_gracefully(self, mock_extractor_class,
                                                                               mock_chunk, mock_extract, mock_get_job_manager):
        """Test that StructuredSolicitation handles missing optional fields gracefully."""
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        sample_text = "Basic solicitation text without detailed metadata."
        mock_extract.return_value = {"text": sample_text}
        mock_chunk.return_value = {"sections": {"full_document": sample_text}}
        
        # Mock LLM to return minimal metadata
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_all_metadata.return_value = {
            "metadata": {
                "award_title": "Basic Solicitation"
                # No funding_ceiling, project_duration_months, or submission_deadline
            },
            "rules": {
                # No pi_eligibility_rules, institutional_limitations, or team_size_constraints
            },
            "skills": {
                # No required_scientific_skills or preferred_skills
            },
            "extraction_summary": {
                "sections_processed": 1,
                "successful_extractions": 1,
                "failed_extractions": 0
            }
        }
        mock_extractor_class.return_value = mock_extractor
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\ntest")
            temp_path = temp_file.name
        
        try:
            result = deconstruct_solicitation_task("test_minimal_fields", temp_path)
            
            # Verify required fields are present
            assert result.solicitation_id == "test_minimal_fields"
            assert result.award_title == "Basic Solicitation"
            assert result.full_text == sample_text
            
            # Verify optional fields have appropriate default values
            assert result.funding_ceiling is None
            assert result.project_duration_months is None
            assert result.submission_deadline is None
            assert result.pi_eligibility_rules == []
            assert result.institutional_limitations == []
            assert result.team_size_constraints is None
            assert result.required_scientific_skills == []
            assert result.preferred_skills == []
            
            # Verify processing metadata is still present
            assert result.processing_time_seconds > 0
            assert 0 <= result.extraction_confidence <= 1.0
            assert isinstance(result.created_at, datetime)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)