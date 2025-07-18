from fastapi import APIRouter, HTTPException, Depends
from app.models.team import (
    DreamTeamRequest, DreamTeamReport, AffinityMatrixExport, TeamComparison
)
from app.services.dream_team_service import DreamTeamService
from app.services.matching_service import MatchingService
from typing import Dict

router = APIRouter(prefix="/teams", tags=["dream_teams"])
dream_team_service = DreamTeamService()

from app.state import team_sessions

@router.get("/")
def teams_info():
    """Get dream team service information"""
    return {
        "message": "NSF Dream Team Assembly Service",
        "available_strategies": ["hybrid", "greedy", "rankings"],
        "default_strategy": "hybrid",
        "available_endpoints": [
            "POST /assemble - Assemble dream team",
            "GET /{team_id} - Get team details",
            "GET /{team_id}/matrix - Export affinity matrix",
            "POST /{team_id}/compare - Compare strategies"
        ]
    }

@router.post("/assemble", response_model=DreamTeamReport)
def assemble_dream_team(request: DreamTeamRequest):
    """Assemble a dream team from matching results"""
    
    from app.state import matching_sessions
    
    # Check if matching results exist
    if request.solicitation_id not in matching_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Matching results for solicitation {request.solicitation_id} not found. Run matching first."
        )
    
    session = matching_sessions[request.solicitation_id]
    
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Matching not completed. Current status: {session['status']}"
        )
    
    matching_results = session["results"]
    
    try:
        # Assemble dream team
        dream_team_report = dream_team_service.assemble_dream_team(
            matching_results=matching_results,
            strategy=request.strategy,
            max_team_size=request.max_team_size,
            guaranteed_top_n=request.guaranteed_top_n,
            marginal_threshold=request.marginal_threshold
        )
        
        # Store team session
        team_id = f"team_{request.solicitation_id}"
        team_sessions[team_id] = {
            "dream_team_report": dream_team_report,
            "matching_results": matching_results,
            "affinity_matrix": None  # Will be created on demand
        }
        
        return dream_team_report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assemble dream team: {str(e)}"
        )

@router.get("/{team_id}", response_model=DreamTeamReport)
def get_dream_team(team_id: str):
    """Get dream team details"""
    
    if team_id not in team_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Dream team {team_id} not found"
        )
    
    return team_sessions[team_id]["dream_team_report"]

@router.get("/{team_id}/matrix", response_model=AffinityMatrixExport)
def export_affinity_matrix(team_id: str):
    """Export the affinity matrix used for team selection"""
    
    if team_id not in team_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Dream team {team_id} not found"
        )
    
    session = team_sessions[team_id]
    
    # Create affinity matrix if not cached
    if session["affinity_matrix"] is None:
        matching_results = session["matching_results"]
        affinity_df, skills_list = dream_team_service.create_affinity_matrix(
            matching_results, top_n_researchers=20
        )
        session["affinity_matrix"] = {
            "df": affinity_df,
            "skills": skills_list
        }
    
    affinity_data = session["affinity_matrix"]
    
    return dream_team_service.export_affinity_matrix(
        affinity_data["df"],
        team_id.replace("team_", ""),
        affinity_data["skills"]
    )

@router.post("/{team_id}/optimize")
def optimize_team(team_id: str, request: DreamTeamRequest):
    """Re-optimize team with different parameters"""
    
    if team_id not in team_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Dream team {team_id} not found"
        )
    
    session = team_sessions[team_id]
    matching_results = session["matching_results"]
    
    # Update request with original solicitation_id
    request.solicitation_id = matching_results.solicitation_id
    
    try:
        # Re-assemble with new parameters
        new_dream_team_report = dream_team_service.assemble_dream_team(
            matching_results=matching_results,
            strategy=request.strategy,
            max_team_size=request.max_team_size,
            guaranteed_top_n=request.guaranteed_top_n,
            marginal_threshold=request.marginal_threshold
        )
        
        # Update session
        session["dream_team_report"] = new_dream_team_report
        session["affinity_matrix"] = None  # Clear cache
        
        return new_dream_team_report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize team: {str(e)}"
        )

@router.post("/{team_id}/compare", response_model=TeamComparison)
def compare_strategies(team_id: str):
    """Compare different team selection strategies"""
    
    if team_id not in team_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Dream team {team_id} not found"
        )
    
    session = team_sessions[team_id]
    matching_results = session["matching_results"]
    
    try:
        # Create affinity matrix
        affinity_df, skills_list = dream_team_service.create_affinity_matrix(
            matching_results, top_n_researchers=20
        )
        
        strategies_results = {}
        
        # Test each strategy
        for strategy in ["hybrid", "greedy", "rankings"]:
            if strategy == "hybrid":
                team_indices, _ = dream_team_service.dream_team_hybrid_strategy(affinity_df)
            elif strategy == "greedy":
                team_indices, _ = dream_team_service.dream_team_greedy_algorithm(affinity_df)
            else:  # rankings
                team_indices, _ = dream_team_service.dream_team_by_rankings(affinity_df)
            
            _, coverage = dream_team_service.calculate_team_coverage(affinity_df, team_indices)
            team_members = [affinity_df.index[idx] for idx in team_indices]
            
            strategies_results[strategy] = {
                "coverage": round(coverage, 2),
                "team_size": len(team_indices),
                "team_members": team_members
            }
        
        # Determine best strategy
        best_strategy = max(strategies_results.keys(), 
                          key=lambda x: strategies_results[x]["coverage"])
        
        comparison_notes = f"""
Strategy Comparison:
- Hybrid: {strategies_results['hybrid']['coverage']} coverage, {strategies_results['hybrid']['team_size']} members
- Greedy: {strategies_results['greedy']['coverage']} coverage, {strategies_results['greedy']['team_size']} members  
- Rankings: {strategies_results['rankings']['coverage']} coverage, {strategies_results['rankings']['team_size']} members

Best Strategy: {best_strategy.title()} (highest coverage)
"""
        
        return TeamComparison(
            solicitation_id=matching_results.solicitation_id,
            strategies=strategies_results,
            recommended_strategy=best_strategy,
            comparison_notes=comparison_notes.strip()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare strategies: {str(e)}"
        )

@router.delete("/{team_id}")
def delete_team_session(team_id: str):
    """Delete a team session"""
    
    if team_id not in team_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Dream team {team_id} not found"
        )
    
    del team_sessions[team_id]
    return {"message": f"Dream team session {team_id} deleted"}