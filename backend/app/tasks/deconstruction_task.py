"""Deconstruction task for processing PDF solicitations into structured data."""

import time
import logging
from typing import Dict, Any
from datetime import datetime
from app.services.pdf_processor import extract_pdf_text, chunk_by_sections
from app.services.llm_metadata_extractor import LLMMetadataExtractor
from app.jobs.job_manager import get_job_manager
from app.models.structured_solicitation import StructuredSolicitation

logger = logging.getLogger(__name__)


def deconstruct_solicitation_task(job_id: str, file_path: str) -> StructuredSolicitation:
    """
    Transform PDF into structured solicitation object with comprehensive error handling
    
    Steps:
    1. Extract full text using PDF library (PyMuPDF)
    2. Chunk text by section headers ("Eligibility", "Award Information", etc.)
    3. Send each chunk to LLM for targeted extraction
    4. Assemble structured solicitation object
    5. Store result in Redis
    
    Args:
        job_id: Unique job identifier
        file_path: Path to the PDF file to process
        
    Returns:
        StructuredSolicitation object with extracted data
        
    Raises:
        Exception: If processing fails at any step
    """
    start_time = time.time()
    job_manager = get_job_manager()
    
    try:
        # Update job status to processing
        job_manager.update_job_status(job_id, "processing", progress=0)
        logger.info(f"Starting deconstruction task for job {job_id}")
        
        # Step 1: Extract PDF text with enhanced error handling
        logger.info(f"Extracting text from PDF: {file_path}")
        try:
            pdf_result = extract_pdf_text(file_path)
            full_text = pdf_result["text"]
            
            if not full_text or not full_text.strip():
                raise Exception("No text could be extracted from the PDF file")
                
            logger.info(f"Extracted {len(full_text)} characters from PDF ({pdf_result.get('page_count', 0)} pages)")
            
        except FileNotFoundError:
            raise Exception(f"PDF file not found: {file_path}")
        except Exception as e:
            if "No text could be extracted" in str(e):
                raise e
            raise Exception(f"PDF extraction failed: {str(e)}")
        
        job_manager.update_job_status(job_id, "processing", progress=25)
        
        # Step 2: Chunk text by sections with error handling
        logger.info("Chunking text by sections")
        try:
            chunking_result = chunk_by_sections(full_text)
            sections = chunking_result["sections"]
            
            if not sections:
                logger.warning("No sections found in PDF, using full text as single section")
                sections = {"full_document": full_text}
                
            logger.info(f"Found {len(sections)} sections: {list(sections.keys())}")
            
        except Exception as e:
            logger.error(f"Text chunking failed: {str(e)}")
            # Fallback to using full text as single section
            sections = {"full_document": full_text}
            logger.info("Using full document as single section due to chunking failure")
        
        job_manager.update_job_status(job_id, "processing", progress=40)
        
        # Step 3: Extract metadata using LLM with comprehensive error handling
        logger.info("Extracting metadata using LLM")
        extracted_metadata = None
        
        try:
            llm_extractor = LLMMetadataExtractor()
            
            if not llm_extractor.is_available():
                logger.warning("LLM service not available, using fallback extraction")
                extracted_metadata = _fallback_metadata_extraction(sections, full_text)
            else:
                logger.info("LLM service available, attempting extraction")
                extracted_metadata = llm_extractor.extract_all_metadata(sections)
                
                # Validate extraction results
                if not extracted_metadata or not any(extracted_metadata.get(key, {}) for key in ["metadata", "rules", "skills"]):
                    logger.warning("LLM extraction returned empty results, falling back to pattern-based extraction")
                    extracted_metadata = _fallback_metadata_extraction(sections, full_text)
                    
        except Exception as e:
            logger.error(f"LLM metadata extraction failed: {str(e)}")
            logger.info("Falling back to pattern-based extraction")
            extracted_metadata = _fallback_metadata_extraction(sections, full_text)
        
        # Ensure we have some metadata structure
        if not extracted_metadata:
            logger.warning("All metadata extraction methods failed, using minimal structure")
            extracted_metadata = {
                "metadata": {},
                "rules": {},
                "skills": {},
                "extraction_summary": {
                    "sections_processed": len(sections),
                    "successful_extractions": 0,
                    "failed_extractions": len(sections),
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        job_manager.update_job_status(job_id, "processing", progress=80)
        logger.info("Metadata extraction completed")
        
        # Step 4: Assemble structured solicitation object with validation
        logger.info("Assembling structured solicitation object")
        processing_time = time.time() - start_time
        
        try:
            structured_solicitation = _assemble_structured_solicitation(
                job_id=job_id,
                full_text=full_text,
                sections=sections,
                extracted_metadata=extracted_metadata,
                processing_time=processing_time
            )
            
            # Validate the assembled object
            if not structured_solicitation.solicitation_id:
                raise Exception("Failed to create valid structured solicitation object")
                
        except Exception as e:
            logger.error(f"Failed to assemble structured solicitation: {str(e)}")
            raise Exception(f"Assembly failed: {str(e)}")
        
        # Step 5: Store result and complete job
        try:
            result_dict = structured_solicitation.model_dump()
            job_manager.store_job_result(job_id, result_dict)
            job_manager.update_job_status(job_id, "completed", progress=100)
            
            logger.info(f"Deconstruction task completed for job {job_id} in {processing_time:.2f}s")
            logger.info(f"Extraction confidence: {structured_solicitation.extraction_confidence:.1f}%")
            
        except Exception as e:
            logger.error(f"Failed to store job result: {str(e)}")
            # Still return the result even if storage fails
            logger.warning("Returning result despite storage failure")
        
        return structured_solicitation
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Deconstruction failed: {str(e)}"
        
        logger.error(f"Deconstruction task failed for job {job_id} after {processing_time:.2f}s: {error_message}")
        
        try:
            job_manager.update_job_status(
                job_id, 
                "failed", 
                error_message=error_message
            )
        except Exception as storage_error:
            logger.error(f"Failed to update job status to failed: {storage_error}")
        
        raise Exception(error_message)


def _assemble_structured_solicitation(
    job_id: str,
    full_text: str,
    sections: Dict[str, str],
    extracted_metadata: Dict[str, Any],
    processing_time: float
) -> StructuredSolicitation:
    """Assemble the final structured solicitation object"""
    
    # Extract metadata fields
    metadata = extracted_metadata.get("metadata", {})
    rules = extracted_metadata.get("rules", {})
    skills = extracted_metadata.get("skills", {})
    
    # Calculate extraction confidence based on successful extractions
    extraction_summary = extracted_metadata.get("extraction_summary", {})
    total_sections = extraction_summary.get("sections_processed", 1)
    successful_extractions = extraction_summary.get("successful_extractions", 0)
    
    # Calculate confidence as percentage, but cap at 100%
    if total_sections > 0:
        extraction_confidence = min(100.0, (successful_extractions / total_sections) * 100)
    else:
        extraction_confidence = 0.0
    
    # Convert to 0-1 range for the model
    extraction_confidence_normalized = extraction_confidence / 100.0
    
    # Prepare data for the model
    solicitation_data = {
        "solicitation_id": job_id,
        "award_title": metadata.get("award_title", "Untitled Solicitation"),
        "full_text": full_text,
        "processing_time_seconds": processing_time,
        "extraction_confidence": extraction_confidence_normalized,
        "created_at": datetime.now()
    }
    
    # Add optional fields only if they have values
    if metadata.get("funding_ceiling"):
        solicitation_data["funding_ceiling"] = metadata.get("funding_ceiling")
    
    if metadata.get("project_duration_months"):
        solicitation_data["project_duration_months"] = metadata.get("project_duration_months")
    
    if metadata.get("submission_deadline"):
        # Try to parse the deadline string into a datetime object
        deadline_str = metadata.get("submission_deadline")
        try:
            # Try common date formats
            date_formats = [
                "%B %d, %Y",  # "March 15, 2025"
                "%b %d, %Y",  # "Mar 15, 2025"
                "%Y-%m-%d",   # "2025-03-15"
                "%m/%d/%Y",   # "03/15/2025"
                "%d/%m/%Y",   # "15/03/2025"
            ]
            
            parsed_deadline = None
            for fmt in date_formats:
                try:
                    parsed_deadline = datetime.strptime(deadline_str, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_deadline:
                solicitation_data["submission_deadline"] = parsed_deadline
            else:
                logger.warning(f"Could not parse submission deadline: {deadline_str}")
                
        except Exception as e:
            logger.warning(f"Error parsing submission deadline '{deadline_str}': {e}")
            pass
    
    # Add rules
    if rules.get("pi_eligibility_rules"):
        solicitation_data["pi_eligibility_rules"] = rules.get("pi_eligibility_rules", [])
    
    if rules.get("institutional_limitations"):
        solicitation_data["institutional_limitations"] = rules.get("institutional_limitations", [])
    
    if rules.get("team_size_constraints"):
        solicitation_data["team_size_constraints"] = rules.get("team_size_constraints")
    
    # Add skills
    if skills.get("required_scientific_skills"):
        solicitation_data["required_scientific_skills"] = skills.get("required_scientific_skills", [])
    
    if skills.get("preferred_skills"):
        solicitation_data["preferred_skills"] = skills.get("preferred_skills", [])
    
    # Note: technical_requirements not supported by current model
    
    # Add sections
    if sections:
        solicitation_data["extracted_sections"] = sections
    
    return StructuredSolicitation(**solicitation_data)


def _fallback_metadata_extraction(sections: Dict[str, str], full_text: str) -> Dict[str, Any]:
    """
    Enhanced fallback metadata extraction when LLM is not available
    Uses comprehensive text processing and pattern matching
    """
    logger.info("Using enhanced fallback metadata extraction")
    
    metadata = {}
    rules = {}
    skills = {}
    successful_extractions = 0
    
    import re
    
    # Enhanced funding amount extraction
    funding_patterns = [
        r'\$([0-9,]+(?:\.[0-9]{2})?)\s*(?:million|M)?',
        r'([0-9,]+)\s*dollars?',
        r'up\s+to\s+\$?([0-9,]+(?:\.[0-9]{2})?)',
        r'awards?\s+of\s+up\s+to\s+\$?([0-9,]+)',
        r'maximum\s+(?:of\s+)?\$?([0-9,]+)',
        r'ceiling\s+of\s+\$?([0-9,]+)'
    ]
    
    max_funding = 0
    for pattern in funding_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            try:
                for match in matches:
                    amount_str = match.replace(',', '')
                    amount = float(amount_str)
                    # Handle millions
                    if 'million' in full_text.lower() and amount < 1000:
                        amount *= 1000000
                    max_funding = max(max_funding, amount)
            except ValueError:
                continue
    
    if max_funding > 0:
        metadata["funding_ceiling"] = max_funding
        successful_extractions += 1
    
    # Enhanced project duration extraction
    duration_patterns = [
        r'([0-9]+)\s*years?\s*\(([0-9]+)\s*months?\)',  # "3 years (36 months)"
        r'([0-9]+)\s*years?',
        r'([0-9]+)\s*months?',
        r'duration[:\s]+([0-9]+)\s*(?:years?|months?)',
        r'project\s+period[:\s]+([0-9]+)'
    ]
    
    for pattern in duration_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            try:
                if isinstance(matches[0], tuple):
                    # Handle "3 years (36 months)" format
                    duration = int(matches[0][1])  # Use months value
                else:
                    duration = int(matches[0])
                    # Convert years to months if pattern contains 'year'
                    if 'year' in pattern.lower():
                        duration *= 12
                metadata["project_duration_months"] = duration
                successful_extractions += 1
                break
            except (ValueError, IndexError):
                continue
    
    # Extract award title from common patterns
    title_patterns = [
        r'NSF\s+[0-9-]+[:\s]+([^.\n]+)',
        r'Program[:\s]+([^.\n]+)',
        r'Award[:\s]+([^.\n]+)',
        r'^([A-Z][^.\n]+(?:Program|Initiative|Award))',
    ]
    
    for pattern in title_patterns:
        matches = re.findall(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        if matches:
            title = matches[0].strip()
            if len(title) > 10 and len(title) < 200:  # Reasonable title length
                metadata["award_title"] = title
                successful_extractions += 1
                break
    
    # Extract submission deadline
    deadline_patterns = [
        r'deadline[:\s]+([A-Za-z]+ [0-9]+, [0-9]{4})',
        r'due[:\s]+([A-Za-z]+ [0-9]+, [0-9]{4})',
        r'submit(?:ted)?\s+by[:\s]+([A-Za-z]+ [0-9]+, [0-9]{4})',
        r'([A-Za-z]+ [0-9]+, [0-9]{4})\s+deadline'
    ]
    
    for pattern in deadline_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            metadata["submission_deadline"] = matches[0].strip()
            successful_extractions += 1
            break
    
    # Enhanced eligibility rules extraction
    eligibility_keywords = [
        "U.S. citizens", "permanent residents", "nationals",
        "Principal Investigators must", "Co-Principal Investigators",
        "eligible institutions", "degree-granting"
    ]
    
    pi_rules = []
    institutional_rules = []
    
    for keyword in eligibility_keywords:
        pattern = rf'[^.\n]*{re.escape(keyword)}[^.\n]*'
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for match in matches:
            clean_match = match.strip()
            if len(clean_match) > 20:  # Meaningful rule
                if "Principal Investigator" in clean_match or "PI" in clean_match:
                    pi_rules.append(clean_match)
                elif "institution" in clean_match.lower():
                    institutional_rules.append(clean_match)
    
    if pi_rules:
        rules["pi_eligibility_rules"] = list(set(pi_rules))  # Remove duplicates
        successful_extractions += 1
    
    if institutional_rules:
        rules["institutional_limitations"] = list(set(institutional_rules))
        successful_extractions += 1
    
    # Extract team size constraints
    team_size_patterns = [
        r'maximum\s+of\s+([0-9]+)\s+(?:Principal\s+)?Investigators?',
        r'up\s+to\s+([0-9]+)\s+(?:total\s+)?researchers?',
        r'teams?\s+(?:may\s+)?include\s+up\s+to\s+([0-9]+)',
        r'([0-9]+)\s+(?:Principal\s+)?Investigators?\s+per\s+proposal'
    ]
    
    team_constraints = {}
    for pattern in team_size_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            try:
                size = int(matches[0])
                if "Principal Investigator" in pattern or "PI" in pattern:
                    team_constraints["max_pi"] = size
                elif "total" in pattern or "researchers" in pattern:
                    team_constraints["max_team_size"] = size
            except ValueError:
                continue
    
    if team_constraints:
        rules["team_size_constraints"] = team_constraints
        successful_extractions += 1
    
    # Enhanced skills extraction with categorization
    required_skill_keywords = [
        "required expertise", "must have", "essential skills",
        "advanced mathematics", "theoretical computer science", "machine learning theory",
        "high-performance computing", "parallel algorithms", "numerical methods"
    ]
    
    preferred_skill_keywords = [
        "preferred qualifications", "desired experience", "advantageous",
        "optimization theory", "statistical learning", "deep learning",
        "artificial intelligence", "data analytics", "computational complexity"
    ]
    
    technical_requirement_keywords = [
        "technical requirements", "access to", "proficiency in",
        "supercomputing facilities", "programming languages", "software",
        "Python", "MATLAB", "C++", "R programming", "Fortran"
    ]
    
    def extract_skills_by_category(keywords, text):
        found_skills = []
        for keyword in keywords:
            if keyword.lower() in text.lower():
                found_skills.append(keyword)
        return found_skills
    
    required_skills = extract_skills_by_category(required_skill_keywords, full_text)
    preferred_skills = extract_skills_by_category(preferred_skill_keywords, full_text)
    technical_reqs = extract_skills_by_category(technical_requirement_keywords, full_text)
    
    if required_skills:
        skills["required_scientific_skills"] = required_skills[:8]
        successful_extractions += 1
    
    if preferred_skills:
        skills["preferred_skills"] = preferred_skills[:8]
        successful_extractions += 1
    
    if technical_reqs:
        skills["technical_requirements"] = technical_reqs[:6]
        successful_extractions += 1
    
    logger.info(f"Fallback extraction completed: {successful_extractions} successful extractions")
    
    return {
        "metadata": metadata,
        "rules": rules,
        "skills": skills,
        "extraction_summary": {
            "sections_processed": len(sections),
            "successful_extractions": successful_extractions,
            "failed_extractions": max(0, len(sections) - successful_extractions),
            "timestamp": datetime.now().isoformat(),
            "extraction_method": "fallback_pattern_matching"
        }
    }


# Helper functions for pure function testing
def _extract_pdf_text(file_path: str) -> str:
    """Pure function for PDF text extraction"""
    result = extract_pdf_text(file_path)
    return result["text"]


def _chunk_by_sections(text: str) -> Dict[str, str]:
    """Pure function for section identification"""
    result = chunk_by_sections(text)
    return result["sections"]


def _extract_metadata_with_llm(section_text: str, section_type: str) -> Dict[str, Any]:
    """LLM-powered data extraction"""
    extractor = LLMMetadataExtractor()
    return extractor._extract_metadata_with_llm(section_text, section_type)