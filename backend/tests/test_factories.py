"""
Tests for the test data factories.

This module verifies that the factories generate realistic and consistent test data
that matches the expected data models and business requirements.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from tests.factories import (
    ResearcherFactory,
    SolicitationFactory,
    MatchingResultFactory,
    TestDataBuilder,
    set_test_seed,
    create_basic_test_scenario,
    create_large_test_scenario,
    create_ai_focused_scenario
)


class TestResearcherFactory:
    """Test the ResearcherFactory functionality."""
    
    def test_create_researcher_basic(self):
        """Test basic researcher creation."""
        researcher = ResearcherFactory.create_researcher()
        
        # Verify required fields
        assert "researcher_id" in researcher
        assert "name" in researcher
        assert "institution" in researcher
        assert "expertise" in researcher
        assert isinstance(researcher["expertise"], list)
        assert len(researcher["expertise"]) >= 3
        
        # Verify realistic metrics
        assert researcher["publications"] >= 0
        assert researcher["h_index"] >= 0
        assert researcher["years_active"] >= 0
        assert 0 <= researcher["collaboration_score"] <= 1.0
        assert 0 <= researcher["recent_activity"] <= 1.0
    
    def test_create_researcher_with_kwargs(self):
        """Test researcher creation with specific parameters."""
        researcher = ResearcherFactory.create_researcher(
            name="Dr. Test Researcher",
            institution="Test University",
            discipline="Computer Science",
            publications=50
        )
        
        assert researcher["name"] == "Dr. Test Researcher"
        assert researcher["institution"] == "Test University"
        assert researcher["publications"] == 50
        assert "machine learning" in str(researcher["expertise"]).lower() or \
               "artificial intelligence" in str(researcher["expertise"]).lower()
    
    def test_create_researcher_batch(self):
        """Test batch researcher creation."""
        researchers = ResearcherFactory.create_researcher_batch(5, institution="Batch University")
        
        assert len(researchers) == 5
        for researcher in researchers:
            assert researcher["institution"] == "Batch University"
            assert "researcher_id" in researcher
    
    def test_create_diverse_researcher_set(self):
        """Test diverse researcher set creation."""
        researchers = ResearcherFactory.create_diverse_researcher_set(10)
        
        assert len(researchers) == 10
        departments = [r["department"] for r in researchers]
        # Should have multiple different departments
        assert len(set(departments)) > 1
    
    def test_create_expert_researcher(self):
        """Test expert researcher creation."""
        researcher = ResearcherFactory.create_expert_researcher("machine learning")
        
        assert "machine learning" in researcher["expertise"]
        assert researcher["publications"] >= 30  # Should be senior
        assert researcher["h_index"] >= 15
        assert researcher["years_active"] >= 10
    
    def test_create_junior_researcher(self):
        """Test junior researcher creation."""
        researcher = ResearcherFactory.create_junior_researcher()
        
        assert researcher["years_active"] <= 5
        assert researcher["publications"] <= 15
        assert researcher["h_index"] <= 8
        assert researcher["grants_received"] <= 2
    
    def test_create_collaboration_network(self):
        """Test collaboration network creation."""
        network = ResearcherFactory.create_collaboration_network(5, ["data science", "AI"])
        
        assert len(network) == 5
        for researcher in network:
            expertise_str = " ".join(researcher["expertise"]).lower()
            assert "data science" in expertise_str or "ai" in expertise_str
            assert researcher["collaboration_score"] >= 0.6


class TestSolicitationFactory:
    """Test the SolicitationFactory functionality."""
    
    def test_create_solicitation_basic(self):
        """Test basic solicitation creation."""
        solicitation = SolicitationFactory.create_solicitation()
        
        # Verify required fields
        assert "solicitation_id" in solicitation
        assert "title" in solicitation
        assert "program" in solicitation
        assert "keywords" in solicitation
        assert isinstance(solicitation["keywords"], list)
        assert len(solicitation["keywords"]) > 0
        
        # Verify realistic data
        assert solicitation["text_length"] >= 5000
        assert solicitation["status"] in ["processing", "completed", "failed"]
        assert isinstance(solicitation["sections_found"], list)
    
    def test_create_solicitation_with_kwargs(self):
        """Test solicitation creation with specific parameters."""
        solicitation = SolicitationFactory.create_solicitation(
            program="MFAI",
            research_area="Artificial Intelligence",
            title="Test AI Solicitation"
        )
        
        assert solicitation["program"] == "MFAI"
        assert solicitation["research_area"] == "Artificial Intelligence"
        assert solicitation["title"] == "Test AI Solicitation"
        assert "artificial" in " ".join(solicitation["keywords"]).lower()
    
    def test_create_solicitation_batch(self):
        """Test batch solicitation creation."""
        solicitations = SolicitationFactory.create_solicitation_batch(3, program="CISE")
        
        assert len(solicitations) == 3
        for solicitation in solicitations:
            assert solicitation["program"] == "CISE"
            assert "solicitation_id" in solicitation


class TestMatchingResultFactory:
    """Test the MatchingResultFactory functionality."""
    
    def test_create_researcher_match(self):
        """Test researcher match creation."""
        researcher = ResearcherFactory.create_researcher()
        match = MatchingResultFactory.create_researcher_match(researcher)
        
        assert match["researcher_id"] == researcher["researcher_id"]
        assert match["researcher_name"] == researcher["name"]
        assert 0 <= match["academic_expertise_score"] <= 1.0
        assert 0 <= match["s_sparse"] <= 1.0
        assert 0 <= match["s_dense"] <= 1.0
        assert 0 <= match["f_ge"] <= 1.0
        assert match["eligibility_status"] in ["eligible", "ineligible"]
    
    def test_create_matching_results(self):
        """Test complete matching results creation."""
        solicitation = SolicitationFactory.create_solicitation()
        researchers = ResearcherFactory.create_researcher_batch(10)
        
        results = MatchingResultFactory.create_matching_results(solicitation, researchers)
        
        assert results["solicitation_id"] == solicitation["solicitation_id"]
        assert results["solicitation_title"] == solicitation["title"]
        assert results["total_researchers"] == 10
        assert len(results["top_matches"]) <= 20  # Default top_n
        assert isinstance(results["skills_analyzed"], list)
        assert results["processing_time_seconds"] > 0
        
        # Verify matches are sorted by score
        scores = [match["final_affinity_score"] for match in results["top_matches"]]
        assert scores == sorted(scores, reverse=True)
    
    def test_create_dream_team_member(self):
        """Test dream team member creation."""
        researcher = ResearcherFactory.create_researcher()
        member = MatchingResultFactory.create_dream_team_member(researcher, "PI")
        
        assert member["researcher_id"] == researcher["researcher_id"]
        assert member["name"] == researcher["name"]
        assert member["role"] == "PI"
        assert 0.6 <= member["avg_affinity"] <= 0.95
        assert isinstance(member["top_skills"], list)
        assert len(member["top_skills"]) <= 3
    
    def test_create_dream_team_report(self):
        """Test dream team report creation."""
        solicitation = SolicitationFactory.create_solicitation()
        researchers = ResearcherFactory.create_researcher_batch(4)
        team_members = [
            MatchingResultFactory.create_dream_team_member(researchers[i], f"Member {i+1}")
            for i in range(4)
        ]
        
        report = MatchingResultFactory.create_dream_team_report(solicitation, team_members)
        
        assert report["solicitation_id"] == solicitation["solicitation_id"]
        assert len(report["team_members"]) == 4
        assert 0.75 <= report["overall_coverage_score"] <= 0.95
        assert isinstance(report["skill_analysis"], list)
        assert isinstance(report["selection_history"], list)
        assert report["strategy_used"] in ["hybrid", "greedy", "rankings"]


class TestTestDataBuilder:
    """Test the TestDataBuilder functionality."""
    
    def test_builder_pattern(self):
        """Test the builder pattern functionality."""
        data = (TestDataBuilder()
                .with_researchers(5)
                .with_solicitations(2)
                .with_matching_results()
                .build())
        
        assert len(data["researchers"]) == 5
        assert len(data["solicitations"]) == 2
        assert len(data["matching_results"]) == 2  # One per solicitation
        
        # Verify matching results reference the created data
        for result in data["matching_results"]:
            assert result["solicitation_id"] in [s["solicitation_id"] for s in data["solicitations"]]
    
    def test_diverse_researchers_builder(self):
        """Test diverse researchers in builder."""
        data = (TestDataBuilder()
                .with_diverse_researchers(8)
                .build())
        
        assert len(data["researchers"]) == 8
        departments = [r["department"] for r in data["researchers"]]
        assert len(set(departments)) > 1  # Should have diversity


class TestConvenienceFunctions:
    """Test the convenience functions for common scenarios."""
    
    def test_create_basic_test_scenario(self):
        """Test basic test scenario creation."""
        scenario = create_basic_test_scenario()
        
        assert len(scenario["researchers"]) == 20
        assert len(scenario["solicitations"]) == 3
        assert len(scenario["matching_results"]) == 3
    
    def test_create_large_test_scenario(self):
        """Test large test scenario creation."""
        scenario = create_large_test_scenario()
        
        assert len(scenario["researchers"]) == 100
        assert len(scenario["solicitations"]) == 10
        assert len(scenario["matching_results"]) == 10
    
    def test_create_ai_focused_scenario(self):
        """Test AI-focused test scenario creation."""
        scenario = create_ai_focused_scenario()
        
        assert len(scenario["researchers"]) == 15
        assert len(scenario["solicitations"]) == 2
        
        # Verify AI focus
        for solicitation in scenario["solicitations"]:
            assert "artificial intelligence" in solicitation["research_area"].lower()
        
        for researcher in scenario["researchers"]:
            assert researcher["department"] == "Computer Science"


class TestDataConsistency:
    """Test data consistency and reproducibility."""
    
    def test_reproducible_data_with_seed(self):
        """Test that setting seed produces reproducible data."""
        set_test_seed(42)
        researcher1 = ResearcherFactory.create_researcher()
        
        set_test_seed(42)
        researcher2 = ResearcherFactory.create_researcher()
        
        # Should be identical when using same seed
        assert researcher1["name"] == researcher2["name"]
        assert researcher1["institution"] == researcher2["institution"]
        assert researcher1["publications"] == researcher2["publications"]
    
    def test_data_relationships(self):
        """Test that generated data maintains logical relationships."""
        researcher = ResearcherFactory.create_researcher()
        
        # Career metrics should be logically consistent
        assert researcher["h_index"] <= researcher["publications"]
        if researcher["years_active"] > 10:
            assert researcher["publications"] > 10  # Senior researchers should have more publications
        
        # Collaboration score should be reasonable
        assert 0 <= researcher["collaboration_score"] <= 1.0
    
    def test_matching_score_consistency(self):
        """Test that matching scores are consistent and realistic."""
        researcher = ResearcherFactory.create_researcher(grants_received=5)
        match = MatchingResultFactory.create_researcher_match(researcher)
        
        # Grant experience factor should reflect actual grants
        assert match["f_ge"] >= 0.5  # Should be boosted by grants
        
        # All scores should be in valid ranges
        assert 0 <= match["academic_expertise_score"] <= 1.0
        assert 0 <= match["final_affinity_score"] <= 1.0


@pytest.mark.performance
class TestFactoryPerformance:
    """Test factory performance for large data generation."""
    
    def test_large_batch_performance(self):
        """Test performance of generating large batches."""
        import time
        
        start_time = time.time()
        researchers = ResearcherFactory.create_researcher_batch(1000)
        end_time = time.time()
        
        assert len(researchers) == 1000
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
    
    def test_complex_scenario_performance(self):
        """Test performance of complex scenario generation."""
        import time
        
        start_time = time.time()
        scenario = create_large_test_scenario()
        end_time = time.time()
        
        assert len(scenario["researchers"]) == 100
        assert len(scenario["solicitations"]) == 10
        assert end_time - start_time < 10.0  # Should complete within 10 seconds