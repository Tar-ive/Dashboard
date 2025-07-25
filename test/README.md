# Test Suite Documentation

## AI-Powered Research Team Matching & Assembly System - Test Suite

This directory contains comprehensive test and debug utilities for the AI-powered research team matching system. The test suite validates all components from document parsing through team assembly, ensuring reliability and performance.

## 📁 Test Structure

```
test/
├── README.md                           # This documentation
├── unit/                              # Unit tests for individual components
│   ├── test_advanced_parser.py        # Advanced parser functionality tests
│   └── test_parser.py                 # Basic parser functionality tests
├── integration/                       # Integration tests for complete workflows
│   ├── test_complete_workflow.py      # End-to-end PDF-to-team workflow
│   ├── test_integration.py            # Advanced parsing pipeline integration
│   ├── test_pdf_integration.py        # PDF parsing integration tests
│   └── test_streamlit_integration.py  # Streamlit workflow integration tests
├── feature/                           # Feature-specific tests
│   ├── test_enhanced_skill_extractor.py    # Enhanced skill extraction tests
│   └── test_streamlit_enhanced_extraction.py # Streamlit enhanced extraction tests
├── debug/                             # Debug utilities and scripts
│   └── debug_pdf_text.py             # PDF text structure analysis
└── comprehensive_test.py              # Complete system validation

```

## 🧪 Test Categories

### Unit Tests
**Purpose**: Test individual components in isolation
- **test_advanced_parser.py**: Advanced solicitation parser features including multi-format support, template system, logging, and performance monitoring
- **test_parser.py**: Basic PDF parsing functionality and text extraction

### Integration Tests
**Purpose**: Test complete workflows and component interactions
- **test_complete_workflow.py**: Full pipeline from PDF upload through team assembly
- **test_integration.py**: Advanced parsing pipeline with document type detection and quality assessment
- **test_pdf_integration.py**: PDF parsing integration within Streamlit workflow
- **test_streamlit_integration.py**: Enhanced skill extraction integration with Streamlit

### Feature Tests
**Purpose**: Test specific advanced features
- **test_enhanced_skill_extractor.py**: Dual-model skill extraction using LLM and OpenAlex
- **test_streamlit_enhanced_extraction.py**: Enhanced extraction in Streamlit context

### Debug Utilities
**Purpose**: Development and troubleshooting tools
- **debug_pdf_text.py**: Analyze PDF text structure for pattern refinement

### Comprehensive Testing
- **comprehensive_test.py**: Complete system validation covering all requirements

## 🚀 Quick Start

### Prerequisites
Ensure all dependencies are installed:
```bash
uv sync
```

Required data files:
- `data/test_solicitation.pdf` - Test PDF document
- `data/tfidf_model.pkl` - TF-IDF model
- `data/researcher_vectors.npz` - Researcher vectors
- `data/conceptual_profiles.npz` - Paper embeddings
- `data/evidence_index.json` - Researcher-paper mapping
- `data/researcher_metadata.parquet` - Researcher profiles

### Running Tests

#### Run All Tests
```bash
# From project root
python -m pytest test/ -v
```

#### Run Specific Test Categories
```bash
# Unit tests only
python test/unit/test_advanced_parser.py

# Integration tests
python test/integration/test_complete_workflow.py

# Feature tests
python test/feature/test_enhanced_skill_extractor.py
```

#### Run Individual Tests
```bash
# Basic parser functionality
python test/unit/test_parser.py

# Complete workflow validation
python test/integration/test_complete_workflow.py

# Enhanced skill extraction
python test/feature/test_enhanced_skill_extractor.py
```

## 📊 Test Coverage

### Core Components Tested
- ✅ **PDF Text Extraction**: PyPDF2 integration with error handling
- ✅ **Document Type Detection**: NSF, NIH, generic RFP pattern recognition
- ✅ **Pattern-based Extraction**: Title, abstract, skills, funding information
- ✅ **Data Validation**: Cleaning, formatting, quality assessment
- ✅ **Solicitation Object Creation**: Mapping to existing data models
- ✅ **Enhanced Skill Extraction**: Dual-model LLM + OpenAlex validation
- ✅ **Template System**: Save/load extraction templates
- ✅ **Performance Monitoring**: Processing time and memory usage tracking
- ✅ **Error Handling**: Graceful degradation and fallback mechanisms

