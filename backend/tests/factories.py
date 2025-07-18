"""
Test data factories for generating realistic test data.

This module provides factory classes for creating consistent, realistic test data
for researchers, solicitations, matching results, and other domain objects.

The factories support:
- ResearcherFactory: Generate realistic researcher profiles with academic metrics
- SolicitationFactory: Create NSF solicitation documents with proper structure
- MatchingResultFactory: Build expected matching outcomes with scoring
- TestDataBuilder: Compose complex test scenarios
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from faker import Faker

# Initialize faker for generating realistic data
fake = Faker()

# Set seed for reproducible test data when needed
def set_test_seed(seed: int = 42):
    """Set seed for reproducible test data generation."""
    random.seed(seed)
    fake.seed_instance(seed)

class ResearcherFactory:
    """Factory for generating realistic researcher test data."""
    
    # Common academic disciplines and expertise areas
    DISCIPLINES = [
        "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology",
        "Engineering", "Psychology", "Economics", "Statistics", "Data Science"
    ]
    
    EXPERTISE_AREAS = {
        "Computer Science": [
            "machine learning", "artificial intelligence", "computer vision",
            "natural language processing", "deep learning", "neural networks",
            "data mining", "algorithms", "software engineering", "cybersecurity"
        ],
        "Mathematics": [
            "applied mathematics", "statistics", "optimization", "numerical analysis",
            "mathematical modeling", "probability theory", "linear algebra",
            "differential equations", "discrete mathematics", "topology"
        ],
        "Physics": [
            "quantum physics", "condensed matter", "particle physics",
            "astrophysics", "computational physics", "optics", "thermodynamics",
            "electromagnetism", "materials science", "biophysics"
        ],
        "Engineering": [
            "electrical engineering", "mechanical engineering", "civil engineering",
            "biomedical engineering", "chemical engineering", "aerospace engineering",
            "systems engineering", "robotics", "control systems", "signal processing"
        ]
    }
    
    INSTITUTIONS = [
        "MIT", "Stanford University", "Harvard University", "UC Berkeley",
        "Carnegie Mellon University", "Georgia Tech", "University of Washington",
        "University of Michigan", "Cornell University", "Princeton University",
        "Yale University", "Columbia University", "University of Chicago",
        "Northwestern University", "Duke University", "Rice University"
    ]
    
    @classmethod
    def create_researcher(cls, **kwargs) -> Dict[str, Any]:
        """Create a single researcher with realistic data."""
        discipline = kwargs.get('discipline', random.choice(cls.DISCIPLINES))
        expertise_pool = cls.EXPERTISE_AREAS.get(discipline, cls.EXPERTISE_AREAS["Computer Science"])
        
        # Generate realistic career metrics
        years_active = random.randint(3, 30)
        base_publications = max(1, int(years_active * random.uniform(1.5, 4.0)))
        h_index = max(1, int(base_publications * random.uniform(0.3, 0.7)))
        
        researcher = {
            "researcher_id": kwargs.get('researcher_id', str(uuid.uuid4())),
            "name": kwargs.get('name', fake.name()),
            "email": kwargs.get('email', fake.email()),
            "institution": kwargs.get('institution', random.choice(cls.INSTITUTIONS)),
            "department": kwargs.get('department', discipline),
            "title": kwargs.get('title', random.choice([
                "Assistant Professor", "Associate Professor", "Professor",
                "Research Scientist", "Principal Investigator", "Postdoc"
            ])),
            "expertise": kwargs.get('expertise', random.sample(expertise_pool, k=random.randint(3, 7))),
            "publications": kwargs.get('publications', base_publications),
            "h_index": kwargs.get('h_index', h_index),
            "years_active": kwargs.get('years_active', years_active),
            "grants_received": kwargs.get('grants_received', random.randint(0, max(1, years_active // 3))),
            "collaboration_score": kwargs.get('collaboration_score', random.uniform(0.1, 1.0)),
            "recent_activity": kwargs.get('recent_activity', random.uniform(0.5, 1.0))
        }
        
        return researcher
    
    @classmethod
    def create_researcher_batch(cls, count: int, **common_kwargs) -> List[Dict[str, Any]]:
        """Create a batch of researchers with optional common attributes."""
        return [cls.create_researcher(**common_kwargs) for _ in range(count)]
    
    @classmethod
    def create_diverse_researcher_set(cls, count: int) -> List[Dict[str, Any]]:
        """Create a diverse set of researchers across different disciplines."""
        researchers = []
        disciplines_cycle = cls.DISCIPLINES * (count // len(cls.DISCIPLINES) + 1)
        
        for i in range(count):
            discipline = disciplines_cycle[i]
            researcher = cls.create_researcher(discipline=discipline)
            researchers.append(researcher)
        
        return researchers
    
    @classmethod
    def create_expert_researcher(cls, expertise_area: str, **kwargs) -> Dict[str, Any]:
        """Create a researcher with high expertise in a specific area."""
        # Find the discipline that contains this expertise area
        discipline = "Computer Science"  # default
        for disc, areas in cls.EXPERTISE_AREAS.items():
            if expertise_area.lower() in [area.lower() for area in areas]:
                discipline = disc
                break
        
        # Create a senior researcher with high metrics
        return cls.create_researcher(
            discipline=discipline,
            expertise=[expertise_area] + random.sample(
                cls.EXPERTISE_AREAS.get(discipline, []), k=random.randint(2, 4)
            ),
            years_active=kwargs.get('years_active', random.randint(10, 25)),
            publications=kwargs.get('publications', random.randint(30, 100)),
            h_index=kwargs.get('h_index', random.randint(15, 50)),
            grants_received=kwargs.get('grants_received', random.randint(3, 15)),
            title=kwargs.get('title', random.choice(["Associate Professor", "Professor"])),
            **kwargs
        )
    
    @classmethod
    def create_junior_researcher(cls, **kwargs) -> Dict[str, Any]:
        """Create a junior researcher with lower metrics."""
        return cls.create_researcher(
            years_active=kwargs.get('years_active', random.randint(1, 5)),
            publications=kwargs.get('publications', random.randint(1, 15)),
            h_index=kwargs.get('h_index', random.randint(1, 8)),
            grants_received=kwargs.get('grants_received', random.randint(0, 2)),
            title=kwargs.get('title', random.choice(["Postdoc", "Assistant Professor"])),
            **kwargs
        )
    
    @classmethod
    def create_collaboration_network(cls, size: int, common_expertise: List[str] = None) -> List[Dict[str, Any]]:
        """Create a network of researchers with overlapping expertise for collaboration testing."""
        if common_expertise is None:
            common_expertise = ["machine learning", "data science"]
        
        researchers = []
        for i in range(size):
            # Each researcher has some common expertise plus unique areas
            unique_expertise = random.sample(
                cls.EXPERTISE_AREAS["Computer Science"], k=random.randint(2, 4)
            )
            combined_expertise = list(set(common_expertise + unique_expertise))
            
            researcher = cls.create_researcher(
                expertise=combined_expertise,
                collaboration_score=random.uniform(0.6, 1.0)  # Higher collaboration scores
            )
            researchers.append(researcher)
        
        return researchers


class SolicitationFactory:
    """Factory for generating realistic NSF solicitation test data."""
    
    NSF_PROGRAMS = [
        "MFAI", "ExpandAI", "CISE", "ENG", "MPS", "BIO", "GEO", "SBE",
        "EHR", "TIP", "OISE", "OAC", "CCF", "CNS", "IIS", "SCC"
    ]
    
    RESEARCH_AREAS = [
        "Artificial Intelligence", "Machine Learning", "Data Science",
        "Cybersecurity", "Quantum Computing", "Robotics", "Bioinformatics",
        "Climate Science", "Materials Science", "Renewable Energy",
        "Healthcare Technology", "Educational Technology", "Smart Cities"
    ]
    
    BUDGET_RANGES = [
        "100000-300000", "300000-500000", "500000-1000000",
        "1000000-2000000", "2000000-5000000"
    ]
    
    @classmethod
    def create_solicitation(cls, **kwargs) -> Dict[str, Any]:
        """Create a single solicitation with realistic data."""
        program = kwargs.get('program', random.choice(cls.NSF_PROGRAMS))
        research_area = kwargs.get('research_area', random.choice(cls.RESEARCH_AREAS))
        
        # Generate realistic title
        title_templates = [
            f"{research_area} Foundations and Applications",
            f"Advancing {research_area} Research",
            f"{research_area}: Theory and Practice",
            f"Mathematical Foundations of {research_area}",
            f"Interdisciplinary {research_area} Initiative"
        ]
        
        solicitation = {
            "solicitation_id": kwargs.get('solicitation_id', str(uuid.uuid4())),
            "filename": kwargs.get('filename', f"NSF-{program}-{fake.random_int(min=1000, max=9999)}.pdf"),
            "title": kwargs.get('title', random.choice(title_templates)),
            "program": program,
            "research_area": research_area,
            "deadline": kwargs.get('deadline', fake.date_between(start_date='+30d', end_date='+365d')),
            "budget_range": kwargs.get('budget_range', random.choice(cls.BUDGET_RANGES)),
            "description": kwargs.get('description', cls._generate_description(research_area)),
            "keywords": kwargs.get('keywords', cls._generate_keywords(research_area)),
            "requirements": kwargs.get('requirements', cls._generate_requirements()),
            "abstract": kwargs.get('abstract', cls._generate_abstract(research_area)),
            "text_length": kwargs.get('text_length', random.randint(5000, 25000)),
            "sections_found": kwargs.get('sections_found', [
                "Abstract", "Program Description", "Award Information",
                "Eligibility Information", "Proposal Preparation Instructions"
            ]),
            "upload_time": kwargs.get('upload_time', fake.date_time_between(start_date='-30d')),
            "status": kwargs.get('status', "completed")
        }
        
        return solicitation
    
    @classmethod
    def _generate_description(cls, research_area: str) -> str:
        """Generate a realistic solicitation description."""
        templates = [
            f"This program supports fundamental research in {research_area.lower()} with emphasis on theoretical foundations and practical applications.",
            f"The {research_area} initiative seeks to advance the state of the art through innovative research approaches.",
            f"This solicitation invites proposals for groundbreaking research in {research_area.lower()} that addresses critical challenges."
        ]
        return random.choice(templates)
    
    @classmethod
    def _generate_keywords(cls, research_area: str) -> List[str]:
        """Generate relevant keywords for the research area."""
        base_keywords = research_area.lower().split()
        
        additional_keywords = {
            "artificial intelligence": ["neural networks", "deep learning", "machine learning"],
            "machine learning": ["algorithms", "data mining", "pattern recognition"],
            "cybersecurity": ["network security", "cryptography", "threat detection"],
            "quantum computing": ["quantum algorithms", "quantum information", "quantum systems"],
            "robotics": ["autonomous systems", "human-robot interaction", "robot learning"]
        }
        
        keywords = base_keywords.copy()
        if research_area.lower() in additional_keywords:
            keywords.extend(additional_keywords[research_area.lower()])
        
        # Add some general research keywords
        general_keywords = ["research", "innovation", "collaboration", "interdisciplinary"]
        keywords.extend(random.sample(general_keywords, k=2))
        
        return keywords[:8]  # Limit to 8 keywords
    
    @classmethod
    def _generate_requirements(cls) -> List[str]:
        """Generate typical NSF proposal requirements."""
        return [
            "Principal Investigator must be affiliated with eligible institution",
            "Proposal must include detailed budget justification",
            "Research plan should demonstrate broader impacts",
            "Collaboration with industry partners encouraged",
            "Open source software development preferred"
        ]
    
    @classmethod
    def _generate_abstract(cls, research_area: str) -> str:
        """Generate a realistic abstract."""
        return f"This solicitation seeks innovative research proposals in {research_area.lower()} " \
               f"that will advance scientific understanding and create practical applications. " \
               f"Proposals should demonstrate clear intellectual merit and broader impacts to society."
    
    @classmethod
    def create_solicitation_batch(cls, count: int, **common_kwargs) -> List[Dict[str, Any]]:
        """Create a batch of solicitations."""
        return [cls.create_solicitation(**common_kwargs) for _ in range(count)]


class MatchingResultFactory:
    """Factory for generating realistic matching results test data."""
    
    @classmethod
    def create_researcher_match(cls, researcher: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create a researcher match result."""
        # Generate realistic scoring
        base_score = random.uniform(0.3, 0.9)
        noise_factor = random.uniform(0.8, 1.2)
        
        match = {
            "researcher_id": researcher["researcher_id"],
            "researcher_name": researcher["name"],
            "academic_expertise_score": kwargs.get('academic_expertise_score', base_score * noise_factor),
            "s_sparse": kwargs.get('s_sparse', random.uniform(0.1, 0.8)),
            "s_dense": kwargs.get('s_dense', random.uniform(0.2, 0.9)),
            "f_ge": kwargs.get('f_ge', min(1.0, researcher.get('grants_received', 0) * 0.2 + 0.5)),
            "final_affinity_score": kwargs.get('final_affinity_score', base_score),
            "total_papers": researcher.get('publications', random.randint(5, 50)),
            "eligibility_status": kwargs.get('eligibility_status', "eligible")
        }
        
        return match
    
    @classmethod
    def create_matching_results(cls, solicitation: Dict[str, Any], 
                              researchers: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Create complete matching results."""
        # Create matches for researchers
        matches = []
        for researcher in researchers:
            match = cls.create_researcher_match(researcher)
            matches.append(match)
        
        # Sort by final affinity score
        matches.sort(key=lambda x: x["final_affinity_score"], reverse=True)
        
        # Take top N matches
        top_n = kwargs.get('top_n_results', 20)
        top_matches = matches[:top_n]
        
        results = {
            "solicitation_id": solicitation["solicitation_id"],
            "solicitation_title": solicitation["title"],
            "eligible_researchers": len([m for m in matches if m["eligibility_status"] == "eligible"]),
            "total_researchers": len(researchers),
            "top_matches": top_matches,
            "skills_analyzed": solicitation.get("keywords", [])[:10],
            "processing_time_seconds": kwargs.get('processing_time_seconds', random.uniform(1.0, 10.0)),
            "generated_at": kwargs.get('generated_at', datetime.now())
        }
        
        return results
    
    @classmethod
    def create_dream_team_member(cls, researcher: Dict[str, Any], role: str, **kwargs) -> Dict[str, Any]:
        """Create a dream team member."""
        member = {
            "researcher_id": researcher["researcher_id"],
            "name": researcher["name"],
            "role": role,
            "avg_affinity": kwargs.get('avg_affinity', random.uniform(0.6, 0.95)),
            "top_skills": kwargs.get('top_skills', [
                {"skill": skill, "score": random.uniform(0.7, 1.0)}
                for skill in researcher.get("expertise", [])[:3]
            ]),
            "selection_reason": kwargs.get('selection_reason', f"Selected as {role} due to strong expertise match")
        }
        
        return member
    
    @classmethod
    def create_dream_team_report(cls, solicitation: Dict[str, Any], 
                               team_members: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Create a complete dream team report."""
        report = {
            "solicitation_id": solicitation["solicitation_id"],
            "solicitation_title": solicitation["title"],
            "team_members": team_members,
            "overall_coverage_score": kwargs.get('overall_coverage_score', random.uniform(0.75, 0.95)),
            "skill_analysis": kwargs.get('skill_analysis', cls._generate_skill_analysis(solicitation, team_members)),
            "strategic_analysis": kwargs.get('strategic_analysis', "This team provides excellent coverage of required skills with strong collaboration potential."),
            "selection_history": kwargs.get('selection_history', cls._generate_selection_history(team_members)),
            "strategy_used": kwargs.get('strategy_used', "hybrid"),
            "generated_at": kwargs.get('generated_at', datetime.now()),
            "affinity_matrix_shape": kwargs.get('affinity_matrix_shape', (len(team_members), 10))
        }
        
        return report
    
    @classmethod
    def _generate_skill_analysis(cls, solicitation: Dict[str, Any], 
                               team_members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate skill coverage analysis."""
        skills = solicitation.get("keywords", ["machine learning", "data science", "algorithms"])
        analysis = []
        
        for skill in skills[:5]:  # Limit to 5 skills
            coverage = {
                "skill": skill,
                "coverage_score": random.uniform(0.6, 1.0),
                "level": random.choice(["High", "Medium", "Low"]),
                "expert": random.choice(team_members)["name"] if team_members else "Unknown",
                "expert_score": random.uniform(0.8, 1.0)
            }
            analysis.append(coverage)
        
        return analysis
    
    @classmethod
    def _generate_selection_history(cls, team_members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate selection step history."""
        history = []
        
        for i, member in enumerate(team_members):
            step = {
                "step": i + 1,
                "action": f"Selected {member['role']}",
                "researcher_name": member["name"],
                "reason": f"Best match for {member['role']} position",
                "team_coverage": random.uniform(0.5 + i * 0.1, 0.9)
            }
            history.append(step)
        
        return history


class TestDataBuilder:
    """Builder class for creating complex test scenarios."""
    
    def __init__(self):
        self.researchers = []
        self.solicitations = []
        self.matching_results = []
    
    def with_researchers(self, count: int, **kwargs) -> 'TestDataBuilder':
        """Add researchers to the test data set."""
        self.researchers.extend(ResearcherFactory.create_researcher_batch(count, **kwargs))
        return self
    
    def with_diverse_researchers(self, count: int) -> 'TestDataBuilder':
        """Add diverse researchers across disciplines."""
        self.researchers.extend(ResearcherFactory.create_diverse_researcher_set(count))
        return self
    
    def with_solicitations(self, count: int, **kwargs) -> 'TestDataBuilder':
        """Add solicitations to the test data set."""
        self.solicitations.extend(SolicitationFactory.create_solicitation_batch(count, **kwargs))
        return self
    
    def with_matching_results(self, **kwargs) -> 'TestDataBuilder':
        """Generate matching results for existing solicitations and researchers."""
        for solicitation in self.solicitations:
            result = MatchingResultFactory.create_matching_results(
                solicitation, self.researchers, **kwargs
            )
            self.matching_results.append(result)
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the complete test data set."""
        return {
            "researchers": self.researchers,
            "solicitations": self.solicitations,
            "matching_results": self.matching_results
        }


# Convenience functions for common test scenarios
def create_basic_test_scenario() -> Dict[str, Any]:
    """Create a basic test scenario with researchers, solicitations, and matches."""
    return (TestDataBuilder()
            .with_diverse_researchers(20)
            .with_solicitations(3)
            .with_matching_results()
            .build())


def create_large_test_scenario() -> Dict[str, Any]:
    """Create a large test scenario for performance testing."""
    return (TestDataBuilder()
            .with_diverse_researchers(100)
            .with_solicitations(10)
            .with_matching_results()
            .build())


def create_ai_focused_scenario() -> Dict[str, Any]:
    """Create a test scenario focused on AI research."""
    return (TestDataBuilder()
            .with_researchers(15, discipline="Computer Science")
            .with_solicitations(2, research_area="Artificial Intelligence")
            .with_matching_results()
            .build())