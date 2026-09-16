from fastapi import APIRouter, HTTPException
from backend.services.ranking.schemas import FinalRankingResponse
from backend.services.ranking.engine import compute_final_rankings
from backend.services.ranking.config import ranking_config
from backend.services.scoring.routes import get_initial_suspect_scores
from backend.services.physics_verification.routes import run_physics_verification

router = APIRouter(prefix="/ranking", tags=["Final Ranking"])

@router.get("/{spill_id}", response_model=FinalRankingResponse)
def get_final_ranking(spill_id: str):
    """
    Computes the final suspect ranking by combining the Initial Score (AIS/Behavior)
    and the Physics Consistency Score.
    """
    # 1. Get initial candidates
    try:
        initial_response = get_initial_suspect_scores(spill_id)
        initial_candidates = initial_response.candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get initial scores: {str(e)}")
        
    # 2. Get physics verification results for Top 3
    try:
        physics_response = run_physics_verification(spill_id, top_n=3)
        physics_results = physics_response.results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run physics verification: {str(e)}")
        
    # 3. Compute Final Rankings
    final_rankings = compute_final_rankings(initial_candidates, physics_results)
    
    return FinalRankingResponse(
        spill_id=spill_id,
        alpha_weight=ranking_config.ALPHA_WEIGHT,
        beta_weight=ranking_config.BETA_WEIGHT,
        rankings=final_rankings
    )
