"""
SlickTrace v2 — Pydantic Schemas for Spill Geometry
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class SpillGeometryGenerateRequest(BaseModel):
    simplification_tolerance: float = Field(
        default=0.0001,
        ge=0.0,
        le=0.01,
        description="Douglas-Peucker simplification tolerance in degrees (~10m at equator is 0.0001)",
    )
    min_component_pixels: int = Field(default=15, ge=1)


class SpillGeometryResponse(BaseModel):
    id: uuid.UUID
    source_detection_id: uuid.UUID
    incident_id: uuid.UUID
    geojson_polygon: Dict[str, Any]
    area_km2: float
    perimeter_km: float
    projected_crs: str
    centroid_lat: float
    centroid_lon: float
    bbox: List[float]
    geometry_quality: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
