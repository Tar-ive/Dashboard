"""Tests for LLM metadata extraction service."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.llm_metadata_extractor import LLMMetadataExtractor


class TestLLMMetadataExtractor:
    """Test suite for LLM metadata extraction functionality"""

    @pytest.fixture
    def mock_groq_client(self):
        """Mock Groq client for testing"""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        mock_message.content = '{"test": "response"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        return mock_client

    @pytest.fixture
    def extractor_with_mock_client(self, mock_groq_client):
        """LLM extractor with mocked client"""
        with patch('app.services.llm_metadata_extractor.Groq') as mock_groq:
            mock_groq.return_value = mock_groq_client
            extractor = LLMMetadataExtractor(api_key="test_key")
            return extractor

    @pytest.fixture
    def sample_metadata_section(self):
        """Sample award information section text"""
        return """
        Award Information
        
        This program provides awards of up to $500,000 for projects lasting 36 months.
        The submission deadline is March 15, 2024.
        Award Title: Advanced Research in Computational Sciences
        """

    @pytest.fixture
    def sample_rules_section(self):
        """Sample eligibility section text"""
        return """
        Eligibility Information
        
        Principal Investigators must be U.S. citizens or permanent residents.
        Only accredited universities in the United States are eligible to apply.
        Teams may include up to 5 researchers with a maximum of 2 PIs.
        """

    @pytest.fixture
    def sample_skills_section(self):
        """Sample program description section text"""
        return """
        Program Description
        
        This program requires expertise in machine learning, data analysis, and statistical modeling.
        Preferred skills include Python programming, deep learning frameworks, and cloud computing.
        Technical requirements include access to high-performance computing resources.
        """

    def test_initialization_with_api_key(self):
        """Test successful initialization with API key"""
        with patch('app.services.llm_metadata_extractor.Groq') as mock_groq:
            mock_groq.return_value = Mock()
            extractor = LLMMetadataExtractor(api_key="test_key")
            assert extractor.is_available()
            assert extractor.api_key == "test_key"
            assert extractor.model == "meta-llama/llama-4-scout-17b-16e-instruct"

    def test_initialization_without_api_key(self):
        """Test initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            extractor = LLMMetadataExtractor()
            assert not extractor.is_available()
            assert extractor.client is None

    def test_initialization_with_env_api_key(self):
        """Test initialization with API key from environment"""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'env_test_key'}):
            with patch('app.services.llm_metadata_extractor.Groq') as mock_groq:
                mock_groq.return_value = Mock()
                extractor = LLMMetadataExtractor()
                assert extractor.api_key == "env_test_key"

    def test_initialization_groq_import_error(self):
        """Test initialization when Groq library is not available"""
        with patch('app.services.llm_metadata_extractor.Groq', side_effect=ImportError):
            extractor = LLMMetadataExtractor(api_key="test_key")
            assert not extractor.is_available()
            assert extractor.client is None

    def test_extract_metadata_with_llm_success(self, extractor_with_mock_client, sample_metadata_section):
        """Test successful metadata extraction"""
        # Mock successful JSON response
        mock_response = {
            "award_title": "Advanced Research in Computational Sciences",
            "funding_ceiling": 500000,
            "project_duration_months": 36,
            "submission_deadline": "March 15, 2024"
        }
        
        extractor_with_mock_client.client.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)
        
        result = extractor_with_mock_client._extract_metadata_with_llm(sample_metadata_section, "metadata")
        
        assert result["award_title"] == "Advanced Research in Computational Sciences"
        assert result["funding_ceiling"] == 500000
        assert result["project_duration_months"] == 36
        assert result["submission_deadline"] == "March 15, 2024"

    def test_extract_metadata_with_llm_service_unavailable(self, sample_metadata_section):
        """Test metadata extraction when LLM service is unavailable"""
        extractor = LLMMetadataExtractor()  # No API key
        result = extractor._extract_metadata_with_llm(sample_metadata_section, "metadata")
        assert result == {}

    def test_extract_metadata_with_llm_api_error(self, extractor_with_mock_client, sample_metadata_section):
        """Test metadata extraction when API call fails"""
        extractor_with_mock_client.client.chat.completions.create.side_effect = Exception("API Error")
        
        result = extractor_with_mock_client._extract_metadata_with_llm(sample_metadata_section, "metadata")
        assert result == {}

    def test_extract_rules_with_llm_success(self, extractor_with_mock_client, sample_rules_section):
        """Test successful rules extraction"""
        mock_response = {
            "pi_eligibility_rules": ["Must be U.S. citizens or permanent residents"],
            "institutional_limitations": ["Only accredited universities in the United States"],
            "team_size_constraints": {"max_team_size": 5, "max_pi": 2}
        }
        
        extractor_with_mock_client.client.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)
        
        result = extractor_with_mock_client._extract_metadata_with_llm(sample_rules_section, "rules")
        
        assert "Must be U.S. citizens or permanent residents" in result["pi_eligibility_rules"]
        assert "Only accredited universities in the United States" in result["institutional_limitations"]
        assert result["team_size_constraints"]["max_team_size"] == 5
        assert result["team_size_constraints"]["max_pi"] == 2

    def test_extract_skills_with_llm_success(self, extractor_with_mock_client, sample_skills_section):
        """Test successful skills extraction"""
        mock_response = {
            "required_scientific_skills": ["machine learning", "data analysis", "statistical modeling"],
            "preferred_skills": ["Python programming", "deep learning frameworks", "cloud computing"],
            "technical_requirements": ["high-performance computing resources"]
        }
        
        extractor_with_mock_client.client.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)
        
        result = extractor_with_mock_client._extract_metadata_with_llm(sample_skills_section, "skills")
        
        assert "machine learning" in result["required_scientific_skills"]
        assert "Python programming" in result["preferred_skills"]
        assert "high-performance computing resources" in result["technical_requirements"]

    def test_create_metadata_prompt(self, extractor_with_mock_client, sample_metadata_section):
        """Test metadata prompt creation"""
        prompt = extractor_with_mock_client._create_metadata_prompt(sample_metadata_section)
        
        assert "award_title" in prompt
        assert "funding_ceiling" in prompt
        assert "project_duration_months" in prompt
        assert "submission_deadline" in prompt
        assert sample_metadata_section in prompt

    def test_create_rules_prompt(self, extractor_with_mock_client, sample_rules_section):
        """Test rules prompt creation"""
        prompt = extractor_with_mock_client._create_rules_prompt(sample_rules_section)
        
        assert "pi_eligibility_rules" in prompt
        assert "institutional_limitations" in prompt
        assert "team_size_constraints" in prompt
        assert sample_rules_section in prompt

    def test_create_skills_prompt(self, extractor_with_mock_client, sample_skills_section):
        """Test skills prompt creation"""
        prompt = extractor_with_mock_client._create_skills_prompt(sample_skills_section)
        
        assert "required_scientific_skills" in prompt
        assert "preferred_skills" in prompt
        assert "technical_requirements" in prompt
        assert sample_skills_section in prompt

    def test_create_extraction_prompt_invalid_type(self, extractor_with_mock_client):
        """Test prompt creation with invalid section type"""
        with pytest.raises(ValueError, match="Unknown section type"):
            extractor_with_mock_client._create_extraction_prompt("test", "invalid_type")

    def test_parse_llm_response_valid_json(self, extractor_with_mock_client):
        """Test parsing valid JSON response"""
        response_text = '{"test_key": "test_value", "number": 42}'
        result = extractor_with_mock_client._parse_llm_response(response_text, "metadata")
        
        # Should be processed through validation
        assert isinstance(result, dict)

    def test_parse_llm_response_json_with_extra_text(self, extractor_with_mock_client):
        """Test parsing JSON response with extra text"""
        response_text = 'Here is the JSON: {"test_key": "test_value"} and some extra text'
        result = extractor_with_mock_client._parse_llm_response(response_text, "metadata")
        
        assert isinstance(result, dict)

    def test_parse_llm_response_invalid_json(self, extractor_with_mock_client):
        """Test parsing invalid JSON response"""
        response_text = 'This is not valid JSON at all'
        result = extractor_with_mock_client._parse_llm_response(response_text, "metadata")
        
        assert result == {}

    def test_validate_metadata_complete(self, extractor_with_mock_client):
        """Test metadata validation with complete data"""
        data = {
            "award_title": "Test Award",
            "funding_ceiling": 500000.0,
            "project_duration_months": 36,
            "submission_deadline": "March 15, 2024"
        }
        
        result = extractor_with_mock_client._validate_metadata(data)
        
        assert result["award_title"] == "Test Award"
        assert result["funding_ceiling"] == 500000.0
        assert result["project_duration_months"] == 36
        assert result["submission_deadline"] == "March 15, 2024"

    def test_validate_metadata_partial(self, extractor_with_mock_client):
        """Test metadata validation with partial data"""
        data = {
            "award_title": "Test Award",
            "funding_ceiling": None,
            "project_duration_months": "invalid",
            "submission_deadline": ""
        }
        
        result = extractor_with_mock_client._validate_metadata(data)
        
        assert result["award_title"] == "Test Award"
        assert "funding_ceiling" not in result
        assert "project_duration_months" not in result
        assert "submission_deadline" not in result

    def test_validate_rules_complete(self, extractor_with_mock_client):
        """Test rules validation with complete data"""
        data = {
            "pi_eligibility_rules": ["Rule 1", "Rule 2"],
            "institutional_limitations": ["Limit 1"],
            "team_size_constraints": {"max_team_size": 5, "min_team_size": 2}
        }
        
        result = extractor_with_mock_client._validate_rules(data)
        
        assert len(result["pi_eligibility_rules"]) == 2
        assert len(result["institutional_limitations"]) == 1
        assert result["team_size_constraints"]["max_team_size"] == 5
        assert result["team_size_constraints"]["min_team_size"] == 2

    def test_validate_rules_invalid_data(self, extractor_with_mock_client):
        """Test rules validation with invalid data"""
        data = {
            "pi_eligibility_rules": "not a list",
            "institutional_limitations": [None, "", "Valid limit"],
            "team_size_constraints": {"max_team_size": "invalid"}
        }
        
        result = extractor_with_mock_client._validate_rules(data)
        
        assert result["pi_eligibility_rules"] == []
        assert result["institutional_limitations"] == ["Valid limit"]
        assert result["team_size_constraints"] == {}

    def test_validate_skills_complete(self, extractor_with_mock_client):
        """Test skills validation with complete data"""
        data = {
            "required_scientific_skills": ["ML", "AI"],
            "preferred_skills": ["Python", "R"],
            "technical_requirements": ["GPU", "Cloud"]
        }
        
        result = extractor_with_mock_client._validate_skills(data)
        
        assert len(result["required_scientific_skills"]) == 2
        assert len(result["preferred_skills"]) == 2
        assert len(result["technical_requirements"]) == 2

    def test_validate_skills_empty_and_invalid(self, extractor_with_mock_client):
        """Test skills validation with empty and invalid data"""
        data = {
            "required_scientific_skills": ["", None, "Valid skill"],
            "preferred_skills": "not a list",
            "technical_requirements": []
        }
        
        result = extractor_with_mock_client._validate_skills(data)
        
        assert result["required_scientific_skills"] == ["Valid skill"]
        assert result["preferred_skills"] == []
        assert result["technical_requirements"] == []

    def test_extract_all_metadata_success(self, extractor_with_mock_client):
        """Test extracting metadata from multiple sections"""
        sections = {
            "award_information": "Award info with $500,000 funding",
            "eligibility_information": "PI must be US citizen",
            "program_description": "Requires machine learning skills"
        }
        
        # Mock different responses for different sections
        def mock_extract(section_text, section_type):
            if section_type == "metadata":
                return {"funding_ceiling": 500000}
            elif section_type == "rules":
                return {"pi_eligibility_rules": ["US citizen required"]}
            elif section_type == "skills":
                return {"required_scientific_skills": ["machine learning"]}
            return {}
        
        extractor_with_mock_client._extract_metadata_with_llm = Mock(side_effect=mock_extract)
        
        result = extractor_with_mock_client.extract_all_metadata(sections)
        
        assert result["extraction_summary"]["sections_processed"] == 3
        assert result["extraction_summary"]["successful_extractions"] == 3
        assert result["extraction_summary"]["failed_extractions"] == 0
        assert result["metadata"]["funding_ceiling"] == 500000
        assert "US citizen required" in result["rules"]["pi_eligibility_rules"]
        assert "machine learning" in result["skills"]["required_scientific_skills"]

    def test_extract_all_metadata_with_failures(self, extractor_with_mock_client):
        """Test extracting metadata with some failures"""
        sections = {
            "award_information": "Award info",
            "eligibility_information": "Eligibility info",
            "program_description": "Program info"
        }
        
        # Mock mixed success/failure responses
        def mock_extract(section_text, section_type):
            if section_type == "metadata":
                return {"funding_ceiling": 500000}
            elif section_type == "rules":
                raise Exception("Extraction failed")
            elif section_type == "skills":
                return {}  # Empty result
            return {}
        
        extractor_with_mock_client._extract_metadata_with_llm = Mock(side_effect=mock_extract)
        
        result = extractor_with_mock_client.extract_all_metadata(sections)
        
        assert result["extraction_summary"]["sections_processed"] == 3
        assert result["extraction_summary"]["successful_extractions"] == 1
        assert result["extraction_summary"]["failed_extractions"] == 2

    def test_extract_all_metadata_empty_sections(self, extractor_with_mock_client):
        """Test extracting metadata from empty sections"""
        sections = {
            "award_information": "",
            "eligibility_information": None,
            "program_description": "   "
        }
        
        result = extractor_with_mock_client.extract_all_metadata(sections)
        
        assert result["extraction_summary"]["sections_processed"] == 0
        assert result["extraction_summary"]["successful_extractions"] == 0
        assert result["extraction_summary"]["failed_extractions"] == 0

    def test_llm_api_call_parameters(self, extractor_with_mock_client, sample_metadata_section):
        """Test that LLM API is called with correct parameters"""
        extractor_with_mock_client._extract_metadata_with_llm(sample_metadata_section, "metadata")
        
        # Verify API call parameters
        call_args = extractor_with_mock_client.client.chat.completions.create.call_args
        assert call_args[1]["model"] == "meta-llama/llama-4-scout-17b-16e-instruct"
        assert call_args[1]["max_tokens"] == 2000
        assert call_args[1]["temperature"] == 0.1
        assert len(call_args[1]["messages"]) == 1
        assert call_args[1]["messages"][0]["role"] == "user"

    def test_prompt_contains_section_text(self, extractor_with_mock_client):
        """Test that prompts contain the section text"""
        section_text = "This is test section content"
        
        metadata_prompt = extractor_with_mock_client._create_metadata_prompt(section_text)
        rules_prompt = extractor_with_mock_client._create_rules_prompt(section_text)
        skills_prompt = extractor_with_mock_client._create_skills_prompt(section_text)
        
        assert section_text in metadata_prompt
        assert section_text in rules_prompt
        assert section_text in skills_prompt

    def test_response_parsing_with_malformed_json(self, extractor_with_mock_client):
        """Test response parsing with various malformed JSON scenarios"""
        malformed_responses = [
            '{"incomplete": "json"',  # Missing closing brace
            '{"invalid": json}',      # Invalid JSON syntax
            'Not JSON at all',        # No JSON content
            '',                       # Empty response
            '{"valid": "json"} extra text {"invalid": json}'  # Mixed content
        ]
        
        for response in malformed_responses:
            result = extractor_with_mock_client._parse_llm_response(response, "metadata")
            assert isinstance(result, dict)  # Should always return dict, even if empty