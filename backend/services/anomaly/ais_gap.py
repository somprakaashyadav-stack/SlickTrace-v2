from backend.services.ais.schemas import AisTrack
from backend.services.anomaly.schemas import AnomalyExplainability
from backend.services.drift.schemas import OriginCandidate
from backend.services.ais.cleaning import parse_time
from backend.services.characterization.geometry import haversine_distance
from datetime import timedelta

def analyze_ais_gap(track: AisTrack, origin: OriginCandidate) -> AnomalyExplainability:
    """
    Distinguishes between a normal communication dropout and a potentially anomalous gap
    (e.g., turning off AIS to hide illicit activity).
    """
    if len(track.points) < 2:
        return AnomalyExplainability(detected=False, classification="normal", reason="Not enough data", severity=0.0)
        
    max_gap_minutes = 0.0
    gap_start_pt = None
    
    for i in range(1, len(track.points)):
        pt1 = track.points[i-1]
        pt2 = track.points[i]
        
        # Skip points that we generated ourselves during reconstruction
        if pt1.is_reconstructed or pt2.is_reconstructed:
            continue
            
        try:
            t1 = parse_time(pt1.timestamp)
            t2 = parse_time(pt2.timestamp)
            gap_mins = (t2 - t1).total_seconds() / 60.0
            
            if gap_mins > max_gap_minutes:
                max_gap_minutes = gap_mins
                gap_start_pt = pt1
        except Exception:
            continue
            
    if max_gap_minutes < 30.0:
        return AnomalyExplainability(
            detected=False,
            classification="normal",
            reason="Continuous transponder coverage",
            severity=0.0
        )
        
    # We have a gap. Is it suspicious?
    # Criteria: gap is near the Origin Cone time (T0) and space (X0, Y0)
    if gap_start_pt and origin:
        try:
            gap_time = parse_time(gap_start_pt.timestamp)
            origin_t0 = parse_time(origin.T0)
            
            time_diff_hours = abs((gap_time - origin_t0).total_seconds() / 3600.0)
            dist_km = haversine_distance(origin.X0, origin.Y0, gap_start_pt.lon, gap_start_pt.lat)
            
            # If gap starts within 12 hours of origin T0 and within 50km of origin
            if time_diff_hours <= 12.0 and dist_km <= origin.uncertainty_radius_km + 50.0:
                return AnomalyExplainability(
                    detected=True,
                    classification="potentially_anomalous",
                    reason=f"Gap occurred near estimated origin window (dist: {dist_km:.1f}km)",
                    duration_minutes=max_gap_minutes,
                    severity=min(1.0, max_gap_minutes / 120.0)
                )
        except Exception:
            pass
            
    # Gap exists, but not near the origin
    return AnomalyExplainability(
        detected=True,
        classification="normal_dropout",
        reason="Communication dropout outside of critical spatio-temporal window",
        duration_minutes=max_gap_minutes,
        severity=0.2
    )
