#!/usr/bin/env python3
"""Manual test for section chunking with the NSF PDF file."""

from app.services.pdf_processor import extract_pdf_text, chunk_by_sections
import os

def test_section_chunking():
    """Test section chunking with the actual NSF PDF file."""
    pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("Testing section chunking with NSF PDF file...")
    
    # First extract text
    print("1. Extracting text from PDF...")
    extraction_result = extract_pdf_text(pdf_path)
    text = extraction_result["text"]
    print(f"   ✅ Extracted {len(text)} characters from {extraction_result['page_count']} pages")
    
    # Then chunk by sections
    print("2. Chunking text by sections...")
    chunking_result = chunk_by_sections(text)
    
    sections = chunking_result["sections"]
    section_count = chunking_result["section_count"]
    
    print(f"   ✅ Found {section_count} sections")
    
    # Display found sections
    print("\n📋 Sections found:")
    print("-" * 60)
    
    for section_name, content in sections.items():
        print(f"\n🔹 {section_name.upper().replace('_', ' ')}")
        print(f"   Length: {len(content)} characters")
        
        # Show first 200 characters of each section
        preview = content[:200].replace('\n', ' ').strip()
        if len(content) > 200:
            preview += "..."
        print(f"   Preview: {preview}")
    
    # Test specific sections we expect in NSF documents
    expected_sections = [
        "program_description",
        "award_information", 
        "eligibility_information",
        "proposal_preparation_instructions"
    ]
    
    print(f"\n🔍 Checking for expected NSF sections:")
    found_expected = []
    for expected in expected_sections:
        if expected in sections:
            found_expected.append(expected)
            print(f"   ✅ {expected.replace('_', ' ').title()}")
        else:
            print(f"   ❌ {expected.replace('_', ' ').title()} (not found)")
    
    # Analyze content quality
    print(f"\n📊 Content Analysis:")
    total_content_length = sum(len(content) for content in sections.values())
    print(f"   Total sectioned content: {total_content_length} characters")
    print(f"   Coverage: {(total_content_length / len(text) * 100):.1f}% of original text")
    
    # Look for key NSF terms in sections
    key_terms = ["NSF", "award", "proposal", "eligibility", "funding", "research"]
    print(f"\n🔎 Key term analysis:")
    
    for section_name, content in sections.items():
        content_lower = content.lower()
        found_terms = [term for term in key_terms if term.lower() in content_lower]
        if found_terms:
            print(f"   {section_name}: {', '.join(found_terms)}")
    
    # Success criteria
    success = (
        section_count >= 2 and  # At least 2 sections found
        len(found_expected) >= 1 and  # At least 1 expected section found
        total_content_length > 1000  # Substantial content extracted
    )
    
    print(f"\n{'🎉' if success else '⚠️'} Test {'PASSED' if success else 'NEEDS REVIEW'}")
    
    if success:
        print("   Section chunking is working correctly with the NSF document!")
    else:
        print("   Section chunking may need adjustment for better NSF document parsing.")
    
    return success

if __name__ == "__main__":
    test_section_chunking()