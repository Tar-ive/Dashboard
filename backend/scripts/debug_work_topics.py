#!/usr/bin/env python3
"""
Debug script to examine work data structure and topics from OpenAlex API.
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.openalex_client import OpenAlexClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_work_structure():
    """Debug the structure of work data from OpenAlex."""
    
    # Initialize client
    email = os.getenv('OPENALEX_EMAIL', 'test@example.com')
    client = OpenAlexClient(email=email, rate_limit_delay=0.1)
    
    try:
        # Search for Texas State University
        logger.info("Searching for Texas State University...")
        institution = client.search_institution("Texas State University")
        
        if not institution:
            logger.error("Institution not found")
            return
        
        institution_id = institution['id']
        logger.info(f"Found institution: {institution['display_name']} ({institution_id})")
        
        # Get first researcher
        logger.info("Getting first researcher...")
        researchers = list(client.get_researchers_by_institution(institution_id, limit=1))
        
        if not researchers:
            logger.error("No researchers found")
            return
        
        researcher = researchers[0]
        researcher_id = researcher['id']
        logger.info(f"Found researcher: {researcher['display_name']} ({researcher_id})")
        
        # Get first few works
        logger.info("Getting first 3 works...")
        works = list(client.get_works_by_author(researcher_id, limit=3))
        
        if not works:
            logger.error("No works found")
            return
        
        # Examine work structure
        for i, work in enumerate(works, 1):
            print(f"\n{'='*60}")
            print(f"WORK {i}: {work.get('title', 'No title')[:100]}...")
            print(f"{'='*60}")
            
            # Print basic info
            print(f"ID: {work.get('id')}")
            print(f"Publication Year: {work.get('publication_year')}")
            print(f"Citations: {work.get('cited_by_count')}")
            
            # Check for topics
            topics = work.get('topics', [])
            print(f"\nTOPICS FOUND: {len(topics)}")
            
            if topics:
                print("Topics structure:")
                for j, topic in enumerate(topics[:3]):  # Show first 3 topics
                    print(f"  Topic {j+1}:")
                    print(f"    Raw data: {json.dumps(topic, indent=6)}")
            else:
                print("No topics found in this work")
            
            # Check other potential topic fields
            potential_topic_fields = ['subjects', 'concepts', 'keywords', 'mesh', 'primary_topic']
            for field in potential_topic_fields:
                if field in work and work[field]:
                    print(f"\n{field.upper()}: {work[field]}")
            
            # Show all top-level keys
            print(f"\nALL TOP-LEVEL KEYS: {list(work.keys())}")
            
            print(f"\n{'='*60}")
        
    except Exception as e:
        logger.error(f"Error during debugging: {e}")
        raise


if __name__ == "__main__":
    debug_work_structure()