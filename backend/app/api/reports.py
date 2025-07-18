from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from app.models.reports import (
    ReportGenerationRequest, ComprehensiveReport, GapAnalysisReport,
    ExecutiveSummary, ReportExport, ReportStatus
)
from app.services.report_service import ReportService
from app.services.ai_service import AIService
from typing import Dict, Optional
import os
import json
import io
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["reports"])

# Initialize services
try:
    ai_service = AIService()
    report_service = ReportService(ai_service)
    print("✅ Report services initialized successfully")
except Exception as e:
    print(f"⚠️ Report services initialization failed: {e}")
    ai_service = None
    report_service = None

from app.state import report_sessions

@router.get("/")
def reports_info():
    """Get reports service information"""
    return {
        "message": "NSF Strategic Reports & GAP Analysis Service",
        "ai_service_available": ai_service is not None,
        "features": [
            "AI-powered gap analysis",
            "Strategic recommendations", 
            "Competitiveness assessment",
            "Multiple export formats"
        ],
        "available_endpoints": [
            "POST /{team_id}/generate - Generate comprehensive report",
            "GET /{team_id}/gap-analysis - Get AI gap analysis",
            "GET /{team_id}/executive-summary - Get executive summary",
            "GET /{team_id}/export/{format} - Export in different formats",
            "GET /{team_id}/status - Check report generation status"
        ]
    }

