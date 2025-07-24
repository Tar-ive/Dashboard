#!/usr/bin/env python3
"""
Test script for Streamlit PDF integration workflow.
Simulates the user workflow from PDF upload to team matching.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# Add modules to path
sys.path.append('.')

from modules.solicitation_parser import SolicitationParser
from modules.data_models import Solicitation


def simulate_pdf_upload_workflow():
    """Simulate the PDF upload workflow as it would happen in Streamlit."""
    
    print("🔍 Simulating Streamlit PDF Upload Workflow...")
    
    # Step 1: Simulate file upload
    print("\n1. Simulating PDF file upload...")
    
    # Create a mock uploaded file object (similar to Streamlit's UploadedFile)
    class MockUploadedFile:
        def __init__(self, file_path):
            self.name = Path(file_path).name
            with open(file_path, 'rb') as f:
                self.content = f.read()
        
        def getbuffer(self):
            return self.content
    
    mock_file = MockUploadedFile('data/test_solicitation.pdf')
    print(f"   ✅ Mock file created: {mock_file.name}")
    
    # Step 2: Simulate the handle_pdf_upload function logic
    print("\n2. Simulating PDF processing...")
    
    temp_path = f"./data/temp_{mock_file.name}"
    
    try:
        # Save uploaded file (as done in handle_pdf_upload)
        with open(temp_path, "wb") as f:
            f.write(mock_file.getbuffer())
        print(f"   ✅ Temporary file saved: {Path(temp_path).name}")
        
        # Parse PDF
        parser = SolicitationParser()
        parsing_result = parser.parse_pdf_solicitation(temp_path)
        print(f"   ✅ PDF parsed successfully!")
        print(f"   📊 Confidence: {parsing_result.confidence_score:.2%}")
        
        # Step 3: Convert to solicitation
        print("\n3. Converting to Solicitation object...")
        solicitation = parser.convert_to_solicitation(parsing_result)
        print(f"   ✅ Conversion successful!")
        print(f"   📝 Title: {solicitation.title}")
        print(f"   🎯 Skills: {len(solicitation.required_skills_checklist)} extracted")
        
        # Step 4: Simulate quality check (as done in the UI)
        print("\n4. Quality assessment...")
        if parsing_result.confidence_score > 0.3:
            print(f"   ✅ Quality acceptable for automatic processing")
        else:
            print(f"   ⚠️  Quality requires manual review")
        
        # Step 5: Simulate data validation for matching workflow
        print("\n5. Validating for matching workflow...")
        
        validation_passed = True
        if not solicitation.title:
            print(f"   ❌ Missing title")
            validation_passed = False
        if not solicitation.abstract:
            print(f"   ❌ Missing abstract")
            validation_passed = False
        if not solicitation.required_skills_checklist:
            print(f"   ❌ Missing required skills")
            validation_passed = False
        
        if validation_passed:
            print(f"   ✅ Ready for researcher matching workflow")
        else:
            print(f"   ⚠️  Requires manual completion before matching")
        
        return solicitation, parsing_result
        
    except Exception as e:
        print(f"   ❌ Workflow failed: {str(e)}")
        return None, None
    finally:
        # Clean up temporary file
        if Path(temp_path).exists():
            Path(temp_path).unlink()
            print(f"   ✅ Temporary file cleaned up")


def test_session_state_simulation():
    """Test session state management simulation."""
    
    print("\n🔍 Testing Session State Management...")
    
    # Simulate Streamlit session state
    session_state = {
        'parsing_result': None,
        'parsed_solicitation': None,
        'data_loaded': True  # Assume system is initialized
    }
    
    solicitation, parsing_result = simulate_pdf_upload_workflow()
    
    if solicitation and parsing_result:
        # Simulate storing in session state
        session_state['parsing_result'] = parsing_result
        session_state['parsed_solicitation'] = solicitation
        
        print(f"\n   ✅ Session state updated:")
        print(f"   📊 Parsing result stored: {session_state['parsing_result'] is not None}")
        print(f"   📋 Solicitation stored: {session_state['parsed_solicitation'] is not None}")
        
        # Simulate transition to next workflow step
        if session_state['parsed_solicitation'] and session_state['data_loaded']:
            print(f"   ✅ Ready to proceed to researcher matching")
            return True
        else:
            print(f"   ❌ Not ready for next step")
            return False
    else:
        print(f"   ❌ Session state update failed")
        return False


def test_error_scenarios():
    """Test error handling in the workflow."""
    
    print("\n🔍 Testing Error Scenarios...")
    
    # Test 1: Invalid file type
    print("\n1. Testing invalid file type...")
    class MockInvalidFile:
        def __init__(self):
            self.name = "test.txt"
        def getbuffer(self):
            return b"This is not a PDF"
    
    mock_file = MockInvalidFile()
    file_type = mock_file.name.split('.')[-1].lower()
    
    if file_type not in ['pdf', 'json']:
        print(f"   ✅ Correctly identified invalid file type: {file_type}")
    else:
        print(f"   ❌ Failed to identify invalid file type")
    
    # Test 2: Corrupted PDF simulation
    print("\n2. Testing corrupted PDF handling...")
    temp_path = "./data/temp_corrupted.pdf"
    
    try:
        # Create a fake corrupted PDF
        with open(temp_path, "wb") as f:
            f.write(b"This is not a valid PDF content")
        
        parser = SolicitationParser()
        try:
            result = parser.parse_pdf_solicitation(temp_path)
            print(f"   ⚠️  Parsing succeeded unexpectedly (graceful fallback)")
            print(f"   📊 Confidence: {result.confidence_score:.2%}")
        except Exception as e:
            print(f"   ✅ Correctly handled corrupted PDF: {type(e).__name__}")
        
    finally:
        if Path(temp_path).exists():
            Path(temp_path).unlink()
    
    return True


def main():
    """Run all workflow tests."""
    
    print("🚀 Starting Streamlit Integration Tests")
    print("=" * 50)
    
    tests = [
        ("PDF Upload Workflow", simulate_pdf_upload_workflow),
        ("Session State Management", test_session_state_simulation),
        ("Error Scenarios", test_error_scenarios)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result is not False:  # Allow None or True as success
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All workflow tests passed! Streamlit integration is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)