import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class GapAnalysisResult(BaseModel):
    critical_gaps: List[str]
    moderate_gaps: List[str]
    strategic_recommendations: List[str]
    competitiveness_score: float
    risk_assessment: str
    mitigation_strategies: List[str]
    collaboration_opportunities: List[str]
    budget_considerations: List[str]

class AIService:
    """Service for AI-powered analysis using Groq API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI service with Groq API key"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = None
        
        if not self.api_key:
            logger.warning("⚠️ Groq API key not found. AI features will be disabled.")
            logger.info("💡 Set GROQ_API_KEY environment variable to enable AI features")
            return
        
        try:
            # Initialize Groq client
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            
            # Test the connection with a minimal request
            # self._test_connection()  # Optional validation
            
            logger.info("✅ Groq AI service initialized successfully")
        except ImportError:
            logger.error("❌ Groq library not found. Install with: pip install groq")
            logger.info("💡 AI features will be disabled. Install groq library.")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {e}")
            logger.info("💡 AI features will be disabled. Check your groq library version.")
            self.client = None

    def _test_connection(self) -> bool:
        """Test the Groq connection with a minimal request"""
        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",  # Fast, efficient model for testing
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10,
                temperature=0.1
            )
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
        
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None
        
    def debug_groq_setup(self) -> Dict[str, Any]:
        """Debug method to check Groq setup"""
        try:
            debug_info = {
                "api_key_present": bool(self.api_key),
                "api_key_length": len(self.api_key) if self.api_key else 0,
                "client_initialized": self.client is not None,
            }
            
            # Try to import groq and get version info
            try:
                import groq
                debug_info["groq_library_available"] = True
                debug_info["groq_version"] = getattr(groq, "__version__", "unknown")
                debug_info["available_classes"] = [attr for attr in dir(groq) if not attr.startswith('_')]
            except ImportError:
                debug_info["groq_library_available"] = False
                debug_info["groq_version"] = "not installed"
            
            # Test a simple API call if client is available
            if self.client:
                try:
                    test_response = self.client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    debug_info["api_test_successful"] = True
                    debug_info["test_response_length"] = len(test_response.choices[0].message.content)
                except Exception as e:
                    debug_info["api_test_successful"] = False
                    debug_info["api_test_error"] = str(e)
            
            return debug_info
            
        except Exception as e:
            return {"error": str(e), "setup_failed": True}
    
    def generate_gap_analysis(self, team_report: Dict, solicitation_data: Dict, 
                            matching_results: Dict) -> GapAnalysisResult:
        """
        Generate comprehensive gap analysis using Groq API
        
        Args:
            team_report: Dream team assembly results
            solicitation_data: Original solicitation analysis
            matching_results: Researcher matching results
            
        Returns:
            GapAnalysisResult with detailed analysis
        """
        if not self.is_available():
            return self._generate_fallback_analysis(team_report, solicitation_data)
        
        try:
            # Prepare comprehensive prompt
            prompt = self._create_gap_analysis_prompt(team_report, solicitation_data, matching_results)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",  # Use larger model for complex analysis
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            return self._parse_gap_analysis_response(analysis_text)
            
        except Exception as e:
            logger.error(f"❌ Gap analysis generation failed: {e}")
            return self._generate_fallback_analysis(team_report, solicitation_data)
    
    def _create_gap_analysis_prompt(self, team_report: Dict, solicitation_data: Dict, 
                                  matching_results: Dict) -> str:
        """Create detailed prompt for gap analysis"""
        
        # Extract key information
        team_members = team_report.get('team_members', [])
        overall_coverage = team_report.get('overall_coverage_score', 0)
        skill_analysis = team_report.get('skill_analysis', [])
        solicitation_title = solicitation_data.get('title', 'Unknown Solicitation')
        skills_analyzed = matching_results.get('skills_analyzed', [])
        
        # Categorize skills by coverage level
        high_coverage_skills = [s for s in skill_analysis if s.get('level') == 'High']
        medium_coverage_skills = [s for s in skill_analysis if s.get('level') == 'Medium']
        low_coverage_skills = [s for s in skill_analysis if s.get('level') == 'Low']
        
        # Create team summary
        team_summary = "\n".join([
            f"- {member.get('name', 'Unknown')} ({member.get('role', 'Researcher')}): "
            f"Avg Affinity {member.get('avg_affinity', 0):.1f}, "
            f"Top Skills: {', '.join([skill.get('skill', 'N/A') for skill in member.get('top_skills', [])[:2]])}"
            for member in team_members
        ])
        
        prompt = f"""You are an expert research strategy consultant analyzing a team's fit for an NSF solicitation. Provide a comprehensive gap analysis in valid JSON format.

