"""
SlickTrace v2 — SpillGeometry ORM Model

Stores topologically repaired, simplified vector geometries generated from
raster segmentation masks. Includes metric area (km2) and perimeter (km)
computed in dynamically projected UTM coordinate systems.
"""
import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SpillGeometry(Base):
    __tablename__ = "spill_geometries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_detection_id = Column(UUID(as_uuid=True), ForeignKey("spill_detections.id"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)

    # WGS84 GeoJSON representation for Mapbox and frontend consumption
    geojson_polygon = Column(JSONB, nullable=False)

    # PostGIS MultiPolygon in EPSG:4326 for spatial index queries
    postgis_geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)

    # Metric Measurements calculated in Projected UTM CRS
    area_km2 = Column(Float, nullable=False)
    perimeter_km = Column(Float, nullable=False)
    projected_crs = Column(String(64), nullable=False)  # e.g., "EPSG:32616 (UTM 16N)"

    # Spatial References in WGS84
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    bbox = Column(JSONB, nullable=False)  # [min_lon, min_lat, max_lon, max_lat]

    # Geometry Quality & Audit Metrics
    geometry_quality = Column(JSONB, nullable=False)
    # {
    #   "validity": "valid" | "repaired",
    #   "simplification_tolerance": float,
    #   "vertex_count": int,
    #   "components_count": int,
    #   "min_component_area_km2": float
    # }

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    detection = relationship("SpillDetection", backref="geometries")
    incident = relationship("Incident", backref="spill_geometries")
