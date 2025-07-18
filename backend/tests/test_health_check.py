"""Tests for health check endpoints with Redis integration."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

class TestHealthCheck:
    """Test health check endpoints."""
    
    def test_basic_health_check(self):
        """Test basic health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "NSF Researcher Matching API is running"
        assert "version" in data
        assert "features" in data
    
    def test_detailed_health_check_redis_connected(self):
        """Test detailed health check with Redis connected."""
        with patch('app.jobs.redis_connection.RedisConnection.test_connection') as mock_test:
            mock_test.return_value = True
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["api_status"] == "ready"
            assert data["redis_status"] == "connected"
            assert "anthropic_configured" in data
            assert "version" in data
    
    def test_detailed_health_check_redis_disconnected(self):
        """Test detailed health check with Redis disconnected."""
        with patch('app.jobs.redis_connection.RedisConnection.test_connection') as mock_test:
            mock_test.return_value = False
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["api_status"] == "ready"
            assert data["redis_status"] == "disconnected"