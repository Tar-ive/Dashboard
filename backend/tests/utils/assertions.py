"""
Custom assertions for NSF Researcher Matching API tests.

This module provides specialized assertion functions for HTTP responses,
data validation, performance testing, and domain-specific validations.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def assert_http_status(response, expected_status: int, message: str = None):
    """
    Assert HTTP response status code with detailed error information.
    
    Args:
        response: HTTP response object
        expected_status: Expected status code
        message: Optional custom error message
    """
    if response.status_code != expected_status:
        error_details = {
            "expected_status": expected_status,
            "actual_status": response.status_code,
            "response_headers": dict(response.headers),
            "response_body": None
        }
        
        try:
            error_details["response_body"] = response.json()
        except Exception:
            try:
                error_details["response_body"] = response.text
            except Exception:
                error_details["response_body"] = str(response.content)
        
        error_msg = message or f"Expected status {expected_status}, got {response.status_code}"
        error_msg += f"\nResponse details: {json.dumps(error_details, indent=2, default=str)}"
        
        pytest.fail(error_msg)


def assert_response_structure(response_data: Dict[str, Any], expected_structure: Dict[str, type]):
    """
    Assert that response data matches expected structure.
    
    Args:
        response_data: Response data dictionary
        expected_structure: Dictionary mapping field names to expected types
    """
    errors = []
    
    for field_name, expected_type in expected_structure.items():
        if field_name not in response_data:
            errors.append(f"Missing field: {field_name}")
            continue
        
        actual_value = response_data[field_name]
        
        if expected_type == "optional":
            continue  # Optional field, skip type check
        
        if not isinstance(actual_value, expected_type):
            errors.append(
                f"Field '{field_name}': expected {expected_type.__name__}, "
                f"got {type(actual_value).__name__}"
            )
    
    if errors:
        pytest.fail(f"Response structure validation failed:\n" + "\n".join(errors))


def assert_json_schema(data: Dict[str, Any], schema: Dict[str, Any]):
    """
    Assert that data conforms to JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema definition
    """
    try:
        import jsonschema
        jsonschema.validate(data, schema)
    except ImportError:
        pytest.skip("jsonschema package not available for schema validation")
    except jsonschema.ValidationError as e:
        pytest.fail(f"JSON schema validation failed: {e.message}")


def assert_performance_threshold(execution_time: float, max_time: float, operation: str = "Operation"):
    """
    Assert that operation completed within performance threshold.
    
    Args:
        execution_time: Actual execution time in seconds
        max_time: Maximum allowed time in seconds
        operation: Description of the operation being tested
    """
    if execution_time > max_time:
        pytest.fail(
            f"{operation} took {execution_time:.3f}s, "
            f"exceeding threshold of {max_time:.3f}s"
        )


def assert_accuracy_metrics(
    actual_results: List[Any],
    expected_results: List[Any],
    min_precision: float = 0.8,
    min_recall: float = 0.8,
    min_f1: float = 0.8
):
    """
    Assert that matching results meet accuracy thresholds.
    
    Args:
        actual_results: Actual matching results
        expected_results: Expected/ground truth results
        min_precision: Minimum required precision
        min_recall: Minimum required recall
        min_f1: Minimum required F1 score
    """
    from .accuracy_metrics import calculate_precision, calculate_recall, calculate_f1_score
    
    precision = calculate_precision(actual_results, expected_results)
    recall = calculate_recall(actual_results, expected_results)
    f1_score = calculate_f1_score(precision, recall)
    
    errors = []
    
    if precision < min_precision:
        errors.append(f"Precision {precision:.3f} below threshold {min_precision}")
    
    if recall < min_recall:
        errors.append(f"Recall {recall:.3f} below threshold {min_recall}")
    
    if f1_score < min_f1:
        errors.append(f"F1 score {f1_score:.3f} below threshold {min_f1}")
    
    if errors:
        pytest.fail(f"Accuracy metrics validation failed:\n" + "\n".join(errors))


def assert_file_exists(file_path: Union[str, Path], message: str = None):
    """
    Assert that file exists at specified path.
    
    Args:
        file_path: Path to file
        message: Optional custom error message
    """
    path = Path(file_path)
    if not path.exists():
        error_msg = message or f"File does not exist: {file_path}"
        pytest.fail(error_msg)


def assert_valid_uuid(value: str, version: int = 4):
    """
    Assert that string is a valid UUID.
    
    Args:
        value: String to validate as UUID
        version: Expected UUID version
    """
    try:
        uuid_obj = uuid.UUID(value)
        if uuid_obj.version != version:
            pytest.fail(f"Expected UUID version {version}, got version {uuid_obj.version}")
    except ValueError:
        pytest.fail(f"Invalid UUID format: {value}")


def assert_datetime_format(value: str, format_string: str = "%Y-%m-%dT%H:%M:%S"):
    """
    Assert that string matches expected datetime format.
    
    Args:
        value: String to validate as datetime
        format_string: Expected datetime format
    """
    try:
        datetime.strptime(value, format_string)
    except ValueError:
        pytest.fail(f"Invalid datetime format: {value} (expected format: {format_string})")


def assert_numeric_range(value: Union[int, float], min_val: float = None, max_val: float = None):
    """
    Assert that numeric value is within specified range.
    
    Args:
        value: Numeric value to check
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
    """
    if min_val is not None and value < min_val:
        pytest.fail(f"Value {value} below minimum {min_val}")
    
    if max_val is not None and value > max_val:
        pytest.fail(f"Value {value} above maximum {max_val}")


def assert_list_contains(actual_list: List[Any], expected_items: List[Any], exact_match: bool = False):
    """
    Assert that list contains expected items.
    
    Args:
        actual_list: List to check
        expected_items: Items that should be present
        exact_match: If True, lists must match exactly
    """
    if exact_match:
        if set(actual_list) != set(expected_items):
            pytest.fail(f"Lists don't match exactly. Expected: {expected_items}, Got: {actual_list}")
    else:
        missing_items = [item for item in expected_items if item not in actual_list]
        if missing_items:
            pytest.fail(f"Missing items in list: {missing_items}")


def assert_email_format(email: str):
    """
    Assert that string is a valid email format.
    
    Args:
        email: String to validate as email
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        pytest.fail(f"Invalid email format: {email}")


