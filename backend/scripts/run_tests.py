#!/usr/bin/env python3
"""
Test runner script for the NSF Researcher Matching API.

This script provides a comprehensive test execution interface with various options
for running different types of tests and generating reports.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner with comprehensive options and reporting."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.test_dir = self.base_dir / "tests"
        self.coverage_dir = self.base_dir / "htmlcov"
        
    def setup_environment(self):
        """Set up test environment."""
        # Create test directories
        test_dirs = [
            self.base_dir / "test_uploads",
            self.base_dir / "test_models", 
            self.base_dir / "test_outputs",
            self.coverage_dir
        ]
        
        for dir_path in test_dirs:
            dir_path.mkdir(exist_ok=True)
        
        # Set environment variables
        os.environ.update({
            "TESTING": "true",
            "DATABASE_URL": "sqlite:///./test.db",
            "UPLOAD_DIR": "./test_uploads",
            "MODEL_DIR": "./test_models",
            "LOG_LEVEL": "DEBUG"
        })
    
    def run_command(self, cmd: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run a command and handle errors."""
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=capture_output,
                text=True,
                check=False
            )
            return result
        except Exception as e:
            print(f"Error running command: {e}")
            sys.exit(1)
    
    def run_unit_tests(self, verbose: bool = True) -> bool:
        """Run unit tests."""
        cmd = ["python", "-m", "pytest", "tests/", "-m", "unit"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_integration_tests(self, verbose: bool = True) -> bool:
        """Run integration tests."""
        cmd = ["python", "-m", "pytest", "tests/", "-m", "integration"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_e2e_tests(self, verbose: bool = True) -> bool:
        """Run end-to-end tests."""
        cmd = ["python", "-m", "pytest", "tests/", "-m", "e2e"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_performance_tests(self, verbose: bool = True) -> bool:
        """Run performance tests."""
        cmd = ["python", "-m", "pytest", "tests/", "-m", "performance", "--tb=short"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_all_tests(self, verbose: bool = True) -> bool:
        """Run all tests."""
        cmd = ["python", "-m", "pytest", "tests/"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_tests_with_coverage(self, verbose: bool = True) -> bool:
        """Run tests with coverage reporting."""
        cmd = [
            "python", "-m", "pytest", "tests/",
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=80"
        ]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            print(f"\nCoverage report generated in: {self.coverage_dir}")
            print("Open htmlcov/index.html to view detailed coverage report")
        
        return result.returncode == 0
    
    def run_fast_tests(self, verbose: bool = True) -> bool:
        """Run fast tests (excluding slow tests)."""
        cmd = ["python", "-m", "pytest", "tests/", "-m", "not slow"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_linting(self) -> bool:
        """Run code linting checks."""
        print("Running linting checks...")
        
        # Run black check
        result = self.run_command(["black", "--check", "--diff", "app/", "tests/"])
        if result.returncode != 0:
            print("Black formatting check failed")
            return False
        
        # Run isort check
        result = self.run_command(["isort", "--check-only", "--diff", "app/", "tests/"])
        if result.returncode != 0:
            print("isort import sorting check failed")
            return False
        
        # Run flake8
        result = self.run_command(["flake8", "app/", "tests/"])
        if result.returncode != 0:
            print("flake8 linting check failed")
            return False
        
        # Run mypy
        result = self.run_command(["mypy", "app/", "--ignore-missing-imports"])
        if result.returncode != 0:
            print("mypy type checking failed")
            return False
        
        print("All linting checks passed!")
        return True
    
    def run_security_checks(self) -> bool:
        """Run security checks."""
        print("Running security checks...")
        
        # Run bandit
        result = self.run_command([
            "bandit", "-r", "app/", "-f", "json", "-o", "bandit-report.json"
        ])
        
        # Run safety check
        result = self.run_command([
            "safety", "check", "--json", "--output", "safety-report.json"
        ])
        
        print("Security checks completed. Check bandit-report.json and safety-report.json for details.")
        return True
    
    def cleanup(self):
        """Clean up test artifacts."""
        print("Cleaning up test artifacts...")
        
        cleanup_paths = [
            self.base_dir / "htmlcov",
            self.base_dir / ".pytest_cache",
            self.base_dir / "coverage.xml",
            self.base_dir / "pytest-report.xml",
            self.base_dir / "bandit-report.json",
            self.base_dir / "safety-report.json",
            self.base_dir / "test_uploads",
            self.base_dir / "test_models",
            self.base_dir / "test_outputs"
        ]
        
        for path in cleanup_paths:
            if path.exists():
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink()
        
        # Clean up __pycache__ directories
        for pycache in self.base_dir.rglob("__pycache__"):
            import shutil
            shutil.rmtree(pycache, ignore_errors=True)
        
        print("Cleanup completed!")


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Test runner for NSF Researcher Matching API")
    
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "e2e", "performance", "all", "coverage", "fast", "lint", "security", "cleanup"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Run tests in quiet mode"
    )
    
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only set up test environment without running tests"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    runner.setup_environment()
    
    if args.setup_only:
        print("Test environment set up successfully!")
        return
    
    verbose = not args.quiet
    success = True
    
    if args.test_type == "unit":
        success = runner.run_unit_tests(verbose)
    elif args.test_type == "integration":
        success = runner.run_integration_tests(verbose)
    elif args.test_type == "e2e":
        success = runner.run_e2e_tests(verbose)
    elif args.test_type == "performance":
        success = runner.run_performance_tests(verbose)
    elif args.test_type == "all":
        success = runner.run_all_tests(verbose)
    elif args.test_type == "coverage":
        success = runner.run_tests_with_coverage(verbose)
    elif args.test_type == "fast":
        success = runner.run_fast_tests(verbose)
    elif args.test_type == "lint":
        success = runner.run_linting()
    elif args.test_type == "security":
        success = runner.run_security_checks()
    elif args.test_type == "cleanup":
        runner.cleanup()
        return
    
    if success:
        print(f"\n✅ {args.test_type.title()} tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ {args.test_type.title()} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()