SOLICITATION: {solicitation_title}

TEAM COMPOSITION:
{team_summary}

COVERAGE ANALYSIS:
- Overall Team Coverage Score: {overall_coverage:.1f}/100
- High Coverage Skills ({len(high_coverage_skills)}): {', '.join([s.get('skill', 'N/A') for s in high_coverage_skills])}
- Medium Coverage Skills ({len(medium_coverage_skills)}): {', '.join([s.get('skill', 'N/A') for s in medium_coverage_skills])}
- Low Coverage Skills ({len(low_coverage_skills)}): {', '.join([s.get('skill', 'N/A') for s in low_coverage_skills])}

REQUIRED SKILLS FOR SOLICITATION:
{chr(10).join([f"- {skill}" for skill in skills_analyzed])}

Provide your analysis in this exact JSON format - respond ONLY with valid JSON:
{{
    "critical_gaps": ["list of 3-5 most critical skill/expertise gaps that pose significant risk"],
    "moderate_gaps": ["list of 3-5 areas that need attention but are manageable"],
    "strategic_recommendations": ["list of 5-8 specific, actionable recommendations to strengthen the proposal"],
    "competitiveness_score": [float between 0-100 representing overall competitiveness],
    "risk_assessment": "paragraph describing main risks and likelihood of success",
    "mitigation_strategies": ["list of 4-6 specific strategies to address identified gaps"],
    "collaboration_opportunities": ["list of 3-5 types of external collaborators or institutions to consider"],
    "budget_considerations": ["list of 3-4 budget allocation recommendations based on gaps"]
}}

Consider these factors in your analysis:
1. Technical expertise alignment with solicitation requirements
2. Grant experience and track record
3. Team diversity and complementary skills
4. Feasibility of addressing gaps within proposal timeline
5. Competitive landscape for this type of solicitation
6. Specific NSF evaluation criteria

Be specific, actionable, and realistic in your recommendations. Focus on strengthening the proposal's competitiveness.

