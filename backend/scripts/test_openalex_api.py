#!/usr/bin/env python3
"""
Manual test script for OpenAlex API integration.
This script tests the basic functionality with real API calls.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.openalex_client import OpenAlexClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_texas_state_university_search():
    """Test searching for Texas State University."""
    print("\n" + "="*60)
    print("TESTING: Texas State University Institution Search")
    print("="*60)
    
    client = OpenAlexClient(email="test@texasstate.edu", rate_limit_delay=0.1)
    
    try:
        institution = client.search_institution("Texas State University")
        
        if institution:
            print(f"✅ Institution found!")
            print(f"   Name: {institution['display_name']}")
            print(f"   ID: {institution['id']}")
            print(f"   Country: {institution.get('country_code', 'N/A')}")
            print(f"   Type: {institution.get('type', 'N/A')}")
            print(f"   Homepage: {institution.get('homepage_url', 'N/A')}")
            
            # Validate response format
            is_valid = client.validate_response_format(institution, 'institution')
            print(f"   Format validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
            
            return institution
        else:
            print("❌ No institution found")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_researchers_fetch(institution_id, limit=5):
    """Test fetching researchers from Texas State University."""
    print("\n" + "="*60)
    print(f"TESTING: Fetching Researchers (limit: {limit})")
    print("="*60)
    
    client = OpenAlexClient(email="test@texasstate.edu", rate_limit_delay=0.1)
    
    try:
        researchers = list(client.get_researchers_by_institution(institution_id, limit=limit))
        
        print(f"✅ Found {len(researchers)} researchers")
        
        for i, researcher in enumerate(researchers, 1):
            print(f"\n{i}. {researcher['display_name']}")
            print(f"   ID: {researcher['id']}")
            
            # Get summary stats
            stats = researcher.get('summary_stats', {})
            print(f"   H-index: {stats.get('h_index', 'N/A')}")
            print(f"   Works count: {stats.get('works_count', 'N/A')}")
            
            # Get affiliations
            affiliations = researcher.get('affiliations', [])
            if affiliations:
                for affiliation in affiliations[:2]:  # Show first 2
                    inst = affiliation.get('institution', {})
                    years = affiliation.get('years', [])
                    print(f"   Affiliation: {inst.get('display_name', 'N/A')} ({min(years) if years else 'N/A'}-{max(years) if years else 'N/A'})")
            
            # Validate response format
            is_valid = client.validate_response_format(researcher, 'author')
            print(f"   Format validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        return researchers
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def test_works_fetch(author_id, author_name, limit=3):
    """Test fetching works for a researcher."""
    print(f"\n" + "="*60)
    print(f"TESTING: Fetching Works for {author_name} (limit: {limit})")
    print("="*60)
    
    client = OpenAlexClient(email="test@texasstate.edu", rate_limit_delay=0.1)
    
    try:
        works = list(client.get_works_by_author(author_id, limit=limit))
        
        print(f"✅ Found {len(works)} works")
        
        for i, work in enumerate(works, 1):
            print(f"\n{i}. {work.get('title', 'No title')}")
            print(f"   ID: {work['id']}")
            print(f"   Year: {work.get('publication_year', 'N/A')}")
            print(f"   DOI: {work.get('doi', 'N/A')}")
            print(f"   Citations: {work.get('cited_by_count', 'N/A')}")
            
            # Test abstract reconstruction
            abstract_index = work.get('abstract_inverted_index')
            if abstract_index:
                abstract = client.reconstruct_abstract(abstract_index)
                print(f"   Abstract: {abstract[:150]}{'...' if len(abstract) > 150 else ''}")
                print(f"   Abstract reconstruction: ✅ SUCCESS")
            else:
                print(f"   Abstract: Not available")
                print(f"   Abstract reconstruction: ⚠️  SKIPPED (no inverted index)")
            
            # Check topics
            topics = work.get('topics', [])
            if topics:
                topic_names = [t.get('display_name', 'Unknown') for t in topics[:3]]
                print(f"   Topics: {', '.join(topic_names)}")
            
            # Validate response format
            is_valid = client.validate_response_format(work, 'work')
            print(f"   Format validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        return works
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def test_abstract_reconstruction():
    """Test abstract reconstruction functionality."""
    print("\n" + "="*60)
    print("TESTING: Abstract Reconstruction")
    print("="*60)
    
    client = OpenAlexClient(email="test@texasstate.edu")
    
    # Test case 1: Simple reconstruction
    print("\n1. Simple reconstruction test:")
    inverted_index = {
        "This": [0],
        "is": [1],
        "a": [2],
        "test": [3],
        "abstract": [4]
    }
    
    result = client.reconstruct_abstract(inverted_index)
    expected = "This is a test abstract"
    
    print(f"   Input: {inverted_index}")
    print(f"   Output: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   Result: {'✅ PASS' if result == expected else '❌ FAIL'}")
    
    # Test case 2: Complex reconstruction with repeated words
    print("\n2. Complex reconstruction test:")
    inverted_index = {
        "The": [0, 8],
        "quick": [1],
        "brown": [2],
        "fox": [3],
        "jumps": [4],
        "over": [5],
        "lazy": [7],
        "dog": [9]
    }
    
    result = client.reconstruct_abstract(inverted_index)
    expected = "The quick brown fox jumps over lazy The dog"
    
    print(f"   Input: {inverted_index}")
    print(f"   Output: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   Result: {'✅ PASS' if result == expected else '❌ FAIL'}")
    
    # Test case 3: Empty input
    print("\n3. Empty input test:")
    result = client.reconstruct_abstract({})
    expected = ""
    
    print(f"   Input: {{}}")
    print(f"   Output: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   Result: {'✅ PASS' if result == expected else '❌ FAIL'}")


def test_data_quality_validation():
    """Test data quality validation functions."""
    print("\n" + "="*60)
    print("TESTING: Data Quality Validation")
    print("="*60)
    
    client = OpenAlexClient(email="test@texasstate.edu")
    
    # Test institution validation
    print("\n1. Institution validation:")
    valid_institution = {
        "id": "https://openalex.org/I12345",
        "display_name": "Texas State University"
    }
    invalid_institution = {"display_name": "Texas State University"}  # Missing ID
    
    result1 = client.validate_response_format(valid_institution, 'institution')
    result2 = client.validate_response_format(invalid_institution, 'institution')
    
    print(f"   Valid data: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"   Invalid data: {'✅ PASS' if not result2 else '❌ FAIL'}")
    
    # Test author validation
    print("\n2. Author validation:")
    valid_author = {
        "id": "https://openalex.org/A12345",
        "display_name": "John Doe"
    }
    invalid_author = {"id": "https://openalex.org/A12345"}  # Missing display_name
    
    result1 = client.validate_response_format(valid_author, 'author')
    result2 = client.validate_response_format(invalid_author, 'author')
    
    print(f"   Valid data: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"   Invalid data: {'✅ PASS' if not result2 else '❌ FAIL'}")
    
    # Test work validation
    print("\n3. Work validation:")
    valid_work = {
        "id": "https://openalex.org/W12345",
        "title": "Sample Paper"
    }
    invalid_work = {"id": "https://openalex.org/W12345"}  # Missing title
    
    result1 = client.validate_response_format(valid_work, 'work')
    result2 = client.validate_response_format(invalid_work, 'work')
    
    print(f"   Valid data: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"   Invalid data: {'✅ PASS' if not result2 else '❌ FAIL'}")


def main():
    """Run all tests."""
    print("OpenAlex API Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Abstract reconstruction (offline test)
    test_abstract_reconstruction()
    
    # Test 2: Data quality validation (offline test)
    test_data_quality_validation()
    
    # Test 3: Institution search (online test)
    institution = test_texas_state_university_search()
    
    if institution:
        # Test 4: Researchers fetch (online test)
        researchers = test_researchers_fetch(institution['id'], limit=3)
        
        if researchers:
            # Test 5: Works fetch (online test)
            first_researcher = researchers[0]
            test_works_fetch(
                first_researcher['id'], 
                first_researcher['display_name'], 
                limit=2
            )
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)
    print("\nIf all tests show ✅ PASS, the OpenAlex API integration is working correctly!")
    print("If any tests show ❌ FAIL, check the error messages above.")


if __name__ == "__main__":
    main()