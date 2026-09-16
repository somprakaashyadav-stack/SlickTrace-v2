from pydantic import BaseModel, Field
from typing import List, Optional

class DriftSimulationRequest(BaseModel):
    spill_id: str
    hours_modeled: int = Field(24, description="Hours to model backward or forward")
    mode: str = Field("backward", description="'backward' (hindcast) or 'forward' (forecast)")

class OriginCandidate(BaseModel):
    X0: float = Field(description="Longitude (centroid)")
    Y0: float = Field(description="Latitude (centroid)")
    T0: str = Field(description="Estimated Release Time (ISO-8601)")
    delta_t_hours: float = Field(description="Hours since release")
    uncertainty_radius_km: float = Field(description="Radius of uncertainty cone")
    origin_probability: float = Field(description="Confidence score [0-1]")

class DriftTrajectoryPoint(BaseModel):
    step: int
    time: str
    lat: float
    lon: float

class DriftSimulationResponse(BaseModel):
    slick_id: str
    engine: str = Field(description="'Demo Lagrangian Model' or 'OpenDrift'")
    direction: str = Field(description="'backward' or 'forward'")
    hours_modeled: int
    particle_count: int
    wind_speed_knots: float
    wind_direction_deg: float
    current_speed_knots: float
    current_direction_deg: float
    trajectories: List[List[DriftTrajectoryPoint]] = Field(description="List of particle trajectories")
    origin_candidate: Optional[OriginCandidate] = None

class OriginConeResponse(BaseModel):
    spill_id: str
    observed_slick_polygon: List[List[float]]
    observed_centroid: List[float]
    time_window_start: str
    time_window_end: str
    probable_origin: OriginCandidate
    trajectories: List[List[DriftTrajectoryPoint]]

