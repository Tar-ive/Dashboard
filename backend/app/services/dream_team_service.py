import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from sklearn.metrics.pairwise import cosine_similarity
from app.models.team import (
    DreamTeamReport, DreamTeamMember, SkillCoverage, 
    SelectionStep, AffinityMatrixExport, TeamComparison
)
from app.models.matching import MatchingResults
from app.services.matching_service import MatchingService
from datetime import datetime
import json

class DreamTeamService:
    """Service for dream team assembly and optimization"""
    
    def __init__(self):
        self.matching_service = MatchingService()
    
    def create_affinity_matrix(self, matching_results: MatchingResults, 
                             top_n_researchers: int = 20) -> Tuple[pd.DataFrame, List[str]]:
        """Create affinity matrix from matching results"""
        print(f"📊 Creating affinity matrix for top {top_n_researchers} researchers...")
        
        # Get top researchers and skills
        top_matches = matching_results.top_matches[:top_n_researchers]
        researcher_names = [match.researcher_name for match in top_matches]
        skills = matching_results.skills_analyzed
        
        print(f"Matrix dimensions: {len(top_matches)} researchers × {len(skills)} skills")
        
        # Create matrix: researchers × skills
        affinity_matrix = np.zeros((len(top_matches), len(skills)))
        
        for i, match in enumerate(top_matches):
            researcher_id = match.researcher_id
            
            for j, skill in enumerate(skills):
                try:
                    # Calculate skill-specific affinity score
                    skill_keywords = self.matching_service.extract_keywords_from_skills([skill])
                    skill_text = ', '.join(skill_keywords)
                    
                    # TF-IDF similarity for this specific skill
                    if (self.matching_service.tfidf_model and 
                        researcher_id in self.matching_service.researcher_vectors):
                        
                        skill_vector = self.matching_service.tfidf_model.transform([skill_text])
                        researcher_vector = self.matching_service.researcher_vectors[researcher_id].reshape(1, -1)
                        sparse_sim = cosine_similarity(skill_vector, researcher_vector)[0][0] * 100
                    else:
                        sparse_sim = 0.0
                    
                    # Use pre-calculated dense score as proxy
                    dense_sim = match.s_dense
                    
                    # Combined affinity score for this skill
                    alpha, beta = 0.7, 0.3  # Same weights as matching service
                    skill_affinity = (alpha * sparse_sim) + (beta * dense_sim)
                    affinity_matrix[i, j] = max(0, skill_affinity)
                    
                except Exception as e:
                    # Fallback: use overall academic score
                    affinity_matrix[i, j] = match.academic_expertise_score
        
        # Create DataFrame
        affinity_df = pd.DataFrame(
            affinity_matrix,
            index=researcher_names,
            columns=[f"Skill_{i+1}: {skill}" for i, skill in enumerate(skills)]
        )
        
        print(f"✅ Created affinity matrix: {affinity_df.shape[0]} researchers × {affinity_df.shape[1]} skills")
        return affinity_df, skills
    
    def calculate_team_coverage(self, affinity_df: pd.DataFrame, team_indices: List[int]) -> Tuple[np.ndarray, float]:
        """Calculate team coverage scores for all skills"""
        if not team_indices:
            return np.array([0.0] * affinity_df.shape[1]), 0.0
        
        team_affinities = affinity_df.iloc[team_indices]
        skill_coverages = team_affinities.max(axis=0).values
        return skill_coverages, np.mean(skill_coverages)
    
    def calculate_marginal_gain(self, affinity_df: pd.DataFrame, 
                               current_team_indices: List[int], candidate_index: int) -> float:
        """Calculate the marginal gain of adding a candidate to the team"""
        _, current_coverage = self.calculate_team_coverage(affinity_df, current_team_indices)
        _, new_coverage = self.calculate_team_coverage(affinity_df, current_team_indices + [candidate_index])
        return new_coverage - current_coverage
    
    def dream_team_hybrid_strategy(self, affinity_df: pd.DataFrame, 
                                 guaranteed_top_n: int = 2, max_team_size: int = 4) -> Tuple[List[int], List[SelectionStep]]:
        """
        Hybrid approach: Lock in top N performers, then optimize coverage for remaining slots
        """
        print(f"🎯 Running Hybrid Dream Team Strategy")
        print(f"   Step 1: Lock in top {guaranteed_top_n} performers")
        print(f"   Step 2: Optimize coverage for remaining {max_team_size - guaranteed_top_n} slots")
        
        # Phase 1: Lock in top performers
        researcher_averages = affinity_df.mean(axis=1).sort_values(ascending=False)
        top_performers = researcher_averages.head(guaranteed_top_n)
        
        selected_indices = []
        selection_history = []
        
        print("🔒 LOCKING IN TOP PERFORMERS:")
        for i, (name, avg_score) in enumerate(top_performers.items()):
            idx = affinity_df.index.get_loc(name)
            selected_indices.append(idx)
            role = "PI" if i == 0 else f"Co-I {i}"
            
            selection_history.append(SelectionStep(
                step=i + 1,
                action=f'Lock {role}',
                researcher_name=name,
                reason=f'Top {i+1} performer (avg: {avg_score:.2f}, proven track record)',
                team_coverage=0  # Will calculate after
            ))
            print(f"   ✅ {name} ({role}) - Avg Score: {avg_score:.2f}")
        
        # Calculate coverage after locking in top performers
        _, coverage_after_top = self.calculate_team_coverage(affinity_df, selected_indices)
        print(f"   📊 Coverage after top {guaranteed_top_n}: {coverage_after_top:.2f}")
        
        # Update coverage in history
        for entry in selection_history:
            entry.team_coverage = coverage_after_top
        
        # Phase 2: Optimize remaining slots for coverage
        print(f"🎯 OPTIMIZING REMAINING {max_team_size - guaranteed_top_n} SLOTS FOR COVERAGE:")
        n_researchers = len(affinity_df)
        
        for step in range(guaranteed_top_n + 1, max_team_size + 1):
            # Calculate marginal gains for all remaining researchers
            gains = [(idx, self.calculate_marginal_gain(affinity_df, selected_indices, idx))
                     for idx in range(n_researchers) if idx not in selected_indices]
            
            if not gains:
                print(f"   ⚠️ No more candidates available")
                break
            
            # Sort by marginal gain and show top candidates
            top_candidates = sorted(gains, key=lambda x: x[1], reverse=True)[:5]
            best_candidate_idx, best_marginal_gain = top_candidates[0]
            
            print(f"   📊 Top candidates for slot {step - guaranteed_top_n}:")
            for i, (idx, gain) in enumerate(top_candidates):
                candidate_name = affinity_df.index[idx]
                candidate_avg = affinity_df.iloc[idx].mean()
                marker = "👑" if i == 0 else f"  {i+1}."
                print(f"      {marker} {candidate_name} (Avg: {candidate_avg:.2f}, Coverage Gain: +{gain:.2f})")
            
            # Add the best candidate for coverage
            if best_marginal_gain > 0.1:  # Lower threshold since we have strong foundation
                selected_indices.append(best_candidate_idx)
                _, new_coverage = self.calculate_team_coverage(affinity_df, selected_indices)
                
                selection_history.append(SelectionStep(
                    step=step,
                    action='Add for Coverage',
                    researcher_name=affinity_df.index[best_candidate_idx],
                    reason=f'Best coverage gain (+{best_marginal_gain:.2f})',
                    team_coverage=new_coverage
                ))
                print(f"   ✅ Added: {affinity_df.index[best_candidate_idx]} (New Coverage: {new_coverage:.2f})")
            else:
                print(f"   🛑 Stopping: Marginal gain {best_marginal_gain:.2f} too small")
                break
        
        final_coverage = self.calculate_team_coverage(affinity_df, selected_indices)[1]
        print(f"🎯 Final Hybrid Team ({len(selected_indices)} members) with {final_coverage:.2f} coverage")
        
        return selected_indices, selection_history
    
    def dream_team_greedy_algorithm(self, affinity_df: pd.DataFrame, 
                                  max_team_size: int = 4, marginal_threshold: float = 0.25) -> Tuple[List[int], List[SelectionStep]]:
        """Pure greedy algorithm for team selection"""
        print("🤖 Running Pure Greedy Algorithm...")
        
        n_researchers = len(affinity_df)
        selected_indices = []
        selection_history = []
        
        # Step 1: Select the best overall researcher as PI
        best_researcher_pos = affinity_df.mean(axis=1).idxmax()
        best_researcher_loc = affinity_df.index.get_loc(best_researcher_pos)
        selected_indices.append(best_researcher_loc)
        _, initial_coverage = self.calculate_team_coverage(affinity_df, selected_indices)
        
        selection_history.append(SelectionStep(
            step=1,
            action='Select PI',
            researcher_name=affinity_df.index[best_researcher_loc],
            reason='Highest average affinity score',
            team_coverage=initial_coverage
        ))
        
        # Step 2-N: Iteratively add members with the highest marginal gain
        for step in range(2, max_team_size + 1):
            gains = [(idx, self.calculate_marginal_gain(affinity_df, selected_indices, idx))
                     for idx in range(n_researchers) if idx not in selected_indices]
            if not gains:
                break
            
            best_candidate_idx, best_marginal_gain = max(gains, key=lambda item: item[1])
            
            # More flexible stopping criteria
            should_add = (
                best_marginal_gain > marginal_threshold or  # Significant gain
                len(selected_indices) < 2 or               # Haven't reached minimum
                (step <= 4 and best_marginal_gain > 0.1)   # Force at least 4 if minimal gain
            )
            
            if should_add:
                selected_indices.append(best_candidate_idx)
                _, new_coverage = self.calculate_team_coverage(affinity_df, selected_indices)
                selection_history.append(SelectionStep(
                    step=step,
                    action='Add Member',
                    researcher_name=affinity_df.index[best_candidate_idx],
                    reason=f'Maximum marginal gain (+{best_marginal_gain:.2f})',
                    team_coverage=new_coverage
                ))
            else:
                break
        
        return selected_indices, selection_history
    
    def dream_team_by_rankings(self, affinity_df: pd.DataFrame, team_size: int = 4) -> Tuple[List[int], List[SelectionStep]]:
        """Simple approach: Select top N researchers by overall ranking"""
        print(f"📈 Running Rankings Strategy (Top {team_size})")
        
        # Sort by average affinity
        researcher_averages = affinity_df.mean(axis=1).sort_values(ascending=False)
        top_researchers = researcher_averages.head(team_size)
        
        team_indices = [affinity_df.index.get_loc(name) for name in top_researchers.index]
        
        # Create selection history
        selection_history = []
        for i, (name, avg_score) in enumerate(top_researchers.items()):
            role = "PI" if i == 0 else f"Co-I {i}"
            selection_history.append(SelectionStep(
                step=i + 1,
                action=f'Select {role}',
                researcher_name=name,
                reason=f'Rank #{i+1} researcher (avg: {avg_score:.2f})',
                team_coverage=0  # Will be updated
            ))
        
        # Update coverage for all steps
        _, final_coverage = self.calculate_team_coverage(affinity_df, team_indices)
        for entry in selection_history:
            entry.team_coverage = final_coverage
        
        return team_indices, selection_history
    
    def generate_coverage_report(self, affinity_df: pd.DataFrame, 
                               team_indices: List[int], skills_list: List[str]) -> Dict[str, Any]:
        """Generate detailed coverage report for the selected team"""
        skill_coverages, overall_coverage = self.calculate_team_coverage(affinity_df, team_indices)
        
        # Team members analysis
        team_members = []
        for i, idx in enumerate(team_indices):
            scores = affinity_df.iloc[idx]
            top_skill_indices = scores.argsort()[-3:][::-1]  # Top 3 skills
            top_skills = [
                {"skill": skills_list[skill_idx], "score": scores.iloc[skill_idx]}
                for skill_idx in top_skill_indices
            ]
            
            role = "PI" if i == 0 else f"Co-I {i}"
            team_members.append(DreamTeamMember(
                researcher_id=f"researcher_{idx}",  # Would be actual ID in production
                name=affinity_df.index[idx],
                role=role,
                avg_affinity=scores.mean(),
                top_skills=top_skills,
                selection_reason=f"Selected as {role} for optimal team coverage"
            ))
        
        # Skill analysis
        skill_analysis = []
        for i, (skill, coverage) in enumerate(zip(skills_list, skill_coverages)):
            team_scores = affinity_df.iloc[team_indices, i]
            if not team_scores.empty and team_scores.max() > 0:
                best_member_name = team_scores.idxmax()
                expert_score = team_scores.max()
            else:
                best_member_name = "N/A"
                expert_score = 0.0
            
            skill_analysis.append(SkillCoverage(
                skill=skill,
                coverage_score=coverage,
                level='High' if coverage >= 70 else 'Medium' if coverage >= 40 else 'Low',
                expert=best_member_name,
                expert_score=expert_score
            ))
        
        return {
            'overall_coverage_score': overall_coverage,
            'team_members': team_members,
            'skill_analysis': skill_analysis
        }
    
    def generate_strategic_analysis(self, coverage_report: Dict, skills_list: List[str], 
                                  solicitation_title: str) -> str:
        """Generate strategic analysis (basic version without AI APIs)"""
        overall_coverage = coverage_report['overall_coverage_score']
        team_members = coverage_report['team_members']
        skill_analysis = coverage_report['skill_analysis']
        
        # Categorize skills by coverage level
        high_skills = [s for s in skill_analysis if s.level == 'High']
        medium_skills = [s for s in skill_analysis if s.level == 'Medium']
        low_skills = [s for s in skill_analysis if s.level == 'Low']
        
        analysis = f"""
# STRATEGIC ANALYSIS: {solicitation_title}

## Executive Summary
Team Coverage Score: **{overall_coverage:.1f}/100**

The assembled {len(team_members)}-member team demonstrates {'strong' if overall_coverage >= 70 else 'moderate' if overall_coverage >= 50 else 'developing'} alignment with the solicitation requirements.

## Team Composition Analysis

**Principal Investigator**: {team_members[0].name}
- Average Affinity Score: {team_members[0].avg_affinity:.1f}
- Top Expertise: {', '.join([skill['skill'] for skill in team_members[0].top_skills[:2]])}

**Co-Investigators**:
"""
        
        for member in team_members[1:]:
            analysis += f"""
- **{member.name}** ({member.role})
  - Affinity Score: {member.avg_affinity:.1f}
  - Key Strength: {member.top_skills[0]['skill'] if member.top_skills else 'General research'}
"""
        
        analysis += f"""
## Skill Coverage Assessment

### Strengths ({len(high_skills)} High-Coverage Areas)
"""
        for skill in high_skills[:3]:  # Show top 3
            analysis += f"- **{skill.skill}** (Coverage: {skill.coverage_score:.1f}) - Led by {skill.expert}\n"
        
        if medium_skills:
            analysis += f"""
### Areas for Development ({len(medium_skills)} Medium-Coverage Areas)
"""
            for skill in medium_skills[:3]:  # Show top 3
                analysis += f"- **{skill.skill}** (Coverage: {skill.coverage_score:.1f}) - Strengthen through collaboration\n"
        
        if low_skills:
            analysis += f"""
### Critical Gaps ({len(low_skills)} Low-Coverage Areas)
"""
            for skill in low_skills:
                analysis += f"- **{skill.skill}** (Coverage: {skill.coverage_score:.1f}) - **REQUIRES ATTENTION**\n"
            
            analysis += """
## Gap Mitigation Strategies
1. **External Collaborations**: Partner with institutions strong in low-coverage areas
2. **Consultant Expertise**: Engage domain experts as consultants or advisors
3. **Subcontracts**: Include specialized subcontractors for technical gaps
4. **Training & Development**: Invest in skill development for medium-coverage areas
"""
        
        analysis += f"""
## Competitive Assessment
{'🟢 **STRONG POSITION**' if overall_coverage >= 70 else '🟡 **COMPETITIVE POSITION**' if overall_coverage >= 50 else '🔴 **NEEDS STRENGTHENING**'}

This team {'demonstrates excellent' if overall_coverage >= 70 else 'shows good' if overall_coverage >= 50 else 'has developing'} alignment with solicitation requirements. 
{'The high coverage scores across multiple areas provide a strong foundation for a competitive proposal.' if overall_coverage >= 70 else 'Focus on addressing identified gaps to strengthen competitiveness.' if overall_coverage >= 50 else 'Significant effort needed to address skill gaps before submission.'}

## Recommendations
1. **Proposal Strategy**: {'Emphasize team strengths in high-coverage areas' if high_skills else 'Focus on demonstrating capability development'}
2. **Budget Allocation**: {'Leverage existing expertise' if overall_coverage >= 60 else 'Allocate resources for external expertise'}
3. **Timeline**: {'Proceed with confidence' if overall_coverage >= 70 else 'Allow extra time for team strengthening'}
"""
        
        return analysis
    
    def assemble_dream_team(self, matching_results: MatchingResults, 
                           strategy: str = "hybrid", max_team_size: int = 4,
                           guaranteed_top_n: int = 2, marginal_threshold: float = 0.25) -> DreamTeamReport:
        """Main function to assemble dream team using specified strategy"""
        
        print(f"🚀 ASSEMBLING DREAM TEAM using {strategy.upper()} strategy")
        print("=" * 60)
        
        # Create affinity matrix
        affinity_df, skills_list = self.create_affinity_matrix(matching_results, top_n_researchers=20)
        
        # Select team based on strategy
        if strategy == "hybrid":
            team_indices, selection_history = self.dream_team_hybrid_strategy(
                affinity_df, guaranteed_top_n, max_team_size
            )
        elif strategy == "greedy":
            team_indices, selection_history = self.dream_team_greedy_algorithm(
                affinity_df, max_team_size, marginal_threshold
            )
        elif strategy == "rankings":
            team_indices, selection_history = self.dream_team_by_rankings(
                affinity_df, max_team_size
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Generate coverage analysis
        coverage_report = self.generate_coverage_report(affinity_df, team_indices, skills_list)
        
        # Generate strategic analysis
        strategic_analysis = self.generate_strategic_analysis(
            coverage_report, skills_list, matching_results.solicitation_title
        )
        
        return DreamTeamReport(
            solicitation_id=matching_results.solicitation_id,
            solicitation_title=matching_results.solicitation_title,
            team_members=coverage_report['team_members'],
            overall_coverage_score=coverage_report['overall_coverage_score'],
            skill_analysis=coverage_report['skill_analysis'],
            strategic_analysis=strategic_analysis,
            selection_history=selection_history,
            strategy_used=strategy,
            generated_at=datetime.now(),
            affinity_matrix_shape=(affinity_df.shape[0], affinity_df.shape[1])
        )
    
    def export_affinity_matrix(self, affinity_df: pd.DataFrame, 
                             solicitation_id: str, skills_list: List[str]) -> AffinityMatrixExport:
        """Export affinity matrix for external analysis"""
        return AffinityMatrixExport(
            solicitation_id=solicitation_id,
            researchers=list(affinity_df.index),
            skills=skills_list,
            matrix=affinity_df.values.tolist(),
            generated_at=datetime.now()
        )