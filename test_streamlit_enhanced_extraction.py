#!/usr/bin/env python3
"""
Quick test to verify enhanced skill extraction is working in Streamlit context.
"""

import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add modules to path
sys.path.append('.')

def test_enhanced_extraction_integration():
    """Test that enhanced extraction works as expected in the Streamlit workflow."""
    
    print("🧪 Testing Enhanced Skill Extraction Integration")
    print("=" * 50)
    
    # Test environment setup
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        print(f"✅ GROQ_API_KEY loaded (length: {len(groq_api_key)})")
    else:
        print("❌ GROQ_API_KEY not found")
        return False
    
    # Test imports
    try:
        from modules.enhanced_skill_extractor import EnhancedSkillExtractor
        from modules.solicitation_parser import SolicitationParser
        print("✅ All modules imported successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test initialization
    try:
        skill_extractor = EnhancedSkillExtractor(groq_api_key=groq_api_key)
        parser = SolicitationParser()
        print("✅ Components initialized successfully")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False
    
    # Test with sample text (simulating document upload)
    sample_text = """
    This NSF solicitation seeks proposals for artificial intelligence research 
    focusing on machine learning algorithms, natural language processing, 
    computer vision systems, and deep learning networks. Projects should 
    demonstrate expertise in data science, statistical analysis, and 
    algorithm development.
    """
    
    try:
        print("\n🤖 Testing enhanced skill extraction...")
        result = skill_extractor.extract_skills_dual_model(sample_text)
        
        print(f"✅ Extraction completed successfully!")
        print(f"   Skills found: {len(result.merged_skills)}")
        print(f"   Quality score: {result.quality_score:.2f}")
        print(f"   Source method: {result.source_method}")
        print(f"   Extraction time: {result.extraction_time:.2f}s")
        
        print(f"\n📋 Extracted skills:")
        for i, skill in enumerate(result.merged_skills, 1):
            print(f"   {i}. {skill}")
        
        # Test the display function components
        print(f"\n🎨 Testing display components...")
        
        # Test that we can create the comparison interface data
        if result.llm_skills:
            print(f"   ✅ LLM skills: {len(result.llm_skills)} found")
        if result.openalex_topics:
            print(f"   ✅ OpenAlex topics: {len(result.openalex_topics)} found")
        if result.merged_skills:
            print(f"   ✅ Merged skills: {len(result.merged_skills)} found")
        
        return True
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_workflow_simulation():
    """Simulate the Streamlit workflow to identify potential issues."""
    
    print("\n🔄 Simulating Streamlit Workflow")
    print("=" * 40)
    
    # Check if test PDF exists
    test_pdf_path = "data/test_solicitation.pdf"
    if not Path(test_pdf_path).exists():
        print(f"⚠️ Test PDF not found: {test_pdf_path}")
        print("   Using sample text instead...")
        
        # Use sample text
        sample_text = """
        SBIR Phase I: AI-Powered Cybersecurity Threat Detection
        
        This project develops artificial intelligence systems for cybersecurity 
        threat detection using machine learning algorithms, natural language 
        processing for threat intelligence, and computer vision for network 
        traffic analysis. The research requires expertise in deep learning, 
        statistical modeling, and algorithm optimization.
        """
        
        from modules.enhanced_skill_extractor import EnhancedSkillExtractor
        
        try:
            print("📄 Processing sample solicitation text...")
            skill_extractor = EnhancedSkillExtractor()
            result = skill_extractor.extract_skills_dual_model(sample_text)
            
            print(f"✅ Workflow simulation successful!")
            print(f"   This is what users should see in Streamlit:")
            print(f"   - Skills extracted: {len(result.merged_skills)}")
            print(f"   - Quality score: {result.quality_score:.2f}")
            print(f"   - Processing time: {result.extraction_time:.2f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Workflow simulation failed: {e}")
            return False
    
    else:
        print(f"✅ Test PDF found: {test_pdf_path}")
        
        try:
            from modules.solicitation_parser import SolicitationParser
            from modules.enhanced_skill_extractor import EnhancedSkillExtractor
            
            # Parse the PDF (like Streamlit does)
            parser = SolicitationParser()
            text, file_type = parser.extract_text_from_file(test_pdf_path)
            print(f"📄 Extracted {len(text)} characters from {file_type}")
            
            # Run enhanced extraction (like Streamlit does)
            skill_extractor = EnhancedSkillExtractor()
            result = skill_extractor.extract_skills_dual_model(text)
            
            print(f"✅ Full workflow simulation successful!")
            print(f"   Users should see:")
            print(f"   - 🤖 Enhanced Skill Extraction Results section")
            print(f"   - {len(result.merged_skills)} skills extracted")
            print(f"   - Quality score: {result.quality_score:.2f}")
            print(f"   - Detailed comparison expandable section")
            
            return True
            
        except Exception as e:
            print(f"❌ Full workflow simulation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Testing Enhanced Skill Extraction for Streamlit Integration")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_enhanced_extraction_integration()
    test2_passed = test_streamlit_workflow_simulation()
    
    print(f"\n📊 Test Results:")
    print(f"   Enhanced Extraction: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Streamlit Workflow: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 All tests passed! Enhanced extraction should work in Streamlit.")
        print(f"   When you upload a document, you should see:")
        print(f"   1. 🚀 NEW FEATURE message")
        print(f"   2. 🤖 Running enhanced skill extraction spinner")
        print(f"   3. ✅ GROQ API key loaded message")
        print(f"   4. 🎉 Enhanced extraction completed message")
        print(f"   5. 🤖 ENHANCED AI SKILL EXTRACTION RESULTS section")
        print(f"   6. Enhanced extraction status in sidebar")
    else:
        print(f"\n❌ Some tests failed. Check the errors above.")