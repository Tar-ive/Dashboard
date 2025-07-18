"""Data models for structured solicitation processing with rule-based extraction."""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

class ExtractionType(str, Enum):
    """Type of extraction to perform."""
    SINGLE = "single"
    MULTIPLE = "multiple"

class PostProcessType(str, Enum):
    """Post-processing functions available."""
    CLEAN_TEXT = "clean_text"
    EXTRACT_NUMBERS = "extract_numbers"
    EXTRACT_DATES = "extract_dates"
    MAX_LENGTH = "max_length"

class ExtractionRule(BaseModel):
    """Rule for extracting specific data from text using regex patterns."""
    
    name: str = Field(..., description="Name of the data field to create")
    pattern: str = Field(..., description="Regular expression pattern to match data")
    extraction_type: ExtractionType = Field(
        default=ExtractionType.SINGLE, 
        description="Whether to find single or multiple matches"
    )
    post_process: Optional[PostProcessType] = Field(
        None, 
        description="Post-processing function to apply"
    )
    max_length: Optional[int] = Field(
        None, 
        description="Maximum length for truncation (used with max_length post_process)"
    )
    
    @validator('pattern')
    def validate_pattern(cls, v):
        """Validate that the regex pattern is valid."""
        import re
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v

class TableExtractionRule(BaseModel):
    """Rule for extracting tabular data from text."""
    
    name: str = Field(..., description="Name of the table to extract")
    start_pattern: str = Field(..., description="Pattern marking start of table")
    end_pattern: Optional[str] = Field(None, description="Pattern marking end of table")
    row_separator: str = Field(default=r"\n", description="Pattern to split rows")
    column_patterns: List[str] = Field(..., description="List of regex patterns for each column")
    header_rows: int = Field(default=1, description="Number of header rows to skip")

class SectionConfig(BaseModel):
    """Configuration for identifying and processing document sections."""
    
    name: str = Field(..., description="Human-readable name for the section")
    start_pattern: str = Field(..., description="Regex pattern marking section start")
    end_pattern: Optional[str] = Field(None, description="Regex pattern marking section end")
    extraction_rules: List[ExtractionRule] = Field(
        default_factory=list, 
        description="Rules for extracting data from this section"
    )
    table_rules: List[TableExtractionRule] = Field(
        default_factory=list, 
        description="Rules for extracting tables from this section"
    )
    
    @validator('start_pattern', 'end_pattern')
    def validate_patterns(cls, v):
        """Validate that regex patterns are valid."""
        if v is not None:
            import re
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        return v

class ProcessingInfo(BaseModel):
    """Information about the processing of the solicitation."""
    
    extracted_at: datetime = Field(..., description="When extraction was performed")
    text_length: int = Field(..., description="Length of original text")
    page_count: int = Field(..., description="Number of pages in document")
    sections_found: int = Field(..., description="Number of sections identified")
    extraction_time: Optional[float] = Field(None, description="Time taken for extraction")
    rules_applied: Optional[int] = Field(None, description="Number of extraction rules applied")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")

class SolicitationSection(BaseModel):
    """A processed section of a solicitation with extracted data."""
    
    name: str = Field(..., description="Section name")
    raw_text: str = Field(..., description="Raw text content of the section")
    extracted_data: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Data extracted using rules"
    )
    tables: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict, 
        description="Extracted table data"
    )
    processing_notes: List[str] = Field(
        default_factory=list, 
        description="Notes about processing this section"
    )