def assert_url_format(url: str):
    """
    Assert that string is a valid URL format.
    
    Args:
        url: String to validate as URL
    """
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        pytest.fail(f"Invalid URL format: {url}")


def assert_researcher_data_structure(researcher_data: Dict[str, Any]):
    """
    Assert that researcher data has expected structure for NSF matching.
    
    Args:
        researcher_data: Researcher data dictionary
    """
    required_fields = {
        "name": str,
        "email": str,
        "institution": str,
        "expertise": list
    }
    
    optional_fields = {
        "department": str,
        "publications": int,
        "h_index": int,
        "orcid": str
    }
    
    # Check required fields
    for field, expected_type in required_fields.items():
        if field not in researcher_data:
            pytest.fail(f"Missing required field in researcher data: {field}")
        
        if not isinstance(researcher_data[field], expected_type):
            pytest.fail(
                f"Researcher field '{field}': expected {expected_type.__name__}, "
                f"got {type(researcher_data[field]).__name__}"
            )
    
    # Validate email format
    assert_email_format(researcher_data["email"])
    
    # Check expertise list is not empty
    if not researcher_data["expertise"]:
        pytest.fail("Researcher expertise list cannot be empty")


def assert_solicitation_data_structure(solicitation_data: Dict[str, Any]):
    """
    Assert that solicitation data has expected structure for NSF matching.
    
    Args:
        solicitation_data: Solicitation data dictionary
    """
    required_fields = {
        "title": str,
        "description": str,
        "keywords": list
    }
    
    optional_fields = {
        "program": str,
        "deadline": str,
        "budget_range": str,
        "requirements": list
    }
    
    # Check required fields
    for field, expected_type in required_fields.items():
        if field not in solicitation_data:
            pytest.fail(f"Missing required field in solicitation data: {field}")
        
        if not isinstance(solicitation_data[field], expected_type):
            pytest.fail(
                f"Solicitation field '{field}': expected {expected_type.__name__}, "
                f"got {type(solicitation_data[field]).__name__}"
            )
    
    # Check keywords list is not empty
    if not solicitation_data["keywords"]:
        pytest.fail("Solicitation keywords list cannot be empty")


def assert_matching_result_structure(matching_result: Dict[str, Any]):
    """
    Assert that matching result has expected structure.
    
    Args:
        matching_result: Matching result dictionary
    """
    required_fields = {
        "researcher_id": str,
        "score": (int, float),
        "rank": int
    }
    
    optional_fields = {
        "explanation": str,
        "confidence": (int, float),
        "metadata": dict
    }
    
    # Check required fields
    for field, expected_types in required_fields.items():
        if field not in matching_result:
            pytest.fail(f"Missing required field in matching result: {field}")
        
        if not isinstance(matching_result[field], expected_types):
            type_names = [t.__name__ for t in (expected_types if isinstance(expected_types, tuple) else (expected_types,))]
            pytest.fail(
                f"Matching result field '{field}': expected {' or '.join(type_names)}, "
                f"got {type(matching_result[field]).__name__}"
            )
    
    # Validate score range
    assert_numeric_range(matching_result["score"], 0.0, 1.0)
    
    # Validate rank is positive
    if matching_result["rank"] < 1:
        pytest.fail(f"Matching result rank must be positive, got {matching_result['rank']}")


def assert_team_composition_valid(team_data: Dict[str, Any], min_size: int = 2, max_size: int = 10):
    """
    Assert that team composition is valid for NSF proposals.
    
    Args:
        team_data: Team composition data
        min_size: Minimum team size
        max_size: Maximum team size
    """
    if "members" not in team_data:
        pytest.fail("Team data missing 'members' field")
    
    members = team_data["members"]
    team_size = len(members)
    
    if team_size < min_size:
        pytest.fail(f"Team size {team_size} below minimum {min_size}")
    
    if team_size > max_size:
        pytest.fail(f"Team size {team_size} above maximum {max_size}")
    
    # Check for duplicate members
    member_ids = [member.get("id") or member.get("researcher_id") for member in members]
    if len(set(member_ids)) != len(member_ids):
        pytest.fail("Team contains duplicate members")
    
    # Validate each member has required role information
    for i, member in enumerate(members):
        if "role" not in member:
            pytest.fail(f"Team member {i} missing role information")


def assert_api_error_response(response, expected_error_code: str = None):
    """
    Assert that API error response has proper structure.
    
    Args:
        response: HTTP response object
        expected_error_code: Expected error code in response
    """
    # Should not be successful status
    if 200 <= response.status_code < 300:
        pytest.fail(f"Expected error response, got success status {response.status_code}")
    
    try:
        error_data = response.json()
    except Exception:
        pytest.fail("Error response should contain valid JSON")
    
    # Check for standard error fields
    if "detail" not in error_data and "message" not in error_data:
        pytest.fail("Error response missing 'detail' or 'message' field")
    
    if expected_error_code and "code" in error_data:
        if error_data["code"] != expected_error_code:
            pytest.fail(f"Expected error code {expected_error_code}, got {error_data['code']}")