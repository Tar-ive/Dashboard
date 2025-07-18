"""
Mock factories for external dependencies in NSF Researcher Matching API tests.

This module provides mock implementations of external services and dependencies
to enable isolated testing without external API calls or file system dependencies.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, MagicMock, AsyncMock
from datetime import datetime, timedelta
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


class MockAIService:
    """Mock AI service for testing without external API dependencies."""
    
    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_request = None
    
    def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Mock text analysis."""
        self.call_count += 1
        self.last_request = {"method": "analyze_text", "text": text, "type": analysis_type}
        
        if "analyze_text" in self.responses:
            return self.responses["analyze_text"]
        
        # Default mock response
        return {
            "keywords": ["machine learning", "artificial intelligence", "research"],
            "summary": f"Mock analysis of text: {text[:50]}...",
            "topics": ["AI", "ML", "Research"],
            "sentiment": "neutral",
            "confidence": 0.85
        }
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Mock embedding generation."""
        self.call_count += 1
        self.last_request = {"method": "generate_embeddings", "text": text}
        
        if "generate_embeddings" in self.responses:
            return self.responses["generate_embeddings"]
        
        # Generate deterministic mock embeddings based on text hash
        import hashlib
        text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        np.random.seed(text_hash % 2**32)
        return np.random.random(384).tolist()  # Standard embedding dimension
    
    async def analyze_text_async(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Mock async text analysis."""
        return self.analyze_text(text, analysis_type)
    
    async def generate_embeddings_async(self, text: str) -> List[float]:
        """Mock async embedding generation."""
        return self.generate_embeddings(text)


class MockPDFProcessor:
    """Mock PDF processor for testing without file dependencies."""
    
    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.processed_files = []
    
    def extract_text(self, file_path: str) -> str:
        """Mock PDF text extraction."""
        self.processed_files.append(file_path)
        
        if "extract_text" in self.responses:
            return self.responses["extract_text"]
        
        # Generate mock text based on filename
        filename = Path(file_path).stem
        return f"""
        Mock PDF Content for {filename}
        
        This is a sample NSF solicitation document for testing purposes.
        
        Program: Mathematical Foundations of Artificial Intelligence (MFAI)
        
        Research Areas:
        - Machine Learning Theory
        - Computational Complexity
        - Statistical Learning
        - Neural Network Analysis
        
        Eligibility Requirements:
        - Principal Investigator must be affiliated with eligible institution
        - Minimum 3 years of relevant research experience
        - Prior NSF funding preferred but not required
        
        Budget Guidelines:
        - Maximum award: $500,000
        - Project duration: 3 years
        - Indirect costs: Standard institutional rate
        """
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Mock PDF metadata extraction."""
        if "extract_metadata" in self.responses:
            return self.responses["extract_metadata"]
        
        return {
            "title": f"Mock Document - {Path(file_path).stem}",
            "author": "NSF Program Office",
            "subject": "Research Solicitation",
            "creator": "Mock PDF Creator",
            "pages": 15,
            "creation_date": datetime.now().isoformat(),
            "modification_date": datetime.now().isoformat()
        }
    
    def validate_pdf(self, file_path: str) -> bool:
        """Mock PDF validation."""
        return Path(file_path).suffix.lower() == '.pdf'


class MockDatabaseSession:
    """Mock database session for testing without database dependencies."""
    
    def __init__(self):
        self.data_store = {}
        self.committed = False
        self.rolled_back = False
        self.closed = False
    
    def add(self, instance):
        """Mock add operation."""
        if not hasattr(instance, 'id'):
            instance.id = str(uuid.uuid4())
        
        table_name = instance.__class__.__name__.lower()
        if table_name not in self.data_store:
            self.data_store[table_name] = {}
        
        self.data_store[table_name][instance.id] = instance
    
    def query(self, model_class):
        """Mock query operation."""
        table_name = model_class.__name__.lower()
        return MockQuery(self.data_store.get(table_name, {}))
    
    def commit(self):
        """Mock commit operation."""
        self.committed = True
    
    def rollback(self):
        """Mock rollback operation."""
        self.rolled_back = True
        self.data_store.clear()
    
    def close(self):
        """Mock close operation."""
        self.closed = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


class MockQuery:
    """Mock database query for testing."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.filters = []
    
    def filter(self, *conditions):
        """Mock filter operation."""
        # Simple mock - just return self for chaining
        return self
    
    def filter_by(self, **kwargs):
        """Mock filter_by operation."""
        return self
    
    def first(self):
        """Mock first operation."""
        if self.data:
            return list(self.data.values())[0]
        return None
    
    def all(self):
        """Mock all operation."""
        return list(self.data.values())
    
    def count(self):
        """Mock count operation."""
        return len(self.data)


class MockFileSystem:
    """Mock file system for testing without actual file operations."""
    
    def __init__(self):
        self.files = {}
        self.directories = set()
    
    def create_file(self, path: str, content: Union[str, bytes]):
        """Mock file creation."""
        self.files[path] = content
        # Add parent directories
        parent = str(Path(path).parent)
        while parent != '.' and parent != '/':
            self.directories.add(parent)
            parent = str(Path(parent).parent)
    
    def read_file(self, path: str) -> Union[str, bytes]:
        """Mock file reading."""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]
    
    def exists(self, path: str) -> bool:
        """Mock path existence check."""
        return path in self.files or path in self.directories
    
    def delete_file(self, path: str):
        """Mock file deletion."""
        if path in self.files:
            del self.files[path]
    
    def list_files(self, directory: str) -> List[str]:
        """Mock directory listing."""
        return [f for f in self.files.keys() if f.startswith(directory)]


