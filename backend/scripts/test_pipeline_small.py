#!/usr/bin/env python3
"""
Small test pipeline with 5 Texas State University researchers.
This script validates the core functionality before running the full 50 researcher test.
"""
import os
import sys
import time
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database.database_manager import DatabaseManager
from app.services.openalex_client import OpenAlexClient
from app.services.text_processor import TextProcessor
from app.services.data_processors import DataProcessorManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_small_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_components():
    """Test individual components before running the full pipeline."""
    logger.info("Testing individual components...")
    
    # Test database connection
    try:
        db_manager = DatabaseManager()
        db_manager.connect()
        logger.info("✅ Database connection successful")
        db_manager.close()
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    
    # Test OpenAlex client
    try:
        email = os.getenv('OPENALEX_EMAIL', 'test@example.com')
        client = OpenAlexClient(email=email, rate_limit_delay=0.1)
        institution = client.search_institution("Texas State University")
        if institution:
            logger.info(f"✅ OpenAlex client successful: Found {institution.get('display_name')}")
        else:
            logger.error("❌ OpenAlex client failed: Institution not found")
            return False
    except Exception as e:
        logger.error(f"❌ OpenAlex client failed: {e}")
        return False
    
    # Test text processor
    try:
        processor = TextProcessor()
        test_text = "This is a test abstract about machine learning and artificial intelligence."
        keywords = processor.extract_keywords(test_text)
        embedding = processor.generate_embedding(test_text)
        
        if keywords and embedding:
            logger.info(f"✅ Text processor successful: {len(keywords)} keywords, {len(embedding)} dim embedding")
        else:
            logger.error("❌ Text processor failed: No keywords or embedding generated")
            return False
    except Exception as e:
        logger.error(f"❌ Text processor failed: {e}")
        return False
    
    logger.info("All components tested successfully!")
    return True


def run_small_pipeline():
    """Run pipeline with 5 researchers."""
    try:
        logger.info("Starting small pipeline test with 5 researchers...")
        
        # Initialize components
        email = os.getenv('OPENALEX_EMAIL', 'test@example.com')
        db_manager = DatabaseManager()
        openalex_client = OpenAlexClient(email=email, rate_limit_delay=0.1)
        text_processor = TextProcessor()
        data_processor = DataProcessorManager()
        
        # Connect to database
        db_manager.connect()
        
        # Process institution
        logger.info("Processing Texas State University...")
        institution_data = openalex_client.search_institution("Texas State University")
        
        if not institution_data:
            raise ValueError("Texas State University not found")
        
        processed_institution = data_processor.process_institution(institution_data)
        institution_id = db_manager.upsert_institution(processed_institution)
        institution_openalex_id = institution_data['id']
        
        logger.info(f"Institution processed: {processed_institution['name']}")
        
        # Process 5 researchers
        logger.info("Processing 5 researchers...")
        researcher_count = 0
        total_works = 0
        
        for researcher_data in openalex_client.get_researchers_by_institution(institution_openalex_id, limit=5):
            try:
                researcher_count += 1
                
                # Process researcher
                processed_researcher = data_processor.process_researcher(researcher_data, institution_id)
                researcher_id = db_manager.upsert_researcher(processed_researcher)
                
                logger.info(f"Researcher {researcher_count}: {processed_researcher['full_name']}")
                
                # Process works for this researcher (limit to 10 works per researcher for testing)
                works_count = 0
                researcher_openalex_id = researcher_data['id']
                
                for work_data in openalex_client.get_works_by_author(researcher_openalex_id):
                    try:
                        # Process text content
                        text_data = text_processor.process_work_text(work_data)
                        
                        # Process work
                        processed_work = data_processor.process_work(work_data, researcher_id, text_data)
                        work_id = db_manager.upsert_work(processed_work)
                        
                        # Process topics
                        topics_data = work_data.get('topics', [])
                        if topics_data:
                            processed_topics = data_processor.process_topics(topics_data, work_id)
                            db_manager.upsert_topics(work_id, processed_topics)
                        
                        works_count += 1
                        total_works += 1
                        
                        # Limit works per researcher for testing
                        if works_count >= 10:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing work: {e}")
                        continue
                
                logger.info(f"  Processed {works_count} works")
                
            except Exception as e:
                logger.error(f"Error processing researcher: {e}")
                continue
        
        # Generate report
        logger.info("Generating test report...")
        stats = db_manager.get_pipeline_stats()
        validation = db_manager.validate_data_quality()
        
        print("\n" + "="*60)
        print("SMALL PIPELINE TEST REPORT")
        print("="*60)
        print(f"Researchers Processed: {researcher_count}")
        print(f"Total Works: {total_works}")
        print(f"Database Stats: {stats}")
        print(f"Data Quality Score: {validation['data_quality_score']:.1f}/100")
        print(f"Works with Embeddings: {validation['works_with_embeddings']}")
        print(f"Works with Keywords: {validation['works_with_keywords']}")
        print("="*60)
        
        # Success criteria
        success = (
            researcher_count >= 5 and
            total_works > 0 and
            validation['works_with_embeddings'] > 0
        )
        
        result = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"Overall Result: {result}")
        
        db_manager.close()
        return success
        
    except Exception as e:
        logger.error(f"Small pipeline test failed: {e}")
        return False


def main():
    """Main function."""
    print("Running small pipeline test...")
    
    # Test components first
    if not test_components():
        print("Component tests failed. Exiting.")
        return False
    
    # Run small pipeline
    success = run_small_pipeline()
    
    if success:
        print("\n✅ Small pipeline test completed successfully!")
        print("You can now run the full 50 researcher test.")
    else:
        print("\n❌ Small pipeline test failed.")
        print("Please check the logs and fix issues before running the full test.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)