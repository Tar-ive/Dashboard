#!/usr/bin/env python3
"""
Debug script to examine PDF text structure for pattern refinement.
"""

from modules.solicitation_parser import SolicitationParser

def debug_pdf_text():
    """Examine PDF text structure to improve extraction patterns."""
    parser = SolicitationParser()
    
    try:
        text = parser.extract_text_from_pdf("data/test_solicitation.pdf")
        
        # Show first 2000 characters to understand structure
        print("=== FIRST 2000 CHARACTERS ===")
        print(text[:2000])
        print("\n" + "="*50 + "\n")
        
        # Look for potential title patterns
        print("=== SEARCHING FOR TITLE PATTERNS ===")
        lines = text.split('\n')
        for i, line in enumerate(lines[:50]):  # First 50 lines
            if line.strip() and len(line.strip()) > 10:
                print(f"Line {i:2d}: {line.strip()}")
        
        print("\n" + "="*50 + "\n")
        
        # Look for sections that might contain abstract/description
        print("=== SEARCHING FOR SECTION HEADERS ===")
        import re
        section_patterns = [
            r'^[A-Z][A-Za-z\s]+:',  # Section headers ending with colon
            r'^[IVX]+\.\s+[A-Z]',   # Roman numeral sections
            r'^\d+\.\s+[A-Z]',      # Numbered sections
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                print(f"Pattern '{pattern}' found:")
                for match in matches[:10]:  # First 10 matches
                    print(f"  - {match}")
        
        print("\n" + "="*50 + "\n")
        
        # Look for NSF-specific patterns
        print("=== NSF-SPECIFIC PATTERNS ===")
        nsf_patterns = [
            r'NSF\s+\d{2}-\d{3}',
            r'Program Solicitation',
            r'Synopsis of Program',
            r'Program Description',
            r'Award Information',
            r'Eligibility Information'
        ]
        
        for pattern in nsf_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"Found '{pattern}': {matches}")
                # Show context around first match
                match_pos = text.lower().find(pattern.lower())
                if match_pos != -1:
                    context_start = max(0, match_pos - 100)
                    context_end = min(len(text), match_pos + 200)
                    context = text[context_start:context_end]
                    print(f"  Context: ...{context}...")
                    print()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdf_text()