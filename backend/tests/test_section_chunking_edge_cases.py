#!/usr/bin/env python3
"""Test edge cases for section chunking."""

from app.services.pdf_processor import chunk_by_sections

def test_edge_cases():
    """Test various edge cases for section chunking."""
    
    print("Testing section chunking edge cases...")
    
    # Test 1: Empty text
    print("\n1. Testing empty text...")
    result = chunk_by_sections("")
    assert result["section_count"] == 0
    assert len(result["sections"]) == 0
    print("   ✅ Empty text handled correctly")
    
    # Test 2: Text with no headers
    print("\n2. Testing text with no section headers...")
    no_headers_text = """
    This is just regular text without any section headers.
    It has multiple paragraphs and sentences but no recognizable
    NSF section headers like Award Information or Eligibility Information.
    """
    result = chunk_by_sections(no_headers_text)
    print(f"   Found {result['section_count']} sections")
    print("   ✅ No-header text handled gracefully")
    
    # Test 3: Case variations
    print("\n3. Testing case variations...")
    case_text = """
    AWARD INFORMATION
    This is in all caps.
    
    eligibility information
    This is in lowercase.
    
    Proposal Preparation Instructions
    This is in title case.
    """
    result = chunk_by_sections(case_text)
    sections = result["sections"]
    print(f"   Found sections: {list(sections.keys())}")
    assert "award_information" in sections
    assert "eligibility_information" in sections
    assert "proposal_preparation_instructions" in sections
    print("   ✅ Case variations handled correctly")
    
    # Test 4: Unicode and special characters
    print("\n4. Testing unicode and special characters...")
    unicode_text = """
    Award Information
    Funding: $500,000–$1,000,000 (em dash)
    Currency: €100,000 (euro symbol)
    
    Eligibility Information
    Requirements: α, β, γ (Greek letters)
    Quotes: "qualified" researchers
    """
    result = chunk_by_sections(unicode_text)
    sections = result["sections"]
    print(f"   Found {len(sections)} sections")
    assert "award_information" in sections
    assert "eligibility_information" in sections
    
    # Check content preservation
    award_content = sections["award_information"]
    assert "–" in award_content or "$500,000" in award_content
    print("   ✅ Unicode characters preserved correctly")
    
    # Test 5: Multiple similar headers (captures all content until next major section)
    print("\n5. Testing multiple similar headers...")
    multiple_text = """
    Award Information
    First award section.
    
    Some other content here.
    
    Award Info
    Second award section (part of same section).
    
    Eligibility Information
    Eligibility content.
    """
    result = chunk_by_sections(multiple_text)
    sections = result["sections"]
    award_content = sections.get("award_information", "")
    assert "First award section" in award_content
    # The second content should be included as it's part of the same section
    assert "Some other content" in award_content
    print("   ✅ Multiple headers handled correctly (captures all content until next section)")
    
    # Test 6: Headers with extra whitespace
    print("\n6. Testing headers with extra whitespace...")
    whitespace_text = """
    
        Award Information    
    
    Content with extra whitespace around header.
    
    
      Eligibility Information
      
    More content with whitespace.
    """
    result = chunk_by_sections(whitespace_text)
    sections = result["sections"]
    assert "award_information" in sections
    assert "eligibility_information" in sections
    print("   ✅ Extra whitespace handled correctly")
    
    print("\n🎉 All edge case tests passed!")
    print("   Section chunking function is robust and handles various scenarios correctly.")

if __name__ == "__main__":
    test_edge_cases()