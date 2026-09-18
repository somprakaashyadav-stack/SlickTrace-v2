"""SlickTrace v2 — Pydantic schemas for CandidateVessel and Physical Consistency Ranking"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FactorContributionSchema(BaseModel):
    factor: str
    value: Any
    contribution: float
    weight: float
    explanation: str


class CandidateResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    mmsi: str
    vessel_name: Optional[str] = None
    vessel_type: Optional[str] = None
    flag_state: Optional[str] = None
    imo_number: Optional[str] = None
    call_sign: Optional[str] = None

    # Observation & Strategy Tracking
    observations_count: Optional[int] = None
    first_observation: Optional[datetime] = None
    last_observation: Optional[datetime] = None
    minimum_distance_to_origin: Optional[float] = None
    time_difference: Optional[float] = None
    strategies_matched: Optional[List[str]] = None
    status_display: Optional[str] = None

    # Trajectory & Behavior Metrics
    mean_sog: Optional[float] = None
    min_sog: Optional[float] = None
    max_sog: Optional[float] = None
    speed_change: Optional[float] = None
    acceleration: Optional[float] = None
    mean_cog: Optional[float] = None
    course_change: Optional[float] = None
    turn_rate: Optional[float] = None
    time_in_origin_zone: Optional[float] = None
    distance_to_origin: Optional[float] = None
    ais_gap_count: Optional[int] = None
    max_ais_gap_duration: Optional[float] = None
    track_completeness: Optional[float] = None
    trajectory_length: Optional[float] = None
    behavioral_metrics: Optional[Dict[str, Any]] = None

    # Explainable Anomalies
    anomalies: Optional[List[str]] = None
    detailed_anomalies: Optional[List[Dict[str, Any]]] = None
    isolation_forest_score: Optional[float] = None
    isolation_forest_explanations: Optional[List[str]] = None

    # Physical Consistency Ranking (Strict non-guilt terminology)
    score: Optional[float] = None
    physical_score: Optional[float] = None
    physical_consistency_score: Optional[float] = None
    investigation_consistency_score: Optional[float] = None
    rank: Optional[int] = None
    confidence: Optional[float] = None
    scoring_mode: Optional[str] = None

    # 10 Consistency Factors
    spatial_consistency: Optional[float] = None
    temporal_consistency: Optional[float] = None
    origin_proximity: Optional[float] = None
    drift_consistency: Optional[float] = None
    trajectory_consistency: Optional[float] = None
    speed_behavior_consistency: Optional[float] = None
    course_behavior_consistency: Optional[float] = None
    ais_continuity_score: Optional[float] = None
    counterfactual_similarity: Optional[float] = None

    # Supporting subscores
    proximity_score: Optional[float] = None
    timing_score: Optional[float] = None
    heading_score: Optional[float] = None
    speed_anomaly_score: Optional[float] = None
    ais_gap_score: Optional[float] = None
    vessel_type_score: Optional[float] = None

    # Explainability & Limitations
    feature_values: Optional[Dict[str, Any]] = None
    feature_contributions: Optional[List[Dict[str, Any]]] = None
    consistency_explanation: Optional[str] = None
    explanation: Optional[str] = None
    limitations: Optional[List[str]] = None
    disclaimer: Optional[str] = (
        "This score measures consistency with the reconstructed physical scenario. "
        "It is not a determination of responsibility."
    )

    # Verification & Counterfactual
    closest_approach_km: Optional[float] = None
    closest_approach_time: Optional[datetime] = None
    counterfactual_run: bool = False
    counterfactual_consistent: Optional[bool] = None
    counterfactual_notes: Optional[str] = None
    counterfactual_results: Optional[Dict[str, Any]] = None
    counterfactual_layers: Optional[Dict[str, Any]] = None


    # Geometry & Tracks
    track_geometry: Optional[Dict[str, Any]] = None
    ais_track_raw: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True
