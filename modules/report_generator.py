"""
ReportGenerator class responsible for generating all human-readable outputs,
including AI analysis and final Markdown reports.
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from .data_models import MatchingResults, TeamAssemblyResult, DreamTeamReport, Solicitation


class ReportGenerator:
    """Handles report generation and AI-powered strategic analysis."""
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize with optional Groq API key."""
        self.groq_client = None
        
        if GROQ_AVAILABLE and groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=groq_api_key)
                print("✅ Groq API client initialized for strategic analysis")
            except Exception as e:
                print(f"⚠️ Groq API setup failed: {e}")
        else:
            print("⚠️ Groq API not available. Strategic analysis will be basic.")
    
    def generate_strategic_analysis(self, team_members: List[Dict], 
                                   solicitation: Solicitation,
                                   coverage_score: float) -> str:
        """Generate AI-powered strategic analysis using Groq API."""
        if not self.groq_client:
            return self._generate_basic_analysis(team_members, solicitation, coverage_score)
        
        try:
            # Prepare team summary for AI analysis
            team_summary = "\n".join([
                f"- {member['name']}: {member['final_affinity_score']:.3f} affinity score, "
                f"{member['total_papers']} papers"
                for member in team_members
            ])
            
            skills_summary = ", ".join(solicitation.required_skills_checklist[:10])
            
            prompt = f"""
            As a research strategy consultant, analyze this assembled research team for the following solicitation:

            SOLICITATION: {solicitation.title}
            
            ABSTRACT: {solicitation.abstract[:500]}...
            
            KEY SKILLS NEEDED: {skills_summary}
            
            ASSEMBLED TEAM:
            {team_summary}
            
            OVERALL COVERAGE SCORE: {coverage_score:.1%}
            
            Please provide a strategic analysis covering:
            1. Team strengths and how they align with solicitation requirements
            2. Potential gaps or areas of concern
            3. Collaboration opportunities within the team
            4. Strategic recommendations for proposal development
            5. Risk assessment and mitigation strategies
            
            Keep the analysis professional, actionable, and under 500 words.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=600
            )
            
            return response.choices[0].message.content or "No response generated"
            
        except Exception as e:
            print(f"❌ Error generating AI analysis: {e}")
            return self._generate_basic_analysis(team_members, solicitation, coverage_score)
    
    def _generate_basic_analysis(self, team_members: List[Dict], 
                                solicitation: Solicitation, coverage_score: float) -> str:
        """Generate basic analysis when AI is not available."""
        team_size = len(team_members)
        avg_papers = sum(m['total_papers'] for m in team_members) / team_size if team_size > 0 else 0
        avg_affinity = sum(m['final_affinity_score'] for m in team_members) / team_size if team_size > 0 else 0
        
        analysis = f"""
        **Strategic Team Analysis**
        
        This {team_size}-member research team has been assembled for "{solicitation.title}" 
        with an overall coverage score of {coverage_score:.1%}.
        
        **Team Metrics:**
        - Average publications per member: {avg_papers:.0f}
        - Average affinity score: {avg_affinity:.3f}
        - Coverage of required skills: {coverage_score:.1%}
        
        **Key Observations:**
        - The team demonstrates {"strong" if coverage_score > 0.7 else "moderate" if coverage_score > 0.5 else "limited"} 
          alignment with solicitation requirements
        - Team members bring diverse research backgrounds and expertise
        - {"Excellent" if avg_papers > 50 else "Good" if avg_papers > 20 else "Emerging"} 
          research productivity across the team
        
        **Recommendations:**
        - Focus on leveraging complementary expertise for interdisciplinary collaboration
        - Ensure clear role definition and communication protocols
        - Consider additional expertise if coverage gaps are identified
        """
        
        return analysis.strip()
    
    def get_team_evidence(self, team_members: List[Dict], data: Dict[str, Any], 
                         skills: List[str], top_papers_per_member: int = 3) -> Dict[str, List[Dict]]:
        """Extract supporting paper evidence for the final team."""
        evidence = {}
        evidence_index = data['evidence_index']
        
        for member in team_members:
            researcher_id = member['researcher_id']
            researcher_name = member['name']
            
            member_papers = []
            
            if researcher_id in evidence_index:
                researcher_evidence = evidence_index[researcher_id]
                
                # Collect papers from relevant skill topics
                for skill in skills[:5]:  # Limit to top 5 skills
                    skill_key = skill.lower().replace(' ', '_')
                    if skill_key in researcher_evidence:
                        papers = researcher_evidence[skill_key][:2]  # Top 2 papers per skill
                        for paper_id in papers:
                            member_papers.append({
                                'paper_id': paper_id,
                                'skill_area': skill,
                                'relevance': 'High'
                            })
            
            evidence[researcher_name] = member_papers[:top_papers_per_member]
        
        return evidence
    
    def format_markdown_report(self, dream_team_report: DreamTeamReport, 
                              team_evidence: Dict[str, List[Dict]], 
                              solicitation: Solicitation) -> str:
        """Format the complete Markdown report for display and download."""
        
        report_md = f"""# Dream Team Analysis Report

