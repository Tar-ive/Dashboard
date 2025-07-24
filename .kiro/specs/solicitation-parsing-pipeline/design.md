# Design Document

## Overview

The Solicitation Parsing Pipeline follows Feature-Driven Development (FDD) principles, delivering incremental value through focused, testable features. Starting with a single real PDF document as our test case, we'll build a minimal viable parser that can be iteratively enhanced.

The design prioritizes working software over comprehensive documentation, using the existing codebase patterns and a real-world PDF tester to validate each feature increment. Each feature will be developed, tested, and integrated before moving to the next.

## Architecture

### FDD-Based Incremental Architecture

Following FDD principles, we'll build features incrementally:

**Phase 1: Core PDF Parser** (MVP)
```
PDF File → Text Extractor → Basic Pattern Matcher → Solicitation Object
```

**Phase 2: Enhanced Extraction**
```
PDF File → Text Extractor → Smart Pattern Matcher → Validation → Solicitation Object
```

**Phase 3: UI Integration**
```
Streamlit Upload → PDF Parser → Preview/Edit → Existing Workflow
```

### Test-Driven Approach

Using a real PDF document (`data/test_solicitation.pdf`) as our primary test case:
- Each feature will be validated against this document
- Extraction patterns will be refined based on actual content
- Quality metrics will be measured against known good data
- User experience will be tested with real document workflow

## Components and Interfaces

### FDD Feature-Based Components

Following the existing codebase patterns, we'll create focused, single-responsibility modules:

### 1. SolicitationParser (`modules/solicitation_parser.py`)

**Purpose**: Core parsing functionality following existing module patterns

```python
class SolicitationParser:
    """Handles PDF solicitation parsing with configurable extraction patterns."""
    
    def __init__(self):
        """Initialize as stateless utility class (matches existing pattern)."""
        self.extraction_configs = self._load_default_configs()
    
    def parse_pdf_solicitation(self, pdf_path: str) -> Dict[str, Any]:
        """Main parsing method - extracts structured data from PDF."""
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract raw text using PyPDF2 (matches your provided code)."""
        
    def extract_solicitation_data(self, text: str) -> Dict[str, Any]:
        """Apply extraction patterns to get structured data."""
        
    def convert_to_solicitation(self, extracted_data: Dict) -> Solicitation:
        """Convert extracted data to existing Solicitation model."""
```

### 2. Extended Data Models (`modules/data_models.py`)

**Purpose**: Minimal extensions to existing data models

```python
@dataclass
class SolicitationParsingResult:
    """Results from solicitation parsing process."""
    extracted_data: Dict[str, Any]
    confidence_score: float
    missing_fields: List[str]
    source_file: str
    processing_time: float

# Extend existing Solicitation class
@dataclass 
class Solicitation:
    # ... existing fields ...
    
    # New optional parsing metadata
    parsing_metadata: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[float] = None
```

### 3. Streamlit Integration (Minimal UI Changes)

**Purpose**: Add parsing capability to existing workflow

- New file upload option in Step 1 (alongside JSON upload)
- Preview extracted data before proceeding to matching
- Maintain existing session state structure

## Data Models

### Minimal Data Model Extensions

Following FDD principles, we'll make minimal changes to existing models:

```python
# Extend existing ExtractionConfig from your provided code
@dataclass
class ExtractionConfig:
    """Configuration for data extraction (from your provided code)."""
    field_name: str
    patterns: List[str]
    extraction_type: str = "single"  # single, multiple, nested, table
    post_process: Optional[str] = None
    required: bool = False
    default_value: Any = ""

# New minimal result class
@dataclass
class SolicitationParsingResult:
    """Results from PDF parsing process."""
    solicitation: Solicitation
    confidence_score: float
    extraction_details: Dict[str, Any]
    processing_time: float
    
# Extend existing Solicitation with optional parsing metadata
# (No breaking changes to existing code)
```

## Error Handling

### FDD-Based Error Handling Strategy

Following existing codebase patterns for graceful degradation:

```python
# Match existing error handling patterns from data_loader.py
try:
    solicitation = parser.parse_pdf_solicitation(pdf_path)
    st.success("✅ Solicitation parsed successfully!")
except Exception as e:
    st.error(f"❌ Error parsing PDF: {str(e)}")
    st.info("💡 Please try manual entry or check PDF format")
    # Fallback to existing manual JSON upload workflow
```

### Graceful Fallback
- **PDF Parsing Fails**: Fall back to existing JSON upload workflow
- **Low Confidence**: Show extracted data with edit options
- **Missing Fields**: Highlight missing required fields for manual entry
- **File Issues**: Clear error messages with alternative options

## Testing Strategy

### FDD Test-Driven Development

Using the real PDF document (`data/test_solicitation.pdf`) as our primary test case:

### Feature-by-Feature Testing
1. **PDF Text Extraction**: Verify text extraction from test PDF
2. **Pattern Matching**: Test extraction patterns against actual content
3. **Data Conversion**: Validate conversion to Solicitation object
4. **UI Integration**: Test upload and preview workflow
5. **End-to-End**: Complete workflow from PDF upload to researcher matching

### Real Document Validation
- Extract known fields from test PDF and compare with manual extraction
- Measure extraction accuracy and confidence scores
- Test edge cases found in the actual document
- Validate that extracted data works with existing matching algorithms

### Incremental Testing Approach
Each feature increment will be tested against the real PDF before proceeding to the next feature.

## Implementation Approach

### FDD Feature Development Sequence

**Feature 1: Basic PDF Text Extraction**
- Create `SolicitationParser` class with PDF text extraction
- Test with real PDF document in `data/test_solicitation.pdf`
- Validate text extraction quality and completeness

**Feature 2: Core Field Extraction**
- Implement pattern matching for essential fields (title, abstract, skills)
- Create extraction configurations based on actual PDF content
- Test extraction accuracy against known values

**Feature 3: Solicitation Object Creation**
- Convert extracted data to existing `Solicitation` data model
- Ensure compatibility with existing workflow
- Test integration with researcher matching pipeline

**Feature 4: Streamlit UI Integration**
- Add PDF upload option to existing Step 1
- Create preview interface for extracted data
- Allow manual editing of extracted fields

**Feature 5: Quality Assessment**
- Add confidence scoring for extracted fields
- Implement validation and error handling
- Provide user feedback on extraction quality

### Configuration Strategy

Start with hardcoded patterns based on test PDF, then make configurable:

```python
# Initial hardcoded approach for MVP
DEFAULT_PATTERNS = {
    "title": [r"Title:\s*([^\n]+)", r"Project Title:\s*([^\n]+)"],
    "abstract": [r"Abstract:\s*(.*?)(?=\n\n|\nTitle)", r"Summary:\s*(.*?)(?=\n\n)"],
    "required_skills": [r"Required.*?Skills?.*?:\s*(.*?)(?=\n\n)", r"Expertise.*?:\s*(.*?)(?=\n\n)"]
}
```

### Performance Considerations

Following existing codebase patterns:
- Use `@st.cache_data` for PDF text extraction (similar to data_loader.py)
- Implement graceful error handling (similar to existing modules)
- Maintain stateless service pattern (like existing utility classes)