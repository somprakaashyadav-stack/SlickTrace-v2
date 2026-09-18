"""
SlickTrace v2 — Pydantic Schemas for Satellite Evidence
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.satellite_evidence import EvidenceProcessingStatus


class SatelliteEvidenceResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    filename: str
    storage_key: str
    file_hash: str
    size_bytes: int
    content_type: str

    # Satellite & Sensor
    platform: Optional[str] = None
    sensor: Optional[str] = None
    product_type: Optional[str] = None
    polarization: Optional[str] = None

    # Attribution Flags
    acquisition_time: Optional[datetime] = None
    temporal_attribution_available: bool
    crs: Optional[str] = None
    crs_epsg: Optional[int] = None
    is_georeferenced: bool
    geospatial_attribution_available: bool

    # Raster Physical Characteristics
    resolution_x_m: Optional[float] = None
    resolution_y_m: Optional[float] = None
    width: int
    height: int
    bands: int
    nodata_value: Optional[float] = None
    dtype: Optional[str] = None

    # Analysis Ready
    analysis_ready_storage_key: Optional[str] = None
    processing_status: EvidenceProcessingStatus

    # Audit & Diagnostics
    validation_notes: Optional[List[str]] = None
    raw_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SatelliteEvidenceSummary(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    filename: str
    file_hash: str
    platform: Optional[str] = None
    sensor: Optional[str] = None
    acquisition_time: Optional[datetime] = None
    geospatial_attribution_available: bool
    temporal_attribution_available: bool
    processing_status: EvidenceProcessingStatus
    created_at: datetime

    class Config:
        from_attributes = True
