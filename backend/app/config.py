import os
from typing import Optional
from pathlib import Path
import logging

class Settings:
    """Simplified application settings"""
    
    def __init__(self):
        # Core API Configuration
        self.API_TITLE = "NSF Researcher Matching API"
        self.API_VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        
        # API Keys
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        
        # Data Paths
        self.DATA_DIR = os.getenv("DATA_DIR", "data")
        self.UPLOADS_DIR = os.getenv("UPLOADS_DIR", "data/uploads")
        self.OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "data/outputs")
        
        # Algorithm Parameters
        self.TF_IDF_ALPHA = 0.7
        self.TF_IDF_BETA = 0.3
        self.DEFAULT_TOP_N_RESEARCHERS = 20
        self.DEFAULT_TEAM_SIZE = 4
        
        # AI Configuration
        self.ANTHROPIC_MODEL = "claude-3-sonnet-20240229"
        self.ANTHROPIC_MAX_TOKENS = 4000
        
        # Ensure directories exist
        for path in [self.DATA_DIR, self.UPLOADS_DIR, self.OUTPUTS_DIR]:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def get_anthropic_key(self) -> str:
        """Get Anthropic API key with error handling"""
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not configured")
        return self.ANTHROPIC_API_KEY

# Global settings instance
settings = Settings()

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)