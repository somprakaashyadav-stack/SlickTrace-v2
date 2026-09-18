import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class HindcastStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class HindcastRun(Base):
    __tablename__ = "hindcast_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    detection_id = Column(UUID(as_uuid=True), ForeignKey("spill_detections.id"), nullable=False)
    status = Column(Enum(HindcastStatus), nullable=False, default=HindcastStatus.PENDING)

    start_lat = Column(Float, nullable=False)
    start_lon = Column(Float, nullable=False)
    detection_time = Column(DateTime(timezone=True), nullable=False)
    hours_back = Column(Integer, nullable=False, default=24)
    n_particles = Column(Integer, nullable=False, default=1000)
    wind_reader = Column(String(64), nullable=True)
    current_reader = Column(String(64), nullable=True)

    origin_time_start = Column(DateTime(timezone=True), nullable=True)
    origin_time_end = Column(DateTime(timezone=True), nullable=True)
    origin_p50_polygon = Column(Geometry("POLYGON", srid=4326), nullable=True)
    origin_p75_polygon = Column(Geometry("POLYGON", srid=4326), nullable=True)
    origin_p90_polygon = Column(Geometry("POLYGON", srid=4326), nullable=True)
    origin_centroid = Column(Geometry("POINT", srid=4326), nullable=True)
    trajectory_geojson = Column(JSONB, nullable=True)
    particle_timesteps_geojson = Column(JSONB, nullable=True)
    uncertainty_metadata = Column(JSONB, nullable=True)
    duration_slices = Column(JSONB, nullable=True)
    simulation_config = Column(JSONB, nullable=True)
    forcing_provenance = Column(JSONB, nullable=True)

    celery_task_id = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    incident = relationship("Incident", back_populates="hindcast_runs")
    detection = relationship("SpillDetection", back_populates="hindcast_runs")
    ais_queries = relationship("AISQuery", back_populates="hindcast_run", cascade="all, delete-orphan")
