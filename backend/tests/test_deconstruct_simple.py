#!/usr/bin/env python3
"""Simple test for deconstruct endpoint without Redis dependency."""

import os
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

def test_with_real_pdf():
    """Test deconstruct endpoint with the actual NSF PDF file."""
    
    pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False
    
    # Create test client
    client = TestClient(app)
    
    # Mock the job manager to avoid Redis dependency
    with patch('app.api.deconstruct.get_job_manager') as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.create_job.return_value = "test-job-nsf-mfai-123"
        mock_get_manager.return_value = mock_manager
        
        with patch('app.api.deconstruct.enqueue_deconstruct_task') as mock_enqueue:
            mock_enqueue.return_value = None
            
            try:
                # Test with the actual PDF file
                with open(pdf_path, "rb") as f:
                    response = client.post(
                        "/api/deconstruct",
                        files={"file": ("nsf_mfai.pdf", f, "application/pdf")}
                    )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Response: {data}")
                    
                    # Verify the job was created and enqueued
                    mock_manager.create_job.assert_called_once_with("deconstruct")
                    mock_enqueue.assert_called_once()
                    
                    # Check the enqueue call arguments
                    call_args = mock_enqueue.call_args[0]
                    job_id = call_args[0]
                    file_path = call_args[1]
                    
                    print(f"Job ID: {job_id}")
                    print(f"File saved to: {file_path}")
                    
                    # Verify file was actually saved
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"✅ File saved successfully! Size: {file_size} bytes")
                        
                        # Clean up the test file
                        os.remove(file_path)
                        print("✅ Test file cleaned up")
                    else:
                        print("❌ File was not saved")
                        return False
                    
                    return True
                else:
                    print(f"❌ Failed: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return False

if __name__ == "__main__":
    print("Testing deconstruct endpoint with NSF PDF file (mocked Redis)...")
    success = test_with_real_pdf()
    
    if success:
        print("\n🎉 All tests passed! The deconstruct endpoint is working correctly.")
    else:
        print("\n❌ Tests failed!")
    
    exit(0 if success else 1)