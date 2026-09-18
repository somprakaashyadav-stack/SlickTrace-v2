"""
SlickTrace v2 — Pydantic Schemas for Remote-Sensing Classification & Segmentation
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from ml.models.taxonomy import SpillClass


class DetectionRunRequest(BaseModel):
    incident_id: uuid.UUID
    evidence_id: Optional[uuid.UUID] = Field(
        default=None,
        description="ID of SatelliteEvidence or Imagery uploaded to incident",
    )
    use_onnx: bool = Field(default=True, description="Enable ONNX Runtime acceleration")
    use_secondary_deeplab: bool = Field(default=False, description="Run DeepLabV3+ secondary validation")
    use_sam2: bool = Field(default=False, description="Run SAM 2 boundary refinement")


class DetectionResultResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    detection_class: SpillClass = Field(serialization_alias="class", alias="class")
    confidence: Optional[float] = None
    mask_url: Optional[str] = None
    polygon: Optional[Dict[str, Any]] = None
    area_km2: Optional[float] = None
    centroid: Optional[Tuple[float, float]] = None
    bbox: Optional[Tuple[float, float, float, float]] = None
    acquisition_time: Optional[datetime] = None
    model_version: str
    source_reference: str
    model_validation_status: str
    deeplab_validation_iou: Optional[float] = None
    status: str
    unavailable_reason: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class DetectionPolygonResponse(BaseModel):
    detection_id: uuid.UUID
    detection_class: SpillClass = Field(serialization_alias="class", alias="class")
    polygon: Optional[Dict[str, Any]] = None
    centroid: Optional[Tuple[float, float]] = None
    bbox: Optional[Tuple[float, float, float, float]] = None
    area_km2: Optional[float] = None

    class Config:
        populate_by_name = True


class DetectionApproveRequest(BaseModel):
    approved_by: str = Field(default="Lead Maritime Investigator")
    edited_polygon: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional adjusted GeoJSON polygon modified during human review",
    )
    simplification_tolerance: float = Field(
        default=0.0001,
        description="Douglas-Peucker simplification tolerance in degrees",
    )
    confidence_override: Optional[float] = None
    notes: Optional[str] = None


class DetectionApprovalResponse(BaseModel):
    detection_id: uuid.UUID
    incident_id: uuid.UUID
    status: str
    is_approved: bool
    approved_by: str
    approved_at: datetime
    area_km2: float
    perimeter_km: float
    projected_crs: str
    centroid_lat: float
    centroid_lon: float
    geojson_polygon: Dict[str, Any]

