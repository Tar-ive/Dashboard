#!/usr/bin/env python3
"""
Test script for PDF parsing integration in Streamlit workflow.
Tests the complete pipeline from PDF upload to solicitation object creation.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add modules to path
sys.path.append('.')

from modules.solicitation_parser import SolicitationParser
from modules.data_models import Solicitation


def test_pdf_parsing():
    """Test PDF parsing functionality."""
    
    print("🔍 Testing PDF Parsing Integration...")
    
    # Test 1: Basic PDF parsing
    print("\n1. Testing basic PDF parsing...")
    parser = SolicitationParser()
    
    try:
        result = parser.parse_pdf_solicitation('data/test_solicitation.pdf')
        print(f"   ✅ Parsing successful!")
        print(f"   📊 Confidence Score: {result.confidence_score:.2%}")
        print(f"   ⏱️  Processing Time: {result.processing_time:.2f}s")
        print(f"   📄 Source File: {Path(result.source_file).name}")
        
        if result.missing_fields:
            print(f"   ⚠️  Missing Fields: {', '.join(result.missing_fields)}")
        else:
            print(f"   ✅ All fields extracted successfully")
            
    except Exception as e:
        print(f"   ❌ Parsing failed: {str(e)}")
        return False
    
    # Test 2: Conversion to Solicitation object
    print("\n2. Testing conversion to Solicitation object...")
    
    try:
        solicitation = parser.convert_to_solicitation(result)
        print(f"   ✅ Conversion successful!")
        print(f"   📝 Title: {solicitation.title[:60]}...")
        print(f"   📋 Abstract Length: {len(solicitation.abstract)} chars")
        print(f"   🎯 Required Skills: {len(solicitation.required_skills_checklist)} skills")
        
        if solicitation.parsing_metadata:
            print(f"   📊 Extraction Confidence: {solicitation.extraction_confidence:.2%}")
            
    except Exception as e:
        print(f"   ❌ Conversion failed: {str(e)}")
        return False
    
    # Test 3: Data quality validation
    print("\n3. Testing data quality...")
    
    required_fields = ['title', 'abstract', 'required_skills_checklist']
    missing_required = []
    
    for field in required_fields:
        value = getattr(solicitation, field, None)
        if not value or (isinstance(value, list) and len(value) == 0):
            missing_required.append(field)
    
    if missing_required:
        print(f"   ⚠️  Missing required fields: {', '.join(missing_required)}")
    else:
        print(f"   ✅ All required fields present")
    
    # Test 4: Skills extraction quality
    print("\n4. Testing skills extraction...")
    
    if solicitation.required_skills_checklist:
        print(f"   ✅ Extracted {len(solicitation.required_skills_checklist)} skills:")
        for i, skill in enumerate(solicitation.required_skills_checklist[:5], 1):
            print(f"      {i}. {skill}")
        if len(solicitation.required_skills_checklist) > 5:
            print(f"      ... and {len(solicitation.required_skills_checklist) - 5} more")
    else:
        print(f"   ⚠️  No skills extracted")
    
    return True


def test_file_handling():
    """Test file upload simulation."""
    
    print("\n🔍 Testing File Handling...")
    
    # Test with temporary file (simulating upload)
    print("\n1. Testing temporary file handling...")
    
    try:
        # Copy test file to temporary location
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            shutil.copy('data/test_solicitation.pdf', temp_file.name)
            temp_path = temp_file.name
        
        # Parse temporary file
        parser = SolicitationParser()
        result = parser.parse_pdf_solicitation(temp_path)
        
        print(f"   ✅ Temporary file parsing successful!")
        print(f"   📊 Confidence: {result.confidence_score:.2%}")
        
        # Clean up
        Path(temp_path).unlink()
        print(f"   ✅ Temporary file cleaned up")
        
    except Exception as e:
        print(f"   ❌ File handling failed: {str(e)}")
        return False
    
    return True


def test_error_handling():
    """Test error handling scenarios."""
    
    print("\n🔍 Testing Error Handling...")
    
    parser = SolicitationParser()
    
    # Test 1: Non-existent file
    print("\n1. Testing non-existent file...")
    try:
        result = parser.parse_pdf_solicitation('nonexistent.pdf')
        print(f"   ❌ Should have failed but didn't")
        return False
    except Exception as e:
        print(f"   ✅ Correctly handled error: {type(e).__name__}")
    
    # Test 2: Non-PDF file
    print("\n2. Testing non-PDF file...")
    try:
        result = parser.parse_pdf_solicitation('requirements.txt')
        print(f"   ❌ Should have failed but didn't")
        return False
    except Exception as e:
        print(f"   ✅ Correctly handled error: {type(e).__name__}")
    
    return True


def main():
    """Run all tests."""
    
    print("🚀 Starting PDF Integration Tests")
    print("=" * 50)
    
    tests = [
        ("PDF Parsing", test_pdf_parsing),
        ("File Handling", test_file_handling),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PDF integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)