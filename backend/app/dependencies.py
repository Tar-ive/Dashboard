from fastapi import Depends
from typing import Optional
from app.services.ai_service import AIService
from app.services.report_service import ReportService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_ai_service() -> Optional[AIService]:
    """Dependency provider for AIService with error handling"""
    try:
        if settings.ANTHROPIC_API_KEY:
            return AIService()
        return None
    except Exception as e:
        logger.warning(f"Failed to initialize AI service: {e}")
        return None

def get_report_service(ai_service: Optional[AIService] = Depends(get_ai_service)) -> ReportService:
    """Dependency provider for ReportService with AIService injection"""
    return ReportService(ai_service=ai_service)
