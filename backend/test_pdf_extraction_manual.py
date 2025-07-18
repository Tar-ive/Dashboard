#!/usr/bin/env python3
"""Manual test for PDF text extraction."""

from app.services.pdf_processor import extract_pdf_text
import os

def test_extraction():
    """Test PDF extraction with the NSF file."""
    pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("Testing PDF text extraction...")
    result = extract_pdf_text(pdf_path)
    
    print(f"✅ Extraction completed!")
    print(f"📄 Pages: {result['page_count']}")
    print(f"📏 Text length: {len(result['text'])} characters")
    print(f"⏱️ Extraction time: {result['extraction_time']:.2f} seconds")
    print(f"💾 File size: {result['file_size']} bytes")
    
    # Show first 500 characters of extracted text
    print(f"\n📝 First 500 characters of extracted text:")
    print("-" * 50)
    print(result['text'][:500])
    print("-" * 50)
    
    # Check for key terms
    text_lower = result['text'].lower()
    key_terms = ['nsf', 'mathematical foundations', 'artificial intelligence', 'mfai']
    found_terms = [term for term in key_terms if term in text_lower]
    
    print(f"\n🔍 Key terms found: {found_terms}")
    
    if len(found_terms) >= 2:
        print("✅ Text extraction appears successful - key terms found!")
    else:
        print("⚠️ Warning: Expected key terms not found in extracted text")

if __name__ == "__main__":
    test_extraction()