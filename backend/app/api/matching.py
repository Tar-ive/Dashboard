from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.matching import MatchingRequest, MatchingResults, MatchingStatus
from app.services.matching_service import MatchingService
from app.services.pdf_service import PDFService
import os
from typing import Dict

router = APIRouter(prefix="/matching", tags=["matching"])
matching_service = MatchingService()
pdf_service = PDFService()

# In-memory storage for demo (use Redis/DB in production)
matching_sessions: Dict[str, Dict] = {}

@router.get("/")
def matching_info():
    """Get matching service information"""
    return {
        "message": "NSF Researcher Matching Service",
        "data_loaded": matching_service.data_loaded,
        "total_researchers": len(matching_service.researcher_metadata) if matching_service.data_loaded else 0,
        "available_endpoints": [
            "POST /run - Run matching algorithm",
            "GET /{session_id}/status - Check matching status",
            "GET /{session_id}/results - Get matching results"
        ]
    }

@router.post("/run", response_model=MatchingStatus)
async def run_matching(request: MatchingRequest, background_tasks: BackgroundTasks):
    """Start matching algorithm for a solicitation"""
    
    # Validate that solicitation exists
    upload_dir = "data/uploads"
    matching_files = [f for f in os.listdir(upload_dir) if f.startswith(request.solicitation_id)]
    
    if not matching_files:
        raise HTTPException(
            status_code=404,
            detail=f"Solicitation {request.solicitation_id} not found"
        )
    
    # Initialize session
    session_id = request.solicitation_id
    matching_sessions[session_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Matching request received"
    }
    
    # Start background processing
    background_tasks.add_task(
        process_matching_background,
        session_id,
        request
    )
    
    return MatchingStatus(
        solicitation_id=session_id,
        status="pending",
        progress_percent=0,
        message="Matching started. Processing solicitation..."
    )

async def process_matching_background(session_id: str, request: MatchingRequest):
    """Background task to process matching"""
    try:
        # Update status
        matching_sessions[session_id].update({
            "status": "processing",
            "progress": 25,
            "message": "Analyzing solicitation PDF..."
        })
        
        # Find and analyze the PDF
        upload_dir = "data/uploads"
        matching_files = [f for f in os.listdir(upload_dir) if f.startswith(session_id)]
        file_path = os.path.join(upload_dir, matching_files[0])
        
        # Extract solicitation data
        solicitation_analysis = pdf_service.extract_and_analyze(file_path)
        solicitation_analysis['solicitation_id'] = session_id
        
        # Update status
        matching_sessions[session_id].update({
            "progress": 50,
            "message": "Running matching algorithm..."
        })
        
        # Run matching
        results = matching_service.run_matching(
            solicitation_analysis,
            top_n=request.top_n_results,
            debug_mode=request.debug_mode
        )
        
        # Store results
        matching_sessions[session_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Matching completed. Found {len(results.top_matches)} matches.",
            "results": results
        })
        
    except Exception as e:
        matching_sessions[session_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Matching failed: {str(e)}"
        })

@router.get("/{session_id}/status", response_model=MatchingStatus)
def get_matching_status(session_id: str):
    """Get the status of a matching session"""
    
    if session_id not in matching_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Matching session {session_id} not found"
        )
    
    session = matching_sessions[session_id]
    
    return MatchingStatus(
        solicitation_id=session_id,
        status=session["status"],
        progress_percent=session["progress"],
        message=session["message"]
    )

@router.get("/{session_id}/results", response_model=MatchingResults)
def get_matching_results(session_id: str):
    """Get the results of a completed matching session"""
    
    if session_id not in matching_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Matching session {session_id} not found"
        )
    
    session = matching_sessions[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Matching not completed. Current status: {session['status']}"
        )
    
    return session["results"]

@router.delete("/{session_id}")
def delete_matching_session(session_id: str):
    """Delete a matching session"""
    
    if session_id not in matching_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Matching session {session_id} not found"
        )
    
    del matching_sessions[session_id]
    return {"message": f"Matching session {session_id} deleted"}