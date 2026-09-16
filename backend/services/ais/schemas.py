from pydantic import BaseModel, Field
from typing import List, Optional

class AisPoint(BaseModel):
    timestamp: str
    lat: float
    lon: float
    speed_knots: float
    heading_deg: float
    course_deg: float
    is_reconstructed: bool = False

class AisTrack(BaseModel):
    mmsi: int
    vessel_name: str
    vessel_type: str
    points: List[AisPoint]

class CandidateScore(BaseModel):
    spatial_score: float = Field(0.0, description="Proximity to origin cone centroid (0-1)")
    temporal_score: float = Field(0.0, description="Proximity to estimated release time (0-1)")
    trajectory_score: float = Field(0.0, description="Intersection factor with origin cone (0-1)")
    heading_score: float = Field(0.0, description="Alignment with drift/spill trajectory (0-1)")
    ais_reliability: float = Field(1.0, description="Penalty for missing observations/gaps (0-1)")
    total_score: float = Field(0.0, description="Weighted composite score")

class CandidateVessel(BaseModel):
    mmsi: int
    vessel_name: str
    vessel_type: str
    scores: CandidateScore
    candidate_status: str = Field(description="'High Risk', 'Medium Risk', 'Low Risk', 'Irrelevant'")
    reconstructed_points: int = Field(0, description="Number of interpolated points in the track")

class CorrelateResponse(BaseModel):
    spill_id: str
    candidates: List[CandidateVessel]
