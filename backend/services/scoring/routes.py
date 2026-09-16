from fastapi import APIRouter, HTTPException
from backend.services.scoring.schemas import InitialScoreResponse
from backend.services.ais.routes import correlate_ais_tracks
from backend.services.anomaly.routes import analyze_vessel_anomaly
from backend.services.scoring.engine import compute_initial_score

router = APIRouter(prefix="/scoring", tags=["Scoring Engine"])

@router.post("/initial/{spill_id}", response_model=InitialScoreResponse)
def get_initial_suspect_scores(spill_id: str):
    """
    Orchestrates the AIS correlation and Anomaly detection engines to 
    produce a unified, weighted Initial Suspect Score prioritizing vessels for investigation.
    """
    
    # 1. Run AIS Correlation to get candidate vessels and spatial/temporal metrics
    try:
        correlate_response = correlate_ais_tracks(spill_id)
        candidates = correlate_response.candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to correlate AIS tracks: {str(e)}")
        
    scored_candidates = []
    
    for candidate in candidates:
        # 2. For each candidate, run Anomaly Detection
        try:
            anomaly_result = analyze_vessel_anomaly(spill_id, candidate.mmsi)
        except Exception:
            continue
            
        # 3. Compute final unified score
        priority = compute_initial_score(candidate, anomaly_result)
        scored_candidates.append(priority)
        
    # 4. Sort by initial_score descending
    scored_candidates.sort(key=lambda x: x.initial_score, reverse=True)
    
    # 5. Assign ranks
    for i, candidate in enumerate(scored_candidates):
        candidate.rank = i + 1
        
    return InitialScoreResponse(
        spill_id=spill_id,
        candidates=scored_candidates
    )
