import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Imagery(Base):
    __tablename__ = "imagery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    storage_key = Column(String(1024), nullable=False)
    sha256 = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sensor = Column(String(64), nullable=True)
    polarisation = Column(String(16), nullable=True)
    scene_id = Column(String(256), nullable=True)
    acquisition_time = Column(DateTime(timezone=True), nullable=True)
    bbox = Column(Geometry("POLYGON", srid=4326), nullable=True)
    epsg = Column(Integer, nullable=True, default=4326)
    resolution_m = Column(Float, nullable=True)
    content_type = Column(String(128), nullable=False, default="image/tiff")
    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    incident = relationship("Incident", back_populates="imagery")
    detections = relationship("SpillDetection", back_populates="imagery", cascade="all, delete-orphan")