@router.post("/{team_id}/generate")
async def generate_comprehensive_report(
    team_id: str, 
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate a comprehensive strategic report with AI analysis"""
    
    from app.state import team_sessions, matching_sessions
    
    # Validate team exists
    if team_id not in team_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Dream team {team_id} not found. Assemble team first."
        )
    
    team_session = team_sessions[team_id]
    dream_team_report = team_session["dream_team_report"]
    matching_results = team_session["matching_results"]
    
    # Initialize report session
    report_id = f"report_{team_id}"
    report_sessions[report_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Report generation started...",
        "team_id": team_id,
        "request": request,
        "started_at": datetime.now()
    }
    
    # Start background processing
    background_tasks.add_task(
        process_report_generation,
        report_id,
        dream_team_report,
        matching_results,
        request
    )
    
    return ReportStatus(
        report_id=report_id,
        team_id=team_id,
        status="pending",
        progress_percent=0,
        message="Comprehensive report generation started. This may take 2-3 minutes.",
        estimated_completion_minutes=3
    )

async def process_report_generation(
    report_id: str,
    dream_team_report,
    matching_results,
    request: ReportGenerationRequest
):
    """Background task to generate comprehensive report"""
    try:
        # Update progress: Data preparation
        report_sessions[report_id].update({
            "status": "processing",
            "progress": 20,
            "message": "Preparing data for analysis..."
        })
        
        # Generate gap analysis with AI
        report_sessions[report_id].update({
            "progress": 40,
            "message": "Running AI-powered gap analysis..."
        })
        
        gap_analysis = None
        if ai_service and request.include_ai_analysis:
            try:
                gap_analysis = await ai_service.generate_gap_analysis(
                    dream_team_report, 
                    matching_results,
                    request.analysis_depth
                )
            except Exception as e:
                print(f"⚠️ AI analysis failed: {e}")
                gap_analysis = report_service.create_basic_gap_analysis(dream_team_report)
        else:
            gap_analysis = report_service.create_basic_gap_analysis(dream_team_report)
        
        # Generate executive summary
        report_sessions[report_id].update({
            "progress": 60,
            "message": "Creating executive summary..."
        })
        
        executive_summary = report_service.generate_executive_summary(
            dream_team_report, gap_analysis
        )
        
        # Generate comprehensive report
        report_sessions[report_id].update({
            "progress": 80,
            "message": "Assembling comprehensive report..."
        })
        
        comprehensive_report = report_service.generate_comprehensive_report(
            dream_team_report=dream_team_report,
            matching_results=matching_results,
            gap_analysis=gap_analysis,
            executive_summary=executive_summary,
            options=request
        )
        
        # Generate exports if requested
        exports = {}
        if request.export_formats:
            report_sessions[report_id].update({
                "progress": 90,
                "message": "Generating export formats..."
            })
            
            for format_type in request.export_formats:
                try:
                    export_content = report_service.export_report(
                        comprehensive_report, format_type
                    )
                    exports[format_type] = export_content
                except Exception as e:
                    print(f"⚠️ Export format {format_type} failed: {e}")
        
        # Complete
        report_sessions[report_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Report generation completed successfully!",
            "comprehensive_report": comprehensive_report,
            "gap_analysis": gap_analysis,
            "executive_summary": executive_summary,
            "exports": exports,
            "completed_at": datetime.now()
        })
        
    except Exception as e:
        report_sessions[report_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Report generation failed: {str(e)}",
            "error": str(e)
        })

@router.get("/{team_id}/status")
def get_report_status(team_id: str):
    """Get the status of report generation"""
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report generation found for team {team_id}"
        )
    
    session = report_sessions[report_id]
    
    return ReportStatus(
        report_id=report_id,
        team_id=team_id,
        status=session["status"],
        progress_percent=session["progress"],
        message=session["message"],
        estimated_completion_minutes=3 if session["status"] == "processing" else 0
    )

@router.get("/{team_id}/gap-analysis")
def get_gap_analysis(team_id: str):
    """Get AI-powered gap analysis for the team"""
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for team {team_id}. Generate report first."
        )
    
    session = report_sessions[report_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not completed. Current status: {session['status']}"
        )
    
    if "gap_analysis" not in session:
        raise HTTPException(
            status_code=404,
            detail="Gap analysis not found in report"
        )
    
    return session["gap_analysis"]

@router.get("/{team_id}/executive-summary")
def get_executive_summary(team_id: str):
    """Get executive summary of the team analysis"""
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for team {team_id}. Generate report first."
        )
    
    session = report_sessions[report_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not completed. Current status: {session['status']}"
        )
    
    if "executive_summary" not in session:
        raise HTTPException(
            status_code=404,
            detail="Executive summary not found in report"
        )
    
    return session["executive_summary"]

@router.get("/{team_id}/comprehensive")
def get_comprehensive_report(team_id: str):
    """Get the full comprehensive report"""
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for team {team_id}. Generate report first."
        )
    
    session = report_sessions[report_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not completed. Current status: {session['status']}"
        )
    
    if "comprehensive_report" not in session:
        raise HTTPException(
            status_code=404,
            detail="Comprehensive report not found"
        )
    
    return session["comprehensive_report"]

@router.get("/{team_id}/export/{format}")
async def export_report(team_id: str, format: str):
    """Export report in specified format (markdown, pdf, json, csv)"""
    
    valid_formats = ["markdown", "pdf", "json", "csv", "xlsx"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{format}'. Supported formats: {valid_formats}"
        )
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for team {team_id}. Generate report first."
        )
    
    session = report_sessions[report_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not completed. Current status: {session['status']}"
        )
    
    try:
        # Check if export already exists
        if "exports" in session and format in session["exports"]:
            export_content = session["exports"][format]
        else:
            # Generate export on demand
            comprehensive_report = session["comprehensive_report"]
            export_content = report_service.export_report(comprehensive_report, format)
        
        # Prepare file download
        if format == "json":
            content = json.dumps(export_content, indent=2, ensure_ascii=False)
            media_type = "application/json"
            filename = f"nsf_report_{team_id}.json"
        elif format == "markdown":
            content = export_content
            media_type = "text/markdown"
            filename = f"nsf_report_{team_id}.md"
        elif format == "csv":
            content = export_content
            media_type = "text/csv"
            filename = f"nsf_team_data_{team_id}.csv"
        elif format == "pdf":
            # Return binary content for PDF
            return StreamingResponse(
                io.BytesIO(export_content),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=nsf_report_{team_id}.pdf"}
            )
        elif format == "xlsx":
            # Return binary content for Excel
            return StreamingResponse(
                io.BytesIO(export_content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=nsf_data_{team_id}.xlsx"}
            )
        
        # Return text-based content
        return StreamingResponse(
            io.StringIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export report in {format} format: {str(e)}"
        )

@router.post("/{team_id}/regenerate-analysis")
async def regenerate_ai_analysis(
    team_id: str,
    background_tasks: BackgroundTasks,
    analysis_type: str = "gap_analysis"  # "gap_analysis", "strategic", "competitive"
):
    """Regenerate specific AI analysis with fresh perspective"""
    
    if not ai_service:
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Check Anthropic API configuration."
        )
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for team {team_id}"
        )
    
    session = report_sessions[report_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Original report not completed. Current status: {session['status']}"
        )
    
    # Start regeneration
    session.update({
        "regeneration_status": "processing",
        "regeneration_message": f"Regenerating {analysis_type}..."
    })
    
    background_tasks.add_task(
        regenerate_analysis_background,
        report_id,
        analysis_type
    )
    
    return {
        "message": f"Regenerating {analysis_type} analysis",
        "status": "processing",
        "estimated_time_minutes": 2
    }

async def regenerate_analysis_background(report_id: str, analysis_type: str):
    """Background task to regenerate specific analysis"""
    try:
        session = report_sessions[report_id]
        
        if analysis_type == "gap_analysis":
            from app.state import team_sessions
            team_id = session["team_id"]
            team_session = team_sessions[team_id]
            
            new_gap_analysis = await ai_service.generate_gap_analysis(
                team_session["dream_team_report"],
                team_session["matching_results"],
                "detailed"  # Force detailed analysis
            )
            
            session["gap_analysis"] = new_gap_analysis
            session["regeneration_status"] = "completed"
            session["regeneration_message"] = "Gap analysis regenerated successfully"
            
    except Exception as e:
        session["regeneration_status"] = "failed"
        session["regeneration_message"] = f"Regeneration failed: {str(e)}"

@router.get("/{team_id}/metrics")
def get_report_metrics(team_id: str):
    """Get quantitative metrics and scores from the report"""
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for team {team_id}"
        )
    
    session = report_sessions[report_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not completed. Current status: {session['status']}"
        )
    
    try:
        metrics = report_service.extract_metrics(session["comprehensive_report"])
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract metrics: {str(e)}"
        )

@router.delete("/{team_id}")
def delete_report_session(team_id: str):
    """Delete a report session and all associated data"""
    
    report_id = f"report_{team_id}"
    
    if report_id not in report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for team {team_id}"
        )
    
    del report_sessions[report_id]
    return {"message": f"Report session for team {team_id} deleted successfully"}

@router.get("/health")
def reports_health_check():
    """Check health of report services"""
    return {
        "reports_service": "healthy",
        "ai_service_status": "available" if ai_service else "unavailable",
        "anthropic_api": "configured" if ai_service else "not_configured",
        "active_report_sessions": len(report_sessions),
        "supported_export_formats": ["markdown", "pdf", "json", "csv", "xlsx"]
    }