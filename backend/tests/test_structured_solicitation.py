"""Tests for StructuredSolicitation data model."""

import pytest
import json
from datetime import datetime
from pydantic import ValidationError
from app.models.structured_solicitation import StructuredSolicitation, SolicitationSection

class TestStructuredSolicitation:
    """Test cases for StructuredSolicitation data model."""
    
    def test_structured_solicitation_creation_with_valid_data(self):
        """Test creating StructuredSolicitation with valid data."""
        
        data = {
            "solicitation_id": "nsf-24-569",
            "title": "Mathematical Foundations of Artificial Intelligence",
            "program_name": "MFAI",
            "agency": "NSF",
            "sections": {
                "program_description": "This program supports research in mathematical foundations of AI.",
                "award_information": "Awards up to $500,000 for 3 years.",
                "eligibility_information": "Open to universities and colleges."
            },
            "extracted_metadata": {
                "max_award_amount": 500000,
                "award_duration_years": 3,
                "deadline": "2024-12-15",
                "eligible_institutions": ["universities", "colleges"],
                "required_skills": ["mathematics", "artificial intelligence", "machine learning"]
            },
            "processing_info": {
                "extracted_at": datetime.now(),
                "text_length": 57497,
                "page_count": 17,
                "sections_found": 2
            }
        }
        
        solicitation = StructuredSolicitation(**data)
        
        # Verify all fields are set correctly
        assert solicitation.solicitation_id == "nsf-24-569"
        assert solicitation.title == "Mathematical Foundations of Artificial Intelligence"
        assert solicitation.program_name == "MFAI"
        assert solicitation.agency == "NSF"
        assert len(solicitation.sections) == 3
        assert "program_description" in solicitation.sections
        assert solicitation.extracted_metadata["max_award_amount"] == 500000
        assert solicitation.processing_info["page_count"] == 17
    
    def test_structured_solicitation_json_serialization(self):
        """Test JSON serialization and deserialization."""
        
        data = {
            "solicitation_id": "test-123",
            "title": "Test Solicitation",
            "program_name": "TEST",
            "agency": "NSF",
            "sections": {
                "award_information": "Test award info"
            },
            "extracted_metadata": {
                "max_award_amount": 100000
            },
            "processing_info": {
                "extracted_at": datetime.now(),
                "text_length": 1000,
                "page_count": 5,
                "sections_found": 1
            }
        }
        
        # Create model instance
        solicitation = StructuredSolicitation(**data)
        
        # Serialize to JSON
        json_str = solicitation.model_dump_json()
        assert isinstance(json_str, str)
        
        # Deserialize from JSON
        json_data = json.loads(json_str)
        solicitation_restored = StructuredSolicitation(**json_data)
        
        # Verify data integrity
        assert solicitation_restored.solicitation_id == solicitation.solicitation_id
        assert solicitation_restored.title == solicitation.title
        assert solicitation_restored.sections == solicitation.sections
        assert solicitation_restored.extracted_metadata == solicitation.extracted_metadata
    
    def test_structured_solicitation_validation_errors(self):
        """Test validation errors for invalid data."""
        
        # Test missing required fields
        with pytest.raises(ValidationError) as exc_info:
            StructuredSolicitation()
        
        errors = exc_info.value.errors()
        required_fields = [error["loc"][0] for error in errors if error["type"] == "missing"]
        assert "solicitation_id" in required_fields
        assert "title" in required_fields
        
        # Test invalid data types
        with pytest.raises(ValidationError):
            StructuredSolicitation(
                solicitation_id=123,  # Should be string
                title="Test",
                sections="not a dict"  # Should be dict
            )
    
    def test_structured_solicitation_with_minimal_data(self):
        """Test creating StructuredSolicitation with minimal required data."""
        
        minimal_data = {
            "solicitation_id": "minimal-test",
            "title": "Minimal Test Solicitation"
        }
        
        solicitation = StructuredSolicitation(**minimal_data)
        
        # Verify required fields
        assert solicitation.solicitation_id == "minimal-test"
        assert solicitation.title == "Minimal Test Solicitation"
        
        # Verify optional fields have defaults
        assert solicitation.program_name is None
        assert solicitation.agency is None
        assert solicitation.sections == {}
        assert solicitation.extracted_metadata == {}
        assert solicitation.processing_info is None
    
    def test_structured_solicitation_with_real_nsf_data(self):
        """Test with data structure similar to real NSF document."""
        
        nsf_data = {
            "solicitation_id": "nsf-24-569",
            "title": "Mathematical Foundations of Artificial Intelligence (MFAI)",
            "program_name": "MFAI",
            "agency": "National Science Foundation",
            "sections": {
                "program_description": "The Mathematical Foundations of Artificial Intelligence (MFAI) program supports research that seeks to establish the theoretical underpinnings of AI systems.",
                "award_information": "Anticipated Type of Award: Standard Grant or Continuing Grant. The National Science Foundation expects to make approximately 15-20 awards.",
                "eligibility_information": "Who May Submit Proposals: Universities and colleges, including community colleges, that award degrees in science, technology, engineering, or mathematics (STEM)."
            },
            "extracted_metadata": {
                "max_award_amount": 500000,
                "award_duration_years": 3,
                "expected_awards": 20,
                "deadline": "2024-12-15",
                "eligible_institutions": ["universities", "colleges", "community colleges"],
                "required_skills": ["mathematics", "artificial intelligence", "theoretical computer science"],
                "funding_type": "Standard Grant or Continuing Grant"
            },
            "processing_info": {
                "extracted_at": datetime.now(),
                "text_length": 57497,
                "page_count": 17,
                "sections_found": 2,
                "extraction_time": 0.09
            }
        }
        
        solicitation = StructuredSolicitation(**nsf_data)
        
        # Verify complex nested data
        assert solicitation.solicitation_id == "nsf-24-569"
        assert "MFAI" in solicitation.title
        assert len(solicitation.sections) == 3
        assert solicitation.extracted_metadata["max_award_amount"] == 500000
        assert "universities" in solicitation.extracted_metadata["eligible_institutions"]
        assert solicitation.processing_info["page_count"] == 17
    
    def test_structured_solicitation_field_validation(self):
        """Test field-specific validation rules."""
        
        # Test solicitation_id validation (should not be empty)
        with pytest.raises(ValidationError):
            StructuredSolicitation(
                solicitation_id="",  # Empty string
                title="Test"
            )
        
        # Test title validation (should not be empty)
        with pytest.raises(ValidationError):
            StructuredSolicitation(
                solicitation_id="test",
                title=""  # Empty string
            )
    
    def test_structured_solicitation_sections_type(self):
        """Test that sections field accepts proper dictionary structure."""
        
        valid_sections = {
            "program_description": "Description text",
            "award_information": "Award details",
            "eligibility_information": "Eligibility requirements"
        }
        
        solicitation = StructuredSolicitation(
            solicitation_id="test",
            title="Test",
            sections=valid_sections
        )
        
        assert solicitation.sections == valid_sections
        assert isinstance(solicitation.sections, dict)
    
    def test_structured_solicitation_metadata_flexibility(self):
        """Test that extracted_metadata accepts flexible dictionary structure."""
        
        flexible_metadata = {
            "custom_field": "custom_value",
            "numeric_field": 12345,
            "list_field": ["item1", "item2"],
            "nested_dict": {
                "sub_field": "sub_value"
            }
        }
        
        solicitation = StructuredSolicitation(
            solicitation_id="test",
            title="Test",
            extracted_metadata=flexible_metadata
        )
        
        assert solicitation.extracted_metadata == flexible_metadata
        assert solicitation.extracted_metadata["custom_field"] == "custom_value"
        assert solicitation.extracted_metadata["numeric_field"] == 12345
        assert len(solicitation.extracted_metadata["list_field"]) == 2
    
    def test_structured_solicitation_redis_storage_compatibility(self):
        """Test compatibility with Redis storage (JSON serialization)."""
        
        data = {
            "solicitation_id": "redis-test",
            "title": "Redis Storage Test",
            "sections": {
                "test_section": "Test content with special chars: àáâãäå"
            },
            "extracted_metadata": {
                "unicode_field": "Test with unicode: 中文测试",
                "special_chars": "Symbols: $500,000–$1,000,000 €100,000"
            },
            "processing_info": {
                "extracted_at": datetime.now(),
                "text_length": 1000,
                "page_count": 1,
                "sections_found": 1
            }
        }
        
        solicitation = StructuredSolicitation(**data)
        
        # Test JSON serialization (for Redis storage)
        json_str = solicitation.model_dump_json()
        
        # Should be valid JSON
        parsed_json = json.loads(json_str)
        assert isinstance(parsed_json, dict)
        
        # Should preserve unicode and special characters
        assert "àáâãäå" in json_str
        assert "中文测试" in json_str
        assert "€" in json_str
        
        # Should be deserializable
        restored = StructuredSolicitation.model_validate_json(json_str)
        assert restored.solicitation_id == solicitation.solicitation_id
        assert restored.extracted_metadata["unicode_field"] == solicitation.extracted_metadata["unicode_field"]