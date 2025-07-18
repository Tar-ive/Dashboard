#!/usr/bin/env python3
"""
Demonstration script for the test data factories.

This script shows how to use the various factories to generate realistic test data
for different testing scenarios in the NSF Researcher Matching API.
"""

from tests.factories import (
    ResearcherFactory,
    SolicitationFactory,
    MatchingResultFactory,
    TestDataBuilder,
    set_test_seed,
    create_basic_test_scenario,
    create_ai_focused_scenario
)


def demo_researcher_factory():
    """Demonstrate ResearcherFactory capabilities."""
    print("=== ResearcherFactory Demo ===")
    
    # Create a basic researcher
    researcher = ResearcherFactory.create_researcher()
    print(f"Basic Researcher: {researcher['name']} from {researcher['institution']}")
    print(f"  Expertise: {', '.join(researcher['expertise'][:3])}")
    print(f"  Publications: {researcher['publications']}, H-index: {researcher['h_index']}")
    
    # Create an expert researcher
    expert = ResearcherFactory.create_expert_researcher("machine learning")
    print(f"\nExpert Researcher: {expert['name']}")
    print(f"  Expertise: {', '.join(expert['expertise'])}")
    print(f"  Publications: {expert['publications']}, H-index: {expert['h_index']}")
    
    # Create a collaboration network
    network = ResearcherFactory.create_collaboration_network(3, ["data science", "AI"])
    print(f"\nCollaboration Network ({len(network)} researchers):")
    for i, researcher in enumerate(network, 1):
        print(f"  {i}. {researcher['name']} - Collaboration Score: {researcher['collaboration_score']:.2f}")
    
    print()


def demo_solicitation_factory():
    """Demonstrate SolicitationFactory capabilities."""
    print("=== SolicitationFactory Demo ===")
    
    # Create a basic solicitation
    solicitation = SolicitationFactory.create_solicitation()
    print(f"Basic Solicitation: {solicitation['title']}")
    print(f"  Program: {solicitation['program']}")
    print(f"  Keywords: {', '.join(solicitation['keywords'][:5])}")
    print(f"  Budget Range: ${solicitation['budget_range']}")
    
    # Create an AI-focused solicitation
    ai_solicitation = SolicitationFactory.create_solicitation(
        research_area="Artificial Intelligence",
        program="MFAI"
    )
    print(f"\nAI Solicitation: {ai_solicitation['title']}")
    print(f"  Research Area: {ai_solicitation['research_area']}")
    print(f"  Keywords: {', '.join(ai_solicitation['keywords'])}")
    
    print()


def demo_matching_factory():
    """Demonstrate MatchingResultFactory capabilities."""
    print("=== MatchingResultFactory Demo ===")
    
    # Create test data
    solicitation = SolicitationFactory.create_solicitation(research_area="Machine Learning")
    researchers = ResearcherFactory.create_researcher_batch(5)
    
    # Create matching results
    results = MatchingResultFactory.create_matching_results(solicitation, researchers)
    
    print(f"Matching Results for: {results['solicitation_title']}")
    print(f"Total Researchers: {results['total_researchers']}")
    print(f"Eligible Researchers: {results['eligible_researchers']}")
    print(f"Processing Time: {results['processing_time_seconds']:.2f}s")
    
    print("\nTop Matches:")
    for i, match in enumerate(results['top_matches'][:3], 1):
        print(f"  {i}. {match['researcher_name']}")
        print(f"     Final Score: {match['final_affinity_score']:.3f}")
        print(f"     TF-IDF: {match['s_sparse']:.3f}, Semantic: {match['s_dense']:.3f}")
    
    # Create a dream team
    team_members = [
        MatchingResultFactory.create_dream_team_member(researchers[0], "PI"),
        MatchingResultFactory.create_dream_team_member(researchers[1], "Co-I 1"),
        MatchingResultFactory.create_dream_team_member(researchers[2], "Co-I 2")
    ]
    
    team_report = MatchingResultFactory.create_dream_team_report(solicitation, team_members)
    
    print(f"\nDream Team Report:")
    print(f"Overall Coverage Score: {team_report['overall_coverage_score']:.3f}")
    print(f"Strategy Used: {team_report['strategy_used']}")
    print("Team Members:")
    for member in team_report['team_members']:
        print(f"  - {member['name']} ({member['role']}) - Affinity: {member['avg_affinity']:.3f}")
    
    print()


def demo_test_data_builder():
    """Demonstrate TestDataBuilder capabilities."""
    print("=== TestDataBuilder Demo ===")
    
    # Build a custom test scenario
    scenario = (TestDataBuilder()
                .with_diverse_researchers(8)
                .with_solicitations(2, program="CISE")
                .with_matching_results(top_n_results=5)
                .build())
    
    print(f"Custom Scenario:")
    print(f"  Researchers: {len(scenario['researchers'])}")
    print(f"  Solicitations: {len(scenario['solicitations'])}")
    print(f"  Matching Results: {len(scenario['matching_results'])}")
    
    # Show diversity in researchers
    departments = set(r['department'] for r in scenario['researchers'])
    print(f"  Departments: {', '.join(departments)}")
    
    print()


def demo_convenience_functions():
    """Demonstrate convenience functions."""
    print("=== Convenience Functions Demo ===")
    
    # Basic test scenario
    basic = create_basic_test_scenario()
    print(f"Basic Scenario: {len(basic['researchers'])} researchers, "
          f"{len(basic['solicitations'])} solicitations")
    
    # AI-focused scenario
    ai_scenario = create_ai_focused_scenario()
    print(f"AI Scenario: {len(ai_scenario['researchers'])} researchers, "
          f"{len(ai_scenario['solicitations'])} solicitations")
    
    # Show AI focus
    ai_keywords = []
    for sol in ai_scenario['solicitations']:
        ai_keywords.extend(sol['keywords'])
    ai_keywords = list(set(ai_keywords))
    print(f"AI Keywords: {', '.join(ai_keywords[:5])}")
    
    print()


def demo_reproducibility():
    """Demonstrate reproducible data generation."""
    print("=== Reproducibility Demo ===")
    
    # Generate data with seed
    set_test_seed(42)
    researcher1 = ResearcherFactory.create_researcher()
    
    # Generate again with same seed
    set_test_seed(42)
    researcher2 = ResearcherFactory.create_researcher()
    
    print(f"Researcher 1: {researcher1['name']} - {researcher1['publications']} publications")
    print(f"Researcher 2: {researcher2['name']} - {researcher2['publications']} publications")
    print(f"Identical: {researcher1['name'] == researcher2['name']}")
    
    print()


def main():
    """Run all demonstrations."""
    print("NSF Researcher Matching API - Test Data Factories Demo")
    print("=" * 60)
    print()
    
    demo_researcher_factory()
    demo_solicitation_factory()
    demo_matching_factory()
    demo_test_data_builder()
    demo_convenience_functions()
    demo_reproducibility()
    
    print("Demo completed successfully!")
    print("\nThe factories are ready for use in your test suites.")
    print("Import them with: from tests.factories import ResearcherFactory, SolicitationFactory, MatchingResultFactory")


if __name__ == "__main__":
    main()