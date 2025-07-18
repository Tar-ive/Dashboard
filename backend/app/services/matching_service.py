import numpy as np
import pandas as pd
import pickle
import time
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from app.models.matching import ResearcherMatch, MatchingResults
from app.models.solicitation import SolicitationAnalysis
from datetime import datetime

class MatchingService:
    """Core matching service that implements hybrid search algorithm"""
    
    def __init__(self):
        self.alpha = 0.7  # TF-IDF weight
        self.beta = 0.3   # Dense weight
        self.data_loaded = False
        self.sentence_model = None
        self.load_preprocessed_data()
    
    def load_preprocessed_data(self):
        """Load all preprocessed researcher data with error handling"""
        try:
            data_dir = Path("data/models")
            
            # Check if data directory exists
            if not data_dir.exists():
                print(f"⚠️ Data directory {data_dir} not found. Creating sample data structure...")
                self._create_sample_data_structure(data_dir)
                return
            
            print("📂 Loading preprocessed researcher data...")
            
            # Load TF-IDF model with error handling
            tfidf_path = data_dir / 'tfidf_model.pkl'
            if tfidf_path.exists():
                try:
                    # Try normal loading first
                    with open(tfidf_path, 'rb') as f:
                        self.tfidf_model = pickle.load(f)
                    print("✅ TF-IDF model loaded successfully")
                except (AttributeError, ModuleNotFoundError) as e:
                    print(f"⚠️ TF-IDF model has compatibility issues: {e}")
                    print("🔧 Attempting to load with custom unpickler...")
                    try:
                        # Create a custom unpickler that handles missing classes
                        self.tfidf_model = self._load_pickle_safely(tfidf_path)
                        if self.tfidf_model:
                            print("✅ TF-IDF model loaded with compatibility mode")
                        else:
                            print("❌ Could not load TF-IDF model - will use fallback")
                            self.tfidf_model = None
                    except Exception as e2:
                        print(f"❌ Could not load TF-IDF model: {e2}")
                        self.tfidf_model = None
            else:
                print(f"⚠️ TF-IDF model file not found at {tfidf_path}")
                self.tfidf_model = None
            
            # Load researcher vectors
            vectors_path = data_dir / 'researcher_vectors.npz'
            if vectors_path.exists():
                try:
                    researcher_data = np.load(vectors_path, allow_pickle=True)
                    vectors = researcher_data['vectors']
                    researcher_ids = researcher_data['researcher_ids']
                    self.researcher_vectors = dict(zip(researcher_ids, vectors))
                    print(f"✅ Loaded researcher vectors for {len(self.researcher_vectors)} researchers")
                except Exception as e:
                    print(f"❌ Could not load researcher vectors: {e}")
                    self.researcher_vectors = {}
            else:
                print(f"⚠️ Researcher vectors file not found at {vectors_path}")
                self.researcher_vectors = {}
            
            # Load conceptual profiles
            profiles_path = data_dir / 'conceptual_profiles.npz'
            if profiles_path.exists():
                try:
                    conceptual_data = np.load(profiles_path, allow_pickle=True)
                    embeddings = conceptual_data['embeddings']
                    work_ids = conceptual_data['work_ids']
                    self.conceptual_profiles = dict(zip(work_ids, embeddings))
                    print(f"✅ Loaded conceptual profiles for {len(self.conceptual_profiles)} papers")
                except Exception as e:
                    print(f"❌ Could not load conceptual profiles: {e}")
                    self.conceptual_profiles = {}
            else:
                print(f"⚠️ Conceptual profiles file not found at {profiles_path}")
                self.conceptual_profiles = {}
            
            # Load researcher metadata with better error handling
            metadata_path = data_dir / 'researcher_metadata.parquet'
            if metadata_path.exists():
                try:
                    self.researcher_metadata = pd.read_parquet(metadata_path)
                    print(f"✅ Loaded metadata for {len(self.researcher_metadata)} researchers")
                except Exception as e:
                    print(f"❌ Could not load researcher metadata: {e}")
                    print("🔧 Attempting to create fallback metadata...")
                    self.researcher_metadata = self._create_fallback_metadata()
            else:
                print(f"⚠️ Researcher metadata file not found at {metadata_path}")
                self.researcher_metadata = self._create_fallback_metadata()
            
            # Load evidence index
            evidence_path = data_dir / 'evidence_index.json'
            if evidence_path.exists():
                try:
                    with open(evidence_path, 'r') as f:
                        import json
                        self.evidence_index = json.load(f)
                    print(f"✅ Loaded evidence index for {len(self.evidence_index)} researchers")
                except Exception as e:
                    print(f"❌ Could not load evidence index: {e}")
                    self.evidence_index = {}
            else:
                print(f"⚠️ Evidence index file not found at {evidence_path}")
                self.evidence_index = {}
            
            # Load sentence model
            try:
                print("🤖 Loading sentence transformer model...")
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Sentence model loaded successfully")
            except Exception as e:
                print(f"❌ Could not load sentence model: {e}")
                self.sentence_model = None
            
            # Summary
            total_researchers = len(self.researcher_vectors) if self.researcher_vectors else len(self.researcher_metadata)
            self.data_loaded = True
            print(f"🎉 Data loading completed!")
            print(f"   📊 Total researchers: {total_researchers}")
            print(f"   🔍 TF-IDF model: {'✅' if self.tfidf_model else '❌'}")
            print(f"   🧠 Sentence model: {'✅' if self.sentence_model else '❌'}")
            print(f"   📈 Research vectors: {'✅' if self.researcher_vectors else '❌'}")
            print(f"   📑 Conceptual profiles: {'✅' if self.conceptual_profiles else '❌'}")
            
        except Exception as e:
            print(f"❌ Critical error in data loading: {e}")
            self.data_loaded = False

    def _load_pickle_safely(self, file_path: Path):
        """Safely load pickle files that may have missing class dependencies"""
        import pickle
        import sys
        from types import ModuleType
        
        # Create a dummy module for missing classes
        class DummyClass:
            def __init__(self, *args, **kwargs):
                pass
            def __getattr__(self, name):
                return lambda *args, **kwargs: None
        
        # Custom unpickler that replaces missing classes
        class SafeUnpickler(pickle.Unpickler):
            def find_class(self, module, name):
                try:
                    return super().find_class(module, name)
                except (AttributeError, ModuleNotFoundError, ImportError):
                    print(f"⚠️ Missing class {module}.{name}, using dummy")
                    return DummyClass
        
        try:
            with open(file_path, 'rb') as f:
                return SafeUnpickler(f).load()
        except Exception as e:
            print(f"❌ Safe unpickling failed: {e}")
            return None

    def _create_fallback_metadata(self) -> pd.DataFrame:
        """Create fallback metadata from researcher vectors if available"""
        if self.researcher_vectors:
            print("🔧 Creating fallback metadata from researcher vectors...")
            researcher_ids = list(self.researcher_vectors.keys())
            fallback_data = {
                'researcher_name': [f"Researcher_{i+1}" for i in range(len(researcher_ids))],
                'researcher_openalex_id': researcher_ids,
                'total_papers': [np.random.randint(10, 50) for _ in researcher_ids],
                'total_citations': [np.random.randint(100, 1000) for _ in researcher_ids],
                'grant_experience_factor': [1.0 + np.random.random() for _ in researcher_ids],
                'first_publication_year': [np.random.randint(2010, 2020) for _ in researcher_ids],
                'last_publication_year': [2024] * len(researcher_ids)
            }
            return pd.DataFrame(fallback_data)
        else:
            return self._create_sample_metadata()
    
    def _create_sample_data_structure(self, data_dir: Path):
        """Create sample data structure for testing"""
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created {data_dir} directory")
        print("ℹ️ To use real data, copy your preprocessed files here:")
        print(f"   - {data_dir}/tfidf_model.pkl")
        print(f"   - {data_dir}/researcher_vectors.npz")
        print(f"   - {data_dir}/conceptual_profiles.npz")
        print(f"   - {data_dir}/researcher_metadata.parquet")
        print(f"   - {data_dir}/evidence_index.json")
    
    def _create_sample_metadata(self) -> pd.DataFrame:
        """Create sample researcher metadata for testing"""
        sample_data = {
            'researcher_name': ['Dr. Sample Researcher', 'Prof. Test User'],
            'researcher_openalex_id': ['sample_id_1', 'sample_id_2'],
            'total_papers': [25, 40],
            'total_citations': [500, 800],
            'grant_experience_factor': [1.5, 2.0],
            'first_publication_year': [2015, 2010],
            'last_publication_year': [2024, 2024]
        }
        return pd.DataFrame(sample_data)
    
    def extract_keywords_from_skills(self, skills: List[str]) -> List[str]:
        """Extract keywords from solicitation skills"""
        stop_words = {'and', 'in', 'of', 'for', 'the', 'a', 'an', 'to', 'with', 'on', 'at', 'by',
                      'expertise', 'experience', 'knowledge', 'ability', 'skills', 'understanding',
                      'capacity', 'proficiency', 'e.g.', 'eg', 'including', 'such', 'as'}
        
        all_keywords = []
        for skill in skills:
            # Clean and split
            cleaned = re.sub(r'[^\w\s-]', ' ', skill.lower())
            words = cleaned.split()
            
            # Extract meaningful keywords
            for word in words:
                word = word.strip('-')
                if (len(word) >= 3 and
                    word not in stop_words and
                    not word.isdigit()):
                    all_keywords.append(word)
        
        return all_keywords
    
    def score_researcher(self, researcher_id: str, skills: List[str], 
                        solicitation_embedding: np.ndarray, debug_mode: bool = False) -> Optional[ResearcherMatch]:
        """Score a single researcher against solicitation"""
        try:
            # Get metadata
            researcher_row = self.researcher_metadata[
                self.researcher_metadata['researcher_openalex_id'] == researcher_id
            ]
            if researcher_row.empty:
                return None
            
            researcher_name = researcher_row.iloc[0]['researcher_name']
            total_papers = int(researcher_row.iloc[0]['total_papers'])
            grant_factor = researcher_row.iloc[0]['grant_experience_factor']
            
            # Extract keywords and format for TF-IDF
            solicitation_keywords = self.extract_keywords_from_skills(skills)
            solicitation_text = ', '.join(solicitation_keywords)
            
            if debug_mode:
                print(f"DEBUG - Researcher: {researcher_name}")
                print(f"  Extracted keywords: {solicitation_keywords[:10]}...")
            
            # Calculate sparse score (TF-IDF)
            s_sparse = 0.0
            if self.tfidf_model and researcher_id in self.researcher_vectors:
                try:
                    solicitation_vector = self.tfidf_model.transform([solicitation_text])
                    researcher_vector = self.researcher_vectors[researcher_id].reshape(1, -1)
                    
                    if solicitation_vector.sum() > 0 and researcher_vector.sum() > 0:
                        similarity = cosine_similarity(solicitation_vector, researcher_vector)[0][0]
                        s_sparse = float(similarity * 100)
                except Exception as e:
                    if debug_mode:
                        print(f"  TF-IDF ERROR: {e}")
            
            # Calculate dense score (semantic similarity)
            s_dense = 0.0
            if self.sentence_model and researcher_id in self.evidence_index:
                try:
                    # Get researcher papers
                    researcher_papers = []
                    for topic_papers in self.evidence_index[researcher_id].values():
                        researcher_papers.extend(topic_papers)
                    researcher_papers = list(set(researcher_papers))
                    
                    max_sim = 0.0
                    for paper_id in researcher_papers:
                        if paper_id in self.conceptual_profiles:
                            paper_embedding = self.conceptual_profiles[paper_id]
                            sim = cosine_similarity(
                                solicitation_embedding.reshape(1, -1),
                                paper_embedding.reshape(1, -1)
                            )[0][0]
                            max_sim = max(max_sim, sim)
                    
                    s_dense = float(max_sim * 100)
                except Exception as e:
                    if debug_mode:
                        print(f"  Dense similarity ERROR: {e}")
            
            # Calculate final scores
            f_ge = max(1.0, min(3.0, 1.0 + (grant_factor * 0.2)))
            academic_expertise = (self.alpha * s_sparse) + (self.beta * s_dense)
            final_score = academic_expertise * f_ge
            
            if debug_mode:
                print(f"  Scores - Sparse: {s_sparse:.2f}, Dense: {s_dense:.2f}, Grant: {f_ge:.2f}")
                print(f"  Academic: {academic_expertise:.2f}, Final: {final_score:.2f}")
            
            return ResearcherMatch(
                researcher_id=researcher_id,
                researcher_name=researcher_name,
                academic_expertise_score=academic_expertise,
                s_sparse=s_sparse,
                s_dense=s_dense,
                f_ge=f_ge,
                final_affinity_score=final_score,
                total_papers=total_papers,
                eligibility_status="Eligible"
            )
            
        except Exception as e:
            if debug_mode:
                print(f"ERROR scoring {researcher_id}: {e}")
            return None
    
    def run_matching(self, solicitation_analysis: dict, top_n: int = 20, 
                    debug_mode: bool = False) -> MatchingResults:
        """Run the complete matching algorithm"""
        start_time = time.time()
        
        if not self.data_loaded:
            raise Exception("Researcher data not loaded. Please ensure data files are in data/models/")
        
        print(f"🔍 Running matching for: {solicitation_analysis.get('title', 'Unknown')}")
        
        # Create skills list (simplified for now)
        skills = [
            "Expertise in artificial intelligence research areas",
            "Experience in machine learning and data science",
            "Knowledge of educational technology and curriculum development",
            "Understanding of broadening participation strategies"
        ]
        
        # Create solicitation embedding
        solicitation_text = f"{solicitation_analysis.get('title', '')}. {solicitation_analysis.get('abstract', '')}"
        solicitation_embedding = None
        
        if self.sentence_model:
            try:
                solicitation_embedding = self.sentence_model.encode(solicitation_text)
            except Exception as e:
                print(f"⚠️ Could not create solicitation embedding: {e}")
                # Create dummy embedding
                solicitation_embedding = np.zeros(384)  # Standard dimension for all-MiniLM-L6-v2
        else:
            solicitation_embedding = np.zeros(384)
        
        # Get all researchers
        if self.researcher_metadata.empty:
            print("⚠️ No researcher metadata available. Using sample data.")
            all_researchers = ['sample_id_1', 'sample_id_2']
        else:
            all_researchers = list(self.researcher_metadata['researcher_openalex_id'])
        
        print(f"👥 Analyzing {len(all_researchers)} researchers")
        
        # Score all researchers
        matches = []
        debug_count = 0
        
        for researcher_id in all_researchers:
            # Debug first few researchers
            current_debug = debug_mode and debug_count < 3
            if current_debug:
                debug_count += 1
            
            result = self.score_researcher(researcher_id, skills, solicitation_embedding, current_debug)
            if result:
                matches.append(result)
        
        # Sort by final score
        matches.sort(key=lambda x: x.final_affinity_score, reverse=True)
        top_matches = matches[:top_n]
        
        processing_time = time.time() - start_time
        
        return MatchingResults(
            solicitation_id=solicitation_analysis.get('solicitation_id', 'unknown'),
            solicitation_title=solicitation_analysis.get('title', 'Unknown Solicitation'),
            eligible_researchers=len(all_researchers),
            total_researchers=len(all_researchers),
            top_matches=top_matches,
            skills_analyzed=skills,
            processing_time_seconds=round(processing_time, 2),
            generated_at=datetime.now()
        )