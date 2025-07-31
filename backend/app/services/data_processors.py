"""
Data processors for institutions, researchers, works, topics, and grants.
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class InstitutionProcessor:
    """Processes institution data from OpenAlex API."""
    
    def process(self, raw_data: Dict) -> Dict:
        """
        Process raw institution data from OpenAlex.
        
        Args:
            raw_data: Raw institution data from OpenAlex API
            
        Returns:
            Processed institution data ready for database insertion
        """
        try:
            processed = {
                'openalex_id': raw_data.get('id', ''),
                'name': raw_data.get('display_name', ''),
                'ror_id': None
            }
            
            # Extract ROR ID if available
            ids = raw_data.get('ids', {})
            if isinstance(ids, dict):
                processed['ror_id'] = ids.get('ror')
            
            logger.debug(f"Processed institution: {processed['name']}")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing institution data: {e}")
            raise


class ResearcherProcessor:
    """Processes researcher data from OpenAlex API."""
    
    def process(self, raw_data: Dict, institution_id: str) -> Dict:
        """
        Process raw researcher data from OpenAlex.
        
        Args:
            raw_data: Raw researcher data from OpenAlex API
            institution_id: Database ID of the institution
            
        Returns:
            Processed researcher data ready for database insertion
        """
        try:
            processed = {
                'institution_id': institution_id,
                'openalex_id': raw_data.get('id', ''),
                'full_name': raw_data.get('display_name', ''),
                'h_index': None,
                'department': None
            }
            
            # Extract h-index from summary stats
            summary_stats = raw_data.get('summary_stats', {})
            if isinstance(summary_stats, dict):
                processed['h_index'] = summary_stats.get('h_index')
            
            # Extract department from affiliations
            affiliations = raw_data.get('affiliations', [])
            if affiliations and isinstance(affiliations, list):
                # Look for the most recent affiliation
                for affiliation in affiliations:
                    if isinstance(affiliation, dict):
                        institution = affiliation.get('institution', {})
                        if isinstance(institution, dict):
                            # Try to extract department information
                            display_name = institution.get('display_name', '')
                            if 'department' in display_name.lower() or 'school' in display_name.lower():
                                processed['department'] = display_name
                                break
            
            logger.debug(f"Processed researcher: {processed['full_name']}")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing researcher data: {e}")
            raise


class WorkProcessor:
    """Processes work (publication) data from OpenAlex API."""
    
    def process(self, raw_data: Dict, researcher_id: str, text_data: Dict) -> Dict:
        """
        Process raw work data from OpenAlex.
        
        Args:
            raw_data: Raw work data from OpenAlex API
            researcher_id: Database ID of the researcher
            text_data: Processed text data (abstract, keywords, embedding)
            
        Returns:
            Processed work data ready for database insertion
        """
        try:
            processed = {
                'researcher_id': researcher_id,
                'openalex_id': raw_data.get('id', ''),
                'title': raw_data.get('title', ''),
                'abstract': text_data.get('abstract', ''),
                'keywords': json.dumps(text_data.get('keywords', [])),  # Store as JSON
                'publication_year': raw_data.get('publication_year'),
                'doi': raw_data.get('doi'),
                'citations': raw_data.get('cited_by_count', 0),
                'embedding': text_data.get('embedding')
            }
            
            # Clean DOI (remove URL prefix if present)
            if processed['doi'] and processed['doi'].startswith('https://doi.org/'):
                processed['doi'] = processed['doi'].replace('https://doi.org/', '')
            
            logger.debug(f"Processed work: {processed['title'][:50]}...")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing work data: {e}")
            raise


class TopicsProcessor:
    """Processes topic data from OpenAlex API."""
    
    def process_work_topics(self, raw_topics: List[Dict], work_id: str) -> List[Dict]:
        """
        Process raw topics data from OpenAlex for a specific work.
        
        Args:
            raw_topics: List of raw topic data from OpenAlex API
            work_id: Database ID of the work
            
        Returns:
            List of processed topic data ready for database insertion
        """
        processed_topics = []
        
        try:
            if not raw_topics or not isinstance(raw_topics, list):
                return processed_topics
            
            for topic_data in raw_topics:
                if not isinstance(topic_data, dict):
                    continue
                
                # The topic data is directly in the topic_data object, not nested under 'topic'
                processed_topic = {
                    'work_id': work_id,
                    'name': topic_data.get('display_name', ''),
                    'type': 'topic',  # Default type
                    'score': topic_data.get('score', 0.0)
                }
                
                # Validate score range
                if processed_topic['score'] < 0.0 or processed_topic['score'] > 1.0:
                    logger.warning(f"Invalid topic score: {processed_topic['score']}, setting to 0.0")
                    processed_topic['score'] = 0.0
                
                if processed_topic['name']:  # Only add if name is not empty
                    processed_topics.append(processed_topic)
            
            logger.debug(f"Processed {len(processed_topics)} topics for work {work_id}")
            return processed_topics
            
        except Exception as e:
            logger.error(f"Error processing work topics data: {e}")
            return processed_topics
    
    def process_standalone_topic(self, raw_topic: Dict) -> Dict:
        """
        Process a standalone topic from OpenAlex topics API.
        
        Args:
            raw_topic: Raw topic data from OpenAlex topics API
            
        Returns:
            Processed topic data ready for database insertion
        """
        try:
            processed = {
                'openalex_id': raw_topic.get('id', ''),
                'name': raw_topic.get('display_name', ''),
                'description': raw_topic.get('description', ''),
                'field': None,
                'subfield': None,
                'domain': None
            }
            
            # Extract field hierarchy
            if 'field' in raw_topic and raw_topic['field']:
                field_data = raw_topic['field']
                if isinstance(field_data, dict):
                    processed['field'] = field_data.get('display_name', '')
            
            if 'subfield' in raw_topic and raw_topic['subfield']:
                subfield_data = raw_topic['subfield']
                if isinstance(subfield_data, dict):
                    processed['subfield'] = subfield_data.get('display_name', '')
            
            if 'domain' in raw_topic and raw_topic['domain']:
                domain_data = raw_topic['domain']
                if isinstance(domain_data, dict):
                    processed['domain'] = domain_data.get('display_name', '')
            
            logger.debug(f"Processed standalone topic: {processed['name']}")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing standalone topic data: {e}")
            raise
    
    # Keep the old method for backward compatibility
    def process(self, raw_topics: List[Dict], work_id: str) -> List[Dict]:
        """Legacy method - redirects to process_work_topics."""
        return self.process_work_topics(raw_topics, work_id)


class GrantsProcessor:
    """Processes grant data from OpenAlex API."""
    
    def process(self, raw_grants: List[Dict], researcher_id: str) -> List[Dict]:
        """
        Process raw grants data from OpenAlex.
        
        Args:
            raw_grants: List of raw grant data from OpenAlex API
            researcher_id: Database ID of the researcher
            
        Returns:
            List of processed grant data ready for database insertion
        """
        processed_grants = []
        
        try:
            if not raw_grants or not isinstance(raw_grants, list):
                return processed_grants
            
            for grant_data in raw_grants:
                if not isinstance(grant_data, dict):
                    continue
                
                processed_grant = {
                    'researcher_id': researcher_id,
                    'award_id': grant_data.get('award_id', ''),
                    'award_year': grant_data.get('award_year'),
                    'role': grant_data.get('role', ''),
                    'award_amount': grant_data.get('award_amount'),
                    'award_title': grant_data.get('award_title', '')
                }
                
                # Validate award year
                current_year = datetime.now().year
                if processed_grant['award_year']:
                    if processed_grant['award_year'] < 1900 or processed_grant['award_year'] > current_year + 10:
                        logger.warning(f"Invalid award year: {processed_grant['award_year']}, setting to None")
                        processed_grant['award_year'] = None
                
                # Validate award amount
                if processed_grant['award_amount'] and processed_grant['award_amount'] < 0:
                    logger.warning(f"Invalid award amount: {processed_grant['award_amount']}, setting to None")
                    processed_grant['award_amount'] = None
                
                if processed_grant['award_id']:  # Only add if award_id is not empty
                    processed_grants.append(processed_grant)
            
            logger.debug(f"Processed {len(processed_grants)} grants for researcher {researcher_id}")
            return processed_grants
            
        except Exception as e:
            logger.error(f"Error processing grants data: {e}")
            return processed_grants


class DataProcessorManager:
    """Manages all data processors."""
    
    def __init__(self):
        """Initialize all processors."""
        self.institution_processor = InstitutionProcessor()
        self.researcher_processor = ResearcherProcessor()
        self.work_processor = WorkProcessor()
        self.topics_processor = TopicsProcessor()
        self.grants_processor = GrantsProcessor()
        
        logger.info("Data processor manager initialized")
    
    def process_institution(self, raw_data: Dict) -> Dict:
        """Process institution data."""
        return self.institution_processor.process(raw_data)
    
    def process_researcher(self, raw_data: Dict, institution_id: str) -> Dict:
        """Process researcher data."""
        return self.researcher_processor.process(raw_data, institution_id)
    
    def process_work(self, raw_data: Dict, researcher_id: str, text_data: Dict) -> Dict:
        """Process work data."""
        return self.work_processor.process(raw_data, researcher_id, text_data)
    
    def process_topics(self, raw_topics: List[Dict], work_id: str) -> List[Dict]:
        """Process topics data for a work."""
        return self.topics_processor.process_work_topics(raw_topics, work_id)
    
    def process_standalone_topic(self, raw_topic: Dict) -> Dict:
        """Process standalone topic data."""
        return self.topics_processor.process_standalone_topic(raw_topic)
    
    def process_grants(self, raw_grants: List[Dict], researcher_id: str) -> List[Dict]:
        """Process grants data."""
        return self.grants_processor.process(raw_grants, researcher_id)