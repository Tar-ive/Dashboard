"""
Test utilities package for NSF Researcher Matching API.

This package provides common utilities, assertions, and helper functions
for testing across all test modules.
"""

from .test_helpers import *
from .assertions import *
from .mock_factories import *
from .accuracy_metrics import *

__all__ = [
    # Test helpers
    'create_test_file',
    'create_test_pdf',
    'create_test_json',
    'generate_test_id',
    'wait_for_condition',
    'retry_on_failure',
    'measure_execution_time',
    'validate_response_structure',
    'extract_error_details',
    
    # Custom assertions
    'assert_http_status',
    'assert_response_structure',
    'assert_json_schema',
    'assert_performance_threshold',
    'assert_accuracy_metrics',
    'assert_file_exists',
    'assert_valid_uuid',
    'assert_datetime_format',
    'assert_numeric_range',
    'assert_list_contains',
    
    # Mock factories
    'MockAIService',
    'MockPDFProcessor',
    'MockDatabaseSession',
    'MockFileSystem',
    'MockHTTPClient',
    'create_mock_researcher',
    'create_mock_solicitation',
    'create_mock_matching_result',
    
    # Accuracy metrics
    'calculate_precision',
    'calculate_recall',
    'calculate_jaccard_similarity',
    'calculate_f1_score',
    'calculate_role_based_accuracy',
    'AccuracyCalculator',
    'GroundTruthValidator'
]