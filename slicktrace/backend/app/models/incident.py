import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class IncidentStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    CLOSED = "closed"


class IncidentMode(str, PyEnum):
    REAL = "real"
    DEMO = "demo"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    operator = Column(String(128), nullable=False, default="system")
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN)
    mode = Column(Enum(IncidentMode), nullable=False, default=IncidentMode.REAL)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    imagery = relationship("Imagery", back_populates="incident", cascade="all, delete-orphan")
    detections = relationship("SpillDetection", back_populates="incident", cascade="all, delete-orphan")
    hindcast_runs = relationship("HindcastRun", back_populates="incident", cascade="all, delete-orphan")
    ais_queries = relationship("AISQuery", back_populates="incident", cascade="all, delete-orphan")
    candidates = relationship("CandidateVessel", back_populates="incident", cascade="all, delete-orphan")
    manifests = relationship("EvidenceManifestRecord", back_populates="incident", cascade="all, delete-orphan")
