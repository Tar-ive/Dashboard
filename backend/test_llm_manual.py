#!/usr/bin/env python3
"""Manual test script for LLM metadata extraction with real Groq API."""

import os
import sys
import json
from dotenv import load_dotenv
from app.services.llm_metadata_extractor import LLMMetadataExtractor

# Load environment variables from .env file
load_dotenv()

def test_llm_with_real_api():
    """Test LLM metadata extraction with real Groq API"""
    
    print("🧪 Testing LLM Metadata Extraction with Groq API")
    print("=" * 60)
    
    # Check if API key is available
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("💡 Please set GROQ_API_KEY to test with real API")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Initialize extractor
    try:
        extractor = LLMMetadataExtractor(api_key=api_key, model="meta-llama/llama-4-scout-17b-16e-instruct")
        print(f"✅ LLM Extractor initialized successfully")
        print(f"📡 Using model: meta-llama/llama-4-scout-17b-16e-instruct")
    except Exception as e:
        print(f"❌ Failed to initialize LLM extractor: {e}")
        return False
    
    if not extractor.is_available():
        print("❌ LLM service is not available")
        return False
    
    print("✅ LLM service is available")
    
    # Test sample NSF solicitation sections
    test_sections = {
        "award_information": """
        Award Information
        
        This program provides awards of up to $500,000 for projects lasting 36 months.
        The submission deadline is March 15, 2024.
        Award Title: Advanced Research in Computational Sciences
        """,
        
        "eligibility_information": """
        Eligibility Information
        
        Principal Investigators must be U.S. citizens or permanent residents.
        Only accredited universities in the United States are eligible to apply.
        Teams may include up to 5 researchers with a maximum of 2 PIs.
        """,
        
        "program_description": """
        Program Description
        
        This program requires expertise in machine learning, data analysis, and statistical modeling.
        Preferred skills include Python programming, deep learning frameworks, and cloud computing.
        Technical requirements include access to high-performance computing resources.
        """
    }
    
    print("\n🔍 Testing metadata extraction from sample sections...")
    print("-" * 60)
    
    try:
        # Test individual section extraction
        for section_type in ["metadata", "rules", "skills"]:
            section_name = list(test_sections.keys())[0] if section_type == "metadata" else \
                          list(test_sections.keys())[1] if section_type == "rules" else \
                          list(test_sections.keys())[2]
            
            section_text = test_sections[section_name]
            
            print(f"\n📝 Testing {section_type} extraction from {section_name}...")
            
            result = extractor._extract_metadata_with_llm(section_text, section_type)
            
            if result:
                print(f"✅ {section_type.title()} extraction successful:")
                print(json.dumps(result, indent=2))
            else:
                print(f"⚠️ {section_type.title()} extraction returned empty result")
        
        # Test comprehensive extraction
        print(f"\n🔄 Testing comprehensive metadata extraction...")
        
        all_metadata = extractor.extract_all_metadata(test_sections)
        
        print("✅ Comprehensive extraction completed!")
        print("\n📊 Extraction Summary:")
        summary = all_metadata.get("extraction_summary", {})
        print(f"  • Sections processed: {summary.get('sections_processed', 0)}")
        print(f"  • Successful extractions: {summary.get('successful_extractions', 0)}")
        print(f"  • Failed extractions: {summary.get('failed_extractions', 0)}")
        
        print("\n📋 Extracted Metadata:")
        metadata = all_metadata.get("metadata", {})
        if metadata:
            print(f"  • Award Title: {metadata.get('award_title', 'N/A')}")
            print(f"  • Funding Ceiling: ${metadata.get('funding_ceiling', 0):,}")
            print(f"  • Duration: {metadata.get('project_duration_months', 0)} months")
            print(f"  • Deadline: {metadata.get('submission_deadline', 'N/A')}")
        
        print("\n📜 Extracted Rules:")
        rules = all_metadata.get("rules", {})
        pi_rules = rules.get("pi_eligibility_rules", [])
        if pi_rules:
            for i, rule in enumerate(pi_rules[:3], 1):
                print(f"  {i}. {rule}")
        
        constraints = rules.get("team_size_constraints", {})
        if constraints:
            print(f"  • Team constraints: {constraints}")
        
        print("\n🎯 Extracted Skills:")
        skills = all_metadata.get("skills", {})
        required_skills = skills.get("required_scientific_skills", [])
        if required_skills:
            print(f"  • Required: {', '.join(required_skills[:5])}")
        
        preferred_skills = skills.get("preferred_skills", [])
        if preferred_skills:
            print(f"  • Preferred: {', '.join(preferred_skills[:5])}")
        
        tech_requirements = skills.get("technical_requirements", [])
        if tech_requirements:
            print(f"  • Technical: {', '.join(tech_requirements[:3])}")
        
        print("\n🎉 LLM integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🛡️ Testing Error Handling Scenarios")
    print("=" * 60)
    
    # Test with invalid API key
    print("Testing with invalid API key...")
    try:
        extractor = LLMMetadataExtractor(api_key="invalid_key")
        result = extractor._extract_metadata_with_llm("test text", "metadata")
        print(f"✅ Graceful handling of invalid API key: {result == {}}")
    except Exception as e:
        print(f"⚠️ Exception with invalid API key: {e}")
    
    # Test with no API key
    print("Testing with no API key...")
    try:
        extractor = LLMMetadataExtractor(api_key=None)
        result = extractor._extract_metadata_with_llm("test text", "metadata")
        print(f"✅ Graceful handling of no API key: {result == {}}")
    except Exception as e:
        print(f"⚠️ Exception with no API key: {e}")

if __name__ == "__main__":
    print("🚀 Starting LLM Integration Manual Test")
    print("=" * 60)
    
    # Test with real API
    success = test_llm_with_real_api()
    
    # Test error handling
    test_error_handling()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ LLM integration is working correctly with Groq API")
    else:
        print("⚠️ Some tests failed - check the output above")
        print("💡 Make sure GROQ_API_KEY is set and valid")
    
    print("=" * 60)