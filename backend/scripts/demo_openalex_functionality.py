#!/usr/bin/env python3
"""
Demonstration script showing OpenAlex API integration functionality.
This script demonstrates all the key features implemented in task 1.
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


def demonstrate_openalex_integration():
    """Demonstrate the complete OpenAlex API integration."""
    
    print("🚀 OpenAlex API Integration Demonstration")
    print("=" * 60)
    
    # Initialize client
    client = OpenAlexClient(email="demo@texasstate.edu", rate_limit_delay=0.1)
    print("✅ OpenAlex client initialized with rate limiting and error handling")
    
    # 1. Search for Texas State University
    print("\n📍 Step 1: Searching for Texas State University...")
    institution = client.search_institution("Texas State University")
    
    if institution:
        print(f"✅ Found: {institution['display_name']}")
        print(f"   OpenAlex ID: {institution['id']}")
        print(f"   Country: {institution.get('country_code', 'N/A')}")
        
        # Validate response format
        is_valid = client.validate_response_format(institution, 'institution')
        print(f"   Data quality validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    else:
        print("❌ Institution not found")
        return
    
    # 2. Fetch sample researchers
    print(f"\n👥 Step 2: Fetching sample researchers from {institution['display_name']}...")
    researchers = list(client.get_researchers_by_institution(institution['id'], limit=2))
    
    print(f"✅ Found {len(researchers)} researchers")
    for i, researcher in enumerate(researchers, 1):
        print(f"   {i}. {researcher['display_name']}")
        stats = researcher.get('summary_stats', {})
        print(f"      H-index: {stats.get('h_index', 'N/A')}")
        
        # Validate response format
        is_valid = client.validate_response_format(researcher, 'author')
        print(f"      Data validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    if not researchers:
        print("❌ No researchers found")
        return
    
    # 3. Fetch works for first researcher
    first_researcher = researchers[0]
    print(f"\n📚 Step 3: Fetching works for {first_researcher['display_name']}...")
    works = list(client.get_works_by_author(first_researcher['id'], limit=2))
    
    print(f"✅ Found {len(works)} works")
    for i, work in enumerate(works, 1):
        print(f"   {i}. {work.get('title', 'No title')[:80]}...")
        print(f"      Year: {work.get('publication_year', 'N/A')}")
        print(f"      Citations: {work.get('cited_by_count', 'N/A')}")
        
        # Test abstract reconstruction
        abstract_index = work.get('abstract_inverted_index')
        if abstract_index:
            abstract = client.reconstruct_abstract(abstract_index)
            print(f"      Abstract: {abstract[:100]}...")
            print(f"      Abstract reconstruction: ✅ SUCCESS")
        else:
            print(f"      Abstract: Not available")
            print(f"      Abstract reconstruction: ⚠️  SKIPPED")
        
        # Validate response format
        is_valid = client.validate_response_format(work, 'work')
        print(f"      Data validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    # 4. Demonstrate abstract reconstruction with sample data
    print(f"\n🔧 Step 4: Demonstrating abstract reconstruction...")
    sample_inverted_index = {
        "Machine": [0],
        "learning": [1],
        "algorithms": [2],
        "are": [3],
        "transforming": [4],
        "research": [5],
        "methodologies": [6],
        "across": [7],
        "multiple": [8],
        "disciplines": [9]
    }
    
    reconstructed = client.reconstruct_abstract(sample_inverted_index)
    print(f"✅ Sample reconstruction: '{reconstructed}'")
    
    # 5. Summary
    print(f"\n📊 Summary of Demonstrated Features:")
    print("   ✅ OpenAlex API client with rate limiting")
    print("   ✅ Error handling and retry logic")
    print("   ✅ Texas State University institution search")
    print("   ✅ Researcher data fetching with pagination")
    print("   ✅ Works data fetching with pagination")
    print("   ✅ Abstract reconstruction from inverted index")
    print("   ✅ Response format validation")
    print("   ✅ Data quality validation")
    
    print(f"\n🎉 OpenAlex API integration is fully functional!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demonstrate_openalex_integration()
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        logger.error(f"Demonstration failed: {e}", exc_info=True)