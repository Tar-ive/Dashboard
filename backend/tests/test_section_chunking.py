"""Tests for section chunking functionality."""

import pytest
from app.services.pdf_processor import chunk_by_sections

class TestSectionChunking:
    """Test cases for section chunking logic."""
    
    def test_chunk_by_sections_with_standard_headers(self):
        """Test chunking with standard NSF section headers."""
        text = """
        NSF 24-569: Mathematical Foundations of Artificial Intelligence
        
        Program Description
        This program supports research in mathematical foundations.
        
        Award Information
        Awards will be made for up to $500,000 over 3 years.
        Maximum award amount is $500,000.
        
        Eligibility Information
        Eligible applicants include universities and colleges.
        Principal investigators must be affiliated with eligible institutions.
        
        Proposal Preparation Instructions
        Proposals must follow NSF guidelines.
        Submit through FastLane or Research.gov.
        
        Additional Information
        Contact program officers for questions.
        """
        
        result = chunk_by_sections(text)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "sections" in result
        assert "section_count" in result
        
        sections = result["sections"]
        
        # Should find key sections
        assert "award_information" in sections
        assert "eligibility_information" in sections
        assert "program_description" in sections
        
        # Verify content is properly extracted
        award_section = sections["award_information"]
        assert "Awards will be made" in award_section
        assert "$500,000" in award_section
        
        eligibility_section = sections["eligibility_information"]
        assert "universities and colleges" in eligibility_section
        assert "Principal investigators" in eligibility_section
    
    def test_chunk_by_sections_with_case_variations(self):
        """Test chunking with different case variations of headers."""
        text = """
        AWARD INFORMATION
        Maximum award is $1,000,000.
        
        eligibility information
        Open to all institutions.
        
        Proposal Preparation Instructions
        Follow standard guidelines.
        """
        
        result = chunk_by_sections(text)
        sections = result["sections"]
        
        # Should handle case variations
        assert "award_information" in sections
        assert "eligibility_information" in sections
        assert "proposal_preparation_instructions" in sections
        
        assert "$1,000,000" in sections["award_information"]
        assert "all institutions" in sections["eligibility_information"]
    
    def test_chunk_by_sections_with_missing_sections(self):
        """Test chunking when some expected sections are missing."""
        text = """
        Program Overview
        This is a research program.
        
        Award Information
        Awards up to $200,000.
        
        Contact Information
        Email: program@nsf.gov
        """
        
        result = chunk_by_sections(text)
        sections = result["sections"]
        
        # Should find available sections
        assert "award_information" in sections
        assert "$200,000" in sections["award_information"]
        
        # Missing sections should not be present
        assert "eligibility_information" not in sections
        assert "proposal_preparation_instructions" not in sections
        
        # Should have reasonable section count
        assert result["section_count"] >= 1
    
    def test_chunk_by_sections_with_malformed_headers(self):
        """Test chunking with malformed or partial headers."""
        text = """
        Award Info
        Some award information here.
        
        Eligibility Requirements
        Requirements for eligibility.
        
        Proposal Instructions
        How to submit proposals.
        """
        
        result = chunk_by_sections(text)
        sections = result["sections"]
        
        # Should handle partial matches or create generic sections
        # The function should be robust to variations
        assert isinstance(sections, dict)
        assert result["section_count"] >= 0
    
    def test_chunk_by_sections_with_real_nsf_text(self):
        """Test chunking with actual NSF document text."""
        # This would use the extracted text from the NSF PDF
        from app.services.pdf_processor import extract_pdf_text
        import os
        
        pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
        
        if not os.path.exists(pdf_path):
            pytest.skip(f"NSF PDF file not found at {pdf_path}")
        
        # Extract text first
        extraction_result = extract_pdf_text(pdf_path)
        text = extraction_result["text"]
        
        # Chunk the text
        result = chunk_by_sections(text)
        
        # Verify structure
        assert isinstance(result, dict)
        assert "sections" in result
        assert "section_count" in result
        
        sections = result["sections"]
        
        # Should find at least some key sections in a real NSF document
        expected_sections = [
            "award_information",
            "eligibility_information", 
            "program_description"
        ]
        
        found_sections = [sec for sec in expected_sections if sec in sections]
        assert len(found_sections) >= 1, f"Expected to find at least one section from {expected_sections}, but found: {list(sections.keys())}"
        
        # Verify sections have substantial content
        for section_name, content in sections.items():
            assert len(content.strip()) > 10, f"Section {section_name} should have substantial content"
    
    def test_chunk_by_sections_with_empty_text(self):
        """Test chunking with empty or minimal text."""
        result = chunk_by_sections("")
        
        assert isinstance(result, dict)
        assert "sections" in result
        assert "section_count" in result
        assert result["section_count"] == 0
        assert len(result["sections"]) == 0
    
    def test_chunk_by_sections_with_no_headers(self):
        """Test chunking with text that has no recognizable headers."""
        text = """
        This is just a paragraph of text without any section headers.
        It continues for several sentences and doesn't have any
        of the expected NSF section headers like Award Information
        or Eligibility Information as headers.
        """
        
        result = chunk_by_sections(text)
        
        assert isinstance(result, dict)
        assert "sections" in result
        assert "section_count" in result
        
        # Should handle gracefully - might create a general section or return empty
        assert result["section_count"] >= 0
    
    def test_chunk_by_sections_is_pure_function(self):
        """Test that the function is pure (no side effects, deterministic)."""
        text = """
        Award Information
        Test award information.
        
        Eligibility Information
        Test eligibility information.
        """
        
        # Call function multiple times
        result1 = chunk_by_sections(text)
        result2 = chunk_by_sections(text)
        
        # Results should be identical
        assert result1 == result2
        assert result1["sections"] == result2["sections"]
        assert result1["section_count"] == result2["section_count"]
    
    def test_chunk_by_sections_handles_unicode_and_special_chars(self):
        """Test chunking with unicode characters and special formatting."""
        text = """
        Award Information
        Awards: $500,000–$1,000,000 (em dash)
        Funding: €100,000 (euro symbol)
        
        Eligibility Information  
        Applicants must be "qualified" researchers.
        Requirements include: α, β, γ (Greek letters)
        """
        
        result = chunk_by_sections(text)
        sections = result["sections"]
        
        # Should handle special characters properly
        assert "award_information" in sections
        assert "eligibility_information" in sections
        
        # Content should preserve special characters
        award_content = sections["award_information"]
        assert "–" in award_content or "500,000" in award_content
        assert "€" in award_content or "100,000" in award_content