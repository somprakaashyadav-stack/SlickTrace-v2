from fastapi import APIRouter, HTTPException
from backend.services.ais.schemas import CorrelateResponse
from backend.services.ais.cleaning import clean_ais_track
from backend.services.ais.filtering import apply_space_time_window
from backend.services.ais.trajectory import reconstruct_trajectory
from backend.services.ais.correlation import score_vessel
from backend.services.drift.origin_routes import get_origin_cone
from backend.services.providers.factory import ais_provider
from backend.services.providers.ais import DemoAISProvider

router = APIRouter(prefix="/ais", tags=["AIS Correlation"])

@router.post("/correlate/{spill_id}", response_model=CorrelateResponse)
def correlate_ais_tracks(spill_id: str):
    """
    Spatio-Temporal AIS Correlation Pipeline.
    1. Fetches the 4D Origin Cone.
    2. Fetches raw AIS tracks.
    3. Cleans, filters, reconstructs, and scores each track.
    4. Returns ranked suspect candidates.
    """
    # 1. Fetch 4D Origin Cone
    try:
        origin_cone = get_origin_cone(spill_id)
        probable_origin = origin_cone.probable_origin
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Origin Cone: {str(e)}")
        
    if not probable_origin:
        raise HTTPException(status_code=400, detail="No probable origin found for this spill.")

    # 2. Fetch Raw AIS Tracks (from Data Engine)
    try:
        # We need a bbox and time window for real API. For demo, they are ignored.
        raw_tracks = ais_provider.get_ais_tracks(
            time_window_start=origin_cone.time_window_start,
            time_window_end=origin_cone.time_window_end,
            bbox=[70.0, 15.0, 75.0, 20.0] # Dummy bounding box around Mumbai for demo/real fallback
        )
    except Exception:
        # Graceful fallback
        demo = DemoAISProvider()
        raw_tracks = demo.get_ais_tracks("", "", [])
    
    candidates = []
    
    # Run the pipeline for each vessel
    for raw_track in raw_tracks:
        # 3a. Clean the data (remove impossible coords/speed jumps)
        cleaned_track = clean_ais_track(raw_track)
        
        # 3b. Fast Space-Time Window Filter
        if not apply_space_time_window(cleaned_track, probable_origin):
            continue # Skip irrelevant vessels
            
        # 3c. Reconstruct gaps (Kinematic interpolation)
        reconstructed_track = reconstruct_trajectory(cleaned_track)
        
        # 3d. Score Vessel
        candidate = score_vessel(reconstructed_track, probable_origin)
        
        if candidate.candidate_status != "Irrelevant":
            candidates.append(candidate)
            
    # Sort candidates by total score descending
    candidates.sort(key=lambda x: x.scores.total_score, reverse=True)
    
    return CorrelateResponse(
        spill_id=spill_id,
        candidates=candidates
    )
