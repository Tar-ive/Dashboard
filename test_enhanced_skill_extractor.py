#!/usr/bin/env python3
"""
Test script for the enhanced skill extraction system.
Tests dual-model validation using the test solicitation PDF.
"""

import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add modules to path
sys.path.append('.')

from modules.enhanced_skill_extractor import EnhancedSkillExtractor
from modules.solicitation_parser import SolicitationParser


def test_enhanced_skill_extraction():
    """Test the enhanced skill extraction system with the test PDF."""
    
    print("🔬 Testing Enhanced Skill Extraction System")
    print("=" * 50)
    
    # Initialize components
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        print(f"✅ GROQ_API_KEY loaded (length: {len(groq_api_key)})")
    else:
        print("⚠️ GROQ_API_KEY not found in environment")
    
    extractor = EnhancedSkillExtractor(groq_api_key=groq_api_key)
    parser = SolicitationParser()
    
    # Test file path
    test_pdf_path = "data/test_solicitation.pdf"
    
    if not Path(test_pdf_path).exists():
        print(f"❌ Test file not found: {test_pdf_path}")
        return
    
    try:
        # Extract text from PDF
        print("📄 Extracting text from PDF...")
        text, file_type = parser.extract_text_from_file(test_pdf_path)
        print(f"✅ Extracted {len(text)} characters from {file_type} file")
        
        # Show sample of text
        print("\n📝 Sample text (first 500 characters):")
        print("-" * 30)
        print(text[:500] + "..." if len(text) > 500 else text)
        print("-" * 30)
        
        # Test dual-model skill extraction
        print("\n🤖 Running dual-model skill extraction...")
        result = extractor.extract_skills_dual_model(text)
        
        # Display results
        print(f"\n✅ Extraction completed in {result.extraction_time:.2f} seconds")
        print(f"📊 Quality Score: {result.quality_score:.2f}")
        print(f"🎯 Source Method: {result.source_method}")
        
        print(f"\n🤖 LLM Skills ({len(result.llm_skills)}):")
        for i, skill in enumerate(result.llm_skills, 1):
            print(f"  {i}. {skill}")
        
        print(f"\n📚 OpenAlex Topics ({len(result.openalex_topics)}):")
        for i, topic in enumerate(result.openalex_topics, 1):
            print(f"  {i}. {topic}")
        
        print(f"\n✨ Merged Skills ({len(result.merged_skills)}):")
        for i, skill in enumerate(result.merged_skills, 1):
            # Show source indicators
            source_indicator = ""
            if skill in result.llm_skills and skill in result.openalex_topics:
                source_indicator = " [BOTH]"
            elif skill in result.llm_skills:
                source_indicator = " [LLM]"
            elif skill in result.openalex_topics:
                source_indicator = " [OpenAlex]"
            
            print(f"  {i}. {skill}{source_indicator}")
        
        # Display quality metrics
        if 'quality_metrics' in result.metadata:
            metrics = result.metadata['quality_metrics']
            print(f"\n📊 Quality Metrics:")
            print(f"  • Skill Count: {metrics['skill_count']}")
            print(f"  • Avg Length: {metrics['avg_skill_length']:.1f} words")
            print(f"  • Atomic Skills: {metrics['atomic_skill_ratio']:.1%}")
            print(f"  • Technical Focus: {metrics['technical_focus_score']:.1%}")
            print(f"  • Uniqueness: {metrics['uniqueness_score']:.1%}")
            print(f"  • Format Compliance: {metrics['format_compliance_score']:.1%}")
        
        # Display confidence scores
        print(f"\n🎯 Confidence Scores:")
        for key, value in result.confidence_scores.items():
            print(f"  • {key.replace('_', ' ').title()}: {value:.1%}")
        
        # Test individual methods
        print(f"\n🧪 Testing Individual Methods:")
        
        # Test LLM extraction only
        print("  Testing LLM extraction...")
        llm_only_skills = extractor.extract_skills_llm(text)
        print(f"    LLM extracted {len(llm_only_skills)} skills")
        
        # Test OpenAlex extraction only
        print("  Testing OpenAlex extraction...")
        openalex_only_skills = extractor.extract_skills_openalex(text)
        print(f"    OpenAlex extracted {len(openalex_only_skills)} skills")
        
        # Test skill quality validation
        print("  Testing skill quality validation...")
        quality_metrics = extractor.validate_skill_quality(result.merged_skills)
        print(f"    Quality validation completed: {quality_metrics.technical_focus_score:.2f} technical focus")
        
        # Performance stats
        print(f"\n📈 Performance Statistics:")
        stats = extractor.get_performance_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  • {key.replace('_', ' ').title()}: {value:.3f}")
            else:
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n✅ Enhanced skill extraction test completed successfully!")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_skill_merging():
    """Test the skill merging algorithm with sample data."""
    
    print("\n🔀 Testing Skill Merging Algorithm")
    print("=" * 40)
    
    extractor = EnhancedSkillExtractor()
    
    # Sample skills for testing
    llm_skills = [
        "Artificial Intelligence Research",
        "Machine Learning Algorithms", 
        "Natural Language Processing",
        "Computer Vision Systems",
        "Deep Learning Networks"
    ]
    
    openalex_topics = [
        "Machine Learning",  # Should merge with "Machine Learning Algorithms"
        "Data Mining Techniques",
        "Neural Network Architecture",
        "Artificial Intelligence",  # Should merge with "Artificial Intelligence Research"
        "Statistical Analysis Methods"
    ]
    
    print("🤖 Sample LLM Skills:")
    for skill in llm_skills:
        print(f"  • {skill}")
    
    print("\n📚 Sample OpenAlex Topics:")
    for topic in openalex_topics:
        print(f"  • {topic}")
    
    # Test merging
    merged = extractor.merge_skill_sources(llm_skills, openalex_topics)
    
    print(f"\n✨ Merged Skills ({len(merged)}):")
    for i, skill in enumerate(merged, 1):
        print(f"  {i}. {skill}")
    
    # Test quality validation
    quality = extractor.validate_skill_quality(merged)
    print(f"\n📊 Merge Quality Metrics:")
    print(f"  • Atomic Skill Ratio: {quality.atomic_skill_ratio:.1%}")
    print(f"  • Technical Focus: {quality.technical_focus_score:.1%}")
    print(f"  • Format Compliance: {quality.format_compliance_score:.1%}")


if __name__ == "__main__":
    # Test enhanced skill extraction
    result = test_enhanced_skill_extraction()
    
    # Test skill merging
    test_skill_merging()
    
    print(f"\n🎉 All tests completed!")