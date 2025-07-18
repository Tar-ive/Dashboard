"""Tests for deconstruction task functionality."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.tasks.deconstruction_task import (
    deconstruct_solicitation_task,
    _assemble_structured_solicitation,
    _fallback_metadata_extraction,
    _extract_pdf_text,
    _chunk_by_sections,
    _extract_metadata_with_llm,
    StructuredSolicitation
)


class TestDeconstructionTask:
    """Test suite for deconstruction task functionality"""

    @pytest.fixture
    def mock_job_manager(self):
        """Mock job manager for testing"""
        mock_manager = Mock()
        mock_manager.update_job_status = Mock()
        return mock_manager

    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF text content for testing"""
        return """
        NSF Solicitation: Advanced Research Program
        
        Award Information
        This program provides awards of up to $500,000 for projects lasting 36 months.
        The submission deadline is March 15, 2024.
        
        Eligibility Information
        Principal Investigators must be U.S. citizens or permanent residents.
        Only accredited universities in the United States are eligible to apply.
        Teams may include up to 5 researchers with a maximum of 2 PIs.
        
        Program Description
        This program requires expertise in machine learning, data analysis, and statistical modeling.
        Preferred skills include Python programming, deep learning frameworks, and cloud computing.
        Technical requirements include access to high-performance computing resources.
        """

    @pytest.fixture
    def sample_sections(self):
        """Sample chunked sections for testing"""
        return {
            "award_information": "This program provides awards of up to $500,000 for projects lasting 36 months.",
            "eligibility_information": "Principal Investigators must be U.S. citizens or permanent residents.",
            "program_description": "This program requires expertise in machine learning, data analysis."
        }

    @pytest.fixture
    def sample_extracted_metadata(self):
        """Sample extracted metadata for testing"""
        return {
            "metadata": {
                "award_title": "Advanced Research Program",
                "funding_ceiling": 500000.0,
                "project_duration_months": 36,
                "submission_deadline": "March 15, 2024"
            },
            "rules": {
                "pi_eligibility_rules": ["Must be U.S. citizens or permanent residents"],
                "institutional_limitations": ["Only accredited universities in the United States"],
                "team_size_constraints": {"max_team_size": 5, "max_pi": 2}
            },
            "skills": {
                "required_scientific_skills": ["machine learning", "data analysis", "statistical modeling"],
                "preferred_skills": ["Python programming", "deep learning frameworks"],
                "technical_requirements": ["high-performance computing resources"]
            },
            "extraction_summary": {
                "sections_processed": 3,
                "successful_extractions": 3,
                "failed_extractions": 0,
                "timestamp": "2024-01-01T00:00:00"
            }
        }

    @pytest.fixture
    def temp_pdf_file(self, sample_pdf_content):
        """Create a temporary PDF-like file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write(sample_pdf_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_extract_pdf_text_pure_function(self, temp_pdf_file, sample_pdf_content):
        """Test pure PDF text extraction function"""
        with patch('app.tasks.deconstruction_task.extract_pdf_text') as mock_extract:
            mock_extract.return_value = {"text": sample_pdf_content}
            
            result = _extract_pdf_text(temp_pdf_file)
            
            assert result == sample_pdf_content
            mock_extract.assert_called_once_with(temp_pdf_file)

    def test_chunk_by_sections_pure_function(self, sample_pdf_content, sample_sections):
        """Test pure section chunking function"""
        with patch('app.tasks.deconstruction_task.chunk_by_sections') as mock_chunk:
            mock_chunk.return_value = {"sections": sample_sections}
            
            result = _chunk_by_sections(sample_pdf_content)
            
            assert result == sample_sections
            mock_chunk.assert_called_once_with(sample_pdf_content)

    def test_extract_metadata_with_llm_pure_function(self):
        """Test pure LLM metadata extraction function"""
        section_text = "Sample section text"
        section_type = "metadata"
        expected_result = {"award_title": "Test Award"}
        
        with patch('app.tasks.deconstruction_task.LLMMetadataExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor._extract_metadata_with_llm.return_value = expected_result
            mock_extractor_class.return_value = mock_extractor
            
            result = _extract_metadata_with_llm(section_text, section_type)
            
            assert result == expected_result
            mock_extractor._extract_metadata_with_llm.assert_called_once_with(section_text, section_type)

    def test_assemble_structured_solicitation(self, sample_sections, sample_extracted_metadata):
        """Test assembling structured solicitation object"""
        job_id = "test_job_123"
        full_text = "Complete PDF text content"
        processing_time = 45.5
        
        result = _assemble_structured_solicitation(
            job_id=job_id,
            full_text=full_text,
            sections=sample_sections,
            extracted_metadata=sample_extracted_metadata,
            processing_time=processing_time
        )
        
        assert isinstance(result, StructuredSolicitation)
        assert result.solicitation_id == job_id
        assert result.award_title == "Advanced Research Program"
        assert result.funding_ceiling == 500000.0
        assert result.project_duration_months == 36
        assert result.submission_deadline == "March 15, 2024"
        assert "Must be U.S. citizens or permanent residents" in result.pi_eligibility_rules
        assert "machine learning" in result.required_scientific_skills
        assert result.full_text == full_text
        assert result.extracted_sections == sample_sections
        assert result.processing_time_seconds == processing_time
        assert result.extraction_confidence == 100.0  # 3/3 successful extractions

    def test_assemble_structured_solicitation_partial_data(self, sample_sections):
        """Test assembling structured solicitation with partial metadata"""
        partial_metadata = {
            "metadata": {"award_title": "Partial Award"},
            "rules": {},
            "skills": {"required_scientific_skills": ["AI"]},
            "extraction_summary": {
                "sections_processed": 3,
                "successful_extractions": 1,
                "failed_extractions": 2
            }
        }
        
        result = _assemble_structured_solicitation(
            job_id="test_job",
            full_text="text",
            sections=sample_sections,
            extracted_metadata=partial_metadata,
            processing_time=30.0
        )
        
        assert result.award_title == "Partial Award"
        assert result.funding_ceiling == 0.0  # Default value
        assert result.pi_eligibility_rules == []  # Empty list
        assert result.required_scientific_skills == ["AI"]
        assert result.extraction_confidence == 33.33333333333333  # 1/3 successful

    def test_fallback_metadata_extraction(self, sample_sections, sample_pdf_content):
        """Test fallback metadata extraction without LLM"""
        result = _fallback_metadata_extraction(sample_sections, sample_pdf_content)
        
        assert "metadata" in result
        assert "rules" in result
        assert "skills" in result
        assert "extraction_summary" in result
        
        # Should extract funding amount
        assert result["metadata"].get("funding_ceiling") == 500000.0
        
        # Should extract project duration
        assert result["metadata"].get("project_duration_months") == 36
        
        # Should find some skills
        assert len(result["skills"]["required_scientific_skills"]) > 0
        assert "machine learning" in result["skills"]["required_scientific_skills"]

    def test_fallback_metadata_extraction_no_patterns(self, sample_sections):
        """Test fallback extraction with text that has no recognizable patterns"""
        text_without_patterns = "This is just some random text without any funding or duration information."
        
        result = _fallback_metadata_extraction(sample_sections, text_without_patterns)
        
        assert result["metadata"] == {}
        assert result["rules"] == {}
        assert len(result["skills"]["required_scientific_skills"]) == 0
        # The function returns 1 if any metadata or skills are found, 0 otherwise
        # Since no patterns match, it should be 0, but the logic counts empty results as 0
        assert result["extraction_summary"]["successful_extractions"] == 0

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_deconstruct_solicitation_task_success(
        self, mock_extractor_class, mock_chunk, mock_extract, mock_get_job_manager,
        temp_pdf_file, sample_pdf_content, sample_sections, sample_extracted_metadata
    ):
        """Test successful deconstruction task execution"""
        # Setup mocks
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        mock_extract.return_value = {"text": sample_pdf_content}
        mock_chunk.return_value = {"sections": sample_sections}
        
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_all_metadata.return_value = sample_extracted_metadata
        mock_extractor_class.return_value = mock_extractor
        
        # Execute task
        result = deconstruct_solicitation_task("test_job_123", temp_pdf_file)
        
        # Verify result
        assert isinstance(result, StructuredSolicitation)
        assert result.solicitation_id == "test_job_123"
        assert result.award_title == "Advanced Research Program"
        assert result.funding_ceiling == 500000.0
        
        # Verify job manager calls
        assert mock_job_manager.update_job_status.call_count >= 4  # At least 4 status updates
        
        # Verify final completion call
        final_call = mock_job_manager.update_job_status.call_args_list[-1]
        assert final_call[0][1] == "completed"  # Status
        assert final_call[1]["progress"] == 100
        assert "result" in final_call[1]

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_deconstruct_solicitation_task_llm_unavailable(
        self, mock_extractor_class, mock_chunk, mock_extract, mock_get_job_manager,
        temp_pdf_file, sample_pdf_content, sample_sections
    ):
        """Test deconstruction task when LLM is unavailable"""
        # Setup mocks
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        mock_extract.return_value = {"text": sample_pdf_content}
        mock_chunk.return_value = {"sections": sample_sections}
        
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = False  # LLM unavailable
        mock_extractor_class.return_value = mock_extractor
        
        # Execute task
        result = deconstruct_solicitation_task("test_job_123", temp_pdf_file)
        
        # Verify result (should use fallback extraction)
        assert isinstance(result, StructuredSolicitation)
        assert result.solicitation_id == "test_job_123"
        
        # Should have used fallback extraction
        assert mock_extractor.extract_all_metadata.call_count == 0

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    def test_deconstruct_solicitation_task_pdf_extraction_failure(
        self, mock_extract, mock_get_job_manager, temp_pdf_file
    ):
        """Test deconstruction task when PDF extraction fails"""
        # Setup mocks
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        mock_extract.side_effect = Exception("PDF extraction failed")
        
        # Execute task and expect failure
        with pytest.raises(Exception, match="Deconstruction failed"):
            deconstruct_solicitation_task("test_job_123", temp_pdf_file)
        
        # Verify job manager was called to mark failure
        mock_job_manager.update_job_status.assert_called()
        final_call = mock_job_manager.update_job_status.call_args_list[-1]
        assert final_call[0][1] == "failed"  # Status
        assert "error_message" in final_call[1]

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    def test_deconstruct_solicitation_task_empty_pdf(
        self, mock_extract, mock_get_job_manager, temp_pdf_file
    ):
        """Test deconstruction task with empty PDF"""
        # Setup mocks
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        mock_extract.return_value = {"text": ""}  # Empty text
        
        # Execute task and expect failure
        with pytest.raises(Exception, match="No text could be extracted"):
            deconstruct_solicitation_task("test_job_123", temp_pdf_file)
        
        # Verify failure was recorded
        mock_job_manager.update_job_status.assert_called()
        final_call = mock_job_manager.update_job_status.call_args_list[-1]
        assert final_call[0][1] == "failed"

    def test_structured_solicitation_model_validation(self):
        """Test StructuredSolicitation model validation"""
        # Test with valid data
        valid_data = {
            "solicitation_id": "test_123",
            "award_title": "Test Award",
            "funding_ceiling": 100000.0,
            "project_duration_months": 24,
            "full_text": "Complete text content"
        }
        
        solicitation = StructuredSolicitation(**valid_data)
        assert solicitation.solicitation_id == "test_123"
        assert solicitation.award_title == "Test Award"
        assert solicitation.funding_ceiling == 100000.0
        assert solicitation.project_duration_months == 24
        
        # Test with minimal data (defaults should be used)
        minimal_data = {"solicitation_id": "test_minimal"}
        minimal_solicitation = StructuredSolicitation(**minimal_data)
        assert minimal_solicitation.solicitation_id == "test_minimal"
        assert minimal_solicitation.award_title == ""
        assert minimal_solicitation.funding_ceiling == 0.0
        assert minimal_solicitation.pi_eligibility_rules == []
        assert minimal_solicitation.required_scientific_skills == []

    def test_structured_solicitation_model_serialization(self, sample_extracted_metadata):
        """Test StructuredSolicitation model serialization"""
        solicitation = _assemble_structured_solicitation(
            job_id="test_job",
            full_text="test text",
            sections={"section1": "content1"},
            extracted_metadata=sample_extracted_metadata,
            processing_time=30.0
        )
        
        # Test model_dump
        data = solicitation.model_dump()
        assert isinstance(data, dict)
        assert data["solicitation_id"] == "test_job"
        assert data["award_title"] == "Advanced Research Program"
        # created_at is a datetime object in the model_dump by default
        assert isinstance(data["created_at"], datetime)
        
        # Test round-trip serialization
        new_solicitation = StructuredSolicitation(**data)
        assert new_solicitation.solicitation_id == solicitation.solicitation_id
        assert new_solicitation.award_title == solicitation.award_title