"""
Test utilities and helper functions for the NSF Researcher Matching API tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
import numpy as np
import pandas as pd


class TestDataGenerator:
    """Generate test data for various components."""
    
    @staticmethod
    def create_sample_pdf_content() -> bytes:
        """Create a minimal valid PDF content for testing."""
        return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
    
    @staticmethod
    def create_solicitation_data(
        title: str = "Test Solicitation",
        program: str = "TEST",
        **kwargs
    ) -> Dict[str, Any]:
        """Create sample solicitation data."""
        base_data = {
            "title": title,
            "program": program,
            "deadline": "2024-12-15",
            "description": "Test solicitation description",
            "keywords": ["test", "research", "science"],
            "budget_range": "100000-500000",
            "requirements": ["PhD required", "Experience in field"],
            "contact_info": "test@nsf.gov"
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_researcher_data(
        name: str = "Dr. Test Researcher",
        email: str = "test@university.edu",
        **kwargs
    ) -> Dict[str, Any]:
        """Create sample researcher data."""
        base_data = {
            "name": name,
            "email": email,
            "institution": "Test University",
            "department": "Computer Science",
            "expertise": ["machine learning", "data science"],
            "publications": 20,
            "h_index": 12,
            "grants": ["NSF-123456", "NIH-789012"],
            "collaborators": ["Dr. Jane Doe", "Dr. John Smith"]
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_matching_request(
        solicitation_id: str = "test-sol-123",
        **kwargs
    ) -> Dict[str, Any]:
        """Create sample matching request data."""
        base_data = {
            "solicitation_id": solicitation_id,
            "max_results": 10,
            "min_score": 0.5,
            "filters": {
                "institution_type": "R1",
                "min_publications": 5,
                "max_distance": 100
            },
            "weights": {
                "expertise_match": 0.4,
                "publication_count": 0.3,
                "collaboration_history": 0.3
            }
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_team_assembly_request(
        solicitation_id: str = "test-sol-123",
        team_size: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Create sample team assembly request data."""
        base_data = {
            "solicitation_id": solicitation_id,
            "team_size": team_size,
            "strategy": "balanced",
            "constraints": {
                "max_same_institution": 2,
                "required_expertise": ["AI", "Statistics"],
                "diversity_weight": 0.3
            },
            "optimization_criteria": ["expertise_coverage", "collaboration_potential"]
        }
        base_data.update(kwargs)
        return base_data


class MockServices:
    """Mock services for testing without external dependencies."""
    
    @staticmethod
    def create_mock_ai_service():
        """Create a mock AI service."""
        mock_service = Mock()
        mock_service.analyze_text.return_value = {
            "keywords": ["machine learning", "artificial intelligence"],
            "summary": "Test analysis summary",
            "topics": ["AI", "ML", "Data Science"],
            "sentiment": "neutral",
            "complexity": 0.7
        }
        mock_service.generate_embeddings.return_value = np.random.rand(384).tolist()
        mock_service.calculate_similarity.return_value = 0.85
        return mock_service
    
    @staticmethod
    def create_mock_pdf_processor():
        """Create a mock PDF processor."""
        mock_processor = Mock()
        mock_processor.extract_text.return_value = "Sample PDF text content for testing"
        mock_processor.extract_metadata.return_value = {
            "title": "Test Document",
            "author": "Test Author",
            "pages": 5,
            "creation_date": "2024-01-01",
            "modification_date": "2024-01-02"
        }
        mock_processor.extract_sections.return_value = {
            "abstract": "Test abstract",
            "introduction": "Test introduction",
            "methodology": "Test methodology",
            "conclusion": "Test conclusion"
        }
        return mock_processor
    
    @staticmethod
    def create_mock_matching_engine():
        """Create a mock matching engine."""
        mock_engine = Mock()
        mock_engine.find_matches.return_value = [
            {
                "researcher_id": "researcher-1",
                "score": 0.95,
                "explanation": "High expertise match",
                "details": {"expertise_score": 0.9, "publication_score": 0.8}
            },
            {
                "researcher_id": "researcher-2", 
                "score": 0.87,
                "explanation": "Good collaboration potential",
                "details": {"expertise_score": 0.8, "collaboration_score": 0.9}
            }
        ]
        mock_engine.calculate_affinity_matrix.return_value = np.array([
            [1.0, 0.7, 0.5],
            [0.7, 1.0, 0.8],
            [0.5, 0.8, 1.0]
        ])
        return mock_engine


