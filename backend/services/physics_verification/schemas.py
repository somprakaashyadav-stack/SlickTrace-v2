from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class PhysicsScenario(BaseModel):
    scenario_id: str
    release_time: str
    release_lat: float
    release_lon: float
    duration_hours: float
    wind_variance: float = 0.0
    current_variance: float = 0.0

class PhysicsMetrics(BaseModel):
    spatial_overlap_pct: float
    centroid_error_km: float
    shape_similarity_score: float
    orientation_similarity_score: float
    timing_error_hours: float

class PhysicsVerificationResult(BaseModel):
    mmsi: int
    vessel_name: str
    physics_consistency_score: int = Field(..., ge=0, le=100)
    classification: Literal["High physical consistency", "Moderate physical consistency", "Low physical consistency"]
    best_scenario: PhysicsScenario
    metrics: PhysicsMetrics
    
class PhysicsVerificationResponse(BaseModel):
    spill_id: str
    top_n_tested: int
    results: List[PhysicsVerificationResult]
