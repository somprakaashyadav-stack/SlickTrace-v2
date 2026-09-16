from fastapi import APIRouter, HTTPException
from backend.services.anomaly.schemas import AnomalyResult
from backend.services.anomaly.behavior import detect_speed_reduction, detect_course_deviation, detect_unusual_stopping
from backend.services.anomaly.ais_gap import analyze_ais_gap
from backend.services.anomaly.isolation_forest import run_isolation_forest
from backend.services.ais.cleaning import clean_ais_track
from backend.services.drift.origin_routes import get_origin_cone
from backend.demo_service import demo_service
import numpy as np

router = APIRouter(prefix="/anomaly", tags=["Vessel Anomaly"])

@router.post("/analyze/{spill_id}/{mmsi}", response_model=AnomalyResult)
def analyze_vessel_anomaly(spill_id: str, mmsi: int):
    # Fetch Origin
    try:
        origin_cone = get_origin_cone(spill_id)
        origin = origin_cone.probable_origin
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Origin Cone: {str(e)}")
        
    # Fetch Track
    raw_tracks = demo_service.get_demo_ais_tracks()
    target_track = None
    for track in raw_tracks:
        if track.get("mmsi") == mmsi:
            target_track = track
            break
            
    if not target_track:
        raise HTTPException(status_code=404, detail="Vessel not found")
        
    cleaned_track = clean_ais_track(target_track)
    
    # 1. Behavior checks
    speed_details = detect_speed_reduction(cleaned_track)
    course_details = detect_course_deviation(cleaned_track)
    stop_details = detect_unusual_stopping(cleaned_track)
    
    # 2. Gap analysis
    # Need to pass raw track to analyze_ais_gap to detect gaps? 
    # clean_ais_track actually leaves the gap untouched, it just drops impossible points.
    gap_details = analyze_ais_gap(cleaned_track, origin)
    
    # 3. Isolation Forest features
    speeds = [pt.speed_knots for pt in cleaned_track.points]
    headings = [pt.heading_deg for pt in cleaned_track.points]
    
    speed_var = np.var(speeds) if speeds else 0.0
    heading_var = np.var(headings) if headings else 0.0
    gap_freq = 1.0 if gap_details.detected else 0.0
    
    # Origin proximity factor (heuristic: if any point is inside uncertainty radius)
    prox_factor = 0.0
    if gap_details.classification == "potentially_anomalous":
        prox_factor = 1.0
        
    features = [speed_var, heading_var, gap_freq, prox_factor]
    
    trajectory_score = run_isolation_forest(features)
    
    # Overall Flag
    overall_flag = (
        speed_details.detected or 
        course_details.detected or 
        gap_details.classification == "potentially_anomalous" or
        trajectory_score > 0.5
    )
    
    return AnomalyResult(
        mmsi=mmsi,
        speed_anomaly_score=speed_details.severity,
        course_deviation_score=course_details.severity,
        ais_gap_score=gap_details.severity,
        trajectory_anomaly_score=round(trajectory_score, 3),
        speed_details=speed_details,
        course_details=course_details,
        gap_details=gap_details,
        stop_details=stop_details,
        overall_anomaly_flag=overall_flag
    )
