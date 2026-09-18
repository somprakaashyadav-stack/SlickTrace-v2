"""
SlickTrace v2 — SatelliteEvidence ORM Model

Represents ingested satellite scene evidence (Sentinel-1 SAR GRD, Sentinel-2 optical,
Cloud-Optimized GeoTIFFs, or compatible raster products).
Stores cryptographic hash, strict metadata, CRS/georeferencing validation results,
acquisition timing, and attribution availability flags.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EvidenceProcessingStatus(str, PyEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class SatelliteEvidence(Base):
    __tablename__ = "satellite_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)

    # File and Cryptographic Identity
    filename = Column(String(512), nullable=False)
    storage_key = Column(String(1024), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(128), nullable=False, default="image/tiff")

    # Satellite & Sensor Metadata
    platform = Column(String(64), nullable=True)     # e.g., "Sentinel-1A", "Sentinel-2B"
    sensor = Column(String(64), nullable=True)       # e.g., "C-SAR", "MSI"
    product_type = Column(String(64), nullable=True) # e.g., "GRD", "L2A", "COG"
    polarization = Column(String(32), nullable=True) # e.g., "VV", "VH", "VV+VH", "HH"

    # Temporal Attribution
    acquisition_time = Column(DateTime(timezone=True), nullable=True)
    temporal_attribution_available = Column(Boolean, nullable=False, default=False)

    # Geospatial Attribution & CRS
    crs = Column(String(128), nullable=True)          # e.g. "EPSG:32616", "WGS 84 / UTM zone 16N"
    crs_epsg = Column(Integer, nullable=True)        # e.g. 32616
    is_georeferenced = Column(Boolean, nullable=False, default=False)
    geospatial_attribution_available = Column(Boolean, nullable=False, default=False)
    bbox = Column(Geometry("POLYGON", srid=4326), nullable=True) # WGS84 footprint

    # Raster Physical Characteristics
    resolution_x_m = Column(Float, nullable=True)
    resolution_y_m = Column(Float, nullable=True)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    bands = Column(Integer, nullable=False, default=1)
    nodata_value = Column(Float, nullable=True)
    dtype = Column(String(32), nullable=True)

    # Analysis-Ready Preprocessed Output
    analysis_ready_storage_key = Column(String(1024), nullable=True)
    processing_status = Column(
        Enum(EvidenceProcessingStatus),
        nullable=False,
        default=EvidenceProcessingStatus.UPLOADED,
    )

    # Audit & Diagnostics
    validation_notes = Column(JSONB, nullable=True)
    raw_metadata = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

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

    incident = relationship("Incident", backref="satellite_evidence_list")
