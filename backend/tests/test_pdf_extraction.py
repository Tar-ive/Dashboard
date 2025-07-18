"""Tests for PDF text extraction functionality."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
import fitz  # PyMuPDF

# Import the function we'll be testing
from app.services.pdf_processor import extract_pdf_text

class TestPDFTextExtraction:
    """Test cases for PDF text extraction."""
    
    def test_extract_pdf_text_with_valid_pdf(self):
        """Test PDF text extraction with a valid PDF file."""
        # Create a simple PDF with known content
        pdf_content = self._create_test_pdf_with_text("Test PDF Content\nThis is a test document.")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file.flush()
            
            try:
                result = extract_pdf_text(temp_file.name)
                
                # Verify the result structure
                assert isinstance(result, dict)
                assert "text" in result
                assert "page_count" in result
                assert "extraction_time" in result
                assert "file_size" in result
                
                # Verify content
                assert len(result["text"]) > 0
                assert result["page_count"] >= 1
                assert result["extraction_time"] >= 0
                assert result["file_size"] > 0
                
            finally:
                os.unlink(temp_file.name)
    
    def test_extract_pdf_text_with_real_nsf_pdf(self):
        """Test PDF text extraction with the actual NSF PDF file."""
        pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
        
        if not os.path.exists(pdf_path):
            pytest.skip(f"NSF PDF file not found at {pdf_path}")
        
        result = extract_pdf_text(pdf_path)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "text" in result
        assert "page_count" in result
        assert "extraction_time" in result
        assert "file_size" in result
        
        # Verify content for NSF document
        text = result["text"]
        assert len(text) > 1000  # Should be substantial content
        assert "NSF" in text or "National Science Foundation" in text
        assert "Mathematical Foundations" in text or "MFAI" in text
        assert result["page_count"] > 1  # Multi-page document
    
    def test_extract_pdf_text_handles_corrupted_pdf(self):
        """Test that function handles corrupted PDF files gracefully."""
        # Create a file that looks like PDF but is corrupted
        corrupted_content = b"%PDF-1.4\nThis is not a valid PDF content"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(corrupted_content)
            temp_file.flush()
            
            try:
                with pytest.raises(Exception) as exc_info:
                    extract_pdf_text(temp_file.name)
                
                # Should raise an exception for corrupted PDF
                assert "PDF" in str(exc_info.value) or "document" in str(exc_info.value).lower()
                
            finally:
                os.unlink(temp_file.name)
    
    def test_extract_pdf_text_handles_nonexistent_file(self):
        """Test that function handles non-existent files gracefully."""
        with pytest.raises(FileNotFoundError):
            extract_pdf_text("/path/that/does/not/exist.pdf")
    
    def test_extract_pdf_text_handles_empty_pdf(self):
        """Test extraction from PDF with no text content."""
        # Create a minimal PDF with no text
        pdf_content = self._create_minimal_empty_pdf()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file.flush()
            
            try:
                result = extract_pdf_text(temp_file.name)
                
                # Should still return valid structure
                assert isinstance(result, dict)
                assert "text" in result
                assert "page_count" in result
                assert result["page_count"] >= 1
                # Text might be empty or minimal
                assert isinstance(result["text"], str)
                
            finally:
                os.unlink(temp_file.name)
    
    def test_extract_pdf_text_performance_with_large_file(self):
        """Test that extraction completes within reasonable time."""
        pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
        
        if not os.path.exists(pdf_path):
            pytest.skip(f"NSF PDF file not found at {pdf_path}")
        
        result = extract_pdf_text(pdf_path)
        
        # Should complete within 10 seconds for typical documents
        assert result["extraction_time"] < 10.0
    
    def test_extract_pdf_text_is_pure_function(self):
        """Test that the function is pure (no side effects, deterministic)."""
        pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
        
        if not os.path.exists(pdf_path):
            pytest.skip(f"NSF PDF file not found at {pdf_path}")
        
        # Call the function multiple times
        result1 = extract_pdf_text(pdf_path)
        result2 = extract_pdf_text(pdf_path)
        
        # Results should be identical (deterministic)
        assert result1["text"] == result2["text"]
        assert result1["page_count"] == result2["page_count"]
        assert result1["file_size"] == result2["file_size"]
        # Extraction time may vary slightly, so we don't check that
    
    def _create_test_pdf_with_text(self, text_content: str) -> bytes:
        """Create a simple PDF with the given text content."""
        # Create a simple PDF using PyMuPDF
        doc = fitz.open()  # Create new PDF
        page = doc.new_page()  # Add a page
        
        # Insert text
        page.insert_text((72, 72), text_content, fontsize=12)
        
        # Get PDF bytes
        pdf_bytes = doc.tobytes()
        doc.close()
        
        return pdf_bytes
    
    def _create_minimal_empty_pdf(self) -> bytes:
        """Create a minimal PDF with no text content."""
        doc = fitz.open()  # Create new PDF
        doc.new_page()  # Add an empty page
        
        # Get PDF bytes
        pdf_bytes = doc.tobytes()
        doc.close()
        
        return pdf_bytes