### Workflow Integration Tested
- ✅ **PDF Upload → Parsing**: File handling and text extraction
- ✅ **Parsing → Data Loading**: System initialization
- ✅ **Data Loading → Matching**: Researcher scoring and ranking
- ✅ **Matching → Team Assembly**: Optimal team composition
- ✅ **Streamlit Integration**: UI workflow and caching
- ✅ **Quality Assessment**: Confidence scoring and validation

## 🔧 Environment Setup

### Required Environment Variables
```bash
# For enhanced skill extraction
GROQ_API_KEY=your_groq_api_key_here
```

### Optional Configuration
```bash
# For debugging
PYTHONPATH=.
```

## 📈 Performance Benchmarks

### Expected Performance Metrics
- **PDF Parsing**: < 5 seconds for typical documents
- **Enhanced Skill Extraction**: < 10 seconds with API calls
- **Complete Workflow**: < 30 seconds end-to-end
- **Memory Usage**: < 500MB peak during processing

### Quality Thresholds
- **Extraction Confidence**: > 70% for production use
- **Skill Detection**: > 3 skills minimum for valid extraction
- **Data Completeness**: Title and abstract required fields

## 🐛 Debugging Guide

### Common Issues and Solutions

#### PDF Parsing Failures
```bash
# Debug PDF text structure
python test/debug/debug_pdf_text.py

# Check file permissions and format
file data/test_solicitation.pdf
```

#### Missing Dependencies
```bash
# Reinstall dependencies
uv sync --force

# Check specific imports
python -c "import PyPDF2; print('PyPDF2 OK')"
```

#### API Key Issues
```bash
# Verify environment variables
echo $GROQ_API_KEY

# Test API connectivity
python test/feature/test_enhanced_skill_extractor.py
```

#### Data File Issues
```bash
# Check required files
ls -la data/

# Verify file integrity
python -c "import pickle; pickle.load(open('data/tfidf_model.pkl', 'rb'))"
```

## 📝 Test Development Guidelines

### Adding New Tests
1. **Choose appropriate category**: unit, integration, feature, or debug
2. **Follow naming convention**: `test_[component]_[feature].py`
3. **Include docstrings**: Describe test purpose and expected behavior
4. **Use descriptive assertions**: Clear success/failure messages
5. **Handle cleanup**: Remove temporary files and reset state

### Test Structure Template
```python
#!/usr/bin/env python3
"""
Test description and purpose.
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.append('.')

def test_feature_name():
    """Test specific feature functionality."""
    print("🧪 Testing Feature Name")
    print("=" * 40)
    
    try:
        # Test implementation
        result = perform_test()
        
        # Assertions
        assert result is not None, "Result should not be None"
        
        print("✅ Test passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_feature_name()
    sys.exit(0 if success else 1)
```

## 🔍 Test Results Interpretation

### Success Indicators
- ✅ **Green checkmarks**: Test passed
- 📊 **Metrics within range**: Performance acceptable
- 🎉 **Completion messages**: All requirements met

### Warning Indicators
- ⚠️ **Yellow warnings**: Non-critical issues
- 📈 **Performance notes**: Slower than expected but functional
- 🔄 **Retry suggestions**: Temporary failures

### Failure Indicators
- ❌ **Red X marks**: Test failed
- 💥 **Error messages**: Critical failures
- 🚫 **Missing dependencies**: Setup issues

## 📚 Additional Resources

### Related Documentation
- [Project Structure](../README.md) - Main project documentation
- [Technology Stack](../.kiro/steering/tech.md) - Technical specifications
- [Product Overview](../.kiro/steering/product.md) - System capabilities

### External Dependencies
- [PyPDF2 Documentation](https://pypdf2.readthedocs.io/)
- [Streamlit Testing](https://docs.streamlit.io/library/advanced-features/testing)
- [scikit-learn Testing](https://scikit-learn.org/stable/developers/testing.html)

### Support
For test-related issues:
1. Check this documentation first
2. Run debug utilities to identify issues
3. Review error messages and stack traces
4. Verify environment setup and dependencies

---

*Last updated: January 2025*
*Test suite version: 1.0*