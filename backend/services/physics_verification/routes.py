from fastapi import APIRouter, HTTPException, Query
from backend.services.physics_verification.schemas import PhysicsVerificationResponse, PhysicsVerificationResult
from backend.services.physics_verification.scenarios import generate_candidate_scenarios
from backend.services.physics_verification.simulator import PhysicsSimulator
from backend.services.physics_verification.comparison import compare_slicks
from backend.services.physics_verification.scoring import calculate_physics_score, classify_consistency
from backend.services.scoring.routes import get_initial_suspect_scores
from backend.services.drift.origin_routes import get_origin_cone
from backend.services.ais.cleaning import parse_time
from backend.demo_service import demo_service
import time

router = APIRouter(prefix="/physics_verification", tags=["Physics Verification"])
engine = PhysicsSimulator()

@router.post("/run/{spill_id}", response_model=PhysicsVerificationResponse)
def run_physics_verification(spill_id: str, top_n: int = Query(3, ge=1, le=10)):
    """
    Runs counterfactual physics verification for the Top-N prioritized candidate vessels.
    """
    # 1. Get Top-N candidates
    try:
        initial_scores = get_initial_suspect_scores(spill_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get initial scores: {str(e)}")
        
    candidates = initial_scores.candidates[:top_n]
    
    # 2. Get Origin Cone (for estimated T0 and observed slick center)
    try:
        origin_cone = get_origin_cone(spill_id)
        estimated_t0 = origin_cone.probable_origin.T0
        observed_centroid = (origin_cone.probable_origin.X0, origin_cone.probable_origin.Y0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Origin Cone: {str(e)}")
        
    # Get all tracks to fetch raw tracks for candidates
    raw_tracks = demo_service.get_demo_ais_tracks()
    track_map = {t["mmsi"]: t for t in raw_tracks}
    
    results = []
    
    # We need to map dict to AisTrack for scenarios, but demo_service returns dicts. 
    # Let's import AisTrack and parse it.
    from backend.services.ais.schemas import AisTrack
    from backend.services.ais.cleaning import clean_ais_track
    
    for candidate in candidates:
        raw_track_dict = track_map.get(candidate.mmsi)
        if not raw_track_dict:
            continue
            
        track = clean_ais_track(raw_track_dict)
        
        # Generate Scenarios
        scenarios = generate_candidate_scenarios(track, estimated_t0, hours_range=6.0)
        
        best_scenario = None
        best_metrics = None
        best_score = -1
        
        for scenario in scenarios:
            # Calculate timing error vs estimated T0
            sc_time = parse_time(scenario.release_time)
            orig_t0 = parse_time(estimated_t0)
            timing_error = (sc_time - orig_t0).total_seconds() / 3600.0
            
            # Simulate forward
            predicted_particles = engine.simulate_forward(scenario, num_particles=100)
            
            # Compare
            metrics = compare_slicks(predicted_particles, observed_centroid, observed_radius_km=15.0, timing_error_hours=timing_error)
            
            # Score
            score = calculate_physics_score(metrics)
            
            if score > best_score:
                best_score = score
                best_metrics = metrics
                best_scenario = scenario
                
        if best_scenario and best_metrics:
            results.append(PhysicsVerificationResult(
                mmsi=candidate.mmsi,
                vessel_name=candidate.vessel_name,
                physics_consistency_score=best_score,
                classification=classify_consistency(best_score),
                best_scenario=best_scenario,
                metrics=best_metrics
            ))
            
    # Sort results by physics consistency score
    results.sort(key=lambda x: x.physics_consistency_score, reverse=True)
    
    return PhysicsVerificationResponse(
        spill_id=spill_id,
        top_n_tested=top_n,
        results=results
    )
