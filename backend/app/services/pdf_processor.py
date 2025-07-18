"""PDF text extraction service using PyMuPDF."""

import time
import os
import re
from typing import Dict, Any, List
import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_pdf_text(file_path: str) -> Dict[str, Any]:
    """
    Extract text from a PDF file using PyMuPDF.
    
    This is a pure function that takes a file path and returns extracted text
    and metadata without any side effects.
    
    Args:
        file_path: Path to the PDF file to extract text from
        
    Returns:
        Dictionary containing:
        - text: Extracted text content
        - page_count: Number of pages in the PDF
        - extraction_time: Time taken for extraction in seconds
        - file_size: Size of the PDF file in bytes
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: If PDF is corrupted or cannot be processed
    """
    start_time = time.time()
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    try:
        # Open the PDF document
        doc = fitz.open(file_path)
        
        # Extract text from all pages
        text_content = ""
        page_count = len(doc)
        
        for page_num in range(page_count):
            page = doc[page_num]
            page_text = page.get_text()
            text_content += page_text + "\n"
        
        # Close the document
        doc.close()
        
        # Calculate extraction time
        extraction_time = time.time() - start_time
        
        logger.info(f"Extracted text from PDF: {file_path} ({page_count} pages, {len(text_content)} chars)")
        
        return {
            "text": text_content.strip(),
            "page_count": page_count,
            "extraction_time": extraction_time,
            "file_size": file_size
        }
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path}: {str(e)}")
        raise Exception(f"Failed to process PDF document: {str(e)}")

def chunk_by_sections(text: str) -> Dict[str, Any]:
    """
    Chunk text by searching for key section headers commonly found in NSF solicitations.
    
    This is a pure function that takes text and returns structured sections
    without any side effects.
    
    Args:
        text: The text content to chunk into sections
        
    Returns:
        Dictionary containing:
        - sections: Dict mapping section names to their content
        - section_count: Number of sections found
        
    """
    if not text or not text.strip():
        return {
            "sections": {},
            "section_count": 0
        }
    
    # Define section headers to look for (case-insensitive)
    section_patterns = {
        "program_description": [
            r"program\s+description",
            r"program\s+overview",
            r"program\s+summary"
        ],
        "award_information": [
            r"award\s+information",
            r"award\s+info",
            r"funding\s+information",
            r"award\s+details"
        ],
        "eligibility_information": [
            r"eligibility\s+information",
            r"eligibility\s+requirements",
            r"eligible\s+applicants",
            r"who\s+may\s+apply"
        ],
        "proposal_preparation_instructions": [
            r"proposal\s+preparation\s+instructions",
            r"proposal\s+instructions",
            r"application\s+instructions",
            r"submission\s+instructions"
        ],
        "proposal_submission_information": [
            r"proposal\s+submission\s+information",
            r"submission\s+information",
            r"how\s+to\s+submit"
        ],
        "review_information": [
            r"review\s+information",
            r"review\s+process",
            r"evaluation\s+criteria"
        ],
        "contacts": [
            r"contacts?",
            r"contact\s+information",
            r"program\s+contacts?"
        ]
    }
    
    # Find all section headers in the text
    sections = {}
    section_positions = []
    
    for section_name, patterns in section_patterns.items():
        for pattern in patterns:
            # Look for the pattern as a header (beginning of line or after whitespace)
            regex = rf"(?:^|\n)\s*({pattern})\s*(?:\n|$)"
            matches = list(re.finditer(regex, text, re.IGNORECASE | re.MULTILINE))
            
            if matches:
                # Take the first match for this section type
                match = matches[0]
                section_positions.append({
                    "name": section_name,
                    "start": match.end(),
                    "header_start": match.start(),
                    "header_text": match.group(1)
                })
                break  # Found this section, move to next
    
    # Sort sections by their position in the text
    section_positions.sort(key=lambda x: x["start"])
    
    # Extract content for each section
    for i, section in enumerate(section_positions):
        start_pos = section["start"]
        
        # Find the end position (start of next section or end of text)
        if i + 1 < len(section_positions):
            end_pos = section_positions[i + 1]["header_start"]
        else:
            end_pos = len(text)
        
        # Extract and clean the section content
        content = text[start_pos:end_pos].strip()
        
        # Remove excessive whitespace and normalize
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple newlines to double
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces/tabs to single space
        
        if content:  # Only add non-empty sections
            sections[section["name"]] = content
    
    logger.info(f"Chunked text into {len(sections)} sections: {list(sections.keys())}")
    
    return {
        "sections": sections,
        "section_count": len(sections)
    }