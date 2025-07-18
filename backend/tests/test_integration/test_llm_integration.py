"""Integration tests for LLM metadata extraction functionality."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from app.services.llm_metadata_extractor import LLMMetadataExtractor
from app.tasks.deconstruction_task import deconstruct_solicitation_task


class TestLLMIntegration:
    """Integration tests for LLM metadata extraction"""

    @pytest.fixture
    def sample_nsf_solicitation_text(self):
        """Sample NSF solicitation text for integration testing"""
        return """
        NSF 24-123: Advanced Computational Research Program
        
        Award Information
        
        This program provides awards of up to $750,000 for computational research projects.
        Project duration is typically 3 years (36 months).
        Full proposal deadline: April 15, 2024.
        
        Eligibility Information
        
        Principal Investigators must be U.S. citizens, nationals, or permanent residents.
        Co-Principal Investigators may include foreign nationals.
        Only degree-granting institutions of higher education in the United States are eligible.
        A maximum of 2 Principal Investigators per proposal is allowed.
        Teams may include up to 8 total researchers.
        
        Program Description
        
        This program supports fundamental research in computational science and engineering.
        Required expertise includes high-performance computing, parallel algorithms, and numerical methods.
        Preferred qualifications include experience with machine learning, artificial intelligence, 
        and data analytics. Technical requirements include access to supercomputing facilities 
        and proficiency in programming languages such as C++, Python, or Fortran.
        
        Review Information
        
        Proposals will be evaluated based on intellectual merit and broader impacts.
        Review criteria include technical approach, team qualifications, and project feasibility.
        """

    @pytest.fixture
    def temp_pdf_file_with_content(self, sample_nsf_solicitation_text):
        """Create a temporary file with NSF solicitation content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write(sample_nsf_solicitation_text)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_llm_metadata_extractor_with_real_structure(self):
        """Test LLM metadata extractor with realistic NSF solicitation structure"""
        sections = {
            "award_information": """
            This program provides awards of up to $750,000 for computational research projects.
            Project duration is typically 3 years (36 months).
            Full proposal deadline: April 15, 2024.
            """,
            "eligibility_information": """
            Principal Investigators must be U.S. citizens, nationals, or permanent residents.
            Co-Principal Investigators may include foreign nationals.
            Only degree-granting institutions of higher education in the United States are eligible.
            A maximum of 2 Principal Investigators per proposal is allowed.
            Teams may include up to 8 total researchers.
            """,
            "program_description": """
            This program supports fundamental research in computational science and engineering.
            Required expertise includes high-performance computing, parallel algorithms, and numerical methods.
            Preferred qualifications include experience with machine learning, artificial intelligence, 
            and data analytics. Technical requirements include access to supercomputing facilities 
            and proficiency in programming languages such as C++, Python, or Fortran.
            """
        }
        
        # Mock the Groq API responses
        mock_responses = {
            "metadata": {
                "award_title": "Advanced Computational Research Program",
                "funding_ceiling": 750000,
                "project_duration_months": 36,
                "submission_deadline": "April 15, 2024"
            },
            "rules": {
                "pi_eligibility_rules": [
                    "Principal Investigators must be U.S. citizens, nationals, or permanent residents",
                    "Co-Principal Investigators may include foreign nationals"
                ],
                "institutional_limitations": [
                    "Only degree-granting institutions of higher education in the United States are eligible"
                ],
                "team_size_constraints": {
                    "max_pi": 2,
                    "max_team_size": 8
                }
            },
            "skills": {
                "required_scientific_skills": [
                    "high-performance computing",
                    "parallel algorithms", 
                    "numerical methods"
                ],
                "preferred_skills": [
                    "machine learning",
                    "artificial intelligence",
                    "data analytics"
                ],
                "technical_requirements": [
                    "access to supercomputing facilities",
                    "proficiency in C++, Python, or Fortran"
                ]
            }
        }
        
        def mock_extract_metadata(section_text, section_type):
            return mock_responses.get(section_type, {})
        
        with patch('app.services.llm_metadata_extractor.Groq') as mock_groq:
            # Setup mock client
            mock_client = Mock()
            mock_groq.return_value = mock_client
            
            extractor = LLMMetadataExtractor(api_key="test_key")
            extractor._extract_metadata_with_llm = Mock(side_effect=mock_extract_metadata)
            
            # Test extraction
            result = extractor.extract_all_metadata(sections)
            
            # Verify comprehensive extraction
            assert result["metadata"]["award_title"] == "Advanced Computational Research Program"
            assert result["metadata"]["funding_ceiling"] == 750000
            assert result["metadata"]["project_duration_months"] == 36
            assert result["metadata"]["submission_deadline"] == "April 15, 2024"
            
            assert "U.S. citizens" in result["rules"]["pi_eligibility_rules"][0]
            assert result["rules"]["team_size_constraints"]["max_pi"] == 2
            assert result["rules"]["team_size_constraints"]["max_team_size"] == 8
            
            assert "high-performance computing" in result["skills"]["required_scientific_skills"]
            assert "machine learning" in result["skills"]["preferred_skills"]
            assert "supercomputing facilities" in result["skills"]["technical_requirements"][0]
            
            # Verify extraction summary
            assert result["extraction_summary"]["sections_processed"] == 3
            assert result["extraction_summary"]["successful_extractions"] == 3
            assert result["extraction_summary"]["failed_extractions"] == 0

    @patch('app.tasks.deconstruction_task.get_job_manager')
    @patch('app.tasks.deconstruction_task.extract_pdf_text')
    @patch('app.tasks.deconstruction_task.chunk_by_sections')
    def test_end_to_end_deconstruction_with_llm(
        self, mock_chunk, mock_extract, mock_get_job_manager,
        temp_pdf_file_with_content, sample_nsf_solicitation_text
    ):
        """Test complete end-to-end deconstruction task with LLM integration"""
        
        # Setup mocks
        mock_job_manager = Mock()
        mock_get_job_manager.return_value = mock_job_manager
        
        mock_extract.return_value = {"text": sample_nsf_solicitation_text}
        mock_chunk.return_value = {
            "sections": {
                "award_information": "Awards up to $750,000, 3 years duration",
                "eligibility_information": "U.S. citizens, max 2 PIs, max 8 team members",
                "program_description": "Computational science, HPC, ML preferred"
            }
        }
        
        # Mock LLM responses
        def mock_llm_extract(section_text, section_type):
            if section_type == "metadata":
                return {
                    "funding_ceiling": 750000,
                    "project_duration_months": 36,
                    "award_title": "Advanced Computational Research Program"
                }
            elif section_type == "rules":
                return {
                    "pi_eligibility_rules": ["U.S. citizens required"],
                    "team_size_constraints": {"max_pi": 2, "max_team_size": 8}
                }
            elif section_type == "skills":
                return {
                    "required_scientific_skills": ["high-performance computing"],
                    "preferred_skills": ["machine learning"]
                }
            return {}
        
        with patch('app.tasks.deconstruction_task.LLMMetadataExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor.is_available.return_value = True
            mock_extractor._extract_metadata_with_llm = Mock(side_effect=mock_llm_extract)
            mock_extractor.extract_all_metadata.return_value = {
                "metadata": {
                    "funding_ceiling": 750000,
                    "project_duration_months": 36,
                    "award_title": "Advanced Computational Research Program"
                },
                "rules": {
                    "pi_eligibility_rules": ["U.S. citizens required"],
                    "team_size_constraints": {"max_pi": 2, "max_team_size": 8}
                },
                "skills": {
                    "required_scientific_skills": ["high-performance computing"],
                    "preferred_skills": ["machine learning"]
                },
                "extraction_summary": {
                    "sections_processed": 3,
                    "successful_extractions": 3,
                    "failed_extractions": 0
                }
            }
            mock_extractor_class.return_value = mock_extractor
            
            # Execute end-to-end task
            result = deconstruct_solicitation_task("integration_test_job", temp_pdf_file_with_content)
            
            # Verify comprehensive result
            assert result.solicitation_id == "integration_test_job"
            assert result.award_title == "Advanced Computational Research Program"
            assert result.funding_ceiling == 750000
            assert result.project_duration_months == 36
            assert "U.S. citizens required" in result.pi_eligibility_rules
            assert result.team_size_constraints["max_pi"] == 2
            assert result.team_size_constraints["max_team_size"] == 8
            assert "high-performance computing" in result.required_scientific_skills
            assert "machine learning" in result.preferred_skills
            assert result.extraction_confidence == 100.0
            
            # Verify job manager interactions
            assert mock_job_manager.update_job_status.call_count >= 4
            final_call = mock_job_manager.update_job_status.call_args_list[-1]
            assert final_call[0][1] == "completed"
            assert final_call[1]["progress"] == 100

    def test_llm_error_handling_and_fallback(self):
        """Test that system gracefully handles LLM errors and falls back appropriately"""
        sections = {
            "award_information": "Awards up to $500,000 for 24 months",
            "program_description": "Research in machine learning and AI"
        }
        
        with patch('app.services.llm_metadata_extractor.Groq') as mock_groq:
            # Setup mock client that fails
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_groq.return_value = mock_client
            
            extractor = LLMMetadataExtractor(api_key="test_key")
            
            # Should handle errors gracefully
            result = extractor.extract_all_metadata(sections)
            
            # Should return empty results but not crash
            assert isinstance(result, dict)
            assert "extraction_summary" in result
            assert result["extraction_summary"]["failed_extractions"] > 0

    def test_prompt_template_quality(self):
        """Test that prompt templates contain necessary instructions and formatting"""
        extractor = LLMMetadataExtractor(api_key="test_key")
        
        sample_text = "Sample NSF solicitation section text"
        
        # Test metadata prompt
        metadata_prompt = extractor._create_metadata_prompt(sample_text)
        assert "award_title" in metadata_prompt
        assert "funding_ceiling" in metadata_prompt
        assert "JSON" in metadata_prompt
        assert sample_text in metadata_prompt
        
        # Test rules prompt
        rules_prompt = extractor._create_rules_prompt(sample_text)
        assert "pi_eligibility_rules" in rules_prompt
        assert "institutional_limitations" in rules_prompt
        assert "team_size_constraints" in rules_prompt
        assert "JSON" in rules_prompt
        
        # Test skills prompt
        skills_prompt = extractor._create_skills_prompt(sample_text)
        assert "required_scientific_skills" in skills_prompt
        assert "preferred_skills" in skills_prompt
        assert "technical_requirements" in skills_prompt
        assert "JSON" in skills_prompt

    def test_data_validation_robustness(self):
        """Test that data validation handles various edge cases robustly"""
        extractor = LLMMetadataExtractor(api_key="test_key")
        
        # Test metadata validation with edge cases
        edge_case_metadata = {
            "award_title": "   Valid Title   ",  # Whitespace
            "funding_ceiling": "500000.50",      # String number
            "project_duration_months": 24.0,     # Float instead of int
            "submission_deadline": ""             # Empty string
        }
        
        validated = extractor._validate_metadata(edge_case_metadata)
        
        assert validated["award_title"] == "Valid Title"  # Trimmed
        assert validated["funding_ceiling"] == 500000.50  # Converted to float
        assert validated["project_duration_months"] == 24  # Converted to int
        assert "submission_deadline" not in validated      # Empty string excluded
        
        # Test rules validation with edge cases
        edge_case_rules = {
            "pi_eligibility_rules": ["Valid rule", "", None, "Another valid rule"],
            "institutional_limitations": None,  # None instead of list
            "team_size_constraints": {"max_team_size": "5", "invalid_key": "invalid"}
        }
        
        validated_rules = extractor._validate_rules(edge_case_rules)
        
        assert len(validated_rules["pi_eligibility_rules"]) == 2  # Only valid rules
        assert validated_rules["institutional_limitations"] == []  # Default empty list
        assert validated_rules["team_size_constraints"]["max_team_size"] == 5  # Converted to int
        assert "invalid_key" not in validated_rules["team_size_constraints"]  # Invalid removed