**Solicitation:** {solicitation.title}
**Generated:** {dream_team_report.generated_at}
**Overall Coverage Score:** {dream_team_report.overall_coverage_score:.1%}

## Executive Summary

{dream_team_report.strategic_analysis}

## Team Composition

"""
        
        # Add team members
        for i, member in enumerate(dream_team_report.team_members, 1):
            report_md += f"""
### {i}. {member['name']}

- **Affinity Score:** {member['final_affinity_score']:.3f}
- **Academic Expertise:** {member['academic_expertise_score']:.3f}
- **Total Publications:** {member['total_papers']}
- **Team Role:** {member['team_role']}

"""
            
            # Add evidence if available
            if member['name'] in team_evidence:
                papers = team_evidence[member['name']]
                if papers:
                    report_md += "**Key Supporting Papers:**\n"
                    for paper in papers:
                        report_md += f"- {paper['paper_id']} (Relevant to: {paper['skill_area']})\n"
                    report_md += "\n"
        
        # Add selection history
        report_md += "\n## Team Selection Process\n\n"
        for step in dream_team_report.selection_history:
            report_md += f"**Round {step['round']}:** {step['researcher']} "
            report_md += f"(Marginal Gain: {step['marginal_gain']:.3f}, "
            report_md += f"Team Coverage: {step['team_coverage']:.3f})\n"
        
        # Add skill analysis if available
        if dream_team_report.skill_analysis:
            report_md += "\n## Skill Coverage Analysis\n\n"
            for skill_data in dream_team_report.skill_analysis:
                skill_name = skill_data.get('skill', 'Unknown')
                coverage = skill_data.get('coverage', 0)
                report_md += f"- **{skill_name}:** {coverage:.1%} coverage\n"
        
        report_md += f"\n---\n*Report generated on {dream_team_report.generated_at}*"
        
        return report_md
    
    def generate_full_report(self, matching_results: MatchingResults, 
                           team_results: TeamAssemblyResult, 
                           solicitation: Solicitation,
                           data: Dict[str, Any]) -> tuple[DreamTeamReport, Dict[str, List[Dict]]]:
        """Main method that orchestrates the creation of the final report."""
        
        print("📋 Generating comprehensive report...")
        
        # Generate strategic analysis
        strategic_analysis = self.generate_strategic_analysis(
            team_results.team_members, 
            solicitation,
            team_results.overall_coverage_score
        )
        
        # Get team evidence
        team_evidence = self.get_team_evidence(
            team_results.team_members, 
            data, 
            matching_results.skills_analyzed
        )
        
        # Create skill analysis
        skill_analysis = []
        if hasattr(team_results, 'affinity_df'):
            skill_columns = [col for col in team_results.affinity_df.columns if col != 'Researcher']
            team_affinities = team_results.affinity_df.iloc[team_results.team_indices][skill_columns]
            
            for skill in skill_columns:
                max_affinity = team_affinities[skill].max()
                skill_analysis.append({
                    'skill': skill,
                    'coverage': max_affinity,
                    'best_member': team_affinities[skill].idxmax()
                })
        
        # Create final report
        dream_team_report = DreamTeamReport(
            team_members=team_results.team_members,
            overall_coverage_score=team_results.overall_coverage_score,
            skill_analysis=skill_analysis,
            strategic_analysis=strategic_analysis,
            selection_history=team_results.selection_history,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        print("✅ Report generation complete")
        
        return dream_team_report, team_evidence
