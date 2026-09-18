import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AISQuery(Base):
    __tablename__ = "ais_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    hindcast_run_id = Column(UUID(as_uuid=True), ForeignKey("hindcast_runs.id"), nullable=False)

    time_start = Column(DateTime(timezone=True), nullable=False)
    time_end = Column(DateTime(timezone=True), nullable=False)
    search_polygon = Column(Geometry("POLYGON", srid=4326), nullable=False)
    radius_km = Column(Float, nullable=True)
    ais_source = Column(String(128), nullable=True)
    ais_file_sha256 = Column(String(64), nullable=True)

    vessel_count = Column(Integer, nullable=True)
    results_summary = Column(JSONB, nullable=True)
    duckdb_query_sql = Column(Text, nullable=True)

    executed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    incident = relationship("Incident", back_populates="ais_queries")
    hindcast_run = relationship("HindcastRun", back_populates="ais_queries")
    candidates = relationship("CandidateVessel", back_populates="ais_query", cascade="all, delete-orphan")
