"""Shared application state to avoid circular imports"""
from typing import Dict

# Global session storage (use Redis/DB in production)
matching_sessions: Dict[str, Dict] = {}
team_sessions: Dict[str, Dict] = {}
report_sessions: Dict[str, Dict] = {}