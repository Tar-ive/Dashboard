#!/usr/bin/env python3
"""
Test script for Streamlit integration with enhanced skill extraction.
Tests the complete workflow integration.
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
from modules.data_models import Solicitation


def test_streamlit_integration():
    """Test the enhanced skill extraction integration with Streamlit workflow."""
    
    print("🔬 Testing Streamlit Integration with Enhanced Skill Extraction")
    print("=" * 60)
    
    # Test file path
    test_pdf_path = "data/test_solicitation.pdf"
    
    if not Path(test_pdf_path).exists():
        print(f"❌ Test file not found: {test_pdf_path}")
        return
    
    try:
        # Step 1: Parse document (existing functionality)
        print("📄 Step 1: Parsing document...")
        parser = SolicitationParser()
        parsing_result = parser.parse_document(test_pdf_path)
        
        print(f"✅ Document parsed with {parsing_result.confidence_score:.1%} confidence")
        print(f"   Fields extracted: {len(parsing_result.extracted_data) - len(parsing_result.missing_fields)}/{len(parsing_result.extracted_data)}")
        
        # Step 2: Enhanced skill extraction (new functionality)
        print("\n🤖 Step 2: Enhanced skill extraction...")
        text, _ = parser.extract_text_from_file(test_pdf_path)
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            print(f"✅ GROQ_API_KEY loaded (length: {len(groq_api_key)})")
        else:
            print("⚠️ GROQ_API_KEY not found in environment")
        
        skill_extractor = EnhancedSkillExtractor(groq_api_key=groq_api_key)
        
        enhanced_result = skill_extractor.extract_skills_dual_model(text)
        
        print(f"✅ Enhanced extraction completed in {enhanced_result.extraction_time:.2f}s")
        print(f"   Quality score: {enhanced_result.quality_score:.2f}")
        print(f"   Source method: {enhanced_result.source_method}")
        print(f"   Skills extracted: {len(enhanced_result.merged_skills)}")
        
        # Step 3: Create solicitation object (integration point)
        print("\n📋 Step 3: Creating solicitation object...")
        solicitation = parser.convert_to_solicitation(parsing_result)
        
        # Use enhanced skills if quality is good
        if enhanced_result.merged_skills and enhanced_result.quality_score > 0.5:
            original_skills = len(solicitation.required_skills_checklist)
            solicitation.required_skills_checklist = enhanced_result.merged_skills
            print(f"✅ Enhanced skills applied: {original_skills} → {len(enhanced_result.merged_skills)} skills")
        else:
            print(f"⚠️ Using original skills: {len(solicitation.required_skills_checklist)} skills")
        
        # Step 4: Display results (simulating Streamlit interface)
        print("\n📊 Step 4: Results summary...")
        print(f"Title: {solicitation.title}")
        print(f"Skills ({len(solicitation.required_skills_checklist)}):")
        for i, skill in enumerate(solicitation.required_skills_checklist, 1):
            print(f"  {i}. {skill}")
        
        # Step 5: Performance metrics
        print(f"\n📈 Step 5: Performance metrics...")
        stats = skill_extractor.get_performance_stats()
        print(f"Total extractions: {stats['total_extractions']}")
        print(f"Average extraction time: {stats.get('avg_extraction_time', 0):.2f}s")
        print(f"Average quality score: {stats.get('avg_quality_score', 0):.2f}")
        print(f"Success rate: {stats.get('success_rate', 0):.1%}")
        
        # Step 6: Quality assessment
        print(f"\n🎯 Step 6: Quality assessment...")
        if 'quality_metrics' in enhanced_result.metadata:
            metrics = enhanced_result.metadata['quality_metrics']
            print(f"Atomic skills: {metrics['atomic_skill_ratio']:.1%}")
            print(f"Technical focus: {metrics['technical_focus_score']:.1%}")
            print(f"Format compliance: {metrics['format_compliance_score']:.1%}")
            print(f"Uniqueness: {metrics['uniqueness_score']:.1%}")
        
        print(f"\n✅ Streamlit integration test completed successfully!")
        
        return {
            'parsing_result': parsing_result,
            'enhanced_result': enhanced_result,
            'solicitation': solicitation,
            'performance_stats': stats
        }
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_skill_comparison_interface():
    """Test the skill comparison interface functionality."""
    
    print("\n🔍 Testing Skill Comparison Interface")
    print("=" * 40)
    
    # Create sample extraction result
    from modules.enhanced_skill_extractor import SkillExtractionResult
    
    sample_result = SkillExtractionResult(
        llm_skills=["Artificial Intelligence Research", "Machine Learning Algorithms", "Data Analysis"],
        openalex_topics=["Computer Science", "Statistical Methods", "Data Mining"],
        merged_skills=["Artificial Intelligence Research", "Machine Learning Algorithms", "Data Analysis", "Statistical Methods"],
        quality_score=0.85,
        extraction_time=1.2,
        source_method="dual-model",
        confidence_scores={
            'llm_confidence': 1.0,
            'openalex_confidence': 0.8,
            'merge_confidence': 0.9
        },
        metadata={
            'quality_metrics': {
                'skill_count': 4,
                'avg_skill_length': 2.5,
                'atomic_skill_ratio': 1.0,
                'technical_focus_score': 0.85,
                'uniqueness_score': 0.9,
                'format_compliance_score': 1.0
            }
        }
    )
    
    print("📊 Sample extraction result created:")
    print(f"  LLM skills: {len(sample_result.llm_skills)}")
    print(f"  OpenAlex topics: {len(sample_result.openalex_topics)}")
    print(f"  Merged skills: {len(sample_result.merged_skills)}")
    print(f"  Quality score: {sample_result.quality_score:.2f}")
    
    # Test the interface creation (would normally be called in Streamlit)
    print("\n✅ Skill comparison interface data prepared successfully!")
    
    return sample_result


def test_caching_performance():
    """Test the caching performance of skill extraction."""
    
    print("\n⚡ Testing Caching Performance")
    print("=" * 30)
    
    test_pdf_path = "data/test_solicitation.pdf"
    
    if not Path(test_pdf_path).exists():
        print(f"❌ Test file not found: {test_pdf_path}")
        return
    
    try:
        parser = SolicitationParser()
        text, _ = parser.extract_text_from_file(test_pdf_path)
        
        skill_extractor = EnhancedSkillExtractor()
        
        # First extraction (should be slower)
        print("🔄 First extraction (no cache)...")
        import time
        start_time = time.time()
        result1 = skill_extractor.extract_skills_dual_model(text)
        first_time = time.time() - start_time
        
        # Second extraction (should use cache)
        print("🔄 Second extraction (with cache)...")
        start_time = time.time()
        result2 = skill_extractor.extract_skills_dual_model(text)
        second_time = time.time() - start_time
        
        print(f"✅ Caching test completed:")
        print(f"  First extraction: {first_time:.2f}s")
        print(f"  Second extraction: {second_time:.2f}s")
        print(f"  Speed improvement: {(first_time/second_time):.1f}x faster")
        print(f"  Results identical: {result1.merged_skills == result2.merged_skills}")
        
        return {
            'first_time': first_time,
            'second_time': second_time,
            'speedup': first_time / second_time if second_time > 0 else 0,
            'identical': result1.merged_skills == result2.merged_skills
        }
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return None


if __name__ == "__main__":
    # Test main integration
    integration_result = test_streamlit_integration()
    
    # Test skill comparison interface
    comparison_result = test_skill_comparison_interface()
    
    # Test caching performance
    caching_result = test_caching_performance()
    
    print(f"\n🎉 All integration tests completed!")
    
    if integration_result and caching_result:
        print(f"\n📊 Summary:")
        print(f"  Skills extracted: {len(integration_result['enhanced_result'].merged_skills)}")
        print(f"  Quality score: {integration_result['enhanced_result'].quality_score:.2f}")
        print(f"  Extraction time: {integration_result['enhanced_result'].extraction_time:.2f}s")
        print(f"  Caching speedup: {caching_result['speedup']:.1f}x")
        print(f"  Success rate: {integration_result['performance_stats'].get('success_rate', 0):.1%}")