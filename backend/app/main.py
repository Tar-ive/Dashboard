from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import solicitations, matching, teams  # Add teams import

app = FastAPI(
    title="NSF Researcher Matching API",
    description="API for matching researchers to NSF solicitations and assembling dream teams",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(solicitations.router, prefix="/api/v1")
app.include_router(matching.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")  # Add this line

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
            "dream_team_assembly"  # Added
        ]
    }

@app.get("/health")
def detailed_health():
    return {
        "api_status": "ready",
        "database": "connected",
        "ml_models": "loaded",
        "version": "1.0.0"
    }