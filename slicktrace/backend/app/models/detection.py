import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DetectionStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class DetectionModel(str, PyEnum):
    UNETPLUSPLUS = "unetplusplus"
    DEEPLABV3PLUS = "deeplabv3plus"
    ENSEMBLE = "ensemble"


class SpillDetection(Base):
    __tablename__ = "spill_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    imagery_id = Column(UUID(as_uuid=True), ForeignKey("imagery.id"), nullable=False)
    status = Column(Enum(DetectionStatus), nullable=False, default=DetectionStatus.PENDING)
    model_used = Column(Enum(DetectionModel), nullable=True)
    spill_polygon = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    centroid = Column(Geometry("POINT", srid=4326), nullable=True)
    area_km2 = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    lookalike_prob = Column(Float, nullable=True)
    is_oil = Column(Boolean, nullable=True)
    sam2_refined = Column(Boolean, nullable=False, default=False)
    celery_task_id = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    unavailable_reason = Column(Text, nullable=True)
    raw_output = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    incident = relationship("Incident", back_populates="detections")
    imagery = relationship("Imagery", back_populates="detections")
    hindcast_runs = relationship("HindcastRun", back_populates="detection", cascade="all, delete-orphan")
