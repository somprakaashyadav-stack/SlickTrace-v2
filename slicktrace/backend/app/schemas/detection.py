"""SlickTrace v2 — Pydantic schemas for SpillDetection"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel
from app.models.detection import DetectionStatus, DetectionModel


class DetectionTriggerRequest(BaseModel):
    imagery_id: uuid.UUID
    model: Optional[str] = "unetplusplus"
    use_sam2: Optional[bool] = False


class DetectionResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    imagery_id: uuid.UUID
    status: DetectionStatus
    model_used: Optional[DetectionModel]
    area_km2: Optional[float]
    confidence: Optional[float]
    lookalike_prob: Optional[float]
    is_oil: Optional[bool]
    sam2_refined: bool
    celery_task_id: Optional[str]
    error_message: Optional[str]
    unavailable_reason: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
