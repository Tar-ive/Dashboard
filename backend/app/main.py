from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import solicitations, matching, teams, reports
from app.config import settings

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with simplified prefix
app.include_router(solicitations.router, prefix="/api")
app.include_router(matching.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

@app.get("/")
def health_check():
    return {
        "status": "healthy", 
        "message": "NSF Researcher Matching API is running",
        "version": "1.0.0",
        "features": [
            "pdf_upload", 
            "text_extraction", 
            "researcher_matching", 
            "dream_team_assembly",
            "ai_powered_reports"  # Added
        ]
    }

@app.get("/health")
def detailed_health():
    return {
        "api_status": "ready",
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "version": settings.API_VERSION
    }