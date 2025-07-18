import os
from typing import Optional, List
from pathlib import Path
from pydantic import BaseSettings, validator
import logging

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic BaseSettings for automatic validation and type conversion.
    """
    
    # API Configuration
    API_TITLE: str = "NSF Researcher Matching API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API for matching researchers to NSF solicitations and assembling dream teams"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Data Paths
    DATA_DIR: str = "data"
    MODELS_DIR: str = "data/models"
    UPLOADS_DIR: str = "data/uploads"
    OUTPUTS_DIR: str = "data/outputs"
    
    # Model Configuration
    SENTENCE_MODEL_NAME: str = "all-MiniLM-L6-v2"
    TF_IDF_ALPHA: float = 0.7  # TF-IDF weight in hybrid scoring
    TF_IDF_BETA: float = 0.3   # Dense similarity weight in hybrid scoring
    
    # Matching Algorithm Parameters
    DEFAULT_TOP_N_RESEARCHERS: int = 20
    DEFAULT_TEAM_SIZE: int = 4
    DEFAULT_GUARANTEED_TOP_N: int = 2
    DEFAULT_MARGINAL_THRESHOLD: float = 0.25
    MIN_PROXY_SCORE: float = 0.8
    CURRENT_YEAR: int = 2025
    
    # AI Service Configuration
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    ANTHROPIC_MAX_TOKENS: int = 4000
    ANTHROPIC_TEMPERATURE: float = 0.3
    
    GROQ_MODEL: str = "llama3-70b-8192"
    GROQ_MAX_TOKENS: int = 2000
    GROQ_TEMPERATURE: float = 0.5
    
    # Rate Limiting
    API_RATE_LIMIT: str = "100/minute"
    AI_API_RATE_LIMIT: str = "10/minute"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["*"]  # Configure for production
    ALLOWED_METHODS: List[str] = ["*"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]
    
    # Cache Configuration
    ENABLE_CACHING: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator("ANTHROPIC_API_KEY")
    def validate_anthropic_key(cls, v):
        if v and not v.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key format")
        return v
    
    @validator("DATA_DIR", "MODELS_DIR", "UPLOADS_DIR", "OUTPUTS_DIR")
    def validate_directories(cls, v):
        """Ensure directories exist or can be created"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @validator("TF_IDF_ALPHA", "TF_IDF_BETA")
    def validate_weights(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Weights must be between 0 and 1")
        return v
    
    @property
    def models_path(self) -> Path:
        """Path to models directory"""
        return Path(self.MODELS_DIR)
    
    @property
    def uploads_path(self) -> Path:
        """Path to uploads directory"""
        return Path(self.UPLOADS_DIR)
    
    @property
    def outputs_path(self) -> Path:
        """Path to outputs directory"""
        return Path(self.OUTPUTS_DIR)
    
    def get_anthropic_key(self) -> str:
        """
        Get Anthropic API key with proper error handling.
        
        Returns:
            str: The API key
            
        Raises:
            ValueError: If API key is not configured
        """
        if not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable. "
                "Get your key at: https://console.anthropic.com/"
            )
        return self.ANTHROPIC_API_KEY
    
    def get_groq_key(self) -> Optional[str]:
        """
        Get Groq API key (optional).
        
        Returns:
            Optional[str]: The API key if configured
        """
        return self.GROQ_API_KEY
    
    def has_ai_capabilities(self) -> bool:
        """Check if any AI service is configured"""
        return bool(self.ANTHROPIC_API_KEY or self.GROQ_API_KEY)
    
    def get_ai_service_status(self) -> dict:
        """Get status of AI services configuration"""
        return {
            "anthropic_configured": bool(self.ANTHROPIC_API_KEY),
            "groq_configured": bool(self.GROQ_API_KEY),
            "openai_configured": bool(self.OPENAI_API_KEY),
            "ai_features_available": self.has_ai_capabilities()
        }
    
    def setup_logging(self):
        """Configure logging based on settings"""
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper()),
            format=self.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f"{self.OUTPUTS_DIR}/app.log")
            ]
        )
        
        # Reduce noise from some libraries
        logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
        logging.getLogger("transformers").setLevel(logging.WARNING)
        logging.getLogger("torch").setLevel(logging.WARNING)
    
    def validate_environment(self) -> dict:
        """
        Validate the current environment setup.
        
        Returns:
            dict: Validation results with status and messages
        """
        validation_results = {
            "status": "valid",
            "warnings": [],
            "errors": [],
            "info": []
        }
        
        # Check required directories
        for dir_path in [self.DATA_DIR, self.MODELS_DIR, self.UPLOADS_DIR, self.OUTPUTS_DIR]:
            if not Path(dir_path).exists():
                validation_results["warnings"].append(f"Directory {dir_path} does not exist - will be created")
        
        # Check AI configuration
        if not self.has_ai_capabilities():
            validation_results["warnings"].append(
                "No AI services configured. Strategic analysis will use basic fallback methods."
            )
        
        # Check model files
        required_model_files = [
            "tfidf_model.pkl",
            "researcher_vectors.npz", 
            "conceptual_profiles.npz",
            "researcher_metadata.parquet",
            "evidence_index.json"
        ]
        
        missing_files = []
        for file_name in required_model_files:
            if not (self.models_path / file_name).exists():
                missing_files.append(file_name)
        
        if missing_files:
            validation_results["warnings"].append(
                f"Missing model files: {', '.join(missing_files)}. "
                "Copy preprocessed data to data/models/ directory."
            )
        
        # Check weights sum
        if abs((self.TF_IDF_ALPHA + self.TF_IDF_BETA) - 1.0) > 0.01:
            validation_results["warnings"].append(
                f"TF-IDF weights don't sum to 1.0: α={self.TF_IDF_ALPHA}, β={self.TF_IDF_BETA}"
            )
        
        # Set overall status
        if validation_results["errors"]:
            validation_results["status"] = "invalid"
        elif validation_results["warnings"]:
            validation_results["status"] = "valid_with_warnings"
        
        return validation_results
    
    def get_full_config_summary(self) -> dict:
        """Get a complete summary of configuration (for debugging)"""
        return {
            "api_config": {
                "title": self.API_TITLE,
                "version": self.API_VERSION,
                "debug": self.DEBUG,
                "host": self.HOST,
                "port": self.PORT
            },
            "paths": {
                "data_dir": self.DATA_DIR,
                "models_dir": self.MODELS_DIR,
                "uploads_dir": self.UPLOADS_DIR,
                "outputs_dir": self.OUTPUTS_DIR
            },
            "ai_services": self.get_ai_service_status(),
            "model_config": {
                "sentence_model": self.SENTENCE_MODEL_NAME,
                "tf_idf_alpha": self.TF_IDF_ALPHA,
                "tf_idf_beta": self.TF_IDF_BETA
            },
            "algorithm_defaults": {
                "top_n_researchers": self.DEFAULT_TOP_N_RESEARCHERS,
                "team_size": self.DEFAULT_TEAM_SIZE,
                "guaranteed_top_n": self.DEFAULT_GUARANTEED_TOP_N,
                "marginal_threshold": self.DEFAULT_MARGINAL_THRESHOLD
            },
            "environment_validation": self.validate_environment()
        }


# Create global settings instance
settings = Settings()

# Configure logging on import
settings.setup_logging()

# Create a logger for this module
logger = logging.getLogger(__name__)

def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings: The configured settings object
    """
    return settings

def validate_startup_environment():
    """
    Validate environment on application startup.
    Logs warnings and errors, raises exception if critical issues found.
    """
    validation = settings.validate_environment()
    
    logger.info("🔧 Environment Validation Results:")
    logger.info(f"   Status: {validation['status'].upper()}")
    
    if validation["info"]:
        for info in validation["info"]:
            logger.info(f"   ℹ️ {info}")
    
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(f"   ⚠️ {warning}")
    
    if validation["errors"]:
        for error in validation["errors"]:
            logger.error(f"   ❌ {error}")
        raise ValueError(f"Environment validation failed: {validation['errors']}")
    
    logger.info("✅ Environment validation completed")

# Export commonly used items
__all__ = [
    "Settings",
    "settings", 
    "get_settings",
    "validate_startup_environment",
    "logger"
]