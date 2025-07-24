"""
Enhanced skill extraction system with dual-model validation.
Combines expert LLM prompting with OpenAlex BERT topic classification for high-quality skill extraction.
"""

import json
import time
import logging
import re
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import streamlit as st

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Core dependencies
import numpy as np

# Optional dependencies with graceful fallback
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


@dataclass
class SkillExtractionResult:
    """Results from dual-model skill extraction."""
    llm_skills: List[str]
    openalex_topics: List[str]
    merged_skills: List[str]
    quality_score: float
    extraction_time: float
    source_method: str
    confidence_scores: Dict[str, float]
    metadata: Dict[str, Any]


@dataclass
class SkillQualityMetrics:
    """Quality assessment for extracted skills."""
    skill_count: int
    avg_skill_length: float
    atomic_skill_ratio: float  # Percentage of skills that are 2-5 words
    technical_focus_score: float  # How well skills focus on technical content
    uniqueness_score: float  # Diversity of extracted skills
    format_compliance_score: float  # How well skills follow expected format


class EnhancedSkillExtractor:
    """
    Advanced skill extraction using LLM prompting and OpenAlex topic classification.
    Implements dual-model validation with intelligent skill merging.
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize with expert LLM prompt and OpenAlex classifier."""
        # Use provided key or load from environment
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.groq_client = None
        self.topic_classifier = None
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize components
        self._initialize_groq_client()
        self._initialize_openalex_classifier()
        
        # Expert prompt template
        self.expert_prompt_template = self._load_expert_prompt()
        
        # Performance monitoring
        self.performance_stats = {
            'total_extractions': 0,
            'groq_extractions': 0,
            'openalex_extractions': 0,
            'extraction_times': [],
            'quality_scores': [],
            'error_count': 0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for skill extraction operations."""
        logger = logging.getLogger('enhanced_skill_extractor')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_groq_client(self):
        """Initialize Groq client with error handling."""
        if not GROQ_AVAILABLE:
            self.logger.warning("⚠️ Groq library not available. Install with: pip install groq")
            return
        
        if not self.groq_api_key:
            self.logger.warning("⚠️ GROQ_API_KEY not found in environment variables")
            return
        
        try:
            self.groq_client = Groq(api_key=self.groq_api_key)
            self.logger.info(f"✅ Groq client initialized successfully (key length: {len(self.groq_api_key)})")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Groq client: {e}")
            self.groq_client = None
    
    def _initialize_openalex_classifier(self):
        """Initialize OpenAlex BERT classifier with error handling."""
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("⚠️ Transformers library not available. OpenAlex classification will be disabled.")
            return
        
        try:
            self.topic_classifier = pipeline(
                "text-classification",
                model="OpenAlex/bert-base-multilingual-cased-finetuned-openalex-topic-classification-title-abstract",
                return_all_scores=True
            )
            self.logger.info("✅ OpenAlex topic classifier initialized successfully")
        except Exception as e:
            self.logger.warning(f"⚠️ OpenAlex classifier setup failed: {e}")
            self.topic_classifier = None
    
    def _load_expert_prompt(self) -> str:
        """Load the expert-role LLM prompt template."""
        return """Your Role:
You are an expert NSF Program Manager and a research taxonomist. Your job is to deconstruct a grant solicitation's scientific and technical description into a granular list of the core, fundable areas of expertise required for a successful proposal.

Your Task:
Read the complete solicitation text provided below. From this text, identify and extract the most critical and distinct skills, technologies, and research areas.

Critical Instructions & Constraints:
- Output Format: Your final output MUST be a clean JSON list of strings. Do not include any other text, explanation, or preamble.
- Skill Granularity: Extract between 8 and 15 distinct skills. The goal is to be comprehensive and specific.
- Skill Format: Each skill MUST be a short, concise noun phrase, typically 2-5 words long. Do NOT use full sentences.
- Content Focus: Focus exclusively on the scientific and technical requirements. IGNORE generic administrative language, funding amounts, deadlines, or boilerplate phrases like "broader impacts" or "intellectual merit."

Example:
Input Text: "This Small Business Innovation Research (SBIR) Phase I project addresses the growing threat of social engineering cyber-attacks, which exploit human vulnerabilities. The opportunity lies in developing an automated, scalable intelligence-gathering system. This project proposes a novel approach using interactive artificial intelligence (AI) chatbot investigators, powered by large language models (LLMs), to engage with social engineering scammers and trace their tactics. Key research objectives include developing novel natural language processing techniques to create an AI agent that can autonomously engage with threats and a system capable of deploying chatbot networks for large-scale threat intelligence."

Your Correct Output:
["Social Engineering Countermeasures", "Human Vulnerability Analysis", "Scalable Intelligence Gathering", "AI Chatbot Investigator Design", "Large Language Model (LLM) Deployment", "Natural Language Processing Techniques", "Autonomous AI Agents", "Large-Scale Threat Intelligence", "Cybercriminal Network Mapping"]

Now, apply this logic to the following complete solicitation text:
{solicitation_text}"""
    
    @st.cache_data
    def extract_skills_dual_model(_self, solicitation_text: str) -> SkillExtractionResult:
        """
        Extract skills using both LLM and OpenAlex, then merge results.
        
        Args:
            solicitation_text: Raw text content from solicitation
            
        Returns:
            SkillExtractionResult with combined extraction results
        """
        start_time = time.time()
        
        try:
            # Extract skills using both methods
            llm_skills = _self.extract_skills_llm(solicitation_text)
            openalex_topics = _self.extract_skills_openalex(solicitation_text)
            
            # Merge skill sources intelligently
            merged_skills = _self.merge_skill_sources(llm_skills, openalex_topics)
            
            # Validate skill quality
            quality_metrics = _self.validate_skill_quality(merged_skills)
            
            # Calculate extraction time
            extraction_time = time.time() - start_time
            
            # Determine primary source method
            source_method = _self._determine_source_method(llm_skills, openalex_topics)
            
            # Calculate confidence scores
            confidence_scores = {
                'llm_confidence': 1.0 if llm_skills else 0.0,
                'openalex_confidence': 1.0 if openalex_topics else 0.0,
                'merge_confidence': quality_metrics.format_compliance_score
            }
            
            # Update performance stats
            _self._update_performance_stats(extraction_time, quality_metrics.technical_focus_score)
            
            result = SkillExtractionResult(
                llm_skills=llm_skills,
                openalex_topics=openalex_topics,
                merged_skills=merged_skills,
                quality_score=quality_metrics.technical_focus_score,
                extraction_time=extraction_time,
                source_method=source_method,
                confidence_scores=confidence_scores,
                metadata={
                    'quality_metrics': asdict(quality_metrics),
                    'text_length': len(solicitation_text),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            _self.logger.info(
                f"✅ Dual-model extraction completed: {len(merged_skills)} skills "
                f"(LLM: {len(llm_skills)}, OpenAlex: {len(openalex_topics)}) "
                f"in {extraction_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            extraction_time = time.time() - start_time
            _self.logger.error(f"❌ Dual-model extraction failed: {e}")
            
            # Return fallback result
            return SkillExtractionResult(
                llm_skills=[],
                openalex_topics=[],
                merged_skills=[],
                quality_score=0.0,
                extraction_time=extraction_time,
                source_method="error",
                confidence_scores={'error': 0.0},
                metadata={'error': str(e)}
            )
    
    def extract_skills_llm(self, solicitation_text: str) -> List[str]:
        """
        Use expert-role LLM prompt to extract 8-15 atomic skills.
        
        Args:
            solicitation_text: Raw text content from solicitation
            
        Returns:
            List of extracted skills from LLM
        """
        if not self.groq_client:
            self.logger.warning("⚠️ Groq client not available, using fallback extraction")
            return self._extract_skills_fallback(solicitation_text)
        
        try:
            # Prepare prompt with solicitation text
            prompt = self.expert_prompt_template.format(solicitation_text=solicitation_text)
            
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",  # Updated to current model
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500,
                top_p=0.9
            )
            
            # Extract and parse response
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                skills = json.loads(response_text)
                if isinstance(skills, list):
                    # Clean and validate skills
                    cleaned_skills = self._clean_llm_skills(skills)
                    self.logger.info(f"✅ LLM extracted {len(cleaned_skills)} skills")
                    return cleaned_skills
                else:
                    self.logger.warning("⚠️ LLM response was not a list")
                    return self._extract_skills_fallback(solicitation_text)
            except json.JSONDecodeError:
                self.logger.warning(f"⚠️ Failed to parse LLM JSON response: {response_text[:200]}...")
                # Try to extract skills from malformed response
                extracted_skills = self._extract_skills_from_text(response_text)
                if extracted_skills:
                    return extracted_skills
                else:
                    return self._extract_skills_fallback(solicitation_text)
                
        except Exception as e:
            self.logger.error(f"❌ LLM skill extraction failed: {e}")
            return self._extract_skills_fallback(solicitation_text)
    
    def extract_skills_openalex(self, solicitation_text: str) -> List[str]:
        """
        Use OpenAlex BERT classifier for topic-based skill extraction.
        
        Args:
            solicitation_text: Raw text content from solicitation
            
        Returns:
            List of topic-based skills from OpenAlex
        """
        if not self.topic_classifier:
            self.logger.warning("⚠️ OpenAlex classifier not available, skipping topic extraction")
            return []
        
        try:
            # Truncate text to model limits (512 tokens ~ 2000 characters)
            text_sample = solicitation_text[:2000]
            
            # Get topic classifications
            results = self.topic_classifier(text_sample)
            
            # Handle different response formats
            topics = []
            if isinstance(results, list) and len(results) > 0:
                # Results is a list of classification results
                if isinstance(results[0], list):
                    # Nested list format - take first result
                    classification_results = results[0]
                else:
                    # Direct list format
                    classification_results = results
                
                # Extract top topics with confidence > 0.1
                for result in classification_results:
                    if isinstance(result, dict) and 'score' in result and 'label' in result:
                        if result['score'] > 0.1:  # Confidence threshold
                            topic_skill = self._topic_to_skill(result['label'])
                            if topic_skill:
                                topics.append(topic_skill)
            
            # Limit to top 10 topics
            topics = topics[:10]
            
            self.logger.info(f"✅ OpenAlex extracted {len(topics)} topic-based skills")
            return topics
            
        except Exception as e:
            self.logger.error(f"❌ OpenAlex skill extraction failed: {e}")
            # Fallback to basic keyword extraction
            return self._extract_skills_fallback(solicitation_text)
    
    def merge_skill_sources(self, llm_skills: List[str], openalex_topics: List[str]) -> List[str]:
        """
        Intelligently combine and deduplicate skills from both sources.
        
        Args:
            llm_skills: Skills extracted from LLM
            openalex_topics: Skills extracted from OpenAlex
            
        Returns:
            Merged and deduplicated list of skills
        """
        # Start with LLM skills (higher priority)
        merged_skills = llm_skills.copy()
        
        # Add OpenAlex topics that don't overlap with LLM skills
        for topic in openalex_topics:
            if not self._is_skill_duplicate(topic, merged_skills):
                merged_skills.append(topic)
        
        # Ensure we have 8-15 skills
        if len(merged_skills) < 8:
            # If we have too few, add more from OpenAlex
            for topic in openalex_topics:
                if len(merged_skills) >= 8:
                    break
                if topic not in merged_skills:
                    merged_skills.append(topic)
        elif len(merged_skills) > 15:
            # If we have too many, prioritize LLM skills
            merged_skills = llm_skills[:10] + openalex_topics[:5]
            merged_skills = merged_skills[:15]
        
        # Final cleanup and validation
        cleaned_skills = [self._clean_skill(skill) for skill in merged_skills if skill.strip()]
        cleaned_skills = [skill for skill in cleaned_skills if len(skill.split()) <= 5]
        
        return cleaned_skills[:15]  # Hard limit
    
    def validate_skill_quality(self, skills: List[str]) -> SkillQualityMetrics:
        """
        Assess skill extraction quality and format compliance.
        
        Args:
            skills: List of extracted skills
            
        Returns:
            SkillQualityMetrics with quality assessment
        """
        if not skills:
            return SkillQualityMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Basic metrics
        skill_count = len(skills)
        avg_skill_length = sum(len(skill.split()) for skill in skills) / len(skills)
        
        # Atomic skill ratio (2-5 words)
        atomic_skills = [skill for skill in skills if 2 <= len(skill.split()) <= 5]
        atomic_skill_ratio = len(atomic_skills) / len(skills)
        
        # Technical focus score (presence of technical terms)
        technical_terms = [
            'ai', 'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'algorithm', 'data', 'analysis', 'modeling',
            'simulation', 'optimization', 'research', 'development', 'innovation',
            'technology', 'system', 'framework', 'methodology', 'technique'
        ]
        
        technical_score = 0
        for skill in skills:
            skill_lower = skill.lower()
            if any(term in skill_lower for term in technical_terms):
                technical_score += 1
        technical_focus_score = technical_score / len(skills)
        
        # Uniqueness score (diversity)
        unique_words = set()
        for skill in skills:
            unique_words.update(skill.lower().split())
        uniqueness_score = len(unique_words) / (len(skills) * avg_skill_length) if avg_skill_length > 0 else 0
        
        # Format compliance score
        format_score = 0
        for skill in skills:
            words = skill.split()
            if 2 <= len(words) <= 5 and skill[0].isupper() and not skill.endswith('.'):
                format_score += 1
        format_compliance_score = format_score / len(skills)
        
        return SkillQualityMetrics(
            skill_count=skill_count,
            avg_skill_length=avg_skill_length,
            atomic_skill_ratio=atomic_skill_ratio,
            technical_focus_score=technical_focus_score,
            uniqueness_score=min(1.0, uniqueness_score),
            format_compliance_score=format_compliance_score
        )
    
    def create_skill_comparison_interface(self, result: SkillExtractionResult) -> None:
        """
        Create skill comparison interface showing Groq LLM vs OpenAlex results side-by-side.
        
        Args:
            result: SkillExtractionResult to display
        """
        st.subheader("🔍 Dual-Model Skill Extraction Comparison")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Skills", len(result.merged_skills))
        with col2:
            st.metric("Quality Score", f"{result.quality_score:.2f}")
        with col3:
            st.metric("Extraction Time", f"{result.extraction_time:.2f}s")
        with col4:
            st.metric("Primary Source", result.source_method.title())
        
        # Side-by-side comparison
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🤖 LLM Skills (Groq)")
            if result.llm_skills:
                for i, skill in enumerate(result.llm_skills, 1):
                    st.markdown(f"{i}. {skill}")
            else:
                st.info("No LLM skills extracted")
        
        with col2:
            st.markdown("### 📚 OpenAlex Topics")
            if result.openalex_topics:
                for i, topic in enumerate(result.openalex_topics, 1):
                    st.markdown(f"{i}. {topic}")
            else:
                st.info("No OpenAlex topics extracted")
        
        with col3:
            st.markdown("### ✨ Merged Skills")
            if result.merged_skills:
                for i, skill in enumerate(result.merged_skills, 1):
                    # Highlight source
                    if skill in result.llm_skills and skill in result.openalex_topics:
                        st.markdown(f"{i}. {skill} 🔄")  # Both sources
                    elif skill in result.llm_skills:
                        st.markdown(f"{i}. {skill} 🤖")  # LLM source
                    elif skill in result.openalex_topics:
                        st.markdown(f"{i}. {skill} 📚")  # OpenAlex source
                    else:
                        st.markdown(f"{i}. {skill}")
            else:
                st.warning("No skills extracted")
        
        # Quality metrics
        if 'quality_metrics' in result.metadata:
            st.markdown("### 📊 Quality Metrics")
            metrics = result.metadata['quality_metrics']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Atomic Skills", f"{metrics['atomic_skill_ratio']:.1%}")
                st.metric("Avg Length", f"{metrics['avg_skill_length']:.1f} words")
            with col2:
                st.metric("Technical Focus", f"{metrics['technical_focus_score']:.1%}")
                st.metric("Uniqueness", f"{metrics['uniqueness_score']:.1%}")
            with col3:
                st.metric("Format Compliance", f"{metrics['format_compliance_score']:.1%}")
        
        # Confidence scores
        st.markdown("### 🎯 Confidence Scores")
        conf_col1, conf_col2, conf_col3 = st.columns(3)
        with conf_col1:
            llm_conf = result.confidence_scores.get('llm_confidence', 0)
            st.metric("LLM Confidence", f"{llm_conf:.1%}")
        with conf_col2:
            openalex_conf = result.confidence_scores.get('openalex_confidence', 0)
            st.metric("OpenAlex Confidence", f"{openalex_conf:.1%}")
        with conf_col3:
            merge_conf = result.confidence_scores.get('merge_confidence', 0)
            st.metric("Merge Quality", f"{merge_conf:.1%}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = self.performance_stats.copy()
        
        if stats['extraction_times']:
            stats['avg_extraction_time'] = sum(stats['extraction_times']) / len(stats['extraction_times'])
            stats['max_extraction_time'] = max(stats['extraction_times'])
            stats['min_extraction_time'] = min(stats['extraction_times'])
        
        if stats['quality_scores']:
            stats['avg_quality_score'] = sum(stats['quality_scores']) / len(stats['quality_scores'])
        
        stats['success_rate'] = (
            (stats['total_extractions'] - stats['error_count']) / stats['total_extractions']
            if stats['total_extractions'] > 0 else 0
        )
        
        return stats
    
    # Helper methods
    
    def _clean_llm_skills(self, skills: List[str]) -> List[str]:
        """Clean and validate LLM-extracted skills."""
        cleaned = []
        for skill in skills:
            if isinstance(skill, str):
                clean_skill = self._clean_skill(skill)
                if clean_skill and 2 <= len(clean_skill.split()) <= 5:
                    cleaned.append(clean_skill)
        return cleaned[:15]  # Limit to 15 skills
    
    def _clean_skill(self, skill: str) -> str:
        """Clean individual skill string."""
        # Remove extra whitespace and normalize
        skill = ' '.join(skill.split())
        
        # Remove quotes and brackets
        skill = re.sub(r'^["\'\[\(]+|["\'\]\)]+$', '', skill)
        
        # Capitalize first letter
        if skill:
            skill = skill[0].upper() + skill[1:]
        
        return skill.strip()
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from malformed LLM response."""
        # Try to find list-like patterns
        patterns = [
            r'"([^"]+)"',  # Quoted strings
            r'\d+\.\s*([^\n]+)',  # Numbered list
            r'[-•]\s*([^\n]+)',  # Bullet points
        ]
        
        skills = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clean_skill = self._clean_skill(match)
                if clean_skill and 2 <= len(clean_skill.split()) <= 5:
                    skills.append(clean_skill)
        
        return skills[:15]
    
    def _topic_to_skill(self, topic_label: str) -> str:
        """Convert OpenAlex topic label to skill format."""
        # OpenAlex topics are often in format like "Computer Science.Artificial Intelligence"
        if '.' in topic_label:
            parts = topic_label.split('.')
            # Use the most specific part
            skill = parts[-1]
        else:
            skill = topic_label
        
        # Clean and format
        skill = skill.replace('_', ' ').replace('-', ' ')
        skill = ' '.join(word.capitalize() for word in skill.split())
        
        return skill
    
    def _is_skill_duplicate(self, skill: str, existing_skills: List[str]) -> bool:
        """Check if skill is duplicate of existing skills."""
        skill_words = set(skill.lower().split())
        
        for existing in existing_skills:
            existing_words = set(existing.lower().split())
            
            # Check for significant overlap (>50% of words)
            overlap = len(skill_words & existing_words)
            min_words = min(len(skill_words), len(existing_words))
            
            if min_words > 0 and overlap / min_words > 0.5:
                return True
        
        return False
    
    def _determine_source_method(self, llm_skills: List[str], openalex_topics: List[str]) -> str:
        """Determine primary source method based on extraction results."""
        if llm_skills and openalex_topics:
            return "dual-model"
        elif llm_skills:
            return "llm"
        elif openalex_topics:
            return "openalex"
        else:
            return "none"
    
    def _extract_skills_fallback(self, solicitation_text: str) -> List[str]:
        """
        Fallback skill extraction using keyword-based approach.
        
        Args:
            solicitation_text: Raw text content from solicitation
            
        Returns:
            List of extracted skills using keyword approach
        """
        # Technical keywords and phrases commonly found in research solicitations
        technical_keywords = {
            'artificial intelligence': 'Artificial Intelligence',
            'machine learning': 'Machine Learning',
            'deep learning': 'Deep Learning',
            'neural network': 'Neural Networks',
            'natural language processing': 'Natural Language Processing',
            'computer vision': 'Computer Vision',
            'data science': 'Data Science',
            'data mining': 'Data Mining',
            'big data': 'Big Data Analytics',
            'cloud computing': 'Cloud Computing',
            'cybersecurity': 'Cybersecurity',
            'blockchain': 'Blockchain Technology',
            'robotics': 'Robotics',
            'automation': 'Process Automation',
            'optimization': 'Optimization Algorithms',
            'simulation': 'Computational Simulation',
            'modeling': 'Mathematical Modeling',
            'algorithm': 'Algorithm Development',
            'software engineering': 'Software Engineering',
            'database': 'Database Systems',
            'network': 'Network Systems',
            'distributed systems': 'Distributed Systems',
            'parallel computing': 'Parallel Computing',
            'high performance computing': 'High Performance Computing',
            'bioinformatics': 'Bioinformatics',
            'computational biology': 'Computational Biology',
            'statistics': 'Statistical Analysis',
            'data visualization': 'Data Visualization',
            'user interface': 'User Interface Design',
            'human computer interaction': 'Human Computer Interaction',
            'research methodology': 'Research Methodology',
            'experimental design': 'Experimental Design'
        }
        
        # Extract skills based on keyword presence
        text_lower = solicitation_text.lower()
        found_skills = []
        
        for keyword, skill_name in technical_keywords.items():
            if keyword in text_lower:
                found_skills.append(skill_name)
        
        # If we found skills, return them
        if found_skills:
            # Remove duplicates and limit to 15
            unique_skills = list(dict.fromkeys(found_skills))[:15]
            self.logger.info(f"✅ Fallback extraction found {len(unique_skills)} skills")
            return unique_skills
        
        # If no technical keywords found, extract from common research terms
        research_patterns = [
            r'research in ([^,.]+)',
            r'development of ([^,.]+)',
            r'study of ([^,.]+)',
            r'analysis of ([^,.]+)',
            r'investigation of ([^,.]+)',
            r'exploration of ([^,.]+)'
        ]
        
        pattern_skills = []
        for pattern in research_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                clean_match = self._clean_skill(match.strip())
                if clean_match and 2 <= len(clean_match.split()) <= 5:
                    pattern_skills.append(clean_match)
        
        if pattern_skills:
            unique_pattern_skills = list(dict.fromkeys(pattern_skills))[:10]
            self.logger.info(f"✅ Fallback pattern extraction found {len(unique_pattern_skills)} skills")
            return unique_pattern_skills
        
        # Last resort: return generic AI/research skills
        generic_skills = [
            "Artificial Intelligence Research",
            "Data Analysis",
            "Research Methodology",
            "Technical Innovation",
            "Computational Methods",
            "Algorithm Development",
            "System Design",
            "Performance Optimization"
        ]
        
        self.logger.info("✅ Using generic research skills as fallback")
        return generic_skills
    
    def _update_performance_stats(self, extraction_time: float, quality_score: float):
        """Update performance monitoring statistics."""
        self.performance_stats['total_extractions'] += 1
        self.performance_stats['extraction_times'].append(extraction_time)
        self.performance_stats['quality_scores'].append(quality_score)
        
        # Keep only last 100 entries to prevent memory bloat
        if len(self.performance_stats['extraction_times']) > 100:
            self.performance_stats['extraction_times'] = self.performance_stats['extraction_times'][-100:]
            self.performance_stats['quality_scores'] = self.performance_stats['quality_scores'][-100:]