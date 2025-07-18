#!/usr/bin/env python3
"""Test the deconstruction task with a small sample"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks.deconstruction_task import deconstruct_solicitation_task
import tempfile

# Create a small test PDF content
test_content = """
NSF 24-TEST: Test Solicitation for AI Research

Award Information:
- Funding: Up to $500,000
- Duration: 3 years (36 months)
- Deadline: March 15, 2025

Eligibility:
- Principal Investigators must be U.S. citizens or permanent residents
- Must be affiliated with eligible institutions

Required Skills:
- Machine Learning
- Python Programming
- Statistical Analysis
"""

# Create a temporary text file (simulating PDF extraction)
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(test_content)
    temp_file = f.name

print(f"Testing with small content file: {temp_file}")

try:
    result = deconstruct_solicitation_task("test_small_job", temp_file)
    print("✅ Task completed successfully!")
    print(f"Award Title: {result.award_title}")
    print(f"Funding: ${result.funding_ceiling:,}" if result.funding_ceiling else "Funding: Not extracted")
    print(f"Duration: {result.project_duration_months} months" if result.project_duration_months else "Duration: Not extracted")
    print(f"Skills: {result.required_scientific_skills}")
    print(f"Confidence: {result.extraction_confidence:.1%}")
except Exception as e:
    print(f"❌ Task failed: {e}")
finally:
    # Clean up
    os.unlink(temp_file)