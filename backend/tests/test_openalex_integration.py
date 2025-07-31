"""
Integration tests for OpenAlex API client.
"""
import pytest
import os
import requests
from unittest.mock import Mock, patch
from app.services.openalex_client import OpenAlexClient


class TestOpenAlexIntegration:
    """Test OpenAlex API integration and basic functionality."""
    
    @pytest.fixture
    def client(self):
        """Create OpenAlex client for testing."""
        return OpenAlexClient(email="test@example.com", rate_limit_delay=0.01)
    
    @pytest.fixture
    def mock_institution_response(self):
        """Mock institution API response."""
        return {
            "results": [{
                "id": "https://openalex.org/I12345",
                "display_name": "Texas State University",
                "ror": "https://ror.org/02hpadn98",
                "country_code": "US",
                "type": "education",
                "homepage_url": "https://www.txstate.edu"
            }],
            "meta": {
                "count": 1,
                "db_response_time_ms": 10
            }
        }
    
    @pytest.fixture
    def mock_researcher_response(self):
        """Mock researcher API response."""
        return {
            "results": [{
                "id": "https://openalex.org/A12345",
                "display_name": "John Doe",
                "summary_stats": {
                    "h_index": 25,
                    "works_count": 50
                },
                "affiliations": [{
                    "institution": {
                        "id": "https://openalex.org/I12345",
                        "display_name": "Texas State University"
                    },
                    "years": [2020, 2021, 2022]
                }]
            }],
            "meta": {
                "count": 1,
                "next_cursor": None
            }
        }
    
    @pytest.fixture
    def mock_work_response(self):
        """Mock work API response."""
        return {
            "results": [{
                "id": "https://openalex.org/W12345",
                "title": "Sample Research Paper",
                "abstract_inverted_index": {
                    "This": [0],
                    "is": [1],
                    "a": [2],
                    "sample": [3],
                    "abstract": [4],
                    "for": [5],
                    "testing": [6]
                },
                "publication_year": 2022,
                "doi": "https://doi.org/10.1000/sample",
                "cited_by_count": 10,
                "topics": [{
                    "id": "https://openalex.org/T12345",
                    "display_name": "Computer Science",
                    "score": 0.95
                }]
            }],
            "meta": {
                "count": 1,
                "next_cursor": None
            }
        }
    
    def test_client_initialization(self, client):
        """Test client initialization with proper configuration."""
        assert client.email == "test@example.com"
        assert client.rate_limit_delay == 0.01
        assert client.max_retries == 3
        assert client.BASE_URL == "https://api.openalex.org"
        assert 'User-Agent' in client.session.headers
        assert 'Accept' in client.session.headers
    
    @patch('requests.Session.get')
    def test_search_institution_success(self, mock_get, client, mock_institution_response):
        """Test successful institution search."""
        mock_response = Mock()
        mock_response.json.return_value = mock_institution_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = client.search_institution("Texas State University")
        
        assert result is not None
        assert result['display_name'] == "Texas State University"
        assert result['id'] == "https://openalex.org/I12345"
        
        # Verify request was made with correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert 'search' in kwargs['params']
        assert kwargs['params']['search'] == "Texas State University"
        assert kwargs['params']['mailto'] == "test@example.com"
    
    @patch('requests.Session.get')
    def test_search_institution_not_found(self, mock_get, client):
        """Test institution search when no results found."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": [], "meta": {"count": 0}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = client.search_institution("Nonexistent University")
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_get_researchers_by_institution(self, mock_get, client, mock_researcher_response):
        """Test fetching researchers by institution."""
        mock_response = Mock()
        mock_response.json.return_value = mock_researcher_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        researchers = list(client.get_researchers_by_institution("https://openalex.org/I12345", limit=1))
        
        assert len(researchers) == 1
        assert researchers[0]['display_name'] == "John Doe"
        assert researchers[0]['summary_stats']['h_index'] == 25
        
        # Verify request parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert 'filter' in kwargs['params']
        assert "last_known_institutions.id:https://openalex.org/I12345" in kwargs['params']['filter']
    
    @patch('requests.Session.get')
    def test_get_works_by_author(self, mock_get, client, mock_work_response):
        """Test fetching works by author."""
        mock_response = Mock()
        mock_response.json.return_value = mock_work_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        works = list(client.get_works_by_author("https://openalex.org/A12345", limit=1))
        
        assert len(works) == 1
        assert works[0]['title'] == "Sample Research Paper"
        assert works[0]['publication_year'] == 2022
        assert works[0]['cited_by_count'] == 10
        
        # Verify request parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert 'filter' in kwargs['params']
        assert "authorships.author.id:https://openalex.org/A12345" in kwargs['params']['filter']
    
    def test_reconstruct_abstract_success(self, client):
        """Test successful abstract reconstruction from inverted index."""
        inverted_index = {
            "This": [0],
            "is": [1],
            "a": [2],
            "sample": [3],
            "abstract": [4],
            "for": [5],
            "testing": [6]
        }
        
        result = client.reconstruct_abstract(inverted_index)
        expected = "This is a sample abstract for testing"
        
        assert result == expected
    
    def test_reconstruct_abstract_empty(self, client):
        """Test abstract reconstruction with empty input."""
        result = client.reconstruct_abstract({})
        assert result == ""
        
        result = client.reconstruct_abstract(None)
        assert result == ""
    
    def test_reconstruct_abstract_complex(self, client):
        """Test abstract reconstruction with complex inverted index."""
        inverted_index = {
            "The": [0, 10],
            "quick": [1],
            "brown": [2],
            "fox": [3],
            "jumps": [4],
            "over": [5],
            "lazy": [7],
            "dog": [8],
            "and": [9],
            "cat": [11]
        }
        
        result = client.reconstruct_abstract(inverted_index)
        expected = "The quick brown fox jumps over lazy dog and The cat"
        
        assert result == expected
    
    def test_validate_response_format_institution(self, client):
        """Test response format validation for institution data."""
        valid_data = {
            "id": "https://openalex.org/I12345",
            "display_name": "Texas State University",
            "country_code": "US"
        }
        
        invalid_data = {
            "display_name": "Texas State University"
            # Missing required 'id' field
        }
        
        assert client.validate_response_format(valid_data, 'institution') is True
        assert client.validate_response_format(invalid_data, 'institution') is False
    
    def test_validate_response_format_author(self, client):
        """Test response format validation for author data."""
        valid_data = {
            "id": "https://openalex.org/A12345",
            "display_name": "John Doe",
            "summary_stats": {"h_index": 25}
        }
        
        invalid_data = {
            "id": "https://openalex.org/A12345"
            # Missing required 'display_name' field
        }
        
        assert client.validate_response_format(valid_data, 'author') is True
        assert client.validate_response_format(invalid_data, 'author') is False
    
    def test_validate_response_format_work(self, client):
        """Test response format validation for work data."""
        valid_data = {
            "id": "https://openalex.org/W12345",
            "title": "Sample Research Paper",
            "publication_year": 2022
        }
        
        invalid_data = {
            "id": "https://openalex.org/W12345"
            # Missing required 'title' field
        }
        
        assert client.validate_response_format(valid_data, 'work') is True
        assert client.validate_response_format(invalid_data, 'work') is False
    
    def test_validate_response_format_unknown_type(self, client):
        """Test response format validation with unknown type."""
        data = {"id": "test", "name": "test"}
        
        assert client.validate_response_format(data, 'unknown') is False
    
    @patch('requests.Session.get')
    def test_rate_limiting(self, mock_get, client):
        """Test that rate limiting is applied between requests."""
        import time
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": [], "meta": {"count": 0}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        start_time = time.time()
        client.search_institution("Test University 1")
        client.search_institution("Test University 2")
        end_time = time.time()
        
        # Should have at least one rate limit delay
        assert end_time - start_time >= client.rate_limit_delay
    
    @patch('requests.Session.get')
    def test_error_handling_and_retry(self, mock_get, client):
        """Test error handling and retry logic."""
        # First call fails, second succeeds
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            Mock(json=lambda: {"results": [], "meta": {"count": 0}}, raise_for_status=lambda: None)
        ]
        
        # Should not raise exception due to retry logic
        result = client.search_institution("Test University")
        assert result is None  # Empty results
        
        # Should have made 2 calls (1 failed + 1 retry)
        assert mock_get.call_count == 2


# Integration test that can be run manually with real API
class TestOpenAlexRealAPI:
    """Real API integration tests (run manually)."""
    
    @pytest.mark.skip(reason="Real API test - run manually")
    def test_real_texas_state_university_search(self):
        """Test searching for Texas State University using real API."""
        client = OpenAlexClient(email="test@example.com")
        
        result = client.search_institution("Texas State University")
        
        assert result is not None
        assert "Texas State" in result['display_name']
        assert result['id'].startswith("https://openalex.org/I")
        
        print(f"Found institution: {result['display_name']}")
        print(f"Institution ID: {result['id']}")
    
    @pytest.mark.skip(reason="Real API test - run manually")
    def test_real_researchers_fetch(self):
        """Test fetching real researchers from Texas State University."""
        client = OpenAlexClient(email="test@example.com")
        
        # First get the institution
        institution = client.search_institution("Texas State University")
        assert institution is not None
        
        # Then get some researchers
        researchers = list(client.get_researchers_by_institution(institution['id'], limit=5))
        
        assert len(researchers) > 0
        
        for researcher in researchers:
            assert client.validate_response_format(researcher, 'author')
            print(f"Researcher: {researcher['display_name']}")
            
            # Test getting works for first researcher
            if researchers:
                works = list(client.get_works_by_author(researchers[0]['id'], limit=3))
                for work in works:
                    assert client.validate_response_format(work, 'work')
                    print(f"  Work: {work['title']}")
                    
                    # Test abstract reconstruction if available
                    if work.get('abstract_inverted_index'):
                        abstract = client.reconstruct_abstract(work['abstract_inverted_index'])
                        print(f"  Abstract: {abstract[:100]}...")