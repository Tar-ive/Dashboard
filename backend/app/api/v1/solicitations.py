from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.models.solicitation import SolicitationResponse, SolicitationAnalysis, SolicitationError
from app.services.pdf_service import PDFService
from datetime import datetime
import uuid
import os

router = APIRouter(prefix="/solicitations", tags=["solicitations"])
pdf_service = PDFService()

@router.get("/")
def list_solicitations():
    """List all uploaded solicitations"""
    return {
        "message": "Solicitations endpoint working",
        "available_endpoints": [
            "POST /upload - Upload a PDF solicitation",
            "GET /{solicitation_id} - Get solicitation analysis",
            "GET / - This endpoint"
        ]
    }

@router.post("/upload", response_model=SolicitationResponse)
async def upload_solicitation(file: UploadFile = File(...)):
    """Upload a PDF solicitation for analysis"""
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {file.content_type}. Only PDF files are accepted."
        )
    
    # Generate unique ID
    solicitation_id = str(uuid.uuid4())
    
    try:
        # Save uploaded file
        upload_path = f"data/uploads/{solicitation_id}_{file.filename}"
        
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return SolicitationResponse(
            solicitation_id=solicitation_id,
            filename=file.filename,
            status="uploaded",
            upload_time=datetime.now(),
            file_size=len(content)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.post("/{solicitation_id}/analyze", response_model=SolicitationAnalysis)
def analyze_solicitation(solicitation_id: str):
    """Analyze an uploaded solicitation PDF"""
    
    try:
        # Find the uploaded file
        upload_dir = "data/uploads"
        matching_files = [f for f in os.listdir(upload_dir) if f.startswith(solicitation_id)]
        
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail=f"Solicitation {solicitation_id} not found"
            )
        
        file_path = os.path.join(upload_dir, matching_files[0])
        original_filename = matching_files[0].split("_", 1)[1]  # Remove UUID prefix
        
        # Extract text using PDF service
        analysis_result = pdf_service.extract_and_analyze(file_path)
        
        return SolicitationAnalysis(
            solicitation_id=solicitation_id,
            filename=original_filename,
            title=analysis_result["title"],
            abstract=analysis_result["abstract"],
            text_length=analysis_result["text_length"],
            processing_time_seconds=analysis_result["processing_time"],
            sections_found=analysis_result["sections_found"],
            extracted_at=datetime.now()
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Solicitation file {solicitation_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze solicitation: {str(e)}"
        )

@router.get("/{solicitation_id}", response_model=SolicitationAnalysis)
def get_solicitation(solicitation_id: str):
    """Get solicitation analysis results"""
    # For now, just trigger analysis
    # In production, you'd check if analysis already exists
    return analyze_solicitation(solicitation_id)