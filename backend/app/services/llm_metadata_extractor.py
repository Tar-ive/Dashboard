"""LLM-powered metadata extraction service for NSF solicitations."""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from groq import Groq

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not available, continue without it

logger = logging.getLogger(__name__)


class ExtractedMetadata(BaseModel):
    """Structured metadata extracted from solicitation sections"""
    award_title: Optional[str] = None
    funding_ceiling: Optional[float] = None
    project_duration_months: Optional[int] = None
    submission_deadline: Optional[str] = None
    
    
class ExtractedRules(BaseModel):
    """Extracted eligibility and institutional rules"""
    pi_eligibility_rules: List[str] = Field(default_factory=list)
    institutional_limitations: List[str] = Field(default_factory=list)
    team_size_constraints: Dict[str, int] = Field(default_factory=dict)


class ExtractedSkills(BaseModel):
    """Extracted required and preferred skills"""
    required_scientific_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    technical_requirements: List[str] = Field(default_factory=list)


class LLMMetadataExtractor:
    """Service for extracting structured metadata from solicitation text using LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        """Initialize LLM metadata extractor with Groq API"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.model = model
        self.client = None
        
        if not self.api_key:
            logger.warning("⚠️ Groq API key not found. LLM metadata extraction will be disabled.")
            return
        
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info("✅ LLM metadata extractor initialized successfully")
        except ImportError:
            logger.error("❌ Groq library not found. Install with: pip install groq")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None

    def _extract_metadata_with_llm(self, section_text: str, section_type: str) -> Dict[str, Any]:
        """
        Extract metadata from a specific section using LLM
        
        Args:
            section_text: The text content of the section
            section_type: Type of section (metadata, rules, skills)
            
        Returns:
            Dictionary containing extracted structured data
        """
        if not self.is_available():
            logger.warning("LLM service not available, returning empty metadata")
            return {}
        
        try:
            prompt = self._create_extraction_prompt(section_text, section_type)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            response_text = response.choices[0].message.content.strip()
            return self._parse_llm_response(response_text, section_type)
            
        except Exception as e:
            logger.error(f"❌ LLM metadata extraction failed for {section_type}: {e}")
            return {}

    def _create_extraction_prompt(self, section_text: str, section_type: str) -> str:
        """Create section-specific extraction prompts"""
        
        if section_type == "metadata":
            return self._create_metadata_prompt(section_text)
        elif section_type == "rules":
            return self._create_rules_prompt(section_text)
        elif section_type == "skills":
            return self._create_skills_prompt(section_text)
        else:
            raise ValueError(f"Unknown section type: {section_type}")

    def _create_metadata_prompt(self, section_text: str) -> str:
        """Create prompt for extracting basic metadata (funding, duration, etc.)"""
        return f"""Extract key metadata from this NSF solicitation section. Focus on funding details, project duration, and submission information.

SECTION TEXT:
{section_text}

Extract the following information and return as valid JSON:
{{
    "award_title": "string - the official title of the award/program",
    "funding_ceiling": "number - maximum funding amount in dollars (extract number only, no currency symbols)",
    "project_duration_months": "number - project duration in months",
    "submission_deadline": "string - submission deadline date in any format mentioned"
}}

Rules:
- Return ONLY valid JSON, no additional text
- Use null for missing information
- For funding_ceiling, extract only the numeric value (e.g., 500000 not "$500,000")
- For project_duration_months, convert years to months if needed (e.g., 3 years = 36 months)
- Extract exact text for award_title and submission_deadline

JSON Response:"""

    def _create_rules_prompt(self, section_text: str) -> str:
        """Create prompt for extracting eligibility rules and constraints"""
        return f"""Extract eligibility rules and institutional constraints from this NSF solicitation section.

SECTION TEXT:
{section_text}

Extract the following information and return as valid JSON:
{{
    "pi_eligibility_rules": ["list of specific PI eligibility requirements"],
    "institutional_limitations": ["list of institutional constraints or limitations"],
    "team_size_constraints": {{"min_team_size": number, "max_team_size": number, "max_pi": number}}
}}

Rules:
- Return ONLY valid JSON, no additional text
- Extract specific, actionable rules (not general statements)
- For pi_eligibility_rules: focus on who can be PI (citizenship, career stage, etc.)
- For institutional_limitations: focus on institutional eligibility, geographic restrictions
- For team_size_constraints: extract any numerical limits on team composition
- Use empty arrays/objects if no relevant information found

JSON Response:"""

    def _create_skills_prompt(self, section_text: str) -> str:
        """Create prompt for extracting required skills and technical requirements"""
        return f"""Extract required scientific skills and technical requirements from this NSF solicitation section.

SECTION TEXT:
{section_text}

Extract the following information and return as valid JSON:
{{
    "required_scientific_skills": ["list of essential scientific/research skills mentioned"],
    "preferred_skills": ["list of preferred or desired skills"],
    "technical_requirements": ["list of specific technical capabilities or tools required"]
}}

Rules:
- Return ONLY valid JSON, no additional text
- Focus on specific skills, not general concepts
- For required_scientific_skills: extract skills that are explicitly required or essential
- For preferred_skills: extract skills that are mentioned as preferred, desired, or advantageous
- For technical_requirements: extract specific tools, software, equipment, or technical capabilities
- Use specific terms (e.g., "machine learning" not "AI", "Python programming" not "coding")
- Use empty arrays if no relevant information found

JSON Response:"""

    def _parse_llm_response(self, response_text: str, section_type: str) -> Dict[str, Any]:
        """Parse LLM response into structured data"""
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
            
            # Validate and clean the parsed data based on section type
            return self._validate_extracted_data(parsed, section_type)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response for {section_type}: {e}")
            logger.debug(f"Raw response: {response_text}")
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to process LLM response for {section_type}: {e}")
            return {}

    def _validate_extracted_data(self, data: Dict[str, Any], section_type: str) -> Dict[str, Any]:
        """Validate and clean extracted data based on section type"""
        try:
            if section_type == "metadata":
                return self._validate_metadata(data)
            elif section_type == "rules":
                return self._validate_rules(data)
            elif section_type == "skills":
                return self._validate_skills(data)
            else:
                return data
        except Exception as e:
            logger.error(f"❌ Data validation failed for {section_type}: {e}")
            return {}

    def _validate_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata extraction results"""
        validated = {}
        
        # Award title
        if "award_title" in data and data["award_title"]:
            validated["award_title"] = str(data["award_title"]).strip()
        
        # Funding ceiling
        if "funding_ceiling" in data and data["funding_ceiling"] is not None:
            try:
                funding = float(data["funding_ceiling"])
                if funding > 0:
                    validated["funding_ceiling"] = funding
            except (ValueError, TypeError):
                logger.warning(f"Invalid funding_ceiling value: {data['funding_ceiling']}")
        
        # Project duration
        if "project_duration_months" in data and data["project_duration_months"] is not None:
            try:
                duration = int(data["project_duration_months"])
                if duration > 0:
                    validated["project_duration_months"] = duration
            except (ValueError, TypeError):
                logger.warning(f"Invalid project_duration_months value: {data['project_duration_months']}")
        
        # Submission deadline
        if "submission_deadline" in data and data["submission_deadline"]:
            validated["submission_deadline"] = str(data["submission_deadline"]).strip()
        
        return validated

    def _validate_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate rules extraction results"""
        validated = {}
        
        # PI eligibility rules
        if "pi_eligibility_rules" in data and isinstance(data["pi_eligibility_rules"], list):
            validated["pi_eligibility_rules"] = [
                str(rule).strip() for rule in data["pi_eligibility_rules"] 
                if rule and str(rule).strip()
            ]
        else:
            validated["pi_eligibility_rules"] = []
        
        # Institutional limitations
        if "institutional_limitations" in data and isinstance(data["institutional_limitations"], list):
            validated["institutional_limitations"] = [
                str(limit).strip() for limit in data["institutional_limitations"] 
                if limit and str(limit).strip()
            ]
        else:
            validated["institutional_limitations"] = []
        
        # Team size constraints
        if "team_size_constraints" in data and isinstance(data["team_size_constraints"], dict):
            constraints = {}
            for key, value in data["team_size_constraints"].items():
                try:
                    if value is not None:
                        constraints[key] = int(value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid team size constraint {key}: {value}")
            validated["team_size_constraints"] = constraints
        else:
            validated["team_size_constraints"] = {}
        
        return validated

    def _validate_skills(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate skills extraction results"""
        validated = {}
        
        # Required scientific skills
        if "required_scientific_skills" in data and isinstance(data["required_scientific_skills"], list):
            validated["required_scientific_skills"] = [
                str(skill).strip() for skill in data["required_scientific_skills"] 
                if skill and str(skill).strip()
            ]
        else:
            validated["required_scientific_skills"] = []
        
        # Preferred skills
        if "preferred_skills" in data and isinstance(data["preferred_skills"], list):
            validated["preferred_skills"] = [
                str(skill).strip() for skill in data["preferred_skills"] 
                if skill and str(skill).strip()
            ]
        else:
            validated["preferred_skills"] = []
        
        # Technical requirements
        if "technical_requirements" in data and isinstance(data["technical_requirements"], list):
            validated["technical_requirements"] = [
                str(req).strip() for req in data["technical_requirements"] 
                if req and str(req).strip()
            ]
        else:
            validated["technical_requirements"] = []
        
        return validated

    def extract_all_metadata(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract all metadata from multiple sections
        
        Args:
            sections: Dictionary mapping section names to their text content
            
        Returns:
            Dictionary containing all extracted metadata
        """
        all_metadata = {
            "metadata": {},
            "rules": {},
            "skills": {},
            "extraction_summary": {
                "sections_processed": 0,
                "successful_extractions": 0,
                "failed_extractions": 0,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Map section names to extraction types
        section_mapping = {
            "award_information": "metadata",
            "program_description": "skills",
            "eligibility_information": "rules",
            "proposal_preparation_instructions": "skills",
            "review_information": "skills"
        }
        
        for section_name, section_text in sections.items():
            if not section_text or not section_text.strip():
                continue
                
            all_metadata["extraction_summary"]["sections_processed"] += 1
            
            # Determine extraction type
            extraction_type = section_mapping.get(section_name, "skills")
            
            try:
                extracted = self._extract_metadata_with_llm(section_text, extraction_type)
                
                if extracted:
                    # Merge extracted data
                    if extraction_type not in all_metadata:
                        all_metadata[extraction_type] = {}
                    
                    for key, value in extracted.items():
                        if isinstance(value, list):
                            if key not in all_metadata[extraction_type]:
                                all_metadata[extraction_type][key] = []
                            all_metadata[extraction_type][key].extend(value)
                        elif isinstance(value, dict):
                            if key not in all_metadata[extraction_type]:
                                all_metadata[extraction_type][key] = {}
                            all_metadata[extraction_type][key].update(value)
                        else:
                            all_metadata[extraction_type][key] = value
                    
                    all_metadata["extraction_summary"]["successful_extractions"] += 1
                else:
                    all_metadata["extraction_summary"]["failed_extractions"] += 1
                    
            except Exception as e:
                logger.error(f"❌ Failed to extract from section {section_name}: {e}")
                all_metadata["extraction_summary"]["failed_extractions"] += 1
        
        return all_metadata