class MockHTTPClient:
    """Mock HTTP client for testing external API calls."""
    
    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.requests = []
    
    def get(self, url: str, **kwargs) -> Mock:
        """Mock GET request."""
        self.requests.append({"method": "GET", "url": url, "kwargs": kwargs})
        
        response = Mock()
        if url in self.responses:
            response.json.return_value = self.responses[url]
            response.status_code = 200
        else:
            response.json.return_value = {"mock": "response"}
            response.status_code = 200
        
        return response
    
    def post(self, url: str, **kwargs) -> Mock:
        """Mock POST request."""
        self.requests.append({"method": "POST", "url": url, "kwargs": kwargs})
        
        response = Mock()
        response.json.return_value = {"success": True, "id": str(uuid.uuid4())}
        response.status_code = 201
        
        return response


def create_mock_researcher(
    researcher_id: str = None,
    name: str = None,
    expertise: List[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create mock researcher data for testing.
    
    Args:
        researcher_id: Optional researcher ID
        name: Optional researcher name
        expertise: Optional expertise list
        **kwargs: Additional researcher fields
    
    Returns:
        Mock researcher data dictionary
    """
    researcher_id = researcher_id or str(uuid.uuid4())
    name = name or f"Dr. Test Researcher {researcher_id[:8]}"
    expertise = expertise or ["machine learning", "data science", "artificial intelligence"]
    
    mock_researcher = {
        "id": researcher_id,
        "name": name,
        "email": f"{name.lower().replace(' ', '.')}@university.edu",
        "institution": "Test University",
        "department": "Computer Science",
        "expertise": expertise,
        "publications": 25,
        "h_index": 15,
        "orcid": f"0000-0000-0000-{researcher_id[:4]}",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    mock_researcher.update(kwargs)
    return mock_researcher


def create_mock_solicitation(
    solicitation_id: str = None,
    title: str = None,
    keywords: List[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create mock solicitation data for testing.
    
    Args:
        solicitation_id: Optional solicitation ID
        title: Optional solicitation title
        keywords: Optional keywords list
        **kwargs: Additional solicitation fields
    
    Returns:
        Mock solicitation data dictionary
    """
    solicitation_id = solicitation_id or str(uuid.uuid4())
    title = title or f"Mock NSF Solicitation {solicitation_id[:8]}"
    keywords = keywords or ["artificial intelligence", "machine learning", "research"]
    
    mock_solicitation = {
        "id": solicitation_id,
        "title": title,
        "program": "MFAI",
        "description": f"Mock description for {title}. This solicitation focuses on advancing research in computational methods and theoretical foundations.",
        "keywords": keywords,
        "deadline": (datetime.now() + timedelta(days=90)).isoformat(),
        "budget_range": "500000-1000000",
        "requirements": [
            "PhD in relevant field",
            "Minimum 3 years research experience",
            "Prior NSF funding preferred"
        ],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    mock_solicitation.update(kwargs)
    return mock_solicitation


def create_mock_matching_result(
    researcher_id: str = None,
    solicitation_id: str = None,
    score: float = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create mock matching result for testing.
    
    Args:
        researcher_id: Optional researcher ID
        solicitation_id: Optional solicitation ID
        score: Optional matching score
        **kwargs: Additional matching result fields
    
    Returns:
        Mock matching result dictionary
    """
    researcher_id = researcher_id or str(uuid.uuid4())
    solicitation_id = solicitation_id or str(uuid.uuid4())
    score = score if score is not None else np.random.uniform(0.5, 0.95)
    
    mock_result = {
        "researcher_id": researcher_id,
        "solicitation_id": solicitation_id,
        "score": round(score, 3),
        "rank": 1,
        "explanation": f"Mock matching explanation for researcher {researcher_id[:8]}",
        "confidence": round(np.random.uniform(0.7, 0.9), 3),
        "metadata": {
            "algorithm": "hybrid_tfidf_semantic",
            "version": "1.0",
            "processing_time": round(np.random.uniform(0.1, 0.5), 3)
        },
        "created_at": datetime.now().isoformat()
    }
    
    mock_result.update(kwargs)
    return mock_result


def create_mock_team_composition(
    team_size: int = 3,
    solicitation_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create mock team composition for testing.
    
    Args:
        team_size: Number of team members
        solicitation_id: Optional solicitation ID
        **kwargs: Additional team fields
    
    Returns:
        Mock team composition dictionary
    """
    solicitation_id = solicitation_id or str(uuid.uuid4())
    
    # Create team members with different roles
    roles = ["Principal Investigator", "Co-Investigator", "Senior Personnel", "Postdoc", "Graduate Student"]
    members = []
    
    for i in range(team_size):
        member = create_mock_researcher()
        member["role"] = roles[i % len(roles)]
        member["contribution_percentage"] = round(100 / team_size, 1)
        members.append(member)
    
    mock_team = {
        "id": str(uuid.uuid4()),
        "solicitation_id": solicitation_id,
        "members": members,
        "total_score": round(np.random.uniform(0.7, 0.9), 3),
        "diversity_score": round(np.random.uniform(0.6, 0.8), 3),
        "collaboration_potential": round(np.random.uniform(0.5, 0.9), 3),
        "created_at": datetime.now().isoformat()
    }
    
    mock_team.update(kwargs)
    return mock_team