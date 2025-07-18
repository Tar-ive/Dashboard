"""Tests for job API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.job import JobStatus, JobStatusResponse
from datetime import datetime

client = TestClient(app)

class TestJobsAPI:
    """Test job status API endpoints."""
    
    def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        mock_status = JobStatusResponse(
            job_id="test-job-123",
            status=JobStatus.COMPLETED,
            progress=100,
            result={"data": "test result"},
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            processing_time_seconds=5.0
        )
        
        with patch('app.api.jobs.get_job_manager') as mock_get_manager:
            mock_job_manager = MagicMock()
            mock_get_manager.return_value = mock_job_manager
            mock_job_manager.get_job_status.return_value = mock_status
            
            response = client.get("/api/jobs/test-job-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "test-job-123"
            assert data["status"] == "completed"
            assert data["progress"] == 100
            assert data["result"] == {"data": "test result"}
            assert data["processing_time_seconds"] == 5.0
    
    def test_get_job_status_not_found(self):
        """Test job status retrieval for non-existent job."""
        with patch('app.api.jobs.get_job_manager') as mock_get_manager:
            mock_job_manager = MagicMock()
            mock_get_manager.return_value = mock_job_manager
            mock_job_manager.get_job_status.return_value = None
            
            response = client.get("/api/jobs/nonexistent-job")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    def test_get_job_status_server_error(self):
        """Test job status retrieval with server error."""
        with patch('app.api.jobs.get_job_manager') as mock_get_manager:
            mock_job_manager = MagicMock()
            mock_get_manager.return_value = mock_job_manager
            mock_job_manager.get_job_status.side_effect = Exception("Database error")
            
            response = client.get("/api/jobs/test-job-123")
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
    
    def test_cleanup_job_success(self):
        """Test successful job cleanup."""
        mock_status = JobStatusResponse(
            job_id="test-job-123",
            status=JobStatus.COMPLETED,
            progress=100,
            created_at=datetime.utcnow()
        )
        
        with patch('app.api.jobs.get_job_manager') as mock_get_manager:
            mock_job_manager = MagicMock()
            mock_get_manager.return_value = mock_job_manager
            mock_job_manager.get_job_status.return_value = mock_status
            
            response = client.delete("/api/jobs/test-job-123")
            
            assert response.status_code == 200
            assert "cleaned up successfully" in response.json()["message"]
            mock_job_manager.cleanup_job.assert_called_once_with("test-job-123")
    
    def test_cleanup_job_not_found(self):
        """Test job cleanup for non-existent job."""
        with patch('app.api.jobs.get_job_manager') as mock_get_manager:
            mock_job_manager = MagicMock()
            mock_get_manager.return_value = mock_job_manager
            mock_job_manager.get_job_status.return_value = None
            
            response = client.delete("/api/jobs/nonexistent-job")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    def test_cleanup_job_server_error(self):
        """Test job cleanup with server error."""
        mock_status = JobStatusResponse(
            job_id="test-job-123",
            status=JobStatus.COMPLETED,
            progress=100,
            created_at=datetime.utcnow()
        )
        
        with patch('app.api.jobs.get_job_manager') as mock_get_manager:
            mock_job_manager = MagicMock()
            mock_get_manager.return_value = mock_job_manager
            mock_job_manager.get_job_status.return_value = mock_status
            mock_job_manager.cleanup_job.side_effect = Exception("Cleanup error")
            
            response = client.delete("/api/jobs/test-job-123")
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]