#!/usr/bin/env python3
"""
Test pipeline with 5 Texas State University researchers including topics processing.
This script implements the core data pipeline to fetch, process, and store
researcher data from OpenAlex API into the Supabase database, including standalone topics.
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
        logging.FileHandler('pipeline_test_5_with_topics.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """Track pipeline execution metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.institutions_processed = 0
        self.researchers_processed = 0
        self.works_processed = 0
        self.topics_processed = 0
        self.standalone_topics_processed = 0
        self.grants_processed = 0
        self.errors_encountered = 0
        self.researchers_with_works = 0
        self.works_with_embeddings = 0
        self.works_with_keywords = 0
    
    def get_summary(self) -> Dict:
        """Get pipeline execution summary."""
        duration = time.time() - self.start_time
        
        return {
            "total_runtime_seconds": duration,
            "total_runtime_minutes": duration / 60,
            "records_processed": {
                "institutions": self.institutions_processed,
                "researchers": self.researchers_processed,
                "works": self.works_processed,
                "topics": self.topics_processed,
                "standalone_topics": self.standalone_topics_processed,
                "grants": self.grants_processed
            },
            "quality_metrics": {
                "researchers_with_works": self.researchers_with_works,
                "works_with_embeddings": self.works_with_embeddings,
                "works_with_keywords": self.works_with_keywords,
                "error_rate": self.errors_encountered / max(1, self.works_processed)
            },
            "performance_metrics": {
                "researchers_per_minute": (self.researchers_processed / max(1, duration)) * 60,
                "works_per_minute": (self.works_processed / max(1, duration)) * 60
            }
        }