IMPORTANT: Respond with ONLY the JSON object, no additional text or formatting."""

        return prompt
    
    def _parse_gap_analysis_response(self, response_text: str) -> GapAnalysisResult:
        """Parse Groq's response into structured result"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Extract JSON from response (handle cases where there's extra text)
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            else:
                json_text = response_text
            
            # Parse JSON
            parsed = json.loads(json_text)
            
            return GapAnalysisResult(
                critical_gaps=parsed.get('critical_gaps', []),
                moderate_gaps=parsed.get('moderate_gaps', []),
                strategic_recommendations=parsed.get('strategic_recommendations', []),
                competitiveness_score=float(parsed.get('competitiveness_score', 50.0)),
                risk_assessment=parsed.get('risk_assessment', 'Analysis unavailable'),
                mitigation_strategies=parsed.get('mitigation_strategies', []),
                collaboration_opportunities=parsed.get('collaboration_opportunities', []),
                budget_considerations=parsed.get('budget_considerations', [])
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to parse gap analysis response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return self._create_fallback_gap_analysis()
    
    def generate_strategic_recommendations(self, team_data: Dict, 
                                         skill_gaps: List[str]) -> Dict[str, Any]:
        """Generate detailed strategic recommendations"""
        if not self.is_available():
            return self._generate_fallback_recommendations(skill_gaps)
        
        try:
            prompt = f"""You are a research strategy expert. Based on this team analysis and identified gaps, provide specific strategic recommendations.

TEAM DATA:
{json.dumps(team_data, indent=2)}

IDENTIFIED GAPS:
{chr(10).join([f"- {gap}" for gap in skill_gaps])}

Provide recommendations in JSON format - respond ONLY with valid JSON:
{{
    "immediate_actions": ["3-5 actions to take before proposal submission"],
    "team_strengthening": ["3-4 ways to strengthen current team"],
    "external_partnerships": ["3-4 specific types of partnerships to pursue"],
    "proposal_strategy": ["4-5 strategic approaches for the proposal narrative"],
    "timeline_recommendations": ["3-4 timeline considerations"],
    "success_factors": ["3-5 key factors that will determine success"]
}}

Be specific and actionable. Respond with ONLY the JSON object."""
            
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            else:
                json_text = response_text
            
            return json.loads(json_text)
            
        except Exception as e:
            logger.error(f"❌ Strategic recommendations generation failed: {e}")
            return self._generate_fallback_recommendations(skill_gaps)
    
    def analyze_team_competitiveness(self, team_coverage: float, 
                                   skill_analysis: List[Dict]) -> Dict[str, Any]:
        """Analyze team competitiveness against typical successful proposals"""
        if not self.is_available():
            return self._generate_fallback_competitiveness(team_coverage)
        
        try:
            # Prepare skill summary
            skill_summary = "\n".join([
                f"- {skill.get('skill', 'Unknown')}: {skill.get('coverage_score', 0):.1f} "
                f"({skill.get('level', 'Unknown')} coverage)"
                for skill in skill_analysis
            ])
            
            prompt = f"""Analyze this research team's competitiveness for NSF funding based on coverage analysis.

OVERALL COVERAGE SCORE: {team_coverage:.1f}/100

SKILL BREAKDOWN:
{skill_summary}

Based on typical NSF evaluation criteria and successful proposal patterns, provide analysis in JSON format - respond ONLY with valid JSON:
{{
    "competitiveness_rating": "[Excellent/Strong/Competitive/Developing/Weak]",
    "percentile_estimate": [0-100 estimate of where this team ranks],
    "key_strengths": ["3-4 main competitive advantages"],
    "key_weaknesses": ["3-4 main areas of concern"],
    "probability_assessment": {{
        "high_confidence_success": [0-100 percentage],
        "moderate_success": [0-100 percentage],
        "needs_significant_improvement": [0-100 percentage]
    }},
    "benchmark_comparison": "paragraph comparing to typical successful NSF teams",
    "improvement_priority": ["top 3 areas to focus improvement efforts"]
}}

Consider NSF's emphasis on intellectual merit, broader impacts, team qualifications, and feasibility. Respond with ONLY the JSON object."""
            
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.2
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            else:
                json_text = response_text
            
            return json.loads(json_text)
            
        except Exception as e:
            logger.error(f"❌ Competitiveness analysis failed: {e}")
            return self._generate_fallback_competitiveness(team_coverage)
    
    def generate_executive_summary(self, full_analysis: Dict) -> str:
        """Generate executive summary of all analyses"""
        if not self.is_available():
            return self._generate_fallback_executive_summary(full_analysis)
        
        try:
            prompt = f"""Create a concise executive summary for research leadership based on this comprehensive team analysis.

ANALYSIS DATA:
{json.dumps(full_analysis, indent=2)}

Create a 2-3 paragraph executive summary that:
1. Opens with overall assessment and competitiveness
2. Highlights 2-3 key strengths and 2-3 critical gaps
3. Provides clear next steps and timeline

Write for senior research administrators who need to make go/no-go decisions on proposal submissions.
Use clear, professional language with specific metrics where relevant.

Provide ONLY the executive summary text, no additional formatting or labels."""
            
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Executive summary generation failed: {e}")
            return self._generate_fallback_executive_summary(full_analysis)
    
    # Fallback methods for when AI is unavailable
    def _generate_fallback_analysis(self, team_report: Dict, 
                                  solicitation_data: Dict) -> GapAnalysisResult:
        """Generate basic analysis without AI"""
        skill_analysis = team_report.get('skill_analysis', [])
        overall_coverage = team_report.get('overall_coverage_score', 0)
        
        low_skills = [s for s in skill_analysis if s.get('level') == 'Low']
        medium_skills = [s for s in skill_analysis if s.get('level') == 'Medium']
        
        return GapAnalysisResult(
            critical_gaps=[s.get('skill', 'Unknown') for s in low_skills[:3]],
            moderate_gaps=[s.get('skill', 'Unknown') for s in medium_skills[:3]],
            strategic_recommendations=[
                "Review team composition for missing expertise areas",
                "Consider external collaborations for critical gaps",
                "Strengthen proposal narrative around team strengths",
                "Allocate budget for consultant expertise if needed"
            ],
            competitiveness_score=max(overall_coverage * 0.8, 30.0),
            risk_assessment=f"Team shows {overall_coverage:.1f}% coverage. "
                          f"{'Strong foundation' if overall_coverage >= 70 else 'Moderate alignment' if overall_coverage >= 50 else 'Significant gaps identified'}.",
            mitigation_strategies=[
                "Identify and recruit additional team members",
                "Establish partnerships with complementary institutions",
                "Allocate resources for training and development"
            ],
            collaboration_opportunities=[
                "Research institutions with complementary expertise",
                "Industry partners for practical applications",
                "International collaborations for broader impact"
            ],
            budget_considerations=[
                "Allocate funds for external consultant expertise",
                "Include travel budget for collaboration meetings",
                "Consider equipment needs for gap areas"
            ]
        )
    
    def _create_fallback_gap_analysis(self) -> GapAnalysisResult:
        """Create minimal gap analysis when parsing fails"""
        return GapAnalysisResult(
            critical_gaps=["Analysis unavailable - AI service error"],
            moderate_gaps=[],
            strategic_recommendations=["Review team manually for gaps"],
            competitiveness_score=50.0,
            risk_assessment="Unable to assess due to AI service limitations",
            mitigation_strategies=["Manual review recommended"],
            collaboration_opportunities=["Consider external partnerships"],
            budget_considerations=["Standard budget allocation recommended"]
        )
    
    def _generate_fallback_recommendations(self, skill_gaps: List[str]) -> Dict[str, Any]:
        """Generate basic recommendations without AI"""
        return {
            "immediate_actions": [
                "Review identified skill gaps",
                "Assess team member capabilities",
                "Identify potential collaborators"
            ],
            "team_strengthening": [
                "Recruit additional expertise",
                "Provide targeted training",
                "Establish mentorship relationships"
            ],
            "external_partnerships": [
                "University collaborations",
                "Industry partnerships",
                "International collaborations"
            ],
            "proposal_strategy": [
                "Emphasize team strengths",
                "Address gaps transparently",
                "Include development plans"
            ],
            "timeline_recommendations": [
                "Allow time for team building",
                "Plan early collaboration meetings",
                "Schedule regular progress reviews"
            ],
            "success_factors": [
                "Strong team coordination",
                "Clear role definitions",
                "Effective communication"
            ]
        }
    
    def _generate_fallback_competitiveness(self, team_coverage: float) -> Dict[str, Any]:
        """Generate basic competitiveness analysis without AI"""
        if team_coverage >= 80:
            rating = "Strong"
            percentile = 75
        elif team_coverage >= 60:
            rating = "Competitive"
            percentile = 60
        elif team_coverage >= 40:
            rating = "Developing"
            percentile = 40
        else:
            rating = "Weak"
            percentile = 25
        
        return {
            "competitiveness_rating": rating,
            "percentile_estimate": percentile,
            "key_strengths": ["Quantitative analysis completed", "Systematic evaluation"],
            "key_weaknesses": ["Limited by fallback analysis", "Manual review needed"],
            "probability_assessment": {
                "high_confidence_success": max(0, team_coverage - 20),
                "moderate_success": 30,
                "needs_significant_improvement": min(100, 100 - team_coverage)
            },
            "benchmark_comparison": f"Based on coverage score of {team_coverage:.1f}%, "
                                  f"team appears {rating.lower()} compared to typical proposals.",
            "improvement_priority": ["Manual gap analysis", "Expert review", "Team enhancement"]
        }
    
    def _generate_fallback_executive_summary(self, full_analysis: Dict) -> str:
        """Generate basic executive summary without AI"""
        coverage = full_analysis.get('team_coverage', 0)
        return f"""
EXECUTIVE SUMMARY - NSF Proposal Team Analysis

The assembled research team demonstrates {coverage:.1f}% alignment with solicitation requirements. 
{'This represents a strong foundation for a competitive proposal' if coverage >= 70 else 
 'This indicates moderate alignment with room for improvement' if coverage >= 50 else 
 'This suggests significant gaps that require attention before submission'}.

Key recommendations include manual review of team composition, identification of specific 
expertise gaps, and consideration of external collaborations to strengthen the proposal. 
A detailed analysis using AI services is recommended when available.

Timeline: Allow 2-4 weeks for team optimization before proposal submission.
"""