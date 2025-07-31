"""
Text Processing Engine for abstract reconstruction, keyword extraction, and embedding generation.
"""
import re
import logging
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text processing tasks for the research pipeline."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the text processor.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._initialize_nltk()
        
    def _initialize_nltk(self):
        """Initialize NLTK resources."""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            
            self.stop_words = set(stopwords.words('english'))
            logger.info("NLTK resources initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NLTK: {e}")
            # Fallback to basic stop words and simple tokenization
            self.stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
            }
    
    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None:
            try:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise
    
    def reconstruct_abstract(self, inverted_index: Dict) -> str:
        """
        Reconstruct abstract text from OpenAlex inverted index format.
        
        Args:
            inverted_index: Dictionary mapping words to position lists
            
        Returns:
            Reconstructed abstract text
        """
        if not inverted_index:
            return ""
        
        try:
            # Create a list to hold words at their positions
            word_positions = []
            
            for word, positions in inverted_index.items():
                if isinstance(positions, list):
                    for pos in positions:
                        word_positions.append((pos, word))
                else:
                    # Handle case where positions is not a list
                    word_positions.append((positions, word))
            
            # Sort by position and extract words
            word_positions.sort(key=lambda x: x[0])
            words = [word for _, word in word_positions]
            
            # Join words with spaces
            abstract = " ".join(words)
            
            logger.debug(f"Reconstructed abstract ({len(words)} words): {abstract[:100]}...")
            return abstract
            
        except Exception as e:
            logger.error(f"Error reconstructing abstract: {e}")
            return ""
    
    def create_proxy_abstract(self, topics: List[Dict]) -> str:
        """
        Create a proxy abstract from topic information when abstract is unavailable.
        
        Args:
            topics: List of topic dictionaries with 'display_name' and 'score'
            
        Returns:
            Generated proxy abstract text
        """
        if not topics:
            return ""
        
        try:
            # Sort topics by score (highest first)
            sorted_topics = sorted(topics, key=lambda x: x.get('score', 0), reverse=True)
            
            # Take top topics and create a descriptive text
            top_topics = [topic.get('display_name', '') for topic in sorted_topics[:5] if topic.get('display_name')]
            
            if top_topics:
                proxy_abstract = f"This research work focuses on {', '.join(top_topics[:-1])} and {top_topics[-1]}." if len(top_topics) > 1 else f"This research work focuses on {top_topics[0]}."
                logger.debug(f"Created proxy abstract from {len(top_topics)} topics")
                return proxy_abstract
            else:
                return "Research work with unspecified topics."
                
        except Exception as e:
            logger.error(f"Error creating proxy abstract: {e}")
            return "Research work with unspecified topics."
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Input text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        if not text:
            return []
        
        try:
            # Clean and tokenize text
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            
            # Try NLTK tokenization first, fallback to simple split
            try:
                tokens = word_tokenize(text)
            except Exception:
                # Fallback to simple tokenization
                tokens = text.split()
            
            # Filter out stop words and short words
            filtered_tokens = [
                token for token in tokens 
                if token not in self.stop_words 
                and len(token) > 2 
                and token.isalpha()
            ]
            
            # Get word frequencies
            word_freq = Counter(filtered_tokens)
            
            # Extract most common words as keywords
            keywords = [word for word, _ in word_freq.most_common(max_keywords)]
            
            logger.debug(f"Extracted {len(keywords)} keywords from text")
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate vector embedding for text using sentence transformer.
        
        Args:
            text: Input text to generate embedding for
            
        Returns:
            384-dimensional vector embedding as list of floats, or None if failed
        """
        if not text:
            return None
        
        try:
            self._load_model()
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list and ensure it's 384 dimensions
            embedding_list = embedding.tolist()
            
            if len(embedding_list) != 384:
                logger.warning(f"Unexpected embedding dimension: {len(embedding_list)}, expected 384")
            
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def process_work_text(self, work_data: Dict) -> Dict:
        """
        Process all text-related aspects of a work (abstract, keywords, embedding).
        
        Args:
            work_data: Dictionary containing work information
            
        Returns:
            Dictionary with processed text data
        """
        result = {
            'abstract': '',
            'keywords': [],
            'embedding': None
        }
        
        try:
            if not work_data:
                logger.warning("Empty work_data provided")
                return result
            
            # 1. Get or reconstruct abstract
            abstract = work_data.get('abstract')
            
            if not abstract:
                # Try to reconstruct from inverted index
                inverted_index = work_data.get('abstract_inverted_index')
                if inverted_index:
                    abstract = self.reconstruct_abstract(inverted_index)
                    logger.debug("Reconstructed abstract from inverted index")
            
            if not abstract:
                # Create proxy abstract from topics
                topics = work_data.get('topics', [])
                abstract = self.create_proxy_abstract(topics)
                logger.debug("Created proxy abstract from topics")
            
            result['abstract'] = abstract or ''
            
            # 2. Extract keywords
            if abstract:
                keywords = self.extract_keywords(abstract)
                result['keywords'] = keywords
            
            # 3. Generate embedding from title + abstract
            title = work_data.get('title', '')
            embedding_text = f"{title} {abstract}".strip()
            
            if embedding_text:
                embedding = self.generate_embedding(embedding_text)
                result['embedding'] = embedding
            
            logger.debug(f"Processed text for work: {title[:50] if title else 'Unknown'}...")
            return result
            
        except Exception as e:
            logger.error(f"Error processing work text: {e}")
            return result