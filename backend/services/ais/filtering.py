from backend.services.ais.schemas import AisTrack
from backend.services.drift.schemas import OriginCandidate
from backend.services.characterization.geometry import haversine_distance
from datetime import datetime, timedelta

# Buffer around the uncertainty radius (in km) to ensure we don't drop edge cases
SPATIAL_BUFFER_KM = 50.0 
# Buffer around the T0 time (in hours) to search for vessels
TEMPORAL_BUFFER_HOURS = 24.0 

def apply_space_time_window(track: AisTrack, origin: OriginCandidate) -> bool:
    """
    Returns True if the vessel falls within the space-time bounding box of the origin cone.
    This acts as a fast preliminary filter to discard irrelevant vessels.
    """
    if not track.points:
        return False
        
    origin_t0 = datetime.fromisoformat(origin.T0.replace("Z", "+00:00"))
    t_start = origin_t0 - timedelta(hours=TEMPORAL_BUFFER_HOURS)
    t_end = origin_t0 + timedelta(hours=TEMPORAL_BUFFER_HOURS)
    
    max_search_radius_km = origin.uncertainty_radius_km + SPATIAL_BUFFER_KM
    
    for pt in track.points:
        try:
            pt_time = datetime.fromisoformat(pt.timestamp.replace("Z", "+00:00"))
        except Exception:
            continue
            
        # Check temporal window
        if t_start <= pt_time <= t_end:
            # Check spatial window
            dist_km = haversine_distance(origin.X0, origin.Y0, pt.lon, pt.lat)
            if dist_km <= max_search_radius_km:
                return True
                
    return False
