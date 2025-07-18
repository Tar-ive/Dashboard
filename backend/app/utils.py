import fitz  # PyMuPDF
import re
import time
from typing import Dict, Tuple
from pathlib import Path

def extract_pdf_text(file_path: str) -> Dict:
    """Extract text from PDF and perform basic analysis"""
    start_time = time.time()
    
    try:
        # Extract text
        text, title, abstract = _extract_text_from_pdf(file_path)
        
        # Basic analysis
        sections = _detect_sections(text)
        
        processing_time = time.time() - start_time
        
        return {
            "title": title,
            "abstract": abstract,
            "full_text": text,
            "text_length": len(text),
            "sections_found": sections,
            "processing_time": round(processing_time, 2)
        }
    
    except Exception as e:
        raise Exception(f"PDF processing failed: {str(e)}")

def _extract_text_from_pdf(file_path: str) -> Tuple[str, str, str]:
    """Extract text, title, and abstract from PDF"""
    doc = None
    try:
        doc = fitz.open(file_path)
        full_text = ""
        
        # Extract text from all pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            full_text += f"\n--- PAGE {page_num + 1} ---\n{text}\n"
        
        # Extract title and abstract
        title, abstract = _extract_title_and_abstract(full_text, Path(file_path).name)
        
        return full_text, title, abstract
    
    except Exception as e:
        raise Exception(f"Text extraction failed: {str(e)}")
    finally:
        if doc:
            doc.close()

def _extract_title_and_abstract(text: str, filename: str) -> Tuple[str, str]:
    """Extract title and abstract from text"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Default title from filename
    title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
    
    # Look for title in first 20 lines
    for i, line in enumerate(lines[:20]):
        if (30 < len(line) < 300 and
            not line.isupper() and
            not re.match(r'^(Page|Section|\d+)', line, re.IGNORECASE) and
            not line.startswith('http')):
            title = line
            break
    
    # Extract abstract
    abstract = ""
    abstract_started = False
    abstract_markers = ['abstract', 'summary', 'overview', 'program description']
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Start abstract detection
        if not abstract_started:
            for marker in abstract_markers:
                if marker in line_lower and len(line) > len(marker) + 5:
                    abstract_started = True
                    # Extract text after marker
                    marker_pos = line_lower.find(marker)
                    remaining_text = line[marker_pos + len(marker):].strip()
                    if remaining_text and not remaining_text.startswith(':'):
                        abstract += remaining_text + " "
                    break
            continue
        
        # Continue abstract collection
        if abstract_started:
            # Stop conditions
            stop_conditions = [
                'table of contents', 'section i', 'section 1', 'introduction',
                'background', 'key dates', 'important dates'
            ]
            
            if any(stop in line_lower for stop in stop_conditions):
                break
            
            abstract += line + " "
            
            # Stop if abstract is getting too long
            if len(abstract) > 2000:
                break
    
    # Fallback for abstract
    if not abstract.strip():
        abstract = ' '.join(lines[1:6])  # Use first few lines
    
    return title.strip(), abstract.strip()[:1500]  # Limit abstract length

def _detect_sections(text: str) -> list:
    """Detect sections in the document"""
    sections_found = []
    
    section_patterns = {
        'Program Description': [
            r'Program\s+Description',
            r'Scientific\s+Objectives',
            r'Research\s+Areas'
        ],
        'Award Information': [
            r'Section\s+II[:\s]*Award\s+Information',
            r'Award\s+Information',
            r'Funding\s+Information'
        ],
        'Eligibility': [
            r'Section\s+III[:\s]*Eligibility',
            r'Eligibility\s+Requirements',
            r'Who\s+May\s+Apply'
        ],
        'Submission Requirements': [
            r'Section\s+V[:\s]*Proposal.*Submission',
            r'Application\s+Instructions',
            r'Submission\s+Instructions'
        ]
    }
    
    for section_name, patterns in section_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                sections_found.append(section_name)
                break
    
    return sections_found