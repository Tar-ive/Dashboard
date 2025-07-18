"""Tests for the StructuredSolicitation model."""

import pytest
import json
from datetime import datetime
from pydantic import ValidationError
from app.models.structured_solicitation import StructuredSolicitation

def test_structured_solicitation_minimal_validation():
    """Test that a minimal StructuredSolicitation can be created."""
    # Create with minimal required fields
    solicitation = StructuredSolicitation(
        solicitation_id="test-123",
        award_title="Test Solicitation",
        full_text="This is a test solicitation",
        extracted_sections={},
        processing_time_seconds=1.5,
        extraction_confidence=0.9,
        created_at=datetime.now()
    )
    
    # Validate the model
    assert solicitation.solicitation_id == "test-123"
    assert solicitation.award_title == "Test Solicitation"
    assert solicitation.full_text == "This is a test solicitation"
    assert isinstance(solicitation.created_at, datetime)

def test_structured_solicitation_complete_validation():
    """Test that a complete StructuredSolicitation can be created."""
    # Create with all fields
    now = datetime.now()
    solicitation = StructuredSolicitation(
        solicitation_id="test-456",
        award_title="Complete Test Solicitation",
        funding_ceiling=1000000.0,
        project_duration_months=36,
        submission_deadline=now,
        pi_eligibility_rules=["Must have PhD", "Must be affiliated with a university"],
        institutional_limitations=["Limited to 2 proposals per institution"],
        team_size_constraints={"PI": 1, "Co-PI": 3},
        required_scientific_skills=["Machine Learning", "Data Science"],
        preferred_skills=["Python", "TensorFlow"],
        full_text="This is a complete test solicitation",
        extracted_sections={"Eligibility": "Must have PhD", "Award Information": "Funding available"},
        processing_time_seconds=2.5,
        extraction_confidence=0.95,
        created_at=now
    )
    
    # Validate the model
    assert solicitation.solicitation_id == "test-456"
    assert solicitation.award_title == "Complete Test Solicitation"
    assert solicitation.funding_ceiling == 1000000.0
    assert solicitation.project_duration_months == 36
    assert solicitation.submission_deadline == now
    assert "Must have PhD" in solicitation.pi_eligibility_rules
    assert "Limited to 2 proposals per institution" in solicitation.institutional_limitations
    assert solicitation.team_size_constraints["PI"] == 1
    assert "Machine Learning" in solicitation.required_scientific_skills
    assert "Python" in solicitation.preferred_skills
    assert solicitation.full_text == "This is a complete test solicitation"
    assert solicitation.extracted_sections["Eligibility"] == "Must have PhD"
    assert solicitation.processing_time_seconds == 2.5
    assert solicitation.extraction_confidence == 0.95
    assert solicitation.created_at == now

def test_structured_solicitation_validation_errors():
    """Test that validation errors are raised for invalid data."""
    # Missing required fields
    with pytest.raises(ValidationError):
        StructuredSolicitation()
    
    # Invalid types
    with pytest.raises(ValidationError):
        StructuredSolicitation(
            solicitation_id="test-123",
            award_title="Test Solicitation",
            full_text="This is a test solicitation",
            extracted_sections={},
            processing_time_seconds="not a number",  # Should be a float
            extraction_confidence=0.9,
            created_at=datetime.now()
        )
    
    # Invalid values
    with pytest.raises(ValidationError):
        StructuredSolicitation(
            solicitation_id="test-123",
            award_title="Test Solicitation",
            full_text="This is a test solicitation",
            extracted_sections={},
            processing_time_seconds=1.5,
            extraction_confidence=1.5,  # Should be between 0 and 1
            created_at=datetime.now()
        )

