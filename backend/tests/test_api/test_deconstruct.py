"""Tests for the deconstruct endpoint following TDD approach."""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.job import JobStatus

client = TestClient(app)

class TestDeconstructEndpoint:
    """Test cases for POST /deconstruct endpoint."""
    
    def test_deconstruct_endpoint_returns_job_id_immediately(self):
        """Test that POST /deconstruct returns job_id without processing."""
        # Create a sample PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file.flush()
            
            try:
                with patch('app.api.deconstruct.get_job_manager') as mock_get_manager:
                    mock_manager = MagicMock()
                    mock_manager.create_job.return_value = "test-job-id-123"
                    mock_get_manager.return_value = mock_manager
                    
                    with patch('app.api.deconstruct.enqueue_deconstruct_task') as mock_enqueue:
                        mock_enqueue.return_value = None
                        
                        with open(temp_file.name, "rb") as f:
                            response = client.post(
                                "/api/deconstruct",
                                files={"file": ("test.pdf", f, "application/pdf")}
                            )
                        
                        # Should return immediately with job_id
                        assert response.status_code == 200
                        data = response.json()
                        assert "job_id" in data
                        assert "status" in data
                        assert data["status"] == "queued"
                        assert data["job_id"] == "test-job-id-123"
                
            finally:
                os.unlink(temp_file.name)
    
    def test_deconstruct_endpoint_validates_pdf_format(self):
        """Test that endpoint validates PDF file format."""
        # Create a non-PDF file
        text_content = b"This is not a PDF file"
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(text_content)
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("test.txt", f, "text/plain")}
                    )
                
                # Should reject non-PDF files
                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
                assert "PDF" in data["detail"] or "pdf" in data["detail"]
                
            finally:
                os.unlink(temp_file.name)
    
    def test_deconstruct_endpoint_validates_file_size(self):
        """Test that endpoint validates file size limits."""
        # Create a large file (simulate > 10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\n")  # PDF header
            temp_file.write(large_content)
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("large.pdf", f, "application/pdf")}
                    )
                
                # Should reject files that are too large
                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
                assert "size" in data["detail"].lower()
                
            finally:
                os.unlink(temp_file.name)
    
    def test_deconstruct_endpoint_saves_file_and_enqueues_job(self):
        """Test that endpoint saves file and enqueues background job."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file.flush()
            
            try:
                with patch('app.api.deconstruct.get_job_manager') as mock_get_manager:
                    mock_manager = MagicMock()
                    mock_manager.create_job.return_value = "test-job-id-456"
                    mock_get_manager.return_value = mock_manager
                    
                    with patch('app.api.deconstruct.enqueue_deconstruct_task') as mock_enqueue:
                        mock_enqueue.return_value = None
                        
                        with open(temp_file.name, "rb") as f:
                            response = client.post(
                                "/api/deconstruct",
                                files={"file": ("test.pdf", f, "application/pdf")}
                            )
                        
                        # Should succeed and enqueue job
                        assert response.status_code == 200
                        data = response.json()
                        job_id = data["job_id"]
                        assert job_id == "test-job-id-456"
                        
                        # Verify job was enqueued
                        mock_enqueue.assert_called_once()
                        call_args = mock_enqueue.call_args[0]
                        assert call_args[0] == job_id  # job_id
                        assert call_args[1].endswith(".pdf")  # file_path
                    
            finally:
                os.unlink(temp_file.name)
    
    def test_deconstruct_endpoint_handles_missing_file(self):
        """Test that endpoint handles missing file parameter."""
        response = client.post("/api/deconstruct")
        
        # Should return 422 for missing required parameter
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_deconstruct_endpoint_handles_empty_file(self):
        """Test that endpoint handles empty file uploads."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            # Empty file
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("empty.pdf", f, "application/pdf")}
                    )
                
                # Should reject empty files
                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
                assert "empty" in data["detail"].lower()
                
            finally:
                os.unlink(temp_file.name)