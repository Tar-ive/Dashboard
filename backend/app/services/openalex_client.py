"""
OpenAlex API Client with rate limiting and error handling.
"""
import time
import logging
from typing import Dict, List, Iterator, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class OpenAlexClient:
    """Client for interacting with the OpenAlex API."""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self, email: str, rate_limit_delay: float = 0.1, max_retries: int = 3):
        """
        Initialize the OpenAlex client.
        
        Args:
            email: Email for polite pool access
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
        """
        self.email = email
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'TexasStateResearchPipeline (mailto:{email})',
            'Accept': 'application/json'
        })
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the OpenAlex API with retry logic.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        if params is None:
            params = {}
            
        # Add email to params for polite pool
        params['mailto'] = self.email
        
        logger.debug(f"Making request to {url} with params: {params}")
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        # Rate limiting
        time.sleep(self.rate_limit_delay)
        
        return response.json()
    
    def search_institution(self, name: str) -> Optional[Dict]:
        """
        Search for an institution by name.
        
        Args:
            name: Institution name to search for
            
        Returns:
            Institution data or None if not found
        """
        url = f"{self.BASE_URL}/institutions"
        params = {
            'search': name,
            'per-page': 1
        }
        
        try:
            response = self._make_request(url, params)
            results = response.get('results', [])
            
            if results:
                institution = results[0]
                logger.info(f"Found institution: {institution.get('display_name')} (ID: {institution.get('id')})")
                return institution
            else:
                logger.warning(f"No institution found for search term: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for institution '{name}': {e}")
            raise
    
    def get_researchers_by_institution(self, institution_id: str, limit: Optional[int] = None) -> Iterator[Dict]:
        """
        Get researchers affiliated with an institution.
        
        Args:
            institution_id: OpenAlex institution ID
            limit: Maximum number of researchers to fetch (None for all)
            
        Yields:
            Researcher data dictionaries
        """
        url = f"{self.BASE_URL}/authors"
        params = {
            'filter': f'last_known_institutions.id:{institution_id}',
            'per-page': 200,  # Maximum allowed
            'cursor': '*'
        }
        
        count = 0
        
        while True:
            try:
                response = self._make_request(url, params)
                results = response.get('results', [])
                
                if not results:
                    break
                    
                for researcher in results:
                    if limit and count >= limit:
                        return
                        
                    logger.debug(f"Fetched researcher: {researcher.get('display_name')} (ID: {researcher.get('id')})")
                    yield researcher
                    count += 1
                
                # Check for next page
                meta = response.get('meta', {})
                next_cursor = meta.get('next_cursor')
                
                if not next_cursor:
                    break
                    
                params['cursor'] = next_cursor
                
            except Exception as e:
                logger.error(f"Error fetching researchers for institution {institution_id}: {e}")
                raise
        
        logger.info(f"Fetched {count} researchers for institution {institution_id}")
    
    def get_works_by_author(self, author_id: str, limit: Optional[int] = None) -> Iterator[Dict]:
        """
        Get works (publications) by an author.
        
        Args:
            author_id: OpenAlex author ID
            limit: Maximum number of works to fetch (None for all)
            
        Yields:
            Work data dictionaries
        """
        url = f"{self.BASE_URL}/works"
        params = {
            'filter': f'authorships.author.id:{author_id}',
            'per-page': 200,  # Maximum allowed
            'cursor': '*'
        }
        
        count = 0
        
        while True:
            try:
                response = self._make_request(url, params)
                results = response.get('results', [])
                
                if not results:
                    break
                    
                for work in results:
                    if limit and count >= limit:
                        return
                        
                    logger.debug(f"Fetched work: {work.get('title')} (ID: {work.get('id')})")
                    yield work
                    count += 1
                
                # Check for next page
                meta = response.get('meta', {})
                next_cursor = meta.get('next_cursor')
                
                if not next_cursor:
                    break
                    
                params['cursor'] = next_cursor
                
            except Exception as e:
                logger.error(f"Error fetching works for author {author_id}: {e}")
                raise
        
        logger.info(f"Fetched {count} works for author {author_id}")
    
    def get_topics(self, limit: Optional[int] = None) -> Iterator[Dict]:
        """
        Get topics from OpenAlex.
        
        Args:
            limit: Maximum number of topics to fetch (None for all)
            
        Yields:
            Topic data dictionaries
        """
        url = f"{self.BASE_URL}/topics"
        params = {
            'per-page': 200,  # Maximum allowed
            'cursor': '*',
            'sort': 'cited_by_count:desc'  # Sort by most cited topics first
        }
        
        count = 0
        
        while True:
            try:
                response = self._make_request(url, params)
                results = response.get('results', [])
                
                if not results:
                    break
                    
                for topic in results:
                    if limit and count >= limit:
                        return
                        
                    logger.debug(f"Fetched topic: {topic.get('display_name')} (ID: {topic.get('id')})")
                    yield topic
                    count += 1
                
                # Check for next page
                meta = response.get('meta', {})
                next_cursor = meta.get('next_cursor')
                
                if not next_cursor:
                    break
                    
                params['cursor'] = next_cursor
                
            except Exception as e:
                logger.error(f"Error fetching topics: {e}")
                raise
        
        logger.info(f"Fetched {count} topics from OpenAlex")
    
    def reconstruct_abstract(self, abstract_inverted_index: Dict) -> str:
        """
        Reconstruct abstract text from inverted index.
        
        Args:
            abstract_inverted_index: Dictionary mapping words to position lists
            
        Returns:
            Reconstructed abstract text
        """
        if not abstract_inverted_index:
            return ""
        
        try:
            # Create a list to hold words at their positions
            word_positions = []
            
            for word, positions in abstract_inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            
            # Sort by position and extract words
            word_positions.sort(key=lambda x: x[0])
            words = [word for _, word in word_positions]
            
            # Join words with spaces
            abstract = " ".join(words)
            
            logger.debug(f"Reconstructed abstract: {abstract[:100]}...")
            return abstract
            
        except Exception as e:
            logger.error(f"Error reconstructing abstract: {e}")
            return ""
    
    def validate_response_format(self, data: Dict, expected_type: str) -> bool:
        """
        Validate the format of API response data.
        
        Args:
            data: Response data to validate
            expected_type: Expected data type ('institution', 'author', 'work')
            
        Returns:
            True if format is valid, False otherwise
        """
        try:
            if expected_type == 'institution':
                required_fields = ['id', 'display_name']
                return all(field in data for field in required_fields)
                
            elif expected_type == 'author':
                required_fields = ['id', 'display_name']
                return all(field in data for field in required_fields)
                
            elif expected_type == 'work':
                required_fields = ['id', 'title']
                return all(field in data for field in required_fields)
                
            else:
                logger.warning(f"Unknown expected type: {expected_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating response format: {e}")
            return False