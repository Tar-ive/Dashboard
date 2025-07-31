#!/usr/bin/env python3
"""Manual test script for the deconstruct endpoint with real PDF file."""

import requests
import os
import sys

def test_deconstruct_endpoint():
    """Test the deconstruct endpoint with the actual NSF PDF file."""
    
    # Path to the PDF file
    pdf_path = "data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False
    
    # API endpoint
    url = "http://localhost:8000/api/deconstruct"
    
    try:
        # Open and upload the PDF file
        with open(pdf_path, "rb") as f:
            files = {"file": ("nsf_mfai.pdf", f, "application/pdf")}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get("job_id")
            print(f"✅ Success! Job created with ID: {job_id}")
            
            # Test job status endpoint
            status_url = f"http://localhost:8000/api/jobs/{job_id}"
            status_response = requests.get(status_url)
            print(f"Job Status: {status_response.status_code}")
            if status_response.status_code == 200:
                print(f"Job Details: {status_response.json()}")
            
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing deconstruct endpoint with NSF PDF file...")
    success = test_deconstruct_endpoint()
    sys.exit(0 if success else 1)