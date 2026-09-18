import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CandidateVessel(Base):
    __tablename__ = "candidate_vessels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    ais_query_id = Column(UUID(as_uuid=True), ForeignKey("ais_queries.id"), nullable=False)

    mmsi = Column(String(50), nullable=False)
    vessel_name = Column(String(256), nullable=True)
    vessel_type = Column(String(128), nullable=True)
    flag_state = Column(String(64), nullable=True)
    imo_number = Column(String(20), nullable=True)
    call_sign = Column(String(20), nullable=True)

    # Observation & Strategy tracking
    observations_count = Column(Integer, nullable=True)
    first_observation = Column(DateTime(timezone=True), nullable=True)
    last_observation = Column(DateTime(timezone=True), nullable=True)
    minimum_distance_to_origin = Column(Float, nullable=True)
    time_difference = Column(Float, nullable=True)
    strategies_matched = Column(JSONB, nullable=True)
    status_display = Column(String(255), default="Candidate because of observed AIS evidence")

    # Kinematic & Trajectory behavior metrics
    mean_sog = Column(Float, nullable=True)
    min_sog = Column(Float, nullable=True)
    max_sog = Column(Float, nullable=True)
    speed_change = Column(Float, nullable=True)
    acceleration = Column(Float, nullable=True)
    mean_cog = Column(Float, nullable=True)
    course_change = Column(Float, nullable=True)
    turn_rate = Column(Float, nullable=True)
    time_in_origin_zone = Column(Float, nullable=True)
    distance_to_origin = Column(Float, nullable=True)
    ais_gap_count = Column(Integer, nullable=True)
    max_ais_gap_duration = Column(Float, nullable=True)
    track_completeness = Column(Float, nullable=True)
    trajectory_length = Column(Float, nullable=True)
    behavioral_metrics = Column(JSONB, nullable=True)

    # Anomalies & Explainable Isolation Forest
    anomalies = Column(JSONB, nullable=True)  # List of display strings
    detailed_anomalies = Column(JSONB, nullable=True)  # List of structured anomaly objects
    isolation_forest_score = Column(Float, nullable=True)
    isolation_forest_explanations = Column(JSONB, nullable=True)

    # Core Physical Consistency Ranking (Strict non-guilt terminology)
    physical_score = Column(Float, nullable=True)  # Primary: Physical Consistency Score (0-100)
    physical_consistency_score = Column(Float, nullable=True)
    investigation_consistency_score = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    scoring_mode = Column(String(64), nullable=True)

    # 10 Consistency Factors
    spatial_consistency = Column(Float, nullable=True)
    temporal_consistency = Column(Float, nullable=True)
    origin_proximity = Column(Float, nullable=True)
    drift_consistency = Column(Float, nullable=True)
    trajectory_consistency = Column(Float, nullable=True)
    speed_behavior_consistency = Column(Float, nullable=True)
    course_behavior_consistency = Column(Float, nullable=True)
    ais_continuity_score = Column(Float, nullable=True)
    counterfactual_similarity = Column(Float, nullable=True)

    # Supporting legacy scores
    proximity_score = Column(Float, nullable=True)
    timing_score = Column(Float, nullable=True)
    heading_score = Column(Float, nullable=True)
    speed_anomaly_score = Column(Float, nullable=True)
    ais_gap_score = Column(Float, nullable=True)
    vessel_type_score = Column(Float, nullable=True)

    # Factor breakdowns and explainability
    feature_values = Column(JSONB, nullable=True)
    feature_contributions = Column(JSONB, nullable=True)
    consistency_explanation = Column(Text, nullable=True)
    limitations = Column(JSONB, nullable=True)
    disclaimer = Column(
        String(255),
        default="This score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility.",
    )

    track_geometry = Column(Geometry("LINESTRING", srid=4326), nullable=True)
    closest_approach_point = Column(Geometry("POINT", srid=4326), nullable=True)
    closest_approach_time = Column(DateTime(timezone=True), nullable=True)
    closest_approach_km = Column(Float, nullable=True)

    counterfactual_run = Column(Boolean, nullable=False, default=False)
    counterfactual_consistent = Column(Boolean, nullable=True)
    counterfactual_notes = Column(Text, nullable=True)
    counterfactual_results = Column(JSONB, nullable=True)
    counterfactual_layers = Column(JSONB, nullable=True)

    ais_track_raw = Column(JSONB, nullable=True)
    xgboost_features = Column(JSONB, nullable=True)


    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    incident = relationship("Incident", back_populates="candidates")
    ais_query = relationship("AISQuery", back_populates="candidates")
