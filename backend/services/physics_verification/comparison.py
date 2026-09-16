from typing import List, Tuple
from backend.services.physics_verification.schemas import PhysicsMetrics
from backend.services.characterization.geometry import haversine_distance
import numpy as np
from datetime import datetime

def compare_slicks(predicted_particles: List[Tuple[float, float]], 
                  observed_centroid: Tuple[float, float],
                  observed_radius_km: float = 10.0,
                  timing_error_hours: float = 0.0) -> PhysicsMetrics:
    """
    Compares the predicted particle cloud against the observed satellite slick.
    """
    if not predicted_particles:
        return PhysicsMetrics(
            spatial_overlap_pct=0.0,
            centroid_error_km=999.0,
            shape_similarity_score=0.0,
            orientation_similarity_score=0.0,
            timing_error_hours=timing_error_hours
        )
        
    # Calculate predicted centroid
    lons = [p[0] for p in predicted_particles]
    lats = [p[1] for p in predicted_particles]
    
    pred_centroid_lon = sum(lons) / len(lons)
    pred_centroid_lat = sum(lats) / len(lats)
    
    # 1. Centroid distance
    centroid_dist = haversine_distance(pred_centroid_lon, pred_centroid_lat, observed_centroid[0], observed_centroid[1])
    
    # 2. Spatial overlap (rough approximation: % of particles within observed_radius_km of observed_centroid)
    overlap_count = 0
    for lon, lat in predicted_particles:
        dist = haversine_distance(lon, lat, observed_centroid[0], observed_centroid[1])
        if dist <= observed_radius_km:
            overlap_count += 1
            
    overlap_pct = (overlap_count / len(predicted_particles)) * 100.0
    
    # 3. Shape / Orientation similarity (simplified for demo)
    # We could calculate the covariance matrix of the particles to find elongation/orientation
    # For now, we simulate a scoring function that rewards low centroid distance
    shape_score = max(0.0, 100.0 - (centroid_dist * 2.0))
    orientation_score = max(0.0, 100.0 - (centroid_dist * 1.5))
    
    return PhysicsMetrics(
        spatial_overlap_pct=overlap_pct,
        centroid_error_km=centroid_dist,
        shape_similarity_score=shape_score,
        orientation_similarity_score=orientation_score,
        timing_error_hours=timing_error_hours
    )
