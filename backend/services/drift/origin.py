from backend.services.drift.schemas import OriginCandidate
from typing import List, Dict, Any

def compute_origin_uncertainty(trajectories: List[List[Dict[str, Any]]], centroid_lat: float, centroid_lon: float, hours: int) -> float:
    """
    Computes an uncertainty radius in km based on the dispersion of the final particles.
    """
    if not trajectories:
        return 0.0
        
    final_lats = [t[-1]["lat"] for t in trajectories]
    final_lons = [t[-1]["lon"] for t in trajectories]
    
    # Calculate simple variance / std dev spread
    import math
    from backend.services.characterization.geometry import haversine_distance
    
    distances = []
    for lat, lon in zip(final_lats, final_lons):
        dist = haversine_distance(centroid_lon, centroid_lat, lon, lat)
        distances.append(dist)
        
    # The 95th percentile distance roughly bounds the uncertainty cone
    distances.sort()
    idx_95 = int(len(distances) * 0.95)
    radius_km = distances[idx_95] if distances else 0.0
    
    # Add base uncertainty based on time (e.g. 0.5 km per hour of drift)
    radius_km += (hours * 0.5)
    
    return round(radius_km, 2)
    
def generate_origin_candidate(
    centroid_lat: float, 
    centroid_lon: float, 
    start_time: str, 
    hours: int, 
    trajectories: List[List[Dict[str, Any]]]
) -> OriginCandidate:
    
    radius = compute_origin_uncertainty(trajectories, centroid_lat, centroid_lon, hours)
    
    # Time formatting (simplified string manipulation for ISO-8601)
    from datetime import datetime, timedelta
    release_time = datetime.fromisoformat(start_time.replace("Z", "+00:00")) - timedelta(hours=hours)
    
    return OriginCandidate(
        X0=round(centroid_lon, 5),
        Y0=round(centroid_lat, 5),
        T0=release_time.isoformat(),
        delta_t_hours=hours,
        uncertainty_radius_km=radius,
        origin_probability=0.85  # Example confidence score
    )