class ResearcherPipelineWithTopics:
    """Main pipeline for processing researcher data including standalone topics."""
    
    def __init__(self):
        """Initialize pipeline components."""
        # Get configuration from environment
        self.email = os.getenv('OPENALEX_EMAIL', 'test@example.com')
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.openalex_client = OpenAlexClient(email=self.email, rate_limit_delay=0.1)
        self.text_processor = TextProcessor()
        self.data_processor = DataProcessorManager()
        self.metrics = PipelineMetrics()
        
        logger.info("Pipeline initialized successfully")
    
    def connect_database(self):
        """Connect to the database."""
        try:
            self.db_manager.connect()
            logger.info("Database connection established")
            
            # Create standalone topics table if it doesn't exist
            self.db_manager.create_standalone_topics_table()
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def process_standalone_topics(self, limit: int = 100):
        """
        Process standalone topics from OpenAlex.
        
        Args:
            limit: Maximum number of topics to process
        """
        try:
            logger.info(f"Processing up to {limit} standalone topics from OpenAlex...")
            
            count = 0
            for topic_data in self.openalex_client.get_topics(limit=limit):
                try:
                    # Process topic data
                    processed_data = self.data_processor.process_standalone_topic(topic_data)
                    topic_id = self.db_manager.upsert_standalone_topic(processed_data)
                    
                    self.metrics.standalone_topics_processed += 1
                    count += 1
                    
                    logger.info(f"Processed standalone topic {count}/{limit}: {processed_data['name']}")
                    
                    if count >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing topic {topic_data.get('display_name', 'Unknown')}: {e}")
                    self.metrics.errors_encountered += 1
                    continue
            
            logger.info(f"Successfully processed {count} standalone topics")
            
        except Exception as e:
            logger.error(f"Error processing standalone topics: {e}")
            raise
    
    def process_institution(self) -> str:
        """
        Process Texas State University institution data.
        
        Returns:
            Institution database ID
        """
        try:
            logger.info("Processing Texas State University institution...")
            
            # Search for Texas State University
            institution_data = self.openalex_client.search_institution("Texas State University")
            
            if not institution_data:
                raise ValueError("Texas State University not found in OpenAlex")
            
            # Process and store institution
            processed_data = self.data_processor.process_institution(institution_data)
            institution_id = self.db_manager.upsert_institution(processed_data)
            
            self.metrics.institutions_processed += 1
            logger.info(f"Institution processed successfully: {processed_data['name']} (ID: {institution_id})")
            
            return institution_id
            
        except Exception as e:
            logger.error(f"Error processing institution: {e}")
            self.metrics.errors_encountered += 1
            raise
    
    def process_researchers(self, institution_openalex_id: str, limit: int = 5) -> List[str]:
        """
        Process researchers from the institution.
        
        Args:
            institution_openalex_id: OpenAlex ID of the institution
            limit: Maximum number of researchers to process
            
        Returns:
            List of researcher database IDs
        """
        researcher_ids = []
        
        try:
            logger.info(f"Processing up to {limit} researchers from Texas State University...")
            
            # Get institution database ID
            institution_query = "SELECT id FROM institutions WHERE openalex_id = %s;"
            result = self.db_manager.execute_query(institution_query, (institution_openalex_id,), fetch=True)
            
            if not result:
                raise ValueError("Institution not found in database")
            
            institution_db_id = str(result[0]['id'])
            
            # Fetch researchers
            count = 0
            for researcher_data in self.openalex_client.get_researchers_by_institution(institution_openalex_id, limit=limit):
                try:
                    # Process researcher data
                    processed_data = self.data_processor.process_researcher(researcher_data, institution_db_id)
                    researcher_id = self.db_manager.upsert_researcher(processed_data)
                    
                    researcher_ids.append(researcher_id)
                    self.metrics.researchers_processed += 1
                    count += 1
                    
                    logger.info(f"Processed researcher {count}/{limit}: {processed_data['full_name']}")
                    
                    if count >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing researcher {researcher_data.get('display_name', 'Unknown')}: {e}")
                    self.metrics.errors_encountered += 1
                    continue
            
            logger.info(f"Successfully processed {len(researcher_ids)} researchers")
            return researcher_ids
            
        except Exception as e:
            logger.error(f"Error processing researchers: {e}")
            raise
    
    def process_researcher_works(self, researcher_openalex_id: str, researcher_db_id: str, limit: int = None) -> int:
        """
        Process all works for a researcher.
        
        Args:
            researcher_openalex_id: OpenAlex ID of the researcher
            researcher_db_id: Database ID of the researcher
            limit: Maximum number of works to process (None for all)
            
        Returns:
            Number of works processed
        """
        works_count = 0
        
        try:
            # Fetch works for researcher
            for work_data in self.openalex_client.get_works_by_author(researcher_openalex_id):
                try:
                    # Process text content (abstract, keywords, embedding)
                    text_data = self.text_processor.process_work_text(work_data)
                    
                    # Process work data
                    processed_work = self.data_processor.process_work(work_data, researcher_db_id, text_data)
                    work_id = self.db_manager.upsert_work(processed_work)
                    
                    # Process topics
                    topics_data = work_data.get('topics', [])
                    if topics_data:
                        processed_topics = self.data_processor.process_topics(topics_data, work_id)
                        self.db_manager.upsert_topics(work_id, processed_topics)
                        self.metrics.topics_processed += len(processed_topics)
                    
                    # Update metrics
                    works_count += 1
                    self.metrics.works_processed += 1
                    
                    if text_data.get('embedding'):
                        self.metrics.works_with_embeddings += 1
                    
                    if text_data.get('keywords'):
                        self.metrics.works_with_keywords += 1
                    
                    # Check limit
                    if limit and works_count >= limit:
                        logger.info(f"Reached limit of {limit} works for researcher")
                        break
                    
                except Exception as e:
                    logger.error(f"Error processing work {work_data.get('title', 'Unknown')}: {e}")
                    self.metrics.errors_encountered += 1
                    continue
            
            if works_count > 0:
                self.metrics.researchers_with_works += 1
            
            return works_count
            
        except Exception as e:
            logger.error(f"Error processing works for researcher {researcher_openalex_id}: {e}")
            return works_count
    
    def run_pipeline(self, limit: int = 5):
        """
        Run the complete pipeline.
        
        Args:
            limit: Maximum number of researchers to process
        """
        try:
            logger.info(f"Starting pipeline test with {limit} researchers and topics processing")
            
            # Connect to database
            self.connect_database()
            
            # Process standalone topics first
            self.process_standalone_topics(limit=100)
            
            # Process institution
            institution_id = self.process_institution()
            
            # Get institution OpenAlex ID for researcher fetching
            institution_query = "SELECT openalex_id FROM institutions WHERE id = %s;"
            result = self.db_manager.execute_query(institution_query, (institution_id,), fetch=True)
            institution_openalex_id = result[0]['openalex_id']
            
            # Process researchers
            researcher_ids = self.process_researchers(institution_openalex_id, limit)
            
            # Process works for each researcher
            logger.info("Processing works for each researcher...")
            
            for i, researcher_id in enumerate(researcher_ids, 1):
                try:
                    # Get researcher OpenAlex ID
                    researcher_query = "SELECT openalex_id, full_name FROM researchers WHERE id = %s;"
                    result = self.db_manager.execute_query(researcher_query, (researcher_id,), fetch=True)
                    
                    if result:
                        researcher_openalex_id = result[0]['openalex_id']
                        researcher_name = result[0]['full_name']
                        
                        logger.info(f"Processing works for researcher {i}/{len(researcher_ids)}: {researcher_name}")
                        
                        works_count = self.process_researcher_works(researcher_openalex_id, researcher_id)
                        logger.info(f"  Processed {works_count} works")
                        
                except Exception as e:
                    logger.error(f"Error processing works for researcher {researcher_id}: {e}")
                    self.metrics.errors_encountered += 1
                    continue
            
            # Generate final report
            self.generate_report()
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            self.db_manager.close()
    
    def generate_report(self):
        """Generate and display pipeline execution report."""
        try:
            logger.info("Generating pipeline execution report...")
            
            # Get metrics summary
            metrics_summary = self.metrics.get_summary()
            
            # Get database statistics
            db_stats = self.db_manager.get_pipeline_stats()
            
            # Get data quality validation
            quality_validation = self.db_manager.validate_data_quality()
            
            # Print comprehensive report
            print("\n" + "="*80)
            print("PIPELINE EXECUTION REPORT (WITH TOPICS)")
            print("="*80)
            
            print(f"\n📊 EXECUTION METRICS:")
            print(f"  Total Runtime: {metrics_summary['total_runtime_minutes']:.2f} minutes")
            print(f"  Researchers Processed: {metrics_summary['records_processed']['researchers']}")
            print(f"  Works Processed: {metrics_summary['records_processed']['works']}")
            print(f"  Work Topics Processed: {metrics_summary['records_processed']['topics']}")
            print(f"  Standalone Topics Processed: {metrics_summary['records_processed']['standalone_topics']}")
            print(f"  Processing Rate: {metrics_summary['performance_metrics']['researchers_per_minute']:.1f} researchers/min")
            
            print(f"\n📈 DATABASE STATISTICS:")
            print(f"  Institutions: {db_stats.get('institutions', 0)}")
            print(f"  Researchers: {db_stats.get('researchers', 0)}")
            print(f"  Works: {db_stats.get('works', 0)}")
            print(f"  Work Topics: {db_stats.get('topics', 0)}")
            print(f"  Standalone Topics: {db_stats.get('standalone_topics', 0)}")
            print(f"  Grants: {db_stats.get('grants', 0)}")
            
            print(f"\n🔍 DATA QUALITY METRICS:")
            print(f"  Researchers with Works: {quality_validation['researchers_with_works']}/{quality_validation['total_researchers']}")
            print(f"  Works with Abstracts: {quality_validation['works_with_abstracts']}/{db_stats.get('works', 0)}")
            print(f"  Works with Embeddings: {quality_validation['works_with_embeddings']}/{db_stats.get('works', 0)}")
            print(f"  Works with Keywords: {quality_validation['works_with_keywords']}/{db_stats.get('works', 0)}")
            print(f"  Works with Topics: {quality_validation['works_with_topics']}/{db_stats.get('works', 0)}")
            print(f"  Data Quality Score: {quality_validation['data_quality_score']:.1f}/100")
            
            print(f"\n⚠️  ERROR METRICS:")
            print(f"  Total Errors: {self.metrics.errors_encountered}")
            print(f"  Error Rate: {metrics_summary['quality_metrics']['error_rate']:.2%}")
            
            print(f"\n📋 AVERAGES:")
            print(f"  Works per Researcher: {quality_validation['average_works_per_researcher']:.1f}")
            print(f"  Citations per Work: {quality_validation['average_citations_per_work']:.1f}")
            
            # Success criteria evaluation
            print(f"\n✅ SUCCESS CRITERIA EVALUATION:")
            success_criteria = {
                "5 researchers processed": metrics_summary['records_processed']['researchers'] >= 5,
                "All researchers have works": quality_validation['researchers_with_works'] > 0,
                "Works have embeddings": quality_validation['works_with_embeddings'] > 0,
                "Works have keywords": quality_validation['works_with_keywords'] > 0,
                "Topics processed": (metrics_summary['records_processed']['topics'] > 0 or 
                                  metrics_summary['records_processed']['standalone_topics'] > 0),
                "Data quality > 70%": quality_validation['data_quality_score'] > 70,
                "Error rate < 10%": metrics_summary['quality_metrics']['error_rate'] < 0.1
            }
            
            for criterion, passed in success_criteria.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {criterion}: {status}")
            
            overall_success = all(success_criteria.values())
            print(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ NEEDS IMPROVEMENT'}")
            
            print("="*80)
            
            return overall_success
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return False


def main():
    """Main function to run the pipeline test."""
    try:
        # Create and run pipeline
        pipeline = ResearcherPipelineWithTopics()
        pipeline.run_pipeline(limit=5)
        
        logger.info("Pipeline test with topics completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)