class TestFileManager:
    """Manage test files and temporary directories."""
    
    def __init__(self):
        self.temp_dirs = []
        self.temp_files = []
    
    def create_temp_dir(self, prefix: str = "test_") -> Path:
        """Create a temporary directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(
        self, 
        content: str = "", 
        suffix: str = ".txt",
        binary_content: Optional[bytes] = None
    ) -> Path:
        """Create a temporary file with content."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb' if binary_content else 'w',
            suffix=suffix,
            delete=False
        )
        
        if binary_content:
            temp_file.write(binary_content)
        else:
            temp_file.write(content)
        
        temp_file.close()
        temp_path = Path(temp_file.name)
        self.temp_files.append(temp_path)
        return temp_path
    
    def create_sample_pdf(self, filename: str = "sample.pdf") -> Path:
        """Create a sample PDF file."""
        pdf_content = TestDataGenerator.create_sample_pdf_content()
        return self.create_temp_file(
            binary_content=pdf_content,
            suffix=".pdf"
        )
    
    def cleanup(self):
        """Clean up all temporary files and directories."""
        import shutil
        
        for temp_file in self.temp_files:
            if temp_file.exists():
                temp_file.unlink()
        
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        self.temp_files.clear()
        self.temp_dirs.clear()


class AssertionHelpers:
    """Helper functions for test assertions."""
    
    @staticmethod
    def assert_response_structure(response_data: Dict, expected_keys: List[str]):
        """Assert that response has expected structure."""
        for key in expected_keys:
            assert key in response_data, f"Missing key '{key}' in response"
    
    @staticmethod
    def assert_score_range(score: float, min_val: float = 0.0, max_val: float = 1.0):
        """Assert that score is within expected range."""
        assert min_val <= score <= max_val, f"Score {score} not in range [{min_val}, {max_val}]"
    
    @staticmethod
    def assert_list_not_empty(data_list: List, message: str = "List should not be empty"):
        """Assert that list is not empty."""
        assert len(data_list) > 0, message
    
    @staticmethod
    def assert_valid_email(email: str):
        """Assert that email format is valid."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(pattern, email), f"Invalid email format: {email}"
    
    @staticmethod
    def assert_valid_uuid(uuid_string: str):
        """Assert that string is a valid UUID."""
        import uuid
        try:
            uuid.UUID(uuid_string)
        except ValueError:
            assert False, f"Invalid UUID format: {uuid_string}"
    
    @staticmethod
    def assert_performance_threshold(elapsed_time: float, threshold: float):
        """Assert that operation completed within time threshold."""
        assert elapsed_time <= threshold, f"Operation took {elapsed_time}s, exceeding threshold of {threshold}s"


class DatabaseHelpers:
    """Helper functions for database testing."""
    
    @staticmethod
    def create_test_data(session, model_class, data_list: List[Dict]):
        """Create test data in database."""
        objects = []
        for data in data_list:
            obj = model_class(**data)
            session.add(obj)
            objects.append(obj)
        session.commit()
        return objects
    
    @staticmethod
    def count_records(session, model_class) -> int:
        """Count records in table."""
        return session.query(model_class).count()
    
    @staticmethod
    def clear_table(session, model_class):
        """Clear all records from table."""
        session.query(model_class).delete()
        session.commit()


# Export commonly used utilities
__all__ = [
    'TestDataGenerator',
    'MockServices', 
    'TestFileManager',
    'AssertionHelpers',
    'DatabaseHelpers'
]