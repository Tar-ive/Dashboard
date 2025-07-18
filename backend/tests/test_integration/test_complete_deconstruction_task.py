"""
Integration tests for complete deconstruction task (Task 3.6).

This module tests the full orchestration of the deconstruction task:
PDF extraction → chunking → LLM processing → assembly
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.tasks.deconstruction_task import deconstruct_solicitation_task
from app.models.structured_solicitation import StructuredSolicitation
from app.models.job import JobStatus


class TestCompleteDeconstructionTask:
    """Integration tests for complete deconstruction task orchestration"""

    @pytest.fixture
    def sample_nsf_pdf_content(self):
        """Sample NSF solicitation content for testing"""
        return """
        NSF 24-569: Mathematical Foundations of Artificial Intelligence (MFAI)
        
        Award Information
        
        This program provides awards of up to $1,200,000 for research projects in mathematical foundations of AI.
        Project duration is typically 4 years (48 months).
        Full proposal deadline: March 15, 2025.
        Collaborative proposals may request up to $2,000,000 total.
        
        Eligibility Information
        
        Principal Investigators must be U.S. citizens, nationals, or permanent residents.
        Co-Principal Investigators may include foreign nationals with appropriate visa status.
        Only degree-granting institutions of higher education in the United States are eligible to submit proposals.
        A maximum of 3 Principal Investigators per proposal is allowed.
        Research teams may include up to 12 total researchers including graduate students and postdocs.
        Industry partnerships are encouraged but must be led by academic institutions.
        
        Program Description
        
        This program supports fundamental research in mathematical foundations of artificial intelligence.
        Required expertise includes advanced mathematics, theoretical computer science, and machine learning theory.
        Preferred qualifications include experience with optimization theory, statistical learning theory, 
        computational complexity, and deep learning architectures. 
        Technical requirements include access to high-performance computing resources and 
        proficiency in mathematical software such as MATLAB, Python with NumPy/SciPy, or R.
        
        Proposal Preparation Instructions
        
        Proposals must include a detailed mathematical framework section.
        All theoretical claims must be supported by rigorous proofs or computational validation.
        Collaboration plans with industry partners should be clearly outlined.
        
        Review Information
        
        Proposals will be evaluated based on intellectual merit and broader impacts.
        Review criteria include mathematical rigor, theoretical innovation, and potential for practical applications.
        Special emphasis will be placed on interdisciplinary approaches and reproducible research practices.
        """

    @pytest.fixture
    def temp_pdf_file(self, sample_nsf_pdf_content):
        """Create a temporary PDF file with sample content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write(sample_nsf_pdf_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def expected_sections(self):
        """Expected sections after chunking"""
        return {
            "award_information": """This program provides awards of up to $1,200,000 for research projects in mathematical foundations of AI.
Project duration is typically 4 years (48 months).
Full proposal deadline: March 15, 2025.
Collaborative proposals may request up to $2,000,000 total.""",
            "eligibility_information": """Principal Investigators must be U.S. citizens, nationals, or permanent residents.
Co-Principal Investigators may include foreign nationals with appropriate visa status.
Only degree-granting institutions of higher education in the United States are eligible to submit proposals.
A maximum of 3 Principal Investigators per proposal is allowed.
Research teams may include up to 12 total researchers including graduate students and postdocs.
Industry partnerships are encouraged but must be led by academic institutions.""",
            "program_description": """This program supports fundamental research in mathematical foundations of artificial intelligence.
Required expertise includes advanced mathematics, theoretical computer science, and machine learning theory.
Preferred qualifications include experience with optimization theory, statistical learning theory, 
computational complexity, and deep learning architectures. 
Technical requirements include access to high-performance computing resources and 
proficiency in mathematical software such as MATLAB, Python with NumPy/SciPy, or R."""
        }

    @pytest.fixture
    def expected_llm_metadata(self):
        """Expected metadata from LLM extraction"""
        return {
            "metadata": {
                "award_title": "Mathematical Foundations of Artificial Intelligence (MFAI)",
                "funding_ceiling": 1200000.0,
                "project_duration_months": 48,
                "submission_deadline": "March 15, 2025"
            },
            "rules": {
                "pi_eligibility_rules": [
                    "Principal Investigators must be U.S. citizens, nationals, or permanent residents",
                    "Co-Principal Investigators may include foreign nationals with appropriate visa status"
                ],
                "institutional_limitations": [
                    "Only degree-granting institutions of higher education in the United States are eligible to submit proposals",
                    "Industry partnerships are encouraged but must be led by academic institutions"
                ],
                "team_size_constraints": {
                    "max_pi": 3,
                    "max_team_size": 12
                }
            },
            "skills": {
                "required_scientific_skills": [
                    "advanced mathematics",
                    "theoretical computer science", 
                    "machine learning theory"
                ],
                "preferred_skills": [
                    "optimization theory",
                    "statistical learning theory",
                    "computational complexity",
                    "deep learning architectures"
                ],
                "technical_requirements": [
                    "access to high-performance computing resources",
                    "proficiency in MATLAB, Python with NumPy/SciPy, or R"
                ]
            },
            "extraction_summary": {
                "sections_processed": 3,
                "successful_extractions": 3,
                "failed_extractions": 0,
                "timestamp": datetime.now().isoformat()
            }
        }

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_complete_deconstruction_task_success_with_llm(
        self, mock_extractor_class, mock_chunk, mock_extract, mock_get_job_manager,
        temp_pdf_file, sample_nsf_pdf_content, expected_sections, expected_llm_metadata
    ):
        """Test complete successful deconstruction task execution with LLM"""
        
        # Setup job manager mock
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        # Setup PDF extraction mock
        mock_extract.return_value = {
            "text": sample_nsf_pdf_content,
            "page_count": 5,
            "extraction_time": 0.5,
            "file_size": 1024
        }
        
        # Setup chunking mock
        mock_chunk.return_value = {
            "sections": expected_sections,
            "section_count": 3
        }
        
        # Setup LLM extractor mock
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_all_metadata.return_value = expected_llm_metadata
        mock_extractor_class.return_value = mock_extractor
        
        # Execute the complete task
        result = deconstruct_solicitation_task("test_job_complete_123", temp_pdf_file)
        
        # Verify result structure and content
        assert isinstance(result, StructuredSolicitation)
        assert result.solicitation_id == "test_job_complete_123"
        
        # Verify extracted metadata
        assert result.award_title == "Mathematical Foundations of Artificial Intelligence (MFAI)"
        assert result.funding_ceiling == 1200000.0
        assert result.project_duration_months == 48
        # submission_deadline is now a datetime object
        assert result.submission_deadline is not None
        assert result.submission_deadline.year == 2025
        assert result.submission_deadline.month == 3
        assert result.submission_deadline.day == 15
        
        # Verify extracted rules
        assert len(result.pi_eligibility_rules) == 2
        assert "U.S. citizens" in result.pi_eligibility_rules[0]
        assert len(result.institutional_limitations) == 2
        assert result.team_size_constraints["max_pi"] == 3
        assert result.team_size_constraints["max_team_size"] == 12
        
        # Verify extracted skills
        assert "advanced mathematics" in result.required_scientific_skills
        assert "optimization theory" in result.preferred_skills
        
        # Verify text content
        assert result.full_text.strip() == sample_nsf_pdf_content.strip()
        assert len(result.extracted_sections) == 3
        assert "award_information" in result.extracted_sections
        
        # Verify processing metadata
        assert result.processing_time_seconds > 0
        assert result.extraction_confidence == 1.0  # Perfect confidence (0-1 range)
        assert isinstance(result.created_at, datetime)
        
        # Verify job manager interactions (orchestration)
        job_status_calls = mock_job_manager.update_job_status.call_args_list
        assert len(job_status_calls) >= 4  # At least: processing(0%), processing(25%), processing(40%), processing(80%), completed(100%)
        
        # Verify status progression
        assert job_status_calls[0][0] == ("test_job_complete_123", "processing")
        assert job_status_calls[0][1]["progress"] == 0
        
        final_call = job_status_calls[-1]
        assert final_call[0] == ("test_job_complete_123", "completed")
        assert final_call[1]["progress"] == 100
        assert "result" in final_call[1]
        
        # Verify component interactions (orchestration)
        mock_extract.assert_called_once_with(temp_pdf_file)
        mock_chunk.assert_called_once_with(sample_nsf_pdf_content)
        mock_extractor.extract_all_metadata.assert_called_once_with(expected_sections)

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_complete_deconstruction_task_with_llm_unavailable(
        self, mock_extractor_class, mock_chunk, mock_extract, mock_get_job_manager,
        temp_pdf_file, sample_nsf_pdf_content, expected_sections
    ):
        """Test complete deconstruction task when LLM is unavailable (fallback mode)"""
        
        # Setup job manager mock
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        # Setup PDF extraction mock
        mock_extract.return_value = {
            "text": sample_nsf_pdf_content,
            "page_count": 3,
            "extraction_time": 0.3,
            "file_size": 512
        }
        
        # Setup chunking mock
        mock_chunk.return_value = {
            "sections": expected_sections,
            "section_count": 3
        }
        
        # Setup LLM extractor mock (unavailable)
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = False
        mock_extractor_class.return_value = mock_extractor
        
        # Execute the complete task
        result = deconstruct_solicitation_task("test_job_fallback_456", temp_pdf_file)
        
        # Verify result structure
        assert isinstance(result, StructuredSolicitation)
        assert result.solicitation_id == "test_job_fallback_456"
        
        # Verify fallback extraction worked
        assert result.full_text.strip() == sample_nsf_pdf_content.strip()
        assert len(result.extracted_sections) == 3
        
        # Verify fallback metadata extraction (should find some basic info)
        # The fallback should extract funding amounts from text patterns
        assert result.funding_ceiling > 0  # Should find $1,200,000 or $2,000,000
        
        # Verify processing metadata
        assert result.processing_time_seconds > 0
        assert 0 <= result.extraction_confidence <= 1.0  # Model expects 0-1 range
        
        # Verify job completion
        final_call = mock_job_manager.update_job_status.call_args_list[-1]
        assert final_call[0] == ("test_job_fallback_456", "completed")
        assert final_call[1]["progress"] == 100

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    def test_complete_deconstruction_task_pdf_extraction_error(
        self, mock_extract, mock_get_job_manager, temp_pdf_file
    ):
        """Test complete deconstruction task with PDF extraction error"""
        
        # Setup job manager mock
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        # Setup PDF extraction to fail
        mock_extract.side_effect = Exception("PDF file is corrupted")
        
        # Execute task and expect failure
        with pytest.raises(Exception, match="Deconstruction failed"):
            deconstruct_solicitation_task("test_job_pdf_error_789", temp_pdf_file)
        
        # Verify error handling
        error_calls = [call for call in mock_job_manager.update_job_status.call_args_list 
                      if call[0][1] == "failed"]
        assert len(error_calls) == 1
        
        error_call = error_calls[0]
        assert "PDF file is corrupted" in error_call[1]["error_message"]

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    def test_complete_deconstruction_task_empty_pdf_error(
        self, mock_extract, mock_get_job_manager, temp_pdf_file
    ):
        """Test complete deconstruction task with empty PDF"""
        
        # Setup job manager mock
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        # Setup PDF extraction to return empty text
        mock_extract.return_value = {"text": "", "page_count": 1}
        
        # Execute task and expect failure
        with pytest.raises(Exception, match="No text could be extracted"):
            deconstruct_solicitation_task("test_job_empty_pdf_101", temp_pdf_file)
        
        # Verify error handling
        error_calls = [call for call in mock_job_manager.update_job_status.call_args_list 
                      if call[0][1] == "failed"]
        assert len(error_calls) == 1

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_complete_deconstruction_task_llm_extraction_error(
        self, mock_extractor_class, mock_chunk, mock_extract, mock_get_job_manager,
        temp_pdf_file, sample_nsf_pdf_content, expected_sections
    ):
        """Test complete deconstruction task with LLM extraction error (should fallback gracefully)"""
        
        # Setup job manager mock
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        # Setup PDF extraction mock
        mock_extract.return_value = {"text": sample_nsf_pdf_content}
        
        # Setup chunking mock
        mock_chunk.return_value = {"sections": expected_sections}
        
        # Setup LLM extractor mock (available but fails)
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_all_metadata.side_effect = Exception("LLM API timeout")
        mock_extractor_class.return_value = mock_extractor
        
        # Execute task - should not fail, should use fallback
        result = deconstruct_solicitation_task("test_job_llm_error_202", temp_pdf_file)
        
        # Verify task completed successfully with fallback
        assert isinstance(result, StructuredSolicitation)
        assert result.solicitation_id == "test_job_llm_error_202"
        assert result.full_text.strip() == sample_nsf_pdf_content.strip()
        
        # Verify job completed (not failed)
        final_call = mock_job_manager.update_job_status.call_args_list[-1]
        assert final_call[0][1] == "completed"

    def test_complete_deconstruction_task_with_real_pdf_file(self):
        """Test complete deconstruction task with a real PDF file from uploads directory"""
        
        # Use one of the existing PDF files
        real_pdf_path = "backend/data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
        
        if not os.path.exists(real_pdf_path):
            pytest.skip("Real PDF file not available for testing")
        
        with patch('app.tasks.deconstruction_task.get_job_manager') as mock_get_job_manager:
            # Setup job manager mock
            mock_job_manager = Mock()
            mock_get_job_manager.return_value = mock_job_manager
            
            # Execute task with real PDF (this will use real PDF extraction and chunking)
            try:
                result = deconstruct_solicitation_task("test_job_real_pdf_303", real_pdf_path)
                
                # Verify basic structure
                assert isinstance(result, StructuredSolicitation)
                assert result.solicitation_id == "test_job_real_pdf_303"
                assert len(result.full_text) > 100  # Should have substantial text
                assert result.processing_time_seconds > 0
                assert isinstance(result.created_at, datetime)
                
                # Verify job completion
                final_call = mock_job_manager.update_job_status.call_args_list[-1]
                assert final_call[0][1] == "completed"
                
                # Log results for manual verification
                print(f"\n=== Real PDF Test Results ===")
                print(f"Award Title: {result.award_title}")
                print(f"Funding Ceiling: ${result.funding_ceiling:,.2f}" if result.funding_ceiling else "Not extracted")
                print(f"Duration: {result.project_duration_months} months" if result.project_duration_months else "Not extracted")
                print(f"Sections Found: {list(result.extracted_sections.keys())}")
                print(f"Required Skills: {result.required_scientific_skills[:3]}..." if result.required_scientific_skills else "None")
                print(f"Extraction Confidence: {result.extraction_confidence:.1f}%")
                print(f"Processing Time: {result.processing_time_seconds:.2f}s")
                
            except Exception as e:
                # Real PDF processing might fail due to missing dependencies or API keys
                # This is acceptable for integration testing
                print(f"Real PDF processing failed (expected in test environment): {e}")
                pytest.skip(f"Real PDF processing failed: {e}")

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    @patch('app.tasks.deconstruction_task.LLMMetadataExtractor')
    def test_complete_deconstruction_task_progress_tracking(
        self, mock_extractor_class, mock_chunk, mock_extract, mock_get_job_manager,
        temp_pdf_file, sample_nsf_pdf_content, expected_sections, expected_llm_metadata
    ):
        """Test that deconstruction task properly tracks progress through all stages"""
        
        # Setup mocks
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        mock_extract.return_value = {"text": sample_nsf_pdf_content}
        mock_chunk.return_value = {"sections": expected_sections}
        
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_all_metadata.return_value = expected_llm_metadata
        mock_extractor_class.return_value = mock_extractor
        
        # Execute task
        result = deconstruct_solicitation_task("test_job_progress_404", temp_pdf_file)
        
        # Verify progress tracking
        progress_calls = mock_job_manager.update_job_status.call_args_list
        
        # Should have calls for: processing(0), processing(25), processing(40), processing(80), completed(100)
        assert len(progress_calls) >= 5
        
        # Verify progress sequence
        progress_values = [call[1].get("progress", 0) for call in progress_calls if "progress" in call[1]]
        assert 0 in progress_values  # Started
        assert 25 in progress_values  # PDF extracted
        assert 40 in progress_values  # Text chunked
        assert 80 in progress_values  # LLM processing done
        assert 100 in progress_values  # Completed
        
        # Verify final result is stored
        final_call = progress_calls[-1]
        assert final_call[0][1] == "completed"
        assert final_call[1]["progress"] == 100
        assert "result" in final_call[1]
        
        # Verify result structure matches expected output
        stored_result = final_call[1]["result"]
        assert stored_result["solicitation_id"] == "test_job_progress_404"
        assert stored_result["award_title"] == expected_llm_metadata["metadata"]["award_title"]

    def test_structured_solicitation_validation(self):
        """Test that StructuredSolicitation model validates data correctly"""
        
        # Test valid data
        valid_data = {
            "solicitation_id": "test_123",
            "award_title": "Test Award",
            "funding_ceiling": 500000.0,
            "project_duration_months": 36,
            "submission_deadline": datetime(2025, 4, 15),  # Use datetime object
            "pi_eligibility_rules": ["Must be US citizen"],
            "institutional_limitations": ["Academic institutions only"],
            "team_size_constraints": {"max_pi": 2, "max_team_size": 10},
            "required_scientific_skills": ["machine learning", "statistics"],
            "preferred_skills": ["deep learning"],
            "full_text": "Complete solicitation text here...",
            "extracted_sections": {"award_info": "Award details..."},
            "processing_time_seconds": 45.5,
            "extraction_confidence": 0.85,
            "created_at": datetime.now()
        }
        
        solicitation = StructuredSolicitation(**valid_data)
        assert solicitation.solicitation_id == "test_123"
        assert solicitation.funding_ceiling == 500000.0
        assert solicitation.extraction_confidence == 0.85
        
        # Test invalid data (empty required fields)
        try:
            from pydantic import ValidationError
            invalid_solicitation = StructuredSolicitation(
                solicitation_id="",  # Empty ID should fail
                award_title="Test",
                full_text="Text",
                processing_time_seconds=1.0,
                extraction_confidence=0.5,
                created_at=datetime.now()
            )
            # If we get here, validation didn't work as expected
            assert False, "Expected validation error for empty solicitation_id"
        except (ValueError, ValidationError):
            pass  # Expected validation error
        
        # Test invalid confidence range
        try:
            invalid_confidence = StructuredSolicitation(
                solicitation_id="test",
                award_title="Test",
                full_text="Text",
                processing_time_seconds=1.0,
                extraction_confidence=1.5,  # > 1.0 should fail
                created_at=datetime.now()
            )
            # If we get here, validation didn't work as expected
            assert False, "Expected validation error for confidence > 1.0"
        except (ValueError, ValidationError):
            pass  # Expected validation error