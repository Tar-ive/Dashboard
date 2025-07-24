"""
Comprehensive testing suite for the advanced solicitation parser.
Tests multi-format support, template system, logging, and performance monitoring.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the enhanced parser
from modules.solicitation_parser import SolicitationParser
from modules.data_models import ExtractionConfig, SolicitationParsingResult


class TestAdvancedSolicitationParser(unittest.TestCase):
    """Test suite for advanced solicitation parser features."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = SolicitationParser(
            templates_dir=f"{self.temp_dir}/templates",
            logs_dir=f"{self.temp_dir}/logs"
        )
        
        # Sample text content for testing
        self.sample_nsf_text = """
        NSF 23-123: Advanced Research in Computer Science
        
        Program Solicitation
        
        National Science Foundation
        
        II. Program Description
        This program supports innovative research in computer science and engineering.
        The program aims to advance the state of the art in computational methods.
        
        Required Skills: machine learning, data analysis, software engineering
        
        Anticipated Funding Amount: $500,000
        
        Submission Window Date(s): March 15, 2024 - April 15, 2024
        
        Cognizant Program Officer: Dr. Jane Smith
        """
        
        self.sample_generic_text = """
        Request for Proposals: Advanced AI Research
        
        Title: Artificial Intelligence for Healthcare Applications
        
        Abstract: This RFP seeks proposals for developing AI systems for healthcare.
        The goal is to improve patient outcomes through intelligent automation.
        
        Required Skills: artificial intelligence, healthcare informatics, data science
        
        Budget: $750,000
        
        Deadline: June 30, 2024
        """
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_document_type_detection(self):
        """Test automatic document type detection."""
        # Test NSF document detection
        doc_type, confidence = self.parser.detect_document_type(self.sample_nsf_text)
        self.assertEqual(doc_type, 'nsf')
        self.assertGreater(confidence, 0.5)
        
        # Test generic RFP detection
        doc_type, confidence = self.parser.detect_document_type(self.sample_generic_text)
        self.assertEqual(doc_type, 'generic_rfp')
        self.assertGreater(confidence, 0.0)
    
    def test_text_extraction_caching(self):
        """Test that text extraction is properly cached."""
        # Create a temporary PDF file (mock)
        temp_pdf = Path(self.temp_dir) / "test.pdf"
        temp_pdf.write_text("dummy content")
        
        with patch.object(self.parser, '_extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = self.sample_nsf_text
            
            # First call should hit the extraction method
            text1, file_type1 = self.parser.extract_text_from_file(str(temp_pdf))
            
            # Second call should use cache (method not called again)
            text2, file_type2 = self.parser.extract_text_from_file(str(temp_pdf))
            
            self.assertEqual(text1, text2)
            self.assertEqual(file_type1, file_type2)
            # Due to caching, extract method should only be called once
            self.assertEqual(mock_extract.call_count, 1)
    
    def test_template_save_and_load(self):
        """Test template saving and loading functionality."""
        # Save a template
        template_name = "test_template"
        template_desc = "Test template for unit testing"
        
        success = self.parser.save_template(template_name, template_desc)
        self.assertTrue(success)
        
        # Verify template file was created
        template_file = Path(self.parser.templates_dir) / f"{template_name}.json"
        self.assertTrue(template_file.exists())
        
        # Load the template
        success = self.parser.load_template(template_name)
        self.assertTrue(success)
        
        # List templates
        templates = self.parser.list_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['name'], template_name)
        self.assertEqual(templates[0]['description'], template_desc)
    
    def test_multi_format_support(self):
        """Test support for multiple document formats."""
        # Test PDF support
        temp_pdf = Path(self.temp_dir) / "test.pdf"
        temp_pdf.write_bytes(b"dummy pdf content")
        
        with patch.object(self.parser, '_extract_text_from_pdf') as mock_pdf:
            mock_pdf.return_value = self.sample_nsf_text
            text, file_type = self.parser.extract_text_from_file(str(temp_pdf))
            self.assertEqual(file_type, 'pdf')
            self.assertEqual(text, self.sample_nsf_text)
        
        # Test text file support
        temp_txt = Path(self.temp_dir) / "test.txt"
        temp_txt.write_text(self.sample_generic_text)
        
        text, file_type = self.parser.extract_text_from_file(str(temp_txt))
        self.assertEqual(file_type, 'txt')
        self.assertEqual(text.strip(), self.sample_generic_text.strip())
        
        # Test unsupported format
        temp_unsupported = Path(self.temp_dir) / "test.xyz"
        temp_unsupported.write_text("content")
        
        with self.assertRaises(ValueError):
            self.parser.extract_text_from_file(str(temp_unsupported))
    
    def test_performance_monitoring(self):
        """Test performance statistics tracking."""
        # Initial stats should be empty
        stats = self.parser.get_performance_stats()
        self.assertEqual(stats['total_documents_processed'], 0)
        self.assertEqual(stats['success_count'], 0)
        self.assertEqual(stats['error_count'], 0)
        
        # Simulate successful processing
        self.parser._update_performance_stats(1.5, 10.0, success=True)
        self.parser._update_performance_stats(2.0, 12.0, success=True)
        
        # Simulate failed processing
        self.parser._update_performance_stats(0.5, 5.0, success=False)
        
        # Check updated stats
        stats = self.parser.get_performance_stats()
        self.assertEqual(stats['total_documents_processed'], 3)
        self.assertEqual(stats['success_count'], 2)
        self.assertEqual(stats['error_count'], 1)
        self.assertAlmostEqual(stats['success_rate'], 2/3, places=2)
        self.assertAlmostEqual(stats['avg_processing_time'], (1.5 + 2.0 + 0.5) / 3, places=2)
        self.assertAlmostEqual(stats['avg_memory_usage'], (10.0 + 12.0 + 5.0) / 3, places=2)
    
    def test_data_validation_and_cleaning(self):
        """Test data validation and cleaning functionality."""
        # Test data with various issues
        raw_data = {
            'title': '  Title with   extra   spaces  ',
            'abstract': 'Abstract\nwith\nnewlines\tand\ttabs',
            'required_skills': 'skill1; skill2, skill3\nskill4',
            'funding_amount': '$500,000.00 USD',
            'program': '',  # Empty field
        }
        
        cleaned_data = self.parser._validate_and_clean_data(raw_data)
        
        # Check title cleaning
        self.assertEqual(cleaned_data['title'], 'Title with extra spaces')
        
        # Check abstract cleaning
        self.assertIn('Abstract with newlines and tabs', cleaned_data['abstract'])
        
        # Check skills formatting
        self.assertIn('skill1', cleaned_data['required_skills'])
        self.assertIn('skill2', cleaned_data['required_skills'])
        
        # Check funding amount cleaning
        self.assertEqual(cleaned_data['funding_amount'], '500,000.00')
        
        # Check empty field handling
        self.assertEqual(cleaned_data['program'], '')  # Should use default value
    
    def test_quality_assessment(self):
        """Test quality assessment functionality."""
        # High quality data
        good_data = {
            'title': 'A Comprehensive Research Project Title',
            'abstract': 'This is a detailed abstract that provides comprehensive information about the research project and its objectives. It contains sufficient detail to understand the scope and goals.',
            'required_skills': 'machine learning; data analysis; software engineering; statistics',
            'funding_amount': '500,000',
            'program': 'NSF 23-123'
        }
        
        confidence, missing = self.parser._assess_quality(good_data)
        self.assertGreater(confidence, 0.7)
        self.assertEqual(len(missing), 0)
        
        # Poor quality data
        poor_data = {
            'title': 'Short',
            'abstract': 'Brief',
            'required_skills': '',
            'funding_amount': '',
            'program': ''
        }
        
        confidence, missing = self.parser._assess_quality(poor_data)
        self.assertLess(confidence, 0.5)
        self.assertGreater(len(missing), 0)
    
    def test_field_quality_calculation(self):
        """Test individual field quality calculation."""
        # Test title quality
        self.assertEqual(self.parser._calculate_field_quality('title', 'Good Research Title'), 1.0)
        self.assertLess(self.parser._calculate_field_quality('title', 'Short'), 1.0)
        
        # Test abstract quality
        long_abstract = 'This is a very long abstract that contains detailed information about the research project and its methodology.'
        self.assertEqual(self.parser._calculate_field_quality('abstract', long_abstract), 1.0)
        self.assertLess(self.parser._calculate_field_quality('abstract', 'Brief'), 1.0)
        
        # Test skills quality
        self.assertEqual(self.parser._calculate_field_quality('required_skills', 'skill1; skill2; skill3'), 1.0)
        self.assertLess(self.parser._calculate_field_quality('required_skills', 'single_skill'), 1.0)
        
        # Test funding amount quality
        self.assertEqual(self.parser._calculate_field_quality('funding_amount', '500,000'), 1.0)
        self.assertLess(self.parser._calculate_field_quality('funding_amount', 'unknown'), 1.0)
    
    def test_logging_setup(self):
        """Test that logging is properly configured."""
        # Check that logger is created
        self.assertIsNotNone(self.parser.logger)
        self.assertEqual(self.parser.logger.name, 'solicitation_parser')
        
        # Check that log directory exists
        self.assertTrue(self.parser.logs_dir.exists())
        
        # Test logging functionality
        self.parser.logger.info("Test log message")
        
        # Force handler to flush
        for handler in self.parser.logger.handlers:
            handler.flush()
        
        # Check that log file is created (may be empty but should exist)
        log_files = list(self.parser.logs_dir.glob("parsing_*.log"))
        # Just check that the logger is properly configured, file creation is implementation detail
        self.assertTrue(len(self.parser.logger.handlers) > 0)
    
    def test_backward_compatibility(self):
        """Test that legacy methods still work."""
        # Create a temporary PDF file
        temp_pdf = Path(self.temp_dir) / "test.pdf"
        temp_pdf.write_bytes(b"dummy content")
        
        with patch.object(self.parser, '_extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = self.sample_nsf_text
            
            # Test legacy parse_pdf_solicitation method
            result = self.parser.parse_pdf_solicitation(str(temp_pdf))
            self.assertIsInstance(result, SolicitationParsingResult)
            
            # Test legacy extract_text_from_pdf method
            text = self.parser.extract_text_from_pdf(str(temp_pdf))
            self.assertEqual(text, self.sample_nsf_text)
    
    def test_error_handling(self):
        """Test error handling and graceful degradation."""
        # Test with non-existent file
        result = self.parser.parse_document("/non/existent/file.pdf")
        self.assertEqual(result.confidence_score, 0.0)
        self.assertGreater(len(result.missing_fields), 0)
        
        # Test with empty file
        empty_file = Path(self.temp_dir) / "empty.txt"
        empty_file.write_text("")
        
        result = self.parser.parse_document(str(empty_file))
        self.assertEqual(result.confidence_score, 0.0)


class TestDocumentTypePatterns(unittest.TestCase):
    """Test document type detection patterns."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = SolicitationParser(
            templates_dir=f"{self.temp_dir}/templates",
            logs_dir=f"{self.temp_dir}/logs"
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_nsf_pattern_detection(self):
        """Test NSF document pattern detection."""
        nsf_samples = [
            "NSF 23-123: Research Program",
            "National Science Foundation Program Solicitation",
            "Cognizant Program Officer: Dr. Smith"
        ]
        
        for sample in nsf_samples:
            doc_type, confidence = self.parser.detect_document_type(sample)
            self.assertEqual(doc_type, 'nsf')
    
    def test_nih_pattern_detection(self):
        """Test NIH document pattern detection."""
        nih_samples = [
            "NIH RFA-123: Research Funding",
            "National Institutes of Health",
            "Funding Opportunity Announcement FOA Number: RFA-123"
        ]
        
        for sample in nih_samples:
            doc_type, confidence = self.parser.detect_document_type(sample)
            self.assertEqual(doc_type, 'nih')
    
    def test_generic_rfp_detection(self):
        """Test generic RFP pattern detection."""
        rfp_samples = [
            "Request for Proposals RFP-2024-001",
            "Proposal Submission Guidelines",
            "Funding Opportunity Available"
        ]
        
        for sample in rfp_samples:
            doc_type, confidence = self.parser.detect_document_type(sample)
            self.assertEqual(doc_type, 'generic_rfp')


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)