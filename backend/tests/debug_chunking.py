#!/usr/bin/env python3
"""Debug the chunking issue."""

from app.services.pdf_processor import chunk_by_sections

def debug_multiple_headers():
    """Debug the multiple headers issue."""
    
    multiple_text = """
    Award Information
    First award section.
    
    Some other content here.
    
    Award Info
    Second award section (should be ignored).
    
    Eligibility Information
    Eligibility content.
    """
    
    result = chunk_by_sections(multiple_text)
    sections = result["sections"]
    
    print("Sections found:")
    for name, content in sections.items():
        print(f"\n{name}:")
        print(f"Content: {repr(content[:100])}")
    
    award_content = sections.get("award_information", "")
    print(f"\nAward content contains 'First': {'First award section' in award_content}")
    print(f"Award content contains 'Second': {'Second award section' in award_content}")

if __name__ == "__main__":
    debug_multiple_headers()