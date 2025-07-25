#!/usr/bin/env python3
"""
Complete end-to-end workflow test for PDF parsing integration.
Tests the full pipeline from PDF upload through team assembly.
"""

import sys
import os
from pathlib import Path

# Add modules to path
sys.path.append('.')

from modules.solicitation_parser import SolicitationParser
from modules.data_loader import DataLoader
from modules.matcher import ResearcherMatcher
from modules.team_builder import TeamBuilder
from modules.data_models import Solicitation


def test_complete_workflow():
    """Test the complete workflow from PDF to team assembly."""
    
    print("🚀 Testing Complete PDF-to-Team Workflow")
    print("=" * 50)
    
    # Step 1: PDF Parsing
    print("\n📄 Step 1: PDF Parsing")
    try:
        parser = SolicitationParser()
        parsing_result = parser.parse_pdf_solicitation('data/test_solicitation.pdf')
        solicitation = parser.convert_to_solicitation(parsing_result)
        
        print(f"   ✅ PDF parsed successfully")
        print(f"   📊 Confidence: {parsing_result.confidence_score:.2%}")
        print(f"   📝 Title: {solicitation.title}")
        print(f"   🎯 Skills: {len(solicitation.required_skills_checklist)}")
        
    except Exception as e:
        print(f"   ❌ PDF parsing failed: {str(e)}")
        return False
    
    # Step 2: Data Loading (System Initialization)
    print("\n🔧 Step 2: System Initialization")
    try:
        data_loader = DataLoader("./data")
        all_data = data_loader.get_all_data()
        
        print(f"   ✅ Data loaded successfully")
        print(f"   👥 Researchers: {len(all_data['data']['researcher_vectors'])}")
        print(f"   📚 Papers: {len(all_data['data']['conceptual_profiles'])}")
        
    except Exception as e:
        print(f"   ❌ Data loading failed: {str(e)}")
        return False
    
    # Step 3: Researcher Matching
    print("\n🔍 Step 3: Researcher Matching")
    try:
        matcher = ResearcherMatcher()
        matching_results = matcher.search_researchers(
            solicitation,
            all_data['models'],
            all_data['data'],
            top_k=50
        )
        
        print(f"   ✅ Matching completed successfully")
        print(f"   🎯 Top matches: {len(matching_results.top_matches)}")
        print(f"   ✅ Eligible researchers: {matching_results.eligible_researchers}")
        print(f"   ⏱️  Processing time: {matching_results.processing_time_seconds:.2f}s")
        
    except Exception as e:
        print(f"   ❌ Researcher matching failed: {str(e)}")
        return False
    
    # Step 4: Team Assembly
    print("\n🏗️ Step 4: Team Assembly")
    try:
        team_builder = TeamBuilder()
        team_results = team_builder.assemble_team(
            matching_results,
            all_data['models'],
            all_data['data'],
            max_team_size=6
        )
        
        print(f"   ✅ Team assembled successfully")
        print(f"   👥 Team size: {len(team_results.team_members)}")
        print(f"   📊 Coverage score: {team_results.overall_coverage_score:.2%}")
        
        # Show team members
        print(f"   🏆 Team members:")
        for i, member in enumerate(team_results.team_members[:3], 1):
            print(f"      {i}. {member['name']} (Score: {member['final_affinity_score']:.3f})")
        if len(team_results.team_members) > 3:
            print(f"      ... and {len(team_results.team_members) - 3} more")
        
    except Exception as e:
        print(f"   ❌ Team assembly failed: {str(e)}")
        return False
    
    # Step 5: Workflow Validation
    print("\n✅ Step 5: Workflow Validation")
    
    # Validate that PDF data flows correctly through the pipeline
    validation_checks = [
        ("Solicitation title preserved", bool(solicitation.title)),
        ("Skills extracted and used", len(solicitation.required_skills_checklist) > 0),
        ("Matching found candidates", len(matching_results.top_matches) > 0),
        ("Team assembled", len(team_results.team_members) > 0),
        ("Coverage achieved", team_results.overall_coverage_score > 0),
        ("Parsing metadata preserved", solicitation.parsing_metadata is not None)
    ]
    
    passed_checks = 0
    for check_name, check_result in validation_checks:
        if check_result:
            print(f"   ✅ {check_name}")
            passed_checks += 1
        else:
            print(f"   ❌ {check_name}")
    
    print(f"\n📊 Validation Results: {passed_checks}/{len(validation_checks)} checks passed")
    
    if passed_checks == len(validation_checks):
        print("🎉 Complete workflow validation successful!")
        return True
    else:
        print("⚠️  Some validation checks failed")
        return False


def test_data_quality():
    """Test the quality of data flowing through the pipeline."""
    
    print("\n🔍 Testing Data Quality Through Pipeline")
    print("-" * 40)
    
    # Parse PDF
    parser = SolicitationParser()
    parsing_result = parser.parse_pdf_solicitation('data/test_solicitation.pdf')
    solicitation = parser.convert_to_solicitation(parsing_result)
    
    # Quality checks
    quality_checks = []
    
    # Title quality
    if solicitation.title and len(solicitation.title) > 10:
        quality_checks.append(("Title quality", True, f"Length: {len(solicitation.title)} chars"))
    else:
        quality_checks.append(("Title quality", False, "Too short or missing"))
    
    # Abstract quality
    if solicitation.abstract and len(solicitation.abstract) > 50:
        quality_checks.append(("Abstract quality", True, f"Length: {len(solicitation.abstract)} chars"))
    else:
        quality_checks.append(("Abstract quality", False, "Too short or missing"))
    
    # Skills quality
    if solicitation.required_skills_checklist and len(solicitation.required_skills_checklist) >= 3:
        quality_checks.append(("Skills quality", True, f"Count: {len(solicitation.required_skills_checklist)}"))
    else:
        quality_checks.append(("Skills quality", False, "Too few skills extracted"))
    
    # Confidence score
    if parsing_result.confidence_score > 0.7:
        quality_checks.append(("Extraction confidence", True, f"Score: {parsing_result.confidence_score:.2%}"))
    else:
        quality_checks.append(("Extraction confidence", False, f"Low score: {parsing_result.confidence_score:.2%}"))
    
    # Display results
    passed_quality = 0
    for check_name, passed, details in quality_checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}: {details}")
        if passed:
            passed_quality += 1
    
    print(f"\n📊 Quality Results: {passed_quality}/{len(quality_checks)} checks passed")
    return passed_quality == len(quality_checks)


def main():
    """Run all comprehensive tests."""
    
    print("🧪 Comprehensive PDF Integration Testing")
    print("=" * 60)
    
    # Check prerequisites
    required_files = [
        'data/test_solicitation.pdf',
        'data/tfidf_model.pkl',
        'data/researcher_vectors.npz',
        'data/conceptual_profiles.npz',
        'data/evidence_index.json',
        'data/researcher_metadata.parquet'
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    
    # Run tests
    tests = [
        ("Complete Workflow", test_complete_workflow),
        ("Data Quality", test_data_quality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n🎉 {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Final Results: {passed}/{total} comprehensive tests passed")
    
    if passed == total:
        print("🚀 PDF integration is fully functional and ready for production!")
        print("\n📋 Summary of capabilities:")
        print("   ✅ PDF upload and parsing")
        print("   ✅ Quality assessment and confidence scoring")
        print("   ✅ Data extraction and validation")
        print("   ✅ Seamless integration with existing workflow")
        print("   ✅ End-to-end pipeline from PDF to team assembly")
        return True
    else:
        print("⚠️  Integration has issues that need to be addressed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)