def test_structured_solicitation_json_serialization():
    """Test that a StructuredSolicitation can be serialized to JSON."""
    # Create a solicitation
    now = datetime.now()
    solicitation = StructuredSolicitation(
        solicitation_id="test-789",
        award_title="JSON Test Solicitation",
        funding_ceiling=500000.0,
        project_duration_months=24,
        pi_eligibility_rules=["Must have PhD"],
        required_scientific_skills=["AI"],
        full_text="This is a JSON test solicitation",
        extracted_sections={"Summary": "This is a summary"},
        processing_time_seconds=1.0,
        extraction_confidence=0.8,
        created_at=now
    )
    
    # Serialize to JSON
    json_str = solicitation.model_dump_json()
    
    # Deserialize from JSON
    data = json.loads(json_str)
    
    # Validate the deserialized data
    assert data["solicitation_id"] == "test-789"
    assert data["award_title"] == "JSON Test Solicitation"
    assert data["funding_ceiling"] == 500000.0
    assert data["project_duration_months"] == 24
    assert data["pi_eligibility_rules"] == ["Must have PhD"]
    assert data["required_scientific_skills"] == ["AI"]
    assert data["full_text"] == "This is a JSON test solicitation"
    assert data["extracted_sections"]["Summary"] == "This is a summary"
    assert data["processing_time_seconds"] == 1.0
    assert data["extraction_confidence"] == 0.8
    assert "created_at" in data

def test_structured_solicitation_redis_serialization():
    """Test that a StructuredSolicitation can be serialized for Redis storage."""
    # Create a solicitation
    now = datetime.now()
    solicitation = StructuredSolicitation(
        solicitation_id="test-redis",
        award_title="Redis Test Solicitation",
        funding_ceiling=750000.0,
        project_duration_months=18,
        pi_eligibility_rules=["Must have PhD"],
        required_scientific_skills=["Quantum Computing"],
        full_text="This is a Redis test solicitation",
        extracted_sections={"Eligibility": "PhD required"},
        processing_time_seconds=3.0,
        extraction_confidence=0.85,
        created_at=now
    )
    
    # Serialize to JSON string for Redis
    redis_str = solicitation.model_dump_json()
    
    # Deserialize from Redis string
    deserialized = StructuredSolicitation.model_validate_json(redis_str)
    
    # Validate the deserialized object
    assert deserialized.solicitation_id == "test-redis"
    assert deserialized.award_title == "Redis Test Solicitation"
    assert deserialized.funding_ceiling == 750000.0
    assert deserialized.project_duration_months == 18
    assert deserialized.pi_eligibility_rules == ["Must have PhD"]
    assert deserialized.required_scientific_skills == ["Quantum Computing"]
    assert deserialized.full_text == "This is a Redis test solicitation"
    assert deserialized.extracted_sections["Eligibility"] == "PhD required"
    assert deserialized.processing_time_seconds == 3.0
    assert deserialized.extraction_confidence == 0.85
    assert isinstance(deserialized.created_at, datetime)

def test_structured_solicitation_field_constraints():
    """Test field constraints and validation rules."""
    # Test extraction_confidence constraint (0-1)
    with pytest.raises(ValidationError):
        StructuredSolicitation(
            solicitation_id="test-123",
            award_title="Test Solicitation",
            full_text="This is a test solicitation",
            extracted_sections={},
            processing_time_seconds=1.5,
            extraction_confidence=-0.1,  # Invalid: less than 0
            created_at=datetime.now()
        )
    
    with pytest.raises(ValidationError):
        StructuredSolicitation(
            solicitation_id="test-123",
            award_title="Test Solicitation",
            full_text="This is a test solicitation",
            extracted_sections={},
            processing_time_seconds=1.5,
            extraction_confidence=1.1,  # Invalid: greater than 1
            created_at=datetime.now()
        )
    
    # Test project_duration_months constraint (positive integer)
    with pytest.raises(ValidationError):
        StructuredSolicitation(
            solicitation_id="test-123",
            award_title="Test Solicitation",
            full_text="This is a test solicitation",
            extracted_sections={},
            processing_time_seconds=1.5,
            extraction_confidence=0.9,
            project_duration_months=-6,  # Invalid: negative
            created_at=datetime.now()
        )