from backend.services.physics_verification.schemas import PhysicsMetrics
from typing import Literal

def calculate_physics_score(metrics: PhysicsMetrics) -> int:
    """
    Weights the spatial, temporal, and morphological factors to produce a 
    single physical consistency score (0-100).
    """
    # Base score on spatial overlap
    overlap_score = min(100.0, metrics.spatial_overlap_pct)
    
    # Penalize centroid error (e.g. drop 2 points per km of error)
    centroid_penalty = min(50.0, metrics.centroid_error_km * 2.0)
    
    # Penalize timing error (e.g. drop 5 points per hour)
    timing_penalty = min(30.0, abs(metrics.timing_error_hours) * 5.0)
    
    # Shape/Orientation reward/penalty
    morph_score = (metrics.shape_similarity_score + metrics.orientation_similarity_score) / 2.0
    
    raw_score = (overlap_score * 0.4) + (morph_score * 0.6) - centroid_penalty - timing_penalty
    
    return int(min(100, max(0, round(raw_score))))

def classify_consistency(score: int) -> Literal["High physical consistency", "Moderate physical consistency", "Low physical consistency"]:
    """
    Categorizes the score using STRICT TERMINOLOGY.
    Does not make causal claims.
    """
    if score >= 75:
        return "High physical consistency"
    elif score >= 40:
        return "Moderate physical consistency"
    else:
        return "Low physical consistency"
