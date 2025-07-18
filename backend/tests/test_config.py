"""
Test configuration module for environment-specific test settings.
"""

import os
from pathlib import Path
from typing import Dict, Any


class TestConfig:
    """Test configuration class for managing test environment settings."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.test_dir = self.base_dir / "tests"
        
    @property
    def database_config(self) -> Dict[str, Any]:
        """Database configuration for testing."""
        return {
            "url": "sqlite:///:memory:",
            "echo": False,
            "pool_pre_ping": True,
            "connect_args": {"check_same_thread": False}
        }
    
    @property
    def file_system_config(self) -> Dict[str, str]:
        """File system configuration for testing."""
        return {
            "upload_dir": str(self.test_dir / "temp_uploads"),
            "model_dir": str(self.test_dir / "temp_models"),
            "output_dir": str(self.test_dir / "temp_outputs"),
            "cache_dir": str(self.test_dir / "temp_cache")
        }
    
    @property
    def api_config(self) -> Dict[str, Any]:
        """API configuration for testing."""
        return {
            "host": "127.0.0.1",
            "port": 8000,
            "debug": True,
            "testing": True,
            "log_level": "DEBUG"
        }
    
    @property
    def ml_config(self) -> Dict[str, Any]:
        """Machine learning configuration for testing."""
        return {
            "model_name": "test-model",
            "embedding_dim": 384,
            "batch_size": 16,
            "max_length": 512,
            "use_mock": True
        }
    
    @property
    def performance_config(self) -> Dict[str, Any]:
        """Performance testing configuration."""
        return {
            "timeout": 30,
            "max_concurrent": 10,
            "memory_limit": "512MB",
            "cpu_limit": 2
        }
    
    def get_env_config(self, env: str = "test") -> Dict[str, Any]:
        """Get configuration for specific environment."""
        configs = {
            "test": {
                **self.database_config,
                **self.file_system_config,
                **self.api_config,
                **self.ml_config
            },
            "ci": {
                **self.database_config,
                **self.file_system_config,
                **self.api_config,
                **self.ml_config,
                "parallel": True,
                "workers": 4
            },
            "performance": {
                **self.database_config,
                **self.file_system_config,
                **self.api_config,
                **self.ml_config,
                **self.performance_config
            }
        }
        
        return configs.get(env, configs["test"])


# Global test configuration instance
test_config = TestConfig()


def setup_test_environment():
    """Set up test environment variables and directories."""
    config = test_config.get_env_config()
    
    # Set environment variables
    os.environ.update({
        "TESTING": "true",
        "DATABASE_URL": config["url"],
        "UPLOAD_DIR": config["upload_dir"],
        "MODEL_DIR": config["model_dir"],
        "LOG_LEVEL": config["log_level"]
    })
    
    # Create test directories
    for dir_path in [
        config["upload_dir"],
        config["model_dir"],
        config["output_dir"],
        config["cache_dir"]
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def cleanup_test_environment():
    """Clean up test environment and temporary files."""
    import shutil
    
    config = test_config.get_env_config()
    
    # Remove test directories
    for dir_path in [
        config["upload_dir"],
        config["model_dir"],
        config["output_dir"],
        config["cache_dir"]
    ]:
        if Path(dir_path).exists():
            shutil.rmtree(dir_path, ignore_errors=True)


# Test markers and categories
TEST_MARKERS = {
    "unit": "Unit tests for individual components",
    "integration": "Integration tests for component interactions",
    "e2e": "End-to-end tests for complete workflows",
    "performance": "Performance and load tests",
    "golden": "Ground-truth validation tests",
    "slow": "Tests that take longer to run",
    "external": "Tests that require external services"
}


# Test data constants
SAMPLE_DATA = {
    "solicitation": {
        "title": "Mathematical Foundations of Artificial Intelligence",
        "program": "MFAI",
        "deadline": "2024-12-15",
        "description": "Research in mathematical foundations of AI systems",
        "keywords": ["mathematics", "artificial intelligence", "foundations"],
        "budget_range": "500000-1000000"
    },
    "researcher": {
        "name": "Dr. Jane Smith",
        "email": "jane.smith@university.edu",
        "institution": "Test University",
        "department": "Computer Science",
        "expertise": ["machine learning", "data science", "algorithms"],
        "publications": 25,
        "h_index": 15
    },
    "pdf_content": b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
}