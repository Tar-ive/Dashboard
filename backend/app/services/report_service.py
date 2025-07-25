import json
import markdown
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from jinja2 import Template, Environment, DictLoader
import pandas as pd
from app.models.team import DreamTeamReport
from app.models.matching import MatchingResults
from app.models.reports import (
    ComprehensiveReport, GapAnalysisReport, ReportExport,
    ExecutiveSummary, SupportingEvidence
)
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """Service for generating comprehensive reports with AI-powered analysis"""
    
    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service
        self.template_env = self._setup_templates()
        
        # Log AI service availability
        if self.ai_service:
            logger.info("✅ AI service injected for report generation")
        else:
            logger.warning("⚠️ AI service not available - running without AI features")
    
    def _setup_templates(self) -> Environment:
        """Setup Jinja2 templates for report generation"""
        
        # Define templates as strings (could be moved to separate files)
        templates = {
            'comprehensive_report': """
# {{ title }}

**Generated:** {{ generated_at }}  
**Solicitation:** {{ solicitation_title }}  
**Team Coverage Score:** {{ coverage_score }}/100

---

## 🏆 Executive Summary

{{ executive_summary }}

---

## 👥 Recommended Dream Team

| Role | Researcher | Affinity Score | Top Expertise |
|:-----|:-----------|:-------------:|:-------------|
{% for member in team_members -%}
| {{ member.role }} | **{{ member.name }}** | {{ "%.1f"|format(member.avg_affinity) }} | {{ member.top_skills[0].skill if member.top_skills else "General Research" }} |
{% endfor %}

### Team Selection Strategy
**Strategy Used:** {{ strategy_used.title() }}

#### Selection Process:
{% for step in selection_history -%}
**Step {{ step.step }}:** {{ step.action }} - {{ step.researcher_name }}
- Reason: {{ step.reason }}
- Team Coverage: {{ "%.1f"|format(step.team_coverage) }}

{% endfor %}

---

## 📊 Skills Coverage Analysis

### Overall Coverage: {{ "%.1f"|format(coverage_score) }}/100

| Skill Area | Coverage | Level | Primary Expert |
|:-----------|:--------:|:------|:---------------|
{% for skill in skill_analysis -%}
| {{ skill.skill }} | {{ "%.1f"|format(skill.coverage_score) }} | {{ skill.level_emoji }} {{ skill.level }} | {{ skill.expert }} |
{% endfor %}

### Coverage Breakdown:
- 🟢 **High Coverage** (70+): {{ high_coverage_count }} skills
- 🟡 **Medium Coverage** (40-69): {{ medium_coverage_count }} skills  
- 🔴 **Low Coverage** (<40): {{ low_coverage_count }} skills

---

## 🧠 AI-Powered Gap Analysis

{{ gap_analysis }}

---

## 📈 Strategic Recommendations

{{ strategic_recommendations }}

---

## 💡 Next Steps

{{ next_steps }}

---

## 📚 Supporting Evidence

{{ supporting_evidence }}

---

*Report generated by NSF Researcher Matching System v1.0*
""",

            'executive_summary': """
# Executive Summary: {{ solicitation_title }}

**Team Coverage Score:** {{ coverage_score }}/100  
**Recommended Strategy:** {{ strategy_used.title() }}  
**Generated:** {{ generated_at }}

## Key Findings

### Team Composition
- **{{ team_size }}** carefully selected researchers
- **Principal Investigator:** {{ pi_name }} (Affinity: {{ pi_score }})
- **Strategy:** {{ strategy_description }}

### Coverage Assessment
- **Strengths:** {{ strengths_summary }}
- **Gaps:** {{ gaps_summary }}
- **Risk Level:** {{ risk_level }}

### Competitiveness
{{ competitiveness_assessment }}

### Immediate Actions Required
{{ action_items }}

---

**Bottom Line:** {{ bottom_line }}
""",

            'gap_analysis': """
## Critical Gap Analysis

### Identified Gaps
{% for gap in critical_gaps -%}
#### {{ gap.area }}
- **Severity:** {{ gap.severity }}
- **Impact:** {{ gap.impact }}
- **Mitigation:** {{ gap.mitigation_strategy }}

{% endfor %}

### Risk Assessment
{{ risk_assessment }}

### Strategic Recommendations
{% for rec in recommendations -%}
- **{{ rec.category }}:** {{ rec.description }}
{% endfor %}
"""
        }
        
        return Environment(loader=DictLoader(templates))
    
    def generate_comprehensive_report(
        self, 
        solicitation_id: str,
        team_report: DreamTeamReport,
        matching_results: MatchingResults,
        include_ai_analysis: bool = True
    ) -> ComprehensiveReport:
        """Generate a comprehensive report combining all analysis components"""
        
        logger.info(f"🚀 Generating comprehensive report for solicitation {solicitation_id}")
        
        try:
            # Generate AI-powered gap analysis if available
            gap_analysis = None
            if include_ai_analysis and self.ai_service:
                gap_analysis = self._generate_ai_gap_analysis(team_report, matching_results)
            
            # Create executive summary
            executive_summary = self._create_executive_summary(team_report, gap_analysis)
            
            # Generate strategic recommendations
            strategic_recommendations = self._generate_strategic_recommendations(
                team_report, gap_analysis
            )
            
            # Collect supporting evidence
            supporting_evidence = self._collect_supporting_evidence(
                team_report, matching_results
            )
            
            # Generate next steps
            next_steps = self._generate_next_steps(team_report, gap_analysis)
            
            # Create comprehensive report
            report = ComprehensiveReport(
                solicitation_id=solicitation_id,
                solicitation_title=team_report.solicitation_title,
                team_report=team_report,
                matching_results=matching_results,
                executive_summary=executive_summary,
                gap_analysis=gap_analysis,
                strategic_recommendations=strategic_recommendations,
                supporting_evidence=supporting_evidence,
                next_steps=next_steps,
                generated_at=datetime.now(),
                report_version="1.0"
            )
            
            logger.info("✅ Comprehensive report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating comprehensive report: {e}")
            raise
    
    def _generate_ai_gap_analysis(
        self, 
        team_report: DreamTeamReport, 
        matching_results: MatchingResults
    ) -> Optional[GapAnalysisReport]:
        """Generate AI-powered gap analysis using Anthropic"""
        
        if not self.ai_service:
            logger.warning("⚠️ AI service not available for gap analysis")
            return None
        
        try:
            logger.info("🤖 Generating AI-powered gap analysis...")
            
            # Prepare data for AI analysis
            analysis_data = {
                'solicitation_title': team_report.solicitation_title,
                'team_coverage_score': team_report.overall_coverage_score,
                'team_members': [
                    {
                        'name': member.name,
                        'role': member.role,
                        'avg_affinity': member.avg_affinity,
                        'top_skills': [skill['skill'] for skill in member.top_skills[:3]]
                    }
                    for member in team_report.team_members
                ],
                'skill_analysis': [
                    {
                        'skill': skill.skill,
                        'coverage_score': skill.coverage_score,
                        'level': skill.level,
                        'expert': skill.expert
                    }
                    for skill in team_report.skill_analysis
                ],
                'skills_analyzed': matching_results.skills_analyzed,
                'strategy_used': team_report.strategy_used
            }
            
            # Generate gap analysis using AI
            gap_analysis = self.ai_service.generate_gap_analysis(analysis_data)
            
            logger.info("✅ AI gap analysis generated")
            return gap_analysis
            
        except Exception as e:
            logger.error(f"❌ Error generating AI gap analysis: {e}")
            return None
    
    def _create_executive_summary(
        self, 
        team_report: DreamTeamReport, 
        gap_analysis: Optional[GapAnalysisReport]
    ) -> str:
        """Create executive summary"""
        
        # Analyze skill coverage
        high_coverage = [s for s in team_report.skill_analysis if s.level == 'High']
        medium_coverage = [s for s in team_report.skill_analysis if s.level == 'Medium']
        low_coverage = [s for s in team_report.skill_analysis if s.level == 'Low']
        
        # Determine competitiveness level
        coverage_score = team_report.overall_coverage_score
        if coverage_score >= 75:
            competitiveness = "HIGHLY COMPETITIVE - Strong alignment across all key areas"
            risk_level = "Low"
        elif coverage_score >= 60:
            competitiveness = "COMPETITIVE - Good coverage with some areas for improvement"
            risk_level = "Medium"
        elif coverage_score >= 45:
            competitiveness = "DEVELOPING - Requires strategic strengthening"
            risk_level = "Medium-High"
        else:
            competitiveness = "NEEDS SIGNIFICANT IMPROVEMENT - Major gaps identified"
            risk_level = "High"
        
        # Create strengths and gaps summary
        strengths_summary = f"{len(high_coverage)} high-coverage areas including " + \
                          ", ".join([s.skill for s in high_coverage[:3]])
        
        if low_coverage:
            gaps_summary = f"{len(low_coverage)} critical gaps requiring attention: " + \
                          ", ".join([s.skill for s in low_coverage[:3]])
        else:
            gaps_summary = "No critical gaps identified"
        
        # Action items
        action_items = []
        if low_coverage:
            action_items.append("Address critical skill gaps through collaboration or recruitment")
        if medium_coverage:
            action_items.append("Strengthen medium-coverage areas through targeted partnerships")
        action_items.append("Leverage high-coverage areas as proposal strengths")
        
        # Bottom line assessment
        bottom_line = f"Team demonstrates {coverage_score:.0f}% alignment with solicitation requirements. " + \
                     ("Proceed with confidence." if coverage_score >= 70 else 
                      "Strengthen identified gaps before submission." if coverage_score >= 50 else
                      "Significant restructuring recommended.")
        
        template = self.template_env.get_template('executive_summary')
        
        return template.render(
            solicitation_title=team_report.solicitation_title,
            coverage_score=coverage_score,
            strategy_used=team_report.strategy_used,
            generated_at=datetime.now().strftime("%B %d, %Y"),
            team_size=len(team_report.team_members),
            pi_name=team_report.team_members[0].name if team_report.team_members else "N/A",
            pi_score=f"{team_report.team_members[0].avg_affinity:.1f}" if team_report.team_members else "N/A",
            strategy_description=self._get_strategy_description(team_report.strategy_used),
            strengths_summary=strengths_summary,
            gaps_summary=gaps_summary,
            risk_level=risk_level,
            competitiveness_assessment=competitiveness,
            action_items="\n".join([f"- {item}" for item in action_items]),
            bottom_line=bottom_line
        )
    
    def _get_strategy_description(self, strategy: str) -> str:
        """Get human-readable strategy description"""
        descriptions = {
            "hybrid": "Hybrid approach combining top performers with coverage optimization",
            "greedy": "Pure optimization strategy maximizing overall team coverage",
            "rankings": "Top-ranked researchers by overall performance"
        }
        return descriptions.get(strategy, strategy)
    
    def _generate_strategic_recommendations(
        self, 
        team_report: DreamTeamReport, 
        gap_analysis: Optional[GapAnalysisReport]
    ) -> str:
        """Generate strategic recommendations"""
        
        recommendations = []
        
        # Coverage-based recommendations
        low_coverage = [s for s in team_report.skill_analysis if s.level == 'Low']
        medium_coverage = [s for s in team_report.skill_analysis if s.level == 'Medium']
        high_coverage = [s for s in team_report.skill_analysis if s.level == 'High']
        
        # Proposal strategy recommendations
        if len(high_coverage) >= 3:
            recommendations.append(
                "**Proposal Strategy:** Lead with team strengths in " + 
                ", ".join([s.skill for s in high_coverage[:3]]) + 
                ". Position these as core competitive advantages."
            )
        
        # Gap mitigation strategies
        if low_coverage:
            recommendations.append("**Gap Mitigation:**")
            for skill in low_coverage[:3]:
                recommendations.append(
                    f"  - {skill.skill}: Consider external collaboration or consultant expertise"
                )
        
        # Team development recommendations
        if medium_coverage:
            recommendations.append(
                "**Team Development:** Invest in strengthening medium-coverage areas through " +
                "targeted training or strategic partnerships."
            )
        
        # Budget allocation guidance
        coverage_score = team_report.overall_coverage_score
        if coverage_score >= 70:
            recommendations.append(
                "**Budget Allocation:** Leverage existing team strengths. " +
                "Minimal external expertise required."
            )
        elif coverage_score >= 50:
            recommendations.append(
                "**Budget Allocation:** Reserve 15-25% of budget for external expertise " +
                "to address identified gaps."
            )
        else:
            recommendations.append(
                "**Budget Allocation:** Significant investment required in external partnerships " +
                "or consultant expertise (25-40% of budget)."
            )
        
        # Timeline recommendations
        if coverage_score >= 70:
            recommendations.append("**Timeline:** Proceed with standard proposal timeline.")
        else:
            recommendations.append(
                "**Timeline:** Allow additional 2-4 weeks for team strengthening activities."
            )
        
        # AI-generated recommendations
        if gap_analysis and hasattr(gap_analysis, 'strategic_recommendations'):
            recommendations.append("**AI-Generated Insights:**")
            for rec in gap_analysis.strategic_recommendations[:3]:
                recommendations.append(f"  - {rec}")
        
        return "\n\n".join(recommendations)
    
    def _collect_supporting_evidence(
        self, 
        team_report: DreamTeamReport, 
        matching_results: MatchingResults
    ) -> str:
        """Collect supporting evidence for the team selection"""
        
        evidence_sections = []
        
        # Team member evidence
        evidence_sections.append("### Team Member Qualifications")
        for member in team_report.team_members:
            evidence_sections.append(f"**{member.name}** ({member.role})")
            evidence_sections.append(f"- Average Affinity Score: {member.avg_affinity:.1f}")
            evidence_sections.append("- Top Expertise Areas:")
            for skill in member.top_skills[:3]:
                evidence_sections.append(f"  - {skill['skill']} (Score: {skill['score']:.1f})")
            evidence_sections.append("")
        
        # Algorithm performance evidence
        evidence_sections.append("### Algorithm Performance")
        evidence_sections.append(f"- Total researchers analyzed: {matching_results.total_researchers}")
        evidence_sections.append(f"- Eligible researchers: {matching_results.eligible_researchers}")
        evidence_sections.append(f"- Processing time: {matching_results.processing_time_seconds:.1f} seconds")
        evidence_sections.append(f"- Skills analyzed: {len(matching_results.skills_analyzed)}")
        
        # Selection methodology evidence
        evidence_sections.append("### Selection Methodology")
        evidence_sections.append(f"- Strategy: {team_report.strategy_used.title()}")
        evidence_sections.append(f"- Affinity matrix dimensions: {team_report.affinity_matrix_shape}")
        evidence_sections.append("- Selection criteria: Academic expertise, grant experience, skill coverage")
        
        return "\n".join(evidence_sections)
    
    def _generate_next_steps(
        self, 
        team_report: DreamTeamReport, 
        gap_analysis: Optional[GapAnalysisReport]
    ) -> str:
        """Generate actionable next steps"""
        
        next_steps = []
        
        # Immediate actions
        next_steps.append("## Immediate Actions (Next 1-2 weeks)")
        
        low_coverage = [s for s in team_report.skill_analysis if s.level == 'Low']
        if low_coverage:
            next_steps.append("1. **Address Critical Gaps:**")
            for skill in low_coverage[:3]:
                next_steps.append(f"   - Identify collaborators for: {skill.skill}")
        else:
            next_steps.append("1. **Leverage Team Strengths:** Develop proposal outline emphasizing high-coverage areas")
        
        next_steps.append("2. **Team Coordination:** Schedule team alignment meeting")
        next_steps.append("3. **Proposal Planning:** Create detailed work plan and timeline")
        
        # Short-term actions
        next_steps.append("\n## Short-term Actions (Next 2-4 weeks)")
        next_steps.append("1. **Proposal Development:** Begin writing based on team strengths")
        next_steps.append("2. **Partnership Development:** Formalize any external collaborations")
        next_steps.append("3. **Budget Planning:** Allocate resources based on team structure")
        
        # Long-term considerations
        next_steps.append("\n## Long-term Considerations")
        coverage_score = team_report.overall_coverage_score
        if coverage_score >= 70:
            next_steps.append("1. **Proposal Submission:** Team is ready for competitive submission")
        else:
            next_steps.append("1. **Team Enhancement:** Consider additional recruitment or partnerships")
        
        next_steps.append("2. **Future Opportunities:** Evaluate team for related solicitations")
        next_steps.append("3. **Continuous Improvement:** Monitor team performance and adjust strategy")
        
        return "\n".join(next_steps)
    
    def create_markdown_report(self, report: ComprehensiveReport) -> str:
        """Create formatted markdown report"""
        
        try:
            # Prepare template data
            template_data = {
                'title': f"Strategic Analysis: {report.solicitation_title}",
                'generated_at': report.generated_at.strftime("%B %d, %Y at %I:%M %p"),
                'solicitation_title': report.solicitation_title,
                'coverage_score': report.team_report.overall_coverage_score,
                'executive_summary': report.executive_summary,
                'team_members': report.team_report.team_members,
                'strategy_used': report.team_report.strategy_used,
                'selection_history': report.team_report.selection_history,
                'skill_analysis': self._prepare_skill_analysis_for_template(report.team_report.skill_analysis),
                'high_coverage_count': len([s for s in report.team_report.skill_analysis if s.level == 'High']),
                'medium_coverage_count': len([s for s in report.team_report.skill_analysis if s.level == 'Medium']),
                'low_coverage_count': len([s for s in report.team_report.skill_analysis if s.level == 'Low']),
                'gap_analysis': report.gap_analysis.analysis_text if report.gap_analysis else "AI analysis not available",
                'strategic_recommendations': report.strategic_recommendations,
                'next_steps': report.next_steps,
                'supporting_evidence': report.supporting_evidence
            }
            
            template = self.template_env.get_template('comprehensive_report')
            markdown_content = template.render(**template_data)
            
            logger.info("✅ Markdown report created successfully")
            return markdown_content
            
        except Exception as e:
            logger.error(f"❌ Error creating markdown report: {e}")
            raise
    
    def _prepare_skill_analysis_for_template(self, skill_analysis) -> List[Dict]:
        """Prepare skill analysis data for template rendering"""
        result = []
        for skill in skill_analysis:
            emoji_map = {'High': '🟢', 'Medium': '🟡', 'Low': '🔴'}
            result.append({
                'skill': skill.skill,
                'coverage_score': skill.coverage_score,
                'level': skill.level,
                'level_emoji': emoji_map.get(skill.level, '⚪'),
                'expert': skill.expert
            })
        return result
    
    def export_report(
        self, 
        report: ComprehensiveReport, 
        format_type: str = "markdown"
    ) -> ReportExport:
        """Export report in specified format"""
        
        try:
            if format_type.lower() == "markdown":
                content = self.create_markdown_report(report)
                
            elif format_type.lower() == "json":
                content = json.dumps(report.dict(), indent=2, default=str)
                
            elif format_type.lower() == "csv":
                content = self._create_csv_export(report)
                
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            return ReportExport(
                solicitation_id=report.solicitation_id,
                format_type=format_type,
                content=content,
                generated_at=datetime.now(),
                metadata={
                    'team_size': len(report.team_report.team_members),
                    'coverage_score': report.team_report.overall_coverage_score,
                    'strategy_used': report.team_report.strategy_used
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error exporting report: {e}")
            raise
    
    def _create_csv_export(self, report: ComprehensiveReport) -> str:
        """Create CSV export of key data"""
        
        # Team members data
        team_data = []
        for member in report.team_report.team_members:
            team_data.append({
                'Name': member.name,
                'Role': member.role,
                'Avg_Affinity': member.avg_affinity,
                'Top_Skill': member.top_skills[0]['skill'] if member.top_skills else '',
                'Selection_Reason': member.selection_reason
            })
        
        # Skills coverage data
        skills_data = []
        for skill in report.team_report.skill_analysis:
            skills_data.append({
                'Skill': skill.skill,
                'Coverage_Score': skill.coverage_score,
                'Level': skill.level,
                'Expert': skill.expert,
                'Expert_Score': skill.expert_score
            })
        
        # Convert to CSV strings
        team_df = pd.DataFrame(team_data)
        skills_df = pd.DataFrame(skills_data)
        
        csv_content = "# Team Members\n"
        csv_content += team_df.to_csv(index=False)
        csv_content += "\n# Skills Coverage\n"
        csv_content += skills_df.to_csv(index=False)
        
        return csv_content
    
    def generate_quick_summary(self, team_report: DreamTeamReport) -> Dict[str, Any]:
        """Generate a quick summary for API responses"""
        
        low_coverage = [s for s in team_report.skill_analysis if s.level == 'Low']
        
        return {
            'solicitation_id': team_report.solicitation_id,
            'overall_score': round(team_report.overall_coverage_score, 1),
            'team_size': len(team_report.team_members),
            'strategy': team_report.strategy_used,
            'pi_name': team_report.team_members[0].name if team_report.team_members else 'N/A',
            'critical_gaps': len(low_coverage),
            'competitiveness': (
                'High' if team_report.overall_coverage_score >= 75 else
                'Medium' if team_report.overall_coverage_score >= 60 else
                'Low'
            ),
            'recommendation': (
                'Proceed with proposal' if team_report.overall_coverage_score >= 70 else
                'Address gaps before submission' if team_report.overall_coverage_score >= 50 else
                'Significant team restructuring needed'
            )
        }