#!/usr/bin/env python3
"""
Validate pipeline data quality and completeness.
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database.database_manager import DatabaseManager

# Load environment variables
load_dotenv()


def validate_data():
    """Validate the current data in the database."""
    db_manager = DatabaseManager()
    db_manager.connect()
    
    try:
        print("="*80)
        print("DATABASE VALIDATION REPORT")
        print("="*80)
        
        # Get basic stats
        stats = db_manager.get_pipeline_stats()
        validation = db_manager.validate_data_quality()
        
        print(f"\n📊 BASIC STATISTICS:")
        print(f"  Institutions: {stats['institutions']}")
        print(f"  Researchers: {stats['researchers']}")
        print(f"  Works: {stats['works']}")
        print(f"  Topics: {stats['topics']}")
        print(f"  Grants: {stats['grants']}")
        
        print(f"\n🔍 DATA QUALITY:")
        print(f"  Works with Abstracts: {validation['works_with_abstracts']}/{stats['works']} ({validation['works_with_abstracts']/max(1,stats['works'])*100:.1f}%)")
        print(f"  Works with Embeddings: {validation['works_with_embeddings']}/{stats['works']} ({validation['works_with_embeddings']/max(1,stats['works'])*100:.1f}%)")
        print(f"  Works with Keywords: {validation['works_with_keywords']}/{stats['works']} ({validation['works_with_keywords']/max(1,stats['works'])*100:.1f}%)")
        print(f"  Works with Topics: {validation['works_with_topics']}/{stats['works']} ({validation['works_with_topics']/max(1,stats['works'])*100:.1f}%)")
        print(f"  Overall Quality Score: {validation['data_quality_score']:.1f}/100")
        
        print(f"\n📈 RESEARCH METRICS:")
        print(f"  Researchers with Works: {validation['researchers_with_works']}/{validation['total_researchers']}")
        print(f"  Average Works per Researcher: {validation['average_works_per_researcher']:.1f}")
        print(f"  Average Citations per Work: {validation['average_citations_per_work']:.1f}")
        
        # Sample data queries
        print(f"\n📋 SAMPLE DATA:")
        
        # Top researchers by work count
        top_researchers = db_manager.execute_query("""
            SELECT r.full_name, COUNT(w.id) as work_count, SUM(w.citations) as total_citations
            FROM researchers r
            LEFT JOIN works w ON r.id = w.researcher_id
            GROUP BY r.id, r.full_name
            ORDER BY work_count DESC
            LIMIT 5;
        """, fetch=True)
        
        print(f"  Top 5 Researchers by Work Count:")
        for researcher in top_researchers:
            print(f"    {researcher['full_name']}: {researcher['work_count']} works, {researcher['total_citations']} citations")
        
        # Recent works with embeddings
        recent_works = db_manager.execute_query("""
            SELECT w.title, w.publication_year, w.citations, r.full_name,
                   CASE WHEN w.embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding,
                   CASE WHEN w.keywords IS NOT NULL AND w.keywords != '[]' THEN 'Yes' ELSE 'No' END as has_keywords
            FROM works w
            JOIN researchers r ON w.researcher_id = r.id
            WHERE w.publication_year >= 2020
            ORDER BY w.publication_year DESC, w.citations DESC
            LIMIT 5;
        """, fetch=True)
        
        print(f"\n  Recent High-Impact Works (2020+):")
        for work in recent_works:
            print(f"    {work['title'][:60]}... ({work['publication_year']})")
            print(f"      Author: {work['full_name']}, Citations: {work['citations']}")
            print(f"      Embedding: {work['has_embedding']}, Keywords: {work['has_keywords']}")
        
        # Keywords sample
        keyword_sample = db_manager.execute_query("""
            SELECT w.title, w.keywords
            FROM works w
            WHERE w.keywords IS NOT NULL AND w.keywords != '[]'
            LIMIT 3;
        """, fetch=True)
        
        print(f"\n  Sample Keywords:")
        for work in keyword_sample:
            print(f"    {work['title'][:50]}...")
            print(f"      Keywords: {work['keywords']}")
        
        print("="*80)
        
        # Determine if ready for 50 researcher test
        ready_for_full_test = (
            stats['researchers'] >= 5 and
            stats['works'] >= 20 and
            validation['works_with_embeddings'] > 0 and
            validation['works_with_keywords'] > 0
        )
        
        if ready_for_full_test:
            print("✅ READY FOR FULL 50 RESEARCHER TEST")
            print("The pipeline is working correctly with embeddings and keywords.")
        else:
            print("❌ NOT READY FOR FULL TEST")
            print("Please fix issues before running the full 50 researcher test.")
        
        return ready_for_full_test
        
    finally:
        db_manager.close()


if __name__ == "__main__":
    validate_data()