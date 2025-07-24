#!/usr/bin/env python3
"""
Test script for the solicitation parser using the test PDF document.
"""

from modules.solicitation_parser import SolicitationParser
from modules.data_models import Solicitation

def test_pdf_parsing():
    """Test PDF parsing with the test document."""
    parser = SolicitationParser()
    
    # Test PDF text extraction
    print("Testing PDF text extraction...")
    try:
        text = parser.extract_text_from_pdf("data/test_solicitation.pdf")
        print(f"✅ Successfully extracted {len(text)} characters of text")
        print(f"First 500 characters:\n{text[:500]}...")
    except Exception as e:
        print(f"❌ Failed to extract text: {e}")
        return
    
    # Test full parsing
    print("\nTesting full PDF parsing...")
    try:
        result = parser.parse_pdf_solicitation("data/test_solicitation.pdf")
        print(f"✅ Parsing completed in {result.processing_time:.2f} seconds")
        print(f"Confidence score: {result.confidence_score:.2f}")
        print(f"Missing fields: {result.missing_fields}")
        
        print("\nExtracted data:")
        for field, value in result.extracted_data.items():
            if value:
                print(f"  {field}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            else:
                print(f"  {field}: [EMPTY]")
        
        # Test conversion to Solicitation object
        print("\nTesting conversion to Solicitation object...")
        solicitation = parser.convert_to_solicitation(result)
        print(f"✅ Successfully created Solicitation object")
        print(f"Title: {solicitation.title}")
        print(f"Abstract: {solicitation.abstract[:200]}{'...' if len(solicitation.abstract) > 200 else ''}")
        print(f"Required skills: {solicitation.required_skills_checklist[:5]}")  # First 5 skills
        print(f"Extraction confidence: {solicitation.extraction_confidence}")
        
    except Exception as e:
        print(f"❌ Failed to parse PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_parsing()