class StructuredSolicitation(BaseModel):
    """Complete structured representation of a solicitation document."""
    
    # Required identification fields
    solicitation_id: str = Field(..., min_length=1, description="Unique identifier for the solicitation")
    title: str = Field(..., min_length=1, description="Title of the solicitation")
    
    # Optional metadata fields
    program_name: Optional[str] = Field(None, description="Name of the funding program")
    agency: Optional[str] = Field(None, description="Funding agency")
    solicitation_number: Optional[str] = Field(None, description="Official solicitation number")
    
    # Processed sections with extracted data
    sections: Dict[str, SolicitationSection] = Field(
        default_factory=dict, 
        description="Processed sections with extracted data"
    )
    
    # Legacy simple sections (for backward compatibility)
    simple_sections: Dict[str, str] = Field(
        default_factory=dict, 
        description="Simple text sections (legacy format)"
    )
    
    # Consolidated extracted metadata from all sections
    extracted_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="All extracted metadata consolidated"
    )
    
    # Processing information
    processing_info: Optional[ProcessingInfo] = Field(
        None, 
        description="Information about the extraction process"
    )
    
    # Configuration used for extraction
    extraction_config: Optional[Dict[str, SectionConfig]] = Field(
        None, 
        description="Configuration used for rule-based extraction"
    )
    
    @validator('solicitation_id', 'title')
    def validate_non_empty_strings(cls, v):
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    def get_section_data(self, section_name: str, field_name: str) -> Any:
        """Get extracted data from a specific section."""
        if section_name in self.sections:
            return self.sections[section_name].extracted_data.get(field_name)
        return None
    
    def get_all_extracted_data(self) -> Dict[str, Any]:
        """Get all extracted data from all sections combined."""
        all_data = {}
        for section_name, section in self.sections.items():
            for field_name, value in section.extracted_data.items():
                # Prefix with section name to avoid conflicts
                key = f"{section_name}_{field_name}"
                all_data[key] = value
        
        # Also include consolidated metadata
        all_data.update(self.extracted_metadata)
        return all_data
    
    def get_table_data(self, section_name: str, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get table data from a specific section."""
        if section_name in self.sections:
            return self.sections[section_name].tables.get(table_name)
        return None
    
    def add_processing_error(self, error_message: str) -> None:
        """Add an error message to processing info."""
        if self.processing_info is None:
            self.processing_info = ProcessingInfo(
                extracted_at=datetime.now(),
                text_length=0,
                page_count=0,
                sections_found=0
            )
        self.processing_info.errors.append(error_message)

# NSF-specific configuration for common solicitation patterns
NSF_SOLICITATION_CONFIG = {
    "basic_info": SectionConfig(
        name="basic_info",
        start_pattern=r"NSF \d{2}-\d{3}:",
        end_pattern=r"Program Description|PROGRAM DESCRIPTION",
        extraction_rules=[
            ExtractionRule(
                name="solicitation_number",
                pattern=r"NSF (\d{2}-\d{3}):",
                post_process=PostProcessType.CLEAN_TEXT
            ),
            ExtractionRule(
                name="program_title",
                pattern=r"NSF \d{2}-\d{3}:\s*([^\n]+)",
                post_process=PostProcessType.CLEAN_TEXT
            ),
            ExtractionRule(
                name="posted_date",
                pattern=r"Posted:\s*([^\n]+)",
                post_process=PostProcessType.EXTRACT_DATES
            )
        ]
    ),
    "program_description": SectionConfig(
        name="program_description",
        start_pattern=r"Program Description|PROGRAM DESCRIPTION",
        end_pattern=r"Award Information|AWARD INFORMATION",
        extraction_rules=[
            ExtractionRule(
                name="program_summary",
                pattern=r"Program Description\s*\n\s*([^§]+?)(?=\n\s*[A-Z][A-Z\s]+\n|\n\s*Award Information|$)",
                post_process=PostProcessType.CLEAN_TEXT,
                max_length=1000
            )
        ]
    ),
    "award_information": SectionConfig(
        name="award_information",
        start_pattern=r"Award Information|AWARD INFORMATION",
        end_pattern=r"Eligibility Information|ELIGIBILITY INFORMATION",
        extraction_rules=[
            ExtractionRule(
                name="anticipated_award_type",
                pattern=r"Anticipated Type of Award:\s*([^\n]+)",
                post_process=PostProcessType.CLEAN_TEXT
            ),
            ExtractionRule(
                name="estimated_number_of_awards",
                pattern=r"Estimated Number of Awards:\s*([^\n]+)",
                post_process=PostProcessType.EXTRACT_NUMBERS
            ),
            ExtractionRule(
                name="anticipated_funding_amount",
                pattern=r"Anticipated Funding Amount:\s*\$([0-9,]+)",
                post_process=PostProcessType.EXTRACT_NUMBERS
            ),
            ExtractionRule(
                name="award_ceiling",
                pattern=r"Award Ceiling:\s*\$([0-9,]+)",
                post_process=PostProcessType.EXTRACT_NUMBERS
            ),
            ExtractionRule(
                name="award_floor",
                pattern=r"Award Floor:\s*\$([0-9,]+)",
                post_process=PostProcessType.EXTRACT_NUMBERS
            )
        ]
    ),
    "eligibility_information": SectionConfig(
        name="eligibility_information",
        start_pattern=r"Eligibility Information|ELIGIBILITY INFORMATION",
        end_pattern=r"Proposal Preparation|PROPOSAL PREPARATION",
        extraction_rules=[
            ExtractionRule(
                name="who_may_submit",
                pattern=r"Who May Submit Proposals:\s*([^§]+?)(?=Who May Serve as PI|Limit on Number|$)",
                post_process=PostProcessType.CLEAN_TEXT,
                max_length=500
            ),
            ExtractionRule(
                name="who_may_serve_as_pi",
                pattern=r"Who May Serve as PI:\s*([^§]+?)(?=Limit on Number|$)",
                post_process=PostProcessType.CLEAN_TEXT,
                max_length=500
            ),
            ExtractionRule(
                name="proposal_limit_per_org",
                pattern=r"Limit on Number of Proposals per Organization:\s*([^\n]+)",
                post_process=PostProcessType.CLEAN_TEXT
            ),
            ExtractionRule(
                name="proposal_limit_per_pi",
                pattern=r"Limit on Number of Proposals per PI or co-PI:\s*([^\n]+)",
                post_process=PostProcessType.CLEAN_TEXT
            )
        ]
    )
}