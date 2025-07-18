"""
Test helper utilities for NSF Researcher Matching API.

This module provides common utility functions for test setup, data generation,
file operations, and test execution helpers.
"""

import os
import json
import uuid
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
import asyncio
from functools import wraps

import pytest
from fastapi.testclient import TestClient
from fastapi import status


def create_test_file(content: str, filename: str = None, directory: str = None) -> str:
    """
    Create a temporary test file with specified content.
    
    Args:
        content: File content as string
        filename: Optional filename, generates UUID if not provided
        directory: Optional directory path, uses temp dir if not provided
    
    Returns:
        Full path to created file
    """
    if directory is None:
        directory = tempfile.gettempdir()
    
    if filename is None:
        filename = f"test_{uuid.uuid4().hex[:8]}.txt"
    
    file_path = Path(directory) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)


def create_test_pdf(content: str = None, filename: str = None, directory: str = None) -> str:
    """
    Create a minimal test PDF file.
    
    Args:
        content: Optional text content for PDF
        filename: Optional filename
        directory: Optional directory path
    
    Returns:
        Full path to created PDF file
    """
    if directory is None:
        directory = tempfile.gettempdir()
    
    if filename is None:
        filename = f"test_{uuid.uuid4().hex[:8]}.pdf"
    
    if content is None:
        content = "Test PDF Content"
    
    # Create minimal PDF structure
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(content) + 50}
>>
stream
BT
/F1 12 Tf
72 720 Td
({content}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000173 00000 n 
0000000301 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
{400 + len(content)}
%%EOF"""
    
    file_path = Path(directory) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(pdf_content)
    
    return str(file_path)


def create_test_json(data: Dict[str, Any], filename: str = None, directory: str = None) -> str:
    """
    Create a test JSON file with specified data.
    
    Args:
        data: Dictionary to serialize as JSON
        filename: Optional filename
        directory: Optional directory path
    
    Returns:
        Full path to created JSON file
    """
    if directory is None:
        directory = tempfile.gettempdir()
    
    if filename is None:
        filename = f"test_{uuid.uuid4().hex[:8]}.json"
    
    file_path = Path(directory) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    return str(file_path)


def generate_test_id(prefix: str = "test") -> str:
    """
    Generate a unique test ID with optional prefix.
    
    Args:
        prefix: String prefix for the ID
    
    Returns:
        Unique test ID string
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 10.0,
    interval: float = 0.1,
    error_message: str = "Condition not met within timeout"
) -> bool:
    """
    Wait for a condition to become true within a timeout period.
    
    Args:
        condition: Callable that returns boolean
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        error_message: Error message if timeout is reached
    
    Returns:
        True if condition is met, raises TimeoutError otherwise
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)
    
    raise TimeoutError(error_message)


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function execution on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between attempts in seconds
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    continue
            
            raise last_exception
        
        return wrapper
    return decorator


def measure_execution_time(func: Callable) -> tuple:
    """
    Measure execution time of a function.
    
    Args:
        func: Function to measure
    
    Returns:
        Tuple of (result, execution_time_seconds)
    """
    start_time = time.time()
    result = func()
    execution_time = time.time() - start_time
    return result, execution_time


async def measure_async_execution_time(coro) -> tuple:
    """
    Measure execution time of an async function.
    
    Args:
        coro: Coroutine to measure
    
    Returns:
        Tuple of (result, execution_time_seconds)
    """
    start_time = time.time()
    result = await coro
    execution_time = time.time() - start_time
    return result, execution_time


def validate_response_structure(response_data: Dict[str, Any], expected_keys: List[str]) -> bool:
    """
    Validate that response data contains expected keys.
    
    Args:
        response_data: Response data dictionary
        expected_keys: List of expected keys
    
    Returns:
        True if all expected keys are present
    """
    missing_keys = [key for key in expected_keys if key not in response_data]
    if missing_keys:
        raise AssertionError(f"Missing keys in response: {missing_keys}")
    return True


def extract_error_details(response) -> Dict[str, Any]:
    """
    Extract error details from HTTP response.
    
    Args:
        response: HTTP response object
    
    Returns:
        Dictionary with error details
    """
    error_details = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "content": None,
        "json": None
    }
    
    try:
        error_details["json"] = response.json()
    except Exception:
        try:
            error_details["content"] = response.text
        except Exception:
            error_details["content"] = str(response.content)
    
    return error_details


def create_multipart_file_data(file_path: str, field_name: str = "file") -> Dict[str, Any]:
    """
    Create multipart form data for file upload testing.
    
    Args:
        file_path: Path to file to upload
        field_name: Form field name for the file
    
    Returns:
        Dictionary suitable for requests/httpx files parameter
    """
    with open(file_path, 'rb') as f:
        return {
            field_name: (Path(file_path).name, f.read(), "application/octet-stream")
        }


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text for comparison.
    
    Args:
        text: Input text
    
    Returns:
        Text with normalized whitespace
    """
    return ' '.join(text.split())


def deep_sort_dict(obj: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively sort dictionary keys and list items for consistent comparison.
    
    Args:
        obj: Object to sort (dict, list, or other)
    
    Returns:
        Sorted object
    """
    if isinstance(obj, dict):
        return {k: deep_sort_dict(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return sorted([deep_sort_dict(item) for item in obj], key=str)
    else:
        return obj


def create_test_environment_vars(overrides: Dict[str, str] = None) -> Dict[str, str]:
    """
    Create test environment variables with optional overrides.
    
    Args:
        overrides: Dictionary of environment variable overrides
    
    Returns:
        Dictionary of test environment variables
    """
    test_env = {
        "TESTING": "true",
        "LOG_LEVEL": "WARNING",
        "DATABASE_URL": "sqlite:///./test.db",
        "UPLOAD_DIR": "./test_uploads",
        "MODEL_DIR": "./test_models",
        "OUTPUT_DIR": "./test_outputs",
        "ENABLE_CACHING": "false",
        "DEFAULT_TOP_N_RESEARCHERS": "5",
        "DEFAULT_TEAM_SIZE": "3"
    }
    
    if overrides:
        test_env.update(overrides)
    
    return test_env


class TestTimer:
    """Context manager for measuring test execution time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time


class AsyncTestTimer:
    """Async context manager for measuring test execution time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time


def skip_if_external_service_unavailable(service_name: str):
    """
    Decorator to skip tests if external service is unavailable.
    
    Args:
        service_name: Name of the external service
    
    Returns:
        Pytest skip decorator
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if service is available (implement service-specific checks)
            if service_name.lower() == "ai" and not os.getenv("ANTHROPIC_API_KEY"):
                pytest.skip(f"Skipping test: {service_name} service not available")
            return func(*args, **kwargs)
        return wrapper
    return decorator