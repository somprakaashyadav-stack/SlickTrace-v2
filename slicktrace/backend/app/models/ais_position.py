import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AISPosition(Base):
    __tablename__ = "ais_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mmsi = Column(String(50), nullable=False)
    imo = Column(String(50), nullable=True)
    vessel_name = Column(String(255), nullable=True)
    call_sign = Column(String(50), nullable=True)
    vessel_type = Column(String(100), nullable=True)
    length = Column(Float, nullable=True)
    beam = Column(Float, nullable=True)
    draft = Column(Float, nullable=True)

    timestamp_utc = Column(DateTime(timezone=True), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    sog = Column(Float, nullable=True)
    cog = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)

    # PostGIS geometry representation for spatial indexing
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    
    # Provenance requirements
    provider = Column(String(128), nullable=False)
    dataset = Column(String(255), nullable=False)

    __table_args__ = (
        Index("ix_ais_positions_timestamp_utc", "timestamp_utc"),
        Index("ix_ais_positions_mmsi", "mmsi"),
        Index("ix_ais_positions_timestamp_mmsi", "timestamp_utc", "mmsi"),
        # Note: GIST index on geom is created automatically by geoalchemy2 Geometry
    )
